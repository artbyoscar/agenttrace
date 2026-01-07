# AgentTrace Architecture Documentation

Welcome to the AgentTrace architecture documentation. This directory contains comprehensive technical documentation about the system architecture, design decisions, and technical specifications.

---

## 📁 Directory Structure

```
docs/architecture/
├── README.md                  # This file
├── decisions/                 # Architecture Decision Records (ADRs)
│   ├── TEMPLATE.md           # ADR template
│   ├── ADR-001-*.md          # Individual ADRs
│   └── README.md             # ADR index
└── diagrams/                 # Architecture diagrams (future)
```

---

## 🏗️ Architecture Overview

AgentTrace is a distributed observability platform for AI agents, designed with the following principles:

### Core Principles

1. **Cost Efficiency First**
   - Use object storage (S3/MinIO) for traces
   - Optimize for cold storage
   - Minimize compute costs

2. **Developer Experience**
   - Zero-config auto-instrumentation
   - Simple local development setup
   - Comprehensive documentation

3. **Scalability**
   - Horizontal scaling for all components
   - Stateless services
   - Cloud-native architecture

4. **Flexibility**
   - Support multiple frameworks
   - Self-hosted or cloud deployment
   - Pluggable components

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        AgentTrace                            │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Python SDK  │  │   Dashboard  │  │  Examples    │
│  (PyPI)      │  │  (Next.js)   │  │  (Demos)     │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                  │
       └────────┬────────┴──────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│                     Ingestion Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Go Service │→ │    Kafka     │→ │  Query API   │      │
│  │  (High perf) │  │ (Buffering)  │  │  (FastAPI)   │      │
│  └──────────────┘  └──────────────┘  └──────┬───────┘      │
└─────────────────────────────────────────────│──────────────┘
                                              │
                ┌─────────────────────────────┼───────────┐
                ▼                             ▼           ▼
┌──────────────────┐        ┌──────────────────┐  ┌──────────────┐
│  S3/MinIO        │        │    DuckDB         │  │  PostgreSQL  │
│  (Trace Storage) │        │   (Analytics)     │  │  (Metadata)  │
└──────────────────┘        └──────────────────┘  └──────────────┘
```

---

## 📋 Architecture Decision Records

All major architectural decisions are documented as ADRs in the [`decisions/`](decisions/) directory.

### Key Decisions

| ADR | Decision | Status |
|-----|----------|--------|
| [ADR-001](decisions/ADR-001-monorepo-vs-multirepo.md) | Monorepo with standard tooling | ✅ Accepted |
| [ADR-002](decisions/ADR-002-trace-storage-backend.md) | S3 + DuckDB for storage | ✅ Accepted |
| [ADR-003](decisions/ADR-003-sdk-instrumentation-approach.md) | Monkey-patching + decorators | ✅ Accepted |

[**View all ADRs →**](decisions/README.md)

---

## 🎯 System Architecture

### High-Level Architecture

**Technology Stack:**

- **Frontend:** Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend API:** Python FastAPI, PostgreSQL, Redis
- **Ingestion:** Go service, Kafka
- **Storage:** S3/MinIO (traces), DuckDB (analytics), PostgreSQL (metadata)
- **SDK:** Python 3.9+, async/sync support

### Data Flow

1. **Trace Collection**
   ```
   User Code → SDK → Ingestion Service → Kafka → Storage
   ```

2. **Trace Retrieval**
   ```
   Dashboard → Query API → DuckDB (index) → S3 (traces)
   ```

3. **Analytics**
   ```
   Dashboard → Query API → DuckDB → Parquet files in S3
   ```

### Storage Architecture

**Decision:** S3-compatible object storage with DuckDB indexing ([ADR-002](decisions/ADR-002-trace-storage-backend.md))

```
Traces → Parquet Format → S3 Storage
                              │
                              ├─ Hot: S3 Standard (0-7 days)
                              └─ Cold: S3 Glacier (>7 days)

Metadata → DuckDB Index → Fast Queries
```

**Benefits:**
- 87% cost savings vs PostgreSQL
- Unlimited retention
- Excellent query performance
- Simple data portability

### SDK Architecture

**Decision:** Monkey-patching + decorators ([ADR-003](decisions/ADR-003-sdk-instrumentation-approach.md))

**Auto-instrumentation:**
```python
from agenttrace import init
init(auto_instrument=["langchain", "openai"])
# LangChain and OpenAI now auto-traced
```

**Manual instrumentation:**
```python
from agenttrace import AgentTrace
tracer = AgentTrace()

@tracer.trace_agent()
def my_agent():
    pass
```

---

## 🔧 Component Details

### 1. Python SDK (`packages/sdk-python/`)

**Purpose:** Instrument AI agent code and send traces to ingestion service

**Key Features:**
- Auto-instrumentation for LangChain, CrewAI, OpenAI
- Manual instrumentation with decorators/context managers
- Async/sync support
- Minimal performance overhead (<5%)

**Architecture:**
```
SDK Components:
├── client.py         # Main AgentTrace class
├── tracer.py         # Span and trace management
├── auto/             # Auto-instrumentation
│   ├── langchain.py
│   ├── crewai.py
│   └── openai.py
└── evals/            # Evaluation framework
```

### 2. Ingestion Service (`apps/ingestion/`)

**Purpose:** High-performance trace ingestion and buffering

**Technology:** Go 1.21+

**Features:**
- 10,000+ traces/second per instance
- Validates and enriches trace data
- Publishes to Kafka for reliability
- Horizontal scaling

**Why Go:** Superior performance for I/O-bound operations, low memory footprint

### 3. Query API (`apps/api/`)

**Purpose:** Serve trace data to dashboard and external clients

**Technology:** Python FastAPI

**Endpoints:**
- `POST /api/v1/traces` - Ingest traces (alternative path)
- `GET /api/v1/traces/{id}` - Retrieve trace by ID
- `GET /api/v1/traces` - List/search traces
- `GET /api/v1/analytics/*` - Analytics queries

### 4. Dashboard (`apps/dashboard/`)

**Purpose:** Visualize traces and analytics

**Technology:** Next.js 14 (App Router), React 18, TypeScript

**Features:**
- Real-time trace visualization
- Analytics dashboards
- Project management
- User authentication

---

## 📊 Scalability

### Horizontal Scaling

All components scale horizontally:

| Component | Scaling Strategy | Bottleneck |
|-----------|------------------|------------|
| **SDK** | N/A (client-side) | Network bandwidth |
| **Ingestion** | Add instances behind LB | Kafka throughput |
| **Query API** | Add workers | Database queries |
| **Dashboard** | CDN + edge deployment | API requests |
| **Storage** | S3 auto-scales | Cost |

### Performance Targets

| Metric | Target | Measured |
|--------|--------|----------|
| Ingestion throughput | 10K traces/sec | - |
| Query latency (by ID) | <100ms (p95) | - |
| Analytics queries | <5s (p95) | - |
| SDK overhead | <5% | - |
| Storage cost | <$0.05/1M traces | - |

---

## 🔐 Security Architecture

### Authentication

- **API:** JWT tokens with RS256 signing
- **SDK:** API keys (scoped by project)
- **Dashboard:** NextAuth.js with multiple providers

### Data Protection

- TLS/SSL for all communications
- Encrypted at rest (S3 server-side encryption)
- API key rotation support
- Rate limiting per project/key

### Access Control

- Role-based access control (RBAC)
- Project-level isolation
- Team permissions management

---

## 🚀 Deployment Architecture

### Local Development

```yaml
docker-compose.yml:
  - PostgreSQL
  - Redis
  - MinIO (S3-compatible)
  - Kafka + Zookeeper
  - API
  - Dashboard
  - Ingestion
```

### Cloud Deployment

**Option 1: AWS**
```
- ECS/Fargate for services
- RDS PostgreSQL
- ElastiCache Redis
- S3 for traces
- MSK (Managed Kafka)
```

**Option 2: Kubernetes**
```
- Any K8s cluster
- Helm charts provided
- StatefulSets for stateful services
- HPA for auto-scaling
```

---

## 🔄 Data Retention

### Lifecycle Policies

| Age | Storage Tier | Access Pattern | Cost |
|-----|-------------|----------------|------|
| 0-7 days | S3 Standard | Frequent | $0.023/GB |
| 8-30 days | S3 IA | Infrequent | $0.0125/GB |
| 31-90 days | S3 Glacier | Rare | $0.004/GB |
| >90 days | S3 Deep Archive | Archive | $0.00099/GB |

**User Control:**
- Configurable retention per project
- Automatic lifecycle transitions
- Manual export before deletion

---

## 📈 Monitoring

### Observability Stack

- **Metrics:** Prometheus + Grafana
- **Logs:** Structured JSON logging
- **Traces:** Self-tracing with AgentTrace
- **Alerts:** Prometheus Alertmanager

### Key Metrics

- Ingestion rate (traces/sec)
- Storage usage by project
- Query latency percentiles
- Error rates
- API key usage

---

## 🔄 Future Architecture Considerations

### Planned Enhancements

1. **Real-time streaming** (ADR-004 planned)
   - WebSocket support for live traces
   - Server-Sent Events for updates

2. **Multi-region** (ADR-005 planned)
   - Geo-distributed deployment
   - Data residency compliance

3. **Advanced analytics** (ADR-006 planned)
   - ML-powered anomaly detection
   - Trace clustering and similarity

4. **Cost tracking**
   - Token usage analytics
   - Cost attribution by project

---

## 📚 Related Documentation

### Main Documentation

- [Getting Started Guide](../getting-started.md)
- [SDK Reference](../sdk-reference.md)
- [API Documentation](../api-reference.md)

### Development

- [Contributing Guide](../../CONTRIBUTING.md)
- [Development Setup](../../README.md)
- [CI/CD Guide](../../CI_CD_GUIDE.md)

### Project

- [Project Overview](../../PROJECT_OVERVIEW.md)
- [Roadmap](../../ROADMAP.md)
- [Changelog](../../CHANGELOG.md)

---

## 🤝 Contributing to Architecture

### Proposing Changes

1. **Discuss first** - Open a GitHub issue
2. **Document decision** - Create ADR
3. **Get feedback** - PR for review
4. **Implement** - Reference ADR in code
5. **Review regularly** - Update as needed

### ADR Process

See [ADR README](decisions/README.md) for details on creating and maintaining Architecture Decision Records.

---

**Maintained by:** AgentTrace Architecture Team

**Last Updated:** 2025-01-06

**Next Review:** 2025-07-01
