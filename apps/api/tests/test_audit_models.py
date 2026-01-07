"""
Tests for audit event models.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from ..models.audit import (
    AuditEvent,
    AuditEventFilter,
    ActorType,
    EventCategory,
    Severity,
    Action,
    AuthEventTypes,
    DataEventTypes,
)


def test_audit_event_creation():
    """Test basic audit event creation."""
    event = AuditEvent(
        event_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc),
        organization_id="org-123",
        project_id="proj-456",
        actor_type=ActorType.USER,
        actor_id="user-789",
        actor_email="test@example.com",
        event_category=EventCategory.DATA,
        event_type=DataEventTypes.TRACE_CREATED,
        resource_type="trace",
        resource_id="trace-abc",
        action=Action.CREATE,
        request_id=str(uuid4())
    )

    assert event.event_id is not None
    assert event.organization_id == "org-123"
    assert event.actor_type == ActorType.USER
    assert event.event_category == EventCategory.DATA
    assert event.hash != ""  # Hash should be computed


def test_audit_event_auto_fields():
    """Test that auto-generated fields are set correctly."""
    event = AuditEvent(
        event_id="",  # Should be auto-generated
        timestamp=datetime(2024, 1, 1, 12, 0, 0),  # No timezone
        organization_id="org-123",
        event_category=EventCategory.AUTH,
        event_type=AuthEventTypes.USER_LOGIN,
        resource_type="user",
        resource_id="user-123",
        action=Action.READ,
        request_id=""  # Should be auto-generated
    )

    # Event ID should be generated
    assert event.event_id != ""

    # Timestamp should be converted to UTC
    assert event.timestamp.tzinfo == timezone.utc

    # Request ID should be generated
    assert event.request_id != ""

    # Hash should be computed
    assert event.hash != ""


def test_audit_event_hash_computation():
    """Test that event hash is computed correctly."""
    event = AuditEvent(
        event_id="test-123",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type=DataEventTypes.TRACE_CREATED,
        resource_type="trace",
        resource_id="trace-123",
        action=Action.CREATE,
        request_id="req-123"
    )

    # Hash should be a valid SHA-256 hash (64 hex characters)
    assert len(event.hash) == 64
    assert all(c in '0123456789abcdef' for c in event.hash)


def test_audit_event_hash_verification():
    """Test hash verification."""
    event = AuditEvent(
        event_id="test-123",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type=DataEventTypes.TRACE_CREATED,
        resource_type="trace",
        resource_id="trace-123",
        action=Action.CREATE,
        request_id="req-123"
    )

    # Hash should verify
    assert event.verify_hash() is True

    # Manually change a field (simulating tampering)
    event.resource_id = "trace-456"

    # Hash should no longer verify
    assert event.verify_hash() is False


def test_audit_event_chain_verification():
    """Test blockchain-style chain verification."""
    # Create first event
    event1 = AuditEvent(
        event_id="event-1",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type=DataEventTypes.TRACE_CREATED,
        resource_type="trace",
        resource_id="trace-1",
        action=Action.CREATE,
        request_id="req-1",
        previous_hash=""  # First event in chain
    )

    # First event should verify with no previous event
    assert event1.verify_chain(None) is True

    # Create second event linked to first
    event2 = AuditEvent(
        event_id="event-2",
        timestamp=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type=DataEventTypes.TRACE_VIEWED,
        resource_type="trace",
        resource_id="trace-1",
        action=Action.READ,
        request_id="req-2",
        previous_hash=event1.hash
    )

    # Second event should verify with first event
    assert event2.verify_chain(event1) is True

    # Create third event with wrong previous_hash
    event3 = AuditEvent(
        event_id="event-3",
        timestamp=datetime(2024, 1, 1, 12, 2, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.DATA,
        event_type=DataEventTypes.TRACE_DELETED,
        resource_type="trace",
        resource_id="trace-1",
        action=Action.DELETE,
        request_id="req-3",
        previous_hash="wrong-hash"
    )

    # Third event should NOT verify with second event
    assert event3.verify_chain(event2) is False


def test_audit_event_to_dict():
    """Test conversion to dictionary."""
    event = AuditEvent(
        event_id="test-123",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        actor_type=ActorType.USER,
        event_category=EventCategory.DATA,
        event_type=DataEventTypes.TRACE_CREATED,
        resource_type="trace",
        resource_id="trace-123",
        action=Action.CREATE,
        request_id="req-123"
    )

    data = event.to_dict()

    assert data["event_id"] == "test-123"
    assert data["organization_id"] == "org-123"
    assert data["actor_type"] == "user"  # Should be string value
    assert data["event_category"] == "data"
    assert data["action"] == "create"
    assert "hash" in data


def test_audit_event_from_dict():
    """Test creation from dictionary."""
    data = {
        "event_id": "test-123",
        "timestamp": "2024-01-01T12:00:00+00:00",
        "organization_id": "org-123",
        "project_id": None,
        "actor_type": "user",
        "actor_id": "user-123",
        "actor_email": "test@example.com",
        "actor_ip": None,
        "actor_user_agent": None,
        "event_category": "data",
        "event_type": "trace.created",
        "event_severity": "info",
        "resource_type": "trace",
        "resource_id": "trace-123",
        "resource_name": None,
        "action": "create",
        "previous_state": None,
        "new_state": None,
        "request_id": "req-123",
        "session_id": None,
        "previous_hash": "",
        "hash": ""
    }

    event = AuditEvent.from_dict(data)

    assert event.event_id == "test-123"
    assert event.organization_id == "org-123"
    assert event.actor_type == ActorType.USER
    assert event.event_category == EventCategory.DATA
    assert event.action == Action.CREATE
    assert isinstance(event.timestamp, datetime)


def test_audit_event_with_state():
    """Test audit event with previous and new state."""
    previous = {"name": "Old Name", "value": 100}
    new = {"name": "New Name", "value": 200}

    event = AuditEvent(
        event_id="test-123",
        timestamp=datetime.now(timezone.utc),
        organization_id="org-123",
        event_category=EventCategory.CONFIG,
        event_type="project.updated",
        resource_type="project",
        resource_id="proj-123",
        action=Action.UPDATE,
        previous_state=previous,
        new_state=new,
        request_id="req-123"
    )

    assert event.previous_state == previous
    assert event.new_state == new

    # State should be included in hash
    data = event.to_dict()
    assert data["previous_state"] == previous
    assert data["new_state"] == new


def test_audit_event_filter():
    """Test audit event filter."""
    filter = AuditEventFilter(
        organization_id="org-123",
        project_id="proj-456",
        event_category=EventCategory.DATA,
        action=Action.CREATE,
        limit=50,
        offset=10
    )

    assert filter.organization_id == "org-123"
    assert filter.project_id == "proj-456"
    assert filter.event_category == EventCategory.DATA
    assert filter.action == Action.CREATE
    assert filter.limit == 50
    assert filter.offset == 10


def test_audit_event_filter_to_dict():
    """Test filter conversion to dictionary."""
    filter = AuditEventFilter(
        organization_id="org-123",
        event_category=EventCategory.DATA,
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 31, tzinfo=timezone.utc),
        limit=100
    )

    data = filter.to_dict()

    assert data["organization_id"] == "org-123"
    assert data["event_category"] == "data"
    assert "start_time" in data
    assert "end_time" in data
    assert data["limit"] == 100
    # None values should be excluded
    assert "project_id" not in data


def test_event_type_constants():
    """Test that event type constants are defined."""
    # Auth events
    assert AuthEventTypes.USER_LOGIN == "user.login"
    assert AuthEventTypes.API_KEY_CREATED == "api_key.created"

    # Data events
    assert DataEventTypes.TRACE_CREATED == "trace.created"
    assert DataEventTypes.TRACE_DELETED == "trace.deleted"

    # Config events
    from ..models.audit import ConfigEventTypes
    assert ConfigEventTypes.PROJECT_CREATED == "project.created"

    # Admin events
    from ..models.audit import AdminEventTypes
    assert AdminEventTypes.USER_INVITED == "user.invited"

    # Eval events
    from ..models.audit import EvalEventTypes
    assert EvalEventTypes.EVALUATION_STARTED == "evaluation.started"


def test_audit_event_repr():
    """Test string representation of audit event."""
    event = AuditEvent(
        event_id="test-123",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        organization_id="org-123",
        actor_type=ActorType.USER,
        actor_id="user-789",
        event_category=EventCategory.DATA,
        event_type=DataEventTypes.TRACE_CREATED,
        resource_type="trace",
        resource_id="trace-123",
        action=Action.CREATE,
        request_id="req-123"
    )

    repr_str = repr(event)

    assert "AuditEvent" in repr_str
    assert "test-123" in repr_str
    assert "user:user-789" in repr_str
    assert "data:trace.created" in repr_str
    assert "trace:trace-123" in repr_str
