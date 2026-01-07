"""Unit tests for efficiency evaluators."""

import pytest
from agenttrace.evals.base import Trace
from agenttrace.evals.evaluators.efficiency import (
    TokenEfficiencyEvaluator,
    LatencyEvaluator,
    TrajectoryOptimalityEvaluator,
)


@pytest.fixture
def trace_with_tokens():
    """Create a trace with token usage."""
    return Trace(
        trace_id="test-trace-tokens",
        spans=[
            {
                "span_id": "1",
                "name": "llm_call",
                "parent_id": None,
                "duration": 1.5,
                "metadata": {
                    "tokens": 500,
                    "prompt_tokens": 300,
                    "completion_tokens": 200,
                },
            },
            {
                "span_id": "2",
                "name": "llm_call",
                "parent_id": "1",
                "duration": 0.8,
                "metadata": {
                    "tokens": 300,
                    "prompt_tokens": 200,
                    "completion_tokens": 100,
                },
            },
        ],
    )


@pytest.fixture
def trace_excessive_tokens():
    """Create a trace with excessive token usage."""
    return Trace(
        trace_id="test-trace-excessive",
        spans=[
            {
                "span_id": "1",
                "name": "llm_call",
                "parent_id": None,
                "duration": 2.0,
                "metadata": {"tokens": 5000},
            }
        ],
    )


@pytest.fixture
def trace_with_latency():
    """Create a trace with various latencies."""
    return Trace(
        trace_id="test-trace-latency",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "duration": 3.5,
            },
            {
                "span_id": "2",
                "name": "llm_call",
                "parent_id": "1",
                "duration": 2.0,
            },
            {
                "span_id": "3",
                "name": "tool_use",
                "parent_id": "1",
                "duration": 1.0,
            },
            {
                "span_id": "4",
                "name": "retrieval",
                "parent_id": "1",
                "duration": 0.5,
            },
        ],
    )


@pytest.fixture
def trace_with_loops():
    """Create a trace with redundant steps and loops."""
    return Trace(
        trace_id="test-trace-loops",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "duration": 5.0,
                "metadata": {},
            },
            {
                "span_id": "2",
                "name": "search",
                "parent_id": "1",
                "metadata": {"input": "query1"},
            },
            {
                "span_id": "3",
                "name": "search",
                "parent_id": "1",
                "metadata": {"input": "query1"},  # Redundant
            },
            {
                "span_id": "4",
                "name": "process",
                "parent_id": "1",
                "metadata": {},
            },
            {
                "span_id": "5",
                "name": "retry",
                "parent_id": "1",
                "status": "error",
            },
        ],
    )


class TestTokenEfficiencyEvaluator:
    """Tests for TokenEfficiencyEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = TokenEfficiencyEvaluator()

        assert evaluator.name == "token_efficiency"
        assert "token" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_tokens(self):
        """Test evaluation with no token usage."""
        trace = Trace(
            trace_id="test",
            spans=[{"span_id": "1", "name": "root", "parent_id": None, "metadata": {}}],
        )

        evaluator = TokenEfficiencyEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["efficiency_ratio"].value == 1.0
        assert result.metadata["total_tokens"] == 0
        assert "no token usage" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_efficient_token_usage(self, trace_with_tokens):
        """Test evaluation with efficient token usage."""
        # Total tokens = 800, baseline = 1000
        evaluator = TokenEfficiencyEvaluator(baseline_tokens=1000, threshold=0.7)
        result = await evaluator.evaluate(trace_with_tokens)

        # Should be efficient (using less than baseline)
        assert result.scores["efficiency_ratio"].value == 1.0
        assert result.metadata["total_tokens"] == 800
        assert result.metadata["baseline_tokens"] == 1000
        assert "efficient" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_excessive_token_usage(self, trace_excessive_tokens):
        """Test evaluation with excessive token usage."""
        # Total tokens = 5000, baseline = 1000, max ratio = 1.5
        evaluator = TokenEfficiencyEvaluator(
            baseline_tokens=1000, max_acceptable_ratio=1.5, threshold=0.7
        )
        result = await evaluator.evaluate(trace_excessive_tokens)

        # Should be inefficient (5x baseline, well over max ratio of 1.5)
        assert result.scores["efficiency_ratio"].value == 0.0
        assert result.metadata["total_tokens"] == 5000
        assert "excessive" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_llm_spans_metadata(self, trace_with_tokens):
        """Test that LLM spans are tracked in metadata."""
        evaluator = TokenEfficiencyEvaluator()
        result = await evaluator.evaluate(trace_with_tokens)

        assert "llm_spans" in result.metadata
        llm_spans = result.metadata["llm_spans"]
        assert len(llm_spans) == 2
        assert all("tokens" in span for span in llm_spans)

    @pytest.mark.asyncio
    async def test_actual_ratio_calculation(self):
        """Test actual ratio calculation."""
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "llm_call",
                    "parent_id": None,
                    "metadata": {"tokens": 1200},
                }
            ],
        )

        # 1200 tokens vs 1000 baseline = 1.2 ratio
        evaluator = TokenEfficiencyEvaluator(baseline_tokens=1000)
        result = await evaluator.evaluate(trace)

        assert result.metadata["actual_ratio"] == 1.2
        # Score should be between 0 and 1 (not perfect but not terrible)
        assert 0.0 < result.scores["efficiency_ratio"].value < 1.0


class TestLatencyEvaluator:
    """Tests for LatencyEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = LatencyEvaluator()

        assert evaluator.name == "latency"
        assert "latency" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_root_span(self):
        """Test handling of trace without root span."""
        trace = Trace(
            trace_id="test", spans=[{"span_id": "1", "name": "child", "parent_id": "0"}]
        )

        evaluator = LatencyEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["latency"].value == 0.0
        assert "no root span" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_low_latency(self):
        """Test evaluation with low latency."""
        trace = Trace(
            trace_id="test",
            spans=[
                {"span_id": "1", "name": "root", "parent_id": None, "duration": 0.5}
            ],
        )

        # Latency well below thresholds
        evaluator = LatencyEvaluator(
            latency_thresholds={"p50": 2.0, "p95": 5.0, "p99": 10.0}
        )
        result = await evaluator.evaluate(trace)

        # Should have perfect scores
        assert result.scores["latency"].value == 1.0
        assert result.scores["p50"].value == 1.0
        assert result.scores["p95"].value == 1.0
        assert result.scores["p99"].value == 1.0

    @pytest.mark.asyncio
    async def test_high_latency(self):
        """Test evaluation with high latency."""
        trace = Trace(
            trace_id="test",
            spans=[
                {"span_id": "1", "name": "root", "parent_id": None, "duration": 15.0}
            ],
        )

        # Latency well above thresholds
        evaluator = LatencyEvaluator(
            latency_thresholds={"p50": 2.0, "p95": 5.0, "p99": 10.0}
        )
        result = await evaluator.evaluate(trace)

        # Should have low scores
        assert result.scores["latency"].value < 0.5

    @pytest.mark.asyncio
    async def test_percentile_calculation(self, trace_with_latency):
        """Test percentile calculation."""
        evaluator = LatencyEvaluator()
        result = await evaluator.evaluate(trace_with_latency)

        assert "p50" in result.metadata
        assert "p95" in result.metadata
        assert "p99" in result.metadata
        assert "total_duration" in result.metadata
        assert result.metadata["total_duration"] == 3.5

    @pytest.mark.asyncio
    async def test_span_type_thresholds(self, trace_with_latency):
        """Test span-type specific thresholds."""
        span_thresholds = {"llm_call": 1.5, "tool_use": 0.8}

        evaluator = LatencyEvaluator(span_type_thresholds=span_thresholds)
        result = await evaluator.evaluate(trace_with_latency)

        # LLM call took 2.0s, threshold is 1.5s - should be flagged
        # tool_use took 1.0s, threshold is 0.8s - should be flagged
        slow_spans = result.metadata.get("slow_spans", [])
        assert len(slow_spans) == 2

    @pytest.mark.asyncio
    async def test_feedback_format(self, trace_with_latency):
        """Test feedback message format."""
        evaluator = LatencyEvaluator()
        result = await evaluator.evaluate(trace_with_latency)

        feedback = result.feedback
        assert "3.5" in feedback  # Total duration
        assert "p50" in feedback
        assert "p95" in feedback
        assert "p99" in feedback


class TestTrajectoryOptimalityEvaluator:
    """Tests for TrajectoryOptimalityEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = TrajectoryOptimalityEvaluator()

        assert evaluator.name == "trajectory_optimality"
        assert "optimal" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_empty_trace(self):
        """Test evaluation with empty trace."""
        trace = Trace(trace_id="test", spans=[])

        evaluator = TrajectoryOptimalityEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["optimality"].value == 0.0
        assert "no spans" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_optimal_trajectory(self):
        """Test evaluation with optimal trajectory."""
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "status": "completed",
                },
                {
                    "span_id": "2",
                    "name": "search",
                    "parent_id": "1",
                    "status": "completed",
                    "metadata": {"input": "query1"},
                },
                {
                    "span_id": "3",
                    "name": "process",
                    "parent_id": "1",
                    "status": "completed",
                },
            ],
        )

        evaluator = TrajectoryOptimalityEvaluator(threshold=0.7)
        result = await evaluator.evaluate(trace)

        # No inefficiencies, should be optimal
        assert result.scores["optimality"].value == 1.0
        assert result.metadata["total_inefficiencies"] == 0
        assert "optimal" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_with_redundant_calls(self, trace_with_loops):
        """Test detection of redundant calls."""
        evaluator = TrajectoryOptimalityEvaluator()
        result = await evaluator.evaluate(trace_with_loops)

        # Should detect redundancy
        assert result.metadata["total_inefficiencies"] > 0
        redundant_calls = result.metadata["redundant_calls"]
        assert len(redundant_calls) > 0

    @pytest.mark.asyncio
    async def test_with_loops(self):
        """Test detection of loops."""
        trace = Trace(
            trace_id="test",
            spans=[
                {"span_id": f"{i}", "name": "retry", "parent_id": None}
                for i in range(5)
            ],  # 5 consecutive retries
        )

        evaluator = TrajectoryOptimalityEvaluator()
        result = await evaluator.evaluate(trace)

        loops = result.metadata["loops"]
        assert len(loops) > 0
        assert "loop" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_with_retries(self, trace_with_loops):
        """Test detection of retry/error spans."""
        evaluator = TrajectoryOptimalityEvaluator()
        result = await evaluator.evaluate(trace_with_loops)

        assert result.metadata["retries"] == 1  # One retry span

    @pytest.mark.asyncio
    async def test_inefficiency_penalty(self, trace_with_loops):
        """Test that inefficiencies lower the score."""
        evaluator = TrajectoryOptimalityEvaluator()
        result = await evaluator.evaluate(trace_with_loops)

        # Should have reduced score due to inefficiencies
        assert result.scores["optimality"].value < 1.0
        assert result.metadata["total_inefficiencies"] > 0

    @pytest.mark.asyncio
    async def test_feedback_details(self, trace_with_loops):
        """Test that feedback includes inefficiency details."""
        evaluator = TrajectoryOptimalityEvaluator()
        result = await evaluator.evaluate(trace_with_loops)

        feedback = result.feedback.lower()
        # Should mention specific inefficiencies
        assert any(
            keyword in feedback
            for keyword in ["redundant", "loop", "retry", "inefficien"]
        )
