# AgentTrace Schema

Shared schema definitions for AgentTrace.

## Overview

This package contains:
- Trace data models
- Event schemas
- Validation rules
- Type definitions

## Usage

```python
from agenttrace_schema import TraceEvent, Span

# Create a trace event
event = TraceEvent(
    trace_id="trace_123",
    name="my-agent",
    status="completed"
)
```

## Schema Definitions

### Trace

- `trace_id`: Unique identifier
- `project`: Project name
- `name`: Trace name
- `status`: Status (running, completed, error)
- `start_time`: Start timestamp
- `end_time`: End timestamp
- `metadata`: Custom metadata
- `tags`: Tags for filtering

### Span

- `span_id`: Unique identifier
- `trace_id`: Parent trace ID
- `parent_id`: Parent span ID (optional)
- `name`: Span name
- `duration`: Duration in seconds
- `logs`: Log entries
- `error`: Error details (if any)
