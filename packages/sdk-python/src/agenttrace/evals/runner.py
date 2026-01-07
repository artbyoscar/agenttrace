"""Evaluation runner for executing evaluators on traces"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from .models import Evaluator, EvaluationResult, EvaluationScore, ScoreType
from ..http_client import HTTPClient


class EvaluationRunner:
    """Runs evaluations on traces"""

    def __init__(
        self,
        evaluators: List[Evaluator],
        http_client: Optional[HTTPClient] = None,
        auto_submit: bool = True,
    ):
        """
        Initialize evaluation runner

        Args:
            evaluators: List of evaluators to run
            http_client: HTTP client for submitting results
            auto_submit: Whether to automatically submit results to API
        """
        self.evaluators = evaluators
        self.http_client = http_client
        self.auto_submit = auto_submit

    def run(
        self,
        trace_data: Dict[str, Any],
        evaluators: Optional[List[Evaluator]] = None,
    ) -> EvaluationResult:
        """
        Run evaluations on trace data

        Args:
            trace_data: The trace data to evaluate
            evaluators: Optional list of evaluators to use (overrides default)

        Returns:
            EvaluationResult with all metric results
        """
        evaluators_to_run = evaluators or self.evaluators
        trace_id = trace_data.get("trace_id", "unknown")
        evaluation_id = str(uuid.uuid4())

        # Run all evaluators
        metrics = []
        for evaluator in evaluators_to_run:
            if evaluator.enabled:
                metric = evaluator.evaluate(trace_data)
                metrics.append(metric)

        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)

        # Create result
        result = EvaluationResult(
            trace_id=trace_id,
            evaluation_id=evaluation_id,
            timestamp=datetime.utcnow(),
            metrics=metrics,
            overall_score=overall_score,
            metadata={
                "num_evaluators": len(evaluators_to_run),
                "num_metrics": len(metrics),
            },
        )

        # Submit to API if enabled
        if self.auto_submit and self.http_client:
            self.submit_result(result)

        return result

    def _calculate_overall_score(
        self, metrics: List
    ) -> Optional[EvaluationScore]:
        """Calculate overall score from all metrics"""
        # Get all numeric scores
        numeric_scores = []
        for metric in metrics:
            if metric.score and metric.score.score_type == ScoreType.NUMERIC:
                if isinstance(metric.score.value, (int, float)):
                    numeric_scores.append(metric.score.value)

        if not numeric_scores:
            return None

        # Calculate average
        avg_score = sum(numeric_scores) / len(numeric_scores)

        return EvaluationScore(
            value=avg_score,
            score_type=ScoreType.NUMERIC,
            min_value=0.0,
            max_value=100.0,
        )

    def submit_result(self, result: EvaluationResult) -> Dict[str, Any]:
        """Submit evaluation result to API"""
        if not self.http_client:
            raise ValueError("HTTP client not configured")

        try:
            response = self.http_client.client.post(
                "/api/v1/evaluations",
                json=result.to_dict(),
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error submitting evaluation result: {e}")
            return {}

    def add_evaluator(self, evaluator: Evaluator) -> None:
        """Add an evaluator to the runner"""
        self.evaluators.append(evaluator)

    def remove_evaluator(self, evaluator_name: str) -> None:
        """Remove an evaluator by name"""
        self.evaluators = [e for e in self.evaluators if e.name != evaluator_name]

    def get_evaluator(self, name: str) -> Optional[Evaluator]:
        """Get an evaluator by name"""
        for evaluator in self.evaluators:
            if evaluator.name == name:
                return evaluator
        return None

    def enable_evaluator(self, name: str) -> None:
        """Enable an evaluator by name"""
        evaluator = self.get_evaluator(name)
        if evaluator:
            evaluator.enabled = True

    def disable_evaluator(self, name: str) -> None:
        """Disable an evaluator by name"""
        evaluator = self.get_evaluator(name)
        if evaluator:
            evaluator.enabled = False
