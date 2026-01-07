# Architecture

Technical architecture overview of AgentTrace.

## System Overview

AgentTrace is built as a distributed system with the following components:

```
┌─────────────┐
│   SDK       │  (Python, JS, etc.)
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Ingestion Service  │  (Go - High throughput)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│      Kafka          │  (Message Queue)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Query API         │  (Python FastAPI)
│                     │
│  ┌──────────────┐   │
│  │  PostgreSQL  │   │  (Primary Storage)
│  └──────────────┘   │
│                     │
│  ┌──────────────┐   │
│  │    Redis     │   │  (Caching)
│  └──────────────┘   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│    Dashboard        │  (Next.js)
└─────────────────────┘
```

## Components

### 1. SDK (Python)

**Technology:** Python 3.9+

**Responsibilities:**
- Instrument agent code
- Capture traces and spans
- Send data to ingestion service
- Handle retries and batching

**Key Features:**
- Async/sync support
- Framework integrations (LangChain, CrewAI)
- Automatic error tracking
- Minimal performance impact

### 2. Ingestion Service

**Technology:** Go 1.21+

**Responsibilities:**
- Receive trace data from SDKs
- Validate incoming data
- Publish to message queue
- High-throughput processing

**Key Features:**
- Written in Go for performance
- Handles 10,000+ requests/second
- Non-blocking I/O
- Horizontal scaling

**Why Go:**
- Superior performance for I/O-bound operations
- Low memory footprint
- Built-in concurrency
- Fast compilation and deployment

### 3. Message Queue (Kafka)

**Technology:** Apache Kafka

**Responsibilities:**
- Decouple ingestion from processing
- Buffer during traffic spikes
- Guarantee message delivery
- Enable stream processing

**Topics:**
- `agent-traces`: Raw trace data
- `trace-events`: Processed events
- `analytics-events`: Analytics aggregations

### 4. Query API

**Technology:** Python FastAPI

**Responsibilities:**
- Process trace data from Kafka
- Store in PostgreSQL
- Serve API requests
- Handle authentication
- Generate analytics

**Endpoints:**
- `POST /api/v1/traces` - Create trace
- `GET /api/v1/traces/{id}` - Get trace
- `GET /api/v1/traces` - List traces
- `GET /api/v1/analytics` - Analytics data
- `GET /api/v1/projects` - Project management

### 5. Database (PostgreSQL)

**Schema:**

```sql
-- Traces table
CREATE TABLE traces (
    id UUID PRIMARY KEY,
    project VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration FLOAT,
    metadata JSONB,
    tags TEXT[],
    environment VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Spans table
CREATE TABLE spans (
    id UUID PRIMARY KEY,
    trace_id UUID REFERENCES traces(id),
    parent_id UUID REFERENCES spans(id),
    name VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration FLOAT,
    logs JSONB,
    error JSONB,
    metadata JSONB
);

-- Indexes
CREATE INDEX idx_traces_project ON traces(project);
CREATE INDEX idx_traces_created_at ON traces(created_at);
CREATE INDEX idx_spans_trace_id ON spans(trace_id);
```

### 6. Cache (Redis)

**Usage:**
- Session storage
- API response caching
- Rate limiting
- Real-time counters

**Key Patterns:**
- `trace:{id}` - Cached trace data
- `project:{id}:stats` - Project statistics
- `rate_limit:{user}` - Rate limit counters

### 7. Dashboard

**Technology:** Next.js 14, React 18, TypeScript

**Features:**
- Trace visualization
- Real-time updates
- Analytics dashboards
- Project management
- User authentication

**Pages:**
- `/` - Dashboard home
- `/traces` - Trace list
- `/traces/[id]` - Trace details
- `/analytics` - Analytics
- `/projects` - Project management

## Data Flow

### 1. Trace Creation

```
SDK → Ingestion Service → Kafka → Query API → PostgreSQL
```

1. SDK captures trace data
2. Sends HTTP POST to ingestion service
3. Ingestion validates and publishes to Kafka
4. Query API consumes from Kafka
5. Data is stored in PostgreSQL

### 2. Trace Retrieval

```
Dashboard → Query API → Redis/PostgreSQL → Dashboard
```

1. Dashboard requests trace data
2. Query API checks Redis cache
3. If miss, queries PostgreSQL
4. Caches result in Redis
5. Returns to dashboard

## Scalability

### Horizontal Scaling

All components can scale horizontally:

- **Ingestion Service**: Add more instances behind load balancer
- **Query API**: Add more workers
- **Kafka**: Add more brokers and partitions
- **PostgreSQL**: Read replicas for queries
- **Dashboard**: Edge deployment with CDN

### Performance Targets

- Ingestion: 10,000 traces/second per instance
- Query API: 1,000 requests/second per instance
- End-to-end latency: < 100ms (p95)
- Storage: 1M traces = ~5GB

## Security

### Authentication

- JWT-based authentication
- API key for SDK authentication
- Role-based access control (RBAC)

### Data Protection

- TLS/SSL for all communications
- Encrypted at rest (PostgreSQL encryption)
- Secure credential storage
- Regular security audits

## Monitoring

### Metrics

- Trace ingestion rate
- API response times
- Database query performance
- Cache hit rates
- Error rates

### Logging

- Structured JSON logs
- Centralized log aggregation
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for tracing

## Deployment

### Docker Compose (Development)

```bash
docker-compose up
```

### Kubernetes (Production)

```yaml
# Example deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agenttrace-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agenttrace-api
  template:
    spec:
      containers:
      - name: api
        image: agenttrace/api:latest
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## Future Enhancements

1. **Real-time streaming**: WebSocket support for live trace updates
2. **AI-powered insights**: Automatic anomaly detection
3. **Cost tracking**: Token usage and cost analysis
4. **Multi-region**: Geo-distributed deployment
5. **Export**: Export traces to S3, BigQuery, etc.

## References

- [Getting Started](getting-started.md)
- [SDK Reference](sdk-reference.md)
- [API Documentation](https://docs.agenttrace.dev/api)
