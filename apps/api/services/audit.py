"""
Audit Event Service

This module provides the main service for capturing, managing, and querying
audit events. It handles async event capture, validation, enrichment,
hash chain maintenance, batch writing, and event deduplication.
"""

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from uuid import uuid4

from ..models.audit import (
    AuditEvent,
    AuditEventFilter,
    ActorType,
    EventCategory,
    Severity,
    Action,
)
from .audit_storage import AuditStorage, LocalAuditStorage


class AuditService:
    """
    Main service for managing audit events.

    This service provides:
    - Async, non-blocking event capture
    - Event validation and enrichment
    - Hash chain maintenance for immutability
    - Batch writing for performance
    - Event deduplication
    - Query and retrieval capabilities
    """

    def __init__(
        self,
        storage: AuditStorage,
        batch_size: int = 100,
        batch_interval: float = 5.0,
        enable_deduplication: bool = True,
        deduplication_window: int = 60
    ):
        """
        Initialize the audit service.

        Args:
            storage: Storage backend for audit events
            batch_size: Number of events to batch before writing
            batch_interval: Time in seconds between batch writes
            enable_deduplication: Whether to deduplicate events
            deduplication_window: Time window in seconds for deduplication
        """
        self.storage = storage
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.enable_deduplication = enable_deduplication
        self.deduplication_window = deduplication_window

        # Event queue for batching
        self._event_queue: List[AuditEvent] = []
        self._queue_lock = asyncio.Lock()

        # Background task for batch processing
        self._batch_task: Optional[asyncio.Task] = None
        self._running = False

        # Hash chain tracking per organization
        self._last_event_hash: Dict[str, str] = {}
        self._hash_lock = asyncio.Lock()

        # Deduplication tracking
        self._recent_events: Dict[str, datetime] = {}
        self._dedup_lock = asyncio.Lock()

        # Enrichment callbacks
        self._enrichment_callbacks: List[Callable[[AuditEvent], AuditEvent]] = []

    async def start(self):
        """Start the audit service background tasks."""
        if self._running:
            return

        self._running = True
        self._batch_task = asyncio.create_task(self._batch_processor())
        print("AuditService: Background batch processor started")

    async def stop(self):
        """Stop the audit service and flush remaining events."""
        if not self._running:
            return

        self._running = False

        if self._batch_task:
            self._batch_task.cancel()
            try:
                await self._batch_task
            except asyncio.CancelledError:
                pass

        # Flush remaining events
        await self._flush_queue()
        print("AuditService: Stopped and flushed remaining events")

    async def _batch_processor(self):
        """Background task that processes event batches periodically."""
        while self._running:
            try:
                await asyncio.sleep(self.batch_interval)
                await self._flush_queue()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"AuditService: Error in batch processor: {e}")

    async def _flush_queue(self):
        """Flush the event queue to storage."""
        async with self._queue_lock:
            if not self._event_queue:
                return

            events_to_write = self._event_queue.copy()
            self._event_queue.clear()

        # Write batch to storage
        try:
            written = await self.storage.write_events_batch(events_to_write)
            if written != len(events_to_write):
                print(f"AuditService: Warning - only {written}/{len(events_to_write)} events written")
        except Exception as e:
            print(f"AuditService: Error writing batch: {e}")
            # TODO: Implement retry logic or dead letter queue

    def add_enrichment_callback(self, callback: Callable[[AuditEvent], AuditEvent]):
        """
        Add a callback function to enrich audit events.

        The callback receives an AuditEvent and returns an enriched AuditEvent.

        Args:
            callback: Function that enriches audit events
        """
        self._enrichment_callbacks.append(callback)

    async def capture_event(
        self,
        organization_id: str,
        event_category: EventCategory,
        event_type: str,
        resource_type: str,
        resource_id: str,
        action: Action,
        actor_type: ActorType = ActorType.SYSTEM,
        actor_id: str = "system",
        actor_email: Optional[str] = None,
        actor_ip: Optional[str] = None,
        actor_user_agent: Optional[str] = None,
        project_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_severity: Severity = Severity.INFO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Capture an audit event asynchronously.

        This is the main method for recording audit events. It performs:
        1. Event creation with auto-generated IDs and timestamps
        2. Deduplication checking
        3. Enrichment via callbacks
        4. Hash chain linking
        5. Queuing for batch write

        Args:
            organization_id: Organization identifier
            event_category: Event category (AUTH, DATA, CONFIG, ADMIN, EVAL)
            event_type: Specific event type (e.g., "trace.deleted")
            resource_type: Type of resource affected
            resource_id: Resource identifier
            action: Action performed (CREATE, READ, UPDATE, DELETE, EXPORT)
            actor_type: Type of actor (USER, SERVICE, SYSTEM)
            actor_id: Actor identifier
            actor_email: Actor email (for users)
            actor_ip: Source IP address
            actor_user_agent: Client user agent
            project_id: Project identifier
            resource_name: Human-readable resource name
            previous_state: State before the action
            new_state: State after the action
            request_id: Correlation ID for request tracking
            session_id: Session identifier
            event_severity: Severity level (INFO, WARNING, CRITICAL)
            metadata: Additional metadata

        Returns:
            The event_id of the captured event
        """
        # Generate event ID and timestamp
        event_id = str(uuid4())
        timestamp = datetime.now(timezone.utc)

        if not request_id:
            request_id = str(uuid4())

        # Get previous hash for chain
        async with self._hash_lock:
            previous_hash = self._last_event_hash.get(organization_id, "")

        # Create event
        event = AuditEvent(
            event_id=event_id,
            timestamp=timestamp,
            organization_id=organization_id,
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_ip=actor_ip,
            actor_user_agent=actor_user_agent,
            event_category=event_category,
            event_type=event_type,
            event_severity=event_severity,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            action=action,
            previous_state=previous_state,
            new_state=new_state,
            request_id=request_id,
            session_id=session_id,
            previous_hash=previous_hash
        )

        # Check for duplicate
        if self.enable_deduplication:
            if await self._is_duplicate(event):
                print(f"AuditService: Duplicate event detected, skipping: {event_id}")
                return event_id

        # Apply enrichment callbacks
        for callback in self._enrichment_callbacks:
            try:
                event = callback(event)
            except Exception as e:
                print(f"AuditService: Error in enrichment callback: {e}")

        # Update hash chain
        async with self._hash_lock:
            self._last_event_hash[organization_id] = event.hash

        # Add to queue
        async with self._queue_lock:
            self._event_queue.append(event)

            # Flush if batch size reached
            if len(self._event_queue) >= self.batch_size:
                asyncio.create_task(self._flush_queue())

        # Track for deduplication
        if self.enable_deduplication:
            await self._track_event(event)

        return event_id

    async def _is_duplicate(self, event: AuditEvent) -> bool:
        """
        Check if an event is a duplicate within the deduplication window.

        Events are considered duplicates if they have the same organization,
        event type, resource, and action within the time window.
        """
        async with self._dedup_lock:
            dedup_key = (
                f"{event.organization_id}:"
                f"{event.event_type}:"
                f"{event.resource_type}:"
                f"{event.resource_id}:"
                f"{event.action.value}"
            )

            if dedup_key in self._recent_events:
                last_time = self._recent_events[dedup_key]
                time_diff = (event.timestamp - last_time).total_seconds()

                if time_diff < self.deduplication_window:
                    return True

            return False

    async def _track_event(self, event: AuditEvent):
        """Track an event for deduplication."""
        async with self._dedup_lock:
            dedup_key = (
                f"{event.organization_id}:"
                f"{event.event_type}:"
                f"{event.resource_type}:"
                f"{event.resource_id}:"
                f"{event.action.value}"
            )

            self._recent_events[dedup_key] = event.timestamp

            # Clean up old entries
            now = datetime.now(timezone.utc)
            keys_to_remove = [
                key for key, timestamp in self._recent_events.items()
                if (now - timestamp).total_seconds() > self.deduplication_window
            ]

            for key in keys_to_remove:
                del self._recent_events[key]

    async def get_event(self, event_id: str) -> Optional[AuditEvent]:
        """
        Retrieve a single audit event by ID.

        Args:
            event_id: The event ID to retrieve

        Returns:
            The audit event if found, None otherwise
        """
        return await self.storage.read_event(event_id)

    async def query_events(self, filter: AuditEventFilter) -> List[AuditEvent]:
        """
        Query audit events based on filter criteria.

        Args:
            filter: Filter criteria for the query

        Returns:
            List of matching audit events
        """
        return await self.storage.query_events(filter)

    async def verify_integrity(
        self, organization_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Verify the integrity of the audit chain.

        Args:
            organization_id: Organization to verify
            start_time: Optional start of time range
            end_time: Optional end of time range

        Returns:
            Dictionary with verification results
        """
        return await self.storage.verify_integrity(
            organization_id, start_time, end_time
        )

    async def export_events(
        self,
        filter: AuditEventFilter,
        format: str = "json"
    ) -> str:
        """
        Export audit events in a specified format.

        Args:
            filter: Filter criteria for the export
            format: Export format ("json", "csv")

        Returns:
            Exported data as a string
        """
        events = await self.query_events(filter)

        if format == "json":
            import json
            return json.dumps(
                [event.to_dict() for event in events],
                indent=2,
                default=str
            )
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            if not events:
                return ""

            # Get all field names from first event
            fieldnames = list(events[0].to_dict().keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)

            writer.writeheader()
            for event in events:
                writer.writerow(event.to_dict())

            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Decorator for auditing function calls
def audit_action(
    event_category: EventCategory,
    event_type: str,
    resource_type: str,
    action: Action,
    severity: Severity = Severity.INFO
):
    """
    Decorator to automatically audit function calls.

    Usage:
        @audit_action(
            event_category=EventCategory.DATA,
            event_type="trace.deleted",
            resource_type="trace",
            action=Action.DELETE
        )
        async def delete_trace(trace_id: str, organization_id: str):
            # Function implementation
            pass

    The decorator expects the decorated function to have or return:
    - organization_id: Required
    - resource_id: Required (or extracted from return value)
    - actor_id, actor_type, actor_email: Optional
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get audit service from somewhere (e.g., dependency injection)
            # For now, this is a placeholder
            audit_service = kwargs.pop('_audit_service', None)

            if audit_service is None:
                # If no audit service provided, just call the function
                return await func(*args, **kwargs)

            # Extract parameters
            organization_id = kwargs.get('organization_id')
            resource_id = kwargs.get('resource_id')
            actor_id = kwargs.get('actor_id', 'system')
            actor_type = kwargs.get('actor_type', ActorType.SYSTEM)
            actor_email = kwargs.get('actor_email')

            # Call the function
            result = await func(*args, **kwargs)

            # If resource_id not in params, try to get from result
            if not resource_id and isinstance(result, dict):
                resource_id = result.get('id') or result.get('resource_id')

            # Capture audit event
            if organization_id and resource_id:
                await audit_service.capture_event(
                    organization_id=organization_id,
                    event_category=event_category,
                    event_type=event_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=action,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    actor_email=actor_email,
                    event_severity=severity
                )

            return result

        return wrapper
    return decorator


@asynccontextmanager
async def audit_context(
    audit_service: AuditService,
    organization_id: str,
    event_category: EventCategory,
    event_type: str,
    resource_type: str,
    resource_id: str,
    action: Action,
    actor_type: ActorType = ActorType.SYSTEM,
    actor_id: str = "system",
    severity: Severity = Severity.INFO,
    capture_state: bool = True
):
    """
    Context manager for auditing operations with before/after state.

    Usage:
        async with audit_context(
            audit_service=service,
            organization_id="org-123",
            event_category=EventCategory.CONFIG,
            event_type="project.updated",
            resource_type="project",
            resource_id="proj-456",
            action=Action.UPDATE
        ) as ctx:
            # Capture state before
            ctx.before = {"name": "Old Name"}

            # Perform operation
            update_project()

            # Capture state after
            ctx.after = {"name": "New Name"}

    The context manager will automatically capture an audit event with
    the before and after states.
    """
    class AuditContext:
        def __init__(self):
            self.before: Optional[Dict[str, Any]] = None
            self.after: Optional[Dict[str, Any]] = None

    ctx = AuditContext()

    try:
        yield ctx
    finally:
        # Capture audit event
        await audit_service.capture_event(
            organization_id=organization_id,
            event_category=event_category,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            actor_type=actor_type,
            actor_id=actor_id,
            previous_state=ctx.before if capture_state else None,
            new_state=ctx.after if capture_state else None,
            event_severity=severity
        )


# Global audit service instance (to be initialized in app startup)
_global_audit_service: Optional[AuditService] = None


def get_audit_service() -> Optional[AuditService]:
    """Get the global audit service instance."""
    return _global_audit_service


def set_audit_service(service: AuditService):
    """Set the global audit service instance."""
    global _global_audit_service
    _global_audit_service = service
