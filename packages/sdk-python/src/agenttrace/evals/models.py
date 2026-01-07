"""Data structures for evaluation results and scores."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class EvalScore:
    """Represents a single evaluation score.

    Attributes:
        name: Name of the score metric (e.g., "accuracy", "completeness")
        value: Normalized score value between 0.0 and 1.0
        threshold: Optional threshold for pass/fail determination
        passed: Whether the score meets the threshold (computed automatically)

    Example:
        >>> score = EvalScore(name="accuracy", value=0.85, threshold=0.8)
        >>> score.passed
        True
    """

    name: str
    value: float
    threshold: Optional[float] = None
    passed: Optional[bool] = field(init=False, default=None)

    def __post_init__(self):
        """Validate score value and compute passed status."""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(
                f"Score value must be between 0.0 and 1.0, got {self.value}"
            )

        if self.threshold is not None:
            if not 0.0 <= self.threshold <= 1.0:
                raise ValueError(
                    f"Threshold must be between 0.0 and 1.0, got {self.threshold}"
                )
            self.passed = self.value >= self.threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert score to dictionary representation.

        Returns:
            Dictionary containing all score attributes
        """
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "passed": self.passed,
        }


@dataclass
class EvalResult:
    """Represents the result of a single evaluation.

    Attributes:
        evaluator_name: Name of the evaluator that produced this result
        scores: Dictionary of score names to EvalScore objects
        feedback: Optional human-readable feedback message
        metadata: Additional metadata about the evaluation
        timestamp: When the evaluation was performed

    Example:
        >>> result = EvalResult(
        ...     evaluator_name="completeness_check",
        ...     scores={"completeness": EvalScore("completeness", 0.9)},
        ...     feedback="All required fields present",
        ... )
    """

    evaluator_name: str
    scores: Dict[str, EvalScore]
    feedback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate that scores dict is not empty."""
        if not self.scores:
            raise ValueError("EvalResult must contain at least one score")

    def get_score(self, name: str) -> Optional[EvalScore]:
        """Get a specific score by name.

        Args:
            name: Name of the score to retrieve

        Returns:
            EvalScore object or None if not found
        """
        return self.scores.get(name)

    def all_passed(self) -> bool:
        """Check if all scores with thresholds passed.

        Returns:
            True if all scores with thresholds passed, False otherwise
            Returns True if no scores have thresholds
        """
        scores_with_thresholds = [
            score for score in self.scores.values()
            if score.threshold is not None
        ]

        if not scores_with_thresholds:
            return True

        return all(score.passed for score in scores_with_thresholds)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary representation.

        Returns:
            Dictionary containing all result attributes
        """
        return {
            "evaluator_name": self.evaluator_name,
            "scores": {name: score.to_dict() for name, score in self.scores.items()},
            "feedback": self.feedback,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EvalSummary:
    """Aggregates multiple evaluation results.

    Attributes:
        results: List of individual evaluation results
        total_evaluators: Total number of evaluators run
        passed_evaluators: Number of evaluators that passed all thresholds
        failed_evaluators: Number of evaluators that failed any threshold
        average_scores: Dictionary of average scores across all evaluators

    Example:
        >>> summary = EvalSummary([result1, result2, result3])
        >>> summary.pass_rate
        0.66
    """

    results: List[EvalResult]
    total_evaluators: int = field(init=False)
    passed_evaluators: int = field(init=False)
    failed_evaluators: int = field(init=False)
    average_scores: Dict[str, float] = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Compute summary statistics."""
        self.total_evaluators = len(self.results)
        self.passed_evaluators = sum(1 for r in self.results if r.all_passed())
        self.failed_evaluators = self.total_evaluators - self.passed_evaluators

        # Compute average scores across all evaluators
        score_sums: Dict[str, List[float]] = {}
        for result in self.results:
            for score_name, score in result.scores.items():
                if score_name not in score_sums:
                    score_sums[score_name] = []
                score_sums[score_name].append(score.value)

        self.average_scores = {
            name: sum(values) / len(values)
            for name, values in score_sums.items()
        }

    @property
    def pass_rate(self) -> float:
        """Calculate the pass rate of all evaluators.

        Returns:
            Percentage of evaluators that passed (0.0 to 1.0)
        """
        if self.total_evaluators == 0:
            return 0.0
        return self.passed_evaluators / self.total_evaluators

    def get_failed_results(self) -> List[EvalResult]:
        """Get all results that failed.

        Returns:
            List of EvalResult objects that failed
        """
        return [r for r in self.results if not r.all_passed()]

    def get_passed_results(self) -> List[EvalResult]:
        """Get all results that passed.

        Returns:
            List of EvalResult objects that passed
        """
        return [r for r in self.results if r.all_passed()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert summary to dictionary representation.

        Returns:
            Dictionary containing all summary attributes
        """
        return {
            "total_evaluators": self.total_evaluators,
            "passed_evaluators": self.passed_evaluators,
            "failed_evaluators": self.failed_evaluators,
            "pass_rate": self.pass_rate,
            "average_scores": self.average_scores,
            "results": [r.to_dict() for r in self.results],
        }
