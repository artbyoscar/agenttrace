# Getting Started with AgentTrace Benchmark

This guide will help you get up and running with the AgentTrace Benchmark in under 15 minutes.

## Table of Contents

1. [Installation](#installation)
2. [Core Concepts](#core-concepts)
3. [Your First Evaluation](#your-first-evaluation)
4. [Understanding Results](#understanding-results)
5. [Creating Custom Tasks](#creating-custom-tasks)
6. [Best Practices](#best-practices)
7. [Next Steps](#next-steps)

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/artbyoscar/agenttrace.git
cd agenttrace/packages/benchmark

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Install with visualization tools
pip install -e ".[viz]"
```

### Verify Installation

```python
import agenttrace_benchmark as atb

print(f"AgentTrace Benchmark v{atb.__version__}")
print(f"Available categories: {len(atb.BenchmarkCategory)}")
```

---

## Core Concepts

### 1. Categories

The benchmark evaluates six core capabilities:

```python
from agenttrace_benchmark import BenchmarkCategory

for category in BenchmarkCategory:
    print(category.value)
# reasoning, tool_use, planning, grounding, robustness, efficiency
```

### 2. Tasks

Each task is a complete specification of what to evaluate:

```python
from agenttrace_benchmark import BenchmarkTask, DifficultyLevel

task = BenchmarkTask(
    category=BenchmarkCategory.REASONING,
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Simple Logic Puzzle",
    prompt="Your task prompt here...",
    time_limit_seconds=60,
    token_budget=300,
)
```

### 3. Scoring

Evaluation produces hierarchical scores:

- **Task Score**: 0-100 for individual task
- **Category Score**: Aggregate across category with confidence intervals
- **Composite Score**: Weighted average across all categories

---

## Your First Evaluation

### Step 1: Define Your Agent

Create a function that takes a prompt and returns a response:

```python
def my_agent(prompt: str) -> str:
    """
    Your agent implementation.

    This could call an LLM, run a reasoning system, etc.
    """
    # Example: Simple LLM call
    response = your_llm.generate(prompt)
    return response
```

### Step 2: Load a Task

```python
from agenttrace_benchmark.examples.example_tasks import create_reasoning_task

task = create_reasoning_task()
print(f"Task: {task.name}")
print(f"Difficulty: {task.difficulty.value}")
```

### Step 3: Run Your Agent

```python
import time

# Track execution metrics
start_time = time.time()
agent_output = my_agent(task.prompt)
execution_time = time.time() - start_time

# You'll need to track these from your agent
tokens_used = 234  # Count tokens in prompt + response
tool_calls = 0     # Number of external tool invocations
```

### Step 4: Score the Result

```python
from agenttrace_benchmark import ScoringEngine

engine = ScoringEngine()
score = engine.score_task(
    task=task,
    agent_output=agent_output,
    execution_time=execution_time,
    tokens_used=tokens_used,
    tool_calls=tool_calls,
)

print(f"Score: {score.normalized_score:.1f}/100")
print(f"Success: {score.success}")
```

### Complete Example

```python
from agenttrace_benchmark import ScoringEngine
from agenttrace_benchmark.examples.example_tasks import create_reasoning_task
import time

# Load task
task = create_reasoning_task()

# Run agent
start_time = time.time()
agent_output = my_agent(task.prompt)
execution_time = time.time() - start_time

# Score
engine = ScoringEngine()
score = engine.score_task(
    task=task,
    agent_output=agent_output,
    execution_time=execution_time,
    tokens_used=234,
    tool_calls=0,
)

print(f"✓ {task.name}: {score.normalized_score:.1f}/100")
```

---

## Understanding Results

### Task-Level Metrics

```python
print(f"Raw Score: {score.raw_score:.1f}/100")
print(f"Normalized Score: {score.normalized_score:.1f}/100")  # Difficulty-adjusted
print(f"Execution Time: {score.execution_time_seconds:.2f}s")
print(f"Tokens Used: {score.tokens_used}")
print(f"Success: {score.success}")

if score.error_message:
    print(f"Error: {score.error_message}")
```

**Key Points**:
- `raw_score`: Unadjusted evaluation result
- `normalized_score`: Adjusted for difficulty (harder tasks worth more)
- `success`: Whether task was completed without violations

### Category-Level Metrics

```python
category_score = engine.compute_category_score(
    BenchmarkCategory.REASONING,
    [score1, score2, score3]  # All scores in category
)

print(f"Mean: {category_score.mean_score:.1f}/100")
print(f"Median: {category_score.median_score:.1f}/100")
print(f"Std Dev: {category_score.std_dev:.1f}")
print(f"95% CI: [{category_score.confidence_interval[0]:.1f}, "
      f"{category_score.confidence_interval[1]:.1f}]")
```

**Key Points**:
- Mean is primary metric
- Median is robust to outliers
- Confidence interval quantifies uncertainty
- Wider CI = more variance in performance

### Composite Score

```python
composite = engine.compute_composite_score(
    category_scores,
    agent_name="MyAgent",
    agent_version="1.0.0",
)

print(f"Overall: {composite.overall_score:.1f}/100")
print(f"Confidence: [{composite.confidence_interval[0]:.1f}, "
      f"{composite.confidence_interval[1]:.1f}]")
print(f"Success Rate: {composite.total_successes}/{composite.total_tasks}")
```

**Category Weights** (default):
- Reasoning: 20%
- Tool Use: 20%
- Planning: 18%
- Grounding: 18%
- Robustness: 12%
- Efficiency: 12%

---

## Creating Custom Tasks

### Basic Task Template

```python
from agenttrace_benchmark import (
    BenchmarkTask,
    BenchmarkCategory,
    DifficultyLevel,
    EvaluationType,
    EvaluationCriterion,
    TaskMetadata,
)

task = BenchmarkTask(
    # Identification
    category=BenchmarkCategory.REASONING,
    subcategory="your_subcategory",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Task Name",
    description="What this task evaluates",

    # Content
    prompt="The actual task prompt...",

    # Evaluation
    evaluation_type=EvaluationType.EXACT_MATCH,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correctness",
            description="Is the answer correct?",
            weight=1.0,
            measurement_type="binary",
        ),
    ],

    # Constraints
    time_limit_seconds=60,
    token_budget=300,

    # Metadata
    metadata=TaskMetadata(
        version="1.0.0",
        author=["Your Name"],
        tags=["tag1", "tag2"],
    ),
)
```

### Adding Evaluation Criteria

Tasks can have multiple weighted criteria:

```python
evaluation_criteria=[
    EvaluationCriterion(
        name="correctness",
        description="Is the final answer correct?",
        weight=0.5,  # 50% of score
        measurement_type="binary",
        rubric="1.0 if correct, 0.0 otherwise",
    ),
    EvaluationCriterion(
        name="reasoning_quality",
        description="Is the reasoning sound?",
        weight=0.3,  # 30% of score
        measurement_type="continuous",
        rubric="Score 0.0-1.0 based on logical validity",
    ),
    EvaluationCriterion(
        name="clarity",
        description="Is the explanation clear?",
        weight=0.2,  # 20% of score
        measurement_type="continuous",
        rubric="Score 0.0-1.0 based on readability",
    ),
]
# Weights must sum to 1.0
```

### Adding Tool Requirements

For tasks requiring specific tools:

```python
from agenttrace_benchmark import ToolRequirement

required_tools=[
    ToolRequirement(
        tool_name="web_search",
        tool_type="api",
        version="2.0",
        configuration={"rate_limit": "10/minute"},
        required=True,
    ),
    ToolRequirement(
        tool_name="calculator",
        tool_type="function",
        required=True,
    ),
]
```

---

## Best Practices

### 1. Track All Metrics

Always track execution time, tokens, and tool calls:

```python
class AgentWrapper:
    def __init__(self, agent):
        self.agent = agent

    def run(self, prompt):
        start = time.time()

        # Initialize counters
        self.tokens_used = 0
        self.tool_calls = 0

        # Run agent with instrumentation
        output = self.agent.run_with_tracking(prompt)

        execution_time = time.time() - start

        return output, execution_time, self.tokens_used, self.tool_calls
```

### 2. Batch Evaluations

Evaluate multiple tasks together for efficiency:

```python
def evaluate_batch(agent, tasks):
    engine = ScoringEngine()
    results = []

    for task in tasks:
        output, exec_time, tokens, tools = agent.run(task.prompt)
        score = engine.score_task(task, output, exec_time, tokens, tools)
        results.append(score)

    return results
```

### 3. Save Results

Persist results for later analysis:

```python
import json
from datetime import datetime

results = {
    "agent": "MyAgent",
    "version": "1.0.0",
    "timestamp": datetime.utcnow().isoformat(),
    "scores": [
        {
            "task_id": str(score.task_id),
            "normalized_score": score.normalized_score,
            "success": score.success,
        }
        for score in task_scores
    ],
}

with open("results.json", "w") as f:
    json.dump(results, f, indent=2)
```

### 4. Compare Versions

Track improvements across agent versions:

```python
def compare_versions(scores_v1, scores_v2):
    engine = ScoringEngine()

    comparison = engine.compare_submissions(scores_v1, scores_v2)

    print(f"Improvement: {comparison['difference']:+.1f} points")
    print(f"Effect size: {comparison['effect_size']:.3f} ({comparison['interpretation']})")
    print(f"Significant: {comparison['significant']}")
```

---

## Next Steps

### 1. Run the Examples

```bash
cd examples/
python basic_usage.py
```

### 2. Create Your Own Tasks

See [example_tasks.py](../examples/example_tasks.py) for templates.

### 3. Read the Design Doc

Understand the academic foundations: [DESIGN.md](DESIGN.md)

### 4. Explore Categories

Read about each category in the main README: [README.md](../README.md#benchmark-categories)

### 5. Join the Community

- Report issues: https://github.com/artbyoscar/agenttrace/issues
- Discussions: https://github.com/artbyoscar/agenttrace/discussions
- Documentation: https://docs.agenttrace.dev/benchmark

---

## Common Questions

### Q: How do I implement custom evaluation logic?

A: Set `evaluation_type=EvaluationType.CUSTOM` and provide a `custom_evaluator` function name. You'll need to register this function with the scoring engine.

### Q: Can I change category weights?

A: Yes! Pass custom weights when computing composite scores:

```python
from agenttrace_benchmark.categories import CATEGORY_DEFINITIONS

# Create custom weights
custom_weights = CATEGORY_DEFINITIONS.copy()
custom_weights[BenchmarkCategory.EFFICIENCY].weight = 0.30  # Prioritize efficiency

# Use in scoring
composite = engine.compute_composite_score(
    category_scores,
    # Custom weights applied via modified CATEGORY_DEFINITIONS
)
```

### Q: How many tasks do I need for reliable results?

A: We recommend:
- Minimum: 5 tasks per category
- Good: 10-15 tasks per category
- Excellent: 20+ tasks per category

More tasks → narrower confidence intervals → more reliable scores.

### Q: What if my agent times out?

A: The scoring engine will:
1. Mark `success=False`
2. Apply a penalty (50% of score)
3. Record the timeout in `error_message`

### Q: Can I submit to a leaderboard?

A: Public leaderboard is planned for v1.0.0. Currently, you can track results locally or share them manually.

---

## Troubleshooting

### Import Errors

```bash
# Ensure package is installed
pip install -e .

# Verify installation
python -c "import agenttrace_benchmark; print('OK')"
```

### Scoring Errors

```python
# Check task validity
task.__post_init__()  # Will raise ValueError if invalid

# Verify criteria weights
total = sum(c.weight for c in task.evaluation_criteria)
assert abs(total - 1.0) < 1e-6, "Weights must sum to 1.0"
```

### Performance Issues

```python
# Reduce bootstrap samples for faster scoring
engine = ScoringEngine(n_bootstrap_samples=1000)  # Default: 10000

# Note: Fewer samples = less accurate confidence intervals
```

---

**Ready to benchmark your agent? Start with the [basic usage example](../examples/basic_usage.py)!**

For questions or feedback, visit: https://github.com/artbyoscar/agenttrace/issues
