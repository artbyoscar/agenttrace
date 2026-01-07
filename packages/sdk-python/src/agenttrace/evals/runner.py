"""Evaluation runner for orchestrating evaluator execution against traces."""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable, Union
from collections import defaultdict
import statistics

from .base import Evaluator, Trace
from .models import EvalResult, EvalScore
from .registry import get_registry


@dataclass
class RunnerConfig:
    """Configuration for evaluation runner.

    Attributes:
        max_concurrency: Maximum concurrent evaluations
        timeout_per_trace_seconds: Timeout for evaluating a single trace
        continue_on_error: Continue batch if individual evaluations fail
        required_evaluators: Evaluators that must pass for trace to pass
        score_weights: Optional weights for computing overall score

    Example:
        >>> config = RunnerConfig(
        ...     max_concurrency=5,
        ...     required_evaluators=["response_completeness"],
        ...     score_weights={"completeness": 2.0, "relevance": 1.0}
        ... )
    """

    max_concurrency: int = 10
    timeout_per_trace_seconds: int = 60
    continue_on_error: bool = True
    required_evaluators: List[str] = field(default_factory=list)
    score_weights: Optional[Dict[str, float]] = None

    def __post_init__(self):
        """Validate configuration."""
        if self.max_concurrency < 1:
            raise ValueError("max_concurrency must be at least 1")
        if self.timeout_per_trace_seconds < 1:
            raise ValueError("timeout_per_trace_seconds must be at least 1")


@dataclass
class TraceEvaluation:
    """Results from evaluating a single trace.

    Attributes:
        trace_id: Trace identifier
        results: List of evaluation results
        overall_score: Weighted average score across all evaluators
        passed: Whether all required evaluators passed
        duration_ms: Time taken to evaluate (milliseconds)
        errors: Any errors encountered during evaluation
        metadata: Additional metadata

    Example:
        >>> evaluation = TraceEvaluation(
        ...     trace_id="trace-123",
        ...     results=[result1, result2],
        ...     overall_score=0.85,
        ...     passed=True,
        ...     duration_ms=1234
        ... )
    """

    trace_id: str
    results: List[EvalResult]
    overall_score: float
    passed: bool
    duration_ms: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_result(self, evaluator_name: str) -> Optional[EvalResult]:
        """Get result for a specific evaluator.

        Args:
            evaluator_name: Name of the evaluator

        Returns:
            EvalResult or None if not found
        """
        for result in self.results:
            if result.evaluator_name == evaluator_name:
                return result
        return None

    def get_scores(self) -> Dict[str, float]:
        """Get all scores from all evaluators.

        Returns:
            Dictionary mapping score name to value
        """
        scores = {}
        for result in self.results:
            for score_name, score in result.scores.items():
                scores[score_name] = score.value
        return scores

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with all attributes
        """
        return {
            "trace_id": self.trace_id,
            "results": [r.to_dict() for r in self.results],
            "overall_score": self.overall_score,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "errors": self.errors,
            "metadata": self.metadata,
        }


@dataclass
class BatchSummary:
    """Summary statistics for a batch of evaluations.

    Attributes:
        total_traces: Total number of traces evaluated
        passed_traces: Number of traces that passed
        failed_traces: Number of traces that failed
        error_traces: Number of traces with errors
        average_scores: Average score per evaluator
        score_distributions: Distribution of scores per evaluator
        average_duration_ms: Average evaluation time

    Example:
        >>> summary = BatchSummary(
        ...     total_traces=100,
        ...     passed_traces=95,
        ...     failed_traces=5,
        ...     error_traces=0,
        ...     average_scores={"completeness": 0.85},
        ...     score_distributions={"completeness": [0.8, 0.9, ...]},
        ...     average_duration_ms=1500
        ... )
    """

    total_traces: int
    passed_traces: int
    failed_traces: int
    error_traces: int
    average_scores: Dict[str, float]
    score_distributions: Dict[str, List[float]]
    average_duration_ms: float

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate.

        Returns:
            Pass rate (0.0-1.0)
        """
        if self.total_traces == 0:
            return 0.0
        return self.passed_traces / self.total_traces

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with all attributes
        """
        return {
            "total_traces": self.total_traces,
            "passed_traces": self.passed_traces,
            "failed_traces": self.failed_traces,
            "error_traces": self.error_traces,
            "pass_rate": self.pass_rate,
            "average_scores": self.average_scores,
            "score_distributions": self.score_distributions,
            "average_duration_ms": self.average_duration_ms,
        }


@dataclass
class BatchEvaluation:
    """Results from evaluating a batch of traces.

    Attributes:
        evaluations: List of trace evaluations
        summary: Summary statistics
        started_at: When evaluation started
        completed_at: When evaluation completed
        metadata: Additional metadata

    Example:
        >>> batch = BatchEvaluation(
        ...     evaluations=[eval1, eval2, eval3],
        ...     summary=summary,
        ...     started_at=datetime.utcnow(),
        ...     completed_at=datetime.utcnow()
        ... )
    """

    evaluations: List[TraceEvaluation]
    summary: BatchSummary
    started_at: datetime
    completed_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Calculate total batch duration.

        Returns:
            Duration in seconds
        """
        delta = self.completed_at - self.started_at
        return delta.total_seconds()

    def get_evaluation(self, trace_id: str) -> Optional[TraceEvaluation]:
        """Get evaluation for a specific trace.

        Args:
            trace_id: Trace identifier

        Returns:
            TraceEvaluation or None if not found
        """
        for evaluation in self.evaluations:
            if evaluation.trace_id == trace_id:
                return evaluation
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with all attributes
        """
        return {
            "evaluations": [e.to_dict() for e in self.evaluations],
            "summary": self.summary.to_dict(),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


@dataclass
class Regression:
    """Represents a regression in evaluation scores.

    Attributes:
        evaluator: Evaluator name
        score_name: Score name
        baseline_score: Score in baseline
        current_score: Score in current run
        delta: Difference (current - baseline)
        trace_id: Affected trace ID

    Example:
        >>> regression = Regression(
        ...     evaluator="completeness",
        ...     score_name="completeness",
        ...     baseline_score=0.9,
        ...     current_score=0.7,
        ...     delta=-0.2,
        ...     trace_id="trace-123"
        ... )
    """

    evaluator: str
    score_name: str
    baseline_score: float
    current_score: float
    delta: float
    trace_id: str

    @property
    def percent_change(self) -> float:
        """Calculate percent change.

        Returns:
            Percent change from baseline
        """
        if self.baseline_score == 0:
            return 0.0
        return (self.delta / self.baseline_score) * 100


@dataclass
class Improvement:
    """Represents an improvement in evaluation scores.

    Attributes:
        evaluator: Evaluator name
        score_name: Score name
        baseline_score: Score in baseline
        current_score: Score in current run
        delta: Difference (current - baseline)
        trace_id: Affected trace ID
    """

    evaluator: str
    score_name: str
    baseline_score: float
    current_score: float
    delta: float
    trace_id: str

    @property
    def percent_change(self) -> float:
        """Calculate percent change.

        Returns:
            Percent change from baseline
        """
        if self.baseline_score == 0:
            return 0.0
        return (self.delta / self.baseline_score) * 100


@dataclass
class Comparison:
    """Comparison between two evaluation runs.

    Attributes:
        regressions: List of regressions found
        improvements: List of improvements found
        unchanged: List of unchanged evaluators
        statistical_summary: Statistical comparison summary

    Example:
        >>> comparison = Comparison(
        ...     regressions=[regression1, regression2],
        ...     improvements=[improvement1],
        ...     unchanged=["latency"],
        ...     statistical_summary={"mean_delta": -0.05}
        ... )
    """

    regressions: List[Regression]
    improvements: List[Improvement]
    unchanged: List[str]
    statistical_summary: Dict[str, Any]

    @property
    def has_regressions(self) -> bool:
        """Check if there are any regressions.

        Returns:
            True if regressions exist
        """
        return len(self.regressions) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with all attributes
        """
        return {
            "regressions": [
                {
                    "evaluator": r.evaluator,
                    "score_name": r.score_name,
                    "baseline_score": r.baseline_score,
                    "current_score": r.current_score,
                    "delta": r.delta,
                    "percent_change": r.percent_change,
                    "trace_id": r.trace_id,
                }
                for r in self.regressions
            ],
            "improvements": [
                {
                    "evaluator": i.evaluator,
                    "score_name": i.score_name,
                    "baseline_score": i.baseline_score,
                    "current_score": i.current_score,
                    "delta": i.delta,
                    "percent_change": i.percent_change,
                    "trace_id": i.trace_id,
                }
                for i in self.improvements
            ],
            "unchanged": self.unchanged,
            "statistical_summary": self.statistical_summary,
        }


class EvaluationRunner:
    """Runner for orchestrating evaluator execution against traces.

    Supports single trace evaluation, batch evaluation, and baseline comparison
    with parallel execution and error handling.

    Example:
        >>> from agenttrace.evals import EvaluationRunner, RunnerConfig
        >>>
        >>> runner = EvaluationRunner(
        ...     evaluators=["response_completeness", "latency"],
        ...     config=RunnerConfig(max_concurrency=5)
        ... )
        >>>
        >>> # Single trace
        >>> result = await runner.evaluate_trace(trace)
        >>>
        >>> # Batch
        >>> batch_result = await runner.evaluate_batch(traces)
    """

    def __init__(
        self,
        evaluators: Optional[List[Union[str, Evaluator]]] = None,
        config: Optional[RunnerConfig] = None,
    ):
        """Initialize the evaluation runner.

        Args:
            evaluators: List of evaluator names or instances (None = all registered)
            config: Runner configuration

        Example:
            >>> runner = EvaluationRunner(
            ...     evaluators=["completeness", "relevance"],
            ...     config=RunnerConfig(max_concurrency=5)
            ... )
        """
        self.config = config or RunnerConfig()
        self._evaluators = self._resolve_evaluators(evaluators)
        self._semaphore = asyncio.Semaphore(self.config.max_concurrency)

    def _resolve_evaluators(
        self, evaluators: Optional[List[Union[str, Evaluator]]]
    ) -> List[Evaluator]:
        """Resolve evaluator names/instances to evaluator instances.

        Args:
            evaluators: List of names or instances

        Returns:
            List of Evaluator instances

        Raises:
            ValueError: If evaluator not found
        """
        registry = get_registry()

        if evaluators is None:
            # Use all registered evaluators
            return list(registry.get_all().values())

        resolved = []
        for evaluator in evaluators:
            if isinstance(evaluator, str):
                # Look up by name
                instance = registry.get(evaluator)
                if instance is None:
                    raise ValueError(
                        f"Evaluator '{evaluator}' not found in registry. "
                        f"Available: {registry.list_all()}"
                    )
                resolved.append(instance)
            elif isinstance(evaluator, Evaluator):
                # Already an instance
                resolved.append(evaluator)
            else:
                raise TypeError(
                    f"Evaluator must be string or Evaluator instance, got {type(evaluator)}"
                )

        return resolved

    async def evaluate_trace(
        self,
        trace: Trace,
        evaluators: Optional[List[str]] = None,
    ) -> TraceEvaluation:
        """Evaluate a single trace with specified evaluators.

        Args:
            trace: Trace to evaluate
            evaluators: Optional list of evaluator names (None = all configured)

        Returns:
            TraceEvaluation with results

        Example:
            >>> result = await runner.evaluate_trace(trace)
            >>> print(f"Overall score: {result.overall_score:.2f}")
            >>> print(f"Passed: {result.passed}")
        """
        start_time = time.time()

        # Resolve evaluators for this trace
        if evaluators is not None:
            eval_instances = self._resolve_evaluators(evaluators)
        else:
            eval_instances = self._evaluators

        # Run evaluations in parallel
        tasks = []
        for evaluator in eval_instances:
            task = self._evaluate_with_timeout(evaluator, trace)
            tasks.append(task)

        results_or_errors = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate results and errors
        results = []
        errors = []

        for i, result_or_error in enumerate(results_or_errors):
            if isinstance(result_or_error, Exception):
                errors.append(
                    {
                        "evaluator": eval_instances[i].name,
                        "error": str(result_or_error),
                        "type": type(result_or_error).__name__,
                    }
                )
            else:
                results.append(result_or_error)

        # Calculate overall score
        overall_score = self._calculate_overall_score(results)

        # Check if trace passed
        passed = self._check_trace_passed(results, errors)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        return TraceEvaluation(
            trace_id=trace.trace_id,
            results=results,
            overall_score=overall_score,
            passed=passed,
            duration_ms=duration_ms,
            errors=errors,
        )

    async def _evaluate_with_timeout(
        self, evaluator: Evaluator, trace: Trace
    ) -> EvalResult:
        """Evaluate with timeout and concurrency control.

        Args:
            evaluator: Evaluator instance
            trace: Trace to evaluate

        Returns:
            EvalResult

        Raises:
            asyncio.TimeoutError: If evaluation times out
            Exception: If evaluation fails
        """
        async with self._semaphore:
            try:
                result = await asyncio.wait_for(
                    evaluator.evaluate(trace),
                    timeout=self.config.timeout_per_trace_seconds,
                )
                return result
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Evaluation timed out after {self.config.timeout_per_trace_seconds}s"
                )

    def _calculate_overall_score(self, results: List[EvalResult]) -> float:
        """Calculate weighted average score across all results.

        Args:
            results: List of evaluation results

        Returns:
            Overall score (0.0-1.0)
        """
        if not results:
            return 0.0

        weighted_sum = 0.0
        total_weight = 0.0

        for result in results:
            for score_name, score in result.scores.items():
                # Get weight (default 1.0)
                weight = 1.0
                if self.config.score_weights:
                    weight = self.config.score_weights.get(score_name, 1.0)

                weighted_sum += score.value * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _check_trace_passed(
        self, results: List[EvalResult], errors: List[Dict]
    ) -> bool:
        """Check if trace passed all required evaluators.

        Args:
            results: List of evaluation results
            errors: List of errors encountered

        Returns:
            True if all required evaluators passed
        """
        # If there are errors in required evaluators, fail
        if errors and self.config.required_evaluators:
            for error in errors:
                if error["evaluator"] in self.config.required_evaluators:
                    return False

        # Check that all required evaluators passed
        if self.config.required_evaluators:
            for evaluator_name in self.config.required_evaluators:
                result = next(
                    (r for r in results if r.evaluator_name == evaluator_name), None
                )
                if result is None:
                    return False  # Required evaluator missing
                if not result.all_passed():
                    return False  # Required evaluator failed

        # Otherwise, check if all evaluators passed
        return all(result.all_passed() for result in results)

    async def evaluate_batch(
        self,
        traces: List[Trace],
        evaluators: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchEvaluation:
        """Evaluate a batch of traces.

        Args:
            traces: List of traces to evaluate
            evaluators: Optional list of evaluator names
            progress_callback: Optional callback(completed, total)

        Returns:
            BatchEvaluation with aggregated results

        Example:
            >>> def progress(completed, total):
            ...     print(f"Progress: {completed}/{total}")
            >>>
            >>> batch = await runner.evaluate_batch(
            ...     traces,
            ...     progress_callback=progress
            ... )
        """
        started_at = datetime.utcnow()
        evaluations = []

        # Evaluate each trace
        for i, trace in enumerate(traces):
            try:
                evaluation = await self.evaluate_trace(trace, evaluators)
                evaluations.append(evaluation)
            except Exception as e:
                if not self.config.continue_on_error:
                    raise

                # Record error and continue
                evaluations.append(
                    TraceEvaluation(
                        trace_id=trace.trace_id,
                        results=[],
                        overall_score=0.0,
                        passed=False,
                        duration_ms=0,
                        errors=[
                            {
                                "evaluator": "runner",
                                "error": str(e),
                                "type": type(e).__name__,
                            }
                        ],
                    )
                )

            # Call progress callback
            if progress_callback:
                progress_callback(i + 1, len(traces))

        completed_at = datetime.utcnow()

        # Calculate summary
        summary = self._calculate_batch_summary(evaluations)

        return BatchEvaluation(
            evaluations=evaluations,
            summary=summary,
            started_at=started_at,
            completed_at=completed_at,
        )

    def _calculate_batch_summary(
        self, evaluations: List[TraceEvaluation]
    ) -> BatchSummary:
        """Calculate summary statistics for batch.

        Args:
            evaluations: List of trace evaluations

        Returns:
            BatchSummary with statistics
        """
        total = len(evaluations)
        passed = sum(1 for e in evaluations if e.passed)
        failed = sum(1 for e in evaluations if not e.passed and not e.errors)
        errors = sum(1 for e in evaluations if e.errors)

        # Collect scores by evaluator/score name
        scores_by_name: Dict[str, List[float]] = defaultdict(list)

        for evaluation in evaluations:
            for result in evaluation.results:
                for score_name, score in result.scores.items():
                    scores_by_name[score_name].append(score.value)

        # Calculate averages
        average_scores = {
            name: statistics.mean(scores) for name, scores in scores_by_name.items()
        }

        # Average duration
        avg_duration = statistics.mean(e.duration_ms for e in evaluations) if evaluations else 0.0

        return BatchSummary(
            total_traces=total,
            passed_traces=passed,
            failed_traces=failed,
            error_traces=errors,
            average_scores=average_scores,
            score_distributions=dict(scores_by_name),
            average_duration_ms=avg_duration,
        )

    async def compare_to_baseline(
        self,
        current: BatchEvaluation,
        baseline: BatchEvaluation,
        regression_threshold: float = 0.05,
    ) -> Comparison:
        """Compare current evaluation to baseline.

        Args:
            current: Current batch evaluation
            baseline: Baseline batch evaluation
            regression_threshold: Threshold for detecting regressions (default 0.05 = 5%)

        Returns:
            Comparison with regressions and improvements

        Example:
            >>> comparison = await runner.compare_to_baseline(
            ...     current=pr_results,
            ...     baseline=main_results,
            ...     regression_threshold=0.05
            ... )
            >>> if comparison.has_regressions:
            ...     print(f"Found {len(comparison.regressions)} regressions")
        """
        regressions = []
        improvements = []
        unchanged = []

        # Compare trace by trace
        for curr_eval in current.evaluations:
            baseline_eval = baseline.get_evaluation(curr_eval.trace_id)
            if baseline_eval is None:
                continue  # Skip traces not in baseline

            # Compare each evaluator's scores
            for curr_result in curr_eval.results:
                baseline_result = baseline_eval.get_result(curr_result.evaluator_name)
                if baseline_result is None:
                    continue

                # Compare each score
                for score_name, curr_score in curr_result.scores.items():
                    baseline_score = baseline_result.scores.get(score_name)
                    if baseline_score is None:
                        continue

                    delta = curr_score.value - baseline_score.value

                    # Check if this is a regression
                    if delta < -regression_threshold:
                        regressions.append(
                            Regression(
                                evaluator=curr_result.evaluator_name,
                                score_name=score_name,
                                baseline_score=baseline_score.value,
                                current_score=curr_score.value,
                                delta=delta,
                                trace_id=curr_eval.trace_id,
                            )
                        )
                    elif delta > regression_threshold:
                        improvements.append(
                            Improvement(
                                evaluator=curr_result.evaluator_name,
                                score_name=score_name,
                                baseline_score=baseline_score.value,
                                current_score=curr_score.value,
                                delta=delta,
                                trace_id=curr_eval.trace_id,
                            )
                        )
                    else:
                        if score_name not in unchanged:
                            unchanged.append(score_name)

        # Calculate statistical summary
        statistical_summary = self._calculate_statistical_summary(
            current, baseline, regressions, improvements
        )

        return Comparison(
            regressions=regressions,
            improvements=improvements,
            unchanged=unchanged,
            statistical_summary=statistical_summary,
        )

    def _calculate_statistical_summary(
        self,
        current: BatchEvaluation,
        baseline: BatchEvaluation,
        regressions: List[Regression],
        improvements: List[Improvement],
    ) -> Dict[str, Any]:
        """Calculate statistical summary of comparison.

        Args:
            current: Current batch
            baseline: Baseline batch
            regressions: List of regressions
            improvements: List of improvements

        Returns:
            Dictionary with statistical metrics
        """
        # Calculate mean score changes
        score_changes = []
        for name in current.summary.average_scores.keys():
            if name in baseline.summary.average_scores:
                delta = (
                    current.summary.average_scores[name]
                    - baseline.summary.average_scores[name]
                )
                score_changes.append(delta)

        return {
            "regression_count": len(regressions),
            "improvement_count": len(improvements),
            "mean_score_change": statistics.mean(score_changes) if score_changes else 0.0,
            "current_pass_rate": current.summary.pass_rate,
            "baseline_pass_rate": baseline.summary.pass_rate,
            "pass_rate_change": current.summary.pass_rate - baseline.summary.pass_rate,
        }
