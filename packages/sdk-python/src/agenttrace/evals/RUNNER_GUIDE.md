# Evaluation Runner Guide

Comprehensive guide to using the AgentTrace evaluation runner for orchestrating evaluator execution, batch processing, and CI/CD integration.

## Overview

The `EvaluationRunner` orchestrates the execution of evaluators against traces with:

- **Parallel Execution**: Evaluators run concurrently for maximum performance
- **Batch Processing**: Evaluate multiple traces with progress tracking
- **Baseline Comparison**: Detect regressions in CI/CD pipelines
- **Error Handling**: Graceful degradation with configurable error policies
- **Concurrency Control**: Semaphore-based rate limiting
- **Weighted Scoring**: Customize importance of different evaluators
- **Required Evaluators**: Mark critical evaluators that must pass

## Quick Start

### Basic Single Trace Evaluation

```python
from agenttrace.evals import EvaluationRunner
from agenttrace.evals.base import Trace

# Create runner with evaluators
runner = EvaluationRunner(
    evaluators=["response_completeness", "latency", "token_efficiency"]
)

# Evaluate a single trace
trace = Trace(trace_id="trace-123", spans=[...])
result = await runner.evaluate_trace(trace)

print(f"Overall Score: {result.overall_score:.2f}")
print(f"Passed: {result.passed}")
print(f"Duration: {result.duration_ms}ms")

# Access individual results
for eval_result in result.results:
    print(f"{eval_result.evaluator_name}: {eval_result.scores}")
```

### Batch Evaluation

```python
# Evaluate multiple traces
traces = [
    Trace(trace_id="trace-1", spans=[...]),
    Trace(trace_id="trace-2", spans=[...]),
    Trace(trace_id="trace-3", spans=[...]),
]

batch = await runner.evaluate_batch(traces)

print(f"Pass Rate: {batch.summary.pass_rate:.1%}")
print(f"Average Scores: {batch.summary.average_scores}")
print(f"Total Duration: {batch.duration_seconds:.2f}s")
```

### With Progress Tracking

```python
def progress_callback(completed, total):
    print(f"Progress: {completed}/{total} ({completed/total:.1%})")

batch = await runner.evaluate_batch(
    traces,
    progress_callback=progress_callback
)
```

## Configuration

### RunnerConfig

Control runner behavior with `RunnerConfig`:

```python
from agenttrace.evals import RunnerConfig, EvaluationRunner

config = RunnerConfig(
    max_concurrency=10,              # Max concurrent evaluations
    timeout_per_trace_seconds=60,    # Timeout per trace
    continue_on_error=True,          # Continue batch on errors
    required_evaluators=[            # Evaluators that must pass
        "response_completeness",
        "pii_detection"
    ],
    score_weights={                  # Custom scoring weights
        "completeness": 2.0,         # Double weight
        "relevance": 1.5,
        "latency": 1.0
    }
)

runner = EvaluationRunner(
    evaluators=["completeness", "relevance", "latency"],
    config=config
)
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `max_concurrency` | 10 | Maximum concurrent evaluations |
| `timeout_per_trace_seconds` | 60 | Timeout for single trace evaluation |
| `continue_on_error` | True | Continue batch processing on errors |
| `required_evaluators` | [] | List of evaluator names that must pass |
| `score_weights` | None | Optional weights for score aggregation |

## Single Trace Evaluation

### Basic Usage

```python
result = await runner.evaluate_trace(trace)

# Access results
print(f"Trace ID: {result.trace_id}")
print(f"Overall Score: {result.overall_score}")
print(f"Passed: {result.passed}")
print(f"Duration: {result.duration_ms}ms")

# Get specific evaluator result
completeness_result = result.get_result("response_completeness")
if completeness_result:
    print(f"Completeness: {completeness_result.scores['completeness'].value}")

# Get all scores
all_scores = result.get_scores()
print(f"All Scores: {all_scores}")
```

### Override Evaluators Per Trace

```python
# Use only specific evaluators for this trace
result = await runner.evaluate_trace(
    trace,
    evaluators=["response_completeness", "latency"]
)
```

### Error Handling

```python
result = await runner.evaluate_trace(trace)

if result.errors:
    print(f"Errors encountered: {len(result.errors)}")
    for error in result.errors:
        print(f"  {error['evaluator']}: {error['error']}")

# Even with errors, successful evaluations are included
print(f"Successful evaluations: {len(result.results)}")
```

## Batch Evaluation

### Basic Batch Processing

```python
traces = load_traces()  # Your trace loading logic

batch = await runner.evaluate_batch(traces)

# Summary statistics
summary = batch.summary
print(f"Total Traces: {summary.total_traces}")
print(f"Passed: {summary.passed_traces}")
print(f"Failed: {summary.failed_traces}")
print(f"Errors: {summary.error_traces}")
print(f"Pass Rate: {summary.pass_rate:.1%}")
```

### Progress Callbacks

```python
from rich.progress import Progress, TaskID

# Using rich for progress bars
with Progress() as progress:
    task = progress.add_task("[green]Evaluating...", total=len(traces))

    def callback(completed, total):
        progress.update(task, completed=completed)

    batch = await runner.evaluate_batch(
        traces,
        progress_callback=callback
    )
```

### Simple Progress Function

```python
def simple_progress(completed, total):
    percent = (completed / total) * 100
    print(f"Progress: {completed}/{total} ({percent:.1f}%)", end="\r")

batch = await runner.evaluate_batch(
    traces,
    progress_callback=simple_progress
)
print()  # New line after progress
```

### Error Handling in Batches

```python
# Continue on errors (default)
config = RunnerConfig(continue_on_error=True)
runner = EvaluationRunner(evaluators=[...], config=config)

batch = await runner.evaluate_batch(traces)

# Check for error traces
if batch.summary.error_traces > 0:
    print(f"Warning: {batch.summary.error_traces} traces had errors")

    # Find error traces
    for evaluation in batch.evaluations:
        if evaluation.errors:
            print(f"Trace {evaluation.trace_id} errors:")
            for error in evaluation.errors:
                print(f"  - {error}")
```

```python
# Stop on first error
config = RunnerConfig(continue_on_error=False)
runner = EvaluationRunner(evaluators=[...], config=config)

try:
    batch = await runner.evaluate_batch(traces)
except Exception as e:
    print(f"Batch failed: {e}")
```

### Accessing Batch Results

```python
batch = await runner.evaluate_batch(traces)

# Get specific trace evaluation
trace_eval = batch.get_evaluation("trace-123")
if trace_eval:
    print(f"Score: {trace_eval.overall_score}")

# Iterate all evaluations
for evaluation in batch.evaluations:
    print(f"{evaluation.trace_id}: {evaluation.overall_score:.2f}")

# Score distributions
for score_name, distribution in batch.summary.score_distributions.items():
    import statistics
    print(f"{score_name}:")
    print(f"  Mean: {statistics.mean(distribution):.2f}")
    print(f"  StdDev: {statistics.stdev(distribution):.2f}")
```

## Baseline Comparison

Perfect for CI/CD pipelines to detect regressions.

### Basic Comparison

```python
# Evaluate baseline (e.g., main branch)
baseline_traces = load_traces("main")
baseline = await runner.evaluate_batch(baseline_traces)

# Evaluate current (e.g., PR branch)
current_traces = load_traces("pr-branch")
current = await runner.evaluate_batch(current_traces)

# Compare
comparison = await runner.compare_to_baseline(
    current=current,
    baseline=baseline,
    regression_threshold=0.05  # 5% threshold
)
```

### Handling Comparison Results

```python
# Check for regressions
if comparison.has_regressions:
    print(f"🔴 Found {len(comparison.regressions)} regressions!")

    for regression in comparison.regressions:
        print(f"\nRegression in {regression.evaluator}:")
        print(f"  Trace: {regression.trace_id}")
        print(f"  Score: {regression.baseline_score:.2f} → {regression.current_score:.2f}")
        print(f"  Change: {regression.delta:.2f} ({regression.percent_change:.1f}%)")
else:
    print("✅ No regressions detected")

# Check for improvements
if comparison.improvements:
    print(f"\n🎉 Found {len(comparison.improvements)} improvements!")

    for improvement in comparison.improvements:
        print(f"\nImprovement in {improvement.evaluator}:")
        print(f"  Trace: {improvement.trace_id}")
        print(f"  Score: {improvement.baseline_score:.2f} → {improvement.current_score:.2f}")
        print(f"  Change: +{improvement.delta:.2f} (+{improvement.percent_change:.1f}%)")
```

### Statistical Summary

```python
stats = comparison.statistical_summary

print(f"Regressions: {stats['regression_count']}")
print(f"Improvements: {stats['improvement_count']}")
print(f"Mean Score Change: {stats['mean_score_change']:.3f}")
print(f"Pass Rate Change: {stats['pass_rate_change']:.1%}")
```

### CI/CD Integration

```python
# GitHub Actions / GitLab CI example
import sys

async def ci_check():
    baseline = await runner.evaluate_batch(baseline_traces)
    current = await runner.evaluate_batch(current_traces)

    comparison = await runner.compare_to_baseline(current, baseline)

    if comparison.has_regressions:
        print("❌ CI Check Failed: Regressions detected")

        # Print details
        for reg in comparison.regressions:
            print(f"  - {reg.evaluator} regressed by {reg.percent_change:.1f}%")

        sys.exit(1)  # Fail CI
    else:
        print("✅ CI Check Passed: No regressions")
        sys.exit(0)

# Run
import asyncio
asyncio.run(ci_check())
```

## Advanced Usage

### Weighted Scoring

Give more importance to critical evaluators:

```python
config = RunnerConfig(
    score_weights={
        "response_completeness": 3.0,    # 3x weight
        "factual_accuracy": 3.0,         # 3x weight
        "pii_detection": 2.0,            # 2x weight
        "latency": 1.0,                  # 1x weight
        "token_efficiency": 1.0          # 1x weight
    }
)

runner = EvaluationRunner(
    evaluators=["response_completeness", "factual_accuracy",
                "pii_detection", "latency", "token_efficiency"],
    config=config
)

result = await runner.evaluate_trace(trace)

# Overall score is weighted average
# (3*completeness + 3*accuracy + 2*pii + 1*latency + 1*efficiency) / 10
print(f"Weighted Score: {result.overall_score:.2f}")
```

### Required Evaluators

Mark evaluators that must pass:

```python
config = RunnerConfig(
    required_evaluators=[
        "pii_detection",        # Must not leak PII
        "harmful_content",      # Must not be harmful
        "factual_accuracy"      # Must be factually correct
    ]
)

runner = EvaluationRunner(evaluators=[...], config=config)

result = await runner.evaluate_trace(trace)

# result.passed is False if any required evaluator fails
if not result.passed:
    print("❌ Trace failed required evaluators")

    # Check which required evaluator failed
    for req_eval in config.required_evaluators:
        eval_result = result.get_result(req_eval)
        if eval_result and not eval_result.all_passed():
            print(f"  Failed: {req_eval}")
```

### Concurrency Control

Limit concurrent evaluations to avoid overwhelming LLM APIs:

```python
# Conservative - 5 concurrent
config = RunnerConfig(max_concurrency=5)

# Aggressive - 20 concurrent
config = RunnerConfig(max_concurrency=20)

runner = EvaluationRunner(evaluators=[...], config=config)

# The semaphore ensures we never exceed max_concurrency
batch = await runner.evaluate_batch(large_trace_list)
```

### Timeout Configuration

```python
# Shorter timeout for fast evaluations
config = RunnerConfig(timeout_per_trace_seconds=30)

# Longer timeout for complex evaluations
config = RunnerConfig(timeout_per_trace_seconds=300)  # 5 minutes

runner = EvaluationRunner(evaluators=[...], config=config)
```

### Using Evaluator Instances

```python
from agenttrace.evals.evaluators import ResponseCompletenessEvaluator
from agenttrace.evals.judge import JudgeConfig, get_default_config

# Configure custom evaluators
judge_config = get_default_config("fast")
completeness = ResponseCompletenessEvaluator(config=judge_config, threshold=0.8)

# Pass instances directly
runner = EvaluationRunner(
    evaluators=[completeness, "latency", "token_efficiency"]
)
```

### Using All Registered Evaluators

```python
# Use all evaluators in registry
runner = EvaluationRunner()  # evaluators=None means all

result = await runner.evaluate_trace(trace)
```

## Result Serialization

### Convert to Dictionary

```python
result = await runner.evaluate_trace(trace)

# Serialize trace evaluation
data = result.to_dict()

# Save to JSON
import json
with open("evaluation.json", "w") as f:
    json.dump(data, f, indent=2)
```

### Batch Serialization

```python
batch = await runner.evaluate_batch(traces)

# Serialize entire batch
data = batch.to_dict()

# Save results
import json
with open("batch_results.json", "w") as f:
    json.dump(data, f, indent=2)
```

### Comparison Serialization

```python
comparison = await runner.compare_to_baseline(current, baseline)

# Serialize comparison
data = comparison.to_dict()

# Generate report
with open("regression_report.json", "w") as f:
    json.dump(data, f, indent=2)
```

## Best Practices

### 1. Choose Appropriate Concurrency

```python
# For local testing - lower concurrency
local_config = RunnerConfig(max_concurrency=3)

# For production - higher concurrency
prod_config = RunnerConfig(max_concurrency=15)
```

### 2. Use Progress Callbacks for Long Batches

```python
# Always use progress callbacks for batches > 10 traces
if len(traces) > 10:
    batch = await runner.evaluate_batch(
        traces,
        progress_callback=lambda c, t: print(f"{c}/{t}")
    )
```

### 3. Set Required Evaluators for Critical Checks

```python
# Safety-critical evaluators should be required
config = RunnerConfig(
    required_evaluators=["pii_detection", "harmful_content"]
)
```

### 4. Weight Important Evaluators Higher

```python
# Prioritize accuracy and safety over efficiency
config = RunnerConfig(
    score_weights={
        "factual_accuracy": 3.0,
        "pii_detection": 3.0,
        "completeness": 2.0,
        "latency": 1.0
    }
)
```

### 5. Use Baseline Comparison in CI/CD

```python
# Always compare against baseline in CI
comparison = await runner.compare_to_baseline(
    current=pr_results,
    baseline=main_results,
    regression_threshold=0.03  # 3% threshold
)

if comparison.has_regressions:
    sys.exit(1)  # Fail CI
```

### 6. Handle Errors Gracefully

```python
# For exploratory analysis - continue on errors
explore_config = RunnerConfig(continue_on_error=True)

# For production validation - stop on errors
prod_config = RunnerConfig(continue_on_error=False)
```

## Complete Examples

### Example 1: Development Testing

```python
from agenttrace.evals import EvaluationRunner, RunnerConfig

async def test_my_agent():
    """Quick test during development."""

    config = RunnerConfig(
        max_concurrency=3,  # Don't overwhelm API during dev
        required_evaluators=["pii_detection"]
    )

    runner = EvaluationRunner(
        evaluators=["response_completeness", "pii_detection", "latency"],
        config=config
    )

    # Test single trace
    trace = create_trace_from_agent_run()
    result = await runner.evaluate_trace(trace)

    print(f"Score: {result.overall_score:.2f}")
    print(f"Passed: {result.passed}")

    if not result.passed:
        print("Fix required evaluators before deploying!")

import asyncio
asyncio.run(test_my_agent())
```

### Example 2: Batch Analysis

```python
async def analyze_production_traces():
    """Analyze batch of production traces."""

    runner = EvaluationRunner(
        evaluators=[
            "response_completeness",
            "response_relevance",
            "latency",
            "token_efficiency",
            "trajectory_optimality"
        ]
    )

    traces = load_production_traces(limit=100)

    def progress(completed, total):
        print(f"Analyzed: {completed}/{total} ({completed/total:.0%})", end="\r")

    batch = await runner.evaluate_batch(traces, progress_callback=progress)
    print()  # New line

    # Generate report
    summary = batch.summary
    print(f"\n📊 Analysis Report")
    print(f"Pass Rate: {summary.pass_rate:.1%}")
    print(f"\nAverage Scores:")
    for name, score in summary.average_scores.items():
        print(f"  {name}: {score:.2f}")

    # Find problematic traces
    failed_traces = [e for e in batch.evaluations if not e.passed]
    print(f"\n❌ Failed Traces: {len(failed_traces)}")
    for trace_eval in failed_traces[:5]:  # Show first 5
        print(f"  - {trace_eval.trace_id}: {trace_eval.overall_score:.2f}")

asyncio.run(analyze_production_traces())
```

### Example 3: CI/CD Pipeline

```python
#!/usr/bin/env python3
"""
CI/CD evaluation script.
Usage: python ci_eval.py --baseline=main --current=pr-123
"""

import sys
import asyncio
from agenttrace.evals import EvaluationRunner, RunnerConfig

async def ci_evaluation_check(baseline_traces, current_traces):
    """Run evaluation comparison for CI/CD."""

    config = RunnerConfig(
        max_concurrency=10,
        timeout_per_trace_seconds=120,
        required_evaluators=[
            "pii_detection",
            "harmful_content",
            "factual_accuracy"
        ],
        score_weights={
            "factual_accuracy": 3.0,
            "response_completeness": 2.0,
            "response_relevance": 2.0,
            "latency": 1.0
        }
    )

    runner = EvaluationRunner(
        evaluators=[
            "response_completeness",
            "response_relevance",
            "factual_accuracy",
            "pii_detection",
            "harmful_content",
            "latency",
            "token_efficiency"
        ],
        config=config
    )

    print("🔄 Evaluating baseline...")
    baseline = await runner.evaluate_batch(baseline_traces)

    print("🔄 Evaluating current...")
    current = await runner.evaluate_batch(current_traces)

    print("🔍 Comparing to baseline...")
    comparison = await runner.compare_to_baseline(
        current=current,
        baseline=baseline,
        regression_threshold=0.05  # 5% regression threshold
    )

    # Print results
    print("\n" + "="*60)
    print("📊 EVALUATION RESULTS")
    print("="*60)

    stats = comparison.statistical_summary
    print(f"\nPass Rate: {current.summary.pass_rate:.1%} (baseline: {baseline.summary.pass_rate:.1%})")
    print(f"Mean Score Change: {stats['mean_score_change']:+.3f}")

    if comparison.regressions:
        print(f"\n❌ REGRESSIONS DETECTED: {len(comparison.regressions)}")
        for reg in comparison.regressions[:10]:  # Show first 10
            print(f"  - {reg.evaluator} [{reg.trace_id}]: "
                  f"{reg.baseline_score:.2f} → {reg.current_score:.2f} "
                  f"({reg.percent_change:+.1f}%)")

        print("\n🚫 CI Check FAILED")
        return False

    if comparison.improvements:
        print(f"\n✨ IMPROVEMENTS DETECTED: {len(comparison.improvements)}")
        for imp in comparison.improvements[:5]:  # Show first 5
            print(f"  + {imp.evaluator} [{imp.trace_id}]: "
                  f"{imp.baseline_score:.2f} → {imp.current_score:.2f} "
                  f"(+{imp.percent_change:.1f}%)")

    print("\n✅ CI Check PASSED")
    return True

if __name__ == "__main__":
    baseline = load_traces("baseline")
    current = load_traces("current")

    passed = asyncio.run(ci_evaluation_check(baseline, current))
    sys.exit(0 if passed else 1)
```

## Troubleshooting

### Timeouts

```python
# If evaluations are timing out
config = RunnerConfig(
    timeout_per_trace_seconds=300,  # Increase timeout
    max_concurrency=5                # Reduce concurrency
)
```

### Rate Limits

```python
# If hitting LLM API rate limits
config = RunnerConfig(
    max_concurrency=3  # Reduce concurrent requests
)
```

### Memory Issues

```python
# For very large batches, process in chunks
async def process_large_batch(all_traces, chunk_size=50):
    all_results = []

    for i in range(0, len(all_traces), chunk_size):
        chunk = all_traces[i:i+chunk_size]
        batch = await runner.evaluate_batch(chunk)
        all_results.extend(batch.evaluations)

    return all_results
```

## Integration with Judge Infrastructure

The runner works seamlessly with the LLM-as-judge infrastructure:

```python
from agenttrace.evals.judge import JudgeConfig, get_default_config
from agenttrace.evals.evaluators import ResponseCompletenessEvaluator

# Configure judge
judge_config = get_default_config("balanced")  # gpt-4o

# Create evaluators with custom judge config
completeness = ResponseCompletenessEvaluator(config=judge_config)

# Use in runner
runner = EvaluationRunner(evaluators=[completeness])
```

## Summary

The evaluation runner provides a robust, production-ready system for:

- ✅ Orchestrating evaluator execution with parallel processing
- ✅ Batch evaluation with progress tracking
- ✅ Baseline comparison for detecting regressions
- ✅ Configurable error handling and timeouts
- ✅ Weighted scoring and required evaluators
- ✅ Full serialization for reporting

Perfect for development testing, production monitoring, and CI/CD integration.
