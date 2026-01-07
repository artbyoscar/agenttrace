"""
Anti-Gaming Measures for AgentTrace Benchmark

This module implements strategies to prevent benchmark overfitting and gaming,
ensuring the benchmark remains a valid measure of general agent capabilities
rather than narrow optimization to specific tasks.

Threat Model:
1. Direct memorization of task solutions
2. Overfitting to task distribution
3. Exploiting evaluation artifacts
4. Statistical anomalies indicating gaming
5. Coordinated attacks on benchmark integrity

Defense Strategy:
- Held-out test sets (never publicly released)
- Regular task rotation and versioning
- Submission rate limiting
- Diversity requirements
- Statistical anomaly detection
- Differential privacy in leaderboards

Academic Foundation:
- Based on ML security research (Papernot et al., 2016)
- Dataset contamination detection (Dodge et al., 2021)
- Benchmark integrity best practices (Dehghani et al., 2021)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from uuid import UUID
import numpy as np
from scipy import stats

from ..schema import BenchmarkTask, TaskSuite
from ..scoring import CompositeScore


@dataclass
class SubmissionPolicy:
    """
    Rules governing benchmark submission frequency and requirements.

    Attributes:
        max_submissions_per_day: Maximum submissions from one entity per day
        max_submissions_per_week: Maximum submissions per week
        min_time_between_submissions: Minimum hours between submissions
        require_system_description: Whether to require architecture documentation
        require_code_availability: Whether to require open-source code
        diversity_threshold: Minimum required diversity across task types
    """

    max_submissions_per_day: int = 5
    max_submissions_per_week: int = 20
    min_time_between_submissions: float = 1.0  # hours
    require_system_description: bool = True
    require_code_availability: bool = False
    diversity_threshold: float = 0.8  # Must attempt 80% of categories


@dataclass
class HeldOutTestSet:
    """
    Private test set held out from public release.

    The held-out set is used for official evaluations and leaderboard ranking
    to prevent direct optimization to the test distribution.

    Attributes:
        test_suite: Private task suite
        creation_date: When test set was created
        rotation_schedule: When to rotate in new tasks
        contamination_checks: Tasks to check for data leakage
        access_log: Record of all accesses to test set
    """

    test_suite: TaskSuite
    creation_date: datetime = field(default_factory=datetime.utcnow)
    rotation_schedule: timedelta = field(default=timedelta(days=90))  # Quarterly rotation
    contamination_checks: List[str] = field(default_factory=list)
    access_log: List[Dict[str, any]] = field(default_factory=list)

    def is_due_for_rotation(self) -> bool:
        """Check if test set should be rotated."""
        time_since_creation = datetime.utcnow() - self.creation_date
        return time_since_creation >= self.rotation_schedule

    def log_access(self, accessor_id: str, purpose: str) -> None:
        """Record access to held-out test set."""
        self.access_log.append({
            "accessor_id": accessor_id,
            "purpose": purpose,
            "timestamp": datetime.utcnow().isoformat(),
        })


class TaskRotationManager:
    """
    Manages periodic rotation of benchmark tasks to prevent overfitting.

    Tasks are rotated on a schedule, with some moved to held-out set and
    new tasks introduced to the public benchmark.
    """

    def __init__(
        self,
        rotation_period_days: int = 90,
        rotation_percentage: float = 0.2,
    ):
        """
        Initialize rotation manager.

        Args:
            rotation_period_days: Days between rotations (default quarterly)
            rotation_percentage: Fraction of tasks to rotate each period
        """
        self.rotation_period = timedelta(days=rotation_period_days)
        self.rotation_percentage = rotation_percentage
        self.last_rotation: Optional[datetime] = None
        self.rotation_history: List[Dict[str, any]] = []

    def should_rotate(self) -> bool:
        """Check if rotation is due."""
        if self.last_rotation is None:
            return True
        time_since_rotation = datetime.utcnow() - self.last_rotation
        return time_since_rotation >= self.rotation_period

    def select_tasks_for_rotation(
        self,
        public_tasks: List[BenchmarkTask],
        performance_data: Optional[Dict[UUID, float]] = None,
    ) -> List[UUID]:
        """
        Select which tasks to rotate out of public benchmark.

        Strategy:
        1. Prioritize tasks with suspiciously high performance
        2. Ensure diversity across categories
        3. Respect minimum task age requirements

        Args:
            public_tasks: Current public task suite
            performance_data: Optional map of task_id to success rate

        Returns:
            List of task IDs to move to held-out set
        """
        n_to_rotate = int(len(public_tasks) * self.rotation_percentage)

        # If performance data available, prioritize high-performing tasks
        # (possible sign of memorization)
        if performance_data:
            sorted_tasks = sorted(
                public_tasks,
                key=lambda t: performance_data.get(t.task_id, 0.0),
                reverse=True,
            )
        else:
            # Otherwise, random selection
            rng = np.random.RandomState(42)
            sorted_tasks = list(public_tasks)
            rng.shuffle(sorted_tasks)

        # Select top n_to_rotate
        selected = sorted_tasks[:n_to_rotate]

        # Record rotation
        self.rotation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "n_rotated": len(selected),
            "task_ids": [str(t.task_id) for t in selected],
        })

        self.last_rotation = datetime.utcnow()

        return [t.task_id for t in selected]


class AnomalyDetector:
    """
    Detects statistical anomalies that may indicate benchmark gaming.

    Anomalies checked:
    1. Suspiciously high performance on specific task subsets
    2. Performance discontinuities (sudden jumps)
    3. Inconsistent performance across similar tasks
    4. Unusual efficiency patterns
    5. Outlier detection in score distributions
    """

    def __init__(
        self,
        z_score_threshold: float = 3.0,
        performance_jump_threshold: float = 15.0,
    ):
        """
        Initialize anomaly detector.

        Args:
            z_score_threshold: Z-score for outlier detection
            performance_jump_threshold: Percentage jump considered anomalous
        """
        self.z_score_threshold = z_score_threshold
        self.performance_jump_threshold = performance_jump_threshold

    def detect_anomalies(
        self,
        current_score: CompositeScore,
        historical_scores: List[CompositeScore],
    ) -> Dict[str, any]:
        """
        Analyze submission for statistical anomalies.

        Args:
            current_score: Submission to analyze
            historical_scores: Previous submissions from same submitter

        Returns:
            Dictionary of detected anomalies with severity
        """
        anomalies = {}

        # Check for performance discontinuity
        if historical_scores:
            prev_score = historical_scores[-1].overall_score
            jump = current_score.overall_score - prev_score
            if jump > self.performance_jump_threshold:
                anomalies["discontinuity"] = {
                    "severity": "high",
                    "message": f"Performance jump of {jump:.1f}% from previous submission",
                    "previous": prev_score,
                    "current": current_score.overall_score,
                }

        # Check for suspicious category imbalance
        category_imbalance = self._check_category_imbalance(current_score)
        if category_imbalance:
            anomalies["category_imbalance"] = category_imbalance

        # Check for outlier performance
        outlier_check = self._check_outlier_performance(current_score, historical_scores)
        if outlier_check:
            anomalies["outlier"] = outlier_check

        return anomalies

    def _check_category_imbalance(self, score: CompositeScore) -> Optional[Dict[str, any]]:
        """
        Check if performance is suspiciously imbalanced across categories.

        This could indicate overfitting to specific task types.
        """
        category_scores = [cs.mean_score for cs in score.category_scores.values()]
        if len(category_scores) < 2:
            return None

        # Calculate coefficient of variation
        cv = np.std(category_scores) / np.mean(category_scores) if np.mean(category_scores) > 0 else 0

        # High variance across categories is suspicious
        if cv > 0.5:  # 50% coefficient of variation
            return {
                "severity": "medium",
                "message": "Highly imbalanced performance across categories",
                "coefficient_of_variation": float(cv),
                "category_scores": {
                    cat.value: cs.mean_score
                    for cat, cs in score.category_scores.items()
                },
            }

        return None

    def _check_outlier_performance(
        self,
        current_score: CompositeScore,
        historical_scores: List[CompositeScore],
    ) -> Optional[Dict[str, any]]:
        """
        Check if performance is a statistical outlier.

        Uses z-score method with historical distribution.
        """
        if len(historical_scores) < 5:  # Need sufficient history
            return None

        all_scores = [s.overall_score for s in historical_scores]
        mean_score = np.mean(all_scores)
        std_score = np.std(all_scores)

        if std_score == 0:
            return None

        z_score = (current_score.overall_score - mean_score) / std_score

        if abs(z_score) > self.z_score_threshold:
            return {
                "severity": "high",
                "message": f"Performance is {abs(z_score):.1f} standard deviations from mean",
                "z_score": float(z_score),
                "current": current_score.overall_score,
                "historical_mean": float(mean_score),
                "historical_std": float(std_score),
            }

        return None


class DiversityChecker:
    """
    Ensures submissions demonstrate broad capabilities across task types.

    Prevents gaming by requiring agents to perform well across diverse tasks
    rather than specializing on narrow subsets.
    """

    def __init__(self, minimum_category_coverage: float = 0.8):
        """
        Initialize diversity checker.

        Args:
            minimum_category_coverage: Minimum fraction of categories to attempt
        """
        self.minimum_category_coverage = minimum_category_coverage

    def check_diversity(self, score: CompositeScore) -> Dict[str, any]:
        """
        Verify submission meets diversity requirements.

        Args:
            score: Submission to check

        Returns:
            Dictionary with diversity metrics and pass/fail
        """
        from ..categories import BenchmarkCategory

        total_categories = len(BenchmarkCategory)
        attempted_categories = len(score.category_scores)
        coverage = attempted_categories / total_categories

        # Check category coverage
        meets_coverage = coverage >= self.minimum_category_coverage

        # Check for category-specific gaming (very high score in one, low in others)
        if len(score.category_scores) > 1:
            scores = [cs.mean_score for cs in score.category_scores.values()]
            max_score = max(scores)
            min_score = min(scores)
            score_range = max_score - min_score

            # Flag if range is too large (suggests specialization)
            balanced = score_range < 40.0  # Max 40 point spread
        else:
            balanced = False

        return {
            "passes": meets_coverage and balanced,
            "category_coverage": coverage,
            "categories_attempted": attempted_categories,
            "categories_total": total_categories,
            "balanced": balanced,
            "recommendations": self._generate_recommendations(
                meets_coverage, balanced, score
            ),
        }

    def _generate_recommendations(
        self,
        meets_coverage: bool,
        balanced: bool,
        score: CompositeScore,
    ) -> List[str]:
        """Generate recommendations for improving diversity."""
        recommendations = []

        if not meets_coverage:
            recommendations.append(
                f"Attempt tasks in more categories. "
                f"Current: {len(score.category_scores)}, "
                f"Required: {int(self.minimum_category_coverage * 6)}"
            )

        if not balanced:
            recommendations.append(
                "Performance is imbalanced across categories. "
                "Focus on improving weaker categories."
            )

        return recommendations


class ContaminationDetector:
    """
    Detects potential data contamination or leakage.

    Checks for signs that the agent may have been trained on test data
    or has memorized specific task solutions.
    """

    def __init__(self):
        """Initialize contamination detector."""
        self.contamination_patterns: List[str] = []

    def check_for_contamination(
        self,
        agent_output: str,
        task: BenchmarkTask,
        reference_solution: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Check if agent output shows signs of contamination.

        Signals of contamination:
        1. Exact match to reference solution (including formatting)
        2. Presence of specific markers from task construction
        3. Unrealistic precision in numeric answers
        4. Suspiciously efficient path to solution

        Args:
            agent_output: Agent's response
            task: The benchmark task
            reference_solution: Reference solution (if available)

        Returns:
            Dictionary with contamination analysis
        """
        issues = []

        # Check for exact match with reference
        if reference_solution:
            if agent_output.strip() == reference_solution.strip():
                issues.append({
                    "type": "exact_match",
                    "severity": "high",
                    "message": "Output exactly matches reference solution",
                })

        # Check for internal markers (e.g., "REFERENCE_SOLUTION_v1.2")
        internal_markers = ["REFERENCE", "SOLUTION_v", "INTERNAL_USE", "TEST_ANSWER"]
        for marker in internal_markers:
            if marker in agent_output:
                issues.append({
                    "type": "internal_marker",
                    "severity": "critical",
                    "message": f"Output contains internal marker: {marker}",
                })

        return {
            "contaminated": len(issues) > 0,
            "issues": issues,
            "confidence": "high" if any(i["severity"] == "critical" for i in issues) else "medium",
        }


@dataclass
class AntiGamingReport:
    """
    Comprehensive report on anti-gaming measures for a submission.

    Attributes:
        submission_id: ID of evaluated submission
        timestamp: When analysis was performed
        policy_compliance: Whether submission meets policy requirements
        anomalies_detected: Statistical anomalies found
        diversity_check: Results of diversity analysis
        contamination_check: Results of contamination detection
        recommendation: Overall recommendation (ACCEPT, REVIEW, REJECT)
        notes: Additional observations
    """

    submission_id: UUID
    timestamp: datetime = field(default_factory=datetime.utcnow)
    policy_compliance: bool = True
    anomalies_detected: Dict[str, any] = field(default_factory=dict)
    diversity_check: Dict[str, any] = field(default_factory=dict)
    contamination_check: Dict[str, any] = field(default_factory=dict)
    recommendation: str = "ACCEPT"
    notes: List[str] = field(default_factory=list)


__all__ = [
    "SubmissionPolicy",
    "HeldOutTestSet",
    "TaskRotationManager",
    "AnomalyDetector",
    "DiversityChecker",
    "ContaminationDetector",
    "AntiGamingReport",
]
