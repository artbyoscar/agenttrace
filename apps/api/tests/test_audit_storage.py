"""
Tests for audit storage backends.
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
    Severity,
    Action,
)
from ..services.audit_storage import LocalAuditStorage


@pytest.fixture
def temp_audit_dir():
    """Create a temporary directory for audit logs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def storage(temp_audit_dir):
    """Create a LocalAuditStorage instance."""
    return LocalAuditStorage(base_path=temp_audit_dir)


@pytest.fixture
def sample_event():
    """Create a sample audit event."""
    return AuditEvent(
        event_id="test-event-123",
        timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        project_id="proj-456",
        actor_type=ActorType.USER,
        actor_id="user-789",
        actor_email="test@example.com",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-abc",
        action=Action.CREATE,
        request_id="req-123"
    )


@pytest.mark.asyncio
async def test_write_event(storage, sample_event):
    """Test writing a single audit event."""
    result = await storage.write_event(sample_event)

    assert result is True

    # Verify file was created
    event_path = storage._get_event_path(
        sample_event.organization_id,
        sample_event.event_id,
        sample_event.timestamp
    )
    assert event_path.exists()


@pytest.mark.asyncio
async def test_write_event_prevent_overwrite(storage, sample_event):
    """Test that events cannot be overwritten (WORM)."""
    # Write first time
    result1 = await storage.write_event(sample_event)
    assert result1 is True

    # Try to write again
    result2 = await storage.write_event(sample_event)
    assert result2 is False  # Should fail to prevent overwrite


@pytest.mark.asyncio
async def test_write_events_batch(storage):
    """Test batch writing of events."""
    events = []
    for i in range(5):
        event = AuditEvent(
            event_id=f"event-{i}",
            timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE,
            request_id=f"req-{i}"
        )
        events.append(event)

    result = await storage.write_events_batch(events)

    assert result == 5  # All events should be written


@pytest.mark.asyncio
async def test_read_event(storage, sample_event):
    """Test reading a single audit event."""
    # Write event
    await storage.write_event(sample_event)

    # Read it back
    retrieved = await storage.read_event(sample_event.event_id)

    assert retrieved is not None
    assert retrieved.event_id == sample_event.event_id
    assert retrieved.organization_id == sample_event.organization_id
    assert retrieved.resource_id == sample_event.resource_id


@pytest.mark.asyncio
async def test_read_nonexistent_event(storage):
    """Test reading an event that doesn't exist."""
    retrieved = await storage.read_event("nonexistent-id")
    assert retrieved is None


@pytest.mark.asyncio
async def test_query_events_by_organization(storage):
    """Test querying events by organization."""
    # Create events for different organizations
    for org_id in ["org-1", "org-2"]:
        for i in range(3):
            event = AuditEvent(
                event_id=f"{org_id}-event-{i}",
                timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
                organization_id=org_id,
                event_category=EventCategory.DATA,
                event_type="trace.created",
                resource_type="trace",
                resource_id=f"trace-{i}",
                action=Action.CREATE,
                request_id=f"req-{i}"
            )
            await storage.write_event(event)

    # Query for org-1
    filter = AuditEventFilter(organization_id="org-1", limit=10)
    events = await storage.query_events(filter)

    assert len(events) == 3
    assert all(e.organization_id == "org-1" for e in events)


@pytest.mark.asyncio
async def test_query_events_by_category(storage):
    """Test querying events by category."""
    # Create events with different categories
    categories = [EventCategory.AUTH, EventCategory.DATA, EventCategory.CONFIG]

    for i, category in enumerate(categories * 2):  # 2 of each
        event = AuditEvent(
            event_id=f"event-{i}",
            timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
            organization_id="org-123",
            event_category=category,
            event_type=f"test.{category.value}",
            resource_type="test",
            resource_id=f"res-{i}",
            action=Action.CREATE,
            request_id=f"req-{i}"
        )
        await storage.write_event(event)

    # Query for DATA category
    filter = AuditEventFilter(
        organization_id="org-123",
        event_category=EventCategory.DATA,
        limit=10
    )
    events = await storage.query_events(filter)

    assert len(events) == 2
    assert all(e.event_category == EventCategory.DATA for e in events)


@pytest.mark.asyncio
async def test_query_events_by_time_range(storage):
    """Test querying events by time range."""
    # Create events across different times
    base_time = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)

    for i in range(10):
        event = AuditEvent(
            event_id=f"event-{i}",
            timestamp=base_time + timedelta(hours=i),
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE,
            request_id=f"req-{i}"
        )
        await storage.write_event(event)

    # Query for events between hour 3 and hour 7
    filter = AuditEventFilter(
        organization_id="org-123",
        start_time=base_time + timedelta(hours=3),
        end_time=base_time + timedelta(hours=7),
        limit=10
    )
    events = await storage.query_events(filter)

    assert len(events) == 5  # Hours 3, 4, 5, 6, 7


@pytest.mark.asyncio
async def test_query_events_pagination(storage):
    """Test pagination of query results."""
    # Create 25 events
    for i in range(25):
        event = AuditEvent(
            event_id=f"event-{i:02d}",
            timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE,
            request_id=f"req-{i}"
        )
        await storage.write_event(event)

    # Get first page
    filter1 = AuditEventFilter(organization_id="org-123", limit=10, offset=0)
    page1 = await storage.query_events(filter1)
    assert len(page1) == 10

    # Get second page
    filter2 = AuditEventFilter(organization_id="org-123", limit=10, offset=10)
    page2 = await storage.query_events(filter2)
    assert len(page2) == 10

    # Get third page
    filter3 = AuditEventFilter(organization_id="org-123", limit=10, offset=20)
    page3 = await storage.query_events(filter3)
    assert len(page3) == 5

    # Verify no overlap
    page1_ids = {e.event_id for e in page1}
    page2_ids = {e.event_id for e in page2}
    assert len(page1_ids & page2_ids) == 0


@pytest.mark.asyncio
async def test_verify_integrity_empty(storage):
    """Test integrity verification with no events."""
    result = await storage.verify_integrity("org-123")

    assert result["valid"] is True
    assert result["total_events"] == 0
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_verify_integrity_valid_chain(storage):
    """Test integrity verification with valid event chain."""
    # Create a chain of events
    previous_hash = ""

    for i in range(5):
        event = AuditEvent(
            event_id=f"event-{i}",
            timestamp=datetime(2024, 1, 15, 10, i, 0, tzinfo=timezone.utc),
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE,
            request_id=f"req-{i}",
            previous_hash=previous_hash
        )
        await storage.write_event(event)
        previous_hash = event.hash

    # Verify integrity
    result = await storage.verify_integrity("org-123")

    assert result["valid"] is True
    assert result["total_events"] == 5
    assert result["verified_events"] == 5
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_verify_integrity_broken_chain(storage):
    """Test integrity verification with broken chain."""
    # Create first event
    event1 = AuditEvent(
        event_id="event-1",
        timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-1",
        action=Action.CREATE,
        request_id="req-1",
        previous_hash=""
    )
    await storage.write_event(event1)

    # Create second event with wrong previous_hash
    event2 = AuditEvent(
        event_id="event-2",
        timestamp=datetime(2024, 1, 15, 10, 1, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-2",
        action=Action.CREATE,
        request_id="req-2",
        previous_hash="wrong-hash"  # Intentionally wrong
    )
    await storage.write_event(event2)

    # Verify integrity
    result = await storage.verify_integrity("org-123")

    assert result["valid"] is False
    assert result["total_events"] == 2
    assert len(result["errors"]) == 1
    assert "chain verification failed" in result["errors"][0]["error"].lower()


@pytest.mark.asyncio
async def test_event_path_organization(storage):
    """Test that events are organized by organization and date."""
    event = AuditEvent(
        event_id="test-123",
        timestamp=datetime(2024, 3, 15, 10, 30, 0, tzinfo=timezone.utc),
        organization_id="org-abc",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-123",
        action=Action.CREATE,
        request_id="req-123"
    )

    path = storage._get_event_path(
        event.organization_id,
        event.event_id,
        event.timestamp
    )

    # Verify path structure
    assert "org-abc" in str(path)
    assert "2024" in str(path)
    assert "03" in str(path)
    assert "15" in str(path)
    assert "test-123.json" in str(path)
