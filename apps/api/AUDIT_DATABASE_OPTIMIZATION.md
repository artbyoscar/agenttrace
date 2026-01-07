# Audit Trail Database Optimization Guide

## Overview

This guide provides comprehensive recommendations for database schema design, indexing strategies, and query optimization for the AgentTrace audit trail system.

## Database Schema

### Primary Table: `audit_events`

```sql
CREATE TABLE audit_events (
    -- Event identification
    event_id VARCHAR(64) PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    organization_id VARCHAR(64) NOT NULL,
    project_id VARCHAR(64),

    -- Actor information
    actor_type VARCHAR(20) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    actor_email VARCHAR(255),
    actor_ip INET,
    actor_user_agent TEXT,

    -- Event classification
    event_category VARCHAR(20) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_severity VARCHAR(20) NOT NULL,

    -- Resource information
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(64) NOT NULL,
    resource_name VARCHAR(255),

    -- Change details
    action VARCHAR(20) NOT NULL,
    previous_state JSONB,
    new_state JSONB,

    -- Request context
    request_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64),

    -- Integrity (for blockchain-style chaining)
    hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL DEFAULT '',

    -- Constraints
    CONSTRAINT valid_actor_type CHECK (actor_type IN ('user', 'service', 'system')),
    CONSTRAINT valid_event_category CHECK (event_category IN ('auth', 'data', 'config', 'admin', 'eval')),
    CONSTRAINT valid_action CHECK (action IN ('create', 'read', 'update', 'delete', 'export')),
    CONSTRAINT valid_severity CHECK (event_severity IN ('info', 'warning', 'critical'))
);
```

## Critical Indexes

### 1. Time-Based Queries (Most Common)

**Primary time-series index:**
```sql
CREATE INDEX idx_audit_org_timestamp
ON audit_events (organization_id, timestamp DESC, event_id);
```

**Why:** Most audit queries filter by organization and time range. The `DESC` on timestamp is crucial for recent-events-first queries. Including `event_id` makes this a covering index for pagination.

**Benefits:**
- Supports cursor-based pagination efficiently
- Enables fast time-range queries
- Covers `GET /v1/audit/events` endpoint

### 2. Actor-Based Queries

**Actor activity index:**
```sql
CREATE INDEX idx_audit_actor
ON audit_events (organization_id, actor_id, timestamp DESC);
```

**Why:** Supports user activity reviews and security investigations.

**Benefits:**
- Powers `GET /v1/audit/actors/{actor_id}/activity`
- Enables fast lookup of all actions by a specific user
- Critical for compliance and security audits

### 3. Resource-Based Queries

**Resource access tracking:**
```sql
CREATE INDEX idx_audit_resource
ON audit_events (organization_id, resource_type, resource_id, timestamp DESC);
```

**Why:** Track all access/modifications to specific resources.

**Benefits:**
- Shows complete history of a trace, evaluation, or other resource
- Supports "who accessed this data?" queries
- Critical for data lineage and compliance

### 4. Event Type Filtering

**Event category and type index:**
```sql
CREATE INDEX idx_audit_event_type
ON audit_events (organization_id, event_category, event_type, timestamp DESC);
```

**Why:** Filter events by category (e.g., all auth events, all data access events).

**Benefits:**
- Supports security monitoring dashboards
- Enables fast filtering by event type
- Critical for anomaly detection

### 5. Severity-Based Alerting

**Critical events index:**
```sql
CREATE INDEX idx_audit_severity
ON audit_events (organization_id, event_severity, timestamp DESC)
WHERE event_severity = 'critical';
```

**Why:** Partial index for critical events only (reduces index size).

**Benefits:**
- Fast retrieval of security-critical events
- Supports real-time alerting systems
- Smaller index size (partial index)

### 6. Hash Chain Verification

**Chain verification index:**
```sql
CREATE INDEX idx_audit_hash
ON audit_events (organization_id, timestamp ASC, hash, previous_hash);
```

**Why:** Efficiently verify blockchain-style integrity chains.

**Benefits:**
- Fast integrity verification
- Supports tamper detection
- Required for compliance verification

### 7. Full-Text Search (Optional)

**Event search index:**
```sql
CREATE INDEX idx_audit_search
ON audit_events USING GIN (
    to_tsvector('english',
        COALESCE(event_type, '') || ' ' ||
        COALESCE(resource_name, '') || ' ' ||
        COALESCE(new_state::text, '')
    )
);
```

**Why:** Enable full-text search across audit events.

**Benefits:**
- Search for specific activities or resources
- Incident investigation
- Optional: only create if search is needed

## Partitioning Strategy

For high-volume audit trails (>10M events), implement table partitioning:

### Time-Based Partitioning (Recommended)

```sql
-- Create partitioned table
CREATE TABLE audit_events (
    -- ... same schema as above
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE audit_events_2026_01
PARTITION OF audit_events
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE audit_events_2026_02
PARTITION OF audit_events
FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Automate partition creation with pg_partman or similar
```

**Benefits:**
- Query performance improves (smaller partitions)
- Easy to archive old data
- Efficient deletion of expired data
- Better index maintenance

### Organization-Based Partitioning (Alternative)

For multi-tenant deployments with very large organizations:

```sql
-- Create hash partitions by organization
CREATE TABLE audit_events
PARTITION BY HASH (organization_id);

CREATE TABLE audit_events_0 PARTITION OF audit_events
FOR VALUES WITH (MODULUS 8, REMAINDER 0);

-- ... create 8 partitions total
```

## Query Optimization Tips

### 1. Always Filter by Organization

**BAD:**
```sql
SELECT * FROM audit_events
WHERE actor_id = 'user-123';
```

**GOOD:**
```sql
SELECT * FROM audit_events
WHERE organization_id = 'org-456'
  AND actor_id = 'user-123';
```

### 2. Use Cursor-Based Pagination

**BAD (Offset-based):**
```sql
SELECT * FROM audit_events
ORDER BY timestamp DESC
LIMIT 100 OFFSET 10000;  -- Slow for large offsets
```

**GOOD (Cursor-based):**
```sql
SELECT * FROM audit_events
WHERE organization_id = 'org-123'
  AND (timestamp, event_id) < ('2026-01-15 10:00:00', 'evt-456')
ORDER BY timestamp DESC, event_id DESC
LIMIT 100;
```

### 3. Limit Time Ranges

**BAD:**
```sql
SELECT * FROM audit_events
WHERE organization_id = 'org-123';  -- No time limit
```

**GOOD:**
```sql
SELECT * FROM audit_events
WHERE organization_id = 'org-123'
  AND timestamp >= NOW() - INTERVAL '90 days'
  AND timestamp < NOW();
```

### 4. Use EXPLAIN ANALYZE

Always test critical queries:

```sql
EXPLAIN ANALYZE
SELECT * FROM audit_events
WHERE organization_id = 'org-123'
  AND timestamp >= '2026-01-01'
  AND timestamp < '2026-02-01'
ORDER BY timestamp DESC
LIMIT 100;
```

Look for:
- Index usage (`Index Scan` is good, `Seq Scan` is bad)
- Estimated vs actual rows
- Execution time

## Caching Strategy

### 1. Query Result Caching (Redis)

Cache expensive aggregation queries:

```python
# Cache summary statistics for 5 minutes
cache_key = f"audit:summary:{org_id}:{start_time}:{end_time}"
cached = redis.get(cache_key)
if cached:
    return json.loads(cached)

result = await query_audit_summary(...)
redis.setex(cache_key, 300, json.dumps(result))
return result
```

### 2. Event Count Approximation

For `total_count` in paginated responses, use approximate counts for large datasets:

```sql
-- Exact count (slow for large tables)
SELECT COUNT(*) FROM audit_events WHERE ...;

-- Approximate count (fast)
SELECT reltuples::bigint
FROM pg_class
WHERE relname = 'audit_events';
```

### 3. Materialized Views

For expensive aggregations, use materialized views:

```sql
CREATE MATERIALIZED VIEW audit_daily_summary AS
SELECT
    organization_id,
    DATE(timestamp) as date,
    event_category,
    COUNT(*) as event_count,
    COUNT(DISTINCT actor_id) as unique_actors
FROM audit_events
GROUP BY organization_id, DATE(timestamp), event_category;

CREATE INDEX ON audit_daily_summary (organization_id, date);

-- Refresh periodically (e.g., hourly)
REFRESH MATERIALIZED VIEW CONCURRENTLY audit_daily_summary;
```

## Write Optimization

### 1. Batch Inserts

**BAD:**
```python
for event in events:
    await db.execute("INSERT INTO audit_events ...")
```

**GOOD:**
```python
# Batch insert
await db.executemany(
    "INSERT INTO audit_events VALUES (...)",
    event_batches
)
```

### 2. Async Writes

Don't block API responses waiting for audit logs:

```python
# Queue event for async writing
await audit_queue.put(event)

# Background worker processes queue
async def audit_writer():
    while True:
        batch = await audit_queue.get_batch(size=1000)
        await db.executemany("INSERT INTO ...", batch)
```

### 3. Connection Pooling

Use connection pooling for better performance:

```python
# asyncpg example
pool = await asyncpg.create_pool(
    dsn=DATABASE_URL,
    min_size=5,
    max_size=20,
    command_timeout=60
)
```

## Monitoring & Maintenance

### 1. Monitor Index Usage

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'audit_events'
ORDER BY idx_scan ASC;
```

**Action:** Drop indexes with `idx_scan = 0` (never used).

### 2. Monitor Table Bloat

```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_dead_tup
FROM pg_stat_user_tables
WHERE tablename = 'audit_events';
```

**Action:** Run `VACUUM` if `n_dead_tup` is high.

### 3. Analyze Statistics

Keep table statistics up to date:

```sql
ANALYZE audit_events;
```

**Automate:** Configure `autovacuum` for regular maintenance.

## Storage Considerations

### 1. JSONB Compression

PostgreSQL automatically compresses JSONB fields. For better compression:

```sql
ALTER TABLE audit_events
ALTER COLUMN previous_state SET STORAGE EXTERNAL;

ALTER TABLE audit_events
ALTER COLUMN new_state SET STORAGE EXTERNAL;
```

### 2. Table Compression

Use table-level compression:

```sql
ALTER TABLE audit_events
SET (toast_compression = lz4);
```

### 3. Archive Old Data

Move old audit data to cold storage:

```sql
-- Archive events older than 7 years
INSERT INTO audit_events_archive
SELECT * FROM audit_events
WHERE timestamp < NOW() - INTERVAL '7 years';

DELETE FROM audit_events
WHERE timestamp < NOW() - INTERVAL '7 years';

VACUUM FULL audit_events;
```

## Production Checklist

- [ ] All critical indexes created
- [ ] Table partitioning configured (if >10M events)
- [ ] Connection pooling enabled
- [ ] Query result caching implemented
- [ ] Batch insert strategy in place
- [ ] Async write queue configured
- [ ] Monitoring dashboards for index usage
- [ ] Automated vacuum/analyze scheduled
- [ ] Backup and archival strategy defined
- [ ] Retention policy automated
- [ ] Read replicas configured for reporting queries

## Performance Benchmarks

Expected query performance with proper indexes:

| Query Type | Records | Time (P95) |
|------------|---------|------------|
| Time range (1 day) | 10K | <100ms |
| Time range (30 days) | 300K | <500ms |
| Actor activity (90 days) | 50K | <200ms |
| Resource history | 1K | <50ms |
| Event by ID | 1 | <10ms |
| Aggregation (1 day) | 10K | <300ms |

If queries are slower, check:
1. Index usage (`EXPLAIN ANALYZE`)
2. Table statistics (`ANALYZE`)
3. Connection pool exhaustion
4. Missing `WHERE organization_id` clause
