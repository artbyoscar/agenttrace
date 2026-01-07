"""
AgentTrace Python SDK - AI Agent Observability Platform

OpenTelemetry-compatible tracing for AI agents with extensions for
LLM calls, tool invocations, and agent-specific operations.

Quick Start:
    >>> import agenttrace
    >>> from agenttrace import SpanType, Framework
    >>>
    >>> # Initialize
    >>> trace = agenttrace.init(
    ...     api_key="my-key",
    ...     project_id="my-project"
    ... )
    >>>
    >>> # Use decorators
    >>> @trace.trace_agent(name="my-agent")
    >>> def my_agent(query: str):
    ...     return "response"
    >>>
    >>> # Or use context managers
    >>> with trace.span("operation", SpanType.LLM_CALL) as span:
    ...     span.set_llm_metadata(model="gpt-4", ...)
    ...     # Do work
    >>>
    >>> # Shutdown
    >>> agenttrace.shutdown()
"""

__version__ = "0.1.0"

# Core client
from .client import (
    AgentTrace,
    init,
    get_client,
    shutdown,
)

# Configuration
from .config import (
    AgentTraceConfig,
    ExportMode,
    LogLevel,
    Config,  # Backwards compatibility
)

# Schema types
from .schema import (
    # Enums
    Framework,
    SpanType,
    SpanStatus,
    MessageRole,
    # Data classes
    Message,
    TokenUsage,
    LLMCall,
    ToolCall,
    RetrievalCall,
    SpanEvent,
    SpanLink,
    Span as SchemaSpan,
    Trace as SchemaTrace,
    # Helper functions
    create_llm_span,
    create_tool_span,
    create_retrieval_span,
)

# Span management
from .span import (
    Span,
    create_span,
)

# Context management
from .context import (
    TraceContext,
    get_current_trace_id,
    get_current_span_id,
    get_current_span,
    new_trace,
    clear_context,
)

# Exporters
from .exporter import (
    SpanExporter,
    ConsoleExporter,
    FileExporter,
    HTTPExporter,
    CompositeExporter,
    create_exporter,
)

# Public API
__all__ = [
    # Version
    "__version__",

    # Core client
    "AgentTrace",
    "init",
    "get_client",
    "shutdown",

    # Configuration
    "AgentTraceConfig",
    "ExportMode",
    "LogLevel",
    "Config",

    # Schema enums
    "Framework",
    "SpanType",
    "SpanStatus",
    "MessageRole",

    # Schema data classes
    "Message",
    "TokenUsage",
    "LLMCall",
    "ToolCall",
    "RetrievalCall",
    "SpanEvent",
    "SpanLink",
    "SchemaSpan",
    "SchemaTrace",

    # Schema helpers
    "create_llm_span",
    "create_tool_span",
    "create_retrieval_span",

    # Span
    "Span",
    "create_span",

    # Context
    "TraceContext",
    "get_current_trace_id",
    "get_current_span_id",
    "get_current_span",
    "new_trace",
    "clear_context",

    # Exporters
    "SpanExporter",
    "ConsoleExporter",
    "FileExporter",
    "HTTPExporter",
    "CompositeExporter",
    "create_exporter",
]
