"""
AgentTrace Schema Definitions

Defines the data structures for traces and spans in AgentTrace.
Compatible with OpenTelemetry while adding AI agent-specific extensions.

Based on OpenTelemetry Trace specification:
https://opentelemetry.io/docs/reference/specification/trace/api/
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Literal, Union
from datetime import datetime
from enum import Enum
import uuid


class Framework(str, Enum):
    """
    AI agent framework identification.

    Used to identify which framework generated the trace, enabling
    framework-specific handling and analytics.
    """

    LANGCHAIN = "langchain"
    CREWAI = "crewai"
    AUTOGEN = "autogen"
    OPENAI_AGENTS = "openai_agents"
    LLAMAINDEX = "llamaindex"
    SEMANTIC_KERNEL = "semantic_kernel"
    HAYSTACK = "haystack"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class SpanType(str, Enum):
    """
    Classification of span types for AI agent operations.

    Each type represents a different operation in agent execution,
    enabling specific handling, visualization, and analysis.
    """

    # LLM Operations
    LLM_CALL = "llm_call"  # Direct LLM API call (completion, chat, etc.)
    EMBEDDING = "embedding"  # Embedding generation

    # Agent Operations
    AGENT_STEP = "agent_step"  # Single agent reasoning/action step
    CHAIN = "chain"  # Chain or workflow execution
    WORKFLOW = "workflow"  # Multi-step workflow

    # Tool Operations
    TOOL_CALL = "tool_call"  # External tool invocation
    RETRIEVAL = "retrieval"  # Vector store or database retrieval
    SEARCH = "search"  # Web or document search

    # Data Operations
    PREPROCESSING = "preprocessing"  # Input preprocessing
    POSTPROCESSING = "postprocessing"  # Output postprocessing
    TRANSFORMATION = "transformation"  # Data transformation

    # Memory Operations
    MEMORY_READ = "memory_read"  # Reading from agent memory
    MEMORY_WRITE = "memory_write"  # Writing to agent memory

    # Generic
    SPAN = "span"  # Generic span for custom operations
    ROOT = "root"  # Root span of a trace


class SpanStatus(str, Enum):
    """
    Execution status of a span.

    Based on OpenTelemetry status codes.
    """

    UNSET = "unset"  # Status not set
    OK = "ok"  # Operation completed successfully
    ERROR = "error"  # Operation failed


class MessageRole(str, Enum):
    """
    Role of a message in LLM conversation.

    Standard roles used across LLM providers.
    """

    SYSTEM = "system"  # System message (instructions)
    USER = "user"  # User message (input)
    ASSISTANT = "assistant"  # Assistant message (output)
    FUNCTION = "function"  # Function call result
    TOOL = "tool"  # Tool call result


@dataclass
class Message:
    """
    Represents a single message in an LLM conversation.

    Used to capture the complete conversation context for LLM calls,
    enabling replay and debugging capabilities.
    """

    role: MessageRole
    content: str
    name: Optional[str] = None  # Name of the function/tool if role is function/tool
    function_call: Optional[Dict[str, Any]] = None  # Function call data (deprecated)
    tool_calls: Optional[List[Dict[str, Any]]] = None  # Tool calls data (new format)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class TokenUsage:
    """
    Token usage statistics for LLM calls.

    Tracks token consumption for cost analysis and optimization.
    """

    prompt_tokens: int = 0  # Tokens in the prompt
    completion_tokens: int = 0  # Tokens in the completion
    total_tokens: int = 0  # Total tokens used

    def __post_init__(self):
        """Calculate total if not provided."""
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens


@dataclass
class LLMCall:
    """
    LLM-specific metadata for LLM_CALL spans.

    Captures all relevant information about an LLM API call for
    debugging, replay, and cost analysis.
    """

    # Model information
    model: str  # Model name (e.g., "gpt-4", "claude-2")
    provider: Optional[str] = None  # Provider (e.g., "openai", "anthropic")

    # Request parameters
    messages: List[Message] = field(default_factory=list)  # Conversation messages
    temperature: Optional[float] = None  # Sampling temperature
    max_tokens: Optional[int] = None  # Maximum tokens to generate
    top_p: Optional[float] = None  # Nucleus sampling parameter
    frequency_penalty: Optional[float] = None  # Frequency penalty
    presence_penalty: Optional[float] = None  # Presence penalty
    stop_sequences: Optional[List[str]] = None  # Stop sequences

    # Response data
    response: Optional[str] = None  # Generated response text
    finish_reason: Optional[str] = None  # Why generation stopped

    # Usage statistics
    usage: Optional[TokenUsage] = None  # Token usage

    # Function/Tool calling
    functions: Optional[List[Dict[str, Any]]] = None  # Available functions
    function_call: Optional[Dict[str, Any]] = None  # Function call result
    tools: Optional[List[Dict[str, Any]]] = None  # Available tools (new format)
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None  # Tool choice strategy

    # Cost tracking
    cost_usd: Optional[float] = None  # Estimated cost in USD

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling nested objects."""
        result = {}
        for key, value in asdict(self).items():
            if value is None:
                continue
            if key == "messages":
                result[key] = [msg.to_dict() for msg in self.messages]
            elif key == "usage" and isinstance(value, dict):
                result[key] = value
            else:
                result[key] = value
        return result


@dataclass
class ToolCall:
    """
    Tool-specific metadata for TOOL_CALL spans.

    Captures information about external tool invocations, enabling
    debugging and replay of tool interactions.
    """

    tool_name: str  # Name of the tool
    tool_input: Optional[Dict[str, Any]] = None  # Input parameters
    tool_output: Optional[Any] = None  # Output result
    tool_error: Optional[str] = None  # Error message if failed
    tool_metadata: Optional[Dict[str, Any]] = None  # Additional tool metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class RetrievalCall:
    """
    Retrieval-specific metadata for RETRIEVAL spans.

    Captures vector search and retrieval operations, common in RAG
    (Retrieval-Augmented Generation) systems.
    """

    query: str  # Query text or embedding
    collection: Optional[str] = None  # Collection/index name
    top_k: Optional[int] = None  # Number of results requested
    score_threshold: Optional[float] = None  # Minimum similarity score
    filters: Optional[Dict[str, Any]] = None  # Query filters

    # Results
    num_results: Optional[int] = None  # Actual number of results
    results: Optional[List[Dict[str, Any]]] = None  # Retrieved documents
    scores: Optional[List[float]] = None  # Similarity scores

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class SpanEvent:
    """
    An event that occurred during span execution.

    Based on OpenTelemetry span events, used for logging important
    occurrences during span execution.
    """

    name: str  # Event name
    timestamp: datetime  # When the event occurred
    attributes: Dict[str, Any] = field(default_factory=dict)  # Event attributes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO timestamp."""
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "attributes": self.attributes,
        }


@dataclass
class SpanLink:
    """
    Link to another span.

    Based on OpenTelemetry span links, used to associate spans across
    different traces or establish non-parent relationships.
    """

    trace_id: str  # Linked trace ID
    span_id: str  # Linked span ID
    attributes: Dict[str, Any] = field(default_factory=dict)  # Link attributes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Span:
    """
    Represents a single operation in a trace.

    Based on OpenTelemetry span specification with AI agent-specific extensions.
    A span represents a unit of work or operation, such as an LLM call,
    tool invocation, or agent step.
    """

    # OpenTelemetry-compatible fields
    trace_id: str  # Unique identifier for the trace
    span_id: str  # Unique identifier for this span
    parent_span_id: Optional[str] = None  # Parent span ID (None for root)
    name: str = "span"  # Human-readable span name
    start_time: Optional[datetime] = None  # When span started
    end_time: Optional[datetime] = None  # When span ended
    status: SpanStatus = SpanStatus.UNSET  # Execution status
    status_message: Optional[str] = None  # Additional status info

    # AI agent-specific fields
    span_type: SpanType = SpanType.SPAN  # Type of operation
    framework: Framework = Framework.UNKNOWN  # Framework that generated this span

    # Input/Output for replay
    input: Optional[Any] = None  # Input to the operation
    output: Optional[Any] = None  # Output from the operation

    # Type-specific metadata
    llm: Optional[LLMCall] = None  # LLM call metadata (if span_type is LLM_CALL)
    tool: Optional[ToolCall] = None  # Tool call metadata (if span_type is TOOL_CALL)
    retrieval: Optional[RetrievalCall] = None  # Retrieval metadata (if span_type is RETRIEVAL)

    # OpenTelemetry attributes and context
    attributes: Dict[str, Any] = field(default_factory=dict)  # Custom attributes
    events: List[SpanEvent] = field(default_factory=list)  # Span events (logs)
    links: List[SpanLink] = field(default_factory=list)  # Links to other spans

    # Error tracking
    error: Optional[Dict[str, Any]] = None  # Error information if status is ERROR

    # Metadata
    tags: List[str] = field(default_factory=list)  # Tags for filtering
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def __post_init__(self):
        """Initialize computed fields."""
        # Generate IDs if not provided
        if not self.span_id:
            self.span_id = str(uuid.uuid4())

        # Set start time if not provided
        if not self.start_time:
            self.start_time = datetime.utcnow()

    @property
    def duration(self) -> Optional[float]:
        """
        Calculate span duration in seconds.

        Returns None if span hasn't ended yet.
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def is_root(self) -> bool:
        """Check if this is a root span (no parent)."""
        return self.parent_span_id is None

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add an event to the span.

        Args:
            name: Event name
            attributes: Optional event attributes
        """
        event = SpanEvent(
            name=name,
            timestamp=datetime.utcnow(),
            attributes=attributes or {},
        )
        self.events.append(event)

    def set_error(self, error: Exception):
        """
        Mark span as error and record exception.

        Args:
            error: The exception that occurred
        """
        self.status = SpanStatus.ERROR
        self.error = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": None,  # TODO: Add traceback capture
        }

    def end(self, status: Optional[SpanStatus] = None):
        """
        End the span.

        Args:
            status: Optional status to set (defaults to OK if not ERROR)
        """
        self.end_time = datetime.utcnow()
        if status:
            self.status = status
        elif self.status == SpanStatus.UNSET:
            self.status = SpanStatus.OK

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert span to dictionary for serialization.

        Returns:
            Dictionary representation of the span
        """
        result = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "status": self.status.value,
            "status_message": self.status_message,
            "span_type": self.span_type.value,
            "framework": self.framework.value,
            "input": self.input,
            "output": self.output,
            "attributes": self.attributes,
            "events": [event.to_dict() for event in self.events],
            "links": [link.to_dict() for link in self.links],
            "error": self.error,
            "tags": self.tags,
            "metadata": self.metadata,
        }

        # Add type-specific metadata
        if self.llm:
            result["llm"] = self.llm.to_dict()
        if self.tool:
            result["tool"] = self.tool.to_dict()
        if self.retrieval:
            result["retrieval"] = self.retrieval.to_dict()

        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


@dataclass
class Trace:
    """
    Represents a complete trace (collection of spans).

    A trace represents an end-to-end execution of an agent operation,
    containing multiple spans organized in a parent-child hierarchy.
    """

    # Trace identification
    trace_id: str  # Unique identifier for the trace
    name: str  # Human-readable trace name
    project_id: str  # Project this trace belongs to

    # Temporal information
    start_time: datetime  # When trace started
    end_time: Optional[datetime] = None  # When trace ended

    # Status
    status: SpanStatus = SpanStatus.UNSET  # Overall trace status

    # Spans
    spans: List[Span] = field(default_factory=list)  # All spans in the trace

    # Classification
    framework: Framework = Framework.UNKNOWN  # Primary framework used
    tags: List[str] = field(default_factory=list)  # Tags for filtering
    environment: str = "development"  # Environment (dev, staging, prod)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)  # Custom metadata
    user_id: Optional[str] = None  # User who triggered the trace
    session_id: Optional[str] = None  # Session identifier

    # Summary statistics (computed)
    total_tokens: Optional[int] = None  # Total tokens across all LLM calls
    total_cost: Optional[float] = None  # Total cost across all LLM calls
    error_count: int = 0  # Number of spans with errors

    def __post_init__(self):
        """Initialize trace ID if not provided."""
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())

    @property
    def duration(self) -> Optional[float]:
        """
        Calculate total trace duration in seconds.

        Returns None if trace hasn't ended yet.
        """
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def root_span(self) -> Optional[Span]:
        """Get the root span of the trace."""
        for span in self.spans:
            if span.is_root:
                return span
        return None

    def add_span(self, span: Span):
        """
        Add a span to the trace.

        Args:
            span: Span to add
        """
        # Ensure span has the correct trace_id
        span.trace_id = self.trace_id
        self.spans.append(span)

    def get_span(self, span_id: str) -> Optional[Span]:
        """
        Get a span by ID.

        Args:
            span_id: Span ID to find

        Returns:
            Span if found, None otherwise
        """
        for span in self.spans:
            if span.span_id == span_id:
                return span
        return None

    def get_children(self, span_id: str) -> List[Span]:
        """
        Get all child spans of a given span.

        Args:
            span_id: Parent span ID

        Returns:
            List of child spans
        """
        return [span for span in self.spans if span.parent_span_id == span_id]

    def compute_statistics(self):
        """
        Compute summary statistics from spans.

        Updates total_tokens, total_cost, and error_count.
        """
        total_tokens = 0
        total_cost = 0.0
        error_count = 0

        for span in self.spans:
            # Count errors
            if span.status == SpanStatus.ERROR:
                error_count += 1

            # Sum tokens and costs from LLM calls
            if span.llm and span.llm.usage:
                total_tokens += span.llm.usage.total_tokens

            if span.llm and span.llm.cost_usd:
                total_cost += span.llm.cost_usd

        self.total_tokens = total_tokens if total_tokens > 0 else None
        self.total_cost = total_cost if total_cost > 0 else None
        self.error_count = error_count

    def end(self, status: Optional[SpanStatus] = None):
        """
        End the trace.

        Args:
            status: Optional status to set
        """
        self.end_time = datetime.utcnow()

        # Compute statistics
        self.compute_statistics()

        # Determine status if not provided
        if status:
            self.status = status
        elif self.error_count > 0:
            self.status = SpanStatus.ERROR
        else:
            self.status = SpanStatus.OK

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert trace to dictionary for serialization.

        Returns:
            Dictionary representation of the trace
        """
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "project_id": self.project_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "status": self.status.value,
            "framework": self.framework.value,
            "tags": self.tags,
            "environment": self.environment,
            "metadata": self.metadata,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "spans": [span.to_dict() for span in self.spans],
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "error_count": self.error_count,
        }


# Convenience functions for creating spans

def create_llm_span(
    trace_id: str,
    name: str,
    model: str,
    messages: List[Message],
    parent_span_id: Optional[str] = None,
    **kwargs,
) -> Span:
    """
    Create an LLM call span.

    Args:
        trace_id: Trace ID
        name: Span name
        model: LLM model name
        messages: Conversation messages
        parent_span_id: Optional parent span ID
        **kwargs: Additional LLMCall parameters

    Returns:
        Configured LLM span
    """
    llm_call = LLMCall(model=model, messages=messages, **kwargs)

    return Span(
        trace_id=trace_id,
        name=name,
        parent_span_id=parent_span_id,
        span_type=SpanType.LLM_CALL,
        llm=llm_call,
    )


def create_tool_span(
    trace_id: str,
    name: str,
    tool_name: str,
    tool_input: Optional[Dict[str, Any]] = None,
    parent_span_id: Optional[str] = None,
) -> Span:
    """
    Create a tool call span.

    Args:
        trace_id: Trace ID
        name: Span name
        tool_name: Name of the tool
        tool_input: Tool input parameters
        parent_span_id: Optional parent span ID

    Returns:
        Configured tool span
    """
    tool_call = ToolCall(tool_name=tool_name, tool_input=tool_input)

    return Span(
        trace_id=trace_id,
        name=name,
        parent_span_id=parent_span_id,
        span_type=SpanType.TOOL_CALL,
        tool=tool_call,
    )


def create_retrieval_span(
    trace_id: str,
    name: str,
    query: str,
    parent_span_id: Optional[str] = None,
    **kwargs,
) -> Span:
    """
    Create a retrieval span.

    Args:
        trace_id: Trace ID
        name: Span name
        query: Query text
        parent_span_id: Optional parent span ID
        **kwargs: Additional RetrievalCall parameters

    Returns:
        Configured retrieval span
    """
    retrieval_call = RetrievalCall(query=query, **kwargs)

    return Span(
        trace_id=trace_id,
        name=name,
        parent_span_id=parent_span_id,
        span_type=SpanType.RETRIEVAL,
        retrieval=retrieval_call,
    )
