# AgentTrace Python SDK - Public API Design

## Design Principles

1. **Two lines to get started** - Minimal setup required
2. **Local-first development** - Zero config for local development
3. **Auto-instrumentation** - Framework integrations require no code changes
4. **Manual when needed** - Full control through decorators and context managers
5. **Production-ready** - Comprehensive configuration for all environments

---

## API Overview

### Core Initialization

```python
from agenttrace import AgentTrace

# Local mode (zero config)
trace = AgentTrace.init()

# Production mode
trace = AgentTrace.init(
    api_key="at_xxx",
    project_id="my-project"
)
```

---

## 1. Auto-Instrumentation API

**Zero code changes** - Automatically trace all framework operations.

### LangChain

```python
from agenttrace import AgentTrace

trace = AgentTrace.init()
AgentTrace.instrument_langchain()

# Now all LangChain operations are automatically traced
from langchain.chains import LLMChain
chain = LLMChain(...)
chain.run("query")  # ✅ Automatically traced!
```

**Automatically captures:**
- LLM calls with model, tokens, cost
- Chain executions with inputs/outputs
- Agent steps with reasoning
- Tool invocations with results
- Retriever queries with documents

### OpenAI

```python
from agenttrace import AgentTrace

trace = AgentTrace.init()
AgentTrace.instrument_openai()

# Now all OpenAI calls are automatically traced
import openai
openai.ChatCompletion.create(...)  # ✅ Automatically traced!
```

**Automatically captures:**
- Model name and parameters
- Full conversation history
- Token usage and costs
- Response and finish reason

### CrewAI

```python
from agenttrace import AgentTrace

trace = AgentTrace.init()
AgentTrace.instrument_crewai()

# Now all CrewAI operations are automatically traced
from crewai import Crew
crew = Crew(...)
crew.kickoff()  # ✅ Automatically traced!
```

**Automatically captures:**
- Agent executions
- Task completions
- Crew workflows
- Tool invocations

---

## 2. Decorator API

**Minimal code changes** - Add one decorator to trace functions.

### Agent Decorator

Trace entire agent functions:

```python
@trace.trace_agent(name="my_agent", framework=Framework.CUSTOM)
def my_agent(query: str) -> str:
    """Your agent logic."""
    return process_query(query)
```

**Features:**
- Automatic input/output capture
- Error handling with stack traces
- Duration tracking
- Framework identification

### LLM Decorator

Specialized for LLM calls:

```python
@trace.trace_llm(name="gpt4_call", model="gpt-4")
def call_llm(prompt: str) -> str:
    """Call GPT-4."""
    return openai.ChatCompletion.create(...)
```

**Features:**
- LLM-specific metadata capture
- Token usage tracking
- Cost calculation
- Model identification

### Tool Decorator

Specialized for tool invocations:

```python
@trace.trace_tool(name="web_search", tool_name="google")
def search_web(query: str) -> dict:
    """Search the web."""
    return google.search(query)
```

**Features:**
- Tool name and input tracking
- Output capture
- Error recording
- Execution time

---

## 3. Context Manager API

**Full control** - Manual span creation and management.

### Span Context Manager

Create individual spans:

```python
with trace.span("operation_name", SpanType.LLM_CALL) as span:
    # Set metadata
    span.set_attribute("key", "value")
    span.set_input(input_data)

    # Do work
    result = do_work()

    # Record result
    span.set_output(result)
```

**Available span types:**
- `LLM_CALL` - LLM API calls
- `TOOL_CALL` - Tool invocations
- `AGENT_STEP` - Agent reasoning steps
- `RETRIEVAL` - Vector/database retrieval
- `CHAIN` - Chain executions
- `WORKFLOW` - Multi-step workflows
- `PREPROCESSING` - Input preprocessing
- `POSTPROCESSING` - Output postprocessing
- `MEMORY_READ` / `MEMORY_WRITE` - Memory operations

### Trace Context Manager

Create hierarchical traces:

```python
with trace.trace("agent_pipeline", framework=Framework.CUSTOM) as root:
    # Set root metadata
    root.set_attribute("user_id", "123")
    root.set_input(query)

    # Child spans automatically nested
    with trace.span("retrieve") as retrieval:
        context = retrieve(query)

    with trace.span("generate") as generation:
        response = generate(query, context)

    root.set_output(response)
```

**Features:**
- Automatic parent-child relationships
- Hierarchical visualization
- Root span for end-to-end timing
- Nested context propagation

---

## 4. Metadata API

### Basic Attributes

```python
span.set_attribute("key", "value")
span.set_attributes({
    "user_id": "123",
    "model": "gpt-4",
    "temperature": 0.7
})
```

### Tags

```python
span.add_tag("production")
span.add_tag("experiment-v2")
span.add_tags(["high-priority", "premium-user"])
```

### Input/Output

```python
span.set_input({"query": "What is AI?"})
span.set_output({"response": "AI is..."})
```

### LLM Metadata

```python
span.set_llm_metadata(
    model="gpt-4",
    provider="openai",
    temperature=0.7,
    messages=[
        Message(role="system", content="You are helpful"),
        Message(role="user", content="Hello")
    ],
    usage=TokenUsage(
        prompt_tokens=10,
        completion_tokens=20
    )
)
```

### Tool Metadata

```python
span.set_tool_metadata(
    tool_name="calculator",
    tool_input={"operation": "add", "a": 1, "b": 2},
    tool_output={"result": 3}
)
```

### Retrieval Metadata

```python
span.set_retrieval_metadata(
    query="AI applications",
    collection="documents",
    top_k=5,
    results=[...],
    scores=[0.95, 0.87, 0.82]
)
```

---

## 5. Error Handling API

### Automatic Error Capture

Errors are automatically captured in decorators and context managers:

```python
@trace.trace_agent(name="my_agent")
def my_agent():
    # This error is automatically captured
    raise ValueError("Something went wrong")
```

**Automatically captured:**
- Exception type
- Error message
- Full stack trace
- Span marked as ERROR status

### Manual Error Recording

```python
with trace.span("operation") as span:
    try:
        risky_operation()
    except Exception as e:
        # Manually record exception
        span.record_exception(e)

        # Handle gracefully
        fallback_result = fallback()
        span.set_output(fallback_result)
```

---

## 6. Async Support API

Full async/await support with context propagation:

```python
@trace.trace_agent(name="async_agent")
async def async_agent(query: str) -> str:
    """Async agent with tracing."""
    results = await async_search(query)
    answer = await async_synthesize(results)
    return answer

# Run async
asyncio.run(async_agent("query"))
```

**Features:**
- Context propagation across async boundaries
- Concurrent operation tracking
- Async context managers
- Full async decorator support

---

## 7. Configuration API

### Basic Configuration

```python
from agenttrace import AgentTrace, AgentTraceConfig

config = AgentTraceConfig(
    api_key="at_xxx",
    project_id="my-project",
    environment="production",
    tags=["v2", "us-east-1"]
)

trace = AgentTrace.init(config=config)
```

### From Environment Variables

```bash
export AGENTTRACE_API_KEY=at_xxx
export AGENTTRACE_PROJECT_ID=my-project
export AGENTTRACE_ENVIRONMENT=production
export AGENTTRACE_TAGS=v2,us-east-1
```

```python
# Automatically loads from env
trace = AgentTrace.init()
```

### Advanced Configuration

```python
config = AgentTraceConfig(
    # Authentication
    api_key="at_xxx",
    project_id="my-project",

    # Environment
    environment="production",
    tags=["v2"],

    # Export
    export_mode=ExportMode.ASYNC,  # SYNC, ASYNC, DISABLED
    batch_size=20,
    flush_interval=10.0,

    # Data capture
    capture_input=True,
    capture_output=True,
    max_attribute_length=8192,

    # Sampling
    sample_rate=0.1,  # Sample 10% of traces

    # Local export
    console_export=True,
    file_export=True,
    file_export_path="./traces",

    # Performance
    timeout=30,
    max_retries=3
)
```

---

## 8. Lifecycle Management API

### Initialization

```python
# Initialize global instance
trace = AgentTrace.init()

# Get global instance
trace = AgentTrace.get_instance()
```

### Flushing

```python
# Force flush pending spans
trace.flush()
```

### Shutdown

```python
# Graceful shutdown
trace.shutdown()

# Or use atexit
import atexit
atexit.register(trace.shutdown)

# Or use context manager
with AgentTrace.init() as trace:
    # Your code
    pass
# Automatically shutdown
```

---

## 9. Schema Types

### Enums

```python
from agenttrace import Framework, SpanType, SpanStatus, MessageRole

# Framework identification
Framework.LANGCHAIN
Framework.CREWAI
Framework.OPENAI_AGENTS
Framework.CUSTOM

# Span types
SpanType.LLM_CALL
SpanType.TOOL_CALL
SpanType.AGENT_STEP
SpanType.RETRIEVAL
SpanType.CHAIN

# Span status
SpanStatus.OK
SpanStatus.ERROR
SpanStatus.UNSET

# Message roles
MessageRole.SYSTEM
MessageRole.USER
MessageRole.ASSISTANT
```

### Data Classes

```python
from agenttrace import Message, TokenUsage, LLMCall, ToolCall, RetrievalCall

# Message
msg = Message(role="user", content="Hello")

# Token usage
usage = TokenUsage(
    prompt_tokens=10,
    completion_tokens=20,
    total_tokens=30
)

# LLM call metadata
llm = LLMCall(
    model="gpt-4",
    messages=[msg],
    usage=usage
)
```

---

## 10. Global Convenience Functions

```python
import agenttrace

# Initialize global instance
trace = agenttrace.init(api_key="at_xxx")

# Get global instance
trace = agenttrace.get_client()

# Shutdown
agenttrace.shutdown()

# Auto-instrumentation
agenttrace.instrument_langchain()
agenttrace.instrument_openai()
agenttrace.instrument_crewai()
```

---

## Complete Example

Putting it all together:

```python
from agenttrace import AgentTrace, SpanType, Framework

# 1. Initialize (one line)
trace = AgentTrace.init()

# 2. Auto-instrument (optional, one line)
AgentTrace.instrument_langchain()

# 3. Use decorators for agent functions
@trace.trace_agent(name="research_agent", framework=Framework.CUSTOM)
def research_agent(query: str) -> str:
    # 4. Use context managers for detailed tracing
    with trace.span("retrieve", SpanType.RETRIEVAL) as span:
        span.set_retrieval_metadata(
            query=query,
            collection="knowledge_base",
            top_k=5
        )
        docs = retrieve_documents(query)
        span.set_output(docs)

    with trace.span("generate", SpanType.LLM_CALL) as span:
        span.set_llm_metadata(
            model="gpt-4",
            temperature=0.7
        )
        answer = generate_answer(query, docs)
        span.set_output(answer)

    return answer

# 5. Call your agent
result = research_agent("What is AI observability?")

# 6. Shutdown gracefully
trace.shutdown()
```

---

## API Design Goals ✅

- ✅ **Two lines to get started**: `AgentTrace.init()` + `@trace_agent`
- ✅ **Auto-instrumentation**: `instrument_langchain()`, etc.
- ✅ **Manual instrumentation**: Decorators and context managers
- ✅ **Local-first**: Zero config defaults to console output
- ✅ **Production-ready**: Comprehensive configuration options
- ✅ **Async support**: Full async/await compatibility
- ✅ **Error handling**: Automatic capture with manual override
- ✅ **Rich metadata**: LLM, tool, and retrieval specific fields
- ✅ **Hierarchical tracing**: Automatic parent-child relationships
- ✅ **Type-safe**: Full type hints and enums

---

## Next Steps

1. Review [examples/quickstart.py](../examples/quickstart.py) for quick start
2. Explore [examples/sdk-usage.py](../examples/sdk-usage.py) for comprehensive examples
3. Read the [API reference](./API_REFERENCE.md) for detailed documentation
4. Visit [docs.agenttrace.dev](https://docs.agenttrace.dev) for guides and tutorials
