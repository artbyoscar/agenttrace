"""Global registry for managing evaluators."""

from typing import Dict, List, Optional
import threading

from .base import Evaluator


class EvaluatorRegistry:
    """Thread-safe registry for storing and retrieving evaluators.

    The registry supports namespaced evaluators (e.g., "agenttrace.completeness")
    and provides methods to register, retrieve, and list evaluators.

    Example:
        >>> registry = EvaluatorRegistry()
        >>> registry.register(my_evaluator)
        >>> evaluator = registry.get("my_evaluator")
        >>> all_evaluators = registry.list_all()
    """

    def __init__(self):
        """Initialize an empty registry with thread safety."""
        self._evaluators: Dict[str, Evaluator] = {}
        self._lock = threading.Lock()

    def register(self, evaluator: Evaluator, namespace: Optional[str] = None) -> None:
        """Register an evaluator in the registry.

        Args:
            evaluator: The evaluator instance to register
            namespace: Optional namespace prefix (e.g., "agenttrace")

        Raises:
            TypeError: If evaluator is not an instance of Evaluator
            ValueError: If an evaluator with this name already exists

        Example:
            >>> registry.register(my_evaluator)
            >>> registry.register(my_evaluator, namespace="agenttrace")
        """
        if not isinstance(evaluator, Evaluator):
            raise TypeError(
                f"Expected Evaluator instance, got {type(evaluator).__name__}"
            )

        # Construct the full name with namespace if provided
        if namespace:
            full_name = f"{namespace}.{evaluator.name}"
        else:
            full_name = evaluator.name

        with self._lock:
            if full_name in self._evaluators:
                raise ValueError(
                    f"Evaluator '{full_name}' is already registered. "
                    f"Use unregister() first or choose a different name."
                )

            self._evaluators[full_name] = evaluator

    def get(self, name: str) -> Optional[Evaluator]:
        """Retrieve an evaluator by name.

        Args:
            name: The name of the evaluator (can include namespace)

        Returns:
            The evaluator instance or None if not found

        Example:
            >>> evaluator = registry.get("agenttrace.completeness")
            >>> if evaluator:
            ...     result = await evaluator.evaluate(trace)
        """
        with self._lock:
            return self._evaluators.get(name)

    def unregister(self, name: str) -> bool:
        """Remove an evaluator from the registry.

        Args:
            name: The name of the evaluator to remove

        Returns:
            True if the evaluator was removed, False if it wasn't found

        Example:
            >>> success = registry.unregister("my_evaluator")
        """
        with self._lock:
            if name in self._evaluators:
                del self._evaluators[name]
                return True
            return False

    def list_all(self, namespace: Optional[str] = None) -> List[str]:
        """List all registered evaluator names.

        Args:
            namespace: Optional namespace to filter by

        Returns:
            List of evaluator names

        Example:
            >>> all_names = registry.list_all()
            >>> agenttrace_names = registry.list_all(namespace="agenttrace")
        """
        with self._lock:
            if namespace:
                prefix = f"{namespace}."
                return [
                    name for name in self._evaluators.keys()
                    if name.startswith(prefix)
                ]
            return list(self._evaluators.keys())

    def get_all(self, namespace: Optional[str] = None) -> Dict[str, Evaluator]:
        """Get all registered evaluators.

        Args:
            namespace: Optional namespace to filter by

        Returns:
            Dictionary mapping names to evaluator instances

        Example:
            >>> all_evaluators = registry.get_all()
            >>> for name, evaluator in all_evaluators.items():
            ...     print(f"{name}: {evaluator.description}")
        """
        with self._lock:
            if namespace:
                prefix = f"{namespace}."
                return {
                    name: evaluator
                    for name, evaluator in self._evaluators.items()
                    if name.startswith(prefix)
                }
            return dict(self._evaluators)

    def clear(self) -> None:
        """Remove all evaluators from the registry.

        Warning:
            This will remove all registered evaluators. Use with caution.

        Example:
            >>> registry.clear()
        """
        with self._lock:
            self._evaluators.clear()

    def __contains__(self, name: str) -> bool:
        """Check if an evaluator is registered.

        Args:
            name: The name to check

        Returns:
            True if the evaluator is registered

        Example:
            >>> if "my_evaluator" in registry:
            ...     print("Evaluator is registered")
        """
        with self._lock:
            return name in self._evaluators

    def __len__(self) -> int:
        """Get the number of registered evaluators.

        Returns:
            Number of evaluators in the registry

        Example:
            >>> count = len(registry)
        """
        with self._lock:
            return len(self._evaluators)


# Global registry instance
_global_registry: Optional[EvaluatorRegistry] = None
_registry_lock = threading.Lock()


def get_registry() -> EvaluatorRegistry:
    """Get the global evaluator registry instance.

    This function implements a thread-safe singleton pattern.

    Returns:
        The global EvaluatorRegistry instance

    Example:
        >>> from agenttrace.evals import get_registry
        >>> registry = get_registry()
        >>> registry.register(my_evaluator)
    """
    global _global_registry

    if _global_registry is None:
        with _registry_lock:
            # Double-check locking pattern
            if _global_registry is None:
                _global_registry = EvaluatorRegistry()

    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (primarily for testing).

    Warning:
        This will clear and reset the global registry. Use only in tests.

    Example:
        >>> from agenttrace.evals import reset_registry
        >>> reset_registry()  # Clear all registered evaluators
    """
    global _global_registry

    with _registry_lock:
        _global_registry = None
