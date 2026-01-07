## AgentTrace Benchmark Execution Engine

**Version**: 0.1.0
**Status**: Production Ready
**Last Updated**: 2024-01-06

---

## Overview

The AgentTrace Benchmark Execution Engine provides a complete, production-ready infrastructure for running benchmark evaluations on submitted agents. It includes comprehensive security, reproducibility, and scalability features.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Benchmark Orchestrator                    │
│  - Queue Management    - Circuit Breaker    - Progress      │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
    ┌────▼────┐     ┌────▼────┐
    │ Worker 1│     │ Worker 2│   ... (configurable)
    └────┬────┘     └────┬────┘
         │               │
         └───────┬───────┘
                 │
      ┌──────────▼──────────┐
      │    Task Executor     │
      │  - Task Scheduling   │
      │  - Resource Tracking │
      │  - Scoring           │
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │  Agent Interface     │
      │  - HTTP / gRPC       │
      │  - Local Python      │
      │  - Sandboxing        │
      └─────────────────────┘
```

## Core Components

### 1. Submission Handler

Validates and queues benchmark evaluation requests.

**File**: `engine/submission.py`

**Key Features**:
- ✅ Comprehensive validation (11 checks)
- ✅ Rate limiting (5/day, 20/week)
- ✅ Endpoint reachability testing
- ✅ Terms of service enforcement
- ✅ Category validation
- ✅ Quota management

**Usage**:
```python
from agenttrace_benchmark.engine import SubmissionHandler, BenchmarkSubmission

handler = SubmissionHandler()

# Create submission
submission = BenchmarkSubmission(
    agent_name="MyAgent",
    agent_version="1.0.0",
    contact_email="me@example.com",
    agent_endpoint=AgentEndpoint(endpoint_type="http", url="https://..."),
    terms_accepted=True,
    submitted_by="user_123",
)

# Validate
result = await handler.validate_submission(submission)

if result.is_valid:
    await handler.queue_submission(submission)
```

### 2. Agent Interface

Secure, sandboxed interface for invoking agents.

**File**: `engine/agent_interface.py`

**Supported Types**:
- **HTTP**: REST API agents
- **Local**: Python function agents
- **gRPC**: Coming soon

**Security Features**:
- Timeout enforcement (task and overall)
- Token counting and budget limits
- Output size limits (50KB default)
- Input sanitization
- Authentication support (Bearer, API Key)

**Usage**:
```python
from agenttrace_benchmark.engine import create_agent_interface, AgentEndpoint

# HTTP agent
agent = create_agent_interface(AgentEndpoint(
    endpoint_type="http",
    url="https://api.example.com/agent",
    auth_type="bearer",
    auth_credentials={"token": "..."},
))

# Invoke
response = await agent.invoke(
    prompt="Task prompt...",
    config={},
    timeout=300.0,
)
```

### 3. Task Executor

Executes benchmark tasks with scoring and resource tracking.

**File**: `engine/executor.py`

**Capabilities**:
- Single task execution
- Category execution (parallel)
- Full benchmark execution
- Automatic scoring
- Retry logic (2 attempts default)
- Resource tracking (tokens, time, tool calls)

**Usage**:
```python
from agenttrace_benchmark.engine import TaskExecutor
from agenttrace_benchmark.tasks import get_tasks_by_category
from agenttrace_benchmark.categories import BenchmarkCategory

executor = TaskExecutor()

# Execute single task
task_result = await executor.execute_task(
    agent=agent,
    task=task,
    submission_id="sub-123",
)

# Execute category (3 tasks in parallel)
category_result = await executor.execute_category(
    agent=agent,
    category=BenchmarkCategory.REASONING,
    submission_id="sub-123",
    parallelism=3,
)
```

### 4. Benchmark Orchestrator

Coordinates complete benchmark execution with workers and queues.

**File**: `engine/orchestrator.py`

**Features**:
- Worker pool management (configurable size)
- Priority queue processing
- Circuit breaker protection
- Real-time progress updates
- Graceful shutdown
- Status monitoring

**Usage**:
```python
from agenttrace_benchmark.engine import BenchmarkOrchestrator

orchestrator = BenchmarkOrchestrator(
    submission_handler=handler,
    executor=executor,
    num_workers=3,
)

# Register progress callback
orchestrator.register_progress_callback(lambda p: print(f"Progress: {p.progress_percentage()}%"))

# Start processing
await orchestrator.start()

# Monitor status
status = orchestrator.get_queue_status()
print(f"Queue size: {status['queue_size']}")
print(f"Active: {status['active_executions']}")

# Stop when done
await orchestrator.stop(graceful=True)
```

---

## Data Models

### Submission Models

**BenchmarkSubmission**
```python
@dataclass
class BenchmarkSubmission:
    submission_id: str
    agent_name: str
    agent_version: str
    organization: Optional[str]
    contact_email: str
    agent_endpoint: AgentEndpoint
    categories: List[BenchmarkCategory]  # Empty = all
    terms_accepted: bool
    submitted_by: str
    # ... more fields
```

**AgentEndpoint**
```python
@dataclass
class AgentEndpoint:
    endpoint_type: str  # "http", "grpc", "local"
    url: Optional[str]
    module_path: Optional[str]  # For local
    function_name: Optional[str]  # For local
    auth_type: Optional[str]
    auth_credentials: Optional[Dict[str, str]]
    max_retries: int = 3
    timeout_seconds: float = 300.0
```

### Execution Models

**TaskExecution**
```python
@dataclass
class TaskExecution:
    execution_id: UUID
    task_id: UUID
    submission_id: str
    status: ExecutionStatus
    agent_input: str
    agent_output: str
    tool_calls: List[ToolCall]
    resource_usage: ResourceUsage
    raw_score: float
    normalized_score: float
    # ... more fields
```

**CategoryExecution**
```python
@dataclass
class CategoryExecution:
    category: str
    submission_id: str
    task_executions: List[TaskExecution]
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_score: float
    # ... more fields
```

**BenchmarkExecution**
```python
@dataclass
class BenchmarkExecution:
    execution_id: UUID
    submission_id: str
    agent_name: str
    agent_version: str
    categories_executed: List[str]
    category_executions: Dict[str, CategoryExecution]
    overall_score: float
    total_tasks: int
    completed_tasks: int
    # ... more fields
```

---

## Validation Process

The submission handler performs these checks:

| Check | Description | Failure Action |
|-------|-------------|----------------|
| **required_fields** | All required fields present | Reject |
| **terms_accepted** | ToS must be accepted | Reject |
| **quota_available** | Rate limits not exceeded | Reject |
| **endpoint_reachable** | Agent endpoint responds | Reject |
| **categories_valid** | Categories exist | Reject |
| **config_valid** | Configuration is safe | Warning only |

**Validation Flow**:
```
Submission
    ↓
Required Fields Check
    ↓
Terms Acceptance Check
    ↓
Quota Check
    ↓
Endpoint Reachability
    ↓
Category Validation
    ↓
Config Safety Check
    ↓
ValidationResult
```

---

## Execution Flow

### Single Task Execution

```
1. Create agent interface from endpoint
2. Sanitize task prompt
3. Invoke agent with timeout
4. Capture response and tool calls
5. Track resource usage
6. Check budget violations
7. Score output
8. Return TaskExecution
```

### Category Execution

```
1. Load tasks for category
2. Create semaphore for parallelism control
3. Execute tasks concurrently (default: 3)
4. Collect results
5. Calculate aggregate metrics
6. Return CategoryExecution
```

### Full Benchmark

```
1. Determine categories to evaluate
2. For each category:
   a. Execute category
   b. Update progress
   c. Store results
3. Calculate overall metrics
4. Return BenchmarkExecution
```

---

## Reproducibility

The engine ensures reproducibility through:

### 1. Environment Snapshots

```python
from agenttrace_benchmark.engine import EnvironmentSnapshot

# Capture environment
snapshot = EnvironmentSnapshot.capture(random_seed=42)

# Included in snapshot:
# - Python version and implementation
# - Platform details (OS, arch)
# - Package versions
# - Benchmark version
# - Random seed
# - Timestamp
```

### 2. Deterministic Task Ordering

```python
from agenttrace_benchmark.engine import DeterministicTaskOrdering

# Tasks always ordered same way for same submission ID
seed = DeterministicTaskOrdering.seed_from_submission_id(submission.submission_id)
ordered_tasks = DeterministicTaskOrdering.order_tasks(tasks, seed)
```

### 3. Execution Recording

```python
from agenttrace_benchmark.engine import ExecutionRecorder

recorder = ExecutionRecorder()

# Records:
# - Agent invocations (prompt, response, duration)
# - Tool calls (tool, parameters, result, duration)
# - Timestamps

# Save for replay
recorder.save_to_file("execution_trace.json")
```

### 4. Verification

```python
from agenttrace_benchmark.engine import ReproducibilityVerifier

# Verify two executions match
matches, differences = ReproducibilityVerifier.verify_executions_match(
    exec1, exec2, tolerance=0.01
)

if not matches:
    print(f"Executions differ: {differences}")
```

---

## Circuit Breaker

Protects against repeatedly failing agents.

**States**:
- **CLOSED**: Normal operation
- **OPEN**: Agent failing, reject requests
- **HALF_OPEN**: Testing recovery

**Parameters**:
- `failure_threshold`: Failures before opening (default: 5)
- `success_threshold`: Successes to close (default: 2)
- `timeout_seconds`: Time before retry (default: 300s)

**Flow**:
```
CLOSED
  ↓ (5 failures)
OPEN
  ↓ (5 min timeout)
HALF_OPEN
  ↓ (2 successes)
CLOSED

or

HALF_OPEN
  ↓ (1 failure)
OPEN
```

---

## Resource Tracking

Every execution tracks:

| Resource | Tracked | Enforced |
|----------|---------|----------|
| **Tokens** | ✓ Input + Output | ✓ Budget limit |
| **Time** | ✓ Wall-clock | ✓ Timeout |
| **Tool Calls** | ✓ Count + Details | - |
| **API Calls** | ✓ Count | - |
| **Memory** | Future | Future |

**ResourceUsage Model**:
```python
@dataclass
class ResourceUsage:
    tokens_input: int
    tokens_output: int
    tokens_total: int
    execution_time_seconds: float
    tool_calls_count: int
    api_calls_count: int
    memory_peak_mb: float
```

---

## Error Handling

### Failure Reasons

Categorized for debugging:

| Reason | Description | Retry? |
|--------|-------------|--------|
| **AGENT_ERROR** | Agent raised exception | Yes |
| **AGENT_TIMEOUT** | Exceeded time limit | No |
| **AGENT_UNREACHABLE** | Network error | Yes |
| **RESOURCE_EXCEEDED** | Over budget | No |
| **INVALID_OUTPUT** | Malformed response | No |
| **SECURITY_VIOLATION** | Prohibited operation | No |
| **INTERNAL_ERROR** | Evaluation system error | Yes |

### Retry Logic

```python
# Configurable in TaskExecutor
executor = TaskExecutor(
    enable_retries=True,
    max_retries=2,  # Total 3 attempts
)

# Exponential backoff: 2^attempt seconds
# Attempt 1: immediate
# Attempt 2: 2s delay
# Attempt 3: 4s delay
```

---

## Progress Tracking

Real-time progress updates via callbacks:

```python
def my_progress_callback(progress: ExecutionProgress):
    print(f"""
    Submission: {progress.submission_id}
    Progress: {progress.progress_percentage():.1f}%
    Completed: {progress.completed_tasks}
    Failed: {progress.failed_tasks}
    Remaining: {progress.tasks_remaining()}
    Current: {progress.current_task}
    Status: {progress.status_message}
    """)

orchestrator.register_progress_callback(my_progress_callback)
```

---

## Performance Considerations

### Parallelism

Default parallelism: **3 tasks concurrently**

Adjust based on:
- Agent capacity
- Network bandwidth
- Memory constraints

```python
# Per-category parallelism
executor.execute_category(..., parallelism=5)

# Worker pool size
orchestrator = BenchmarkOrchestrator(..., num_workers=10)
```

### Resource Limits

**Defaults**:
- Max input: 100KB
- Max output: 50KB
- Task timeout: Per-task limit
- Token budget: Per-task limit

**Override**:
```python
agent = HTTPAgentInterface(
    endpoint,
    max_output_size=100000,  # 100KB
)
```

### Scalability

**Current**: Single-process async
**Future**: Multi-process, distributed execution

**Scaling Strategy**:
1. Increase `num_workers` (async concurrency)
2. Add process-level parallelism
3. Distribute across machines (future)

---

## Security

### Input Sanitization

- Size limits (100KB input)
- Encoding validation
- Injection detection (future)

### Output Sanitization

- Size limits (50KB output)
- Automatic truncation
- Format validation

### Network Isolation

- Only whitelisted tool endpoints
- No arbitrary network access
- Authentication required

### Authentication

Supported methods:
- Bearer token
- API key
- Custom headers (future)

---

## Monitoring & Logging

### Log Levels

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Log Events**:
- Submission received
- Validation pass/fail
- Execution start/end
- Task completion
- Errors and warnings
- Resource usage
- Circuit breaker state changes

### Metrics

Track via `orchestrator.get_queue_status()`:
- Queue size
- Active executions
- Completed executions
- Worker status
- Circuit breaker states

---

## API Reference

See inline documentation in:
- `engine/submission.py`
- `engine/executor.py`
- `engine/agent_interface.py`
- `engine/orchestrator.py`
- `engine/models/`

---

## Examples

### Complete Example

See [examples/engine_usage.py](../examples/engine_usage.py) for:
1. Creating submissions
2. Validation
3. Single task execution
4. Category execution
5. Full orchestrated execution
6. HTTP vs local agents

### Quick Start

```python
import asyncio
from agenttrace_benchmark.engine import *

async def main():
    # Setup
    handler = SubmissionHandler()
    executor = TaskExecutor()
    orchestrator = BenchmarkOrchestrator(handler, executor)

    # Create submission
    submission = BenchmarkSubmission(...)

    # Validate
    result = await handler.validate_submission(submission)

    if result.is_valid:
        # Queue
        await handler.queue_submission(submission)

        # Start processing
        await orchestrator.start()

        # Monitor
        status = orchestrator.get_queue_status()

        # Stop
        await orchestrator.stop()

asyncio.run(main())
```

---

## Future Enhancements

### Short-term (v0.2.0)
- [ ] gRPC agent support
- [ ] Memory profiling
- [ ] Advanced caching
- [ ] Result persistence (database)

### Medium-term (v0.3.0)
- [ ] Multi-process execution
- [ ] Streaming progress updates
- [ ] Cost estimation
- [ ] Benchmark scheduling

### Long-term (v1.0.0)
- [ ] Distributed execution
- [ ] Custom tool sandboxes
- [ ] Advanced security (sandboxed Docker)
- [ ] Real-time leaderboard integration

---

## Troubleshooting

### Common Issues

**Issue**: "Endpoint not reachable"
**Solution**: Check URL, firewall, authentication

**Issue**: "Rate limit exceeded"
**Solution**: Wait or request quota increase

**Issue**: "Circuit breaker open"
**Solution**: Fix agent, wait for timeout, then retry

**Issue**: "Task timeout"
**Solution**: Optimize agent or increase time limit

**Issue**: "Token budget exceeded"
**Solution**: Optimize agent output or increase budget

---

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for:
- Code style guidelines
- Testing requirements
- Pull request process

---

## License

MIT License - See [LICENSE](../../LICENSE)

---

**Last Updated**: 2024-01-06
**Maintainer**: AgentTrace Team
**Status**: Production Ready
