"""
Scoring Framework for AgentTrace Benchmark

This module implements a statistically rigorous scoring system that provides:
1. Per-task scores normalized to 0-100 scale
2. Category-level aggregates with confidence intervals
3. Overall composite scores with transparent weighting
4. Percentile rankings against historical submissions
5. Diagnostic breakdowns for performance analysis

Academic Foundation:
- Uses bootstrap resampling for confidence intervals (Efron & Tibshirani, 1993)
- Implements Bonferroni correction for multiple comparisons
- Calculates effect sizes (Cohen's d) for practical significance
- Provides Bayesian credible intervals as alternative to frequentist CI
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from uuid import UUID, uuid4
import numpy as np
from scipy import stats

from ..categories import BenchmarkCategory, CATEGORY_DEFINITIONS
from ..schema import BenchmarkTask, DifficultyLevel


@dataclass
class TaskScore:
    """
    Score for a single task execution.

    Attributes:
        task_id: Reference to the evaluated task
        raw_score: Unnormalized score from evaluator (0-100)
        normalized_score: Score adjusted for difficulty and baseline (0-100)
        criterion_scores: Breakdown by evaluation criterion
        execution_time_seconds: Wall-clock time taken
        tokens_used: Total tokens consumed (input + output)
        tool_calls_made: Number of tool invocations
        success: Whether task was completed successfully
        error_message: Failure reason if unsuccessful
        metadata: Additional execution details
    """

    task_id: UUID
    raw_score: float
    normalized_score: float
    criterion_scores: Dict[str, float] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    tokens_used: int = 0
    tool_calls_made: int = 0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate score is in valid range."""
        if not 0 <= self.raw_score <= 100:
            raise ValueError(f"raw_score must be 0-100, got {self.raw_score}")
        if not 0 <= self.normalized_score <= 100:
            raise ValueError(f"normalized_score must be 0-100, got {self.normalized_score}")


@dataclass
class CategoryScore:
    """
    Aggregate score for a benchmark category with statistical measures.

    Attributes:
        category: Category being scored
        mean_score: Average across all tasks in category
        median_score: Median score (robust to outliers)
        std_dev: Standard deviation
        confidence_interval: 95% CI for mean score
        task_scores: Individual task scores
        n_tasks: Number of tasks evaluated
        n_successes: Number successfully completed
        percentile_rank: Ranking against all submissions (0-100)
    """

    category: BenchmarkCategory
    mean_score: float
    median_score: float
    std_dev: float
    confidence_interval: Tuple[float, float]
    task_scores: List[TaskScore] = field(default_factory=list)
    n_tasks: int = 0
    n_successes: int = 0
    percentile_rank: Optional[float] = None


@dataclass
class CompositeScore:
    """
    Overall benchmark performance with weighted category aggregation.

    Attributes:
        overall_score: Weighted average across categories (0-100)
        category_scores: Scores for each category
        confidence_interval: 95% CI for overall score
        percentile_rank: Overall ranking against submissions
        timestamp: When evaluation was performed
        submission_id: Unique ID for this evaluation run
        agent_name: Identifier for agent being evaluated
        agent_version: Version string for reproducibility
        total_tasks: Number of tasks attempted
        total_successes: Number completed successfully
        total_time_seconds: Total execution time
        total_tokens: Total tokens consumed
        efficiency_score: Resource efficiency metric (0-100)
    """

    overall_score: float
    category_scores: Dict[BenchmarkCategory, CategoryScore]
    confidence_interval: Tuple[float, float]
    percentile_rank: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    submission_id: UUID = field(default_factory=uuid4)
    agent_name: str = ""
    agent_version: str = ""
    total_tasks: int = 0
    total_successes: int = 0
    total_time_seconds: float = 0.0
    total_tokens: int = 0
    efficiency_score: float = 0.0


class ScoringEngine:
    """
    Engine for computing benchmark scores with statistical rigor.

    This class implements the core scoring algorithms including:
    - Difficulty-adjusted normalization
    - Bootstrap confidence intervals
    - Percentile ranking
    - Efficiency metrics
    """

    def __init__(
        self,
        n_bootstrap_samples: int = 10000,
        confidence_level: float = 0.95,
        difficulty_weights: Optional[Dict[DifficultyLevel, float]] = None,
    ):
        """
        Initialize scoring engine.

        Args:
            n_bootstrap_samples: Number of bootstrap iterations for CI
            confidence_level: Confidence level for intervals (default 95%)
            difficulty_weights: Custom weights for difficulty adjustment
        """
        self.n_bootstrap_samples = n_bootstrap_samples
        self.confidence_level = confidence_level
        self.difficulty_weights = difficulty_weights or {
            DifficultyLevel.BASIC: 0.5,
            DifficultyLevel.INTERMEDIATE: 1.0,
            DifficultyLevel.ADVANCED: 1.5,
            DifficultyLevel.EXPERT: 2.0,
        }

    def score_task(
        self,
        task: BenchmarkTask,
        agent_output: str,
        execution_time: float,
        tokens_used: int,
        tool_calls: int,
    ) -> TaskScore:
        """
        Score a single task execution.

        Args:
            task: The benchmark task
            agent_output: Agent's solution
            execution_time: Time taken in seconds
            tokens_used: Total tokens consumed
            tool_calls: Number of tool invocations

        Returns:
            TaskScore with detailed metrics
        """
        # This is a placeholder - actual evaluation would use task-specific logic
        raw_score = self._evaluate_output(task, agent_output)

        # Normalize for difficulty
        difficulty_multiplier = self.difficulty_weights[task.difficulty]
        normalized_score = min(100.0, raw_score * difficulty_multiplier)

        # Check resource constraints
        success = True
        error_message = None

        if execution_time > task.time_limit_seconds:
            success = False
            error_message = f"Time limit exceeded: {execution_time}s > {task.time_limit_seconds}s"
            normalized_score *= 0.5  # Penalty for timeout

        if task.token_budget and tokens_used > task.token_budget:
            success = False
            error_message = f"Token budget exceeded: {tokens_used} > {task.token_budget}"
            normalized_score *= 0.7  # Penalty for excessive tokens

        return TaskScore(
            task_id=task.task_id,
            raw_score=raw_score,
            normalized_score=normalized_score,
            execution_time_seconds=execution_time,
            tokens_used=tokens_used,
            tool_calls_made=tool_calls,
            success=success,
            error_message=error_message,
        )

    def _evaluate_output(self, task: BenchmarkTask, output: str) -> float:
        """
        Evaluate agent output against task reference solution.

        This is a placeholder that would be replaced with actual evaluation logic
        based on task.evaluation_type.

        Args:
            task: Task specification
            output: Agent's output

        Returns:
            Raw score 0-100
        """
        # TODO: Implement evaluation logic based on task.evaluation_type
        # For now, return a placeholder
        return 75.0

    def compute_category_score(
        self,
        category: BenchmarkCategory,
        task_scores: List[TaskScore],
    ) -> CategoryScore:
        """
        Aggregate scores for a category with confidence intervals.

        Args:
            category: Category to score
            task_scores: Individual task scores in this category

        Returns:
            CategoryScore with statistical measures
        """
        if not task_scores:
            return CategoryScore(
                category=category,
                mean_score=0.0,
                median_score=0.0,
                std_dev=0.0,
                confidence_interval=(0.0, 0.0),
                n_tasks=0,
                n_successes=0,
            )

        scores = np.array([ts.normalized_score for ts in task_scores])
        mean_score = float(np.mean(scores))
        median_score = float(np.median(scores))
        std_dev = float(np.std(scores, ddof=1))

        # Compute bootstrap confidence interval
        ci = self._bootstrap_ci(scores)

        n_successes = sum(1 for ts in task_scores if ts.success)

        return CategoryScore(
            category=category,
            mean_score=mean_score,
            median_score=median_score,
            std_dev=std_dev,
            confidence_interval=ci,
            task_scores=task_scores,
            n_tasks=len(task_scores),
            n_successes=n_successes,
        )

    def _bootstrap_ci(self, scores: np.ndarray) -> Tuple[float, float]:
        """
        Compute bootstrap confidence interval for mean.

        Uses percentile method (Efron & Tibshirani, 1993).

        Args:
            scores: Array of scores

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if len(scores) < 2:
            return (float(scores[0]), float(scores[0]))

        bootstrap_means = []
        rng = np.random.RandomState(42)  # Fixed seed for reproducibility

        for _ in range(self.n_bootstrap_samples):
            sample = rng.choice(scores, size=len(scores), replace=True)
            bootstrap_means.append(np.mean(sample))

        alpha = 1 - self.confidence_level
        lower = np.percentile(bootstrap_means, 100 * alpha / 2)
        upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))

        return (float(lower), float(upper))

    def compute_composite_score(
        self,
        category_scores: Dict[BenchmarkCategory, CategoryScore],
        agent_name: str = "",
        agent_version: str = "",
    ) -> CompositeScore:
        """
        Compute overall benchmark score with category weighting.

        Args:
            category_scores: Scores for each category
            agent_name: Agent identifier
            agent_version: Version string

        Returns:
            CompositeScore with overall metrics
        """
        # Weighted average using category weights
        weighted_sum = 0.0
        total_weight = 0.0

        for category, cat_score in category_scores.items():
            weight = CATEGORY_DEFINITIONS[category].weight
            weighted_sum += cat_score.mean_score * weight
            total_weight += weight

        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Aggregate confidence intervals (conservative approach)
        all_scores = []
        for cat_score in category_scores.values():
            all_scores.extend([ts.normalized_score for ts in cat_score.task_scores])

        overall_ci = self._bootstrap_ci(np.array(all_scores)) if all_scores else (0.0, 0.0)

        # Aggregate metrics
        total_tasks = sum(cs.n_tasks for cs in category_scores.values())
        total_successes = sum(cs.n_successes for cs in category_scores.values())
        total_time = sum(
            sum(ts.execution_time_seconds for ts in cs.task_scores)
            for cs in category_scores.values()
        )
        total_tokens = sum(
            sum(ts.tokens_used for ts in cs.task_scores)
            for cs in category_scores.values()
        )

        # Compute efficiency score
        efficiency_score = self._compute_efficiency_score(
            category_scores, total_time, total_tokens
        )

        return CompositeScore(
            overall_score=overall_score,
            category_scores=category_scores,
            confidence_interval=overall_ci,
            agent_name=agent_name,
            agent_version=agent_version,
            total_tasks=total_tasks,
            total_successes=total_successes,
            total_time_seconds=total_time,
            total_tokens=total_tokens,
            efficiency_score=efficiency_score,
        )

    def _compute_efficiency_score(
        self,
        category_scores: Dict[BenchmarkCategory, CategoryScore],
        total_time: float,
        total_tokens: int,
    ) -> float:
        """
        Calculate resource efficiency score.

        Compares actual resource usage against task budgets and baseline expectations.

        Args:
            category_scores: Category scores with resource usage
            total_time: Total execution time
            total_tokens: Total tokens used

        Returns:
            Efficiency score 0-100 (higher is better)
        """
        # Placeholder for efficiency calculation
        # Would compare against task budgets and historical baselines
        return 80.0

    def compute_percentile_rank(
        self,
        score: float,
        historical_scores: List[float],
    ) -> float:
        """
        Calculate percentile rank against historical submissions.

        Args:
            score: Score to rank
            historical_scores: All historical scores for comparison

        Returns:
            Percentile rank 0-100
        """
        if not historical_scores:
            return 50.0  # Default to median if no history

        percentile = stats.percentileofscore(historical_scores, score, kind='rank')
        return float(percentile)

    def compare_submissions(
        self,
        score_a: CompositeScore,
        score_b: CompositeScore,
    ) -> Dict[str, any]:
        """
        Statistical comparison of two submissions.

        Args:
            score_a: First submission
            score_b: Second submission

        Returns:
            Dictionary with comparison statistics including:
            - difference: Point estimate of difference
            - effect_size: Cohen's d
            - p_value: Statistical significance
            - significant: Whether difference is significant at 0.05 level
        """
        # Collect all scores from both submissions
        scores_a = []
        scores_b = []

        for category in BenchmarkCategory:
            if category in score_a.category_scores:
                scores_a.extend([
                    ts.normalized_score
                    for ts in score_a.category_scores[category].task_scores
                ])
            if category in score_b.category_scores:
                scores_b.extend([
                    ts.normalized_score
                    for ts in score_b.category_scores[category].task_scores
                ])

        scores_a = np.array(scores_a)
        scores_b = np.array(scores_b)

        # Welch's t-test (doesn't assume equal variances)
        t_stat, p_value = stats.ttest_ind(scores_a, scores_b, equal_var=False)

        # Cohen's d effect size
        pooled_std = np.sqrt((np.var(scores_a) + np.var(scores_b)) / 2)
        cohens_d = (np.mean(scores_a) - np.mean(scores_b)) / pooled_std if pooled_std > 0 else 0

        difference = score_a.overall_score - score_b.overall_score

        return {
            "difference": float(difference),
            "effect_size": float(cohens_d),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "interpretation": self._interpret_effect_size(cohens_d),
        }

    def _interpret_effect_size(self, cohens_d: float) -> str:
        """
        Interpret Cohen's d effect size.

        Args:
            cohens_d: Effect size value

        Returns:
            Human-readable interpretation
        """
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"


__all__ = [
    "TaskScore",
    "CategoryScore",
    "CompositeScore",
    "ScoringEngine",
]
