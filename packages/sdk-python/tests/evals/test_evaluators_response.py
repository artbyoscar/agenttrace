"""Unit tests for response quality evaluators."""

import pytest
from agenttrace.evals.base import Trace
from agenttrace.evals.evaluators.response import (
    ResponseCompletenessEvaluator,
    ResponseRelevanceEvaluator,
    ResponseCoherenceEvaluator,
)
from agenttrace.evals.evaluators._llm_judge import JudgeConfig


@pytest.fixture
def sample_trace():
    """Create a sample trace for testing."""
    return Trace(
        trace_id="test-trace-123",
        spans=[
            {
                "span_id": "1",
                "name": "agent_run",
                "parent_id": None,
                "metadata": {
                    "input": "What is the capital of France?",
                    "output": "The capital of France is Paris.",
                },
                "duration": 1.5,
            }
        ],
    )


@pytest.fixture
def incomplete_trace():
    """Create a trace with incomplete response."""
    return Trace(
        trace_id="test-trace-456",
        spans=[
            {
                "span_id": "1",
                "name": "agent_run",
                "parent_id": None,
                "metadata": {
                    "input": "Tell me about Paris: its history, culture, and famous landmarks.",
                    "output": "Paris is the capital of France.",
                },
                "duration": 1.0,
            }
        ],
    )


@pytest.fixture
def no_root_trace():
    """Create a trace without a root span."""
    return Trace(
        trace_id="test-trace-789",
        spans=[
            {
                "span_id": "1",
                "name": "child_span",
                "parent_id": "0",
                "metadata": {},
            }
        ],
    )


class TestResponseCompletenessEvaluator:
    """Tests for ResponseCompletenessEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = ResponseCompletenessEvaluator()

        assert evaluator.name == "response_completeness"
        assert "completeness" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_root_span(self, no_root_trace):
        """Test handling of trace without root span."""
        evaluator = ResponseCompletenessEvaluator()
        result = await evaluator.evaluate(no_root_trace)

        assert result.evaluator_name == "response_completeness"
        assert "completeness" in result.scores
        assert result.scores["completeness"].value == 0.0
        assert "no root span" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_missing_input_output(self):
        """Test handling of trace with missing input/output."""
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "metadata": {},
                }
            ],
        )

        evaluator = ResponseCompletenessEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["completeness"].value == 0.0
        assert "missing" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_with_valid_trace(self, sample_trace):
        """Test evaluation with valid trace."""
        evaluator = ResponseCompletenessEvaluator(threshold=0.5)
        result = await evaluator.evaluate(sample_trace)

        assert result.evaluator_name == "response_completeness"
        assert "completeness" in result.scores
        # Score should be between 0 and 1
        assert 0.0 <= result.scores["completeness"].value <= 1.0
        assert result.feedback is not None

    @pytest.mark.asyncio
    async def test_custom_threshold(self, sample_trace):
        """Test custom threshold configuration."""
        evaluator = ResponseCompletenessEvaluator(threshold=0.9)
        result = await evaluator.evaluate(sample_trace)

        assert result.scores["completeness"].threshold == 0.9

    @pytest.mark.asyncio
    async def test_metadata_includes_judge_model(self, sample_trace):
        """Test that metadata includes judge model info."""
        config = JudgeConfig(model="gpt-4")
        evaluator = ResponseCompletenessEvaluator(config=config)
        result = await evaluator.evaluate(sample_trace)

        assert "judge_model" in result.metadata
        assert result.metadata["judge_model"] == "gpt-4"


class TestResponseRelevanceEvaluator:
    """Tests for ResponseRelevanceEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = ResponseRelevanceEvaluator()

        assert evaluator.name == "response_relevance"
        assert "relevance" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_root_span(self, no_root_trace):
        """Test handling of trace without root span."""
        evaluator = ResponseRelevanceEvaluator()
        result = await evaluator.evaluate(no_root_trace)

        assert "relevance" in result.scores
        assert result.scores["relevance"].value == 0.0

    @pytest.mark.asyncio
    async def test_with_valid_trace(self, sample_trace):
        """Test evaluation with valid trace."""
        evaluator = ResponseRelevanceEvaluator(threshold=0.7)
        result = await evaluator.evaluate(sample_trace)

        assert result.evaluator_name == "response_relevance"
        assert "relevance" in result.scores
        assert 0.0 <= result.scores["relevance"].value <= 1.0

    @pytest.mark.asyncio
    async def test_custom_config(self, sample_trace):
        """Test custom judge configuration."""
        config = JudgeConfig(model="claude-3-opus", temperature=0.1)
        evaluator = ResponseRelevanceEvaluator(config=config)
        result = await evaluator.evaluate(sample_trace)

        assert result.metadata["judge_model"] == "claude-3-opus"


class TestResponseCoherenceEvaluator:
    """Tests for ResponseCoherenceEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = ResponseCoherenceEvaluator()

        assert evaluator.name == "response_coherence"
        assert "coherence" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_root_span(self, no_root_trace):
        """Test handling of trace without root span."""
        evaluator = ResponseCoherenceEvaluator()
        result = await evaluator.evaluate(no_root_trace)

        assert "coherence" in result.scores
        assert result.scores["coherence"].value == 0.0

    @pytest.mark.asyncio
    async def test_missing_output(self):
        """Test handling of trace with missing output."""
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "metadata": {"input": "test"},
                }
            ],
        )

        evaluator = ResponseCoherenceEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["coherence"].value == 0.0
        assert "missing output" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_with_valid_trace(self, sample_trace):
        """Test evaluation with valid trace."""
        evaluator = ResponseCoherenceEvaluator(threshold=0.6)
        result = await evaluator.evaluate(sample_trace)

        assert result.evaluator_name == "response_coherence"
        assert "coherence" in result.scores
        assert 0.0 <= result.scores["coherence"].value <= 1.0
        assert "output_length" in result.metadata

    @pytest.mark.asyncio
    async def test_coherence_without_input(self):
        """Test coherence evaluation without input (should still work)."""
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "metadata": {
                        "output": "This is a coherent response. It flows logically."
                    },
                }
            ],
        )

        evaluator = ResponseCoherenceEvaluator()
        result = await evaluator.evaluate(trace)

        # Should still evaluate even without input
        assert 0.0 <= result.scores["coherence"].value <= 1.0
