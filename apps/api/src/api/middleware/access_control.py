"""
Access Control and Rate Limiting for Audit API

Implements permission checks and rate limiting to prevent abuse.
"""

import time
from collections import defaultdict
from typing import Optional, Callable
from functools import wraps
from datetime import datetime, timedelta

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Permission constants
class Permission:
    """Audit API permissions."""
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    AUDIT_ADMIN = "audit:admin"


# Simple in-memory rate limiter (replace with Redis in production)
class RateLimiter:
    """
    Simple rate limiter using token bucket algorithm.

    In production, replace with Redis-based rate limiter.
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute per user
        """
        self.requests_per_minute = requests_per_minute
        self.buckets = defaultdict(lambda: {
            "tokens": requests_per_minute,
            "last_refill": time.time()
        })

    def check_rate_limit(self, key: str) -> bool:
        """
        Check if request is within rate limit.

        Args:
            key: Identifier for rate limiting (e.g., user_id, ip_address)

        Returns:
            True if within limit, False if exceeded
        """
        bucket = self.buckets[key]

        # Refill tokens based on time elapsed
        now = time.time()
        time_elapsed = now - bucket["last_refill"]
        tokens_to_add = time_elapsed * (self.requests_per_minute / 60)

        bucket["tokens"] = min(
            self.requests_per_minute,
            bucket["tokens"] + tokens_to_add
        )
        bucket["last_refill"] = now

        # Check if we have tokens
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True

        return False

    def get_retry_after(self, key: str) -> int:
        """
        Get number of seconds until next token is available.

        Args:
            key: Identifier for rate limiting

        Returns:
            Seconds until retry
        """
        bucket = self.buckets[key]
        tokens_needed = 1 - bucket["tokens"]
        seconds_per_token = 60 / self.requests_per_minute
        return int(tokens_needed * seconds_per_token) + 1


# Global rate limiters
_rate_limiters = {
    "query": RateLimiter(requests_per_minute=60),
    "export": RateLimiter(requests_per_minute=10),
    "stream": RateLimiter(requests_per_minute=5)
}


# Security scheme
security = HTTPBearer(auto_error=False)


class User:
    """
    User model for access control.

    In production, replace with actual user model from database.
    """

    def __init__(self, user_id: str, permissions: list):
        self.user_id = user_id
        self.permissions = permissions

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get current authenticated user.

    In production, this would:
    1. Validate JWT token
    2. Look up user in database
    3. Load permissions

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        User instance

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        # For demo, allow unauthenticated access with limited permissions
        return User(user_id="anonymous", permissions=[Permission.AUDIT_READ])

    # In production, validate token and load user
    # For now, create mock user with all permissions
    return User(
        user_id="user_123",
        permissions=[Permission.AUDIT_READ, Permission.AUDIT_EXPORT, Permission.AUDIT_ADMIN]
    )


def require_permission(permission: str):
    """
    Decorator to require specific permission.

    Usage:
        @router.get("/sensitive")
        @require_permission(Permission.AUDIT_EXPORT)
        async def sensitive_endpoint(user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs (injected by Depends)
            user = kwargs.get("user") or kwargs.get("current_user")

            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required"
                )

            if not user.has_permission(permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission required: {permission}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def rate_limit(limiter_type: str = "query"):
    """
    Decorator for rate limiting.

    Usage:
        @router.get("/api")
        @rate_limit("query")
        async def my_endpoint(user: User = Depends(get_current_user)):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs
            user = kwargs.get("user") or kwargs.get("current_user")

            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required for rate limiting"
                )

            # Check rate limit
            limiter = _rate_limiters.get(limiter_type, _rate_limiters["query"])

            if not limiter.check_rate_limit(user.user_id):
                retry_after = limiter.get_retry_after(user.user_id)
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(retry_after)}
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Dependency for checking audit read permission
async def require_audit_read(user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require audit read permission.

    Usage:
        @router.get("/events")
        async def get_events(user: User = Depends(require_audit_read)):
            ...
    """
    if not user.has_permission(Permission.AUDIT_READ):
        raise HTTPException(
            status_code=403,
            detail="Audit read permission required"
        )
    return user


# Dependency for checking audit export permission
async def require_audit_export(user: User = Depends(get_current_user)) -> User:
    """
    Dependency to require audit export permission.

    Usage:
        @router.post("/export")
        async def create_export(user: User = Depends(require_audit_export)):
            ...
    """
    if not user.has_permission(Permission.AUDIT_EXPORT):
        raise HTTPException(
            status_code=403,
            detail="Audit export permission required"
        )
    return user


# Middleware for logging audit API access
class AuditAPIMiddleware:
    """
    Middleware to audit access to audit API (meta-audit).

    Logs all queries to the audit log itself.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        """Process request and log to audit."""
        from datetime import datetime, timezone

        # Only log audit API access
        if request.url.path.startswith("/api/v1/audit"):
            start_time = datetime.now(timezone.utc)

            # Get user from request state (set by auth)
            user_id = "anonymous"
            try:
                # Try to extract user from headers
                auth_header = request.headers.get("authorization")
                if auth_header:
                    # In production, decode JWT and get user ID
                    user_id = "authenticated_user"
            except:
                pass

            # Process request
            response = await call_next(request)

            # Log to audit trail
            try:
                from ...models.audit import (
                    AuditEvent,
                    ActorType,
                    EventCategory,
                    Action,
                    Severity,
                    AdminEventTypes
                )
                from ...services.audit import get_audit_service

                audit_service = get_audit_service()
                if audit_service:
                    # Create audit event for meta-audit
                    event = AuditEvent(
                        event_id="",  # Will be auto-generated
                        timestamp=start_time,
                        organization_id="system",  # Meta-audit is system-wide
                        actor_type=ActorType.USER if user_id != "anonymous" else ActorType.SYSTEM,
                        actor_id=user_id,
                        actor_ip=request.client.host if request.client else None,
                        actor_user_agent=request.headers.get("user-agent"),
                        event_category=EventCategory.ADMIN,
                        event_type=AdminEventTypes.AUDIT_LOG_VIEWED,
                        event_severity=Severity.INFO,
                        resource_type="audit_api",
                        resource_id=request.url.path,
                        action=Action.READ if request.method == "GET" else Action.EXPORT,
                        request_id=request.headers.get("x-request-id", ""),
                        new_state={
                            "method": request.method,
                            "path": request.url.path,
                            "query_params": dict(request.query_params),
                            "status_code": response.status_code,
                            "response_time_ms": int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                        }
                    )

                    # Log asynchronously (don't block response)
                    import asyncio
                    asyncio.create_task(audit_service.log_event(event))
            except Exception as e:
                # Don't fail request if meta-audit logging fails
                print(f"Meta-audit logging failed: {e}")

            return response
        else:
            # Not an audit API endpoint, just pass through
            response = await call_next(request)
            return response
