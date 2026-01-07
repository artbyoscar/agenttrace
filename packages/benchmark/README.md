# AgentTrace Benchmark Suite

**Academic-grade evaluation framework for AI agent capabilities**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Overview

The AgentTrace Benchmark Suite is a comprehensive, statistically rigorous evaluation framework designed to measure AI agent capabilities across six core dimensions:

- **Reasoning**: Multi-step logical inference and problem decomposition
- **Tool Use**: Appropriate tool selection, composition, and error recovery
- **Planning**: Goal-directed task decomposition and replanning under uncertainty
- **Grounding**: Factual accuracy, source attribution, and hallucination resistance
- **Robustness**: Performance under adversarial inputs and distribution shift
- **Efficiency**: Resource optimization while maintaining quality

## Key Features

### 🎯 Academic Rigor
- Grounded in cognitive science and AI research
- Comprehensive citations for each evaluation dimension
- Statistical confidence intervals for all scores
- Bootstrap resampling for robust estimation
- Effect size calculations for practical significance

### 🛡️ Anti-Gaming Measures
- Held-out test sets never publicly released
- Quarterly task rotation schedule
- Statistical anomaly detection
- Submission rate limiting
- Diversity requirements across categories
- Contamination detection algorithms

### 📊 Transparent Scoring
- Per-task scores normalized 0-100
- Category aggregates with confidence intervals
- Weighted composite scores
- Percentile rankings against all submissions
- Detailed diagnostic breakdowns

### 🔄 Reproducibility
- Versioned task specifications
- Comprehensive metadata tracking
- Deterministic evaluation procedures
- Docker-based execution environments

## Installation

```bash
# From PyPI (when released)
pip install agenttrace-benchmark

# From source
cd packages/benchmark
pip install -e .

# With development dependencies
pip install -e ".[dev]"

# With visualization tools
pip install -e ".[viz]"
```

## Quick Start

### Evaluating an Agent

```python
from agenttrace_benchmark import BenchmarkTask, ScoringEngine, BenchmarkCategory
from agenttrace_benchmark.schema import DifficultyLevel, EvaluationType

# Define a benchmark task
task = BenchmarkTask(
    category=BenchmarkCategory.REASONING,
    subcategory="deductive_reasoning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Logic Puzzle: Knights and Knaves",
    description="Tests ability to perform logical deduction with truth-tellers and liars",
    prompt="""
    You are on an island where some inhabitants always tell the truth (Knights)
    and others always lie (Knaves). You meet two inhabitants, A and B.

    A says: "We are both Knaves."

    What are A and B?
    """,
    evaluation_type=EvaluationType.EXACT_MATCH,
    time_limit_seconds=60,
    token_budget=500,
)

# Run your agent
agent_output = your_agent.run(task.prompt)
execution_time = 12.5  # seconds
tokens_used = 234
tool_calls = 0

# Score the response
engine = ScoringEngine()
score = engine.score_task(
    task=task,
    agent_output=agent_output,
    execution_time=execution_time,
    tokens_used=tokens_used,
    tool_calls=tool_calls,
)

print(f"Task Score: {score.normalized_score:.1f}/100")
print(f"Success: {score.success}")
```

### Loading a Task Suite

```python
from agenttrace_benchmark import TaskSuite
import json

# Load official benchmark suite
with open("benchmark_suite_v1.json", "r") as f:
    suite_data = json.load(f)

# Evaluate across all tasks
results = []
for task_data in suite_data["tasks"]:
    task = BenchmarkTask(**task_data)
    # Run agent and score...
    results.append(score)

# Compute composite score
category_scores = {}
for category in BenchmarkCategory:
    category_tasks = [s for s in results if s.category == category]
    category_scores[category] = engine.compute_category_score(
        category, category_tasks
    )

composite = engine.compute_composite_score(
    category_scores,
    agent_name="MyAgent",
    agent_version="1.0.0",
)

print(f"Overall Score: {composite.overall_score:.1f}/100")
print(f"95% CI: [{composite.confidence_interval[0]:.1f}, {composite.confidence_interval[1]:.1f}]")
```

## Benchmark Categories

### 1. Reasoning

**What it measures**: Ability to perform logical inference, decompose complex problems, and chain reasoning steps.

**Subcategories**:
- Deductive reasoning
- Inductive reasoning
- Abductive reasoning
- Analogical reasoning
- Causal reasoning
- Counterfactual reasoning
- Mathematical reasoning
- Spatial reasoning

**Example tasks**:
- Multi-hop question answering
- Logic puzzles (Einstein's riddle, Sudoku)
- Mathematical word problems
- Code debugging requiring backward reasoning

### 2. Tool Use

**What it measures**: Capability to select appropriate tools, compose them into workflows, and handle failures gracefully.

**Subcategories**:
- Tool selection
- Parameter binding
- Tool composition
- Error detection
- Error recovery
- Tool learning
- Parallel execution
- Resource management

**Example tasks**:
- API composition with authentication
- File system operations with permissions
- Database queries with fallbacks
- Multi-modal tasks combining vision, code, and search

### 3. Planning

**What it measures**: Ability to decompose goals into action sequences, track progress, and replan when circumstances change.

**Subcategories**:
- Task decomposition
- Action sequencing
- Goal tracking
- Replanning
- Partial observability
- Resource optimization
- Multi-agent coordination
- Temporal planning

**Example tasks**:
- Travel itinerary planning with constraints
- Software refactoring with backward compatibility
- Research planning with unknown paper availability
- Resource allocation in multi-objective optimization

### 4. Grounding

**What it measures**: Commitment to factual accuracy, source attribution, and resistance to hallucination.

**Subcategories**:
- Factual accuracy
- Source attribution
- Hallucination resistance
- Knowledge boundaries
- Confidence calibration
- Claim verification
- Temporal awareness
- Context sensitivity

**Example tasks**:
- Multi-source fact verification
- Historical question answering
- Scientific claim validation with citations
- News summarization preserving accuracy

### 5. Robustness

**What it measures**: Performance under distribution shift, adversarial inputs, and edge cases.

**Subcategories**:
- Adversarial resistance
- Prompt injection defense
- Distribution shift
- Edge case handling
- Consistency
- Input validation
- Graceful degradation
- Security awareness

**Example tasks**:
- Question answering with adversarial context
- Code generation with malicious requirements
- Instruction following with prompt injection
- Classification under distributional shift

### 6. Efficiency

**What it measures**: Ability to achieve goals with minimal resource expenditure.

**Subcategories**:
- Token economy
- Latency optimization
- API call minimization
- Caching utilization
- Parallel execution
- Early termination
- Lazy evaluation
- Resource budgeting

**Example tasks**:
- Information retrieval with token budgets
- Code optimization under latency constraints
- Data processing with rate limits
- Question answering with early stopping

## Scoring Methodology

### Per-Task Scoring

Each task is scored on a 0-100 scale based on:

1. **Correctness**: Does the output meet evaluation criteria?
2. **Difficulty Adjustment**: Harder tasks receive higher weight
3. **Resource Compliance**: Penalties for exceeding time/token budgets
4. **Criterion Breakdown**: Weighted average across evaluation dimensions

```python
normalized_score = raw_score × difficulty_multiplier × compliance_factor
```

### Category Aggregation

Category scores are computed with:
- Mean score across all tasks
- Median score (robust to outliers)
- Standard deviation
- 95% confidence interval via bootstrap resampling
- Success rate (% of tasks completed)

### Composite Score

Overall score is weighted average across categories:

```
overall_score = Σ(category_score × category_weight)
```

Default weights:
- Reasoning: 20%
- Tool Use: 20%
- Planning: 18%
- Grounding: 18%
- Robustness: 12%
- Efficiency: 12%

## Anti-Gaming Measures

### Held-Out Test Set

- 30-50% of tasks are never publicly released
- Used for official leaderboard rankings
- Rotated quarterly to prevent adaptation
- Access logged and audited

### Task Rotation

- 20% of public tasks rotated every 90 days
- High-performing tasks prioritized for rotation
- Maintains category distribution balance
- Version history tracked for reproducibility

### Anomaly Detection

Statistical checks for:
- Performance discontinuities (sudden jumps)
- Category imbalance (specialization)
- Outlier scores (>3 standard deviations)
- Contamination patterns

### Diversity Requirements

Submissions must:
- Attempt ≥80% of categories
- Maintain balance across categories (<40 point spread)
- Demonstrate consistent performance

### Rate Limiting

- Maximum 5 submissions per day
- Maximum 20 submissions per week
- Minimum 1 hour between submissions

## Research and Citation

If you use the AgentTrace Benchmark in your research, please cite:

```bibtex
@software{agenttrace_benchmark_2024,
  title = {AgentTrace Benchmark: Academic-Grade AI Agent Evaluation},
  author = {AgentTrace Team},
  year = {2024},
  url = {https://github.com/artbyoscar/agenttrace},
  version = {0.1.0}
}
```

### Academic Foundation

The benchmark design is grounded in:

**Reasoning**:
- Kahneman, D. (2011). Thinking, Fast and Slow
- Johnson-Laird, P. N. (2010). Mental models and human reasoning
- Wei, J. et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in LLMs

**Tool Use**:
- Gibson, J. J. (1979). The Ecological Approach to Visual Perception
- Norman, D. A. (1988). The Psychology of Everyday Things
- Schick, T. et al. (2023). Toolformer: Language Models Can Teach Themselves to Use Tools

**Planning**:
- Erol, K. et al. (1994). HTN Planning: Complexity and Expressivity
- Botvinick, M., & Weinstein, A. (2014). Model-based hierarchical reinforcement learning
- Yao, S. et al. (2023). Tree of Thoughts: Deliberate Problem Solving with LLMs

**Grounding**:
- Harnad, S. (1990). The Symbol Grounding Problem
- Maynez, J. et al. (2020). On Faithfulness and Factuality in Abstractive Summarization
- Lin, S. et al. (2022). TruthfulQA: Measuring How Models Mimic Human Falsehoods

**Robustness**:
- Goodfellow, I. J. et al. (2014). Explaining and Harnessing Adversarial Examples
- Zou, A. et al. (2023). Universal and Transferable Adversarial Attacks on Aligned LLMs

**Efficiency**:
- Simon, H. A. (1972). Theories of Bounded Rationality
- Russell, S., & Wefald, E. (1991). Principles of Metareasoning

## Development

### Running Tests

```bash
# Unit tests
pytest tests/

# With coverage
pytest --cov=agenttrace_benchmark --cov-report=html

# Specific test file
pytest tests/test_scoring.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

### Building Documentation

```bash
cd docs/
make html
```

## Contributing

We welcome contributions! See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines.

Key areas for contribution:
- New benchmark tasks
- Additional evaluation metrics
- Improved anti-gaming measures
- Visualization tools
- Documentation improvements

## License

MIT License - see [LICENSE](../../LICENSE) for details.

## Support

- Documentation: https://docs.agenttrace.dev/benchmark
- Issues: https://github.com/artbyoscar/agenttrace/issues
- Discussions: https://github.com/artbyoscar/agenttrace/discussions

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**Built with ❤️ by the AgentTrace team**
