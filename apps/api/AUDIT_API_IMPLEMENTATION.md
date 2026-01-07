# AgentTrace Audit Trail API - Implementation Summary

## Overview

The AgentTrace Audit Trail API provides comprehensive query, aggregation, and export capabilities for enterprise compliance and security monitoring. This document summarizes the complete implementation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Audit API Middleware (Meta-Audit)             │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Access Control Layer                       │ │
│  │  • JWT Authentication                                       │ │
│  │  • Permission Checks (AUDIT_READ, AUDIT_EXPORT)            │ │
│  │  • Rate Limiting (60/min query, 10/min export)             │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Audit Trail Router                       │ │
│  │  • Query Endpoints       • Aggregation Endpoints           │ │
│  │  • Export Endpoints      • WebSocket Streaming             │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Service Layer                            │ │
│  │  • AuditService         • AuditExportService               │ │
│  │  • AuditChain           • AuditStorage                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                          │                        │
         ▼                          ▼                        ▼
  ┌────────────┐          ┌──────────────┐         ┌──────────────┐
  │ PostgreSQL │          │    Redis     │         │   S3/Local   │
  │  (Events)  │          │  (Caching)   │         │   (Exports)  │
  └────────────┘          └──────────────┘         └──────────────┘
```

## API Endpoints

### 1. Query Endpoints

#### `GET /v1/audit/events`

Query audit events with comprehensive filtering and cursor-based pagination.

**Query Parameters:**
- `organization_id` (required) - Organization identifier
- `start_time` (required) - Start of time range (ISO 8601)
- `end_time` (required) - End of time range (ISO 8601)
- `actor_id` - Filter by specific user
- `actor_type` - Filter by actor type (USER, SERVICE, SYSTEM)
- `event_category` - Filter by category (AUTH, DATA, CONFIG, ADMIN, EVAL)
- `event_type` - Filter by specific event type
- `resource_type` - Filter by resource type
- `resource_id` - Filter by specific resource
- `action` - Filter by action (CREATE, READ, UPDATE, DELETE, EXPORT)
- `severity` - Filter by severity (INFO, WARNING, CRITICAL)
- `limit` - Results per page (default: 100, max: 1000)
- `cursor` - Pagination cursor

**Response:**
```json
{
  "events": [...],
  "count": 100,
  "next_cursor": "eyJ0aW1lc3RhbXAiOi...",
  "query_metadata": {
    "time_range_ms": 2592000000,
    "filters_applied": ["event_category", "actor_id"]
  }
}
```

**Access Control:**
- Requires: `AUDIT_READ` permission
- Rate Limit: 60 requests/minute

**Example:**
```bash
curl -X GET "https://api.agenttrace.dev/v1/audit/events?\
organization_id=org-123&\
start_time=2026-01-01T00:00:00Z&\
end_time=2026-01-31T23:59:59Z&\
event_category=DATA&\
limit=100" \
-H "Authorization: Bearer YOUR_TOKEN"
```

#### `GET /v1/audit/events/{event_id}`

Retrieve a single event with full details and verification status.

**Response:**
```json
{
  "event": {
    "event_id": "evt-123",
    "timestamp": "2026-01-15T10:30:00Z",
    "organization_id": "org-123",
    "actor_id": "user-456",
    "event_type": "trace.deleted",
    "resource_id": "trace-789",
    ...
  },
  "verification": {
    "hash_valid": true,
    "computed_hash": "abc123...",
    "stored_hash": "abc123..."
  }
}
```

**Access Control:**
- Requires: `AUDIT_READ` permission
- Rate Limit: 60 requests/minute

#### `GET /v1/audit/events/{event_id}/context`

Get surrounding events (before and after) for incident investigation.

**Query Parameters:**
- `before` - Number of events before (default: 5, max: 50)
- `after` - Number of events after (default: 5, max: 50)

**Response:**
```json
{
  "event": {...},
  "before": [{...}, {...}],
  "after": [{...}, {...}],
  "verification_status": "valid"
}
```

**Access Control:**
- Requires: `AUDIT_READ` permission
- Rate Limit: 60 requests/minute

### 2. Aggregation Endpoints

#### `GET /v1/audit/summary`

Get aggregated statistics over a time range.

**Query Parameters:**
- `organization_id` (required)
- `start_time` (required)
- `end_time` (required)

**Response:**
```json
{
  "organization_id": "org-123",
  "time_range": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-01-31T23:59:59Z"
  },
  "total_events": 15234,
  "events_by_category": {
    "auth": 1234,
    "data": 8765,
    "config": 543,
    "admin": 234,
    "eval": 4458
  },
  "events_by_day": {
    "2026-01-01": 500,
    "2026-01-02": 523,
    ...
  },
  "top_actors": [
    {"actor": "user:user-123", "count": 234},
    {"actor": "service:api-worker", "count": 123}
  ],
  "top_resources": [
    {
      "resource": "trace:trace-456",
      "resource_type": "trace",
      "count": 45,
      "unique_actions": 3
    }
  ],
  "anomalies": [
    {
      "type": "spike",
      "date": "2026-01-15",
      "count": 2000,
      "average": 500
    }
  ]
}
```

**Access Control:**
- Requires: `AUDIT_READ` permission
- Rate Limit: 60 requests/minute

#### `GET /v1/audit/actors/{actor_id}/activity`

Get full activity timeline for a specific actor.

**Query Parameters:**
- `organization_id` (required)
- `start_time` - Start time (default: 90 days ago)
- `end_time` - End time (default: now)
- `limit` - Max events (default: 1000, max: 10000)

**Response:**
```json
{
  "actor_id": "user-123",
  "actor_type": "user",
  "organization_id": "org-123",
  "time_range": {...},
  "total_events": 543,
  "events_by_category": {...},
  "events_by_action": {...},
  "first_event": "2025-10-01T00:00:00Z",
  "last_event": "2026-01-15T10:30:00Z",
  "top_resources": [...],
  "timeline": {...},
  "events": [...]
}
```

**Access Control:**
- Requires: `AUDIT_READ` permission
- Rate Limit: 60 requests/minute

### 3. Export Endpoints

#### `POST /v1/audit/export`

Create an asynchronous export job.

**Request Body:**
```json
{
  "organization_id": "org-123",
  "start_time": "2026-01-01T00:00:00Z",
  "end_time": "2026-01-31T23:59:59Z",
  "format": "csv",  // csv, json, parquet
  "filters": {
    "event_category": "DATA"
  },
  "include_verification": true,
  "encryption": {
    "enabled": true,
    "public_key": "-----BEGIN PUBLIC KEY-----..."
  }
}
```

**Response:**
```json
{
  "export_id": "exp_a1b2c3d4e5f6",
  "status": "processing",
  "format": "csv",
  "include_verification": true,
  "encryption_enabled": true,
  "created_at": "2026-01-15T10:30:00Z"
}
```

**Access Control:**
- Requires: `AUDIT_EXPORT` permission
- Rate Limit: 10 requests/minute (stricter than query)

#### `GET /v1/audit/export/{export_id}`

Check export job status.

**Response:**
```json
{
  "export_id": "exp_a1b2c3d4e5f6",
  "status": "completed",  // pending, processing, completed, failed, expired
  "format": "csv",
  "file_size_bytes": 15234567,
  "event_count": 15234,
  "created_at": "2026-01-15T10:30:00Z",
  "completed_at": "2026-01-15T10:35:00Z",
  "expires_at": "2026-01-16T10:35:00Z"
}
```

**Access Control:**
- Requires: `AUDIT_EXPORT` permission
- Rate Limit: 60 requests/minute

#### `GET /v1/audit/export/{export_id}/download`

Download completed export file.

**Response:**
- File download with appropriate content type
- Filename: `audit_export_{export_id}.{format}`

**Access Control:**
- Requires: `AUDIT_EXPORT` permission
- Rate Limit: 60 requests/minute

### 4. WebSocket Streaming

#### `WS /v1/audit/stream`

Real-time audit event stream for security monitoring dashboards.

**Client Example:**
```javascript
const ws = new WebSocket('wss://api.agenttrace.dev/v1/audit/stream');

ws.onmessage = (event) => {
  const auditEvent = JSON.parse(event.data);
  console.log('New audit event:', auditEvent);

  // Update dashboard in real-time
  updateSecurityDashboard(auditEvent);
};

// Send filter preferences (optional)
ws.send(JSON.stringify({
  event_category: 'AUTH',
  severity: 'CRITICAL'
}));
```

**Access Control:**
- Requires: Valid authentication token
- Rate Limit: 5 connections/minute per user

### 5. Health Check

#### `GET /v1/audit/health`

Check status of audit API components.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "audit_service": "available",
    "export_service": "available",
    "websocket_connections": 12
  }
}
```

## Security Features

### 1. Access Control

**Permission Levels:**
- `AUDIT_READ` - Read audit events (query, view)
- `AUDIT_EXPORT` - Export audit data (create exports, download)
- `AUDIT_ADMIN` - Full audit administration

**Implementation:**
- JWT-based authentication (Bearer tokens)
- Permission checks on all endpoints via FastAPI dependencies
- User context extracted from authentication headers

### 2. Rate Limiting

**Limits:**
- Query endpoints: 60 requests/minute
- Export endpoints: 10 requests/minute
- WebSocket: 5 connections/minute

**Implementation:**
- Token bucket algorithm
- Per-user rate limiting
- HTTP 429 responses with `Retry-After` header

**Production Recommendation:**
Replace in-memory rate limiter with Redis:
```python
from redis import Redis
from limits import storage, strategies

storage = storage.RedisStorage("redis://localhost:6379")
limiter = strategies.MovingWindowRateLimiter(storage)
```

### 3. Meta-Audit Logging

All access to the audit API is itself audited:

**Logged Information:**
- Who accessed audit logs (actor_id)
- When (timestamp)
- What endpoint (resource_id)
- IP address and user agent
- Response time and status code

**Event Type:**
- `audit_log.viewed` - For query endpoints
- `audit_log.exported` - For export endpoints

This creates a complete audit trail of audit trail access for compliance.

### 4. Data Integrity

**Hash Chaining:**
- Each event contains SHA-256 hash of its content
- Each event references previous event's hash (blockchain-style)
- Tamper detection via hash verification

**Storage:**
- LocalAuditStorage: File-based with read-only permissions
- S3AuditStorage: AWS S3 with Object Lock (WORM compliance)

## Integration Guide

### 1. Enable Audit Router

Already integrated in `main.py`:
```python
from src.api.routes import audit
from src.api.middleware.access_control import AuditAPIMiddleware

# Add middleware
app.add_middleware(AuditAPIMiddleware)

# Include router
app.include_router(audit.router, prefix="/api", tags=["audit"])
```

### 2. Configure Storage Backend

**For Development (Local File Storage):**
```python
from apps.api.services.audit_storage import LocalAuditStorage

storage = LocalAuditStorage(base_path="./audit_logs")
```

**For Production (S3 with Object Lock):**
```python
from apps.api.services.audit_storage import S3AuditStorage

storage = S3AuditStorage(
    bucket_name="agenttrace-audit-logs",
    region="us-east-1",
    retention_days=2555  # 7 years for compliance
)
```

### 3. Configure Authentication

Update `get_current_user()` in `access_control.py`:
```python
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Decode JWT token
    token = credentials.credentials
    payload = decode_jwt(token)

    # Load user from database
    user = await db.get_user(payload['user_id'])

    return User(
        user_id=user.id,
        permissions=user.permissions
    )
```

### 4. Set Up Database Indexes

See [AUDIT_DATABASE_OPTIMIZATION.md](./AUDIT_DATABASE_OPTIMIZATION.md) for complete SQL scripts.

**Critical indexes:**
```sql
CREATE INDEX idx_audit_org_timestamp
ON audit_events (organization_id, timestamp DESC, event_id);

CREATE INDEX idx_audit_actor
ON audit_events (organization_id, actor_id, timestamp DESC);

CREATE INDEX idx_audit_resource
ON audit_events (organization_id, resource_type, resource_id, timestamp DESC);
```

### 5. Configure Export Directory

```python
export_service = AuditExportService(
    export_dir="/var/exports/audit",  # Persistent storage
    expiration_hours=24
)
```

## Testing

### Manual Testing

**1. Query Events:**
```bash
curl -X GET "http://localhost:8000/v1/audit/events?\
organization_id=org-123&\
start_time=2026-01-01T00:00:00Z&\
end_time=2026-01-31T23:59:59Z" \
-H "Authorization: Bearer token"
```

**2. Create Export:**
```bash
curl -X POST "http://localhost:8000/v1/audit/export" \
-H "Authorization: Bearer token" \
-H "Content-Type: application/json" \
-d '{
  "organization_id": "org-123",
  "start_time": "2026-01-01T00:00:00Z",
  "end_time": "2026-01-31T23:59:59Z",
  "format": "csv"
}'
```

**3. WebSocket Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/v1/audit/stream');
ws.onmessage = console.log;
```

### Automated Testing

See `apps/api/tests/test_audit_api.py` for comprehensive test suite.

## Performance Considerations

### Query Performance

**Expected Performance (with proper indexes):**
- Single event lookup: <10ms
- Time range query (1 day): <100ms
- Time range query (30 days): <500ms
- Actor activity (90 days): <200ms
- Aggregation (1 day): <300ms

**Optimization Tips:**
1. Always filter by `organization_id`
2. Use cursor-based pagination (not offset)
3. Limit time ranges to necessary window
4. Cache aggregation results (5-minute TTL)

### Export Performance

**Expected Performance:**
- 10K events: ~2 seconds
- 100K events: ~10 seconds
- 1M events: ~60 seconds

**Formats:**
- JSON: Human-readable, moderate size
- CSV: Excel-compatible, smallest size
- Parquet: Columnar format, best for analytics

### Scaling Recommendations

**Up to 1M events/month:**
- Single PostgreSQL instance
- Local file storage for exports
- In-memory rate limiting

**1M-10M events/month:**
- PostgreSQL with read replicas
- Redis for caching and rate limiting
- S3 for export storage
- Table partitioning by month

**>10M events/month:**
- Sharded PostgreSQL or migrate to TimescaleDB
- Redis cluster
- S3 with Object Lock
- Dedicated export workers
- CDN for export downloads

## Compliance Features

✅ **GDPR Compliance:**
- Right to access (query by actor_id)
- Right to export (export endpoints)
- Right to be forgotten (supported via deletion events)

✅ **SOC 2 Compliance:**
- Comprehensive audit trail
- Access control and authentication
- Tamper-proof storage (hash chaining)
- Retention policies

✅ **HIPAA Compliance:**
- Encrypted exports (optional)
- Access logging (meta-audit)
- Integrity verification

✅ **Financial Regulations:**
- Immutable audit trail
- Long-term retention (7+ years)
- Chain-of-custody verification

## Monitoring & Alerting

**Key Metrics to Monitor:**
1. Query latency (P50, P95, P99)
2. Export job success rate
3. Rate limit hit rate
4. Database connection pool usage
5. Storage size growth
6. Failed integrity checks

**Alert Triggers:**
1. Query latency >1 second
2. Export failures
3. Rate limit exceeded (may indicate abuse)
4. Hash verification failures (tampering!)
5. Storage >80% capacity

## Roadmap

**Planned Features:**
- [ ] Advanced anomaly detection (ML-based)
- [ ] Compliance report generation (SOC 2, GDPR)
- [ ] Integration with SIEM systems
- [ ] GraphQL query interface
- [ ] Automated retention policy enforcement
- [ ] Multi-region replication

## Support

**Documentation:**
- API Reference: `/docs` (Swagger UI)
- Database Optimization: [AUDIT_DATABASE_OPTIMIZATION.md](./AUDIT_DATABASE_OPTIMIZATION.md)
- Integration Examples: `apps/api/examples/`

**Issues:**
- GitHub Issues: [agenttrace/issues](https://github.com/agenttrace/agenttrace/issues)
- Security: security@agenttrace.dev
