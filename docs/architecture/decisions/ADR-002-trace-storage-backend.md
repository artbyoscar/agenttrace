# ADR-002: Trace Storage Backend

## Status

**Status:** accepted

**Date:** 2025-01-06

**Deciders:** Oscar Nuñez, AgentTrace Core Team

---

## Context

### Background

AgentTrace needs to store potentially large volumes of trace data:
- Complete execution traces with nested spans
- Metadata (token usage, costs, model parameters)
- Logs and error information
- Custom evaluation results
- Retention requirements vary by user (7 days to unlimited)

Current scale estimates:
- Small deployments: 1K-10K traces/day (~100MB-1GB/day)
- Medium deployments: 100K-1M traces/day (~10GB-100GB/day)
- Large deployments: >10M traces/day (>1TB/day)

### Problem Statement

What storage backend should we use for trace data that balances cost efficiency, query performance, scalability, and developer experience for both cloud and local deployments?

### Goals and Constraints

**Goals:**
- Cost-effective storage for high-volume trace data
- Fast queries for recent traces (last 7 days)
- Support for analytical queries across historical data
- Efficient local development without cloud dependencies
- Unlimited retention capability
- Simple data export and portability
- Support for both hot and cold storage tiers

**Constraints:**
- Limited budget for managed database services
- Need to support self-hosted deployments
- Query latency target: <100ms for recent traces, <5s for analytics
- Must handle unstructured/semi-structured data (JSON)
- PostgreSQL used for operational data (users, projects, API keys)

**Assumptions:**
- Most queries target recent data (last 7 days)
- Full-text search across traces is important
- Cold data access is infrequent but must be possible
- Users may want to export their data easily
- Compression ratios of 5-10x are achievable for trace data

---

## Decision

**We will use S3-compatible object storage (MinIO/S3) for raw trace storage with DuckDB for indexing and analytical queries.**

### Implementation Details

**Architecture:**

```
┌─────────────┐
│   Client    │
│    (SDK)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Ingestion  │
│   Service   │
└──────┬──────┘
       │
       ├──────────────┐
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│     S3      │  │  DuckDB     │
│  (Storage)  │  │  (Index)    │
└─────────────┘  └─────────────┘
       │              │
       └──────┬───────┘
              ▼
       ┌─────────────┐
       │ Query API   │
       └─────────────┘
```

**Storage Layer:**
- **Hot storage (0-7 days)**: S3 Standard or MinIO for local
- **Cold storage (>7 days)**: S3 Glacier/Infrequent Access
- **Format**: Parquet files partitioned by date and project
- **Organization**: `s3://bucket/traces/{project_id}/{date}/{trace_id}.parquet`

**Index Layer:**
- **DuckDB database** with metadata and pointers to S3 objects
- Stores: trace_id, project_id, timestamp, status, tags, summary stats
- Enables fast filtering and analytical queries
- Periodic refresh from S3 (every 5 minutes)

**Query Patterns:**

1. **Recent trace lookup** (by ID):
   - Query DuckDB for S3 path
   - Fetch single Parquet file from S3
   - Latency: ~50-100ms

2. **List recent traces** (with filters):
   - Query DuckDB index
   - Return metadata only (no S3 fetch)
   - Latency: ~10-50ms

3. **Analytics queries**:
   - DuckDB queries Parquet files in S3 directly
   - Uses predicate pushdown and columnar format
   - Latency: ~1-5s for typical queries

4. **Full trace retrieval**:
   - Fetch Parquet file from S3
   - Decompress and deserialize
   - Latency: ~100-200ms

### Key Components

- **MinIO**: S3-compatible object storage for local development and self-hosted deployments
- **AWS S3**: Primary cloud storage backend with lifecycle policies
- **DuckDB**: Embedded analytical database for indexing and queries
- **Parquet**: Columnar file format for efficient storage and queries
- **Lifecycle policies**: Automatic transition to cold storage after 7 days

---

## Consequences

### Positive Consequences

- ✅ **Extremely cost-effective**: S3 storage costs ~$0.023/GB/month (vs $0.10-0.20 for databases)
- ✅ **Unlimited retention**: Can store years of data economically
- ✅ **Excellent local development**: MinIO provides full S3 compatibility locally
- ✅ **Fast analytical queries**: DuckDB efficiently queries Parquet files in S3
- ✅ **Data portability**: Parquet is an open format, easy to export
- ✅ **Scalability**: S3 scales infinitely, no database scaling concerns
- ✅ **Compression**: Parquet with Snappy compression achieves 5-10x compression
- ✅ **Separation of concerns**: Object storage for blobs, PostgreSQL for metadata
- ✅ **Flexible querying**: DuckDB supports SQL and can join with PostgreSQL

### Negative Consequences

- ⚠️ **Added complexity**: Two storage systems to manage (S3 + DuckDB)
- ⚠️ **Eventual consistency**: DuckDB index may lag S3 writes by 5 minutes
- ⚠️ **Network dependency**: Queries require S3 access (latency for remote queries)
- ⚠️ **Cold start penalty**: DuckDB needs to scan Parquet metadata on first query
- ⚠️ **Limited transactional support**: Can't update traces in place easily
- ⚠️ **Learning curve**: Team needs to learn DuckDB and Parquet

### Risks and Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|-------------------|
| S3 costs spiral with scale | High | Medium | Implement aggressive lifecycle policies, compression, and monitoring alerts |
| DuckDB index grows too large | Medium | Low | Partition by date, archive old indexes, use DuckDB's excellent compression |
| Query latency increases | Medium | Medium | Implement caching layer (Redis), optimize Parquet partitioning |
| S3 outage impacts availability | Medium | Low | Cache recent traces in PostgreSQL, implement fallback read path |
| Complex operational overhead | Medium | Medium | Provide Docker Compose setup, automate index refresh, comprehensive monitoring |

---

## Alternatives Considered

### Alternative 1: PostgreSQL with JSONB

**Description:** Store all trace data in PostgreSQL using JSONB columns for flexibility.

**Pros:**
- Simple architecture (single database)
- ACID transactions
- Rich query capabilities with JSONB operators
- No additional storage system to manage
- Good performance for recent data with proper indexing

**Cons:**
- Expensive at scale (storage costs 10x higher than S3)
- JSONB performance degrades with large documents
- Difficult to implement cold storage tiers
- Requires aggressive data retention policies
- Complex queries can impact transactional workload
- Limited compression (TOAST compression not as efficient as Parquet)

**Reason for rejection:** Cost and scalability concerns. PostgreSQL storage costs would become prohibitive at even moderate scale (100K traces/day = $300-500/month vs $20-30 with S3). JSONB is not optimized for analytical queries over large datasets.

### Alternative 2: Elasticsearch / OpenSearch

**Description:** Use Elasticsearch for full-text search and analytical queries over trace data.

**Pros:**
- Excellent full-text search capabilities
- Purpose-built for log/trace data
- Rich query DSL
- Good for real-time analytics
- Built-in aggregations and visualizations

**Cons:**
- Very expensive to operate (requires significant RAM, CPU)
- Complex cluster management
- Poor cost efficiency for cold data
- Difficult to achieve unlimited retention
- High operational complexity
- Resource-intensive for development environments
- Limited compression vs Parquet

**Cost comparison:**
- Elasticsearch: ~$200-500/month for 100GB data + compute
- S3 + DuckDB: ~$2-5/month for 100GB data

**Reason for rejection:** Cost and operational complexity outweigh benefits. Elasticsearch is optimized for real-time search, but most of our queries are simple filters and aggregations that DuckDB handles well. The 100x cost difference is not justified.

### Alternative 3: ClickHouse

**Description:** Use ClickHouse, a columnar OLAP database optimized for analytical queries.

**Pros:**
- Extremely fast analytical queries
- Excellent compression (similar to Parquet)
- Purpose-built for time-series data
- SQL interface
- Good for real-time analytics

**Cons:**
- Complex to operate (cluster management, replication)
- Expensive compute requirements (8GB+ RAM minimum)
- Overkill for current scale
- Difficult local development setup
- Less flexible than object storage for cold data
- Cannot leverage existing S3 ecosystem

**Cost comparison:**
- ClickHouse: ~$100-300/month for hosting + storage
- S3 + DuckDB: ~$2-5/month for storage

**Reason for rejection:** Operational complexity and cost. While ClickHouse would provide excellent query performance, it requires significant operational expertise and resources. DuckDB provides similar query performance for our workload while being much simpler to operate and more cost-effective.

### Alternative 4: TimescaleDB

**Description:** PostgreSQL extension optimized for time-series data.

**Pros:**
- PostgreSQL compatibility (familiar tooling)
- Good compression with columnar storage
- Automatic data tiering
- Continuous aggregates for analytics
- ACID guarantees

**Cons:**
- Still expensive compared to object storage
- Limited to PostgreSQL ecosystem
- Complex to set up tiering to object storage
- Requires careful tuning for performance
- Not as cost-effective as pure object storage

**Reason for rejection:** While better than plain PostgreSQL for time-series data, TimescaleDB doesn't solve the fundamental cost issue. It's still 5-10x more expensive than S3 for cold storage and adds complexity without providing significant benefits over our chosen approach.

### Alternative 5: DynamoDB + S3

**Description:** Use DynamoDB for hot data and metadata, S3 for cold storage.

**Pros:**
- Fully managed (no operational overhead)
- Excellent scalability
- Low latency for key-value lookups
- Good integration with AWS ecosystem

**Cons:**
- Limited analytical query capabilities
- DynamoDB costs can be unpredictable
- Not self-hostable (vendor lock-in)
- Complex pricing model
- Poor support for complex queries
- Requires significant AWS expertise

**Reason for rejection:** Vendor lock-in and limited analytical capabilities. DynamoDB is excellent for key-value access but poor for the analytical queries we need. DuckDB provides better analytical performance while maintaining the ability to self-host.

---

## References

### Technical Documentation

- [DuckDB S3 Integration](https://duckdb.org/docs/extensions/httpfs.html)
- [Parquet Format Specification](https://parquet.apache.org/docs/)
- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [AWS S3 Pricing](https://aws.amazon.com/s3/pricing/)

### Related ADRs

- ADR-001: Monorepo vs Multi-repo (affects schema sharing)
- ADR-003: SDK Instrumentation Approach (affects data collection)

### Supporting Research

- [DuckDB Performance Benchmarks](https://duckdb.org/2021/06/25/querying-parquet.html)
- [Parquet vs JSON Storage Comparison](https://blog.cloudera.com/apache-parquet-1-0-the-columnar-file-format/)
- [S3 Cost Optimization Strategies](https://aws.amazon.com/blogs/storage/optimizing-your-amazon-s3-storage-costs/)

### Industry Examples

- **Uber:** Uses Parquet on HDFS/S3 for analytical data
- **Netflix:** Stores logs in S3, queries with Athena (similar to our approach)
- **Segment:** Uses S3 + Athena for customer data lake
- **Cloudflare:** Stores logs in ClickHouse (different approach, higher scale)

---

## Notes

### Timeline

- **2025-01-06:** Decision proposed and accepted
- **2025-01-15:** Planned implementation start
- **2025-02-01:** Target completion date

### Review Schedule

This decision should be reviewed when:
- Daily trace volume exceeds 10M traces
- Query latency consistently exceeds targets
- Storage costs exceed $500/month
- Self-hosted deployment feedback indicates issues

**Scheduled review date:** 2025-07-01 (6 months)

### Success Metrics

How will we measure if this decision was successful?

- **Storage cost**: <$0.05 per 1M traces stored
- **Query latency**: <100ms for recent traces (p95)
- **Analytics latency**: <5s for typical queries (p95)
- **Local development**: Docker Compose setup works out of the box
- **Data export**: Users can export traces in <5 minutes
- **Retention**: Support unlimited retention without cost prohibitive

### Monitoring Plan

Key metrics to track:
- S3 storage costs by bucket/lifecycle tier
- DuckDB index size and refresh time
- Query latency by pattern (ID lookup, listing, analytics)
- S3 request costs (GET, PUT, LIST operations)
- Data compression ratios
- Index rebuild time

### Implementation Phases

**Phase 1: Basic Storage (Week 1-2)**
- Set up MinIO for local development
- Implement S3 client with basic write/read
- Parquet serialization of trace data
- Basic partitioning by date

**Phase 2: DuckDB Integration (Week 3-4)**
- Set up DuckDB database schema
- Implement index refresh job
- Basic query API (get by ID, list recent)

**Phase 3: Analytics (Week 5-6)**
- Implement analytical queries
- Add predicate pushdown optimizations
- Dashboard integration

**Phase 4: Production Hardening (Week 7-8)**
- Implement lifecycle policies
- Add caching layer
- Monitoring and alerting
- Performance optimization

---

## Appendix: Cost Analysis

### Monthly Cost Estimate (100K traces/day)

**S3 + DuckDB Approach:**
```
Storage: 3TB/month × $0.023/GB = $70
Requests: 100K writes + 1M reads = $1
Data transfer: ~$5 (within region)
Total: ~$76/month
```

**PostgreSQL Approach:**
```
Storage: 3TB (with compression) = 1.5TB actual
RDS cost: 1.5TB × $0.115/GB = $172.50
Backup storage: $50
Compute: db.r5.xlarge = $350
Total: ~$572.50/month
```

**Elasticsearch Approach:**
```
Storage: 3TB with replication = 6TB
Instance costs: 3 × m5.2xlarge = $600
Storage: 6TB × $0.10 = $600
Total: ~$1,200/month
```

**Cost Savings:** 87% vs PostgreSQL, 94% vs Elasticsearch

### Scaling Analysis

At 10M traces/day (100x scale):
- **S3 + DuckDB**: ~$2,300/month (mostly storage)
- **PostgreSQL**: ~$25,000/month (larger instances + storage)
- **Elasticsearch**: ~$50,000/month (large cluster)

**Conclusion:** S3 + DuckDB approach scales cost-effectively.

---

**Last Updated:** 2025-01-06

**Authors:** Oscar Nuñez
