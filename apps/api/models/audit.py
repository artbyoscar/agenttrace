"""
Audit Event Models for Enterprise Compliance

This module defines the immutable audit trail system for capturing all
significant events in the AgentTrace platform for compliance and security purposes.
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4


class ActorType(str, Enum):
    """Type of actor performing the action."""
    USER = "user"
    SERVICE = "service"
    SYSTEM = "system"


class EventCategory(str, Enum):
    """High-level category of the audit event."""
    AUTH = "auth"
    DATA = "data"
    CONFIG = "config"
    ADMIN = "admin"
    EVAL = "eval"


class Severity(str, Enum):
    """Severity level of the audit event."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Action(str, Enum):
    """Action performed on the resource."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"


# Event type constants organized by category
class AuthEventTypes:
    """Authentication and authorization event types."""
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    SSO_INITIATED = "sso.initiated"
    SSO_COMPLETED = "sso.completed"
    SSO_FAILED = "sso.failed"
    TOKEN_REFRESHED = "token.refreshed"
    PASSWORD_CHANGED = "password.changed"
    PASSWORD_RESET = "password.reset"


class DataEventTypes:
    """Data access and manipulation event types."""
    TRACE_CREATED = "trace.created"
    TRACE_VIEWED = "trace.viewed"
    TRACE_EXPORTED = "trace.exported"
    TRACE_DELETED = "trace.deleted"
    TRACE_SHARED = "trace.shared"
    EVALUATION_CREATED = "evaluation.created"
    EVALUATION_VIEWED = "evaluation.viewed"
    EVALUATION_DELETED = "evaluation.deleted"
    DATASET_CREATED = "dataset.created"
    DATASET_UPDATED = "dataset.updated"
    DATASET_DELETED = "dataset.deleted"


class ConfigEventTypes:
    """Configuration change event types."""
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    RETENTION_POLICY_UPDATED = "retention_policy.updated"
    EVALUATOR_CREATED = "evaluator.created"
    EVALUATOR_UPDATED = "evaluator.updated"
    EVALUATOR_DELETED = "evaluator.deleted"
    TEST_SUITE_CREATED = "test_suite.created"
    TEST_SUITE_UPDATED = "test_suite.updated"
    TEST_SUITE_DELETED = "test_suite.deleted"
    ALERT_RULE_CREATED = "alert_rule.created"
    ALERT_RULE_UPDATED = "alert_rule.updated"
    ALERT_RULE_DELETED = "alert_rule.deleted"


class AdminEventTypes:
    """Administrative event types."""
    USER_INVITED = "user.invited"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_REMOVED = "user.removed"
    USER_SUSPENDED = "user.suspended"
    USER_REACTIVATED = "user.reactivated"
    ORGANIZATION_SETTINGS_UPDATED = "organization.settings_updated"
    BILLING_PLAN_CHANGED = "billing.plan_changed"
    COMPLIANCE_EXPORT_REQUESTED = "compliance.export_requested"
    AUDIT_LOG_VIEWED = "audit_log.viewed"
    AUDIT_LOG_EXPORTED = "audit_log.exported"


class EvalEventTypes:
    """Evaluation event types."""
    EVALUATION_STARTED = "evaluation.started"
    EVALUATION_COMPLETED = "evaluation.completed"
    EVALUATION_FAILED = "evaluation.failed"
    BASELINE_UPDATED = "baseline.updated"
    BENCHMARK_STARTED = "benchmark.started"
    BENCHMARK_COMPLETED = "benchmark.completed"


@dataclass
class AuditEvent:
    """
    Immutable audit event for compliance tracking.

    This class represents a single audit event in the system. Events are
    cryptographically chained together using SHA-256 hashes to ensure
    immutability and detect tampering.

    Attributes:
        event_id: UUID v7 (time-ordered) identifier
        timestamp: UTC timestamp when event occurred
        organization_id: Organization identifier
        project_id: Optional project identifier

        actor_type: Type of actor (USER, SERVICE, SYSTEM)
        actor_id: Unique identifier for the actor
        actor_email: Email address for user actors
        actor_ip: Source IP address
        actor_user_agent: Browser or client information

        event_category: High-level category (AUTH, DATA, CONFIG, ADMIN, EVAL)
        event_type: Specific event type (e.g., "trace.deleted")
        event_severity: Severity level (INFO, WARNING, CRITICAL)

        resource_type: Type of resource affected
        resource_id: Unique identifier for the resource
        resource_name: Human-readable resource name

        action: Action performed (CREATE, READ, UPDATE, DELETE, EXPORT)
        previous_state: State before the action (for updates/deletes)
        new_state: State after the action (for creates/updates)

        request_id: Correlation ID for request tracking
        session_id: Session identifier

        hash: SHA-256 hash of event content
        previous_hash: Hash of previous event (blockchain-style chaining)
    """

    # Event identification
    event_id: str
    timestamp: datetime
    organization_id: str
    project_id: Optional[str] = None

    # Actor information
    actor_type: ActorType = ActorType.SYSTEM
    actor_id: str = "system"
    actor_email: Optional[str] = None
    actor_ip: Optional[str] = None
    actor_user_agent: Optional[str] = None

    # Event classification
    event_category: EventCategory = EventCategory.DATA
    event_type: str = ""
    event_severity: Severity = Severity.INFO

    # Resource information
    resource_type: str = ""
    resource_id: str = ""
    resource_name: Optional[str] = None

    # Change details
    action: Action = Action.READ
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None

    # Request context
    request_id: str = ""
    session_id: Optional[str] = None

    # Integrity
    hash: str = field(default="", init=False)
    previous_hash: str = ""

    def __post_init__(self):
        """Validate and initialize the audit event."""
        # Generate event_id if not provided
        if not self.event_id:
            # Note: Python's uuid4() can be replaced with uuid7 when available in Python 3.12+
            self.event_id = str(uuid4())

        # Ensure timestamp is UTC
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)

        # Generate request_id if not provided
        if not self.request_id:
            self.request_id = str(uuid4())

        # Compute hash after all fields are set
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """
        Compute SHA-256 hash of event content for integrity verification.

        The hash includes all event data except the hash field itself,
        creating a cryptographic fingerprint of the event.

        Returns:
            Hexadecimal SHA-256 hash string
        """
        # Create a copy of the event data without the hash field
        event_data = asdict(self)
        event_data.pop('hash', None)

        # Convert datetime to ISO format for consistent hashing
        if isinstance(event_data['timestamp'], datetime):
            event_data['timestamp'] = event_data['timestamp'].isoformat()

        # Convert enums to their string values
        for key, value in event_data.items():
            if isinstance(value, Enum):
                event_data[key] = value.value

        # Create deterministic JSON string (sorted keys)
        json_str = json.dumps(event_data, sort_keys=True, default=str)

        # Compute SHA-256 hash
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def verify_hash(self) -> bool:
        """
        Verify the integrity of the event by recomputing its hash.

        Returns:
            True if the stored hash matches the computed hash
        """
        return self.hash == self._compute_hash()

    def verify_chain(self, previous_event: Optional['AuditEvent']) -> bool:
        """
        Verify the blockchain-style chain to the previous event.

        Args:
            previous_event: The event that should precede this one

        Returns:
            True if the chain is valid
        """
        if previous_event is None:
            # First event in chain should have empty previous_hash
            return self.previous_hash == ""

        return self.previous_hash == previous_event.hash

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the audit event to a dictionary.

        Returns:
            Dictionary representation of the event
        """
        data = asdict(self)

        # Convert datetime to ISO format
        if isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat()

        # Convert enums to their string values
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """
        Create an AuditEvent from a dictionary.

        Args:
            data: Dictionary containing event data

        Returns:
            AuditEvent instance
        """
        # Convert string timestamp to datetime
        if isinstance(data.get('timestamp'), str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])

        # Convert string enums to enum instances
        if isinstance(data.get('actor_type'), str):
            data['actor_type'] = ActorType(data['actor_type'])
        if isinstance(data.get('event_category'), str):
            data['event_category'] = EventCategory(data['event_category'])
        if isinstance(data.get('event_severity'), str):
            data['event_severity'] = Severity(data['event_severity'])
        if isinstance(data.get('action'), str):
            data['action'] = Action(data['action'])

        return cls(**data)

    def __repr__(self) -> str:
        """String representation of the audit event."""
        return (
            f"AuditEvent(event_id='{self.event_id}', "
            f"timestamp={self.timestamp.isoformat()}, "
            f"actor={self.actor_type.value}:{self.actor_id}, "
            f"event={self.event_category.value}:{self.event_type}, "
            f"resource={self.resource_type}:{self.resource_id}, "
            f"action={self.action.value})"
        )


@dataclass
class AuditEventFilter:
    """
    Filter criteria for querying audit events.

    All filter fields are optional. When multiple filters are specified,
    they are combined with AND logic.
    """

    organization_id: Optional[str] = None
    project_id: Optional[str] = None

    actor_type: Optional[ActorType] = None
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None

    event_category: Optional[EventCategory] = None
    event_type: Optional[str] = None
    event_severity: Optional[Severity] = None

    resource_type: Optional[str] = None
    resource_id: Optional[str] = None

    action: Optional[Action] = None

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    limit: int = 100
    offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary, excluding None values."""
        data = asdict(self)

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        # Convert datetime to ISO format
        if 'start_time' in data and isinstance(data['start_time'], datetime):
            data['start_time'] = data['start_time'].isoformat()
        if 'end_time' in data and isinstance(data['end_time'], datetime):
            data['end_time'] = data['end_time'].isoformat()

        # Convert enums to their string values
        for key, value in data.items():
            if isinstance(value, Enum):
                data[key] = value.value

        return data
