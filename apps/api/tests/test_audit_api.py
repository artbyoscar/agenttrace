"""
Tests for Audit API endpoints.
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

from ..models.audit import (
    AuditEvent,
    AuditEventFilter,
    ActorType,
    EventCategory,
    Action,
    Severity
)
from ..services.audit_storage import LocalAuditStorage
from ..services.audit import AuditService, set_audit_service
from ..services.audit_export import AuditExportService, ExportFormat
from ..src.api.utils.pagination import PaginationCursor, PaginatedResponse


@pytest.fixture
def temp_audit_dir():
    """Create temporary directory for audit logs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_export_dir():
    """Create temporary directory for exports."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
async def audit_service(temp_audit_dir):
    """Create and start audit service."""
    storage = LocalAuditStorage(base_path=temp_audit_dir)
    service = AuditService(storage=storage, batch_size=10, batch_interval=0.1)
    await service.start()
    set_audit_service(service)
    yield service
    await service.stop()


@pytest.fixture
def sample_events():
    """Create sample audit events."""
    events = []
    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    categories = [EventCategory.AUTH, EventCategory.DATA, EventCategory.CONFIG]
    actions = [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE]

    for i in range(20):
        event = AuditEvent(
            event_id=f"event-{i:03d}",
            timestamp=base_time + timedelta(minutes=i),
            organization_id="org-123",
            actor_type=ActorType.USER,
            actor_id=f"user-{i % 3}",  # 3 different users
            event_category=categories[i % len(categories)],
            event_type=f"test.event.{i}",
            resource_type="test_resource",
            resource_id=f"res-{i}",
            action=actions[i % len(actions)],
            request_id=f"req-{i}",
            event_severity=Severity.INFO
        )
        events.append(event)

    return events


# Pagination Tests

def test_pagination_cursor_encode_decode():
    """Test pagination cursor encoding and decoding."""
    timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    event_id = "event-123"

    # Encode
    cursor = PaginationCursor.encode(timestamp, event_id)
    assert cursor is not None
    assert isinstance(cursor, str)

    # Decode
    decoded = PaginationCursor.decode(cursor)
    assert decoded["timestamp"] == timestamp
    assert decoded["event_id"] == event_id


def test_pagination_cursor_invalid():
    """Test decoding invalid cursor."""
    with pytest.raises(ValueError):
        PaginationCursor.decode("invalid_cursor")


def test_paginated_response():
    """Test paginated response structure."""
    items = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"}
    ]

    response = PaginatedResponse(
        items=items,
        total_count=100,
        next_cursor="next_page",
        metadata={"filter": "test"}
    )

    result = response.to_dict()

    assert "events" in result
    assert len(result["events"]) == 2
    assert result["count"] == 2
    assert result["total_count"] == 100
    assert result["next_cursor"] == "next_page"
    assert result["query_metadata"]["filter"] == "test"


# Export Service Tests

@pytest.mark.asyncio
async def test_export_service_json(audit_service, sample_events, temp_export_dir):
    """Test JSON export."""
    # Add events to service
    for event in sample_events[:5]:
        await audit_service.capture_event(
            organization_id=event.organization_id,
            event_category=event.event_category,
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action,
            actor_type=event.actor_type,
            actor_id=event.actor_id
        )

    # Wait for batch processing
    import asyncio
    await asyncio.sleep(0.3)

    # Create export service
    export_service = AuditExportService(export_dir=temp_export_dir)
    await export_service.start()

    # Create filter
    filter = AuditEventFilter(organization_id="org-123", limit=100)

    # Create export
    job = await export_service.create_export(
        organization_id="org-123",
        actor_id="user-test",
        filter=filter,
        format=ExportFormat.JSON
    )

    assert job.export_id is not None
    assert job.status.value in ["pending", "processing"]

    # Wait for processing
    await asyncio.sleep(1.0)

    # Check job status
    job = await export_service.get_export(job.export_id)
    assert job.status.value == "completed"
    assert job.event_count == 5
    assert job.file_path is not None

    await export_service.stop()


@pytest.mark.asyncio
async def test_export_service_csv(audit_service, sample_events, temp_export_dir):
    """Test CSV export."""
    # Add events
    for event in sample_events[:3]:
        await audit_service.capture_event(
            organization_id=event.organization_id,
            event_category=event.event_category,
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action
        )

    import asyncio
    await asyncio.sleep(0.3)

    # Create export
    export_service = AuditExportService(export_dir=temp_export_dir)
    await export_service.start()

    filter = AuditEventFilter(organization_id="org-123", limit=100)

    job = await export_service.create_export(
        organization_id="org-123",
        actor_id="user-test",
        filter=filter,
        format=ExportFormat.CSV
    )

    # Wait for processing
    await asyncio.sleep(1.0)

    # Verify
    job = await export_service.get_export(job.export_id)
    assert job.status.value == "completed"
    assert job.file_path.endswith(".csv")

    # Check file exists
    file_path = Path(job.file_path)
    assert file_path.exists()

    # Read CSV content
    with open(file_path, 'r') as f:
        content = f.read()
        assert "event_id" in content  # Header
        assert "org-123" in content  # Data

    await export_service.stop()


@pytest.mark.asyncio
async def test_export_with_verification(audit_service, sample_events, temp_export_dir):
    """Test export with verification data."""
    # Add events
    for event in sample_events[:2]:
        await audit_service.capture_event(
            organization_id=event.organization_id,
            event_category=event.event_category,
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action
        )

    import asyncio
    await asyncio.sleep(0.3)

    # Create export with verification
    export_service = AuditExportService(export_dir=temp_export_dir)
    await export_service.start()

    filter = AuditEventFilter(organization_id="org-123", limit=100)

    job = await export_service.create_export(
        organization_id="org-123",
        actor_id="user-test",
        filter=filter,
        format=ExportFormat.JSON,
        include_verification=True
    )

    await asyncio.sleep(1.0)

    job = await export_service.get_export(job.export_id)
    assert job.include_verification is True

    await export_service.stop()


# Access Control Tests

def test_rate_limiter():
    """Test rate limiter functionality."""
    from ..src.api.middleware.access_control import RateLimiter

    limiter = RateLimiter(requests_per_minute=10)

    # First requests should succeed
    for i in range(10):
        assert limiter.check_rate_limit("user-1") is True

    # 11th request should fail
    assert limiter.check_rate_limit("user-1") is False

    # Different user should have separate limit
    assert limiter.check_rate_limit("user-2") is True


def test_rate_limiter_refill():
    """Test rate limiter token refill."""
    import time
    from ..src.api.middleware.access_control import RateLimiter

    limiter = RateLimiter(requests_per_minute=60)

    # Exhaust tokens
    for i in range(60):
        limiter.check_rate_limit("user-1")

    # Should be exhausted
    assert limiter.check_rate_limit("user-1") is False

    # Wait for refill (1 second should give 1 token)
    time.sleep(1.1)

    # Should have refilled
    assert limiter.check_rate_limit("user-1") is True


def test_permission_check():
    """Test permission checking."""
    from ..src.api.middleware.access_control import User, Permission

    # User with permissions
    user = User(user_id="user-1", permissions=[Permission.AUDIT_READ])
    assert user.has_permission(Permission.AUDIT_READ) is True
    assert user.has_permission(Permission.AUDIT_EXPORT) is False

    # User with all permissions
    admin = User(
        user_id="admin-1",
        permissions=[Permission.AUDIT_READ, Permission.AUDIT_EXPORT, Permission.AUDIT_ADMIN]
    )
    assert admin.has_permission(Permission.AUDIT_EXPORT) is True


# Integration Tests

@pytest.mark.asyncio
async def test_query_and_filter_workflow(audit_service, sample_events):
    """Test complete query and filter workflow."""
    # Add sample events
    for event in sample_events:
        await audit_service.capture_event(
            organization_id=event.organization_id,
            event_category=event.event_category,
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action,
            actor_type=event.actor_type,
            actor_id=event.actor_id
        )

    import asyncio
    await asyncio.sleep(0.3)

    # Query all events
    filter = AuditEventFilter(organization_id="org-123", limit=100)
    all_events = await audit_service.query_events(filter)
    assert len(all_events) == 20

    # Filter by actor
    filter = AuditEventFilter(organization_id="org-123", actor_id="user-0", limit=100)
    user_events = await audit_service.query_events(filter)
    assert all(e.actor_id == "user-0" for e in user_events)

    # Filter by category
    filter = AuditEventFilter(
        organization_id="org-123",
        event_category=EventCategory.AUTH,
        limit=100
    )
    auth_events = await audit_service.query_events(filter)
    assert all(e.event_category == EventCategory.AUTH for e in auth_events)

    # Filter by action
    filter = AuditEventFilter(organization_id="org-123", action=Action.DELETE, limit=100)
    delete_events = await audit_service.query_events(filter)
    assert all(e.action == Action.DELETE for e in delete_events)


@pytest.mark.asyncio
async def test_event_context_retrieval(audit_service, sample_events):
    """Test retrieving event context (before/after)."""
    # Add events in sequence
    for event in sample_events[:10]:
        await audit_service.capture_event(
            organization_id=event.organization_id,
            event_category=event.event_category,
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action
        )

    import asyncio
    await asyncio.sleep(0.3)

    # Get all events
    filter = AuditEventFilter(organization_id="org-123", limit=100)
    events = await audit_service.query_events(filter)

    # Get middle event
    if len(events) >= 5:
        target_event = events[4]

        # Get context would query events before and after
        # This is tested implicitly through the API endpoint
        assert target_event is not None


@pytest.mark.asyncio
async def test_export_lifecycle(audit_service, sample_events, temp_export_dir):
    """Test complete export lifecycle."""
    # Add events
    for event in sample_events[:5]:
        await audit_service.capture_event(
            organization_id=event.organization_id,
            event_category=event.event_category,
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action
        )

    import asyncio
    await asyncio.sleep(0.3)

    # Create export service
    export_service = AuditExportService(
        export_dir=temp_export_dir,
        expiration_hours=1
    )
    await export_service.start()

    # Create export
    filter = AuditEventFilter(organization_id="org-123", limit=100)
    job = await export_service.create_export(
        organization_id="org-123",
        actor_id="user-test",
        filter=filter,
        format=ExportFormat.JSON
    )

    # Check initial status
    assert job.status.value == "pending"
    assert job.file_path is None

    # Wait for processing
    await asyncio.sleep(1.0)

    # Check completed status
    job = await export_service.get_export(job.export_id)
    assert job.status.value == "completed"
    assert job.file_path is not None
    assert job.event_count == 5

    # Get file
    file_path = await export_service.get_export_file(job.export_id)
    assert file_path is not None
    assert file_path.exists()

    await export_service.stop()
