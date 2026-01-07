# AgentTrace Python SDK Examples

This directory contains comprehensive examples showing how to use AgentTrace for AI agent observability.

## Quick Start

### 1. **[quickstart.py](./quickstart.py)** - Get Started in Minutes

The fastest way to get started with AgentTrace. Shows 6 quick-start patterns:

```python
from agenttrace import AgentTrace

# Initialize (one line!)
trace = AgentTrace.init()

# Trace your agent (one decorator!)
@trace.trace_agent(name="my_agent")
def my_agent(query: str) -> str:
    return f"Processed: {query}"
```

**Perfect for:** First-time users, quick prototypes

**Estimated time:** 5 minutes

---

## Comprehensive Guide

### 2. **[sdk-usage.py](./sdk-usage.py)** - Complete Reference

In-depth examples covering every feature of AgentTrace. Contains 25 examples organized by category:

#### **Basic Setup** (Examples 1-3)
- Local mode (zero config)
- Hosted mode (production)
- Environment variables

#### **Auto-Instrumentation** (Examples 4-6)
- LangChain integration
- OpenAI integration
- CrewAI integration

#### **Manual Instrumentation** (Examples 7-10)
- Function decorators
- LLM decorators
- Tool decorators
- Context managers

#### **Advanced Features** (Examples 11-19)
- Trace contexts
- Async support
- Error handling
- Rich metadata (LLM, tools, retrieval)
- Custom attributes and tags
- Nested agent workflows

#### **Production** (Examples 20-25)
- Configuration options
- Environment-specific configs
- Testing and development
- Production monitoring
- Cleanup and shutdown

**Perfect for:** Learning all features, reference documentation

**Estimated time:** 30-60 minutes to review all examples

---

## Example Index

### By Use Case

#### **Getting Started**
- [quickstart.py](./quickstart.py) - Examples 1-6: Fastest way to start

#### **Framework Integration**
- [sdk-usage.py](./sdk-usage.py) - Example 4: LangChain auto-instrumentation
- [sdk-usage.py](./sdk-usage.py) - Example 5: OpenAI auto-instrumentation
- [sdk-usage.py](./sdk-usage.py) - Example 6: CrewAI auto-instrumentation
- [sdk-usage.py](./sdk-usage.py) - Example 23: LangChain best practices

#### **Manual Tracing**
- [sdk-usage.py](./sdk-usage.py) - Example 7: Function decorator
- [sdk-usage.py](./sdk-usage.py) - Example 8: LLM decorator
- [sdk-usage.py](./sdk-usage.py) - Example 9: Tool decorator
- [sdk-usage.py](./sdk-usage.py) - Example 10: Context manager

#### **Complex Workflows**
- [sdk-usage.py](./sdk-usage.py) - Example 11: Trace context manager
- [sdk-usage.py](./sdk-usage.py) - Example 19: Nested agent workflows
- [sdk-usage.py](./sdk-usage.py) - Example 25: Production monitoring

#### **Async Support**
- [quickstart.py](./quickstart.py) - Quick Start 5: Async agents
- [sdk-usage.py](./sdk-usage.py) - Example 12: Async support

#### **Error Handling**
- [quickstart.py](./quickstart.py) - Quick Start 6: Error handling
- [sdk-usage.py](./sdk-usage.py) - Example 13: Automatic error capture
- [sdk-usage.py](./sdk-usage.py) - Example 14: Manual error recording

#### **Production Deployment**
- [sdk-usage.py](./sdk-usage.py) - Example 2: Hosted mode
- [sdk-usage.py](./sdk-usage.py) - Example 20: Configuration options
- [sdk-usage.py](./sdk-usage.py) - Example 21: Environment-specific configs
- [sdk-usage.py](./sdk-usage.py) - Example 25: Production monitoring

#### **Development & Testing**
- [sdk-usage.py](./sdk-usage.py) - Example 1: Local mode
- [sdk-usage.py](./sdk-usage.py) - Example 24: Testing and development

---

## Running the Examples

### Prerequisites

```bash
# Install AgentTrace SDK
pip install agenttrace

# For auto-instrumentation examples, install frameworks:
pip install langchain  # For LangChain examples
pip install openai     # For OpenAI examples
pip install crewai     # For CrewAI examples
```

### Run Quick Start

```bash
python examples/quickstart.py
```

### Run Individual Examples

The examples in `sdk-usage.py` are self-contained. You can copy any example and run it:

```python
# Copy Example 7 (Function Decorator)
from agenttrace import AgentTrace, Framework

trace = AgentTrace.init()

@trace.trace_agent(name="research_agent", framework=Framework.CUSTOM)
def research_agent(query: str) -> str:
    results = search_knowledge_base(query)
    answer = synthesize_answer(results)
    return answer

answer = research_agent("What is observability?")
```

---

## Configuration

### Local Development (Default)

```python
from agenttrace import AgentTrace

# Zero configuration - outputs to console
trace = AgentTrace.init()
```

### Production with API Key

```python
from agenttrace import AgentTrace

trace = AgentTrace.init(
    api_key="at_xxx",  # Get from https://app.agenttrace.dev
    project_id="my-project",
    environment="production"
)
```

### Environment Variables

```bash
export AGENTTRACE_API_KEY=at_xxx
export AGENTTRACE_PROJECT_ID=my-project
export AGENTTRACE_ENVIRONMENT=production
```

```python
from agenttrace import AgentTrace

# Automatically loads from environment
trace = AgentTrace.init()
```

---

## Common Patterns

### Pattern 1: Two-Line Setup

```python
from agenttrace import AgentTrace
trace = AgentTrace.init()
```

### Pattern 2: Auto-Instrumentation

```python
from agenttrace import AgentTrace

trace = AgentTrace.init()
AgentTrace.instrument_langchain()

# All LangChain operations now traced automatically!
```

### Pattern 3: Decorator

```python
@trace.trace_agent(name="my_agent")
def my_agent(query: str) -> str:
    return process(query)
```

### Pattern 4: Context Manager

```python
with trace.span("operation") as span:
    span.set_attribute("key", "value")
    result = do_work()
    span.set_output(result)
```

### Pattern 5: Hierarchical Tracing

```python
with trace.trace("parent") as root:
    with trace.span("child1") as child1:
        # Do work
        pass
    with trace.span("child2") as child2:
        # Do work
        pass
```

---

## Best Practices

### 1. **Initialize Once**
```python
# Good: Initialize at app startup
trace = AgentTrace.init()

# Bad: Don't initialize multiple times
# trace = AgentTrace.init()  # in every file
```

### 2. **Use Auto-Instrumentation When Possible**
```python
# Good: Zero code changes
AgentTrace.instrument_langchain()

# Less ideal: Manual instrumentation everywhere
@trace.trace_agent(...)
def every_function(): ...
```

### 3. **Meaningful Names**
```python
# Good: Descriptive names
@trace.trace_agent(name="user_query_processor")

# Bad: Generic names
@trace.trace_agent(name="function1")
```

### 4. **Add Context**
```python
# Good: Rich metadata
span.set_attribute("user_id", user_id)
span.set_attribute("model", "gpt-4")
span.add_tag("production")

# Less useful: No context
# Just run without metadata
```

### 5. **Handle Errors**
```python
# Good: Errors are automatically captured
@trace.trace_agent(name="safe_agent")
def safe_agent():
    # Errors automatically recorded
    risky_operation()

# Also good: Manual error handling
with trace.span("operation") as span:
    try:
        risky_operation()
    except Exception as e:
        span.record_exception(e)
        handle_error()
```

---

## Next Steps

1. **Start with quickstart.py** - Get familiar with basic usage
2. **Browse sdk-usage.py** - Find examples for your use case
3. **Read the docs** - Visit [docs.agenttrace.dev](https://docs.agenttrace.dev)
4. **Join the community** - Get help and share feedback

---

## Support

- **Documentation:** [docs.agenttrace.dev](https://docs.agenttrace.dev)
- **Issues:** [github.com/agenttrace/agenttrace/issues](https://github.com/agenttrace/agenttrace/issues)
- **Discord:** [discord.gg/agenttrace](https://discord.gg/agenttrace)

---

## License

See the [LICENSE](../LICENSE) file in the root directory.
