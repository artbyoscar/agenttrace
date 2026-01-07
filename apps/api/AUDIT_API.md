## Audit Trail Query and Export API

Comprehensive REST API for querying, aggregating, and exporting audit events.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Query Endpoints](#query-endpoints)
4. [Aggregation Endpoints](#aggregation-endpoints)
5. [Export Endpoints](#export-endpoints)
6. [Real-time Streaming](#real-time-streaming)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## Overview

The Audit API provides comprehensive access to audit trail data with:

✅ **Flexible querying** with 10+ filter parameters
✅ **Cursor-based pagination** for efficient data retrieval
✅ **Aggregation endpoints** for analytics and reporting
✅ **Async export generation** for large datasets (JSON, CSV, Parquet)
✅ **Real-time streaming** via WebSocket
✅ **Rate limiting** to prevent abuse
✅ **Access control** with permission-based authorization

**Base URL**: `http://localhost:8000/v1/audit`

---

## Authentication & Authorization

### Permissions

The API uses three permission levels:

| Permission | Description | Endpoints |
|------------|-------------|-----------|
| `audit:read` | Query audit events | GET /events, /summary, /actors/* |
| `audit:export` | Export audit data | POST /export, GET /export/* |
| `audit:admin` | Full audit access | All endpoints |

### Authentication

**Bearer Token**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/v1/audit/events
```

**API Key**:
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/v1/audit/events
```

---

## Query Endpoints

### GET /v1/audit/events

Query audit events with comprehensive filtering.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `organization_id` | string | Yes | Organization identifier |
| `start_time` | datetime | Yes | Start of time range (ISO 8601) |
| `end_time` | datetime | Yes | End of time range (ISO 8601) |
| `actor_id` | string | No | Filter by specific actor |
| `actor_type` | enum | No | USER, SERVICE, SYSTEM |
| `event_category` | enum | No | AUTH, DATA, CONFIG, ADMIN, EVAL |
| `event_type` | string | No | Specific event type |
| `resource_type` | string | No | Resource type (trace, project, user) |
| `resource_id` | string | No | Specific resource ID |
| `action` | enum | No | CREATE, READ, UPDATE, DELETE, EXPORT |
| `severity` | enum | No | INFO, WARNING, CRITICAL |
| `limit` | integer | No | Results per page (default: 100, max: 1000) |
| `cursor` | string | No | Pagination cursor |

**Example Request**:
```bash
curl "http://localhost:8000/v1/audit/events? \
  organization_id=org-123& \
  start_time=2024-01-01T00:00:00Z& \
  end_time=2024-01-31T23:59:59Z& \
  event_category=DATA& \
  action=DELETE& \
  limit=50"
```

**Response**:
```json
{
  "events": [
    {
      "event_id": "evt-123",
      "timestamp": "2024-01-15T10:30:00Z",
      "organization_id": "org-123",
      "actor_type": "user",
      "actor_id": "user-456",
      "actor_email": "user@example.com",
      "event_category": "data",
      "event_type": "trace.deleted",
      "resource_type": "trace",
      "resource_id": "trace-789",
      "action": "delete",
      "previous_state": {"name": "Old Trace"},
      "hash": "abc123..."
    }
  ],
  "count": 50,
  "next_cursor": "eyJldmVudF9pZCI6ImV2dC0xMjMiLC...",
  "query_metadata": {
    "time_range_ms": 2592000000,
    "filters_applied": ["event_category", "action"]
  }
}
```

**Pagination**:
```bash
# First page
curl "http://localhost:8000/v1/audit/events?organization_id=org-123&..."

# Next page (use next_cursor from response)
curl "http://localhost:8000/v1/audit/events?organization_id=org-123&cursor=eyJ..."
```

---

### GET /v1/audit/events/{event_id}

Get a single audit event with verification status.

**Example Request**:
```bash
curl http://localhost:8000/v1/audit/events/evt-123
```

**Response**:
```json
{
  "event": {
    "event_id": "evt-123",
    "timestamp": "2024-01-15T10:30:00Z",
    ...
  },
  "verification": {
    "hash_valid": true,
    "computed_hash": "abc123...",
    "stored_hash": "abc123..."
  }
}
```

---

### GET /v1/audit/events/{event_id}/context

Get an event with surrounding context (events before and after).

**Parameters**:
- `before`: Number of events before (default: 5, max: 50)
- `after`: Number of events after (default: 5, max: 50)

**Example Request**:
```bash
curl "http://localhost:8000/v1/audit/events/evt-123/context?before=10&after=10"
```

**Response**:
```json
{
  "event": {...},
  "before": [
    {"event_id": "evt-122", ...},
    {"event_id": "evt-121", ...}
  ],
  "after": [
    {"event_id": "evt-124", ...},
    {"event_id": "evt-125", ...}
  ],
  "verification_status": "valid"
}
```

**Use Case**: Incident investigation, understanding event sequences

---

## Aggregation Endpoints

### GET /v1/audit/summary

Get aggregated audit statistics.

**Parameters**:
- `organization_id`: Organization ID (required)
- `start_time`: Start time (required)
- `end_time`: End time (required)

**Example Request**:
```bash
curl "http://localhost:8000/v1/audit/summary? \
  organization_id=org-123& \
  start_time=2024-01-01T00:00:00Z& \
  end_time=2024-01-31T23:59:59Z"
```

**Response**:
```json
{
  "organization_id": "org-123",
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "total_events": 15234,
  "events_by_category": {
    "auth": 1543,
    "data": 10234,
    "config": 2134,
    "admin": 876,
    "eval": 447
  },
  "events_by_day": {
    "2024-01-01": 543,
    "2024-01-02": 612,
    ...
  },
  "top_actors": [
    {"actor": "user:user-123", "count": 543},
    {"actor": "service:api-key-456", "count": 234}
  ],
  "top_resources": [
    {
      "resource": "trace:trace-789",
      "resource_type": "trace",
      "count": 156,
      "unique_actions": 3
    }
  ],
  "anomalies": [
    {
      "type": "spike",
      "date": "2024-01-15",
      "count": 2134,
      "average": 543
    },
    {
      "type": "unusual_actor_activity",
      "actor": "user:user-suspicious",
      "count": 1543,
      "average": 234
    }
  ]
}
```

**Use Cases**:
- Security monitoring dashboards
- Compliance reporting
- Anomaly detection

---

### GET /v1/audit/actors/{actor_id}/activity

Get full activity timeline for a specific actor.

**Parameters**:
- `organization_id`: Organization ID (required)
- `start_time`: Start time (optional, default: 90 days ago)
- `end_time`: End time (optional, default: now)
- `limit`: Max events (default: 1000, max: 10000)

**Example Request**:
```bash
curl "http://localhost:8000/v1/audit/actors/user-123/activity? \
  organization_id=org-123"
```

**Response**:
```json
{
  "actor_id": "user-123",
  "actor_type": "user",
  "organization_id": "org-123",
  "time_range": {
    "start": "2023-10-15T00:00:00Z",
    "end": "2024-01-15T00:00:00Z"
  },
  "total_events": 543,
  "events_by_category": {
    "data": 400,
    "config": 100,
    "auth": 43
  },
  "events_by_action": {
    "read": 300,
    "create": 150,
    "update": 70,
    "delete": 23
  },
  "first_event": "2023-10-15T10:30:00Z",
  "last_event": "2024-01-15T15:45:00Z",
  "top_resources": [
    {"resource": "trace:trace-123", "access_count": 45},
    {"resource": "project:proj-456", "access_count": 32}
  ],
  "timeline": {
    "2023-10-15": 12,
    "2023-10-16": 8,
    ...
  },
  "events": [...]
}
```

**Use Cases**:
- User access reviews
- Security investigations
- Compliance audits

---

## Export Endpoints

### POST /v1/audit/export

Create an async export job.

**Request Body**:
```json
{
  "organization_id": "org-123",
  "start_time": "2024-01-01T00:00:00Z",
  "end_time": "2024-01-31T23:59:59Z",
  "format": "csv",
  "filters": {
    "event_category": "data",
    "actor_id": "user-123"
  },
  "include_verification": true,
  "encryption": {
    "enabled": false
  }
}
```

**Parameters**:
- `organization_id`: Organization ID (required)
- `start_time`: Start time (required)
- `end_time`: End time (required)
- `format`: Export format - "json", "csv", "parquet" (default: json)
- `filters`: Additional filter criteria (optional)
- `include_verification`: Include hash chain data (default: false)
- `encryption`: Encryption configuration (optional)

**Response**:
```json
{
  "export_id": "exp_abc123def456",
  "status": "processing",
  "organization_id": "org-123",
  "format": "csv",
  "include_verification": true,
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_size_bytes": null,
  "event_count": null
}
```

---

### GET /v1/audit/export/{export_id}

Check export job status.

**Example Request**:
```bash
curl http://localhost:8000/v1/audit/export/exp_abc123def456
```

**Response**:
```json
{
  "export_id": "exp_abc123def456",
  "status": "completed",
  "organization_id": "org-123",
  "format": "csv",
  "created_at": "2024-01-15T10:30:00Z",
  "started_at": "2024-01-15T10:30:05Z",
  "completed_at": "2024-01-15T10:32:15Z",
  "file_size_bytes": 15234567,
  "event_count": 10234,
  "expires_at": "2024-01-16T10:32:15Z"
}
```

**Status Values**:
- `pending`: Queued for processing
- `processing`: Currently generating export
- `completed`: Ready for download
- `failed`: Export failed (see error_message)
- `expired`: Export file deleted

---

### GET /v1/audit/export/{export_id}/download

Download completed export file.

**Example Request**:
```bash
curl -O http://localhost:8000/v1/audit/export/exp_abc123def456/download
```

**Response**: File download with appropriate Content-Type

**Content Types**:
- JSON: `application/json`
- CSV: `text/csv`
- Parquet: `application/octet-stream`

**Filename**: `audit_export_{export_id}.{format}`

---

## Real-time Streaming

### WebSocket /v1/audit/stream

Real-time audit event stream via WebSocket.

**JavaScript Example**:
```javascript
const ws = new WebSocket('ws://localhost:8000/v1/audit/stream');

ws.onopen = () => {
  console.log('Connected to audit stream');

  // Send filter preferences (optional)
  ws.send(JSON.stringify({
    filters: {
      event_category: 'data',
      severity: 'critical'
    }
  }));
};

ws.onmessage = (event) => {
  const auditEvent = JSON.parse(event.data);
  console.log('New audit event:', auditEvent);

  // Update dashboard, trigger alerts, etc.
  if (auditEvent.severity === 'critical') {
    showAlert(auditEvent);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from audit stream');
};
```

**Python Example**:
```python
import asyncio
import websockets
import json

async def audit_stream():
    uri = "ws://localhost:8000/v1/audit/stream"

    async with websockets.connect(uri) as websocket:
        # Receive events
        while True:
            message = await websocket.recv()
            event = json.loads(message)

            print(f"Event: {event['event_type']}")
            print(f"Actor: {event['actor_id']}")
            print(f"Resource: {event['resource_id']}")

asyncio.run(audit_stream())
```

**Message Format**:
```json
{
  "event_id": "evt-123",
  "timestamp": "2024-01-15T10:30:00Z",
  "organization_id": "org-123",
  "event_type": "trace.deleted",
  "actor_id": "user-456",
  "resource_id": "trace-789",
  "action": "delete",
  "severity": "warning"
}
```

**Use Cases**:
- Security monitoring dashboards
- Real-time alerting
- Compliance monitoring
- Anomaly detection

---

## Rate Limiting

All endpoints are rate-limited to prevent abuse.

### Limits

| Endpoint Type | Rate Limit |
|---------------|------------|
| Query endpoints | 60 requests/minute |
| Export endpoints | 10 requests/minute |
| Stream connections | 5 connections/minute |

### Rate Limit Headers

**Response Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642252800
```

**Rate Limit Exceeded**:
```json
HTTP 429 Too Many Requests
{
  "detail": "Rate limit exceeded",
  "retry_after": 30
}
```

**Retry-After**: Seconds until rate limit resets

---

## Examples

### Example 1: Query Deleted Traces

```bash
curl "http://localhost:8000/v1/audit/events? \
  organization_id=org-123& \
  start_time=2024-01-01T00:00:00Z& \
  end_time=2024-01-31T23:59:59Z& \
  event_type=trace.deleted& \
  limit=100"
```

### Example 2: Export Critical Events

```bash
# Create export
curl -X POST http://localhost:8000/v1/audit/export \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org-123",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-31T23:59:59Z",
    "format": "csv",
    "filters": {
      "severity": "critical"
    }
  }'

# Response: {"export_id": "exp_abc123"}

# Check status
curl http://localhost:8000/v1/audit/export/exp_abc123

# Download when complete
curl -O http://localhost:8000/v1/audit/export/exp_abc123/download
```

### Example 3: Investigate User Activity

```bash
# Get user activity
curl "http://localhost:8000/v1/audit/actors/user-suspicious/activity? \
  organization_id=org-123& \
  start_time=2024-01-01T00:00:00Z"

# Get specific event with context
curl "http://localhost:8000/v1/audit/events/evt-suspicious/context? \
  before=20& \
  after=20"
```

### Example 4: Generate Compliance Report

```bash
# Get summary
curl "http://localhost:8000/v1/audit/summary? \
  organization_id=org-123& \
  start_time=2024-01-01T00:00:00Z& \
  end_time=2024-03-31T23:59:59Z"

# Export full audit trail
curl -X POST http://localhost:8000/v1/audit/export \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org-123",
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-03-31T23:59:59Z",
    "format": "csv",
    "include_verification": true
  }'
```

### Example 5: Real-time Monitoring

```python
import asyncio
import websockets

async def monitor_critical_events():
    uri = "ws://localhost:8000/v1/audit/stream"

    async with websockets.connect(uri) as ws:
        while True:
            event = await ws.recv()
            data = json.loads(event)

            if data['severity'] == 'critical':
                send_alert(f"Critical event: {data['event_type']}")

            if data['event_type'] == 'user.login_failed':
                check_brute_force(data['actor_id'])

asyncio.run(monitor_critical_events())
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid cursor format"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Permission required: audit:export"
}
```

### 404 Not Found
```json
{
  "detail": "Event not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 30
}
```

### 503 Service Unavailable
```json
{
  "detail": "Audit service not available"
}
```

---

## Best Practices

### 1. Use Pagination

Always use cursor-based pagination for large queries:
```bash
# Initial query
GET /v1/audit/events?organization_id=org-123&limit=100

# Next page
GET /v1/audit/events?organization_id=org-123&cursor=eyJ...&limit=100
```

### 2. Filter Aggressively

Use multiple filters to reduce result size:
```bash
GET /v1/audit/events? \
  organization_id=org-123& \
  event_category=data& \
  action=delete& \
  severity=critical
```

### 3. Export Large Datasets

For queries > 1000 events, use export instead:
```bash
# Don't: Query 100k events via API
# Do: Create export job
POST /v1/audit/export
```

### 4. Cache Summaries

Cache aggregation results:
```python
@cache(ttl=3600)  # Cache for 1 hour
def get_daily_summary():
    return requests.get('/v1/audit/summary?...')
```

### 5. Monitor Rate Limits

Check rate limit headers:
```python
response = requests.get('/v1/audit/events')
remaining = int(response.headers.get('X-RateLimit-Remaining', 0))

if remaining < 10:
    logger.warning('Approaching rate limit')
```

---

## Performance Tips

### Query Performance

| Result Size | Method | Time |
|-------------|--------|------|
| < 1K events | Direct query | <1s |
| 1K-10K events | Paginated query | 1-5s |
| > 10K events | Export job | 10-60s |

### Optimization

1. **Use specific filters**: Reduce result set
2. **Limit time range**: Shorter ranges = faster queries
3. **Use cursor pagination**: More efficient than offset
4. **Export large datasets**: Don't paginate 100+ pages

---

**Version**: 1.0
**Last Updated**: January 2024
**Maintained By**: AgentTrace API Team
