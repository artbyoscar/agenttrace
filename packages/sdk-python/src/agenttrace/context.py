"""
Trace context propagation using contextvars.

Provides thread-safe and async-safe context management for traces and spans.
Enables automatic parent-child relationship tracking and context propagation
across function boundaries.
"""

from contextvars import ContextVar
from typing import Optional, Any
from contextlib import contextmanager
import uuid

# Context variables for current trace and span
_current_trace_id: ContextVar[Optional[str]] = ContextVar("current_trace_id", default=None)
_current_span_id: ContextVar[Optional[str]] = ContextVar("current_span_id", default=None)
_current_span: ContextVar[Optional[Any]] = ContextVar("current_span", default=None)


class TraceContext:
    """
    Manages trace context propagation.

    Uses Python contextvars for thread-safe and async-safe context storage.
    Automatically handles parent-child relationships between spans.

    Example:
        >>> ctx = TraceContext()
        >>> trace_id = ctx.new_trace()
        >>> with ctx.span_context(span):
        ...     # Inside this block, span is the current span
        ...     child_span_id = ctx.get_current_span_id()
    """

    @staticmethod
    def new_trace(trace_id: Optional[str] = None) -> str:
        """
        Start a new trace context.

        Args:
            trace_id: Optional trace ID (generated if not provided)

        Returns:
            str: The trace ID

        Example:
            >>> ctx = TraceContext()
            >>> trace_id = ctx.new_trace()
        """
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        _current_trace_id.set(trace_id)
        _current_span_id.set(None)  # Reset span context
        _current_span.set(None)

        return trace_id

    @staticmethod
    def get_current_trace_id() -> Optional[str]:
        """
        Get the current trace ID from context.

        Returns:
            Optional[str]: Current trace ID or None if no trace is active

        Example:
            >>> trace_id = TraceContext.get_current_trace_id()
        """
        return _current_trace_id.get()

    @staticmethod
    def set_current_trace_id(trace_id: str) -> None:
        """
        Set the current trace ID.

        Args:
            trace_id: Trace ID to set

        Example:
            >>> TraceContext.set_current_trace_id("my-trace-id")
        """
        _current_trace_id.set(trace_id)

    @staticmethod
    def get_current_span_id() -> Optional[str]:
        """
        Get the current span ID from context.

        This is useful for determining the parent span when creating child spans.

        Returns:
            Optional[str]: Current span ID or None if no span is active

        Example:
            >>> parent_span_id = TraceContext.get_current_span_id()
        """
        return _current_span_id.get()

    @staticmethod
    def set_current_span_id(span_id: str) -> None:
        """
        Set the current span ID.

        Args:
            span_id: Span ID to set

        Example:
            >>> TraceContext.set_current_span_id("my-span-id")
        """
        _current_span_id.set(span_id)

    @staticmethod
    def get_current_span() -> Optional[Any]:
        """
        Get the current span object from context.

        Returns:
            Optional[Span]: Current span or None if no span is active

        Example:
            >>> current_span = TraceContext.get_current_span()
            >>> if current_span:
            ...     current_span.set_attribute("key", "value")
        """
        return _current_span.get()

    @staticmethod
    def set_current_span(span: Any) -> None:
        """
        Set the current span object.

        Args:
            span: Span object to set

        Example:
            >>> TraceContext.set_current_span(my_span)
        """
        _current_span.set(span)

    @staticmethod
    @contextmanager
    def span_context(span: Any):
        """
        Context manager for span lifecycle.

        Automatically sets the span as current on entry and restores
        the previous span on exit. This enables automatic parent-child
        relationship tracking.

        Args:
            span: Span object to make current

        Yields:
            Span: The span object

        Example:
            >>> with TraceContext.span_context(my_span) as span:
            ...     # Inside this block, my_span is the current span
            ...     span.set_attribute("key", "value")
            ...     # Child spans created here will automatically have
            ...     # my_span as their parent
        """
        # Save previous context
        previous_span = _current_span.get()
        previous_span_id = _current_span_id.get()

        # Set current context
        _current_span.set(span)
        if hasattr(span, "span_id"):
            _current_span_id.set(span.span_id)

        # Set trace_id if not already set
        if hasattr(span, "trace_id") and _current_trace_id.get() is None:
            _current_trace_id.set(span.trace_id)

        try:
            yield span
        finally:
            # Restore previous context
            _current_span.set(previous_span)
            _current_span_id.set(previous_span_id)

    @staticmethod
    @contextmanager
    def trace_context(trace_id: str):
        """
        Context manager for trace lifecycle.

        Sets the trace ID for the duration of the context and clears it on exit.

        Args:
            trace_id: Trace ID to set

        Yields:
            str: The trace ID

        Example:
            >>> with TraceContext.trace_context("my-trace-id") as trace_id:
            ...     # Inside this block, trace_id is the current trace
            ...     span = create_span()  # Will use this trace_id
        """
        # Save previous context
        previous_trace_id = _current_trace_id.get()

        # Set current trace
        _current_trace_id.set(trace_id)

        try:
            yield trace_id
        finally:
            # Restore previous context
            _current_trace_id.set(previous_trace_id)

    @staticmethod
    def clear() -> None:
        """
        Clear all context.

        Removes all trace and span context. Useful for cleanup and testing.

        Example:
            >>> TraceContext.clear()
        """
        _current_trace_id.set(None)
        _current_span_id.set(None)
        _current_span.set(None)

    @staticmethod
    def get_context() -> dict:
        """
        Get all current context as a dictionary.

        Returns:
            dict: Current context with trace_id and span_id

        Example:
            >>> context = TraceContext.get_context()
            >>> print(context)
            {'trace_id': 'abc123', 'span_id': 'def456'}
        """
        return {
            "trace_id": _current_trace_id.get(),
            "span_id": _current_span_id.get(),
        }

    @staticmethod
    def set_context(trace_id: Optional[str] = None, span_id: Optional[str] = None) -> None:
        """
        Set context from explicit values.

        Args:
            trace_id: Trace ID to set (optional)
            span_id: Span ID to set (optional)

        Example:
            >>> TraceContext.set_context(trace_id="abc123", span_id="def456")
        """
        if trace_id is not None:
            _current_trace_id.set(trace_id)
        if span_id is not None:
            _current_span_id.set(span_id)


# Convenience functions for common operations

def get_current_trace_id() -> Optional[str]:
    """
    Get the current trace ID.

    Convenience function that delegates to TraceContext.

    Returns:
        Optional[str]: Current trace ID or None
    """
    return TraceContext.get_current_trace_id()


def get_current_span_id() -> Optional[str]:
    """
    Get the current span ID.

    Convenience function that delegates to TraceContext.

    Returns:
        Optional[str]: Current span ID or None
    """
    return TraceContext.get_current_span_id()


def get_current_span() -> Optional[Any]:
    """
    Get the current span object.

    Convenience function that delegates to TraceContext.

    Returns:
        Optional[Span]: Current span or None
    """
    return TraceContext.get_current_span()


def new_trace(trace_id: Optional[str] = None) -> str:
    """
    Start a new trace.

    Convenience function that delegates to TraceContext.

    Args:
        trace_id: Optional trace ID

    Returns:
        str: The trace ID
    """
    return TraceContext.new_trace(trace_id)


def clear_context() -> None:
    """
    Clear all context.

    Convenience function that delegates to TraceContext.
    """
    TraceContext.clear()
