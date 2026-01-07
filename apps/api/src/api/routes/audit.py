"""
Audit Trail API Routes

Comprehensive API for querying, aggregating, and exporting audit events.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict, Counter

from fastapi import APIRouter, HTTPException, Query, Depends, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from ....models.audit import (
    AuditEvent,
    AuditEventFilter,
    ActorType,
    EventCategory,
    Action,
    Severity
)
from ....services.audit import get_audit_service
from ....services.audit_export import AuditExportService, ExportFormat, ExportJob
from ....services.audit_verification import AuditChain
from ...utils.pagination import PaginationCursor, PaginatedResponse


router = APIRouter(prefix="/v1/audit", tags=["Audit Trail"])


# Initialize services
_export_service: Optional[AuditExportService] = None
_audit_chain = AuditChain()


def get_export_service() -> AuditExportService:
    """Get or create export service."""
    global _export_service
    if _export_service is None:
        _export_service = AuditExportService(
            export_dir="./exports",
            expiration_hours=24
        )
        asyncio.create_task(_export_service.start())
    return _export_service


# Pydantic models for request/response

class QueryEventsRequest(BaseModel):
    """Request model for querying events."""
    organization_id: str = Field(..., description="Organization ID")
    start_time: datetime = Field(..., description="Start of time range (ISO 8601)")
    end_time: datetime = Field(..., description="End of time range (ISO 8601)")
    actor_id: Optional[str] = Field(None, description="Filter by actor ID")
    actor_type: Optional[ActorType] = Field(None, description="Filter by actor type")
    event_category: Optional[EventCategory] = Field(None, description="Filter by category")
    event_type: Optional[str] = Field(None, description="Filter by specific event type")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    action: Optional[Action] = Field(None, description="Filter by action")
    severity: Optional[Severity] = Field(None, description="Filter by severity")
    limit: int = Field(100, le=1000, description="Number of results per page")
    cursor: Optional[str] = Field(None, description="Pagination cursor")


class EventContextResponse(BaseModel):
    """Response for event context."""
    event: dict
    before: List[dict] = []
    after: List[dict] = []
    verification_status: str


class ExportRequest(BaseModel):
    """Request for creating export."""
    organization_id: str = Field(..., description="Organization ID")
    start_time: datetime = Field(..., description="Start time")
    end_time: datetime = Field(..., description="End time")
    format: ExportFormat = Field(ExportFormat.JSON, description="Export format")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    include_verification: bool = Field(False, description="Include hash chain data")
    encryption: Optional[Dict[str, Any]] = Field(None, description="Encryption config")


class ActivitySummary(BaseModel):
    """Actor activity summary."""
    actor_id: str
    actor_type: str
    total_events: int
    events_by_category: Dict[str, int]
    events_by_action: Dict[str, int]
    first_event: datetime
    last_event: datetime
    top_resources: List[Dict[str, Any]]


# ========== Query Endpoints ==========

@router.get("/events")
async def query_events(
    organization_id: str = Query(..., description="Organization ID"),
    start_time: datetime = Query(..., description="Start time (ISO 8601)"),
    end_time: datetime = Query(..., description="End time (ISO 8601)"),
    actor_id: Optional[str] = Query(None, description="Filter by actor"),
    actor_type: Optional[ActorType] = Query(None, description="Filter by actor type"),
    event_category: Optional[EventCategory] = Query(None, description="Filter by category"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    action: Optional[Action] = Query(None, description="Filter by action"),
    severity: Optional[Severity] = Query(None, description="Filter by severity"),
    limit: int = Query(100, le=1000, description="Results per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor")
):
    """
    Query audit events with comprehensive filtering.

    Supports cursor-based pagination for efficient querying of large datasets.

    **Example**:
    ```
    GET /v1/audit/events?organization_id=org-123&start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z
    ```

    **Response**:
    ```json
    {
      "events": [...],
      "count": 100,
      "next_cursor": "eyJ...",
      "query_metadata": {
        "time_range_ms": 2592000000,
        "filters_applied": ["event_category"]
      }
    }
    ```
    """
    audit_service = get_audit_service()
    if not audit_service:
        raise HTTPException(status_code=503, detail="Audit service not available")

    # Parse cursor if provided
    cursor_timestamp = None
    cursor_event_id = None
    if cursor:
        try:
            cursor_data = PaginationCursor.decode(cursor)
            cursor_timestamp = cursor_data["timestamp"]
            cursor_event_id = cursor_data["event_id"]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Build filter
    filter = AuditEventFilter(
        organization_id=organization_id,
        start_time=start_time,
        end_time=end_time,
        actor_id=actor_id,
        actor_type=actor_type,
        event_category=event_category,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        event_severity=severity,
        limit=limit + 1  # Get one extra to determine if there are more
    )

    # Query events
    events = await audit_service.query_events(filter)

    # Determine if there are more results
    has_more = len(events) > limit
    if has_more:
        events = events[:limit]

    # Generate next cursor
    next_cursor = None
    if has_more and events:
        last_event = events[-1]
        next_cursor = PaginationCursor.encode(last_event.timestamp, last_event.event_id)

    # Calculate metadata
    filters_applied = []
    if actor_id:
        filters_applied.append("actor_id")
    if actor_type:
        filters_applied.append("actor_type")
    if event_category:
        filters_applied.append("event_category")
    if event_type:
        filters_applied.append("event_type")
    if resource_type:
        filters_applied.append("resource_type")
    if resource_id:
        filters_applied.append("resource_id")
    if action:
        filters_applied.append("action")
    if severity:
        filters_applied.append("severity")

    time_range_ms = int((end_time - start_time).total_seconds() * 1000)

    metadata = {
        "time_range_ms": time_range_ms,
        "filters_applied": filters_applied
    }

    # Create paginated response
    response = PaginatedResponse(
        items=events,
        next_cursor=next_cursor,
        metadata=metadata
    )

    return response.to_dict()


@router.get("/events/{event_id}")
async def get_event(event_id: str):
    """
    Get a single audit event by ID with verification status.

    **Example**:
    ```
    GET /v1/audit/events/evt-123
    ```

    **Response**:
    ```json
    {
      "event": {...},
      "verification": {
        "hash_valid": true,
        "computed_hash": "abc123..."
      }
    }
    ```
    """
    audit_service = get_audit_service()
    if not audit_service:
        raise HTTPException(status_code=503, detail="Audit service not available")

    # Get event
    event = await audit_service.get_event(event_id)

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Verify hash
    hash_valid = event.verify_hash()
    computed_hash = _audit_chain.compute_event_hash(event)

    return {
        "event": event.to_dict(),
        "verification": {
            "hash_valid": hash_valid,
            "computed_hash": computed_hash,
            "stored_hash": event.hash
        }
    }


@router.get("/events/{event_id}/context")
async def get_event_context(
    event_id: str,
    before: int = Query(5, le=50, description="Number of events before"),
    after: int = Query(5, le=50, description="Number of events after")
):
    """
    Get an event with surrounding context (events before and after).

    Useful for incident investigation and understanding the sequence of events.

    **Example**:
    ```
    GET /v1/audit/events/evt-123/context?before=5&after=5
    ```

    **Response**:
    ```json
    {
      "event": {...},
      "before": [{...}, {...}],
      "after": [{...}, {...}],
      "verification_status": "valid"
    }
    ```
    """
    audit_service = get_audit_service()
    if not audit_service:
        raise HTTPException(status_code=503, detail="Audit service not available")

    # Get the target event
    event = await audit_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Query events before
    filter_before = AuditEventFilter(
        organization_id=event.organization_id,
        end_time=event.timestamp,
        limit=before
    )
    events_before = await audit_service.query_events(filter_before)

    # Query events after
    filter_after = AuditEventFilter(
        organization_id=event.organization_id,
        start_time=event.timestamp,
        limit=after + 1  # +1 because target event will be included
    )
    events_after = await audit_service.query_events(filter_after)

    # Remove target event from after list
    events_after = [e for e in events_after if e.event_id != event_id][:after]

    # Verify chain for context
    all_events = events_before + [event] + events_after
    verification = _audit_chain.verify_chain(all_events)

    return {
        "event": event.to_dict(),
        "before": [e.to_dict() for e in events_before],
        "after": [e.to_dict() for e in events_after],
        "verification_status": verification.status.value
    }


# ========== Aggregation Endpoints ==========

@router.get("/summary")
async def get_audit_summary(
    organization_id: str = Query(..., description="Organization ID"),
    start_time: datetime = Query(..., description="Start time"),
    end_time: datetime = Query(..., description="End time")
):
    """
    Get audit summary with aggregated statistics.

    Returns:
    - Event counts by category
    - Top actors by event count
    - Most accessed resources
    - Anomaly indicators

    **Example**:
    ```
    GET /v1/audit/summary?organization_id=org-123&start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z
    ```
    """
    audit_service = get_audit_service()
    if not audit_service:
        raise HTTPException(status_code=503, detail="Audit service not available")

    # Query all events in range
    filter = AuditEventFilter(
        organization_id=organization_id,
        start_time=start_time,
        end_time=end_time,
        limit=100000  # Large limit for aggregation
    )

    events = await audit_service.query_events(filter)

    # Aggregate statistics
    events_by_category = defaultdict(int)
    events_by_actor = defaultdict(int)
    events_by_resource = defaultdict(lambda: {"count": 0, "resource_type": "", "actions": []})
    events_by_day = defaultdict(int)

    for event in events:
        # By category
        events_by_category[event.event_category.value] += 1

        # By actor
        actor_key = f"{event.actor_type.value}:{event.actor_id}"
        events_by_actor[actor_key] += 1

        # By resource
        resource_key = f"{event.resource_type}:{event.resource_id}"
        events_by_resource[resource_key]["count"] += 1
        events_by_resource[resource_key]["resource_type"] = event.resource_type
        events_by_resource[resource_key]["actions"].append(event.action.value)

        # By day
        day = event.timestamp.date().isoformat()
        events_by_day[day] += 1

    # Top actors (top 10)
    top_actors = sorted(
        [{"actor": k, "count": v} for k, v in events_by_actor.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:10]

    # Top resources (top 10)
    top_resources = sorted(
        [
            {
                "resource": k,
                "resource_type": v["resource_type"],
                "count": v["count"],
                "unique_actions": len(set(v["actions"]))
            }
            for k, v in events_by_resource.items()
        ],
        key=lambda x: x["count"],
        reverse=True
    )[:10]

    # Detect anomalies (simple heuristics)
    anomalies = []

    # Check for unusual spikes
    daily_counts = list(events_by_day.values())
    if daily_counts:
        avg_daily = sum(daily_counts) / len(daily_counts)
        for day, count in events_by_day.items():
            if count > avg_daily * 3:  # 3x average
                anomalies.append({
                    "type": "spike",
                    "date": day,
                    "count": count,
                    "average": avg_daily
                })

    # Check for unusual actor activity
    actor_counts = list(events_by_actor.values())
    if actor_counts:
        avg_actor = sum(actor_counts) / len(actor_counts)
        for actor, count in events_by_actor.items():
            if count > avg_actor * 5:  # 5x average
                anomalies.append({
                    "type": "unusual_actor_activity",
                    "actor": actor,
                    "count": count,
                    "average": avg_actor
                })

    return {
        "organization_id": organization_id,
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        },
        "total_events": len(events),
        "events_by_category": dict(events_by_category),
        "events_by_day": dict(events_by_day),
        "top_actors": top_actors,
        "top_resources": top_resources,
        "anomalies": anomalies
    }


@router.get("/actors/{actor_id}/activity")
async def get_actor_activity(
    actor_id: str,
    organization_id: str = Query(..., description="Organization ID"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    limit: int = Query(1000, le=10000, description="Max events to return")
):
    """
    Get full activity timeline for a specific actor.

    Useful for access reviews and security investigations.

    **Example**:
    ```
    GET /v1/audit/actors/user-123/activity?organization_id=org-123
    ```
    """
    audit_service = get_audit_service()
    if not audit_service:
        raise HTTPException(status_code=503, detail="Audit service not available")

    # Default time range: last 90 days
    if not end_time:
        end_time = datetime.now(timezone.utc)
    if not start_time:
        start_time = end_time - timedelta(days=90)

    # Query events for actor
    filter = AuditEventFilter(
        organization_id=organization_id,
        actor_id=actor_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )

    events = await audit_service.query_events(filter)

    if not events:
        raise HTTPException(status_code=404, detail="No activity found for actor")

    # Aggregate activity stats
    events_by_category = Counter(e.event_category.value for e in events)
    events_by_action = Counter(e.action.value for e in events)
    resources_accessed = Counter(f"{e.resource_type}:{e.resource_id}" for e in events)

    # Top resources (top 10)
    top_resources = [
        {"resource": k, "access_count": v}
        for k, v in resources_accessed.most_common(10)
    ]

    # Timeline (events by day)
    timeline = defaultdict(int)
    for event in events:
        day = event.timestamp.date().isoformat()
        timeline[day] += 1

    return {
        "actor_id": actor_id,
        "actor_type": events[0].actor_type.value if events else None,
        "organization_id": organization_id,
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        },
        "total_events": len(events),
        "events_by_category": dict(events_by_category),
        "events_by_action": dict(events_by_action),
        "first_event": events[0].timestamp.isoformat() if events else None,
        "last_event": events[-1].timestamp.isoformat() if events else None,
        "top_resources": top_resources,
        "timeline": dict(timeline),
        "events": [e.to_dict() for e in events]
    }


# ========== Export Endpoints ==========

@router.post("/export")
async def create_export(request: ExportRequest):
    """
    Create an async export job.

    The export is generated asynchronously and can be downloaded when complete.

    **Example**:
    ```json
    POST /v1/audit/export
    {
      "organization_id": "org-123",
      "start_time": "2024-01-01T00:00:00Z",
      "end_time": "2024-01-31T23:59:59Z",
      "format": "csv",
      "include_verification": true
    }
    ```

    **Response**:
    ```json
    {
      "export_id": "exp_xxx",
      "status": "processing",
      "estimated_size_bytes": null,
      "created_at": "2024-01-15T10:30:00Z"
    }
    ```
    """
    export_service = get_export_service()

    # Build filter from request
    filter_dict = {
        "organization_id": request.organization_id,
        "start_time": request.start_time,
        "end_time": request.end_time,
        "limit": 1000000  # Large limit for exports
    }

    # Add additional filters
    if request.filters:
        filter_dict.update(request.filters)

    filter = AuditEventFilter(**filter_dict)

    # Create export job
    job = await export_service.create_export(
        organization_id=request.organization_id,
        actor_id="current_user",  # TODO: Get from auth context
        filter=filter,
        format=request.format,
        include_verification=request.include_verification,
        encryption_config=request.encryption
    )

    return job.to_dict()


@router.get("/export/{export_id}")
async def get_export_status(export_id: str):
    """
    Get export job status.

    **Example**:
    ```
    GET /v1/audit/export/exp_xxx
    ```

    **Response**:
    ```json
    {
      "export_id": "exp_xxx",
      "status": "completed",
      "file_size_bytes": 15234567,
      "event_count": 1543,
      "completed_at": "2024-01-15T10:35:00Z"
    }
    ```
    """
    export_service = get_export_service()

    job = await export_service.get_export(export_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export not found")

    return job.to_dict()


@router.get("/export/{export_id}/download")
async def download_export(export_id: str):
    """
    Download completed export file.

    **Example**:
    ```
    GET /v1/audit/export/exp_xxx/download
    ```

    Returns the export file with appropriate content type.
    """
    export_service = get_export_service()

    # Get job
    job = await export_service.get_export(export_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export not found")

    if job.status.value != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Export not ready. Status: {job.status.value}"
        )

    # Get file path
    file_path = await export_service.get_export_file(export_id)

    if not file_path:
        raise HTTPException(status_code=404, detail="Export file not found")

    # Determine content type
    content_type_map = {
        "json": "application/json",
        "csv": "text/csv",
        "parquet": "application/octet-stream"
    }

    content_type = content_type_map.get(job.format.value, "application/octet-stream")

    # Return file
    return FileResponse(
        path=str(file_path),
        media_type=content_type,
        filename=f"audit_export_{export_id}.{job.format.value}"
    )


# ========== WebSocket Streaming ==========

class ConnectionManager:
    """Manage WebSocket connections for real-time streaming."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Connection closed
                pass


_connection_manager = ConnectionManager()


@router.websocket("/stream")
async def audit_stream(websocket: WebSocket):
    """
    Real-time audit event stream via WebSocket.

    Clients can subscribe to audit events and receive them in real-time
    as they are captured.

    **Usage**:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/v1/audit/stream');

    ws.onmessage = (event) => {
      const auditEvent = JSON.parse(event.data);
      console.log('New audit event:', auditEvent);
    };
    ```

    **Message Format**:
    ```json
    {
      "event_id": "evt-123",
      "event_type": "trace.deleted",
      "timestamp": "2024-01-15T10:30:00Z",
      "actor_id": "user-456",
      ...
    }
    ```
    """
    await _connection_manager.connect(websocket)

    try:
        # Keep connection alive and listen for filter updates
        while True:
            data = await websocket.receive_text()

            # Client can send filter preferences
            # For now, just acknowledge
            await websocket.send_json({"status": "connected"})

    except WebSocketDisconnect:
        _connection_manager.disconnect(websocket)


async def broadcast_audit_event(event: AuditEvent):
    """
    Broadcast audit event to all connected WebSocket clients.

    This should be called from the audit service when new events are captured.
    """
    await _connection_manager.broadcast(event.to_dict())


# ========== Health Check ==========

@router.get("/health")
async def audit_api_health():
    """
    Health check for audit API.

    Returns status of all components.
    """
    audit_service = get_audit_service()
    export_service = get_export_service()

    return {
        "status": "healthy",
        "components": {
            "audit_service": "available" if audit_service else "unavailable",
            "export_service": "available" if export_service else "unavailable",
            "websocket_connections": len(_connection_manager.active_connections)
        }
    }
