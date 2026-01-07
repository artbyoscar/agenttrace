"""Unit tests for evaluation models."""

import pytest
from datetime import datetime
from agenttrace.evals.models import EvalScore, EvalResult, EvalSummary


class TestEvalScore:
    """Tests for EvalScore dataclass."""

    def test_create_score_without_threshold(self):
        """Test creating a score without a threshold."""
        score = EvalScore(name="accuracy", value=0.85)

        assert score.name == "accuracy"
        assert score.value == 0.85
        assert score.threshold is None
        assert score.passed is None

    def test_create_score_with_threshold_passed(self):
        """Test creating a score with a threshold that passes."""
        score = EvalScore(name="accuracy", value=0.85, threshold=0.8)

        assert score.name == "accuracy"
        assert score.value == 0.85
        assert score.threshold == 0.8
        assert score.passed is True

    def test_create_score_with_threshold_failed(self):
        """Test creating a score with a threshold that fails."""
        score = EvalScore(name="accuracy", value=0.75, threshold=0.8)

        assert score.name == "accuracy"
        assert score.value == 0.75
        assert score.threshold == 0.8
        assert score.passed is False

    def test_create_score_with_exact_threshold(self):
        """Test creating a score that exactly meets the threshold."""
        score = EvalScore(name="accuracy", value=0.8, threshold=0.8)

        assert score.passed is True

    def test_invalid_score_value_too_high(self):
        """Test that score value > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            EvalScore(name="accuracy", value=1.5)

    def test_invalid_score_value_too_low(self):
        """Test that score value < 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            EvalScore(name="accuracy", value=-0.1)

    def test_invalid_threshold_too_high(self):
        """Test that threshold > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Threshold must be between 0.0 and 1.0"):
            EvalScore(name="accuracy", value=0.5, threshold=1.5)

    def test_invalid_threshold_too_low(self):
        """Test that threshold < 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="Threshold must be between 0.0 and 1.0"):
            EvalScore(name="accuracy", value=0.5, threshold=-0.1)

    def test_to_dict(self):
        """Test converting score to dictionary."""
        score = EvalScore(name="accuracy", value=0.85, threshold=0.8)
        score_dict = score.to_dict()

        assert score_dict == {
            "name": "accuracy",
            "value": 0.85,
            "threshold": 0.8,
            "passed": True,
        }

    def test_boundary_values(self):
        """Test boundary values 0.0 and 1.0."""
        score_min = EvalScore(name="min", value=0.0)
        score_max = EvalScore(name="max", value=1.0)

        assert score_min.value == 0.0
        assert score_max.value == 1.0


class TestEvalResult:
    """Tests for EvalResult dataclass."""

    def test_create_result_with_single_score(self):
        """Test creating a result with a single score."""
        score = EvalScore(name="accuracy", value=0.85)
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores={"accuracy": score},
        )

        assert result.evaluator_name == "test_evaluator"
        assert "accuracy" in result.scores
        assert result.scores["accuracy"] == score
        assert result.feedback is None
        assert result.metadata == {}
        assert isinstance(result.timestamp, datetime)

    def test_create_result_with_multiple_scores(self):
        """Test creating a result with multiple scores."""
        scores = {
            "accuracy": EvalScore(name="accuracy", value=0.85),
            "completeness": EvalScore(name="completeness", value=0.92),
        }
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores=scores,
        )

        assert len(result.scores) == 2
        assert "accuracy" in result.scores
        assert "completeness" in result.scores

    def test_create_result_with_feedback(self):
        """Test creating a result with feedback."""
        score = EvalScore(name="accuracy", value=0.85)
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores={"accuracy": score},
            feedback="Excellent performance",
        )

        assert result.feedback == "Excellent performance"

    def test_create_result_with_metadata(self):
        """Test creating a result with metadata."""
        score = EvalScore(name="accuracy", value=0.85)
        metadata = {"model": "gpt-4", "temperature": 0.7}
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores={"accuracy": score},
            metadata=metadata,
        )

        assert result.metadata == metadata

    def test_empty_scores_raises_error(self):
        """Test that empty scores dict raises ValueError."""
        with pytest.raises(ValueError, match="must contain at least one score"):
            EvalResult(
                evaluator_name="test_evaluator",
                scores={},
            )

    def test_get_score_existing(self):
        """Test getting an existing score."""
        score = EvalScore(name="accuracy", value=0.85)
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores={"accuracy": score},
        )

        retrieved_score = result.get_score("accuracy")
        assert retrieved_score == score

    def test_get_score_nonexistent(self):
        """Test getting a nonexistent score returns None."""
        score = EvalScore(name="accuracy", value=0.85)
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores={"accuracy": score},
        )

        retrieved_score = result.get_score("nonexistent")
        assert retrieved_score is None

    def test_all_passed_with_no_thresholds(self):
        """Test all_passed returns True when no scores have thresholds."""
        scores = {
            "accuracy": EvalScore(name="accuracy", value=0.85),
            "completeness": EvalScore(name="completeness", value=0.92),
        }
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores=scores,
        )

        assert result.all_passed() is True

    def test_all_passed_with_all_passing(self):
        """Test all_passed returns True when all scores pass thresholds."""
        scores = {
            "accuracy": EvalScore(name="accuracy", value=0.85, threshold=0.8),
            "completeness": EvalScore(name="completeness", value=0.92, threshold=0.9),
        }
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores=scores,
        )

        assert result.all_passed() is True

    def test_all_passed_with_one_failing(self):
        """Test all_passed returns False when one score fails threshold."""
        scores = {
            "accuracy": EvalScore(name="accuracy", value=0.85, threshold=0.8),
            "completeness": EvalScore(name="completeness", value=0.75, threshold=0.9),
        }
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores=scores,
        )

        assert result.all_passed() is False

    def test_all_passed_mixed_thresholds(self):
        """Test all_passed with mix of scores with and without thresholds."""
        scores = {
            "accuracy": EvalScore(name="accuracy", value=0.85, threshold=0.8),
            "completeness": EvalScore(name="completeness", value=0.50),  # No threshold
        }
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores=scores,
        )

        # Should only consider score with threshold
        assert result.all_passed() is True

    def test_to_dict(self):
        """Test converting result to dictionary."""
        score = EvalScore(name="accuracy", value=0.85, threshold=0.8)
        metadata = {"model": "gpt-4"}
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores={"accuracy": score},
            feedback="Good job",
            metadata=metadata,
        )

        result_dict = result.to_dict()

        assert result_dict["evaluator_name"] == "test_evaluator"
        assert "accuracy" in result_dict["scores"]
        assert result_dict["feedback"] == "Good job"
        assert result_dict["metadata"] == metadata
        assert "timestamp" in result_dict


class TestEvalSummary:
    """Tests for EvalSummary dataclass."""

    def test_create_summary_with_single_result(self):
        """Test creating a summary with a single result."""
        score = EvalScore(name="accuracy", value=0.85, threshold=0.8)
        result = EvalResult(
            evaluator_name="test_evaluator",
            scores={"accuracy": score},
        )
        summary = EvalSummary(results=[result])

        assert summary.total_evaluators == 1
        assert summary.passed_evaluators == 1
        assert summary.failed_evaluators == 0

    def test_create_summary_with_multiple_results(self):
        """Test creating a summary with multiple results."""
        result1 = EvalResult(
            evaluator_name="eval1",
            scores={"accuracy": EvalScore(name="accuracy", value=0.85, threshold=0.8)},
        )
        result2 = EvalResult(
            evaluator_name="eval2",
            scores={"completeness": EvalScore(name="completeness", value=0.75, threshold=0.9)},
        )
        result3 = EvalResult(
            evaluator_name="eval3",
            scores={"quality": EvalScore(name="quality", value=0.95, threshold=0.7)},
        )

        summary = EvalSummary(results=[result1, result2, result3])

        assert summary.total_evaluators == 3
        assert summary.passed_evaluators == 2
        assert summary.failed_evaluators == 1

    def test_average_scores(self):
        """Test that average scores are computed correctly."""
        result1 = EvalResult(
            evaluator_name="eval1",
            scores={"accuracy": EvalScore(name="accuracy", value=0.8)},
        )
        result2 = EvalResult(
            evaluator_name="eval2",
            scores={"accuracy": EvalScore(name="accuracy", value=0.9)},
        )
        result3 = EvalResult(
            evaluator_name="eval3",
            scores={"accuracy": EvalScore(name="accuracy", value=1.0)},
        )

        summary = EvalSummary(results=[result1, result2, result3])

        assert "accuracy" in summary.average_scores
        assert summary.average_scores["accuracy"] == 0.9

    def test_average_scores_multiple_metrics(self):
        """Test average scores with multiple different metrics."""
        result1 = EvalResult(
            evaluator_name="eval1",
            scores={
                "accuracy": EvalScore(name="accuracy", value=0.8),
                "completeness": EvalScore(name="completeness", value=0.7),
            },
        )
        result2 = EvalResult(
            evaluator_name="eval2",
            scores={
                "accuracy": EvalScore(name="accuracy", value=0.9),
                "quality": EvalScore(name="quality", value=0.85),
            },
        )

        summary = EvalSummary(results=[result1, result2])

        assert summary.average_scores["accuracy"] == 0.85
        assert summary.average_scores["completeness"] == 0.7
        assert summary.average_scores["quality"] == 0.85

    def test_pass_rate(self):
        """Test pass rate calculation."""
        result1 = EvalResult(
            evaluator_name="eval1",
            scores={"accuracy": EvalScore(name="accuracy", value=0.85, threshold=0.8)},
        )
        result2 = EvalResult(
            evaluator_name="eval2",
            scores={"completeness": EvalScore(name="completeness", value=0.75, threshold=0.9)},
        )
        result3 = EvalResult(
            evaluator_name="eval3",
            scores={"quality": EvalScore(name="quality", value=0.95, threshold=0.7)},
        )

        summary = EvalSummary(results=[result1, result2, result3])

        # 2 out of 3 passed
        assert summary.pass_rate == pytest.approx(0.666, rel=0.01)

    def test_pass_rate_empty_results(self):
        """Test pass rate with no results."""
        summary = EvalSummary(results=[])

        assert summary.pass_rate == 0.0

    def test_get_failed_results(self):
        """Test getting failed results."""
        result1 = EvalResult(
            evaluator_name="eval1",
            scores={"accuracy": EvalScore(name="accuracy", value=0.85, threshold=0.8)},
        )
        result2 = EvalResult(
            evaluator_name="eval2",
            scores={"completeness": EvalScore(name="completeness", value=0.75, threshold=0.9)},
        )

        summary = EvalSummary(results=[result1, result2])
        failed = summary.get_failed_results()

        assert len(failed) == 1
        assert failed[0].evaluator_name == "eval2"

    def test_get_passed_results(self):
        """Test getting passed results."""
        result1 = EvalResult(
            evaluator_name="eval1",
            scores={"accuracy": EvalScore(name="accuracy", value=0.85, threshold=0.8)},
        )
        result2 = EvalResult(
            evaluator_name="eval2",
            scores={"completeness": EvalScore(name="completeness", value=0.75, threshold=0.9)},
        )

        summary = EvalSummary(results=[result1, result2])
        passed = summary.get_passed_results()

        assert len(passed) == 1
        assert passed[0].evaluator_name == "eval1"

    def test_to_dict(self):
        """Test converting summary to dictionary."""
        result = EvalResult(
            evaluator_name="eval1",
            scores={"accuracy": EvalScore(name="accuracy", value=0.85, threshold=0.8)},
        )
        summary = EvalSummary(results=[result])

        summary_dict = summary.to_dict()

        assert summary_dict["total_evaluators"] == 1
        assert summary_dict["passed_evaluators"] == 1
        assert summary_dict["failed_evaluators"] == 0
        assert "pass_rate" in summary_dict
        assert "average_scores" in summary_dict
        assert "results" in summary_dict
