"""
Basic Usage Example for AgentTrace Benchmark

This script demonstrates how to:
1. Load or create benchmark tasks
2. Run an agent on tasks
3. Score the results
4. Generate a comprehensive report
"""

from agenttrace_benchmark import (
    BenchmarkTask,
    BenchmarkCategory,
    ScoringEngine,
    TaskSuite,
)
from example_tasks import get_example_tasks


def mock_agent(prompt: str) -> tuple[str, float, int, int]:
    """
    Mock agent for demonstration purposes.

    In practice, replace this with your actual agent implementation.

    Args:
        prompt: Task prompt

    Returns:
        Tuple of (output, execution_time, tokens_used, tool_calls)
    """
    # Simulated agent response
    output = "This is a mock agent response."
    execution_time = 5.2  # seconds
    tokens_used = 150
    tool_calls = 0

    return output, execution_time, tokens_used, tool_calls


def evaluate_single_task():
    """Example: Evaluate a single task."""
    print("=" * 80)
    print("Example 1: Single Task Evaluation")
    print("=" * 80)

    # Get example tasks
    tasks = get_example_tasks()
    reasoning_task = tasks[0]  # Knights and Knaves puzzle

    print(f"\nTask: {reasoning_task.name}")
    print(f"Category: {reasoning_task.category.value}")
    print(f"Difficulty: {reasoning_task.difficulty.value}")
    print(f"\nPrompt:\n{reasoning_task.prompt[:200]}...\n")

    # Run agent
    output, exec_time, tokens, tool_calls = mock_agent(reasoning_task.prompt)

    print(f"Agent completed in {exec_time:.1f}s using {tokens} tokens")

    # Score the task
    engine = ScoringEngine()
    score = engine.score_task(
        task=reasoning_task,
        agent_output=output,
        execution_time=exec_time,
        tokens_used=tokens,
        tool_calls=tool_calls,
    )

    print(f"\nResults:")
    print(f"  Raw Score: {score.raw_score:.1f}/100")
    print(f"  Normalized Score: {score.normalized_score:.1f}/100")
    print(f"  Success: {score.success}")
    print(f"  Time: {score.execution_time_seconds:.1f}s / {reasoning_task.time_limit_seconds}s")
    print(f"  Tokens: {score.tokens_used} / {reasoning_task.token_budget}")


def evaluate_category():
    """Example: Evaluate all tasks in a category."""
    print("\n" + "=" * 80)
    print("Example 2: Category Evaluation")
    print("=" * 80)

    # Get all reasoning tasks (in this case, just one example)
    tasks = get_example_tasks()
    reasoning_tasks = [t for t in tasks if t.category == BenchmarkCategory.REASONING]

    print(f"\nEvaluating {len(reasoning_tasks)} task(s) in REASONING category\n")

    # Evaluate each task
    engine = ScoringEngine()
    task_scores = []

    for task in reasoning_tasks:
        output, exec_time, tokens, tool_calls = mock_agent(task.prompt)
        score = engine.score_task(task, output, exec_time, tokens, tool_calls)
        task_scores.append(score)
        print(f"✓ {task.name}: {score.normalized_score:.1f}/100")

    # Compute category aggregate
    category_score = engine.compute_category_score(
        BenchmarkCategory.REASONING,
        task_scores,
    )

    print(f"\nCategory Results:")
    print(f"  Mean Score: {category_score.mean_score:.1f}/100")
    print(f"  Median Score: {category_score.median_score:.1f}/100")
    print(f"  Std Dev: {category_score.std_dev:.1f}")
    print(f"  95% CI: [{category_score.confidence_interval[0]:.1f}, "
          f"{category_score.confidence_interval[1]:.1f}]")
    print(f"  Success Rate: {category_score.n_successes}/{category_score.n_tasks} "
          f"({100*category_score.n_successes/category_score.n_tasks:.0f}%)")


def evaluate_full_benchmark():
    """Example: Evaluate complete benchmark suite."""
    print("\n" + "=" * 80)
    print("Example 3: Full Benchmark Evaluation")
    print("=" * 80)

    tasks = get_example_tasks()
    print(f"\nEvaluating {len(tasks)} tasks across all categories\n")

    # Group tasks by category
    tasks_by_category = {}
    for task in tasks:
        if task.category not in tasks_by_category:
            tasks_by_category[task.category] = []
        tasks_by_category[task.category].append(task)

    # Evaluate each category
    engine = ScoringEngine()
    category_scores = {}

    for category, category_tasks in tasks_by_category.items():
        print(f"\n{category.value.upper()}:")

        task_scores = []
        for task in category_tasks:
            output, exec_time, tokens, tool_calls = mock_agent(task.prompt)
            score = engine.score_task(task, output, exec_time, tokens, tool_calls)
            task_scores.append(score)
            print(f"  ✓ {task.name}: {score.normalized_score:.1f}/100")

        cat_score = engine.compute_category_score(category, task_scores)
        category_scores[category] = cat_score

    # Compute composite score
    composite = engine.compute_composite_score(
        category_scores,
        agent_name="MockAgent",
        agent_version="1.0.0",
    )

    # Print comprehensive report
    print("\n" + "=" * 80)
    print("COMPREHENSIVE BENCHMARK REPORT")
    print("=" * 80)

    print(f"\nAgent: {composite.agent_name} v{composite.agent_version}")
    print(f"Timestamp: {composite.timestamp.isoformat()}")
    print(f"Submission ID: {composite.submission_id}")

    print(f"\n{'Category':<20} {'Score':<10} {'95% CI':<25} {'Success Rate'}")
    print("-" * 80)

    for category in BenchmarkCategory:
        if category in category_scores:
            cs = category_scores[category]
            ci_str = f"[{cs.confidence_interval[0]:.1f}, {cs.confidence_interval[1]:.1f}]"
            success_rate = f"{cs.n_successes}/{cs.n_tasks}"
            print(f"{category.value:<20} {cs.mean_score:>6.1f}/100  {ci_str:<25} {success_rate}")

    print("-" * 80)
    print(f"{'OVERALL':<20} {composite.overall_score:>6.1f}/100  "
          f"[{composite.confidence_interval[0]:.1f}, {composite.confidence_interval[1]:.1f}]"
          f"{'':>5} {composite.total_successes}/{composite.total_tasks}")

    print(f"\nResource Usage:")
    print(f"  Total Time: {composite.total_time_seconds:.1f}s")
    print(f"  Total Tokens: {composite.total_tokens:,}")
    print(f"  Efficiency Score: {composite.efficiency_score:.1f}/100")

    # Recommendations
    print(f"\nPerformance Analysis:")
    sorted_categories = sorted(
        category_scores.items(),
        key=lambda x: x[1].mean_score
    )

    weakest = sorted_categories[0]
    strongest = sorted_categories[-1]

    print(f"  Strongest Category: {strongest[0].value} ({strongest[1].mean_score:.1f}/100)")
    print(f"  Weakest Category: {weakest[0].value} ({weakest[1].mean_score:.1f}/100)")

    if strongest[1].mean_score - weakest[1].mean_score > 30:
        print(f"\n  ⚠️  High variance across categories suggests specialization.")
        print(f"      Consider improving performance in {weakest[0].value}.")


def compare_two_agents():
    """Example: Statistical comparison of two agent submissions."""
    print("\n" + "=" * 80)
    print("Example 4: Comparing Two Agents")
    print("=" * 80)

    tasks = get_example_tasks()
    engine = ScoringEngine()

    # Simulate two different agents
    print("\nEvaluating Agent A...")
    category_scores_a = {}
    for category in BenchmarkCategory:
        cat_tasks = [t for t in tasks if t.category == category]
        if cat_tasks:
            task_scores = []
            for task in cat_tasks:
                # Agent A - simulated as performing slightly better
                output, exec_time, tokens, tool_calls = mock_agent(task.prompt)
                score = engine.score_task(task, output, exec_time, tokens, tool_calls)
                score.normalized_score += 5  # Simulated boost
                task_scores.append(score)
            category_scores_a[category] = engine.compute_category_score(category, task_scores)

    composite_a = engine.compute_composite_score(
        category_scores_a,
        agent_name="AgentA",
        agent_version="1.0.0",
    )

    print("\nEvaluating Agent B...")
    category_scores_b = {}
    for category in BenchmarkCategory:
        cat_tasks = [t for t in tasks if t.category == category]
        if cat_tasks:
            task_scores = []
            for task in cat_tasks:
                output, exec_time, tokens, tool_calls = mock_agent(task.prompt)
                score = engine.score_task(task, output, exec_time, tokens, tool_calls)
                task_scores.append(score)
            category_scores_b[category] = engine.compute_category_score(category, task_scores)

    composite_b = engine.compute_composite_score(
        category_scores_b,
        agent_name="AgentB",
        agent_version="1.0.0",
    )

    # Statistical comparison
    comparison = engine.compare_submissions(composite_a, composite_b)

    print(f"\n{'Metric':<30} {'Agent A':<15} {'Agent B':<15} {'Difference'}")
    print("-" * 80)
    print(f"{'Overall Score':<30} {composite_a.overall_score:>10.1f}/100  "
          f"{composite_b.overall_score:>10.1f}/100  {comparison['difference']:>+10.1f}")

    print(f"\nStatistical Analysis:")
    print(f"  Effect Size (Cohen's d): {comparison['effect_size']:.3f} ({comparison['interpretation']})")
    print(f"  p-value: {comparison['p_value']:.4f}")
    print(f"  Statistically Significant: {'Yes' if comparison['significant'] else 'No'} (α=0.05)")

    if comparison['significant']:
        winner = "Agent A" if comparison['difference'] > 0 else "Agent B"
        print(f"\n  ✓ {winner} performs significantly better.")
    else:
        print(f"\n  ✗ No significant difference detected.")


if __name__ == "__main__":
    # Run all examples
    evaluate_single_task()
    evaluate_category()
    evaluate_full_benchmark()
    compare_two_agents()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Replace mock_agent() with your actual agent implementation")
    print("  2. Load tasks from the official benchmark suite")
    print("  3. Implement task-specific evaluation logic")
    print("  4. Submit results to the AgentTrace leaderboard")
    print("\nDocumentation: https://docs.agenttrace.dev/benchmark")
