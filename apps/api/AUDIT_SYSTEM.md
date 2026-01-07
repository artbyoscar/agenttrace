# AgentTrace Audit Trail System

## Overview

The AgentTrace audit trail system provides enterprise-grade compliance features through an immutable, blockchain-style event logging system. All significant events are captured with cryptographic integrity verification.

## Features

- **Immutable Event Storage**: Write-once-read-many (WORM) semantics
- **Cryptographic Chain**: SHA-256 hash chain for tamper detection
- **Async Processing**: Non-blocking event capture with batching
- **Event Deduplication**: Prevents duplicate events within time windows
- **Flexible Storage**: Local filesystem or S3 with Object Lock
- **Automatic Capture**: FastAPI middleware for request tracking
- **Rich Context**: IP address, user agent, authentication details
- **Export Capabilities**: JSON and CSV export for compliance reporting

## Architecture

```
┌─────────────────┐
│  FastAPI App    │
│  + Middleware   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Audit Service   │
│ - Validation    │
│ - Enrichment    │
│ - Batching      │
│ - Deduplication │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Audit Storage   │
│ - Local/S3      │
│ - WORM          │
│ - Hash Chain    │
└─────────────────┘
```

## Quick Start

### 1. Initialize the Audit System

```python
from apps.api.services.audit_storage import LocalAuditStorage
from apps.api.services.audit import AuditService
from apps.api.middleware.audit_middleware import AuditMiddleware

# Create storage backend
storage = LocalAuditStorage(base_path="./audit_logs")

# Create audit service
audit_service = AuditService(
    storage=storage,
    batch_size=100,
    batch_interval=5.0,
    enable_deduplication=True,
    deduplication_window=60
)

# Start the service
await audit_service.start()
```

### 2. Add Middleware to FastAPI

```python
from fastapi import FastAPI
from apps.api.middleware import AuditMiddleware

app = FastAPI()

# Add audit middleware
app.add_middleware(
    AuditMiddleware,
    audit_service=audit_service,
    capture_api_access=True,  # Log all API requests
    exclude_paths=["/health", "/metrics"]
)
```

### 3. Capture Events in Your Code

```python
from apps.api.models.audit import EventCategory, Action
from apps.api.services.audit import get_audit_service

# Get the audit service
audit_service = get_audit_service()

# Capture an event
await audit_service.capture_event(
    organization_id="org-123",
    project_id="proj-456",
    event_category=EventCategory.DATA,
    event_type="trace.deleted",
    resource_type="trace",
    resource_id="trace-789",
    action=Action.DELETE,
    actor_type=ActorType.USER,
    actor_id="user-001",
    actor_email="user@example.com"
)
```

## Event Categories and Types

### AUTH Events
- `user.login` - User successfully logged in
- `user.logout` - User logged out
- `user.login_failed` - Failed login attempt
- `api_key.created` - API key created
- `api_key.revoked` - API key revoked
- `sso.initiated` - SSO authentication started
- `sso.completed` - SSO authentication completed

### DATA Events
- `trace.created` - Trace created
- `trace.viewed` - Trace accessed
- `trace.exported` - Trace exported
- `trace.deleted` - Trace deleted
- `trace.shared` - Trace shared with others
- `evaluation.created` - Evaluation created
- `evaluation.viewed` - Evaluation accessed

### CONFIG Events
- `project.created` - Project created
- `project.updated` - Project settings changed
- `project.deleted` - Project deleted
- `retention_policy.updated` - Data retention policy changed
- `evaluator.created` - Evaluator created
- `evaluator.updated` - Evaluator modified
- `test_suite.created` - Test suite created

### ADMIN Events
- `user.invited` - User invited to organization
- `user.role_changed` - User role modified
- `user.removed` - User removed from organization
- `organization.settings_updated` - Organization settings changed
- `billing.plan_changed` - Billing plan updated

### EVAL Events
- `evaluation.started` - Evaluation started
- `evaluation.completed` - Evaluation finished
- `evaluation.failed` - Evaluation failed
- `baseline.updated` - Baseline metrics updated

## Usage Examples

### Example 1: Using Audit Helpers

```python
from apps.api.services.audit_helpers import AuditHelper

# Create helper
helper = AuditHelper(audit_service)

# Log user login
await helper.log_user_login(
    organization_id="org-123",
    user_id="user-456",
    user_email="user@example.com",
    success=True,
    metadata={"ip": "192.168.1.1"}
)

# Log trace deletion with state
await helper.log_trace_deleted(
    organization_id="org-123",
    project_id="proj-456",
    trace_id="trace-789",
    trace_data={"name": "Important Trace", "spans": 42},
    metadata={"reason": "User requested deletion"}
)

# Log project update with before/after state
await helper.log_project_updated(
    organization_id="org-123",
    project_id="proj-456",
    project_name="My Project",
    old_config={"retention_days": 30},
    new_config={"retention_days": 90}
)
```

### Example 2: Using Context Manager

```python
from apps.api.services.audit import audit_context
from apps.api.models.audit import EventCategory, Action, ActorType

async with audit_context(
    audit_service=audit_service,
    organization_id="org-123",
    event_category=EventCategory.CONFIG,
    event_type="project.updated",
    resource_type="project",
    resource_id="proj-456",
    action=Action.UPDATE,
    actor_type=ActorType.USER,
    actor_id="user-789"
) as ctx:
    # Capture before state
    ctx.before = {"name": "Old Name", "status": "active"}

    # Perform your operation
    project = update_project(project_id="proj-456", name="New Name")

    # Capture after state
    ctx.after = {"name": "New Name", "status": "active"}

# Event is automatically captured with both states
```

### Example 3: Querying Audit Events

```python
from apps.api.models.audit import AuditEventFilter, EventCategory
from datetime import datetime, timedelta

# Create filter
filter = AuditEventFilter(
    organization_id="org-123",
    project_id="proj-456",
    event_category=EventCategory.DATA,
    action=Action.DELETE,
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    limit=100,
    offset=0
)

# Query events
events = await audit_service.query_events(filter)

for event in events:
    print(f"{event.timestamp}: {event.event_type} on {event.resource_id}")
    print(f"  Actor: {event.actor_email} ({event.actor_ip})")
    if event.previous_state:
        print(f"  Previous: {event.previous_state}")
```

### Example 4: Exporting Audit Logs

```python
from apps.api.models.audit import AuditEventFilter

# Export last 30 days as JSON
filter = AuditEventFilter(
    organization_id="org-123",
    start_time=datetime.now() - timedelta(days=30),
    limit=10000
)

json_export = await audit_service.export_events(filter, format="json")

# Save to file
with open("audit_export.json", "w") as f:
    f.write(json_export)

# Or export as CSV
csv_export = await audit_service.export_events(filter, format="csv")

with open("audit_export.csv", "w") as f:
    f.write(csv_export)
```

### Example 5: Verifying Integrity

```python
# Verify audit chain integrity
result = await audit_service.verify_integrity(
    organization_id="org-123",
    start_time=datetime.now() - timedelta(days=30),
    end_time=datetime.now()
)

if result["valid"]:
    print(f"✓ Audit chain is valid ({result['total_events']} events)")
else:
    print(f"✗ Audit chain has errors:")
    for error in result["errors"]:
        print(f"  - Event {error['event_id']}: {error['error']}")
```

### Example 6: Custom User Extractor for Middleware

```python
from apps.api.middleware import AuditMiddleware
from apps.api.models.audit import ActorType
import jwt

def custom_user_extractor(request):
    """Extract user from JWT token."""
    auth_header = request.headers.get("authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return {
            "actor_type": ActorType.SYSTEM,
            "actor_id": "system",
            "actor_email": None,
            "organization_id": None,
            "session_id": None
        }

    token = auth_header[7:]

    try:
        payload = jwt.decode(token, "your-secret", algorithms=["HS256"])

        return {
            "actor_type": ActorType.USER,
            "actor_id": payload["user_id"],
            "actor_email": payload["email"],
            "organization_id": payload["organization_id"],
            "session_id": payload.get("session_id")
        }
    except:
        return {
            "actor_type": ActorType.SYSTEM,
            "actor_id": "system",
            "actor_email": None,
            "organization_id": None,
            "session_id": None
        }

# Use custom extractor
app.add_middleware(
    AuditMiddleware,
    audit_service=audit_service,
    user_extractor=custom_user_extractor
)
```

## Production Configuration

### Using S3 with Object Lock (Recommended)

```python
from apps.api.services.audit_storage import S3AuditStorage

# Configure S3 storage with WORM compliance
storage = S3AuditStorage(
    bucket_name="agenttrace-audit-logs",
    region="us-east-1",
    access_key=os.getenv("AWS_ACCESS_KEY_ID"),
    secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    retention_days=2555  # 7 years for compliance
)

audit_service = AuditService(storage=storage)
```

**S3 Bucket Setup:**

```bash
# Create bucket with Object Lock
aws s3api create-bucket \
    --bucket agenttrace-audit-logs \
    --region us-east-1 \
    --object-lock-enabled-for-bucket

# Configure Object Lock default retention
aws s3api put-object-lock-configuration \
    --bucket agenttrace-audit-logs \
    --object-lock-configuration '{
        "ObjectLockEnabled": "Enabled",
        "Rule": {
            "DefaultRetention": {
                "Mode": "COMPLIANCE",
                "Days": 2555
            }
        }
    }'
```

### Environment Variables

```bash
# Storage
AUDIT_STORAGE_BACKEND=s3  # or 'local'
AUDIT_STORAGE_PATH=./audit_logs  # for local
AUDIT_S3_BUCKET=agenttrace-audit-logs
AUDIT_S3_REGION=us-east-1
AUDIT_RETENTION_DAYS=2555

# Service Configuration
AUDIT_BATCH_SIZE=100
AUDIT_BATCH_INTERVAL=5.0
AUDIT_ENABLE_DEDUPLICATION=true
AUDIT_DEDUPLICATION_WINDOW=60

# Middleware
AUDIT_CAPTURE_API_ACCESS=true
```

## Integration with FastAPI Application

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

from apps.api.services.audit_storage import LocalAuditStorage, S3AuditStorage
from apps.api.services.audit import AuditService, set_audit_service
from apps.api.middleware import AuditMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize audit system
    storage = LocalAuditStorage(base_path="./audit_logs")

    audit_service = AuditService(
        storage=storage,
        batch_size=100,
        batch_interval=5.0
    )

    await audit_service.start()
    set_audit_service(audit_service)

    yield

    # Shutdown: Stop audit service
    await audit_service.stop()

app = FastAPI(lifespan=lifespan)

# Add middleware
app.add_middleware(
    AuditMiddleware,
    audit_service=get_audit_service(),
    capture_api_access=True
)
```

## Best Practices

### 1. Always Capture Sensitive Operations

```python
# Deletions
await helper.log_trace_deleted(org_id, proj_id, trace_id, trace_data)

# Exports
await helper.log_trace_exported(org_id, proj_id, trace_id, format)

# Permission changes
await helper.log_user_role_changed(org_id, user_id, email, old_role, new_role)
```

### 2. Include Before/After State for Updates

```python
await audit_service.capture_event(
    organization_id=org_id,
    event_category=EventCategory.CONFIG,
    event_type="project.updated",
    resource_type="project",
    resource_id=project_id,
    action=Action.UPDATE,
    previous_state=old_config,
    new_state=new_config
)
```

### 3. Use Appropriate Severity Levels

- **INFO**: Normal operations (create, read)
- **WARNING**: Sensitive operations (delete, export, permission changes)
- **CRITICAL**: Security events (failed logins, unauthorized access)

### 4. Regular Integrity Verification

```python
# Run daily integrity checks
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2)  # 2 AM daily
async def verify_audit_integrity():
    for org_id in get_all_organizations():
        result = await audit_service.verify_integrity(org_id)
        if not result["valid"]:
            send_alert(f"Audit integrity check failed for {org_id}")

scheduler.start()
```

### 5. Monitor Audit System Health

```python
from fastapi import APIRouter

audit_router = APIRouter()

@audit_router.get("/audit/health")
async def audit_health():
    return {
        "running": audit_service._running,
        "queue_size": len(audit_service._event_queue),
        "recent_events": len(audit_service._recent_events)
    }
```

## Compliance Features

### GDPR Compliance

The audit system supports GDPR requirements:

- **Right to Access**: Query all events for a user
- **Right to Erasure**: Mark events as anonymized (pseudonymization)
- **Data Portability**: Export events as JSON/CSV
- **Audit Trail**: Immutable record of all data processing

```python
# Query all events for a user (Right to Access)
filter = AuditEventFilter(
    organization_id=org_id,
    actor_email="user@example.com",
    limit=10000
)
user_events = await audit_service.query_events(filter)
```

### SOC 2 Compliance

- **Cryptographic Integrity**: SHA-256 hash chain
- **Access Logging**: All data access is logged
- **Change Tracking**: Before/after state for all changes
- **Retention**: Configurable retention periods
- **Immutability**: WORM storage prevents tampering

### HIPAA Compliance

- **Access Auditing**: Log all PHI access
- **Integrity Controls**: Hash verification
- **Retention**: 6+ year retention periods
- **Encryption**: S3 encryption at rest

## Troubleshooting

### Events Not Being Captured

Check that:
1. Audit service is started: `await audit_service.start()`
2. Service is set globally: `set_audit_service(audit_service)`
3. Organization ID is provided
4. Events are not being deduplicated

### High Memory Usage

Reduce batch size or interval:
```python
audit_service = AuditService(
    storage=storage,
    batch_size=50,  # Smaller batches
    batch_interval=2.0  # More frequent flushes
)
```

### Slow Queries

For production, use a database index alongside file/S3 storage:

```python
# Maintain PostgreSQL index for fast queries
# Use S3/files for immutable storage
# Sync events to both systems
```

## API Reference

See the following files for detailed API documentation:

- [models/audit.py](models/audit.py) - Event models and enums
- [services/audit.py](services/audit.py) - Main audit service
- [services/audit_storage.py](services/audit_storage.py) - Storage backends
- [services/audit_helpers.py](services/audit_helpers.py) - Helper functions
- [middleware/audit_middleware.py](middleware/audit_middleware.py) - FastAPI middleware

## Testing

Run the comprehensive test suite:

```bash
cd apps/api
pytest tests/test_audit_*.py -v --cov=services --cov=models
```

## License

Copyright © 2024 AgentTrace. All rights reserved.
