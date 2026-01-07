# AgentTrace Evaluation Framework

A comprehensive framework for evaluating AI agent traces with support for custom evaluators, scoring, and aggregation.

## Overview

The evaluation framework provides:

- **Abstract base classes** for creating custom evaluators
- **Flexible scoring system** with pass/fail thresholds
- **Result aggregation** for analyzing multiple evaluations
- **Global registry** for managing evaluators
- **Decorator support** for function-based evaluators
- **Type safety** with comprehensive type hints
- **Thread-safe** registry implementation

## Core Components

### 1. Evaluator Base Class

Abstract base class for creating custom evaluators:

```python
from agenttrace.evals import Evaluator, EvalResult, EvalScore, Trace

class AccuracyEvaluator(Evaluator):
    @property
    def name(self) -> str:
        return "accuracy"

    @property
    def description(self) -> str:
        return "Evaluates response accuracy"

    async def evaluate(self, trace: Trace) -> EvalResult:
        # Your evaluation logic here
        score = EvalScore(name="accuracy", value=0.95, threshold=0.8)
        return EvalResult(
            evaluator_name=self.name,
            scores={"accuracy": score},
            feedback="High accuracy achieved"
        )
```

### 2. Function-Based Evaluators

Use the `@register_evaluator` decorator for simpler evaluators:

```python
from agenttrace.evals import register_evaluator, Trace, EvalResult, EvalScore

@register_evaluator(name="completeness", description="Checks completeness")
async def check_completeness(trace: Trace) -> EvalResult:
    """Evaluate trace completeness."""
    score = EvalScore(name="completeness", value=0.8, threshold=0.7)
    return EvalResult(
        evaluator_name="completeness",
        scores={"completeness": score}
    )
```

### 3. Result Models

#### EvalScore

Represents a single evaluation metric:

```python
from agenttrace.evals import EvalScore

# Score without threshold
score = EvalScore(name="quality", value=0.85)

# Score with threshold (auto-computes passed status)
score = EvalScore(name="quality", value=0.85, threshold=0.8)
print(score.passed)  # True
```

**Attributes:**
- `name`: Metric name
- `value`: Normalized score (0.0 to 1.0)
- `threshold`: Optional pass/fail threshold
- `passed`: Auto-computed from value vs threshold

#### EvalResult

Contains results from a single evaluator:

```python
from agenttrace.evals import EvalResult, EvalScore

result = EvalResult(
    evaluator_name="my_evaluator",
    scores={
        "accuracy": EvalScore("accuracy", 0.9),
        "completeness": EvalScore("completeness", 0.85)
    },
    feedback="Excellent performance",
    metadata={"model": "gpt-4", "temperature": 0.7}
)

# Check if all scores passed their thresholds
if result.all_passed():
    print("All checks passed!")

# Get specific score
accuracy = result.get_score("accuracy")
```

**Attributes:**
- `evaluator_name`: Name of the evaluator
- `scores`: Dictionary of score name to EvalScore
- `feedback`: Optional human-readable feedback
- `metadata`: Additional evaluation metadata
- `timestamp`: When evaluation was performed

#### EvalSummary

Aggregates multiple evaluation results:

```python
from agenttrace.evals import EvalSummary

summary = EvalSummary(results=[result1, result2, result3])

print(f"Pass rate: {summary.pass_rate:.1%}")
print(f"Average scores: {summary.average_scores}")

# Get failed evaluations
for failed in summary.get_failed_results():
    print(f"Failed: {failed.evaluator_name}")
```

**Attributes:**
- `results`: List of EvalResult objects
- `total_evaluators`: Total number of evaluators
- `passed_evaluators`: Number that passed all thresholds
- `failed_evaluators`: Number that failed any threshold
- `average_scores`: Average values per metric
- `pass_rate`: Percentage that passed (0.0 to 1.0)

### 4. Evaluator Registry

Global registry for managing evaluators:

```python
from agenttrace.evals import get_registry

registry = get_registry()

# Register an evaluator
registry.register(my_evaluator)

# Register with namespace
registry.register(my_evaluator, namespace="agenttrace")

# Get evaluator
evaluator = registry.get("agenttrace.completeness")

# List all evaluators
all_names = registry.list_all()
agenttrace_names = registry.list_all(namespace="agenttrace")

# Check if registered
if "my_evaluator" in registry:
    print("Evaluator is registered")

# Get all evaluators
all_evaluators = registry.get_all()
for name, evaluator in all_evaluators.items():
    print(f"{name}: {evaluator.description}")
```

### 5. Trace Object

Represents a complete trace with spans:

```python
from agenttrace.evals import Trace

trace = Trace(
    trace_id="trace-123",
    spans=[
        {"span_id": "1", "name": "llm_call", "parent_id": None},
        {"span_id": "2", "name": "tool_use", "parent_id": "1"}
    ],
    metadata={"user_id": "user-123"},
    tags=["production"]
)

# Get root span (span with no parent)
root = trace.get_root_span()

# Get spans by name
llm_spans = trace.get_spans_by_name("llm_call")

# Get span by ID
span = trace.get_span_by_id("2")
```

## Usage Patterns

### Pattern 1: Class-Based Evaluator with Registration

```python
from agenttrace.evals import Evaluator, register_evaluator, get_registry

@register_evaluator()
class LatencyEvaluator(Evaluator):
    @property
    def name(self) -> str:
        return "latency"

    @property
    def description(self) -> str:
        return "Checks trace latency"

    async def evaluate(self, trace: Trace) -> EvalResult:
        # Implementation
        pass

# Automatically registered via decorator
registry = get_registry()
evaluator = registry.get("latency")
```

### Pattern 2: Function-Based Evaluator

```python
from agenttrace.evals import register_evaluator

@register_evaluator()
async def error_rate_check(trace: Trace) -> EvalResult:
    """Check error rate in trace."""
    error_spans = [s for s in trace.spans if s.get("status") == "error"]
    error_rate = len(error_spans) / len(trace.spans)

    score = EvalScore(
        name="error_rate",
        value=1.0 - error_rate,  # Inverted: higher is better
        threshold=0.95  # Allow up to 5% errors
    )

    return EvalResult(
        evaluator_name="error_rate_check",
        scores={"error_rate": score},
        feedback=f"Error rate: {error_rate:.1%}"
    )
```

### Pattern 3: Running Multiple Evaluators

```python
from agenttrace.evals import get_registry, EvalSummary

async def evaluate_trace(trace: Trace):
    """Run all registered evaluators on a trace."""
    registry = get_registry()
    results = []

    for name, evaluator in registry.get_all().items():
        result = await evaluator.evaluate(trace)
        results.append(result)

    # Create summary
    summary = EvalSummary(results=results)

    return summary
```

### Pattern 4: Custom Namespace Organization

```python
from agenttrace.evals import get_registry

registry = get_registry()

# Register with namespaces
registry.register(accuracy_eval, namespace="agenttrace.quality")
registry.register(latency_eval, namespace="agenttrace.performance")
registry.register(custom_eval, namespace="mycompany")

# Get by namespace
quality_evals = registry.get_all(namespace="agenttrace.quality")
performance_evals = registry.get_all(namespace="agenttrace.performance")
```

## Testing

The framework includes comprehensive unit tests:

```bash
# Run all eval tests
pytest tests/evals/

# Run specific test file
pytest tests/evals/test_models.py
pytest tests/evals/test_base.py
pytest tests/evals/test_registry.py

# Run with coverage
pytest tests/evals/ --cov=agenttrace.evals --cov-report=html
```

## Best Practices

1. **Normalize scores to 0.0-1.0**: Always normalize evaluation scores to the 0.0-1.0 range
2. **Use meaningful thresholds**: Set thresholds based on actual requirements
3. **Provide feedback**: Include human-readable feedback in results
4. **Add metadata**: Store additional context in metadata for debugging
5. **Use namespaces**: Organize evaluators with namespaces for clarity
6. **Test evaluators**: Write unit tests for custom evaluators
7. **Async by default**: All evaluators should be async for consistency

## API Reference

### Classes

- `Evaluator`: Abstract base class for evaluators
- `FunctionEvaluator`: Wrapper for function-based evaluators
- `Trace`: Represents a complete trace
- `EvalScore`: Single evaluation score
- `EvalResult`: Result from one evaluator
- `EvalSummary`: Aggregated results from multiple evaluators
- `EvaluatorRegistry`: Registry for managing evaluators

### Functions

- `register_evaluator(name, description, auto_register)`: Decorator for registering evaluators
- `get_registry()`: Get the global evaluator registry
- `reset_registry()`: Reset the global registry (for testing)

### Decorators

- `@register_evaluator()`: Register a function or class as an evaluator

## Examples

See [examples/eval_example.py](../../../examples/eval_example.py) for a complete working example.

## License

MIT License - See LICENSE file for details
