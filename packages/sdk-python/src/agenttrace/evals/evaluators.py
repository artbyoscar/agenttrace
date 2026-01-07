"""Built-in evaluators for common metrics"""

from typing import Dict, Any, Optional, Callable
from .models import (
    Evaluator,
    EvaluationMetric,
    EvaluationScore,
    MetricType,
    ScoreType,
    CustomEvaluatorConfig,
)


class LatencyEvaluator(Evaluator):
    """Evaluates trace latency/duration"""

    def __init__(
        self,
        name: str = "latency",
        threshold_ms: Optional[float] = None,
        description: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            description=description or "Evaluates trace execution latency",
            metric_type=MetricType.LATENCY,
        )
        self.threshold_ms = threshold_ms

    def evaluate(self, trace_data: Dict[str, Any]) -> EvaluationMetric:
        """Evaluate latency from trace data"""
        duration = trace_data.get("duration", 0)
        duration_ms = duration * 1000  # Convert to milliseconds

        score = EvaluationScore(
            value=duration_ms,
            score_type=ScoreType.NUMERIC,
            min_value=0,
            threshold=self.threshold_ms,
        )

        # For latency, lower is better, so we invert the pass logic
        if self.threshold_ms is not None:
            score.passed = duration_ms <= self.threshold_ms

        return EvaluationMetric(
            name=self.name,
            metric_type=self.metric_type,
            description=self.description,
            score=score,
            metadata={
                "duration_seconds": duration,
                "duration_ms": duration_ms,
                "threshold_ms": self.threshold_ms,
            },
        )


class TokenUsageEvaluator(Evaluator):
    """Evaluates token usage efficiency"""

    def __init__(
        self,
        name: str = "token_usage",
        max_tokens: Optional[int] = None,
        description: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            description=description or "Evaluates token usage efficiency",
            metric_type=MetricType.TOKEN_USAGE,
        )
        self.max_tokens = max_tokens

    def evaluate(self, trace_data: Dict[str, Any]) -> EvaluationMetric:
        """Evaluate token usage from trace data"""
        metadata = trace_data.get("metadata", {})
        total_tokens = metadata.get("total_tokens", 0)
        prompt_tokens = metadata.get("prompt_tokens", 0)
        completion_tokens = metadata.get("completion_tokens", 0)

        score = EvaluationScore(
            value=total_tokens,
            score_type=ScoreType.NUMERIC,
            min_value=0,
            threshold=self.max_tokens,
        )

        if self.max_tokens is not None:
            score.passed = total_tokens <= self.max_tokens

        return EvaluationMetric(
            name=self.name,
            metric_type=self.metric_type,
            description=self.description,
            score=score,
            metadata={
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "max_tokens": self.max_tokens,
            },
        )


class ErrorRateEvaluator(Evaluator):
    """Evaluates error rate in traces"""

    def __init__(
        self,
        name: str = "error_rate",
        max_error_rate: float = 0.0,
        description: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            description=description or "Evaluates error occurrence rate",
            metric_type=MetricType.ERROR_RATE,
        )
        self.max_error_rate = max_error_rate

    def evaluate(self, trace_data: Dict[str, Any]) -> EvaluationMetric:
        """Evaluate error status from trace data"""
        status = trace_data.get("status", "completed")
        has_error = status == "error" or trace_data.get("error") is not None
        error_rate = 1.0 if has_error else 0.0

        score = EvaluationScore(
            value=error_rate,
            score_type=ScoreType.PERCENTAGE,
            min_value=0.0,
            max_value=1.0,
            threshold=self.max_error_rate,
        )

        score.passed = error_rate <= self.max_error_rate

        return EvaluationMetric(
            name=self.name,
            metric_type=self.metric_type,
            description=self.description,
            score=score,
            metadata={
                "has_error": has_error,
                "status": status,
                "error_rate": error_rate,
                "max_error_rate": self.max_error_rate,
            },
        )


class CostEvaluator(Evaluator):
    """Evaluates cost of trace execution"""

    def __init__(
        self,
        name: str = "cost",
        max_cost_usd: Optional[float] = None,
        description: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            description=description or "Evaluates execution cost",
            metric_type=MetricType.COST,
        )
        self.max_cost_usd = max_cost_usd

    def evaluate(self, trace_data: Dict[str, Any]) -> EvaluationMetric:
        """Evaluate cost from trace data"""
        metadata = trace_data.get("metadata", {})
        cost = metadata.get("cost_usd", 0.0)

        score = EvaluationScore(
            value=cost,
            score_type=ScoreType.NUMERIC,
            min_value=0.0,
            threshold=self.max_cost_usd,
        )

        if self.max_cost_usd is not None:
            score.passed = cost <= self.max_cost_usd

        return EvaluationMetric(
            name=self.name,
            metric_type=self.metric_type,
            description=self.description,
            score=score,
            metadata={
                "cost_usd": cost,
                "max_cost_usd": self.max_cost_usd,
            },
        )


class CustomEvaluator(Evaluator):
    """Custom evaluator using a user-provided function"""

    def __init__(self, config: CustomEvaluatorConfig):
        super().__init__(
            name=config.name,
            description=config.description,
            metric_type=config.metric_type,
        )
        self.evaluator_fn = config.evaluator_fn
        self.threshold = config.threshold
        self.config_metadata = config.metadata

    def evaluate(self, trace_data: Dict[str, Any]) -> EvaluationMetric:
        """Evaluate using custom function"""
        try:
            score = self.evaluator_fn(trace_data)

            # If threshold is set and not already set in score
            if self.threshold is not None and score.threshold is None:
                score.threshold = self.threshold
                if isinstance(score.value, (int, float)):
                    score.passed = score.value >= self.threshold

            return EvaluationMetric(
                name=self.name,
                metric_type=self.metric_type,
                description=self.description,
                score=score,
                metadata=self.config_metadata,
            )
        except Exception as e:
            # Return error metric
            return EvaluationMetric(
                name=self.name,
                metric_type=self.metric_type,
                description=f"Evaluation failed: {str(e)}",
                score=EvaluationScore(
                    value=0,
                    score_type=ScoreType.NUMERIC,
                    passed=False,
                ),
                metadata={"error": str(e), **self.config_metadata},
            )


class AccuracyEvaluator(Evaluator):
    """Evaluates output accuracy against expected result"""

    def __init__(
        self,
        name: str = "accuracy",
        comparison_fn: Optional[Callable[[Any, Any], float]] = None,
        threshold: float = 0.8,
        description: Optional[str] = None,
    ):
        super().__init__(
            name=name,
            description=description or "Evaluates output accuracy",
            metric_type=MetricType.ACCURACY,
        )
        self.comparison_fn = comparison_fn or self._default_comparison
        self.threshold = threshold

    def _default_comparison(self, actual: Any, expected: Any) -> float:
        """Default comparison - exact match returns 1.0, else 0.0"""
        return 1.0 if actual == expected else 0.0

    def evaluate(self, trace_data: Dict[str, Any]) -> EvaluationMetric:
        """Evaluate accuracy from trace data"""
        metadata = trace_data.get("metadata", {})
        actual = metadata.get("actual_output")
        expected = metadata.get("expected_output")

        if actual is None or expected is None:
            score = EvaluationScore(
                value=0.0,
                score_type=ScoreType.PERCENTAGE,
                passed=False,
            )
            metadata_out = {"error": "Missing actual or expected output"}
        else:
            accuracy = self.comparison_fn(actual, expected)
            score = EvaluationScore(
                value=accuracy,
                score_type=ScoreType.PERCENTAGE,
                min_value=0.0,
                max_value=1.0,
                threshold=self.threshold,
                passed=accuracy >= self.threshold,
            )
            metadata_out = {
                "accuracy": accuracy,
                "threshold": self.threshold,
                "actual_length": len(str(actual)),
                "expected_length": len(str(expected)),
            }

        return EvaluationMetric(
            name=self.name,
            metric_type=self.metric_type,
            description=self.description,
            score=score,
            metadata=metadata_out,
        )
