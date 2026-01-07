"""Unit tests for context module."""

import pytest
from agenttrace.context import (
    TraceContext,
    get_current_trace_id,
    get_current_span_id,
    get_current_span,
    new_trace,
    clear_context,
)


class TestTraceContext:
    """Tests for TraceContext class."""

    def setup_method(self):
        """Clear context before each test."""
        TraceContext.clear()

    def teardown_method(self):
        """Clear context after each test."""
        TraceContext.clear()

    def test_new_trace(self):
        """Test creating a new trace."""
        trace_id = TraceContext.new_trace()

        assert trace_id is not None
        assert TraceContext.get_current_trace_id() == trace_id
        assert TraceContext.get_current_span_id() is None

    def test_new_trace_with_id(self):
        """Test creating a new trace with specific ID."""
        trace_id = "custom-trace-id"
        result = TraceContext.new_trace(trace_id)

        assert result == trace_id
        assert TraceContext.get_current_trace_id() == trace_id

    def test_set_get_trace_id(self):
        """Test setting and getting trace ID."""
        trace_id = "test-trace-id"
        TraceContext.set_current_trace_id(trace_id)

        assert TraceContext.get_current_trace_id() == trace_id

    def test_set_get_span_id(self):
        """Test setting and getting span ID."""
        span_id = "test-span-id"
        TraceContext.set_current_span_id(span_id)

        assert TraceContext.get_current_span_id() == span_id

    def test_span_context_manager(self):
        """Test span context manager."""
        class MockSpan:
            span_id = "mock-span-id"
            trace_id = "mock-trace-id"

        span = MockSpan()

        # Before context
        assert TraceContext.get_current_span() is None

        # Inside context
        with TraceContext.span_context(span) as ctx_span:
            assert ctx_span is span
            assert TraceContext.get_current_span() is span
            assert TraceContext.get_current_span_id() == "mock-span-id"
            assert TraceContext.get_current_trace_id() == "mock-trace-id"

        # After context
        assert TraceContext.get_current_span() is None

    def test_nested_span_context(self):
        """Test nested span contexts."""
        class MockSpan:
            def __init__(self, span_id, trace_id):
                self.span_id = span_id
                self.trace_id = trace_id

        parent = MockSpan("parent-id", "trace-id")
        child = MockSpan("child-id", "trace-id")

        with TraceContext.span_context(parent):
            assert TraceContext.get_current_span_id() == "parent-id"

            with TraceContext.span_context(child):
                assert TraceContext.get_current_span_id() == "child-id"

            # Parent restored after child context exits
            assert TraceContext.get_current_span_id() == "parent-id"

        # Context cleared after all contexts exit
        assert TraceContext.get_current_span() is None

    def test_trace_context_manager(self):
        """Test trace context manager."""
        trace_id = "test-trace-id"

        with TraceContext.trace_context(trace_id) as ctx_trace_id:
            assert ctx_trace_id == trace_id
            assert TraceContext.get_current_trace_id() == trace_id

        # Context cleared after exit (restores previous)
        assert TraceContext.get_current_trace_id() is None

    def test_clear(self):
        """Test clearing all context."""
        TraceContext.set_current_trace_id("trace-id")
        TraceContext.set_current_span_id("span-id")

        TraceContext.clear()

        assert TraceContext.get_current_trace_id() is None
        assert TraceContext.get_current_span_id() is None
        assert TraceContext.get_current_span() is None

    def test_get_context(self):
        """Test getting context as dict."""
        TraceContext.set_current_trace_id("trace-id")
        TraceContext.set_current_span_id("span-id")

        context = TraceContext.get_context()

        assert context["trace_id"] == "trace-id"
        assert context["span_id"] == "span-id"

    def test_set_context(self):
        """Test setting context from values."""
        TraceContext.set_context(trace_id="trace-id", span_id="span-id")

        assert TraceContext.get_current_trace_id() == "trace-id"
        assert TraceContext.get_current_span_id() == "span-id"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_new_trace_function(self):
        """Test new_trace convenience function."""
        trace_id = new_trace()

        assert trace_id is not None
        assert get_current_trace_id() == trace_id

    def test_get_functions(self):
        """Test get convenience functions."""
        TraceContext.set_current_trace_id("trace-id")
        TraceContext.set_current_span_id("span-id")

        assert get_current_trace_id() == "trace-id"
        assert get_current_span_id() == "span-id"

    def test_clear_context_function(self):
        """Test clear_context convenience function."""
        TraceContext.set_current_trace_id("trace-id")

        clear_context()

        assert get_current_trace_id() is None
