"""Efficiency evaluators for assessing agent performance and resource usage."""

from typing import Optional, Dict, List
import statistics
from ..base import Evaluator, Trace, register_evaluator
from ..models import EvalResult, EvalScore


@register_evaluator()
class TokenEfficiencyEvaluator(Evaluator):
    """Compares token usage against baseline for similar tasks.

    Flags excessive token consumption and calculates efficiency ratio.

    Example:
        >>> evaluator = TokenEfficiencyEvaluator(baseline_tokens=1000)
        >>> result = await evaluator.evaluate(trace)
        >>> if result.scores["efficiency_ratio"].value < 0.5:
        ...     print("Token usage is inefficient")
    """

    def __init__(
        self,
        baseline_tokens: int = 1000,
        threshold: float = 0.7,
        max_acceptable_ratio: float = 1.5,
    ):
        """Initialize the evaluator.

        Args:
            baseline_tokens: Expected token count for similar tasks
            threshold: Minimum efficiency score to pass
            max_acceptable_ratio: Maximum acceptable ratio vs baseline (1.5 = 150%)
        """
        self._baseline_tokens = baseline_tokens
        self._threshold = threshold
        self._max_acceptable_ratio = max_acceptable_ratio

    @property
    def name(self) -> str:
        return "token_efficiency"

    @property
    def description(self) -> str:
        return "Compares token usage against baseline to detect inefficiency"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate token efficiency.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with efficiency ratio and token usage details
        """
        # Count tokens from all spans
        total_tokens = 0
        llm_spans = []

        for span in trace.spans:
            metadata = span.get("metadata", {})
            span_tokens = metadata.get("tokens", 0)
            total_tokens += span_tokens

            # Track LLM-specific spans
            if "llm" in span.get("name", "").lower() or span_tokens > 0:
                llm_spans.append(
                    {
                        "name": span.get("name"),
                        "tokens": span_tokens,
                        "prompt_tokens": metadata.get("prompt_tokens", 0),
                        "completion_tokens": metadata.get("completion_tokens", 0),
                    }
                )

        if total_tokens == 0:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "efficiency_ratio": EvalScore(
                        name="efficiency_ratio",
                        value=1.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No token usage found in trace",
                metadata={"total_tokens": 0},
            )

        # Calculate efficiency ratio
        # Higher ratio means more efficient (using fewer tokens than baseline)
        # If actual < baseline: ratio > 1.0 (efficient)
        # If actual > baseline: ratio < 1.0 (inefficient)
        actual_ratio = total_tokens / self._baseline_tokens

        # Convert to efficiency score (0.0-1.0)
        # Perfect efficiency (1.0) = at or below baseline
        # Poor efficiency (0.0) = at max_acceptable_ratio or higher
        if actual_ratio <= 1.0:
            efficiency_score = 1.0
        elif actual_ratio >= self._max_acceptable_ratio:
            efficiency_score = 0.0
        else:
            # Linear interpolation between 1.0 and max_acceptable_ratio
            efficiency_score = 1.0 - (
                (actual_ratio - 1.0) / (self._max_acceptable_ratio - 1.0)
            )

        score = EvalScore(
            name="efficiency_ratio",
            value=efficiency_score,
            threshold=self._threshold,
        )

        # Build feedback
        if actual_ratio <= 1.0:
            feedback = f"Efficient token usage: {total_tokens} tokens (baseline: {self._baseline_tokens})"
        else:
            excess_pct = (actual_ratio - 1.0) * 100
            feedback = f"Excessive token usage: {total_tokens} tokens ({excess_pct:.1f}% over baseline of {self._baseline_tokens})"

        return EvalResult(
            evaluator_name=self.name,
            scores={"efficiency_ratio": score},
            feedback=feedback,
            metadata={
                "total_tokens": total_tokens,
                "baseline_tokens": self._baseline_tokens,
                "actual_ratio": actual_ratio,
                "llm_spans": llm_spans,
            },
        )


@register_evaluator()
class LatencyEvaluator(Evaluator):
    """Measures total execution time against configurable thresholds.

    Provides p50, p95, p99 latency scores and supports per-span-type thresholds.

    Example:
        >>> thresholds = {"p50": 1.0, "p95": 3.0, "p99": 5.0}
        >>> evaluator = LatencyEvaluator(latency_thresholds=thresholds)
        >>> result = await evaluator.evaluate(trace)
    """

    def __init__(
        self,
        latency_thresholds: Optional[Dict[str, float]] = None,
        threshold: float = 0.8,
        span_type_thresholds: Optional[Dict[str, float]] = None,
    ):
        """Initialize the evaluator.

        Args:
            latency_thresholds: Max acceptable latencies for p50/p95/p99 in seconds
            threshold: Minimum score to pass
            span_type_thresholds: Max latency per span type (e.g., {"llm_call": 2.0})
        """
        self._latency_thresholds = latency_thresholds or {
            "p50": 2.0,
            "p95": 5.0,
            "p99": 10.0,
        }
        self._threshold = threshold
        self._span_type_thresholds = span_type_thresholds or {}

    @property
    def name(self) -> str:
        return "latency"

    @property
    def description(self) -> str:
        return "Measures execution time against configurable latency thresholds"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate latency performance.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with latency scores and percentile breakdown
        """
        # Get total duration from root span
        root_span = trace.get_root_span()
        if not root_span or root_span.get("duration") is None:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "latency": EvalScore(
                        name="latency",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No root span or duration found",
            )

        total_duration = root_span.get("duration", 0)

        # Collect all span durations for percentile analysis
        durations = [
            span.get("duration", 0)
            for span in trace.spans
            if span.get("duration") is not None and span.get("duration") > 0
        ]

        if not durations:
            durations = [total_duration]

        # Calculate percentiles
        sorted_durations = sorted(durations)
        n = len(sorted_durations)

        p50 = sorted_durations[int(n * 0.5)] if n > 0 else 0
        p95 = sorted_durations[int(n * 0.95)] if n > 0 else 0
        p99 = sorted_durations[int(n * 0.99)] if n > 0 else 0

        # Calculate scores for each percentile
        scores = {}
        for percentile, actual_latency in [
            ("p50", p50),
            ("p95", p95),
            ("p99", p99),
        ]:
            threshold_latency = self._latency_thresholds.get(percentile, 5.0)

            # Score: 1.0 if at or below threshold, decreasing linearly to 0.0 at 2x threshold
            if actual_latency <= threshold_latency:
                score_value = 1.0
            elif actual_latency >= threshold_latency * 2:
                score_value = 0.0
            else:
                score_value = 1.0 - (
                    (actual_latency - threshold_latency) / threshold_latency
                )

            scores[percentile] = EvalScore(
                name=percentile,
                value=score_value,
                threshold=self._threshold,
            )

        # Overall latency score (average of percentile scores)
        avg_score = statistics.mean([s.value for s in scores.values()])
        scores["latency"] = EvalScore(
            name="latency",
            value=avg_score,
            threshold=self._threshold,
        )

        # Check span type thresholds
        slow_spans = []
        for span in trace.spans:
            span_name = span.get("name", "")
            span_duration = span.get("duration", 0)

            if span_name in self._span_type_thresholds:
                if span_duration > self._span_type_thresholds[span_name]:
                    slow_spans.append(
                        {
                            "name": span_name,
                            "duration": span_duration,
                            "threshold": self._span_type_thresholds[span_name],
                        }
                    )

        feedback = f"Total duration: {total_duration:.2f}s (p50: {p50:.2f}s, p95: {p95:.2f}s, p99: {p99:.2f}s)"
        if slow_spans:
            feedback += f"\n{len(slow_spans)} span(s) exceeded type-specific thresholds"

        return EvalResult(
            evaluator_name=self.name,
            scores=scores,
            feedback=feedback,
            metadata={
                "total_duration": total_duration,
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "thresholds": self._latency_thresholds,
                "slow_spans": slow_spans,
            },
        )


@register_evaluator()
class TrajectoryOptimalityEvaluator(Evaluator):
    """Analyzes if agent took optimal path to goal.

    Identifies redundant steps, loops, and inefficient trajectories.

    Example:
        >>> evaluator = TrajectoryOptimalityEvaluator()
        >>> result = await evaluator.evaluate(trace)
        >>> if result.metadata["redundant_steps"] > 0:
        ...     print("Agent took redundant steps")
    """

    def __init__(self, threshold: float = 0.7):
        """Initialize the evaluator.

        Args:
            threshold: Minimum optimality score to pass
        """
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "trajectory_optimality"

    @property
    def description(self) -> str:
        return "Analyzes if agent took optimal path, identifying redundant steps"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate trajectory optimality.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with optimality score and inefficiency details
        """
        if not trace.spans:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "optimality": EvalScore(
                        name="optimality",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No spans found in trace",
            )

        total_steps = len(trace.spans)

        # Detect loops (repeated span names in sequence)
        loops = self._detect_loops(trace.spans)

        # Detect redundant tool calls (same tool with same input multiple times)
        redundant_calls = self._detect_redundant_calls(trace.spans)

        # Count error/retry spans
        retries = sum(
            1
            for span in trace.spans
            if span.get("status") == "error"
            or "retry" in span.get("name", "").lower()
        )

        # Calculate inefficiency penalties
        total_inefficiencies = len(loops) + len(redundant_calls) + retries

        # Optimality score: penalize for each inefficiency
        # Perfect score (1.0) = no inefficiencies
        # Each inefficiency reduces score
        penalty_per_inefficiency = 0.1
        optimality_score = max(
            0.0, 1.0 - (total_inefficiencies * penalty_per_inefficiency)
        )

        score = EvalScore(
            name="optimality",
            value=optimality_score,
            threshold=self._threshold,
        )

        # Build feedback
        issues = []
        if loops:
            issues.append(f"{len(loops)} loop(s) detected")
        if redundant_calls:
            issues.append(f"{len(redundant_calls)} redundant call(s)")
        if retries:
            issues.append(f"{retries} retry/error span(s)")

        if issues:
            feedback = f"Trajectory inefficiencies found: {', '.join(issues)}"
        else:
            feedback = f"Optimal trajectory with {total_steps} steps"

        return EvalResult(
            evaluator_name=self.name,
            scores={"optimality": score},
            feedback=feedback,
            metadata={
                "total_steps": total_steps,
                "loops": loops,
                "redundant_calls": redundant_calls,
                "retries": retries,
                "total_inefficiencies": total_inefficiencies,
            },
        )

    def _detect_loops(self, spans: List[Dict]) -> List[Dict]:
        """Detect loops in span sequence.

        Args:
            spans: List of span dictionaries

        Returns:
            List of detected loops with details
        """
        loops = []
        span_names = [span.get("name", "") for span in spans]

        # Look for consecutive repeated patterns
        i = 0
        while i < len(span_names) - 1:
            current = span_names[i]
            # Count consecutive occurrences
            count = 1
            j = i + 1
            while j < len(span_names) and span_names[j] == current:
                count += 1
                j += 1

            if count >= 3:  # Consider 3+ repetitions as a loop
                loops.append(
                    {"span_name": current, "repetitions": count, "start_index": i}
                )
                i = j
            else:
                i += 1

        return loops

    def _detect_redundant_calls(self, spans: List[Dict]) -> List[Dict]:
        """Detect redundant tool/function calls.

        Args:
            spans: List of span dictionaries

        Returns:
            List of redundant calls with details
        """
        redundant = []
        seen_calls = {}

        for i, span in enumerate(spans):
            name = span.get("name", "")
            metadata = span.get("metadata", {})
            input_data = str(metadata.get("input", ""))

            # Create a signature for this call
            signature = f"{name}:{input_data}"

            if signature in seen_calls:
                redundant.append(
                    {
                        "span_name": name,
                        "first_occurrence": seen_calls[signature],
                        "redundant_occurrence": i,
                        "input": input_data[:100],
                    }
                )
            else:
                seen_calls[signature] = i

        return redundant
