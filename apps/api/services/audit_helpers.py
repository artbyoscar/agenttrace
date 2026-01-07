"""
Audit Helper Utilities

This module provides convenient helper functions and utilities for
common audit logging scenarios.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from ..models.audit import (
    EventCategory,
    Severity,
    Action,
    ActorType,
    AuthEventTypes,
    DataEventTypes,
    ConfigEventTypes,
    AdminEventTypes,
    EvalEventTypes,
)
from .audit import AuditService
from ..middleware.audit_middleware import get_request_context


class AuditHelper:
    """
    Helper class providing convenient methods for common audit scenarios.

    This class wraps the AuditService with higher-level methods for
    specific event types.
    """

    def __init__(self, audit_service: AuditService):
        """
        Initialize the audit helper.

        Args:
            audit_service: AuditService instance
        """
        self.service = audit_service

    async def _capture_with_context(
        self,
        event_category: EventCategory,
        event_type: str,
        resource_type: str,
        resource_id: str,
        action: Action,
        organization_id: Optional[str] = None,
        project_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        severity: Severity = Severity.INFO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Capture an event using request context when available.

        This method automatically extracts actor information from the
        current request context.
        """
        try:
            ctx = get_request_context()
            return await self.service.capture_event(
                organization_id=organization_id or ctx.organization_id or "unknown",
                project_id=project_id,
                event_category=event_category,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                action=action,
                actor_type=ctx.actor_type,
                actor_id=ctx.actor_id,
                actor_email=ctx.actor_email,
                actor_ip=ctx.actor_ip,
                actor_user_agent=ctx.actor_user_agent,
                request_id=ctx.request_id,
                session_id=ctx.session_id,
                previous_state=previous_state,
                new_state=new_state,
                event_severity=severity,
                metadata=metadata
            )
        except Exception:
            # If no request context, use defaults
            return await self.service.capture_event(
                organization_id=organization_id or "unknown",
                project_id=project_id,
                event_category=event_category,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                action=action,
                previous_state=previous_state,
                new_state=new_state,
                event_severity=severity,
                metadata=metadata
            )

    # Authentication Events
    async def log_user_login(
        self,
        organization_id: str,
        user_id: str,
        user_email: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a user login attempt."""
        return await self._capture_with_context(
            event_category=EventCategory.AUTH,
            event_type=AuthEventTypes.USER_LOGIN if success else AuthEventTypes.USER_LOGIN_FAILED,
            resource_type="user",
            resource_id=user_id,
            resource_name=user_email,
            action=Action.READ,
            organization_id=organization_id,
            severity=Severity.INFO if success else Severity.WARNING,
            metadata=metadata
        )

    async def log_user_logout(
        self,
        organization_id: str,
        user_id: str,
        user_email: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a user logout."""
        return await self._capture_with_context(
            event_category=EventCategory.AUTH,
            event_type=AuthEventTypes.USER_LOGOUT,
            resource_type="user",
            resource_id=user_id,
            resource_name=user_email,
            action=Action.READ,
            organization_id=organization_id,
            severity=Severity.INFO,
            metadata=metadata
        )

    async def log_api_key_created(
        self,
        organization_id: str,
        api_key_id: str,
        api_key_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log API key creation."""
        return await self._capture_with_context(
            event_category=EventCategory.AUTH,
            event_type=AuthEventTypes.API_KEY_CREATED,
            resource_type="api_key",
            resource_id=api_key_id,
            resource_name=api_key_name,
            action=Action.CREATE,
            organization_id=organization_id,
            severity=Severity.INFO,
            metadata=metadata
        )

    async def log_api_key_revoked(
        self,
        organization_id: str,
        api_key_id: str,
        api_key_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log API key revocation."""
        return await self._capture_with_context(
            event_category=EventCategory.AUTH,
            event_type=AuthEventTypes.API_KEY_REVOKED,
            resource_type="api_key",
            resource_id=api_key_id,
            resource_name=api_key_name,
            action=Action.DELETE,
            organization_id=organization_id,
            severity=Severity.WARNING,
            metadata=metadata
        )

    # Data Events
    async def log_trace_created(
        self,
        organization_id: str,
        project_id: str,
        trace_id: str,
        trace_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log trace creation."""
        return await self._capture_with_context(
            event_category=EventCategory.DATA,
            event_type=DataEventTypes.TRACE_CREATED,
            resource_type="trace",
            resource_id=trace_id,
            resource_name=trace_name,
            action=Action.CREATE,
            organization_id=organization_id,
            project_id=project_id,
            severity=Severity.INFO,
            metadata=metadata
        )

    async def log_trace_viewed(
        self,
        organization_id: str,
        project_id: str,
        trace_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log trace view."""
        return await self._capture_with_context(
            event_category=EventCategory.DATA,
            event_type=DataEventTypes.TRACE_VIEWED,
            resource_type="trace",
            resource_id=trace_id,
            action=Action.READ,
            organization_id=organization_id,
            project_id=project_id,
            severity=Severity.INFO,
            metadata=metadata
        )

    async def log_trace_exported(
        self,
        organization_id: str,
        project_id: str,
        trace_id: str,
        export_format: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log trace export."""
        metadata = metadata or {}
        metadata["export_format"] = export_format

        return await self._capture_with_context(
            event_category=EventCategory.DATA,
            event_type=DataEventTypes.TRACE_EXPORTED,
            resource_type="trace",
            resource_id=trace_id,
            action=Action.EXPORT,
            organization_id=organization_id,
            project_id=project_id,
            severity=Severity.WARNING,  # Exports are potentially sensitive
            metadata=metadata
        )

    async def log_trace_deleted(
        self,
        organization_id: str,
        project_id: str,
        trace_id: str,
        trace_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log trace deletion."""
        return await self._capture_with_context(
            event_category=EventCategory.DATA,
            event_type=DataEventTypes.TRACE_DELETED,
            resource_type="trace",
            resource_id=trace_id,
            action=Action.DELETE,
            organization_id=organization_id,
            project_id=project_id,
            previous_state=trace_data,
            severity=Severity.WARNING,
            metadata=metadata
        )

    # Configuration Events
    async def log_project_created(
        self,
        organization_id: str,
        project_id: str,
        project_name: str,
        project_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log project creation."""
        return await self._capture_with_context(
            event_category=EventCategory.CONFIG,
            event_type=ConfigEventTypes.PROJECT_CREATED,
            resource_type="project",
            resource_id=project_id,
            resource_name=project_name,
            action=Action.CREATE,
            organization_id=organization_id,
            new_state=project_config,
            severity=Severity.INFO,
            metadata=metadata
        )

    async def log_project_updated(
        self,
        organization_id: str,
        project_id: str,
        project_name: str,
        old_config: Optional[Dict[str, Any]] = None,
        new_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log project update."""
        return await self._capture_with_context(
            event_category=EventCategory.CONFIG,
            event_type=ConfigEventTypes.PROJECT_UPDATED,
            resource_type="project",
            resource_id=project_id,
            resource_name=project_name,
            action=Action.UPDATE,
            organization_id=organization_id,
            previous_state=old_config,
            new_state=new_config,
            severity=Severity.INFO,
            metadata=metadata
        )

    async def log_project_deleted(
        self,
        organization_id: str,
        project_id: str,
        project_name: str,
        project_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log project deletion."""
        return await self._capture_with_context(
            event_category=EventCategory.CONFIG,
            event_type=ConfigEventTypes.PROJECT_DELETED,
            resource_type="project",
            resource_id=project_id,
            resource_name=project_name,
            action=Action.DELETE,
            organization_id=organization_id,
            previous_state=project_config,
            severity=Severity.WARNING,
            metadata=metadata
        )

    # Admin Events
    async def log_user_invited(
        self,
        organization_id: str,
        user_email: str,
        role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log user invitation."""
        metadata = metadata or {}
        metadata["role"] = role

        return await self._capture_with_context(
            event_category=EventCategory.ADMIN,
            event_type=AdminEventTypes.USER_INVITED,
            resource_type="user",
            resource_id=user_email,
            resource_name=user_email,
            action=Action.CREATE,
            organization_id=organization_id,
            severity=Severity.INFO,
            metadata=metadata
        )

    async def log_user_role_changed(
        self,
        organization_id: str,
        user_id: str,
        user_email: str,
        old_role: str,
        new_role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log user role change."""
        return await self._capture_with_context(
            event_category=EventCategory.ADMIN,
            event_type=AdminEventTypes.USER_ROLE_CHANGED,
            resource_type="user",
            resource_id=user_id,
            resource_name=user_email,
            action=Action.UPDATE,
            organization_id=organization_id,
            previous_state={"role": old_role},
            new_state={"role": new_role},
            severity=Severity.WARNING,
            metadata=metadata
        )

    async def log_user_removed(
        self,
        organization_id: str,
        user_id: str,
        user_email: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log user removal."""
        return await self._capture_with_context(
            event_category=EventCategory.ADMIN,
            event_type=AdminEventTypes.USER_REMOVED,
            resource_type="user",
            resource_id=user_id,
            resource_name=user_email,
            action=Action.DELETE,
            organization_id=organization_id,
            severity=Severity.WARNING,
            metadata=metadata
        )

    # Evaluation Events
    async def log_evaluation_started(
        self,
        organization_id: str,
        project_id: str,
        evaluation_id: str,
        evaluator_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log evaluation start."""
        return await self._capture_with_context(
            event_category=EventCategory.EVAL,
            event_type=EvalEventTypes.EVALUATION_STARTED,
            resource_type="evaluation",
            resource_id=evaluation_id,
            resource_name=evaluator_name,
            action=Action.CREATE,
            organization_id=organization_id,
            project_id=project_id,
            severity=Severity.INFO,
            metadata=metadata
        )

    async def log_evaluation_completed(
        self,
        organization_id: str,
        project_id: str,
        evaluation_id: str,
        evaluator_name: str,
        results: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log evaluation completion."""
        return await self._capture_with_context(
            event_category=EventCategory.EVAL,
            event_type=EvalEventTypes.EVALUATION_COMPLETED,
            resource_type="evaluation",
            resource_id=evaluation_id,
            resource_name=evaluator_name,
            action=Action.UPDATE,
            organization_id=organization_id,
            project_id=project_id,
            new_state=results,
            severity=Severity.INFO,
            metadata=metadata
        )

    async def log_evaluation_failed(
        self,
        organization_id: str,
        project_id: str,
        evaluation_id: str,
        evaluator_name: str,
        error: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log evaluation failure."""
        metadata = metadata or {}
        metadata["error"] = error

        return await self._capture_with_context(
            event_category=EventCategory.EVAL,
            event_type=EvalEventTypes.EVALUATION_FAILED,
            resource_type="evaluation",
            resource_id=evaluation_id,
            resource_name=evaluator_name,
            action=Action.UPDATE,
            organization_id=organization_id,
            project_id=project_id,
            severity=Severity.WARNING,
            metadata=metadata
        )
