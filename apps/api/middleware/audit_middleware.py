"""
Audit Middleware for FastAPI

This module provides middleware for automatically capturing audit events
from HTTP requests. It extracts request context (IP, user agent, user info)
and makes it available to route handlers.
"""

from contextvars import ContextVar
from typing import Optional, Dict, Any, Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..models.audit import ActorType, EventCategory, Severity, Action
from ..services.audit import AuditService


# Context variables for request-scoped data
_request_id: ContextVar[str] = ContextVar('request_id', default='')
_actor_id: ContextVar[str] = ContextVar('actor_id', default='system')
_actor_type: ContextVar[ActorType] = ContextVar('actor_type', default=ActorType.SYSTEM)
_actor_email: ContextVar[Optional[str]] = ContextVar('actor_email', default=None)
_actor_ip: ContextVar[Optional[str]] = ContextVar('actor_ip', default=None)
_actor_user_agent: ContextVar[Optional[str]] = ContextVar('actor_user_agent', default=None)
_organization_id: ContextVar[Optional[str]] = ContextVar('organization_id', default=None)
_session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


class RequestContext:
    """Container for request context data."""

    def __init__(
        self,
        request_id: str,
        actor_id: str = "system",
        actor_type: ActorType = ActorType.SYSTEM,
        actor_email: Optional[str] = None,
        actor_ip: Optional[str] = None,
        actor_user_agent: Optional[str] = None,
        organization_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.request_id = request_id
        self.actor_id = actor_id
        self.actor_type = actor_type
        self.actor_email = actor_email
        self.actor_ip = actor_ip
        self.actor_user_agent = actor_user_agent
        self.organization_id = organization_id
        self.session_id = session_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type.value if isinstance(self.actor_type, ActorType) else self.actor_type,
            "actor_email": self.actor_email,
            "actor_ip": self.actor_ip,
            "actor_user_agent": self.actor_user_agent,
            "organization_id": self.organization_id,
            "session_id": self.session_id,
        }


def get_request_context() -> RequestContext:
    """
    Get the current request context.

    This can be called from anywhere within a request to get audit context.

    Returns:
        RequestContext with current request information
    """
    return RequestContext(
        request_id=_request_id.get(),
        actor_id=_actor_id.get(),
        actor_type=_actor_type.get(),
        actor_email=_actor_email.get(),
        actor_ip=_actor_ip.get(),
        actor_user_agent=_actor_user_agent.get(),
        organization_id=_organization_id.get(),
        session_id=_session_id.get(),
    )


class AuditMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic audit event capture.

    This middleware:
    1. Extracts request context (IP, user agent, authentication)
    2. Stores context in request-scoped context variables
    3. Optionally captures API access events
    4. Adds request_id to response headers

    Configuration:
        audit_service: AuditService instance
        capture_api_access: Whether to log all API access (default: False)
        exclude_paths: List of paths to exclude from audit (e.g., health checks)
        user_extractor: Custom function to extract user info from request
    """

    def __init__(
        self,
        app: ASGIApp,
        audit_service: Optional[AuditService] = None,
        capture_api_access: bool = False,
        exclude_paths: Optional[list] = None,
        user_extractor: Optional[Callable] = None
    ):
        """
        Initialize the audit middleware.

        Args:
            app: FastAPI application
            audit_service: AuditService instance for logging events
            capture_api_access: Whether to log all API access
            exclude_paths: List of paths to exclude from audit
            user_extractor: Function to extract user info from request
        """
        super().__init__(app)
        self.audit_service = audit_service
        self.capture_api_access = capture_api_access
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
        self.user_extractor = user_extractor or self._default_user_extractor

    def _default_user_extractor(self, request: Request) -> Dict[str, Any]:
        """
        Default user extraction from request.

        Override this with a custom extractor that understands your
        authentication system (JWT, API keys, sessions, etc.).

        Returns:
            Dictionary with user information:
            - actor_type: ActorType
            - actor_id: str
            - actor_email: Optional[str]
            - organization_id: Optional[str]
            - session_id: Optional[str]
        """
        # Check for API key in headers
        api_key = request.headers.get("x-api-key") or request.headers.get("authorization")

        if api_key:
            # Extract bearer token
            if api_key.startswith("Bearer "):
                api_key = api_key[7:]

            # In a real implementation, you would:
            # 1. Validate the API key
            # 2. Look up the associated user/service
            # 3. Extract organization_id

            return {
                "actor_type": ActorType.SERVICE,
                "actor_id": api_key[:16],  # First 16 chars for logging
                "actor_email": None,
                "organization_id": None,  # TODO: Extract from token
                "session_id": None
            }

        # Check for JWT token (placeholder)
        # In production, decode JWT and extract user info

        # Default to system actor
        return {
            "actor_type": ActorType.SYSTEM,
            "actor_id": "system",
            "actor_email": None,
            "organization_id": None,
            "session_id": None
        }

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Extract client IP address from request.

        Handles X-Forwarded-For header for proxied requests.
        """
        # Check X-Forwarded-For header first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if request.client:
            return request.client.host

        return None

    def _should_audit(self, request: Request) -> bool:
        """Determine if this request should be audited."""
        # Check if path is excluded
        for excluded_path in self.exclude_paths:
            if request.url.path.startswith(excluded_path):
                return False

        return True

    async def dispatch(self, request: Request, call_next):
        """Process the request and capture audit context."""
        # Generate request ID
        request_id = str(uuid4())

        # Extract client information
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Extract user/authentication information
        user_info = self.user_extractor(request)

        # Set context variables
        _request_id.set(request_id)
        _actor_id.set(user_info.get("actor_id", "system"))
        _actor_type.set(user_info.get("actor_type", ActorType.SYSTEM))
        _actor_email.set(user_info.get("actor_email"))
        _actor_ip.set(client_ip)
        _actor_user_agent.set(user_agent)
        _organization_id.set(user_info.get("organization_id"))
        _session_id.set(user_info.get("session_id"))

        # Store in request state for easy access
        request.state.audit_context = get_request_context()

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Capture API access event if enabled
        if self.audit_service and self.capture_api_access and self._should_audit(request):
            # Determine severity based on status code
            if response.status_code >= 500:
                severity = Severity.CRITICAL
            elif response.status_code >= 400:
                severity = Severity.WARNING
            else:
                severity = Severity.INFO

            # Capture event asynchronously (fire and forget)
            if user_info.get("organization_id"):
                try:
                    await self.audit_service.capture_event(
                        organization_id=user_info["organization_id"],
                        event_category=EventCategory.DATA,
                        event_type="api.access",
                        resource_type="api",
                        resource_id=request.url.path,
                        action=self._method_to_action(request.method),
                        actor_type=user_info.get("actor_type", ActorType.SYSTEM),
                        actor_id=user_info.get("actor_id", "system"),
                        actor_email=user_info.get("actor_email"),
                        actor_ip=client_ip,
                        actor_user_agent=user_agent,
                        request_id=request_id,
                        session_id=user_info.get("session_id"),
                        event_severity=severity,
                        metadata={
                            "method": request.method,
                            "path": request.url.path,
                            "status_code": response.status_code,
                        }
                    )
                except Exception as e:
                    # Don't let audit failures break the request
                    print(f"AuditMiddleware: Error capturing event: {e}")

        return response

    def _method_to_action(self, method: str) -> Action:
        """Map HTTP method to audit action."""
        method = method.upper()
        if method == "POST":
            return Action.CREATE
        elif method == "GET":
            return Action.READ
        elif method in ["PUT", "PATCH"]:
            return Action.UPDATE
        elif method == "DELETE":
            return Action.DELETE
        else:
            return Action.READ


# Dependency injection helper for FastAPI routes
async def get_audit_context_dependency() -> RequestContext:
    """
    FastAPI dependency for injecting audit context into routes.

    Usage:
        @app.get("/traces/{trace_id}")
        async def get_trace(
            trace_id: str,
            audit_ctx: RequestContext = Depends(get_audit_context_dependency)
        ):
            # Use audit_ctx for logging
            pass
    """
    return get_request_context()
