# AgentTrace Python SDK

Official Python SDK for AgentTrace - AI Agent Observability Platform.

## Installation

```bash
pip install agenttrace
```

For LangChain integration:
```bash
pip install agenttrace[langchain]
```

For CrewAI integration:
```bash
pip install agenttrace[crewai]
```

## Quick Start

### Basic Usage

```python
from agenttrace import AgentTrace

# Initialize the SDK
trace = AgentTrace(
    api_key="your-api-key",
    project="my-project",
    api_url="http://localhost:8000"
)

# Using decorator
@trace.trace_agent()
def my_agent_function():
    # Your agent code here
    return "result"

# Using context manager
with trace.start_trace(name="my-trace") as span:
    # Your agent code
    span.log("Processing started")
    result = process_data()
    span.log("Processing completed")
```

### LangChain Integration

```python
from agenttrace.integrations.langchain import LangChainTracer
from langchain.chains import LLMChain

tracer = LangChainTracer(
    api_key="your-api-key",
    project="my-project"
)

# Add to your chain
chain = LLMChain(
    llm=llm,
    callbacks=[tracer]
)
```

### CrewAI Integration

```python
from agenttrace.integrations.crewai import CrewAITracer
from crewai import Crew, Agent, Task

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

## Configuration

You can configure the SDK using environment variables:

```bash
export AGENTTRACE_API_KEY=your-api-key
export AGENTTRACE_API_URL=http://localhost:8000
export AGENTTRACE_PROJECT=my-project
```

Or programmatically:

```python
from agenttrace import AgentTrace

trace = AgentTrace(
    api_key="your-api-key",
    project="my-project",
    api_url="http://localhost:8000",
    environment="production",
    tags=["api", "v1"]
)
```

## Features

- Automatic trace collection
- Custom metadata and tags
- Error tracking and reporting
- Token usage tracking
- Latency monitoring
- Framework integrations (LangChain, CrewAI)
- Async support

## Documentation

For full documentation, visit [docs.agenttrace.dev](https://docs.agenttrace.dev)

## Examples

Check out the [examples](../../examples/) directory for more usage examples.

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## License

MIT License - see [LICENSE](../../LICENSE) for details.
