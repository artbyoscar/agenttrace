"""Base evaluator interface and decorator for custom evaluators."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional, Awaitable
from functools import wraps
import inspect

from .models import EvalResult, EvalScore


class Trace:
    """Represents a complete trace with all its spans.

    Attributes:
        trace_id: Unique identifier for the trace
        spans: List of span dictionaries
        metadata: Additional metadata about the trace
        tags: List of tags associated with the trace
    """

    def __init__(
        self,
        trace_id: str,
        spans: list,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[list] = None,
    ):
        self.trace_id = trace_id
        self.spans = spans
        self.metadata = metadata or {}
        self.tags = tags or []

    def get_root_span(self) -> Optional[Dict[str, Any]]:
        """Get the root span (span with no parent).

        Returns:
            Root span dictionary or None if not found
        """
        for span in self.spans:
            if span.get("parent_id") is None:
                return span
        return None

    def get_spans_by_name(self, name: str) -> list:
        """Get all spans with a specific name.

        Args:
            name: Name of the spans to find

        Returns:
            List of span dictionaries
        """
        return [span for span in self.spans if span.get("name") == name]

    def get_span_by_id(self, span_id: str) -> Optional[Dict[str, Any]]:
        """Get a span by its ID.

        Args:
            span_id: ID of the span to find

        Returns:
            Span dictionary or None if not found
        """
        for span in self.spans:
            if span.get("span_id") == span_id:
                return span
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary representation.

        Returns:
            Dictionary containing all trace attributes
        """
        return {
            "trace_id": self.trace_id,
            "spans": self.spans,
            "metadata": self.metadata,
            "tags": self.tags,
        }


class Evaluator(ABC):
    """Abstract base class for all evaluators.

    Subclasses must implement the evaluate method and define name and description
    properties.

    Example:
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
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the evaluator.

        Returns:
            Evaluator name (e.g., "completeness", "accuracy")
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the evaluator does.

        Returns:
            Description string
        """
        pass

    @abstractmethod
    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate a trace and return results.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult containing scores and feedback

        Raises:
            Exception: If evaluation fails
        """
        pass


class FunctionEvaluator(Evaluator):
    """Wrapper to turn a function into an Evaluator.

    This allows simple functions to be used as evaluators without
    creating a full class.

    Args:
        func: The evaluation function
        name: Name of the evaluator
        description: Description of what the evaluator does
    """

    def __init__(
        self,
        func: Callable[[Trace], Awaitable[EvalResult]],
        name: str,
        description: str = "",
    ):
        self._func = func
        self._name = name
        self._description = description or f"Function-based evaluator: {name}"

    @property
    def name(self) -> str:
        """Return the evaluator name."""
        return self._name

    @property
    def description(self) -> str:
        """Return the evaluator description."""
        return self._description

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Call the wrapped function to evaluate the trace."""
        return await self._func(trace)


def register_evaluator(
    name: Optional[str] = None,
    description: Optional[str] = None,
    auto_register: bool = True,
) -> Callable:
    """Decorator to register a function or class as an evaluator.

    Can be used on both async functions and Evaluator subclasses.

    Args:
        name: Optional name for the evaluator (defaults to function/class name)
        description: Optional description of the evaluator
        auto_register: Whether to automatically register in the global registry

    Returns:
        Decorator function

    Example:
        >>> @register_evaluator(name="custom_eval", description="My evaluator")
        ... async def my_evaluator(trace: Trace) -> EvalResult:
        ...     score = EvalScore(name="quality", value=0.8)
        ...     return EvalResult(
        ...         evaluator_name="custom_eval",
        ...         scores={"quality": score}
        ...     )

        >>> @register_evaluator()
        ... class MyEvaluator(Evaluator):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my_evaluator"
        ...     ...
    """

    def decorator(func_or_class):
        # Determine if this is a class or function
        is_class = inspect.isclass(func_or_class)

        if is_class:
            # It's a class - verify it's an Evaluator subclass
            if not issubclass(func_or_class, Evaluator):
                raise TypeError(
                    f"{func_or_class.__name__} must inherit from Evaluator"
                )

            # Auto-register if requested
            if auto_register:
                from .registry import get_registry
                # Instantiate the evaluator class
                instance = func_or_class()
                get_registry().register(instance)

            return func_or_class
        else:
            # It's a function - wrap it in FunctionEvaluator
            evaluator_name = name or func_or_class.__name__
            evaluator_description = description or func_or_class.__doc__ or ""

            # Ensure the function is async
            if not inspect.iscoroutinefunction(func_or_class):
                raise TypeError(
                    f"Evaluator function {func_or_class.__name__} must be async"
                )

            evaluator = FunctionEvaluator(
                func=func_or_class,
                name=evaluator_name,
                description=evaluator_description,
            )

            # Auto-register if requested
            if auto_register:
                from .registry import get_registry
                get_registry().register(evaluator)

            @wraps(func_or_class)
            async def wrapper(trace: Trace) -> EvalResult:
                return await evaluator.evaluate(trace)

            # Attach the evaluator instance to the wrapper for testing
            wrapper._evaluator = evaluator

            return wrapper

    return decorator
