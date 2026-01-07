"""Example usage of the AgentTrace evaluation framework."""

import asyncio
from agenttrace.evals import (
    Evaluator,
    EvalResult,
    EvalScore,
    EvalSummary,
    Trace,
    register_evaluator,
    get_registry,
)


# Example 1: Class-based evaluator
class CompletenessEvaluator(Evaluator):
    """Evaluates if a trace contains all required spans."""

    @property
    def name(self) -> str:
        return "completeness"

    @property
    def description(self) -> str:
        return "Checks if trace contains all required span types"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate trace completeness."""
        required_spans = ["llm_call", "tool_use", "response"]
        present_spans = {span["name"] for span in trace.spans}

        completeness = len(present_spans.intersection(required_spans)) / len(required_spans)

        score = EvalScore(
            name="completeness",
            value=completeness,
            threshold=0.8,
        )

        feedback = f"Found {len(present_spans)} of {len(required_spans)} required spans"

        return EvalResult(
            evaluator_name=self.name,
            scores={"completeness": score},
            feedback=feedback,
            metadata={"required_spans": required_spans, "present_spans": list(present_spans)},
        )


# Example 2: Function-based evaluator with decorator
@register_evaluator(
    name="latency",
    description="Evaluates trace latency performance",
)
async def evaluate_latency(trace: Trace) -> EvalResult:
    """Check if trace completed within acceptable time."""
    root_span = trace.get_root_span()

    if not root_span or root_span.get("duration") is None:
        score = EvalScore(name="latency", value=0.0)
        return EvalResult(
            evaluator_name="latency",
            scores={"latency": score},
            feedback="No root span or duration found",
        )

    duration = root_span["duration"]
    max_duration = 5.0  # 5 seconds

    # Normalize score: 0.0 at max_duration, 1.0 at instant
    latency_score = max(0.0, 1.0 - (duration / max_duration))

    score = EvalScore(
        name="latency",
        value=latency_score,
        threshold=0.7,
    )

    feedback = f"Trace completed in {duration:.2f}s"

    return EvalResult(
        evaluator_name="latency",
        scores={"latency": score},
        feedback=feedback,
        metadata={"duration_seconds": duration, "max_duration": max_duration},
    )


# Example 3: Using multiple evaluators
async def main():
    """Demonstrate evaluation framework usage."""

    # Create a sample trace
    trace = Trace(
        trace_id="trace-123",
        spans=[
            {
                "span_id": "1",
                "name": "llm_call",
                "parent_id": None,
                "duration": 2.5,
                "status": "completed",
            },
            {
                "span_id": "2",
                "name": "tool_use",
                "parent_id": "1",
                "duration": 1.0,
                "status": "completed",
            },
            {
                "span_id": "3",
                "name": "response",
                "parent_id": "1",
                "duration": 0.5,
                "status": "completed",
            },
        ],
        metadata={"user_id": "user-123"},
        tags=["production"],
    )

    # Register class-based evaluator
    registry = get_registry()
    completeness_eval = CompletenessEvaluator()
    registry.register(completeness_eval)

    # Get all registered evaluators
    all_evaluators = registry.get_all()
    print(f"\nRegistered evaluators: {list(all_evaluators.keys())}\n")

    # Run evaluations
    results = []
    for name, evaluator in all_evaluators.items():
        print(f"Running {name}...")
        result = await evaluator.evaluate(trace)
        results.append(result)

        # Print individual result
        print(f"  Evaluator: {result.evaluator_name}")
        print(f"  Feedback: {result.feedback}")
        for score_name, score in result.scores.items():
            print(f"  {score_name}: {score.value:.2f} (passed: {score.passed})")
        print()

    # Create summary
    summary = EvalSummary(results=results)

    print("\n" + "=" * 50)
    print("EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Total evaluators: {summary.total_evaluators}")
    print(f"Passed: {summary.passed_evaluators}")
    print(f"Failed: {summary.failed_evaluators}")
    print(f"Pass rate: {summary.pass_rate:.1%}")
    print(f"\nAverage scores:")
    for score_name, avg_value in summary.average_scores.items():
        print(f"  {score_name}: {avg_value:.2f}")

    # Show failed evaluations
    if summary.failed_evaluators > 0:
        print("\nFailed evaluations:")
        for failed_result in summary.get_failed_results():
            print(f"  - {failed_result.evaluator_name}: {failed_result.feedback}")


if __name__ == "__main__":
    asyncio.run(main())
