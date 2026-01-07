"""
Main client interface for AgentTrace SDK.

Provides the primary AgentTrace class with methods for creating traces,
spans, and decorators for automatic instrumentation.
"""

import functools
import atexit
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Callable
from queue import Queue, Empty

from .config import AgentTraceConfig, ExportMode
from .context import TraceContext
from .span import Span, create_span
from .exporter import SpanExporter, create_exporter
from .schema import SpanType, Framework, Message, TokenUsage


class AgentTrace:
    """
    Main AgentTrace client for tracing AI agents.

    This is the primary interface for the AgentTrace SDK. It handles:
    - Configuration management
    - Span creation and export
    - Context management
    - Automatic instrumentation via decorators

    Example:
        >>> trace = AgentTrace(
        ...     api_key="my-key",
        ...     project_id="my-project"
        ... )
        >>>
        >>> # Use context manager
        >>> with trace.span("my-operation") as span:
        ...     span.set_attribute("key", "value")
        ...     # Do work...
        >>>
        >>> # Use decorator
        >>> @trace.trace_agent(name="my-agent")
        >>> def my_agent():
        ...     return "result"
        >>>
        >>> # Shutdown when done
        >>> trace.shutdown()
    """

    # Global instance for singleton pattern
    _instance: Optional["AgentTrace"] = None
    _lock = threading.Lock()

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        config: Optional[AgentTraceConfig] = None,
        **kwargs,
    ):
        """
        Initialize AgentTrace client.

        Args:
            api_key: API key for authentication (can also use AGENTTRACE_API_KEY env var)
            project_id: Project identifier (can also use AGENTTRACE_PROJECT_ID env var)
            config: Pre-configured AgentTraceConfig (overrides other params)
            **kwargs: Additional config parameters

        Example:
            >>> trace = AgentTrace(api_key="my-key", project_id="my-project")
            >>> trace = AgentTrace(config=AgentTraceConfig.from_env())
        """
        # Use provided config or create from parameters
        if config is None:
            config_kwargs = kwargs.copy()
            if api_key:
                config_kwargs["api_key"] = api_key
            if project_id:
                config_kwargs["project_id"] = project_id

            self.config = AgentTraceConfig.from_env(**config_kwargs)
        else:
            self.config = config

        # Create exporter
        self.exporter = create_exporter(self.config)

        # Span queue for async export
        self.span_queue: Queue = Queue(maxsize=self.config.max_queue_size)

        # Worker thread for async export
        self._worker_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

        # Start worker thread if async mode
        if self.config.export_mode == ExportMode.ASYNC:
            self._start_worker()

        # Register shutdown handler
        atexit.register(self.shutdown)

    def _start_worker(self) -> None:
        """Start background worker thread for async export."""
        if self._worker_thread is not None:
            return

        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="agenttrace-worker",
        )
        self._worker_thread.start()

    def _worker_loop(self) -> None:
        """Worker loop for async span export."""
        batch: List[Span] = []
        last_flush = time.time()

        while not self._shutdown_event.is_set():
            try:
                # Try to get span from queue with timeout
                span = self.span_queue.get(timeout=1.0)
                batch.append(span)

                # Check if we should flush
                should_flush = (
                    len(batch) >= self.config.batch_size
                    or time.time() - last_flush >= self.config.flush_interval
                )

                if should_flush:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = time.time()

            except Empty:
                # Timeout - flush if we have any spans
                if batch:
                    self._flush_batch(batch)
                    batch = []
                    last_flush = time.time()

        # Flush remaining spans on shutdown
        if batch:
            self._flush_batch(batch)

    def _flush_batch(self, batch: List[Span]) -> None:
        """Flush a batch of spans to the exporter."""
        if not batch:
            return

        try:
            # Convert Span instances to SchemaSpan for export
            schema_spans = [span for span in batch]
            self.exporter.export(schema_spans)
        except Exception as e:
            print(f"Error flushing batch: {e}")

    def span(
        self,
        name: str,
        span_type: SpanType = SpanType.SPAN,
        framework: Framework = Framework.UNKNOWN,
        **kwargs,
    ) -> Span:
        """
        Create a new span.

        The span will automatically use the current trace context or create
        a new trace if no context exists.

        Args:
            name: Span name
            span_type: Type of operation
            framework: Framework that generated this span
            **kwargs: Additional span parameters

        Returns:
            Span: New span instance (use as context manager)

        Example:
            >>> with trace.span("my-operation", SpanType.LLM_CALL) as span:
            ...     span.set_attribute("model", "gpt-4")
            ...     # Do work...
        """
        # Get or create trace context
        trace_id = TraceContext.get_current_trace_id()
        if trace_id is None:
            trace_id = str(uuid.uuid4())
            TraceContext.set_current_trace_id(trace_id)

        # Create span
        span = create_span(
            name=name,
            span_type=span_type,
            trace_id=trace_id,
            framework=framework,
            **kwargs,
        )

        # Set up span to export on exit
        original_exit = span.__exit__

        def new_exit(exc_type, exc_val, exc_tb):
            result = original_exit(exc_type, exc_val, exc_tb)
            self._export_span(span)
            return result

        span.__exit__ = new_exit

        return span

    @contextmanager
    def trace(
        self,
        name: str,
        trace_id: Optional[str] = None,
        framework: Framework = Framework.UNKNOWN,
        **kwargs,
    ):
        """
        Create a new trace context.

        This creates a root span and sets up the trace context for child spans.

        Args:
            name: Trace name
            trace_id: Optional trace ID (generated if not provided)
            framework: Framework that generated this trace
            **kwargs: Additional span parameters

        Yields:
            Span: Root span of the trace

        Example:
            >>> with trace.trace("my-agent-run") as root_span:
            ...     root_span.set_attribute("user_id", "123")
            ...
            ...     # Child spans will automatically be part of this trace
            ...     with trace.span("llm-call", SpanType.LLM_CALL) as child:
            ...         # Do work...
            ...         pass
        """
        # Create new trace ID if not provided
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        # Set trace context
        with TraceContext.trace_context(trace_id):
            # Create root span
            root_span = create_span(
                name=name,
                span_type=SpanType.ROOT,
                trace_id=trace_id,
                parent_span_id=None,
                framework=framework,
                **kwargs,
            )

            with root_span:
                try:
                    yield root_span
                finally:
                    self._export_span(root_span)

    def _export_span(self, span: Span) -> None:
        """Export a span based on configuration."""
        if not self.config.enabled:
            return

        if self.config.export_mode == ExportMode.SYNC:
            # Synchronous export
            self.exporter.export([span])
        elif self.config.export_mode == ExportMode.ASYNC:
            # Asynchronous export via queue
            try:
                self.span_queue.put_nowait(span)
            except Exception:
                # Queue full - export synchronously as fallback
                self.exporter.export([span])

    def trace_agent(
        self,
        name: Optional[str] = None,
        framework: Framework = Framework.UNKNOWN,
        **span_kwargs,
    ) -> Callable:
        """
        Decorator to automatically trace a function as an agent operation.

        Creates a root span for the entire function execution.

        Args:
            name: Custom name for the trace (defaults to function name)
            framework: Framework that generated this trace
            **span_kwargs: Additional span parameters

        Returns:
            Callable: Decorated function

        Example:
            >>> @trace.trace_agent(name="my-agent", framework=Framework.LANGCHAIN)
            >>> def my_agent(query: str) -> str:
            ...     # Agent logic here
            ...     return "response"
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                trace_name = name or func.__name__

                with self.trace(trace_name, framework=framework, **span_kwargs) as span:
                    # Capture input if enabled
                    if self.config.capture_input:
                        span.set_input({
                            "args": args,
                            "kwargs": kwargs,
                        })

                    # Execute function
                    try:
                        result = func(*args, **kwargs)

                        # Capture output if enabled
                        if self.config.capture_output:
                            span.set_output(result)

                        return result
                    except Exception as e:
                        span.record_exception(e)
                        raise

            return wrapper

        return decorator

    def trace_llm(
        self,
        name: Optional[str] = None,
        model: Optional[str] = None,
        **span_kwargs,
    ) -> Callable:
        """
        Decorator to automatically trace LLM calls.

        Creates a span with span_type=LLM_CALL and captures LLM metadata.

        Args:
            name: Custom name for the span (defaults to function name)
            model: Model name (if known in advance)
            **span_kwargs: Additional span parameters

        Returns:
            Callable: Decorated function

        Example:
            >>> @trace.trace_llm(name="generate-response", model="gpt-4")
            >>> def call_llm(messages: List[Message]) -> str:
            ...     # LLM call logic here
            ...     return "response"
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                span_name = name or func.__name__

                with self.span(span_name, SpanType.LLM_CALL, **span_kwargs) as span:
                    # Capture input if enabled
                    if self.config.capture_input:
                        span.set_input({
                            "args": args,
                            "kwargs": kwargs,
                        })

                    # Set model if provided
                    if model:
                        span.set_attribute("model", model)

                    # Execute function
                    try:
                        result = func(*args, **kwargs)

                        # Capture output if enabled
                        if self.config.capture_output:
                            span.set_output(result)

                        return result
                    except Exception as e:
                        span.record_exception(e)
                        raise

            return wrapper

        return decorator

    def trace_tool(
        self,
        name: Optional[str] = None,
        tool_name: Optional[str] = None,
        **span_kwargs,
    ) -> Callable:
        """
        Decorator to automatically trace tool calls.

        Creates a span with span_type=TOOL_CALL and captures tool metadata.

        Args:
            name: Custom name for the span (defaults to function name)
            tool_name: Name of the tool (defaults to function name)
            **span_kwargs: Additional span parameters

        Returns:
            Callable: Decorated function

        Example:
            >>> @trace.trace_tool(name="calculator-add", tool_name="calculator")
            >>> def add(a: int, b: int) -> int:
            ...     return a + b
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                span_name = name or func.__name__
                actual_tool_name = tool_name or func.__name__

                with self.span(span_name, SpanType.TOOL_CALL, **span_kwargs) as span:
                    # Set tool metadata
                    span.set_tool_metadata(
                        tool_name=actual_tool_name,
                        tool_input={"args": args, "kwargs": kwargs} if self.config.capture_input else None,
                    )

                    # Execute function
                    try:
                        result = func(*args, **kwargs)

                        # Update tool output
                        if self.config.capture_output and span.tool:
                            span.tool.tool_output = result

                        return result
                    except Exception as e:
                        if span.tool:
                            span.tool.tool_error = str(e)
                        span.record_exception(e)
                        raise

            return wrapper

        return decorator

    def flush(self) -> None:
        """
        Flush all pending spans.

        Forces immediate export of all queued spans. Useful before shutdown
        or at critical checkpoints.

        Example:
            >>> trace.flush()
        """
        # Drain the queue
        batch = []
        try:
            while True:
                span = self.span_queue.get_nowait()
                batch.append(span)
        except Empty:
            pass

        # Flush the batch
        if batch:
            self._flush_batch(batch)

        # Also flush the exporter
        self.exporter.force_flush()

    def shutdown(self) -> None:
        """
        Shutdown the AgentTrace client.

        Stops the worker thread, flushes all pending spans, and closes
        the exporter. Should be called when the client is no longer needed.

        Example:
            >>> trace.shutdown()
        """
        # Signal worker to stop
        self._shutdown_event.set()

        # Wait for worker to finish
        if self._worker_thread is not None:
            self._worker_thread.join(timeout=5.0)

        # Flush any remaining spans
        self.flush()

        # Shutdown exporter
        self.exporter.shutdown()

    @classmethod
    def get_instance(cls) -> Optional["AgentTrace"]:
        """
        Get the global AgentTrace instance.

        Returns:
            Optional[AgentTrace]: Global instance or None

        Example:
            >>> trace = AgentTrace.get_instance()
        """
        return cls._instance

    @classmethod
    def set_instance(cls, instance: "AgentTrace") -> None:
        """
        Set the global AgentTrace instance.

        Args:
            instance: AgentTrace instance to set as global

        Example:
            >>> trace = AgentTrace(api_key="my-key")
            >>> AgentTrace.set_instance(trace)
        """
        with cls._lock:
            cls._instance = instance

    @classmethod
    def init(cls, **kwargs) -> "AgentTrace":
        """
        Initialize and set the global AgentTrace instance.

        Convenience method that creates an instance and sets it as global.

        Args:
            **kwargs: Arguments to pass to AgentTrace constructor

        Returns:
            AgentTrace: The created instance

        Example:
            >>> trace = AgentTrace.init(
            ...     api_key="my-key",
            ...     project_id="my-project"
            ... )
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance.shutdown()

            cls._instance = cls(**kwargs)
            return cls._instance

    @classmethod
    def instrument_langchain(cls) -> None:
        """
        Enable automatic instrumentation for LangChain.

        Patches LangChain to automatically trace all operations including:
        - LLM calls
        - Chain executions
        - Agent steps
        - Tool invocations
        - Retriever queries

        Must be called after AgentTrace.init().

        Example:
            >>> trace = AgentTrace.init()
            >>> AgentTrace.instrument_langchain()
            >>>
            >>> # Now all LangChain operations are automatically traced
            >>> from langchain.chains import LLMChain
            >>> chain = LLMChain(...)
            >>> chain.run("query")  # Automatically traced!

        Note:
            Auto-instrumentation is currently in development.
            Use manual instrumentation with decorators for now.
        """
        from .integrations import get_integration

        instance = cls.get_instance()
        if instance is None:
            raise RuntimeError(
                "AgentTrace must be initialized before enabling instrumentation. "
                "Call AgentTrace.init() first."
            )

        integration = get_integration("langchain", instance)
        integration.enable()

    @classmethod
    def instrument_openai(cls) -> None:
        """
        Enable automatic instrumentation for OpenAI API.

        Patches OpenAI SDK to automatically trace all API calls including:
        - ChatCompletion calls
        - Completion calls
        - Embedding calls
        - All other OpenAI API interactions

        Must be called after AgentTrace.init().

        Example:
            >>> trace = AgentTrace.init()
            >>> AgentTrace.instrument_openai()
            >>>
            >>> # Now all OpenAI calls are automatically traced
            >>> import openai
            >>> openai.ChatCompletion.create(...)  # Automatically traced!

        Note:
            Auto-instrumentation is currently in development.
            Use manual instrumentation with decorators for now.
        """
        from .integrations import get_integration

        instance = cls.get_instance()
        if instance is None:
            raise RuntimeError(
                "AgentTrace must be initialized before enabling instrumentation. "
                "Call AgentTrace.init() first."
            )

        integration = get_integration("openai", instance)
        integration.enable()

    @classmethod
    def instrument_crewai(cls) -> None:
        """
        Enable automatic instrumentation for CrewAI.

        Patches CrewAI to automatically trace all operations including:
        - Agent executions
        - Task executions
        - Crew workflows
        - Tool invocations

        Must be called after AgentTrace.init().

        Example:
            >>> trace = AgentTrace.init()
            >>> AgentTrace.instrument_crewai()
            >>>
            >>> # Now all CrewAI operations are automatically traced
            >>> from crewai import Agent, Task, Crew
            >>> crew = Crew(...)
            >>> crew.kickoff()  # Automatically traced!

        Note:
            Auto-instrumentation is currently in development.
            Use manual instrumentation with decorators for now.
        """
        from .integrations import get_integration

        instance = cls.get_instance()
        if instance is None:
            raise RuntimeError(
                "AgentTrace must be initialized before enabling instrumentation. "
                "Call AgentTrace.init() first."
            )

        integration = get_integration("crewai", instance)
        integration.enable()


# Global convenience functions

def init(**kwargs) -> AgentTrace:
    """
    Initialize the global AgentTrace instance.

    Convenience function for AgentTrace.init().

    Args:
        **kwargs: Arguments to pass to AgentTrace constructor

    Returns:
        AgentTrace: The created instance

    Example:
        >>> import agenttrace
        >>> trace = agenttrace.init(api_key="my-key", project_id="my-project")
    """
    return AgentTrace.init(**kwargs)


def get_client() -> Optional[AgentTrace]:
    """
    Get the global AgentTrace instance.

    Convenience function for AgentTrace.get_instance().

    Returns:
        Optional[AgentTrace]: Global instance or None

    Example:
        >>> import agenttrace
        >>> trace = agenttrace.get_client()
    """
    return AgentTrace.get_instance()


def shutdown() -> None:
    """
    Shutdown the global AgentTrace instance.

    Convenience function for shutting down the global instance.

    Example:
        >>> import agenttrace
        >>> agenttrace.shutdown()
    """
    instance = AgentTrace.get_instance()
    if instance:
        instance.shutdown()
