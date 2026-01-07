# Built-in Evaluators

Comprehensive suite of pre-built evaluators covering common agent quality dimensions.

## Overview

AgentTrace provides 12 built-in evaluators organized into 5 categories:

- **Response Quality** (3 evaluators): Completeness, relevance, coherence
- **Tool Usage** (2 evaluators): Accuracy, selection appropriateness
- **Efficiency** (3 evaluators): Token usage, latency, trajectory optimality
- **Safety** (2 evaluators): PII detection, harmful content
- **Domain-Specific** (2 evaluators): Factual accuracy (RAG), code correctness

All evaluators are automatically registered when imported and can be used immediately.

## Quick Start

```python
from agenttrace.evals import Trace, get_registry
from agenttrace.evals.evaluators import ResponseCompletenessEvaluator

# Create a trace
trace = Trace(
    trace_id="trace-123",
    spans=[{
        "span_id": "1",
        "name": "agent_run",
        "parent_id": None,
        "metadata": {
            "input": "What is Python?",
            "output": "Python is a high-level programming language."
        }
    }]
)

# Use evaluator directly
evaluator = ResponseCompletenessEvaluator()
result = await evaluator.evaluate(trace)
print(f"Completeness: {result.scores['completeness'].value}")

# Or get from registry
registry = get_registry()
evaluator = registry.get("response_completeness")
```

## Response Quality Evaluators

### ResponseCompletenessEvaluator

Assesses if the response addresses all aspects of the input query using LLM-as-judge.

**Configuration:**
```python
from agenttrace.evals.evaluators import ResponseCompletenessEvaluator
from agenttrace.evals.evaluators._llm_judge import JudgeConfig

config = JudgeConfig(
    model="gpt-4",           # Judge model
    temperature=0.0,          # Sampling temperature
    max_tokens=500           # Max response tokens
)

evaluator = ResponseCompletenessEvaluator(
    config=config,
    threshold=0.7            # Minimum passing score
)
```

**Scores:**
- `completeness` (0.0-1.0): How completely the response addresses the input

**Use Cases:**
- Question answering systems
- Customer support agents
- Information retrieval

---

### ResponseRelevanceEvaluator

Measures how relevant the response is to the query, penalizing off-topic content.

**Configuration:**
```python
evaluator = ResponseRelevanceEvaluator(
    config=JudgeConfig(model="gpt-4"),
    threshold=0.75
)
```

**Scores:**
- `relevance` (0.0-1.0): How on-topic the response is

**Use Cases:**
- Chatbots
- Search and retrieval
- Content filtering

---

### ResponseCoherenceEvaluator

Evaluates logical flow and internal consistency, detecting contradictions.

**Configuration:**
```python
evaluator = ResponseCoherenceEvaluator(
    config=JudgeConfig(model="gpt-4"),
    threshold=0.7
)
```

**Scores:**
- `coherence` (0.0-1.0): Logical flow and consistency

**Use Cases:**
- Long-form content generation
- Report generation
- Multi-turn conversations

## Tool Usage Evaluators

### ToolCallAccuracyEvaluator

Measures successful vs failed tool calls, identifying problematic tools.

**Configuration:**
```python
evaluator = ToolCallAccuracyEvaluator(
    threshold=0.9  # Minimum success rate
)
```

**Scores:**
- `tool_success_rate` (0.0-1.0): Percentage of successful tool calls

**Metadata:**
- `failed_tools`: List of tools that failed
- `errors`: Detailed error information

**Use Cases:**
- Tool-using agents
- API integrations
- External service reliability

---

### ToolSelectionEvaluator

Uses LLM to judge if the correct tools were selected for the task.

**Configuration:**
```python
evaluator = ToolSelectionEvaluator(
    config=JudgeConfig(model="gpt-4"),
    threshold=0.75,
    available_tools=["web_search", "calculator", "file_reader"]
)
```

**Scores:**
- `appropriateness` (0.0-1.0): How appropriate the tool selections were

**Use Cases:**
- Agent optimization
- Tool usage analysis
- Identifying missing or unnecessary tool calls

## Efficiency Evaluators

### TokenEfficiencyEvaluator

Compares token usage against a baseline to detect inefficiency.

**Configuration:**
```python
evaluator = TokenEfficiencyEvaluator(
    baseline_tokens=1000,        # Expected token count
    threshold=0.7,               # Minimum efficiency
    max_acceptable_ratio=1.5     # Max acceptable vs baseline (150%)
)
```

**Scores:**
- `efficiency_ratio` (0.0-1.0): Efficiency score (1.0 = at or below baseline)

**Metadata:**
- `total_tokens`: Actual token count
- `actual_ratio`: Actual / baseline ratio
- `llm_spans`: Per-span token breakdowns

**Use Cases:**
- Cost optimization
- Performance monitoring
- Model comparison

---

### LatencyEvaluator

Measures execution time against configurable thresholds with percentile analysis.

**Configuration:**
```python
evaluator = LatencyEvaluator(
    latency_thresholds={
        "p50": 2.0,   # 50th percentile max (seconds)
        "p95": 5.0,   # 95th percentile max
        "p99": 10.0   # 99th percentile max
    },
    threshold=0.8,
    span_type_thresholds={
        "llm_call": 2.0,      # Max latency for LLM calls
        "tool_use": 1.0       # Max latency for tool use
    }
)
```

**Scores:**
- `latency` (0.0-1.0): Overall latency score
- `p50`, `p95`, `p99`: Individual percentile scores

**Metadata:**
- `slow_spans`: Spans exceeding type-specific thresholds

**Use Cases:**
- Performance optimization
- SLA monitoring
- User experience improvement

---

### TrajectoryOptimalityEvaluator

Analyzes if the agent took an optimal path, identifying redundant steps and loops.

**Configuration:**
```python
evaluator = TrajectoryOptimalityEvaluator(
    threshold=0.7
)
```

**Scores:**
- `optimality` (0.0-1.0): Path optimality (1.0 = optimal)

**Metadata:**
- `loops`: Detected repetitive patterns
- `redundant_calls`: Duplicate operations
- `retries`: Error/retry spans

**Use Cases:**
- Agent behavior optimization
- Workflow improvement
- Cost reduction

## Safety Evaluators

### PIIDetectionEvaluator

Scans outputs for personally identifiable information using regex patterns.

**Configuration:**
```python
evaluator = PIIDetectionEvaluator(
    detect_types=["email", "phone", "ssn", "credit_card"],
    use_ner=False,               # Use NER model (optional)
    custom_patterns={
        "employee_id": r"EMP-\d{5}"
    }
)
```

**Available PII Types:**
- `email`: Email addresses
- `phone`: Phone numbers
- `ssn`: Social Security Numbers
- `credit_card`: Credit card numbers
- `ip_address`: IP addresses
- `street_address`: Street addresses

**Scores:**
- `pii_free` (1.0 or 0.0): Binary pass/fail (threshold=1.0)

**Metadata:**
- `detected_pii_types`: List of PII types found
- `pii_count`: Total number of PII instances

**Use Cases:**
- GDPR compliance
- Data privacy
- Healthcare (HIPAA)
- Financial services

---

### HarmfulContentEvaluator

Checks for harmful, toxic, or inappropriate content using LLM-as-judge.

**Configuration:**
```python
evaluator = HarmfulContentEvaluator(
    config=JudgeConfig(model="gpt-4"),
    threshold=0.9,
    sensitivity="high",  # "low", "medium", "high"
    check_categories=[
        "hate_speech",
        "violence",
        "sexual_content",
        "harassment",
        "self_harm",
        "illegal_activities"
    ]
)
```

**Scores:**
- `safety` (0.0-1.0): Content safety score

**Use Cases:**
- Content moderation
- Brand safety
- User-facing applications
- Compliance

## Domain-Specific Evaluators

### FactualAccuracyEvaluator

For RAG applications: compares response against retrieved context to detect hallucinations.

**Configuration:**
```python
evaluator = FactualAccuracyEvaluator(
    config=JudgeConfig(model="gpt-4"),
    threshold=0.8,
    strict_mode=False  # If True, any unsupported claim fails
)
```

**Scores:**
- `grounding` (0.0-1.0): How well grounded in context

**Metadata:**
- `unsupported_claims`: List of claims not supported by context

**Trace Requirements:**
- Must have `context` in root span metadata OR
- Must have retrieval spans with `retrieved_documents`

**Use Cases:**
- RAG systems
- Document QA
- Knowledge bases
- Research assistants

---

### CodeCorrectnessEvaluator

For coding agents: validates generated code with syntax checks and optional execution.

**Configuration:**
```python
evaluator = CodeCorrectnessEvaluator(
    threshold=0.8,
    execute_code=False,          # DANGEROUS - use with caution!
    timeout=5.0,                 # Execution timeout (seconds)
    allowed_imports=["math", "json", "datetime"]
)
```

**Scores:**
- `correctness` (0.0-1.0): Code quality score
  - Base: 0.5 for syntax validity
  - +0.2 for allowed imports
  - +0.3 for successful execution (if enabled)

**Metadata:**
- `syntax_valid`: Boolean
- `imports_valid`: Boolean
- `disallowed_imports`: List of disallowed modules
- `execution_result`: Execution details (if enabled)

**Use Cases:**
- Code generation agents
- Automated code review
- Educational tools
- Code completion

**⚠️ Warning:** Code execution is dangerous and should only be enabled in sandboxed environments.

## Advanced: LLM-as-Judge

Many evaluators use the LLM-as-judge pattern. You can configure the judge model:

```python
from agenttrace.evals.evaluators._llm_judge import JudgeConfig, SimpleLLMClient

# Basic configuration
config = JudgeConfig(
    model="gpt-4-turbo",
    temperature=0.0,
    max_tokens=500
)

# Custom LLM client
class MyLLMClient:
    async def generate(self, prompt: str, **kwargs) -> str:
        # Your LLM API integration
        response = await my_api.call(prompt)
        return response

config = JudgeConfig(client=MyLLMClient())
evaluator = ResponseCompletenessEvaluator(config=config)
```

## Running All Evaluators

```python
from agenttrace.evals import get_registry, EvalSummary

# Get all evaluators
registry = get_registry()
evaluators = registry.get_all()

# Run all evaluators on a trace
results = []
for name, evaluator in evaluators.items():
    result = await evaluator.evaluate(trace)
    results.append(result)

# Create summary
summary = EvalSummary(results=results)
print(f"Pass rate: {summary.pass_rate:.1%}")
```

## Best Practices

1. **Choose appropriate thresholds**: Set thresholds based on your use case
2. **Combine evaluators**: Use multiple evaluators for comprehensive assessment
3. **Monitor trends**: Track scores over time to identify regressions
4. **Configure judge models**: Use appropriate models for LLM-as-judge evaluators
5. **Handle failures gracefully**: Check for evaluation errors in metadata
6. **Test with diverse inputs**: Validate evaluators with varied trace types

## Testing

Run the test suite:

```bash
# All evaluator tests
pytest tests/evals/test_evaluators_*.py -v

# Specific category
pytest tests/evals/test_evaluators_response.py
pytest tests/evals/test_evaluators_tools.py
pytest tests/evals/test_evaluators_efficiency.py
pytest tests/evals/test_evaluators_safety.py
pytest tests/evals/test_evaluators_domain.py

# With coverage
pytest tests/evals/test_evaluators_*.py --cov=agenttrace.evals.evaluators
```

## Contributing

To add a new evaluator:

1. Create the evaluator class inheriting from `Evaluator`
2. Add the `@register_evaluator()` decorator
3. Implement `name`, `description`, and `evaluate()` methods
4. Add comprehensive tests
5. Update this README with usage examples

See the [contributing guide](../../CONTRIBUTING.md) for details.
