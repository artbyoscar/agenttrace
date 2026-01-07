"""Comprehensive unit tests for client module."""

import pytest
import time
from agenttrace.client import AgentTrace, init, get_client, shutdown
from agenttrace.config import AgentTraceConfig, ExportMode
from agenttrace.schema import SpanType, Framework
from agenttrace.context import TraceContext, clear_context


class TestAgentTraceClient:
    """Tests for AgentTrace client class."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context and shutdown client after each test."""
        clear_context()
        if AgentTrace.get_instance():
            AgentTrace.get_instance().shutdown()
            AgentTrace._instance = None

    def test_client_initialization(self):
        """Test initializing client."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            enabled=False,  # Disable for testing
        )

        assert trace.config.api_key == "test-key"
        assert trace.config.project_id == "test-project"
        assert trace.exporter is not None

    def test_client_with_config(self):
        """Test initializing client with config object."""
        config = AgentTraceConfig(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        trace = AgentTrace(config=config)

        assert trace.config == config

    def test_span_creation(self):
        """Test creating a span."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        with trace.span("test-operation") as span:
            assert span.name == "test-operation"
            assert span.span_type == SpanType.SPAN
            assert span.trace_id is not None

    def test_span_with_type(self):
        """Test creating a span with specific type."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        with trace.span("llm-call", SpanType.LLM_CALL) as span:
            assert span.span_type == SpanType.LLM_CALL

    def test_trace_context_manager(self):
        """Test creating a trace context."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        with trace.trace("my-agent") as root_span:
            assert root_span.span_type == SpanType.ROOT
            assert root_span.parent_span_id is None

            # Child spans automatically use the trace context
            with trace.span("child-operation") as child:
                assert child.trace_id == root_span.trace_id
                assert child.parent_span_id == root_span.span_id

    def test_trace_agent_decorator(self):
        """Test @trace_agent decorator."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        @trace.trace_agent(name="my-agent", framework=Framework.LANGCHAIN)
        def my_agent(query: str) -> str:
            return f"Response to: {query}"

        result = my_agent("test query")

        assert result == "Response to: test query"

    def test_trace_agent_decorator_captures_input_output(self):
        """Test that @trace_agent captures input/output."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
            capture_input=True,
            capture_output=True,
        )

        captured_span = None

        @trace.trace_agent(name="my-agent")
        def my_agent(x: int, y: int) -> int:
            nonlocal captured_span
            captured_span = TraceContext.get_current_span()
            return x + y

        result = my_agent(1, 2)

        assert result == 3
        assert captured_span is not None
        assert captured_span.input is not None
        assert captured_span.output == 3

    def test_trace_agent_decorator_handles_exceptions(self):
        """Test that @trace_agent handles exceptions."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        @trace.trace_agent(name="failing-agent")
        def failing_agent():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            failing_agent()

    def test_trace_llm_decorator(self):
        """Test @trace_llm decorator."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        @trace.trace_llm(name="llm-call", model="gpt-4")
        def call_llm(prompt: str) -> str:
            return f"Response to: {prompt}"

        result = call_llm("test prompt")

        assert result == "Response to: test prompt"

    def test_trace_tool_decorator(self):
        """Test @trace_tool decorator."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        @trace.trace_tool(name="calculator", tool_name="add")
        def add(a: int, b: int) -> int:
            return a + b

        result = add(1, 2)

        assert result == 3

    def test_trace_tool_decorator_handles_errors(self):
        """Test that @trace_tool records errors."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        @trace.trace_tool(tool_name="failing-tool")
        def failing_tool():
            raise RuntimeError("Tool failed")

        with pytest.raises(RuntimeError):
            failing_tool()

    def test_flush(self):
        """Test flushing pending spans."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.ASYNC,
            enabled=False,
        )

        # Add some spans to the queue
        with trace.span("test1"):
            pass
        with trace.span("test2"):
            pass

        # Flush should not raise
        trace.flush()

    def test_shutdown(self):
        """Test shutting down client."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.ASYNC,
            enabled=False,
        )

        # Shutdown should not raise
        trace.shutdown()

    def test_singleton_pattern(self):
        """Test singleton instance management."""
        trace1 = AgentTrace.init(
            api_key="test-key",
            project_id="test-project",
            enabled=False,
        )

        trace2 = AgentTrace.get_instance()

        assert trace1 is trace2

    def test_global_init_function(self):
        """Test global init function."""
        trace = init(
            api_key="test-key",
            project_id="test-project",
            enabled=False,
        )

        assert trace is not None
        assert get_client() is trace

    def test_global_shutdown_function(self):
        """Test global shutdown function."""
        init(
            api_key="test-key",
            project_id="test-project",
            enabled=False,
        )

        shutdown()

        assert get_client() is None


class TestAsyncExport:
    """Tests for async export functionality."""

    def teardown_method(self):
        """Shutdown client after each test."""
        if AgentTrace.get_instance():
            AgentTrace.get_instance().shutdown()
            AgentTrace._instance = None

    def test_async_export_worker_starts(self):
        """Test that async worker thread starts."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.ASYNC,
            enabled=False,
        )

        assert trace._worker_thread is not None
        assert trace._worker_thread.is_alive()

    def test_sync_export_no_worker(self):
        """Test that sync mode doesn't start worker."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.SYNC,
            enabled=False,
        )

        assert trace._worker_thread is None


class TestContextPropagation:
    """Tests for context propagation."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context and shutdown client after each test."""
        clear_context()
        if AgentTrace.get_instance():
            AgentTrace.get_instance().shutdown()
            AgentTrace._instance = None

    def test_nested_spans_hierarchy(self):
        """Test that nested spans maintain hierarchy."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        with trace.trace("root") as root:
            with trace.span("child1") as child1:
                assert child1.parent_span_id == root.span_id

                with trace.span("grandchild") as grandchild:
                    assert grandchild.parent_span_id == child1.span_id

            with trace.span("child2") as child2:
                assert child2.parent_span_id == root.span_id

    def test_parallel_traces_isolated(self):
        """Test that parallel traces are isolated."""
        trace = AgentTrace(
            api_key="test-key",
            project_id="test-project",
            export_mode=ExportMode.DISABLED,
        )

        trace_id1 = None
        trace_id2 = None

        with trace.trace("trace1") as root1:
            trace_id1 = root1.trace_id

        with trace.trace("trace2") as root2:
            trace_id2 = root2.trace_id

        assert trace_id1 != trace_id2
