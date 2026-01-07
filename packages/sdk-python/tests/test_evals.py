"""Tests for evaluation framework"""

import pytest
from agenttrace.evals import (
    LatencyEvaluator,
    TokenUsageEvaluator,
    ErrorRateEvaluator,
    CostEvaluator,
    CustomEvaluator,
    AccuracyEvaluator,
)
from agenttrace.evals.models import (
    EvaluationScore,
    ScoreType,
    MetricType,
    CustomEvaluatorConfig,
)
from agenttrace.evals.runner import EvaluationRunner


def test_latency_evaluator_pass():
    """Test latency evaluator with passing threshold"""
    evaluator = LatencyEvaluator(threshold_ms=1000)
    trace_data = {"duration": 0.5}  # 500ms

    metric = evaluator.evaluate(trace_data)

    assert metric.name == "latency"
    assert metric.metric_type == MetricType.LATENCY
    assert metric.score.value == 500.0
    assert metric.score.passed is True


def test_latency_evaluator_fail():
    """Test latency evaluator with failing threshold"""
    evaluator = LatencyEvaluator(threshold_ms=100)
    trace_data = {"duration": 0.5}  # 500ms

    metric = evaluator.evaluate(trace_data)

    assert metric.score.value == 500.0
    assert metric.score.passed is False


def test_token_usage_evaluator():
    """Test token usage evaluator"""
    evaluator = TokenUsageEvaluator(max_tokens=1000)
    trace_data = {
        "metadata": {
            "total_tokens": 500,
            "prompt_tokens": 300,
            "completion_tokens": 200,
        }
    }

    metric = evaluator.evaluate(trace_data)

    assert metric.name == "token_usage"
    assert metric.score.value == 500
    assert metric.score.passed is True
    assert metric.metadata["total_tokens"] == 500


def test_error_rate_evaluator_no_error():
    """Test error rate evaluator with no errors"""
    evaluator = ErrorRateEvaluator(max_error_rate=0.0)
    trace_data = {"status": "completed"}

    metric = evaluator.evaluate(trace_data)

    assert metric.score.value == 0.0
    assert metric.score.passed is True


def test_error_rate_evaluator_with_error():
    """Test error rate evaluator with error"""
    evaluator = ErrorRateEvaluator(max_error_rate=0.0)
    trace_data = {"status": "error", "error": {"message": "Test error"}}

    metric = evaluator.evaluate(trace_data)

    assert metric.score.value == 1.0
    assert metric.score.passed is False


def test_cost_evaluator():
    """Test cost evaluator"""
    evaluator = CostEvaluator(max_cost_usd=0.10)
    trace_data = {"metadata": {"cost_usd": 0.05}}

    metric = evaluator.evaluate(trace_data)

    assert metric.score.value == 0.05
    assert metric.score.passed is True


def test_custom_evaluator():
    """Test custom evaluator"""

    def custom_fn(trace_data):
        value = trace_data.get("custom_value", 0)
        return EvaluationScore(
            value=value,
            score_type=ScoreType.NUMERIC,
        )

    config = CustomEvaluatorConfig(
        name="custom_test",
        evaluator_fn=custom_fn,
        threshold=50.0,
    )

    evaluator = CustomEvaluator(config)
    trace_data = {"custom_value": 75}

    metric = evaluator.evaluate(trace_data)

    assert metric.name == "custom_test"
    assert metric.score.value == 75
    assert metric.score.passed is True


def test_accuracy_evaluator_exact_match():
    """Test accuracy evaluator with exact match"""
    evaluator = AccuracyEvaluator(threshold=1.0)
    trace_data = {
        "metadata": {
            "actual_output": "Hello, World!",
            "expected_output": "Hello, World!",
        }
    }

    metric = evaluator.evaluate(trace_data)

    assert metric.score.value == 1.0
    assert metric.score.passed is True


def test_accuracy_evaluator_no_match():
    """Test accuracy evaluator with no match"""
    evaluator = AccuracyEvaluator(threshold=1.0)
    trace_data = {
        "metadata": {
            "actual_output": "Hello",
            "expected_output": "Goodbye",
        }
    }

    metric = evaluator.evaluate(trace_data)

    assert metric.score.value == 0.0
    assert metric.score.passed is False


def test_evaluation_runner():
    """Test evaluation runner with multiple evaluators"""
    evaluators = [
        LatencyEvaluator(threshold_ms=1000),
        TokenUsageEvaluator(max_tokens=1000),
        ErrorRateEvaluator(max_error_rate=0.0),
    ]

    runner = EvaluationRunner(evaluators=evaluators, auto_submit=False)

    trace_data = {
        "trace_id": "test_trace_123",
        "duration": 0.5,
        "status": "completed",
        "metadata": {
            "total_tokens": 500,
            "prompt_tokens": 300,
            "completion_tokens": 200,
        },
    }

    result = runner.run(trace_data)

    assert result.trace_id == "test_trace_123"
    assert len(result.metrics) == 3
    assert result.passed is True


def test_evaluation_runner_with_failure():
    """Test evaluation runner with a failing evaluator"""
    evaluators = [
        LatencyEvaluator(threshold_ms=100),  # Will fail
        TokenUsageEvaluator(max_tokens=1000),  # Will pass
    ]

    runner = EvaluationRunner(evaluators=evaluators, auto_submit=False)

    trace_data = {
        "trace_id": "test_trace_123",
        "duration": 0.5,  # 500ms - exceeds threshold
        "metadata": {"total_tokens": 500},
    }

    result = runner.run(trace_data)

    assert result.passed is False
    latency_metric = result.get_metric("latency")
    assert latency_metric.score.passed is False


def test_disable_evaluator():
    """Test disabling an evaluator"""
    evaluators = [
        LatencyEvaluator(threshold_ms=100),
        TokenUsageEvaluator(max_tokens=1000),
    ]

    runner = EvaluationRunner(evaluators=evaluators, auto_submit=False)
    runner.disable_evaluator("latency")

    trace_data = {
        "trace_id": "test_trace_123",
        "duration": 0.5,
        "metadata": {"total_tokens": 500},
    }

    result = runner.run(trace_data)

    # Only token_usage metric should be present
    assert len(result.metrics) == 1
    assert result.metrics[0].name == "token_usage"
