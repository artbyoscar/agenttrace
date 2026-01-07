"""AgentTrace Evaluation Framework.

This module provides a comprehensive framework for evaluating AI agent traces.

Core Components:
    - Evaluator: Abstract base class for creating custom evaluators
    - EvalResult: Stores evaluation results with scores and feedback
    - EvalScore: Represents individual score metrics
    - EvalSummary: Aggregates multiple evaluation results
    - Trace: Represents a complete trace with spans

Usage:
    Creating a custom evaluator:
        >>> from agenttrace.evals import Evaluator, EvalResult, EvalScore, Trace
        >>>
        >>> class AccuracyEvaluator(Evaluator):
        ...     @property
        ...     def name(self) -> str:
        ...         return "accuracy"
        ...
        ...     @property
        ...     def description(self) -> str:
        ...         return "Evaluates response accuracy"
        ...
        ...     async def evaluate(self, trace: Trace) -> EvalResult:
        ...         score = EvalScore(name="accuracy", value=0.95)
        ...         return EvalResult(
        ...             evaluator_name=self.name,
        ...             scores={"accuracy": score}
        ...         )

    Using the decorator:
        >>> from agenttrace.evals import register_evaluator, Trace, EvalResult, EvalScore
        >>>
        >>> @register_evaluator(name="completeness", description="Checks completeness")
        ... async def check_completeness(trace: Trace) -> EvalResult:
        ...     score = EvalScore(name="completeness", value=0.8, threshold=0.7)
        ...     return EvalResult(
        ...         evaluator_name="completeness",
        ...         scores={"completeness": score}
        ...     )

    Accessing the registry:
        >>> from agenttrace.evals import get_registry
        >>>
        >>> registry = get_registry()
        >>> evaluator = registry.get("accuracy")
        >>> all_evaluators = registry.list_all()
"""

from .models import EvalResult, EvalScore, EvalSummary
from .base import Evaluator, FunctionEvaluator, Trace, register_evaluator
from .registry import (
    EvaluatorRegistry,
    get_registry,
    reset_registry,
)

__all__ = [
    # Core classes
    "Evaluator",
    "FunctionEvaluator",
    "Trace",
    # Result models
    "EvalResult",
    "EvalScore",
    "EvalSummary",
    # Registry
    "EvaluatorRegistry",
    "get_registry",
    "reset_registry",
    # Decorators
    "register_evaluator",
]

__version__ = "0.1.0"
