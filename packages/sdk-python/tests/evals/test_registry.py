"""Unit tests for evaluator registry."""

import pytest
import threading
from agenttrace.evals.base import Evaluator, Trace
from agenttrace.evals.models import EvalResult, EvalScore
from agenttrace.evals.registry import (
    EvaluatorRegistry,
    get_registry,
    reset_registry,
)


class DummyEvaluator(Evaluator):
    """Dummy evaluator for testing."""

    def __init__(self, name: str, description: str = "Test evaluator"):
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    async def evaluate(self, trace: Trace) -> EvalResult:
        score = EvalScore(name="test", value=0.8)
        return EvalResult(
            evaluator_name=self.name,
            scores={"test": score},
        )


class TestEvaluatorRegistry:
    """Tests for EvaluatorRegistry class."""

    def setup_method(self):
        """Create a fresh registry for each test."""
        self.registry = EvaluatorRegistry()

    def test_create_registry(self):
        """Test creating a new registry."""
        registry = EvaluatorRegistry()
        assert len(registry) == 0

    def test_register_evaluator(self):
        """Test registering an evaluator."""
        evaluator = DummyEvaluator(name="test_eval")
        self.registry.register(evaluator)

        assert "test_eval" in self.registry
        assert len(self.registry) == 1

    def test_register_with_namespace(self):
        """Test registering an evaluator with namespace."""
        evaluator = DummyEvaluator(name="completeness")
        self.registry.register(evaluator, namespace="agenttrace")

        assert "agenttrace.completeness" in self.registry
        assert len(self.registry) == 1

    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate name raises ValueError."""
        evaluator1 = DummyEvaluator(name="test_eval")
        evaluator2 = DummyEvaluator(name="test_eval")

        self.registry.register(evaluator1)

        with pytest.raises(ValueError, match="already registered"):
            self.registry.register(evaluator2)

    def test_register_non_evaluator_raises_error(self):
        """Test that registering non-Evaluator raises TypeError."""
        not_an_evaluator = "not an evaluator"

        with pytest.raises(TypeError, match="Expected Evaluator instance"):
            self.registry.register(not_an_evaluator)

    def test_get_evaluator(self):
        """Test getting a registered evaluator."""
        evaluator = DummyEvaluator(name="test_eval")
        self.registry.register(evaluator)

        retrieved = self.registry.get("test_eval")
        assert retrieved is not None
        assert retrieved.name == "test_eval"

    def test_get_nonexistent_evaluator(self):
        """Test getting a non-existent evaluator returns None."""
        retrieved = self.registry.get("nonexistent")
        assert retrieved is None

    def test_get_namespaced_evaluator(self):
        """Test getting a namespaced evaluator."""
        evaluator = DummyEvaluator(name="completeness")
        self.registry.register(evaluator, namespace="agenttrace")

        retrieved = self.registry.get("agenttrace.completeness")
        assert retrieved is not None
        assert retrieved.name == "completeness"

    def test_unregister_evaluator(self):
        """Test unregistering an evaluator."""
        evaluator = DummyEvaluator(name="test_eval")
        self.registry.register(evaluator)

        success = self.registry.unregister("test_eval")
        assert success is True
        assert "test_eval" not in self.registry

    def test_unregister_nonexistent(self):
        """Test unregistering a non-existent evaluator."""
        success = self.registry.unregister("nonexistent")
        assert success is False

    def test_list_all_empty(self):
        """Test listing all evaluators when registry is empty."""
        names = self.registry.list_all()
        assert names == []

    def test_list_all_with_evaluators(self):
        """Test listing all evaluators."""
        eval1 = DummyEvaluator(name="eval1")
        eval2 = DummyEvaluator(name="eval2")
        eval3 = DummyEvaluator(name="eval3")

        self.registry.register(eval1)
        self.registry.register(eval2)
        self.registry.register(eval3)

        names = self.registry.list_all()
        assert len(names) == 3
        assert "eval1" in names
        assert "eval2" in names
        assert "eval3" in names

    def test_list_all_with_namespace_filter(self):
        """Test listing evaluators filtered by namespace."""
        eval1 = DummyEvaluator(name="completeness")
        eval2 = DummyEvaluator(name="accuracy")
        eval3 = DummyEvaluator(name="custom")

        self.registry.register(eval1, namespace="agenttrace")
        self.registry.register(eval2, namespace="agenttrace")
        self.registry.register(eval3, namespace="custom")

        agenttrace_names = self.registry.list_all(namespace="agenttrace")
        assert len(agenttrace_names) == 2
        assert "agenttrace.completeness" in agenttrace_names
        assert "agenttrace.accuracy" in agenttrace_names

    def test_get_all_evaluators(self):
        """Test getting all evaluator instances."""
        eval1 = DummyEvaluator(name="eval1")
        eval2 = DummyEvaluator(name="eval2")

        self.registry.register(eval1)
        self.registry.register(eval2)

        all_evaluators = self.registry.get_all()
        assert len(all_evaluators) == 2
        assert "eval1" in all_evaluators
        assert "eval2" in all_evaluators

    def test_get_all_with_namespace_filter(self):
        """Test getting all evaluators filtered by namespace."""
        eval1 = DummyEvaluator(name="completeness")
        eval2 = DummyEvaluator(name="accuracy")
        eval3 = DummyEvaluator(name="custom")

        self.registry.register(eval1, namespace="agenttrace")
        self.registry.register(eval2, namespace="agenttrace")
        self.registry.register(eval3, namespace="other")

        agenttrace_evaluators = self.registry.get_all(namespace="agenttrace")
        assert len(agenttrace_evaluators) == 2
        assert "agenttrace.completeness" in agenttrace_evaluators

    def test_clear_registry(self):
        """Test clearing the registry."""
        eval1 = DummyEvaluator(name="eval1")
        eval2 = DummyEvaluator(name="eval2")

        self.registry.register(eval1)
        self.registry.register(eval2)

        assert len(self.registry) == 2

        self.registry.clear()

        assert len(self.registry) == 0

    def test_contains_operator(self):
        """Test the 'in' operator."""
        evaluator = DummyEvaluator(name="test_eval")
        self.registry.register(evaluator)

        assert "test_eval" in self.registry
        assert "nonexistent" not in self.registry

    def test_len_operator(self):
        """Test the len() function."""
        assert len(self.registry) == 0

        eval1 = DummyEvaluator(name="eval1")
        self.registry.register(eval1)
        assert len(self.registry) == 1

        eval2 = DummyEvaluator(name="eval2")
        self.registry.register(eval2)
        assert len(self.registry) == 2

    def test_thread_safety_concurrent_register(self):
        """Test thread safety when registering concurrently."""
        num_threads = 10
        threads = []

        def register_evaluator(i):
            evaluator = DummyEvaluator(name=f"eval_{i}")
            self.registry.register(evaluator)

        for i in range(num_threads):
            thread = threading.Thread(target=register_evaluator, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(self.registry) == num_threads

    def test_thread_safety_concurrent_get(self):
        """Test thread safety when getting concurrently."""
        evaluator = DummyEvaluator(name="test_eval")
        self.registry.register(evaluator)

        results = []

        def get_evaluator():
            result = self.registry.get("test_eval")
            results.append(result)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_evaluator)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 10
        assert all(r is not None for r in results)


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def setup_method(self):
        """Reset the global registry before each test."""
        reset_registry()

    def teardown_method(self):
        """Clean up after each test."""
        reset_registry()

    def test_get_registry_singleton(self):
        """Test that get_registry returns a singleton."""
        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    def test_get_registry_is_thread_safe(self):
        """Test that get_registry is thread-safe."""
        registries = []

        def get_and_store_registry():
            registry = get_registry()
            registries.append(registry)

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_and_store_registry)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All should be the same instance
        assert len(registries) == 10
        assert all(r is registries[0] for r in registries)

    def test_reset_registry(self):
        """Test resetting the global registry."""
        registry1 = get_registry()
        evaluator = DummyEvaluator(name="test_eval")
        registry1.register(evaluator)

        assert len(registry1) == 1

        reset_registry()

        registry2 = get_registry()
        assert len(registry2) == 0
        assert registry1 is not registry2

    def test_registry_persists_across_calls(self):
        """Test that registered evaluators persist across get_registry calls."""
        registry1 = get_registry()
        evaluator = DummyEvaluator(name="test_eval")
        registry1.register(evaluator)

        registry2 = get_registry()
        assert "test_eval" in registry2
        assert len(registry2) == 1

    def test_global_registry_isolation(self):
        """Test that different registries don't interfere."""
        # Use global registry
        global_registry = get_registry()
        eval1 = DummyEvaluator(name="global_eval")
        global_registry.register(eval1)

        # Create separate registry
        separate_registry = EvaluatorRegistry()
        eval2 = DummyEvaluator(name="separate_eval")
        separate_registry.register(eval2)

        # Check isolation
        assert "global_eval" in global_registry
        assert "separate_eval" not in global_registry

        assert "separate_eval" in separate_registry
        assert "global_eval" not in separate_registry
