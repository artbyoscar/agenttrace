# SDK Reference

Complete reference for the AgentTrace Python SDK.

## Installation

```bash
pip install agenttrace
```

With framework integrations:

```bash
pip install agenttrace[langchain]
pip install agenttrace[crewai]
```

## Configuration

### Environment Variables

```bash
export AGENTTRACE_API_KEY=your-api-key
export AGENTTRACE_API_URL=http://localhost:8000
export AGENTTRACE_PROJECT=my-project
```

### Programmatic Configuration

```python
from agenttrace import AgentTrace

trace = AgentTrace(
    api_key="your-api-key",
    project="my-project",
    api_url="http://localhost:8000",
    environment="production",
    tags=["api", "v1"],
    enabled=True
)
```

## Core Classes

### AgentTrace

Main client for tracing operations.

#### Constructor

```python
AgentTrace(
    api_key: Optional[str] = None,
    project: Optional[str] = None,
    api_url: Optional[str] = None,
    environment: str = "development",
    tags: Optional[List[str]] = None,
    enabled: bool = True
)
```

**Parameters:**
- `api_key`: API key for authentication
- `project`: Project identifier
- `api_url`: API endpoint URL
- `environment`: Environment name (development, staging, production)
- `tags`: Default tags for all traces
- `enabled`: Whether tracing is enabled

#### Methods

##### trace_agent()

Decorator to trace agent functions.

```python
@trace.trace_agent(
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None
)
```

**Example:**

```python
@trace.trace_agent(name="my-agent", tags=["production"])
def my_agent(input_data):
    # Your agent logic
    return result
```

##### start_trace()

Context manager to start a trace.

```python
with trace.start_trace(
    name: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None
) as span:
    # Your code
```

**Example:**

```python
with trace.start_trace("data-processing") as span:
    span.log("Starting processing")
    data = process_data()
    span.set_metadata("rows", len(data))
    span.log("Processing complete")
```

##### flush()

Flush all pending traces.

```python
trace.flush()
```

### Span

Represents a single trace span.

#### Methods

##### log()

Add a log entry to the span.

```python
span.log(
    message: str,
    level: str = "info",
    **kwargs
)
```

**Example:**

```python
span.log("Processing started", level="info")
span.log("Warning: rate limit approaching", level="warning")
span.log("Error occurred", level="error", error_code=500)
```

##### set_metadata()

Set metadata on the span.

```python
span.set_metadata(key: str, value: Any)
```

**Example:**

```python
span.set_metadata("user_id", "user_123")
span.set_metadata("tokens_used", 150)
span.set_metadata("model", "gpt-4")
```

##### add_tag()

Add a tag to the span.

```python
span.add_tag(tag: str)
```

**Example:**

```python
span.add_tag("high-priority")
span.add_tag("production")
```

##### record_error()

Record an error on the span.

```python
span.record_error(error: Exception)
```

**Example:**

```python
try:
    risky_operation()
except Exception as e:
    span.record_error(e)
    raise
```

## Framework Integrations

### LangChain

```python
from agenttrace.integrations.langchain import LangChainTracer

tracer = LangChainTracer(
    api_key="your-api-key",
    project="my-project"
)

# Use with chains
chain = LLMChain(llm=llm, callbacks=[tracer])

# Use with agents
agent = initialize_agent(
    tools=tools,
    llm=llm,
    callbacks=[tracer]
)
```

### CrewAI

```python
from agenttrace.integrations.crewai import CrewAITracer

tracer = CrewAITracer(
    api_key="your-api-key",
    project="my-project"
)

crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    callbacks=[tracer]
)
```

## Advanced Usage

### Custom Metadata

```python
@trace.trace_agent(
    metadata={
        "version": "1.0.0",
        "model": "gpt-4",
        "temperature": 0.7
    }
)
def my_agent():
    pass
```

### Nested Spans

```python
with trace.start_trace("parent-operation") as parent:
    parent.log("Parent started")

    with trace.start_trace("child-operation") as child:
        child.log("Child started")
        # Child operation

    parent.log("Parent completed")
```

### Error Handling

```python
with trace.start_trace("risky-operation") as span:
    try:
        result = risky_function()
        span.set_metadata("success", True)
    except Exception as e:
        span.record_error(e)
        span.set_metadata("success", False)
        raise
```

### Conditional Tracing

```python
trace = AgentTrace(
    api_key="your-api-key",
    enabled=os.getenv("ENABLE_TRACING") == "true"
)
```

## Best Practices

1. **Use meaningful names**: Give your traces descriptive names
2. **Add metadata**: Include relevant metadata for filtering and analysis
3. **Tag appropriately**: Use tags for categorization
4. **Handle errors**: Always record errors for debugging
5. **Flush on shutdown**: Call `flush()` before application exit
6. **Use environment variables**: Store API keys in environment variables

## API Response Format

### Successful Response

```json
{
  "trace_id": "trace_abc123",
  "status": "created",
  "message": "Trace recorded successfully"
}
```

### Error Response

```json
{
  "error": "Authentication failed",
  "code": "AUTH_ERROR",
  "status": 401
}
```

## Rate Limits

- Default: 100 requests per minute
- Burst: 200 requests per minute
- Contact support for higher limits

## Support

- [GitHub Issues](https://github.com/yourusername/agenttrace/issues)
- [Documentation](https://docs.agenttrace.dev)
- Email: support@agenttrace.dev
