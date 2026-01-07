"""
Tests for audit service.
"""

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timezone

from ..models.audit import (
    AuditEvent,
    AuditEventFilter,
    ActorType,
    EventCategory,
    Severity,
    Action,
)
from ..services.audit_storage import LocalAuditStorage
from ..services.audit import AuditService


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
async def audit_service(storage):
    """Create an AuditService instance."""
    service = AuditService(
        storage=storage,
        batch_size=10,
        batch_interval=0.1,  # Short interval for testing
        enable_deduplication=True,
        deduplication_window=5
    )
    await service.start()
    yield service
    await service.stop()


@pytest.mark.asyncio
async def test_service_start_stop(storage):
    """Test starting and stopping the audit service."""
    service = AuditService(storage=storage)

    assert service._running is False

    await service.start()
    assert service._running is True

    await service.stop()
    assert service._running is False


@pytest.mark.asyncio
async def test_capture_event(audit_service):
    """Test capturing a single audit event."""
    event_id = await audit_service.capture_event(
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-123",
        action=Action.CREATE,
        actor_type=ActorType.USER,
        actor_id="user-789",
        actor_email="test@example.com"
    )

    assert event_id is not None

    # Wait for batch processing
    await asyncio.sleep(0.2)

    # Verify event was written
    filter = AuditEventFilter(organization_id="org-123")
    events = await audit_service.query_events(filter)

    assert len(events) == 1
    assert events[0].resource_id == "trace-123"
    assert events[0].actor_email == "test@example.com"


@pytest.mark.asyncio
async def test_capture_multiple_events(audit_service):
    """Test capturing multiple events."""
    event_ids = []

    for i in range(5):
        event_id = await audit_service.capture_event(
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE
        )
        event_ids.append(event_id)

    assert len(event_ids) == 5

    # Wait for batch processing
    await asyncio.sleep(0.2)

    # Verify all events were written
    filter = AuditEventFilter(organization_id="org-123")
    events = await audit_service.query_events(filter)

    assert len(events) == 5


@pytest.mark.asyncio
async def test_event_chain_maintenance(audit_service):
    """Test that events are properly chained."""
    # Capture events for the same organization
    for i in range(3):
        await audit_service.capture_event(
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE
        )

    # Wait for batch processing
    await asyncio.sleep(0.2)

    # Verify chain integrity
    result = await audit_service.verify_integrity("org-123")

    assert result["valid"] is True
    assert result["total_events"] == 3


@pytest.mark.asyncio
async def test_batch_processing(audit_service):
    """Test batch processing of events."""
    # Set small batch size
    audit_service.batch_size = 3

    # Capture events
    for i in range(5):
        await audit_service.capture_event(
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE
        )

    # First batch should flush automatically (3 events)
    await asyncio.sleep(0.1)

    # Check that events are being processed
    filter = AuditEventFilter(organization_id="org-123")
    events = await audit_service.query_events(filter)

    # Should have at least the first batch
    assert len(events) >= 3

    # Wait for remaining events
    await asyncio.sleep(0.2)

    events = await audit_service.query_events(filter)
    assert len(events) == 5


@pytest.mark.asyncio
async def test_deduplication(audit_service):
    """Test event deduplication."""
    # Capture same event twice quickly
    event_id1 = await audit_service.capture_event(
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.viewed",
        resource_type="trace",
        resource_id="trace-123",
        action=Action.READ
    )

    event_id2 = await audit_service.capture_event(
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.viewed",
        resource_type="trace",
        resource_id="trace-123",
        action=Action.READ
    )

    # Both should return event IDs
    assert event_id1 is not None
    assert event_id2 is not None

    # Wait for batch processing
    await asyncio.sleep(0.2)

    # Only one event should be stored (deduplicated)
    filter = AuditEventFilter(organization_id="org-123")
    events = await audit_service.query_events(filter)

    assert len(events) == 1


@pytest.mark.asyncio
async def test_deduplication_different_resources(audit_service):
    """Test that deduplication works per resource."""
    # Capture events for different resources
    await audit_service.capture_event(
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.viewed",
        resource_type="trace",
        resource_id="trace-1",
        action=Action.READ
    )

    await audit_service.capture_event(
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.viewed",
        resource_type="trace",
        resource_id="trace-2",  # Different resource
        action=Action.READ
    )

    # Wait for batch processing
    await asyncio.sleep(0.2)

    # Both should be stored (different resources)
    filter = AuditEventFilter(organization_id="org-123")
    events = await audit_service.query_events(filter)

    assert len(events) == 2


@pytest.mark.asyncio
async def test_enrichment_callback(audit_service):
    """Test event enrichment via callback."""
    # Define enrichment callback
    def enrich_event(event: AuditEvent) -> AuditEvent:
        # Add metadata
        if event.new_state is None:
            event.new_state = {}
        event.new_state["enriched"] = True
        event.new_state["version"] = "1.0"
        return event

    # Add callback
    audit_service.add_enrichment_callback(enrich_event)

    # Capture event
    await audit_service.capture_event(
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-123",
        action=Action.CREATE
    )

    # Wait for processing
    await asyncio.sleep(0.2)

    # Verify enrichment
    filter = AuditEventFilter(organization_id="org-123")
    events = await audit_service.query_events(filter)

    assert len(events) == 1
    assert events[0].new_state is not None
    assert events[0].new_state.get("enriched") is True
    assert events[0].new_state.get("version") == "1.0"


@pytest.mark.asyncio
async def test_capture_with_state(audit_service):
    """Test capturing events with previous and new state."""
    previous_state = {"name": "Old Name", "status": "active"}
    new_state = {"name": "New Name", "status": "archived"}

    await audit_service.capture_event(
        organization_id="org-123",
        event_category=EventCategory.CONFIG,
        event_type="project.updated",
        resource_type="project",
        resource_id="proj-123",
        action=Action.UPDATE,
        previous_state=previous_state,
        new_state=new_state
    )

    # Wait for processing
    await asyncio.sleep(0.2)

    # Verify states were captured
    filter = AuditEventFilter(organization_id="org-123")
    events = await audit_service.query_events(filter)

    assert len(events) == 1
    assert events[0].previous_state == previous_state
    assert events[0].new_state == new_state


@pytest.mark.asyncio
async def test_query_with_filters(audit_service):
    """Test querying events with various filters."""
    # Create diverse events
    await audit_service.capture_event(
        organization_id="org-1",
        project_id="proj-1",
        event_category=EventCategory.DATA,
        event_type="trace.created",
        resource_type="trace",
        resource_id="trace-1",
        action=Action.CREATE,
        actor_type=ActorType.USER,
        actor_id="user-1"
    )

    await audit_service.capture_event(
        organization_id="org-1",
        project_id="proj-2",
        event_category=EventCategory.AUTH,
        event_type="user.login",
        resource_type="user",
        resource_id="user-2",
        action=Action.READ,
        actor_type=ActorType.SERVICE,
        actor_id="service-1"
    )

    # Wait for processing
    await asyncio.sleep(0.2)

    # Filter by project
    filter1 = AuditEventFilter(organization_id="org-1", project_id="proj-1")
    events1 = await audit_service.query_events(filter1)
    assert len(events1) == 1
    assert events1[0].project_id == "proj-1"

    # Filter by category
    filter2 = AuditEventFilter(organization_id="org-1", event_category=EventCategory.AUTH)
    events2 = await audit_service.query_events(filter2)
    assert len(events2) == 1
    assert events2[0].event_category == EventCategory.AUTH

    # Filter by actor type
    filter3 = AuditEventFilter(organization_id="org-1", actor_type=ActorType.USER)
    events3 = await audit_service.query_events(filter3)
    assert len(events3) == 1
    assert events3[0].actor_type == ActorType.USER


@pytest.mark.asyncio
async def test_export_events_json(audit_service):
    """Test exporting events as JSON."""
    # Create events
    for i in range(3):
        await audit_service.capture_event(
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE
        )

    # Wait for processing
    await asyncio.sleep(0.2)

    # Export as JSON
    filter = AuditEventFilter(organization_id="org-123")
    export_data = await audit_service.export_events(filter, format="json")

    assert export_data is not None
    assert len(export_data) > 0
    assert "trace-0" in export_data
    assert "trace-1" in export_data
    assert "trace-2" in export_data


@pytest.mark.asyncio
async def test_export_events_csv(audit_service):
    """Test exporting events as CSV."""
    # Create events
    for i in range(2):
        await audit_service.capture_event(
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE
        )

    # Wait for processing
    await asyncio.sleep(0.2)

    # Export as CSV
    filter = AuditEventFilter(organization_id="org-123")
    export_data = await audit_service.export_events(filter, format="csv")

    assert export_data is not None
    assert len(export_data) > 0
    assert "event_id" in export_data  # CSV header
    assert "trace-0" in export_data
    assert "trace-1" in export_data


@pytest.mark.asyncio
async def test_flush_on_stop(storage):
    """Test that events are flushed when service stops."""
    service = AuditService(
        storage=storage,
        batch_size=100,  # Large batch to prevent auto-flush
        batch_interval=10.0  # Long interval
    )
    await service.start()

    # Capture events
    for i in range(5):
        await service.capture_event(
            organization_id="org-123",
            event_category=EventCategory.DATA,
            event_type="trace.created",
            resource_type="trace",
            resource_id=f"trace-{i}",
            action=Action.CREATE
        )

    # Stop service (should flush)
    await service.stop()

    # Verify events were written
    filter = AuditEventFilter(organization_id="org-123")
    events = await storage.query_events(filter)

    assert len(events) == 5
