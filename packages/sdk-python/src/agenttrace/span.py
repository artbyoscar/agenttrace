"""
Span creation and management for AgentTrace SDK.

Extends the schema Span dataclass with SDK-specific functionality for
creating, managing, and exporting spans with automatic timing and
context management.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
import traceback as tb
import uuid

from .schema import (
    Span as BaseSpan,
    SpanType,
    SpanStatus,
    Framework,
    LLMCall,
    ToolCall,
    RetrievalCall,
    Message,
    TokenUsage,
    SpanEvent,
)
from .context import TraceContext


class Span(BaseSpan):
    """
    Extended Span class with SDK functionality.

    Inherits from schema.Span and adds methods for:
    - Automatic timing
    - Context management
    - Metadata setting
    - LLM/Tool/Retrieval metadata helpers
    - Error handling

    Example:
        >>> span = Span(
        ...     trace_id="abc123",
        ...     name="my-operation",
        ...     span_type=SpanType.LLM_CALL
        ... )
        >>> span.set_attribute("key", "value")
        >>> span.set_input({"query": "hello"})
        >>> # Do work...
        >>> span.set_output({"response": "hi there"})
        >>> span.end()
    """

    def __init__(
        self,
        trace_id: str,
        name: str,
        span_type: SpanType = SpanType.SPAN,
        parent_span_id: Optional[str] = None,
        span_id: Optional[str] = None,
        framework: Framework = Framework.UNKNOWN,
        **kwargs,
    ):
        """
        Initialize a new span.

        Args:
            trace_id: Trace ID this span belongs to
            name: Human-readable span name
            span_type: Type of operation
            parent_span_id: Parent span ID (auto-detected from context if None)
            span_id: Span ID (auto-generated if None)
            framework: Framework that generated this span
            **kwargs: Additional fields for the span
        """
        # Generate span_id if not provided
        if span_id is None:
            span_id = str(uuid.uuid4())

        # Auto-detect parent from context if not provided
        if parent_span_id is None:
            parent_span_id = TraceContext.get_current_span_id()

        # Initialize base span with automatic start time
        super().__init__(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            start_time=datetime.utcnow(),
            span_type=span_type,
            framework=framework,
            **kwargs,
        )

        # Track if span has been ended
        self._ended = False

    def set_attribute(self, key: str, value: Any) -> "Span":
        """
        Set a custom attribute on the span.

        Args:
            key: Attribute key
            value: Attribute value

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.set_attribute("user_id", "123")
            >>> span.set_attribute("model", "gpt-4")
        """
        self.attributes[key] = value
        return self

    def set_attributes(self, attributes: Dict[str, Any]) -> "Span":
        """
        Set multiple attributes at once.

        Args:
            attributes: Dictionary of attributes

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.set_attributes({
            ...     "user_id": "123",
            ...     "model": "gpt-4",
            ...     "temperature": 0.7
            ... })
        """
        self.attributes.update(attributes)
        return self

    def set_input(self, input_data: Any) -> "Span":
        """
        Set the input data for this span.

        Used for replay functionality and debugging.

        Args:
            input_data: Input data (can be any JSON-serializable type)

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.set_input({"query": "What is AI?"})
            >>> span.set_input("User query text")
        """
        self.input = input_data
        return self

    def set_output(self, output_data: Any) -> "Span":
        """
        Set the output data for this span.

        Used for replay functionality and debugging.

        Args:
            output_data: Output data (can be any JSON-serializable type)

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.set_output({"response": "AI is..."})
            >>> span.set_output("Response text")
        """
        self.output = output_data
        return self

    def set_llm_metadata(
        self,
        model: str,
        messages: Optional[List[Message]] = None,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response: Optional[str] = None,
        usage: Optional[TokenUsage] = None,
        **kwargs,
    ) -> "Span":
        """
        Set LLM-specific metadata.

        Automatically creates an LLMCall object and attaches it to the span.

        Args:
            model: Model name (e.g., "gpt-4")
            messages: Conversation messages
            provider: Provider (e.g., "openai")
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            response: Generated response
            usage: Token usage statistics
            **kwargs: Additional LLMCall parameters

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.set_llm_metadata(
            ...     model="gpt-4",
            ...     provider="openai",
            ...     temperature=0.7,
            ...     usage=TokenUsage(prompt_tokens=10, completion_tokens=20)
            ... )
        """
        self.llm = LLMCall(
            model=model,
            messages=messages or [],
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            response=response,
            usage=usage,
            **kwargs,
        )
        return self

    def set_tool_metadata(
        self,
        tool_name: str,
        tool_input: Optional[Dict[str, Any]] = None,
        tool_output: Optional[Any] = None,
        tool_error: Optional[str] = None,
        **kwargs,
    ) -> "Span":
        """
        Set tool-specific metadata.

        Automatically creates a ToolCall object and attaches it to the span.

        Args:
            tool_name: Name of the tool
            tool_input: Tool input parameters
            tool_output: Tool output
            tool_error: Error message if failed
            **kwargs: Additional ToolCall parameters

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.set_tool_metadata(
            ...     tool_name="calculator",
            ...     tool_input={"operation": "add", "a": 1, "b": 2},
            ...     tool_output={"result": 3}
            ... )
        """
        self.tool = ToolCall(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            tool_error=tool_error,
            **kwargs,
        )
        return self

    def set_retrieval_metadata(
        self,
        query: str,
        collection: Optional[str] = None,
        top_k: Optional[int] = None,
        results: Optional[List[Dict[str, Any]]] = None,
        scores: Optional[List[float]] = None,
        **kwargs,
    ) -> "Span":
        """
        Set retrieval-specific metadata.

        Automatically creates a RetrievalCall object and attaches it to the span.

        Args:
            query: Query text
            collection: Collection/index name
            top_k: Number of results requested
            results: Retrieved documents
            scores: Similarity scores
            **kwargs: Additional RetrievalCall parameters

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.set_retrieval_metadata(
            ...     query="AI applications",
            ...     collection="documents",
            ...     top_k=5,
            ...     results=[{"id": "1", "text": "..."}],
            ...     scores=[0.95, 0.87, 0.82]
            ... )
        """
        self.retrieval = RetrievalCall(
            query=query,
            collection=collection,
            top_k=top_k,
            results=results,
            scores=scores,
            num_results=len(results) if results else None,
            **kwargs,
        )
        return self

    def record_exception(
        self, exception: Exception, set_status_error: bool = True
    ) -> "Span":
        """
        Record an exception on the span.

        Automatically extracts exception type, message, and traceback.

        Args:
            exception: The exception to record
            set_status_error: Whether to set span status to ERROR

        Returns:
            Span: Self for method chaining

        Example:
            >>> try:
            ...     risky_operation()
            ... except Exception as e:
            ...     span.record_exception(e)
        """
        self.error = {
            "type": type(exception).__name__,
            "message": str(exception),
            "traceback": "".join(tb.format_exception(type(exception), exception, exception.__traceback__)),
        }

        if set_status_error:
            self.status = SpanStatus.ERROR

        # Also add as an event
        self.add_event(
            "exception",
            attributes={
                "exception.type": type(exception).__name__,
                "exception.message": str(exception),
            },
        )

        return self

    def add_tag(self, tag: str) -> "Span":
        """
        Add a tag to the span.

        Args:
            tag: Tag to add

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.add_tag("production")
            >>> span.add_tag("experiment-v2")
        """
        if tag not in self.tags:
            self.tags.append(tag)
        return self

    def add_tags(self, tags: List[str]) -> "Span":
        """
        Add multiple tags to the span.

        Args:
            tags: List of tags to add

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.add_tags(["production", "high-priority"])
        """
        for tag in tags:
            self.add_tag(tag)
        return self

    def end(self, status: Optional[SpanStatus] = None) -> "Span":
        """
        End the span.

        Sets the end time and finalizes the status. This method is idempotent
        and can be called multiple times safely.

        Args:
            status: Optional status to set (defaults to OK if not ERROR)

        Returns:
            Span: Self for method chaining

        Example:
            >>> span.end()
            >>> span.end(SpanStatus.OK)
        """
        if self._ended:
            return self

        self.end_time = datetime.utcnow()

        if status:
            self.status = status
        elif self.status == SpanStatus.UNSET:
            self.status = SpanStatus.OK

        self._ended = True
        return self

    def is_ended(self) -> bool:
        """
        Check if the span has been ended.

        Returns:
            bool: True if span has been ended

        Example:
            >>> if not span.is_ended():
            ...     span.end()
        """
        return self._ended

    def __enter__(self) -> "Span":
        """
        Enter the span context.

        Makes this span the current span in the context.

        Returns:
            Span: Self

        Example:
            >>> with span:
            ...     # Inside this block, span is the current span
            ...     do_work()
        """
        TraceContext.set_current_span(self)
        TraceContext.set_current_span_id(self.span_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the span context.

        Automatically ends the span and records exceptions if any occurred.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if exc_val is not None:
            self.record_exception(exc_val)

        if not self._ended:
            self.end()

        return False  # Don't suppress exceptions


def create_span(
    name: str,
    span_type: SpanType = SpanType.SPAN,
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    framework: Framework = Framework.UNKNOWN,
    **kwargs,
) -> Span:
    """
    Create a new span with automatic context detection.

    This is a convenience function that automatically detects the trace_id
    from context if not provided.

    Args:
        name: Span name
        span_type: Type of operation
        trace_id: Trace ID (auto-detected from context if None)
        parent_span_id: Parent span ID (auto-detected from context if None)
        framework: Framework that generated this span
        **kwargs: Additional span fields

    Returns:
        Span: New span instance

    Example:
        >>> span = create_span("my-operation", SpanType.LLM_CALL)
        >>> with span:
        ...     # Do work
        ...     pass
    """
    # Auto-detect trace_id from context if not provided
    if trace_id is None:
        trace_id = TraceContext.get_current_trace_id()
        if trace_id is None:
            # Create new trace if no context
            trace_id = str(uuid.uuid4())
            TraceContext.set_current_trace_id(trace_id)

    return Span(
        trace_id=trace_id,
        name=name,
        span_type=span_type,
        parent_span_id=parent_span_id,
        framework=framework,
        **kwargs,
    )
