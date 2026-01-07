"""Tests for cost tracking."""

import pytest
from agenttrace.evals.judge.costs import (
    TokenUsage,
    JudgmentCost,
    CostTracker,
    get_global_tracker,
    reset_global_tracker,
    MODEL_PRICING,
)


class TestTokenUsage:
    """Tests for TokenUsage class."""

    def test_create_token_usage(self):
        """Test creating token usage."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_total_tokens_calculated(self):
        """Test that total tokens is auto-calculated."""
        usage = TokenUsage(prompt_tokens=500, completion_tokens=200)

        assert usage.total_tokens == 700


class TestJudgmentCost:
    """Tests for JudgmentCost class."""

    def test_create_judgment_cost_known_model(self):
        """Test creating cost for known model."""
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)
        cost = JudgmentCost(model="gpt-4o-mini", usage=usage)

        # gpt-4o-mini: $0.150 input, $0.600 output per 1M tokens
        expected_input = (1000 / 1_000_000) * 0.150
        expected_output = (500 / 1_000_000) * 0.600
        expected_total = expected_input + expected_output

        assert cost.input_cost == pytest.approx(expected_input, rel=1e-6)
        assert cost.output_cost == pytest.approx(expected_output, rel=1e-6)
        assert cost.total_cost == pytest.approx(expected_total, rel=1e-6)

    def test_create_judgment_cost_unknown_model(self):
        """Test creating cost for unknown model uses default pricing."""
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)
        cost = JudgmentCost(model="unknown-model", usage=usage)

        # Should use default pricing
        assert cost.total_cost > 0

    def test_claude_opus_pricing(self):
        """Test Claude Opus pricing."""
        usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)
        cost = JudgmentCost(model="claude-3-opus-20240229", usage=usage)

        # Claude Opus: $15 input, $75 output per 1M tokens
        expected_input = (1000 / 1_000_000) * 15.0
        expected_output = (500 / 1_000_000) * 75.0

        assert cost.input_cost == pytest.approx(expected_input, rel=1e-6)
        assert cost.output_cost == pytest.approx(expected_output, rel=1e-6)


class TestCostTracker:
    """Tests for CostTracker class."""

    def test_create_tracker(self):
        """Test creating a cost tracker."""
        tracker = CostTracker()

        assert tracker.total_cost == 0.0
        assert tracker.total_tokens == 0
        assert tracker.judgment_count == 0

    def test_record_judgment(self):
        """Test recording a judgment."""
        tracker = CostTracker()
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)

        cost = tracker.record_judgment("gpt-4o-mini", usage)

        assert isinstance(cost, JudgmentCost)
        assert tracker.judgment_count == 1
        assert tracker.total_tokens == 150
        assert tracker.total_cost > 0

    def test_record_multiple_judgments(self):
        """Test recording multiple judgments."""
        tracker = CostTracker()

        for i in range(5):
            usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
            tracker.record_judgment("gpt-4o-mini", usage)

        assert tracker.judgment_count == 5
        assert tracker.total_tokens == 750  # 150 * 5

    def test_costs_by_model(self):
        """Test getting costs broken down by model."""
        tracker = CostTracker()

        # Record for different models
        usage1 = TokenUsage(prompt_tokens=100, completion_tokens=50)
        tracker.record_judgment("gpt-4o-mini", usage1)

        usage2 = TokenUsage(prompt_tokens=200, completion_tokens=100)
        tracker.record_judgment("gpt-4o", usage2)

        usage3 = TokenUsage(prompt_tokens=100, completion_tokens=50)
        tracker.record_judgment("gpt-4o-mini", usage3)

        costs_by_model = tracker.get_costs_by_model()

        assert "gpt-4o-mini" in costs_by_model
        assert "gpt-4o" in costs_by_model
        assert costs_by_model["gpt-4o-mini"] > costs_by_model["gpt-4o"]  # More calls

    def test_usage_by_model(self):
        """Test getting usage broken down by model."""
        tracker = CostTracker()

        usage1 = TokenUsage(prompt_tokens=100, completion_tokens=50)
        tracker.record_judgment("gpt-4o-mini", usage1)

        usage2 = TokenUsage(prompt_tokens=100, completion_tokens=50)
        tracker.record_judgment("gpt-4o-mini", usage2)

        usage_by_model = tracker.get_usage_by_model()

        assert "gpt-4o-mini" in usage_by_model
        stats = usage_by_model["gpt-4o-mini"]
        assert stats["count"] == 2
        assert stats["total_tokens"] == 300
        assert stats["prompt_tokens"] == 200
        assert stats["completion_tokens"] == 100

    def test_get_summary(self):
        """Test getting cost summary."""
        tracker = CostTracker()

        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        tracker.record_judgment("gpt-4o-mini", usage)

        summary = tracker.get_summary()

        assert "total_cost" in summary
        assert "total_tokens" in summary
        assert "judgment_count" in summary
        assert "average_cost_per_judgment" in summary
        assert "costs_by_model" in summary
        assert "usage_by_model" in summary

    def test_reset(self):
        """Test resetting the tracker."""
        tracker = CostTracker()

        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        tracker.record_judgment("gpt-4o-mini", usage)

        assert tracker.judgment_count == 1

        tracker.reset()

        assert tracker.judgment_count == 0
        assert tracker.total_cost == 0.0
        assert tracker.total_tokens == 0

    def test_cost_threshold_warning(self):
        """Test that cost threshold triggers warning."""
        tracker = CostTracker(cost_threshold=0.001)  # Very low threshold

        usage = TokenUsage(prompt_tokens=10000, completion_tokens=5000)

        with pytest.warns(UserWarning, match="Cost threshold exceeded"):
            tracker.record_judgment("gpt-4o-mini", usage)

    def test_repr(self):
        """Test string representation."""
        tracker = CostTracker()

        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        tracker.record_judgment("gpt-4o-mini", usage)

        repr_str = repr(tracker)

        assert "CostTracker" in repr_str
        assert "judgments=1" in repr_str
        assert "total_tokens=150" in repr_str


class TestGlobalTracker:
    """Tests for global tracker functions."""

    def test_get_global_tracker(self):
        """Test getting global tracker."""
        reset_global_tracker()

        tracker = get_global_tracker()

        assert isinstance(tracker, CostTracker)

    def test_global_tracker_singleton(self):
        """Test that global tracker is a singleton."""
        reset_global_tracker()

        tracker1 = get_global_tracker()
        tracker2 = get_global_tracker()

        assert tracker1 is tracker2

    def test_global_tracker_persists(self):
        """Test that global tracker persists across calls."""
        reset_global_tracker()

        tracker1 = get_global_tracker()
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        tracker1.record_judgment("gpt-4o-mini", usage)

        tracker2 = get_global_tracker()

        assert tracker2.judgment_count == 1

    def test_reset_global_tracker(self):
        """Test resetting global tracker."""
        tracker1 = get_global_tracker()
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)
        tracker1.record_judgment("gpt-4o-mini", usage)

        reset_global_tracker()

        tracker2 = get_global_tracker()

        # Should be a new instance
        assert tracker2.judgment_count == 0
