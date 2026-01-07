"""Unit tests for span module."""

import pytest
from datetime import datetime
from agenttrace.span import Span, create_span
from agenttrace.schema import SpanType, SpanStatus, Framework, Message, TokenUsage
from agenttrace.context import TraceContext, clear_context


class TestSpan:
    """Tests for Span class."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_span_creation(self):
        """Test creating a span."""
        span = Span(
            trace_id="trace-123",
            name="test-span",
            span_type=SpanType.LLM_CALL,
        )

        assert span.trace_id == "trace-123"
        assert span.name == "test-span"
        assert span.span_type == SpanType.LLM_CALL
        assert span.span_id is not None
        assert span.start_time is not None
        assert span.status == SpanStatus.UNSET

    def test_span_auto_id_generation(self):
        """Test automatic span ID generation."""
        span = Span(trace_id="trace-123", name="test")

        assert span.span_id is not None
        assert len(span.span_id) > 0

    def test_span_parent_from_context(self):
        """Test parent span detection from context."""
        # Set current span in context
        TraceContext.set_current_span_id("parent-span-id")

        span = Span(trace_id="trace-123", name="child")

        assert span.parent_span_id == "parent-span-id"

    def test_set_attribute(self):
        """Test setting attributes."""
        span = Span(trace_id="trace-123", name="test")

        result = span.set_attribute("key", "value")

        assert result is span  # Method chaining
        assert span.attributes["key"] == "value"

    def test_set_attributes(self):
        """Test setting multiple attributes."""
        span = Span(trace_id="trace-123", name="test")

        span.set_attributes({
            "key1": "value1",
            "key2": "value2",
        })

        assert span.attributes["key1"] == "value1"
        assert span.attributes["key2"] == "value2"

    def test_set_input_output(self):
        """Test setting input and output."""
        span = Span(trace_id="trace-123", name="test")

        span.set_input({"query": "hello"})
        span.set_output({"response": "hi"})

        assert span.input == {"query": "hello"}
        assert span.output == {"response": "hi"}

    def test_set_llm_metadata(self):
        """Test setting LLM metadata."""
        span = Span(
            trace_id="trace-123",
            name="llm-call",
            span_type=SpanType.LLM_CALL,
        )

        usage = TokenUsage(prompt_tokens=10, completion_tokens=20)
        span.set_llm_metadata(
            model="gpt-4",
            provider="openai",
            temperature=0.7,
            usage=usage,
        )

        assert span.llm is not None
        assert span.llm.model == "gpt-4"
        assert span.llm.provider == "openai"
        assert span.llm.temperature == 0.7
        assert span.llm.usage == usage

    def test_set_tool_metadata(self):
        """Test setting tool metadata."""
        span = Span(
            trace_id="trace-123",
            name="tool-call",
            span_type=SpanType.TOOL_CALL,
        )

        span.set_tool_metadata(
            tool_name="calculator",
            tool_input={"operation": "add", "a": 1, "b": 2},
            tool_output={"result": 3},
        )

        assert span.tool is not None
        assert span.tool.tool_name == "calculator"
        assert span.tool.tool_input == {"operation": "add", "a": 1, "b": 2}
        assert span.tool.tool_output == {"result": 3}

    def test_set_retrieval_metadata(self):
        """Test setting retrieval metadata."""
        span = Span(
            trace_id="trace-123",
            name="retrieval",
            span_type=SpanType.RETRIEVAL,
        )

        span.set_retrieval_metadata(
            query="AI applications",
            collection="documents",
            top_k=5,
            results=[{"id": "1", "text": "content"}],
            scores=[0.95],
        )

        assert span.retrieval is not None
        assert span.retrieval.query == "AI applications"
        assert span.retrieval.collection == "documents"
        assert span.retrieval.top_k == 5
        assert span.retrieval.num_results == 1

    def test_record_exception(self):
        """Test recording an exception."""
        span = Span(trace_id="trace-123", name="test")

        try:
            raise ValueError("Test error")
        except ValueError as e:
            span.record_exception(e)

        assert span.error is not None
        assert span.error["type"] == "ValueError"
        assert span.error["message"] == "Test error"
        assert span.status == SpanStatus.ERROR
        assert len(span.events) == 1

    def test_add_tag(self):
        """Test adding tags."""
        span = Span(trace_id="trace-123", name="test")

        span.add_tag("production")
        span.add_tag("experiment")

        assert "production" in span.tags
        assert "experiment" in span.tags

    def test_add_tags(self):
        """Test adding multiple tags."""
        span = Span(trace_id="trace-123", name="test")

        span.add_tags(["tag1", "tag2", "tag3"])

        assert "tag1" in span.tags
        assert "tag2" in span.tags
        assert "tag3" in span.tags

    def test_end_span(self):
        """Test ending a span."""
        span = Span(trace_id="trace-123", name="test")

        assert span.end_time is None
        assert span.is_ended() is False

        span.end()

        assert span.end_time is not None
        assert span.status == SpanStatus.OK
        assert span.is_ended() is True

    def test_end_span_with_status(self):
        """Test ending a span with specific status."""
        span = Span(trace_id="trace-123", name="test")

        span.end(SpanStatus.ERROR)

        assert span.status == SpanStatus.ERROR

    def test_end_span_idempotent(self):
        """Test that ending a span multiple times is safe."""
        span = Span(trace_id="trace-123", name="test")

        span.end()
        first_end_time = span.end_time

        span.end()
        second_end_time = span.end_time

        assert first_end_time == second_end_time

    def test_span_context_manager(self):
        """Test using span as context manager."""
        span = Span(trace_id="trace-123", name="test")

        with span as s:
            assert s is span
            assert TraceContext.get_current_span() is span
            assert span.is_ended() is False

        assert span.is_ended() is True
        assert span.status == SpanStatus.OK

    def test_span_context_manager_with_exception(self):
        """Test span context manager with exception."""
        span = Span(trace_id="trace-123", name="test")

        with pytest.raises(ValueError):
            with span:
                raise ValueError("Test error")

        assert span.is_ended() is True
        assert span.status == SpanStatus.ERROR
        assert span.error is not None

    def test_duration_property(self):
        """Test duration calculation."""
        span = Span(trace_id="trace-123", name="test")

        assert span.duration is None  # Not ended yet

        span.end()

        assert span.duration is not None
        assert span.duration >= 0

    def test_is_root_property(self):
        """Test is_root property."""
        root_span = Span(
            trace_id="trace-123",
            name="root",
            parent_span_id=None,
        )
        child_span = Span(
            trace_id="trace-123",
            name="child",
            parent_span_id="parent-id",
        )

        assert root_span.is_root is True
        assert child_span.is_root is False


class TestCreateSpan:
    """Tests for create_span helper function."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_create_span_with_trace_id(self):
        """Test creating span with explicit trace ID."""
        span = create_span(
            name="test",
            trace_id="trace-123",
            span_type=SpanType.LLM_CALL,
        )

        assert span.trace_id == "trace-123"
        assert span.name == "test"
        assert span.span_type == SpanType.LLM_CALL

    def test_create_span_auto_trace_id(self):
        """Test creating span with auto-generated trace ID."""
        span = create_span(name="test")

        assert span.trace_id is not None
        assert TraceContext.get_current_trace_id() == span.trace_id

    def test_create_span_uses_context_trace_id(self):
        """Test that create_span uses trace ID from context."""
        TraceContext.set_current_trace_id("context-trace-id")

        span = create_span(name="test")

        assert span.trace_id == "context-trace-id"

    def test_create_span_with_parent(self):
        """Test creating span with parent."""
        parent = create_span(name="parent", trace_id="trace-123")

        with TraceContext.span_context(parent):
            child = create_span(name="child", trace_id="trace-123")

            assert child.parent_span_id == parent.span_id
