"""Unit tests for base evaluator classes and decorators."""

import pytest
from agenttrace.evals.base import (
    Trace,
    Evaluator,
    FunctionEvaluator,
    register_evaluator,
)
from agenttrace.evals.models import EvalResult, EvalScore
from agenttrace.evals.registry import reset_registry, get_registry


class TestTrace:
    """Tests for Trace class."""

    def test_create_trace(self):
        """Test creating a basic trace."""
        spans = [
            {"span_id": "1", "name": "root", "parent_id": None},
            {"span_id": "2", "name": "child", "parent_id": "1"},
        ]
        trace = Trace(trace_id="trace-123", spans=spans)

        assert trace.trace_id == "trace-123"
        assert len(trace.spans) == 2
        assert trace.metadata == {}
        assert trace.tags == []

    def test_create_trace_with_metadata_and_tags(self):
        """Test creating a trace with metadata and tags."""
        spans = [{"span_id": "1", "name": "root", "parent_id": None}]
        metadata = {"user_id": "123", "session_id": "abc"}
        tags = ["production", "api-call"]

        trace = Trace(
            trace_id="trace-123",
            spans=spans,
            metadata=metadata,
            tags=tags,
        )

        assert trace.metadata == metadata
        assert trace.tags == tags

    def test_get_root_span(self):
        """Test getting the root span."""
        spans = [
            {"span_id": "1", "name": "root", "parent_id": None},
            {"span_id": "2", "name": "child", "parent_id": "1"},
        ]
        trace = Trace(trace_id="trace-123", spans=spans)

        root = trace.get_root_span()
        assert root is not None
        assert root["span_id"] == "1"
        assert root["name"] == "root"

    def test_get_root_span_no_root(self):
        """Test getting root span when there is no root."""
        spans = [
            {"span_id": "1", "name": "child1", "parent_id": "0"},
            {"span_id": "2", "name": "child2", "parent_id": "0"},
        ]
        trace = Trace(trace_id="trace-123", spans=spans)

        root = trace.get_root_span()
        assert root is None

    def test_get_spans_by_name(self):
        """Test getting spans by name."""
        spans = [
            {"span_id": "1", "name": "llm_call", "parent_id": None},
            {"span_id": "2", "name": "tool_use", "parent_id": "1"},
            {"span_id": "3", "name": "llm_call", "parent_id": "1"},
        ]
        trace = Trace(trace_id="trace-123", spans=spans)

        llm_spans = trace.get_spans_by_name("llm_call")
        assert len(llm_spans) == 2
        assert all(s["name"] == "llm_call" for s in llm_spans)

    def test_get_span_by_id(self):
        """Test getting a span by ID."""
        spans = [
            {"span_id": "1", "name": "root", "parent_id": None},
            {"span_id": "2", "name": "child", "parent_id": "1"},
        ]
        trace = Trace(trace_id="trace-123", spans=spans)

        span = trace.get_span_by_id("2")
        assert span is not None
        assert span["span_id"] == "2"
        assert span["name"] == "child"

    def test_get_span_by_id_not_found(self):
        """Test getting a span by ID that doesn't exist."""
        spans = [{"span_id": "1", "name": "root", "parent_id": None}]
        trace = Trace(trace_id="trace-123", spans=spans)

        span = trace.get_span_by_id("999")
        assert span is None

    def test_to_dict(self):
        """Test converting trace to dictionary."""
        spans = [{"span_id": "1", "name": "root", "parent_id": None}]
        metadata = {"user_id": "123"}
        tags = ["production"]

        trace = Trace(
            trace_id="trace-123",
            spans=spans,
            metadata=metadata,
            tags=tags,
        )

        trace_dict = trace.to_dict()

        assert trace_dict["trace_id"] == "trace-123"
        assert trace_dict["spans"] == spans
        assert trace_dict["metadata"] == metadata
        assert trace_dict["tags"] == tags


class TestEvaluator:
    """Tests for Evaluator abstract base class."""

    def test_cannot_instantiate_abstract_evaluator(self):
        """Test that Evaluator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Evaluator()

    def test_create_concrete_evaluator(self):
        """Test creating a concrete evaluator."""

        class TestEvaluator(Evaluator):
            @property
            def name(self) -> str:
                return "test_evaluator"

            @property
            def description(self) -> str:
                return "A test evaluator"

            async def evaluate(self, trace: Trace) -> EvalResult:
                score = EvalScore(name="test_score", value=0.8)
                return EvalResult(
                    evaluator_name=self.name,
                    scores={"test_score": score},
                )

        evaluator = TestEvaluator()
        assert evaluator.name == "test_evaluator"
        assert evaluator.description == "A test evaluator"

    @pytest.mark.asyncio
    async def test_evaluator_evaluate_method(self):
        """Test that the evaluate method works correctly."""

        class TestEvaluator(Evaluator):
            @property
            def name(self) -> str:
                return "test_evaluator"

            @property
            def description(self) -> str:
                return "A test evaluator"

            async def evaluate(self, trace: Trace) -> EvalResult:
                score = EvalScore(name="test_score", value=0.8)
                return EvalResult(
                    evaluator_name=self.name,
                    scores={"test_score": score},
                )

        evaluator = TestEvaluator()
        trace = Trace(
            trace_id="trace-123",
            spans=[{"span_id": "1", "name": "root", "parent_id": None}],
        )

        result = await evaluator.evaluate(trace)

        assert isinstance(result, EvalResult)
        assert result.evaluator_name == "test_evaluator"
        assert "test_score" in result.scores


class TestFunctionEvaluator:
    """Tests for FunctionEvaluator wrapper class."""

    @pytest.mark.asyncio
    async def test_function_evaluator_basic(self):
        """Test creating a basic function evaluator."""

        async def my_eval_func(trace: Trace) -> EvalResult:
            score = EvalScore(name="quality", value=0.9)
            return EvalResult(
                evaluator_name="my_eval",
                scores={"quality": score},
            )

        evaluator = FunctionEvaluator(
            func=my_eval_func,
            name="my_eval",
            description="My custom evaluator",
        )

        assert evaluator.name == "my_eval"
        assert evaluator.description == "My custom evaluator"

        trace = Trace(
            trace_id="trace-123",
            spans=[{"span_id": "1", "name": "root", "parent_id": None}],
        )

        result = await evaluator.evaluate(trace)
        assert result.evaluator_name == "my_eval"
        assert "quality" in result.scores

    def test_function_evaluator_default_description(self):
        """Test that FunctionEvaluator generates a default description."""

        async def my_eval_func(trace: Trace) -> EvalResult:
            score = EvalScore(name="quality", value=0.9)
            return EvalResult(
                evaluator_name="my_eval",
                scores={"quality": score},
            )

        evaluator = FunctionEvaluator(func=my_eval_func, name="my_eval")

        assert "Function-based evaluator: my_eval" in evaluator.description


class TestRegisterEvaluatorDecorator:
    """Tests for @register_evaluator decorator."""

    def setup_method(self):
        """Reset the registry before each test."""
        reset_registry()

    def teardown_method(self):
        """Clean up the registry after each test."""
        reset_registry()

    @pytest.mark.asyncio
    async def test_register_function_evaluator(self):
        """Test registering a function as an evaluator."""

        @register_evaluator(name="test_func_eval", description="Test function evaluator")
        async def my_evaluator(trace: Trace) -> EvalResult:
            score = EvalScore(name="quality", value=0.85)
            return EvalResult(
                evaluator_name="test_func_eval",
                scores={"quality": score},
            )

        # Check that it was registered
        registry = get_registry()
        evaluator = registry.get("test_func_eval")

        assert evaluator is not None
        assert evaluator.name == "test_func_eval"
        assert evaluator.description == "Test function evaluator"

        # Test that the wrapper function still works
        trace = Trace(
            trace_id="trace-123",
            spans=[{"span_id": "1", "name": "root", "parent_id": None}],
        )
        result = await my_evaluator(trace)
        assert result.evaluator_name == "test_func_eval"

    @pytest.mark.asyncio
    async def test_register_function_with_default_name(self):
        """Test registering a function with default name (function name)."""

        @register_evaluator()
        async def custom_evaluator(trace: Trace) -> EvalResult:
            score = EvalScore(name="quality", value=0.85)
            return EvalResult(
                evaluator_name="custom_evaluator",
                scores={"quality": score},
            )

        registry = get_registry()
        evaluator = registry.get("custom_evaluator")

        assert evaluator is not None
        assert evaluator.name == "custom_evaluator"

    @pytest.mark.asyncio
    async def test_register_function_with_docstring_description(self):
        """Test that decorator uses function docstring as description."""

        @register_evaluator()
        async def documented_evaluator(trace: Trace) -> EvalResult:
            """This is a well-documented evaluator."""
            score = EvalScore(name="quality", value=0.85)
            return EvalResult(
                evaluator_name="documented_evaluator",
                scores={"quality": score},
            )

        registry = get_registry()
        evaluator = registry.get("documented_evaluator")

        assert "well-documented evaluator" in evaluator.description

    def test_register_class_evaluator(self):
        """Test registering a class as an evaluator."""

        @register_evaluator()
        class TestClassEvaluator(Evaluator):
            @property
            def name(self) -> str:
                return "test_class_eval"

            @property
            def description(self) -> str:
                return "Test class evaluator"

            async def evaluate(self, trace: Trace) -> EvalResult:
                score = EvalScore(name="quality", value=0.9)
                return EvalResult(
                    evaluator_name=self.name,
                    scores={"quality": score},
                )

        registry = get_registry()
        evaluator = registry.get("test_class_eval")

        assert evaluator is not None
        assert evaluator.name == "test_class_eval"

    def test_register_non_evaluator_class_raises_error(self):
        """Test that registering a non-Evaluator class raises TypeError."""

        with pytest.raises(TypeError, match="must inherit from Evaluator"):

            @register_evaluator()
            class NotAnEvaluator:
                pass

    def test_register_non_async_function_raises_error(self):
        """Test that registering a non-async function raises TypeError."""

        with pytest.raises(TypeError, match="must be async"):

            @register_evaluator()
            def sync_evaluator(trace: Trace) -> EvalResult:
                score = EvalScore(name="quality", value=0.9)
                return EvalResult(
                    evaluator_name="sync_eval",
                    scores={"quality": score},
                )

    def test_register_with_auto_register_false(self):
        """Test that auto_register=False prevents automatic registration."""

        @register_evaluator(auto_register=False)
        async def unregistered_evaluator(trace: Trace) -> EvalResult:
            score = EvalScore(name="quality", value=0.85)
            return EvalResult(
                evaluator_name="unregistered_evaluator",
                scores={"quality": score},
            )

        registry = get_registry()
        evaluator = registry.get("unregistered_evaluator")

        # Should not be registered
        assert evaluator is None

    def test_register_class_with_auto_register_false(self):
        """Test that auto_register=False works for classes."""

        @register_evaluator(auto_register=False)
        class UnregisteredClassEvaluator(Evaluator):
            @property
            def name(self) -> str:
                return "unregistered_class"

            @property
            def description(self) -> str:
                return "Not registered"

            async def evaluate(self, trace: Trace) -> EvalResult:
                score = EvalScore(name="quality", value=0.9)
                return EvalResult(
                    evaluator_name=self.name,
                    scores={"quality": score},
                )

        registry = get_registry()
        evaluator = registry.get("unregistered_class")

        # Should not be registered
        assert evaluator is None
