"""
Example: Complete Audit System Integration

This example shows how to integrate the audit system into a FastAPI application.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from apps.api.models.audit import (
    EventCategory,
    Action,
    ActorType,
    DataEventTypes,
    ConfigEventTypes,
)
from apps.api.services.audit_storage import LocalAuditStorage, S3AuditStorage
from apps.api.services.audit import AuditService, set_audit_service, get_audit_service
from apps.api.services.audit_helpers import AuditHelper
from apps.api.middleware import AuditMiddleware, get_audit_context_dependency, RequestContext


# Global audit helper
_audit_helper: AuditHelper = None


def get_audit_helper() -> AuditHelper:
    """Dependency to get audit helper."""
    return _audit_helper


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _audit_helper

    # Initialize storage backend
    storage_backend = os.getenv("AUDIT_STORAGE_BACKEND", "local")

    if storage_backend == "s3":
        storage = S3AuditStorage(
            bucket_name=os.getenv("AUDIT_S3_BUCKET", "agenttrace-audit-logs"),
            region=os.getenv("AUDIT_S3_REGION", "us-east-1"),
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            retention_days=int(os.getenv("AUDIT_RETENTION_DAYS", "2555"))
        )
    else:
        storage = LocalAuditStorage(
            base_path=os.getenv("AUDIT_STORAGE_PATH", "./audit_logs")
        )

    # Initialize audit service
    audit_service = AuditService(
        storage=storage,
        batch_size=int(os.getenv("AUDIT_BATCH_SIZE", "100")),
        batch_interval=float(os.getenv("AUDIT_BATCH_INTERVAL", "5.0")),
        enable_deduplication=os.getenv("AUDIT_ENABLE_DEDUPLICATION", "true").lower() == "true",
        deduplication_window=int(os.getenv("AUDIT_DEDUPLICATION_WINDOW", "60"))
    )

    # Start the service
    await audit_service.start()
    set_audit_service(audit_service)

    # Initialize audit helper
    _audit_helper = AuditHelper(audit_service)

    print("✓ Audit system started")

    yield

    # Shutdown: Stop audit service
    await audit_service.stop()
    print("✓ Audit system stopped")


# Create FastAPI app
app = FastAPI(
    title="AgentTrace API",
    description="Observability platform for AI agents with enterprise audit trail",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Audit middleware
app.add_middleware(
    AuditMiddleware,
    audit_service=None,  # Will be set from global
    capture_api_access=os.getenv("AUDIT_CAPTURE_API_ACCESS", "true").lower() == "true",
    exclude_paths=["/health", "/metrics", "/docs", "/openapi.json"]
)


# Health check (excluded from audit)
@app.get("/health")
async def health():
    """Health check endpoint."""
    audit_service = get_audit_service()
    return {
        "status": "healthy",
        "audit_system": {
            "running": audit_service._running if audit_service else False,
            "queue_size": len(audit_service._event_queue) if audit_service else 0
        }
    }


# Example: Trace endpoints with audit logging
@app.post("/traces")
async def create_trace(
    trace_data: dict,
    audit_ctx: RequestContext = Depends(get_audit_context_dependency),
    audit_helper: AuditHelper = Depends(get_audit_helper)
):
    """
    Create a new trace with audit logging.

    This example shows automatic audit capture using the helper.
    """
    # Simulate trace creation
    trace_id = "trace-" + os.urandom(8).hex()
    organization_id = trace_data.get("organization_id", "org-demo")
    project_id = trace_data.get("project_id", "proj-demo")

    # Log the trace creation
    await audit_helper.log_trace_created(
        organization_id=organization_id,
        project_id=project_id,
        trace_id=trace_id,
        trace_name=trace_data.get("name", "Unnamed Trace"),
        metadata={
            "spans_count": trace_data.get("spans_count", 0),
            "duration_ms": trace_data.get("duration_ms", 0)
        }
    )

    return {
        "id": trace_id,
        "status": "created",
        "request_id": audit_ctx.request_id
    }


@app.get("/traces/{trace_id}")
async def get_trace(
    trace_id: str,
    audit_ctx: RequestContext = Depends(get_audit_context_dependency),
    audit_helper: AuditHelper = Depends(get_audit_helper)
):
    """
    Get a trace with audit logging.

    This example shows logging read access to sensitive data.
    """
    # Simulate trace retrieval
    trace = {
        "id": trace_id,
        "name": "Example Trace",
        "organization_id": "org-demo",
        "project_id": "proj-demo"
    }

    # Log the trace view
    await audit_helper.log_trace_viewed(
        organization_id=trace["organization_id"],
        project_id=trace["project_id"],
        trace_id=trace_id,
        metadata={
            "request_id": audit_ctx.request_id,
            "actor": audit_ctx.actor_email or audit_ctx.actor_id
        }
    )

    return trace


@app.delete("/traces/{trace_id}")
async def delete_trace(
    trace_id: str,
    audit_ctx: RequestContext = Depends(get_audit_context_dependency),
    audit_helper: AuditHelper = Depends(get_audit_helper)
):
    """
    Delete a trace with comprehensive audit logging.

    This example shows capturing the state before deletion.
    """
    # Get the trace before deletion
    trace = {
        "id": trace_id,
        "name": "Example Trace",
        "organization_id": "org-demo",
        "project_id": "proj-demo",
        "spans_count": 42,
        "created_at": "2024-01-15T10:30:00Z"
    }

    # Log the deletion with previous state
    await audit_helper.log_trace_deleted(
        organization_id=trace["organization_id"],
        project_id=trace["project_id"],
        trace_id=trace_id,
        trace_data=trace,  # Capture what was deleted
        metadata={
            "reason": "User requested deletion",
            "request_id": audit_ctx.request_id
        }
    )

    # Perform actual deletion
    # delete_from_database(trace_id)

    return {"status": "deleted", "trace_id": trace_id}


@app.post("/traces/{trace_id}/export")
async def export_trace(
    trace_id: str,
    format: str = "json",
    audit_ctx: RequestContext = Depends(get_audit_context_dependency),
    audit_helper: AuditHelper = Depends(get_audit_helper)
):
    """
    Export a trace with audit logging.

    This example shows logging sensitive export operations.
    """
    # Get trace
    trace = {
        "id": trace_id,
        "organization_id": "org-demo",
        "project_id": "proj-demo"
    }

    # Log the export (WARNING severity for sensitive operation)
    await audit_helper.log_trace_exported(
        organization_id=trace["organization_id"],
        project_id=trace["project_id"],
        trace_id=trace_id,
        export_format=format,
        metadata={
            "request_id": audit_ctx.request_id,
            "actor": audit_ctx.actor_email or audit_ctx.actor_id
        }
    )

    # Perform export
    export_data = {"trace": trace, "format": format}

    return export_data


# Example: Project endpoints with manual audit capture
@app.put("/projects/{project_id}")
async def update_project(
    project_id: str,
    updates: dict,
    audit_ctx: RequestContext = Depends(get_audit_context_dependency)
):
    """
    Update a project with manual audit capture using context manager.

    This example shows capturing before/after state using audit_context.
    """
    from apps.api.services.audit import audit_context

    # Get current project state
    old_project = {
        "id": project_id,
        "name": "Old Project Name",
        "retention_days": 30,
        "settings": {"auto_evaluate": False}
    }

    # Perform update
    new_project = {**old_project, **updates}

    # Capture audit event with before/after state
    async with audit_context(
        audit_service=get_audit_service(),
        organization_id="org-demo",
        event_category=EventCategory.CONFIG,
        event_type=ConfigEventTypes.PROJECT_UPDATED,
        resource_type="project",
        resource_id=project_id,
        action=Action.UPDATE,
        actor_type=audit_ctx.actor_type,
        actor_id=audit_ctx.actor_id,
        severity=Severity.INFO
    ) as ctx:
        # Set before state
        ctx.before = old_project

        # Update in database (simulated)
        # db.update_project(project_id, updates)

        # Set after state
        ctx.after = new_project

    return new_project


# Example: Query audit events
@app.get("/audit/events")
async def query_audit_events(
    organization_id: str,
    event_category: str = None,
    limit: int = 100,
    offset: int = 0,
    audit_ctx: RequestContext = Depends(get_audit_context_dependency)
):
    """
    Query audit events.

    This endpoint itself generates an audit event for viewing audit logs.
    """
    from apps.api.models.audit import AuditEventFilter, EventCategory as EC

    audit_service = get_audit_service()

    # Create filter
    filter_dict = {
        "organization_id": organization_id,
        "limit": limit,
        "offset": offset
    }

    if event_category:
        filter_dict["event_category"] = EC(event_category)

    filter = AuditEventFilter(**filter_dict)

    # Query events
    events = await audit_service.query_events(filter)

    # Log that audit logs were viewed (meta!)
    await audit_service.capture_event(
        organization_id=organization_id,
        event_category=EventCategory.ADMIN,
        event_type="audit_log.viewed",
        resource_type="audit_log",
        resource_id=organization_id,
        action=Action.READ,
        actor_type=audit_ctx.actor_type,
        actor_id=audit_ctx.actor_id,
        actor_email=audit_ctx.actor_email,
        actor_ip=audit_ctx.actor_ip,
        metadata={
            "event_count": len(events),
            "filter": filter.to_dict()
        }
    )

    return {
        "events": [e.to_dict() for e in events],
        "total": len(events),
        "limit": limit,
        "offset": offset
    }


# Example: Export audit events
@app.post("/audit/export")
async def export_audit_events(
    organization_id: str,
    format: str = "json",
    audit_ctx: RequestContext = Depends(get_audit_context_dependency)
):
    """
    Export audit events for compliance reporting.

    This generates a CRITICAL severity audit event.
    """
    from apps.api.models.audit import AuditEventFilter
    from datetime import datetime, timedelta

    audit_service = get_audit_service()

    # Create filter for last 30 days
    filter = AuditEventFilter(
        organization_id=organization_id,
        start_time=datetime.now() - timedelta(days=30),
        limit=10000
    )

    # Export events
    export_data = await audit_service.export_events(filter, format=format)

    # Log the export with CRITICAL severity
    await audit_service.capture_event(
        organization_id=organization_id,
        event_category=EventCategory.ADMIN,
        event_type="audit_log.exported",
        resource_type="audit_log",
        resource_id=organization_id,
        action=Action.EXPORT,
        actor_type=audit_ctx.actor_type,
        actor_id=audit_ctx.actor_id,
        actor_email=audit_ctx.actor_email,
        actor_ip=audit_ctx.actor_ip,
        event_severity=Severity.CRITICAL,
        metadata={
            "format": format,
            "time_range_days": 30
        }
    )

    return {
        "format": format,
        "data": export_data,
        "organization_id": organization_id
    }


# Example: Verify audit integrity
@app.get("/audit/verify")
async def verify_audit_integrity(
    organization_id: str,
    audit_ctx: RequestContext = Depends(get_audit_context_dependency)
):
    """
    Verify the integrity of the audit chain.

    This is important for compliance and detecting tampering.
    """
    audit_service = get_audit_service()

    # Verify integrity
    result = await audit_service.verify_integrity(organization_id)

    # Log the integrity check
    await audit_service.capture_event(
        organization_id=organization_id,
        event_category=EventCategory.ADMIN,
        event_type="audit.integrity_check",
        resource_type="audit_log",
        resource_id=organization_id,
        action=Action.READ,
        actor_type=audit_ctx.actor_type,
        actor_id=audit_ctx.actor_id,
        metadata=result
    )

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "audit_integration_example:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
