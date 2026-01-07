"""Tests for evaluation runner."""

import pytest
import asyncio
from datetime import datetime, timedelta
from agenttrace.evals.runner import (
    RunnerConfig,
    TraceEvaluation,
    BatchSummary,
    BatchEvaluation,
    Regression,
    Improvement,
    Comparison,
    EvaluationRunner,
)
from agenttrace.evals.base import Evaluator, Trace
from agenttrace.evals.models import EvalResult, EvalScore


# Test evaluators
class MockEvaluator(Evaluator):
    """Mock evaluator for testing."""

    def __init__(self, name: str, score: float = 0.8, delay: float = 0.0):
        self._name = name
        self._score = score
        self._delay = delay

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Mock evaluator: {self._name}"

    async def evaluate(self, trace: Trace) -> EvalResult:
        if self._delay > 0:
            await asyncio.sleep(self._delay)

        return EvalResult(
            evaluator_name=self._name,
            scores={
                self._name: EvalScore(
                    name=self._name, value=self._score, threshold=0.7
                )
            },
            feedback=f"Mock feedback from {self._name}",
        )


class FailingEvaluator(Evaluator):
    """Evaluator that always fails."""

    @property
    def name(self) -> str:
        return "failing"

    @property
    def description(self) -> str:
        return "Always fails"

    async def evaluate(self, trace: Trace) -> EvalResult:
        raise ValueError("Evaluation failed")


class TestRunnerConfig:
    """Tests for RunnerConfig."""

    def test_create_default_config(self):
        """Test creating default configuration."""
        config = RunnerConfig()

        assert config.max_concurrency == 10
        assert config.timeout_per_trace_seconds == 60
        assert config.continue_on_error is True
        assert config.required_evaluators == []
        assert config.score_weights is None

    def test_create_custom_config(self):
        """Test creating custom configuration."""
        config = RunnerConfig(
            max_concurrency=5,
            timeout_per_trace_seconds=30,
            continue_on_error=False,
            required_evaluators=["completeness"],
            score_weights={"completeness": 2.0},
        )

        assert config.max_concurrency == 5
        assert config.timeout_per_trace_seconds == 30
        assert config.continue_on_error is False
        assert config.required_evaluators == ["completeness"]
        assert config.score_weights == {"completeness": 2.0}

    def test_invalid_max_concurrency(self):
        """Test that invalid max_concurrency raises error."""
        with pytest.raises(ValueError, match="max_concurrency must be at least 1"):
            RunnerConfig(max_concurrency=0)

    def test_invalid_timeout(self):
        """Test that invalid timeout raises error."""
        with pytest.raises(
            ValueError, match="timeout_per_trace_seconds must be at least 1"
        ):
            RunnerConfig(timeout_per_trace_seconds=0)


class TestTraceEvaluation:
    """Tests for TraceEvaluation."""

    def test_create_trace_evaluation(self):
        """Test creating trace evaluation."""
        result = EvalResult(
            evaluator_name="test",
            scores={"test": EvalScore("test", 0.8)},
        )

        evaluation = TraceEvaluation(
            trace_id="trace-123",
            results=[result],
            overall_score=0.8,
            passed=True,
            duration_ms=1000,
        )

        assert evaluation.trace_id == "trace-123"
        assert len(evaluation.results) == 1
        assert evaluation.overall_score == 0.8
        assert evaluation.passed is True
        assert evaluation.duration_ms == 1000
        assert evaluation.errors == []

    def test_get_result(self):
        """Test getting result by evaluator name."""
        result1 = EvalResult(
            evaluator_name="eval1", scores={"score1": EvalScore("score1", 0.8)}
        )
        result2 = EvalResult(
            evaluator_name="eval2", scores={"score2": EvalScore("score2", 0.9)}
        )

        evaluation = TraceEvaluation(
            trace_id="trace-123",
            results=[result1, result2],
            overall_score=0.85,
            passed=True,
            duration_ms=1000,
        )

        assert evaluation.get_result("eval1") == result1
        assert evaluation.get_result("eval2") == result2
        assert evaluation.get_result("eval3") is None

    def test_get_scores(self):
        """Test getting all scores."""
        result1 = EvalResult(
            evaluator_name="eval1", scores={"score1": EvalScore("score1", 0.8)}
        )
        result2 = EvalResult(
            evaluator_name="eval2",
            scores={
                "score2": EvalScore("score2", 0.9),
                "score3": EvalScore("score3", 0.7),
            },
        )

        evaluation = TraceEvaluation(
            trace_id="trace-123",
            results=[result1, result2],
            overall_score=0.8,
            passed=True,
            duration_ms=1000,
        )

        scores = evaluation.get_scores()

        assert scores == {"score1": 0.8, "score2": 0.9, "score3": 0.7}

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = EvalResult(
            evaluator_name="test", scores={"test": EvalScore("test", 0.8)}
        )

        evaluation = TraceEvaluation(
            trace_id="trace-123",
            results=[result],
            overall_score=0.8,
            passed=True,
            duration_ms=1000,
        )

        data = evaluation.to_dict()

        assert data["trace_id"] == "trace-123"
        assert data["overall_score"] == 0.8
        assert data["passed"] is True
        assert data["duration_ms"] == 1000


class TestBatchSummary:
    """Tests for BatchSummary."""

    def test_create_batch_summary(self):
        """Test creating batch summary."""
        summary = BatchSummary(
            total_traces=100,
            passed_traces=95,
            failed_traces=5,
            error_traces=0,
            average_scores={"score1": 0.85, "score2": 0.90},
            score_distributions={"score1": [0.8, 0.9], "score2": [0.85, 0.95]},
            average_duration_ms=1500.0,
        )

        assert summary.total_traces == 100
        assert summary.passed_traces == 95
        assert summary.failed_traces == 5
        assert summary.error_traces == 0

    def test_pass_rate_calculation(self):
        """Test pass rate calculation."""
        summary = BatchSummary(
            total_traces=100,
            passed_traces=80,
            failed_traces=20,
            error_traces=0,
            average_scores={},
            score_distributions={},
            average_duration_ms=1000.0,
        )

        assert summary.pass_rate == 0.8

    def test_pass_rate_zero_traces(self):
        """Test pass rate with zero traces."""
        summary = BatchSummary(
            total_traces=0,
            passed_traces=0,
            failed_traces=0,
            error_traces=0,
            average_scores={},
            score_distributions={},
            average_duration_ms=0.0,
        )

        assert summary.pass_rate == 0.0

    def test_to_dict(self):
        """Test converting to dictionary."""
        summary = BatchSummary(
            total_traces=100,
            passed_traces=95,
            failed_traces=5,
            error_traces=0,
            average_scores={"score1": 0.85},
            score_distributions={"score1": [0.8, 0.9]},
            average_duration_ms=1500.0,
        )

        data = summary.to_dict()

        assert data["total_traces"] == 100
        assert data["pass_rate"] == 0.95


class TestBatchEvaluation:
    """Tests for BatchEvaluation."""

    def test_create_batch_evaluation(self):
        """Test creating batch evaluation."""
        evaluation = TraceEvaluation(
            trace_id="trace-1",
            results=[],
            overall_score=0.8,
            passed=True,
            duration_ms=1000,
        )

        summary = BatchSummary(
            total_traces=1,
            passed_traces=1,
            failed_traces=0,
            error_traces=0,
            average_scores={},
            score_distributions={},
            average_duration_ms=1000.0,
        )

        started = datetime.utcnow()
        completed = started + timedelta(seconds=5)

        batch = BatchEvaluation(
            evaluations=[evaluation],
            summary=summary,
            started_at=started,
            completed_at=completed,
        )

        assert len(batch.evaluations) == 1
        assert batch.duration_seconds == pytest.approx(5.0, abs=0.1)

    def test_get_evaluation(self):
        """Test getting evaluation by trace ID."""
        eval1 = TraceEvaluation(
            trace_id="trace-1",
            results=[],
            overall_score=0.8,
            passed=True,
            duration_ms=1000,
        )
        eval2 = TraceEvaluation(
            trace_id="trace-2",
            results=[],
            overall_score=0.9,
            passed=True,
            duration_ms=1000,
        )

        summary = BatchSummary(
            total_traces=2,
            passed_traces=2,
            failed_traces=0,
            error_traces=0,
            average_scores={},
            score_distributions={},
            average_duration_ms=1000.0,
        )

        batch = BatchEvaluation(
            evaluations=[eval1, eval2],
            summary=summary,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        assert batch.get_evaluation("trace-1") == eval1
        assert batch.get_evaluation("trace-2") == eval2
        assert batch.get_evaluation("trace-3") is None

    def test_to_dict(self):
        """Test converting to dictionary."""
        evaluation = TraceEvaluation(
            trace_id="trace-1",
            results=[],
            overall_score=0.8,
            passed=True,
            duration_ms=1000,
        )

        summary = BatchSummary(
            total_traces=1,
            passed_traces=1,
            failed_traces=0,
            error_traces=0,
            average_scores={},
            score_distributions={},
            average_duration_ms=1000.0,
        )

        batch = BatchEvaluation(
            evaluations=[evaluation],
            summary=summary,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        data = batch.to_dict()

        assert "evaluations" in data
        assert "summary" in data
        assert "duration_seconds" in data


class TestRegression:
    """Tests for Regression."""

    def test_create_regression(self):
        """Test creating regression."""
        regression = Regression(
            evaluator="completeness",
            score_name="completeness",
            baseline_score=0.9,
            current_score=0.7,
            delta=-0.2,
            trace_id="trace-123",
        )

        assert regression.evaluator == "completeness"
        assert regression.delta == -0.2

    def test_percent_change(self):
        """Test percent change calculation."""
        regression = Regression(
            evaluator="completeness",
            score_name="completeness",
            baseline_score=0.9,
            current_score=0.7,
            delta=-0.2,
            trace_id="trace-123",
        )

        # -0.2 / 0.9 * 100 = -22.22%
        assert regression.percent_change == pytest.approx(-22.22, abs=0.01)

    def test_percent_change_zero_baseline(self):
        """Test percent change with zero baseline."""
        regression = Regression(
            evaluator="test",
            score_name="test",
            baseline_score=0.0,
            current_score=0.5,
            delta=0.5,
            trace_id="trace-123",
        )

        assert regression.percent_change == 0.0


class TestImprovement:
    """Tests for Improvement."""

    def test_create_improvement(self):
        """Test creating improvement."""
        improvement = Improvement(
            evaluator="completeness",
            score_name="completeness",
            baseline_score=0.7,
            current_score=0.9,
            delta=0.2,
            trace_id="trace-123",
        )

        assert improvement.evaluator == "completeness"
        assert improvement.delta == 0.2

    def test_percent_change(self):
        """Test percent change calculation."""
        improvement = Improvement(
            evaluator="completeness",
            score_name="completeness",
            baseline_score=0.7,
            current_score=0.9,
            delta=0.2,
            trace_id="trace-123",
        )

        # 0.2 / 0.7 * 100 = 28.57%
        assert improvement.percent_change == pytest.approx(28.57, abs=0.01)


class TestComparison:
    """Tests for Comparison."""

    def test_create_comparison(self):
        """Test creating comparison."""
        regression = Regression(
            evaluator="test",
            score_name="test",
            baseline_score=0.9,
            current_score=0.7,
            delta=-0.2,
            trace_id="trace-123",
        )

        comparison = Comparison(
            regressions=[regression],
            improvements=[],
            unchanged=[],
            statistical_summary={},
        )

        assert len(comparison.regressions) == 1
        assert comparison.has_regressions is True

    def test_no_regressions(self):
        """Test comparison with no regressions."""
        comparison = Comparison(
            regressions=[],
            improvements=[],
            unchanged=["test"],
            statistical_summary={},
        )

        assert comparison.has_regressions is False

    def test_to_dict(self):
        """Test converting to dictionary."""
        regression = Regression(
            evaluator="test",
            score_name="test",
            baseline_score=0.9,
            current_score=0.7,
            delta=-0.2,
            trace_id="trace-123",
        )

        comparison = Comparison(
            regressions=[regression],
            improvements=[],
            unchanged=[],
            statistical_summary={"mean_change": -0.05},
        )

        data = comparison.to_dict()

        assert len(data["regressions"]) == 1
        assert data["statistical_summary"]["mean_change"] == -0.05


class TestEvaluationRunner:
    """Tests for EvaluationRunner."""

    @pytest.mark.asyncio
    async def test_create_runner_with_evaluators(self):
        """Test creating runner with evaluator instances."""
        eval1 = MockEvaluator("eval1")
        eval2 = MockEvaluator("eval2")

        runner = EvaluationRunner(evaluators=[eval1, eval2])

        assert len(runner._evaluators) == 2

    @pytest.mark.asyncio
    async def test_evaluate_trace_basic(self):
        """Test basic trace evaluation."""
        eval1 = MockEvaluator("eval1", score=0.8)
        eval2 = MockEvaluator("eval2", score=0.9)

        runner = EvaluationRunner(evaluators=[eval1, eval2])

        trace = Trace(trace_id="trace-123", spans=[])
        result = await runner.evaluate_trace(trace)

        assert result.trace_id == "trace-123"
        assert len(result.results) == 2
        assert result.passed is True
        assert result.overall_score > 0

    @pytest.mark.asyncio
    async def test_evaluate_trace_parallel_execution(self):
        """Test that evaluations run in parallel."""
        # Each evaluator delays 0.1 seconds
        eval1 = MockEvaluator("eval1", delay=0.1)
        eval2 = MockEvaluator("eval2", delay=0.1)
        eval3 = MockEvaluator("eval3", delay=0.1)

        runner = EvaluationRunner(evaluators=[eval1, eval2, eval3])

        trace = Trace(trace_id="trace-123", spans=[])

        import time

        start = time.time()
        result = await runner.evaluate_trace(trace)
        duration = time.time() - start

        # Should take ~0.1s (parallel), not 0.3s (sequential)
        assert duration < 0.2
        assert len(result.results) == 3

    @pytest.mark.asyncio
    async def test_evaluate_trace_with_error(self):
        """Test evaluation with failing evaluator."""
        eval1 = MockEvaluator("eval1")
        eval2 = FailingEvaluator()

        runner = EvaluationRunner(evaluators=[eval1, eval2])

        trace = Trace(trace_id="trace-123", spans=[])
        result = await runner.evaluate_trace(trace)

        # Should have 1 result and 1 error
        assert len(result.results) == 1
        assert len(result.errors) == 1
        assert result.errors[0]["evaluator"] == "failing"

    @pytest.mark.asyncio
    async def test_evaluate_trace_timeout(self):
        """Test evaluation timeout."""
        # Evaluator that takes too long
        eval1 = MockEvaluator("eval1", delay=5.0)

        config = RunnerConfig(timeout_per_trace_seconds=1)
        runner = EvaluationRunner(evaluators=[eval1], config=config)

        trace = Trace(trace_id="trace-123", spans=[])
        result = await runner.evaluate_trace(trace)

        # Should have timeout error
        assert len(result.errors) == 1
        assert "timed out" in result.errors[0]["error"].lower()

    @pytest.mark.asyncio
    async def test_weighted_scoring(self):
        """Test weighted score calculation."""
        eval1 = MockEvaluator("eval1", score=0.6)
        eval2 = MockEvaluator("eval2", score=1.0)

        # Weight eval2 higher
        config = RunnerConfig(score_weights={"eval1": 1.0, "eval2": 3.0})
        runner = EvaluationRunner(evaluators=[eval1, eval2], config=config)

        trace = Trace(trace_id="trace-123", spans=[])
        result = await runner.evaluate_trace(trace)

        # Weighted average: (0.6 * 1 + 1.0 * 3) / (1 + 3) = 3.6 / 4 = 0.9
        assert result.overall_score == pytest.approx(0.9, abs=0.01)

    @pytest.mark.asyncio
    async def test_required_evaluators_pass(self):
        """Test required evaluators - passing case."""
        eval1 = MockEvaluator("eval1", score=0.8)
        eval2 = MockEvaluator("eval2", score=0.9)

        config = RunnerConfig(required_evaluators=["eval1"])
        runner = EvaluationRunner(evaluators=[eval1, eval2], config=config)

        trace = Trace(trace_id="trace-123", spans=[])
        result = await runner.evaluate_trace(trace)

        assert result.passed is True

    @pytest.mark.asyncio
    async def test_required_evaluators_fail(self):
        """Test required evaluators - failing case."""
        eval1 = MockEvaluator("eval1", score=0.5)  # Below threshold
        eval2 = MockEvaluator("eval2", score=0.9)

        config = RunnerConfig(required_evaluators=["eval1"])
        runner = EvaluationRunner(evaluators=[eval1, eval2], config=config)

        trace = Trace(trace_id="trace-123", spans=[])
        result = await runner.evaluate_trace(trace)

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_required_evaluator_error(self):
        """Test required evaluator with error."""
        eval1 = FailingEvaluator()

        config = RunnerConfig(required_evaluators=["failing"])
        runner = EvaluationRunner(evaluators=[eval1], config=config)

        trace = Trace(trace_id="trace-123", spans=[])
        result = await runner.evaluate_trace(trace)

        assert result.passed is False

    @pytest.mark.asyncio
    async def test_evaluate_batch_basic(self):
        """Test basic batch evaluation."""
        eval1 = MockEvaluator("eval1")

        runner = EvaluationRunner(evaluators=[eval1])

        traces = [
            Trace(trace_id="trace-1", spans=[]),
            Trace(trace_id="trace-2", spans=[]),
            Trace(trace_id="trace-3", spans=[]),
        ]

        batch = await runner.evaluate_batch(traces)

        assert len(batch.evaluations) == 3
        assert batch.summary.total_traces == 3
        assert batch.summary.passed_traces == 3

    @pytest.mark.asyncio
    async def test_evaluate_batch_progress_callback(self):
        """Test batch evaluation with progress callback."""
        eval1 = MockEvaluator("eval1")
        runner = EvaluationRunner(evaluators=[eval1])

        traces = [
            Trace(trace_id="trace-1", spans=[]),
            Trace(trace_id="trace-2", spans=[]),
        ]

        progress_calls = []

        def progress(completed, total):
            progress_calls.append((completed, total))

        batch = await runner.evaluate_batch(traces, progress_callback=progress)

        assert len(progress_calls) == 2
        assert progress_calls[0] == (1, 2)
        assert progress_calls[1] == (2, 2)

    @pytest.mark.asyncio
    async def test_evaluate_batch_continue_on_error(self):
        """Test batch evaluation with continue_on_error."""
        eval1 = MockEvaluator("eval1")

        runner = EvaluationRunner(evaluators=[eval1])

        # Create traces where one will cause an error
        traces = [
            Trace(trace_id="trace-1", spans=[]),
            Trace(trace_id="trace-2", spans=[]),
        ]

        # Make eval1 fail for second trace
        original_evaluate = eval1.evaluate

        async def failing_evaluate(trace):
            if trace.trace_id == "trace-2":
                raise ValueError("Test error")
            return await original_evaluate(trace)

        eval1.evaluate = failing_evaluate

        batch = await runner.evaluate_batch(traces)

        # Should have both traces, one with error
        assert len(batch.evaluations) == 2
        assert batch.summary.error_traces == 1

    @pytest.mark.asyncio
    async def test_evaluate_batch_stop_on_error(self):
        """Test batch evaluation stops on error when configured."""
        eval1 = MockEvaluator("eval1")

        config = RunnerConfig(continue_on_error=False)
        runner = EvaluationRunner(evaluators=[eval1], config=config)

        traces = [
            Trace(trace_id="trace-1", spans=[]),
            Trace(trace_id="trace-2", spans=[]),
        ]

        # Make eval1 fail for first trace
        original_evaluate = eval1.evaluate

        async def failing_evaluate(trace):
            if trace.trace_id == "trace-1":
                raise ValueError("Test error")
            return await original_evaluate(trace)

        eval1.evaluate = failing_evaluate

        with pytest.raises(ValueError, match="Test error"):
            await runner.evaluate_batch(traces)

    @pytest.mark.asyncio
    async def test_batch_summary_calculation(self):
        """Test batch summary statistics calculation."""
        eval1 = MockEvaluator("eval1", score=0.8)
        eval2 = MockEvaluator("eval2", score=0.9)

        runner = EvaluationRunner(evaluators=[eval1, eval2])

        traces = [
            Trace(trace_id="trace-1", spans=[]),
            Trace(trace_id="trace-2", spans=[]),
        ]

        batch = await runner.evaluate_batch(traces)

        # Check summary
        assert batch.summary.total_traces == 2
        assert batch.summary.passed_traces == 2
        assert "eval1" in batch.summary.average_scores
        assert "eval2" in batch.summary.average_scores
        assert batch.summary.average_scores["eval1"] == 0.8
        assert batch.summary.average_scores["eval2"] == 0.9

    @pytest.mark.asyncio
    async def test_compare_to_baseline_no_changes(self):
        """Test baseline comparison with no changes."""
        eval1 = MockEvaluator("eval1", score=0.8)
        runner = EvaluationRunner(evaluators=[eval1])

        traces = [Trace(trace_id="trace-1", spans=[])]

        baseline = await runner.evaluate_batch(traces)
        current = await runner.evaluate_batch(traces)

        comparison = await runner.compare_to_baseline(current, baseline)

        assert len(comparison.regressions) == 0
        assert len(comparison.improvements) == 0
        assert len(comparison.unchanged) > 0

    @pytest.mark.asyncio
    async def test_compare_to_baseline_regression(self):
        """Test baseline comparison with regression."""
        eval1 = MockEvaluator("eval1", score=0.9)
        runner = EvaluationRunner(evaluators=[eval1])

        traces = [Trace(trace_id="trace-1", spans=[])]

        baseline = await runner.evaluate_batch(traces)

        # Change score for current
        eval1._score = 0.7
        current = await runner.evaluate_batch(traces)

        comparison = await runner.compare_to_baseline(
            current, baseline, regression_threshold=0.05
        )

        # Should detect regression (0.9 -> 0.7 = -0.2)
        assert len(comparison.regressions) > 0
        assert comparison.has_regressions is True

    @pytest.mark.asyncio
    async def test_compare_to_baseline_improvement(self):
        """Test baseline comparison with improvement."""
        eval1 = MockEvaluator("eval1", score=0.7)
        runner = EvaluationRunner(evaluators=[eval1])

        traces = [Trace(trace_id="trace-1", spans=[])]

        baseline = await runner.evaluate_batch(traces)

        # Change score for current
        eval1._score = 0.9
        current = await runner.evaluate_batch(traces)

        comparison = await runner.compare_to_baseline(
            current, baseline, regression_threshold=0.05
        )

        # Should detect improvement (0.7 -> 0.9 = +0.2)
        assert len(comparison.improvements) > 0

    @pytest.mark.asyncio
    async def test_compare_statistical_summary(self):
        """Test statistical summary in comparison."""
        eval1 = MockEvaluator("eval1", score=0.9)
        runner = EvaluationRunner(evaluators=[eval1])

        traces = [Trace(trace_id="trace-1", spans=[])]

        baseline = await runner.evaluate_batch(traces)

        eval1._score = 0.7
        current = await runner.evaluate_batch(traces)

        comparison = await runner.compare_to_baseline(current, baseline)

        summary = comparison.statistical_summary

        assert "regression_count" in summary
        assert "improvement_count" in summary
        assert "mean_score_change" in summary
        assert "current_pass_rate" in summary
        assert "baseline_pass_rate" in summary

    @pytest.mark.asyncio
    async def test_concurrency_control(self):
        """Test that concurrency is limited by semaphore."""
        eval1 = MockEvaluator("eval1", delay=0.1)

        # Limit concurrency to 2
        config = RunnerConfig(max_concurrency=2)
        runner = EvaluationRunner(evaluators=[eval1], config=config)

        # Create 5 traces
        traces = [Trace(trace_id=f"trace-{i}", spans=[]) for i in range(5)]

        batch = await runner.evaluate_batch(traces)

        # All should succeed
        assert len(batch.evaluations) == 5

    @pytest.mark.asyncio
    async def test_runner_duration_tracking(self):
        """Test that durations are tracked correctly."""
        eval1 = MockEvaluator("eval1")
        runner = EvaluationRunner(evaluators=[eval1])

        trace = Trace(trace_id="trace-1", spans=[])

        result = await runner.evaluate_trace(trace)

        # Duration should be tracked
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_batch_duration_tracking(self):
        """Test that batch duration is tracked."""
        eval1 = MockEvaluator("eval1")
        runner = EvaluationRunner(evaluators=[eval1])

        traces = [Trace(trace_id="trace-1", spans=[])]

        batch = await runner.evaluate_batch(traces)

        # Duration should be positive
        assert batch.duration_seconds >= 0
