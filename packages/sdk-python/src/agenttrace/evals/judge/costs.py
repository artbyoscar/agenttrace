"""Cost tracking for LLM-as-judge evaluations."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import threading


# Pricing per 1M tokens (as of January 2025)
# Prices in USD
MODEL_PRICING = {
    # OpenAI GPT-4o
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-2024-11-20": {"input": 2.50, "output": 10.00},
    # OpenAI GPT-4o-mini
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "gpt-4o-mini-2024-07-18": {"input": 0.150, "output": 0.600},
    # Anthropic Claude 3 Opus
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    # Anthropic Claude 3.5 Sonnet
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
    # Anthropic Claude 3.5 Haiku
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    # Anthropic Claude 3 Sonnet (older)
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    # Anthropic Claude 3 Haiku (older)
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}


@dataclass
class TokenUsage:
    """Token usage information for a single judgment.

    Attributes:
        prompt_tokens: Input tokens
        completion_tokens: Output tokens
        total_tokens: Total tokens (prompt + completion)
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int = field(init=False)

    def __post_init__(self):
        """Calculate total tokens."""
        self.total_tokens = self.prompt_tokens + self.completion_tokens


@dataclass
class JudgmentCost:
    """Cost information for a single judgment.

    Attributes:
        model: Model name
        usage: Token usage
        input_cost: Cost of input tokens (USD)
        output_cost: Cost of output tokens (USD)
        total_cost: Total cost (USD)
        timestamp: When judgment was made
    """

    model: str
    usage: TokenUsage
    input_cost: float = field(init=False)
    output_cost: float = field(init=False)
    total_cost: float = field(init=False)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Calculate costs based on model pricing."""
        pricing = MODEL_PRICING.get(self.model)

        if pricing is None:
            # Unknown model - use average pricing
            pricing = {"input": 2.0, "output": 10.0}

        # Calculate costs (pricing is per 1M tokens)
        self.input_cost = (self.usage.prompt_tokens / 1_000_000) * pricing["input"]
        self.output_cost = (
            self.usage.completion_tokens / 1_000_000
        ) * pricing["output"]
        self.total_cost = self.input_cost + self.output_cost


class CostTracker:
    """Thread-safe cost tracker for judgment operations.

    Tracks token usage and costs across multiple judgments.

    Example:
        >>> tracker = CostTracker()
        >>> usage = TokenUsage(prompt_tokens=500, completion_tokens=100)
        >>> tracker.record_judgment("gpt-4o-mini", usage)
        >>> print(f"Total cost: ${tracker.total_cost:.4f}")
    """

    def __init__(self, cost_threshold: Optional[float] = None):
        """Initialize the cost tracker.

        Args:
            cost_threshold: Optional threshold in USD to trigger warnings
        """
        self._judgments: List[JudgmentCost] = []
        self._lock = threading.Lock()
        self._cost_threshold = cost_threshold

    def record_judgment(self, model: str, usage: TokenUsage) -> JudgmentCost:
        """Record a judgment and its costs.

        Args:
            model: Model name
            usage: Token usage information

        Returns:
            JudgmentCost object

        Raises:
            Warning: If cost threshold is exceeded
        """
        cost = JudgmentCost(model=model, usage=usage)

        with self._lock:
            self._judgments.append(cost)

            # Check threshold
            if self._cost_threshold is not None:
                if self.total_cost > self._cost_threshold:
                    import warnings

                    warnings.warn(
                        f"Cost threshold exceeded: ${self.total_cost:.4f} > ${self._cost_threshold:.4f}",
                        UserWarning,
                    )

        return cost

    @property
    def total_cost(self) -> float:
        """Get total cost across all judgments.

        Returns:
            Total cost in USD
        """
        with self._lock:
            return sum(j.total_cost for j in self._judgments)

    @property
    def total_tokens(self) -> int:
        """Get total tokens used across all judgments.

        Returns:
            Total token count
        """
        with self._lock:
            return sum(j.usage.total_tokens for j in self._judgments)

    @property
    def judgment_count(self) -> int:
        """Get number of judgments recorded.

        Returns:
            Number of judgments
        """
        with self._lock:
            return len(self._judgments)

    def get_costs_by_model(self) -> Dict[str, float]:
        """Get costs broken down by model.

        Returns:
            Dictionary mapping model name to total cost
        """
        costs_by_model: Dict[str, float] = {}

        with self._lock:
            for judgment in self._judgments:
                if judgment.model not in costs_by_model:
                    costs_by_model[judgment.model] = 0.0
                costs_by_model[judgment.model] += judgment.total_cost

        return costs_by_model

    def get_usage_by_model(self) -> Dict[str, Dict[str, int]]:
        """Get token usage broken down by model.

        Returns:
            Dictionary mapping model to usage stats
        """
        usage_by_model: Dict[str, Dict[str, int]] = {}

        with self._lock:
            for judgment in self._judgments:
                if judgment.model not in usage_by_model:
                    usage_by_model[judgment.model] = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "count": 0,
                    }

                stats = usage_by_model[judgment.model]
                stats["prompt_tokens"] += judgment.usage.prompt_tokens
                stats["completion_tokens"] += judgment.usage.completion_tokens
                stats["total_tokens"] += judgment.usage.total_tokens
                stats["count"] += 1

        return usage_by_model

    def get_summary(self) -> Dict[str, any]:
        """Get a summary of costs and usage.

        Returns:
            Dictionary with summary statistics
        """
        with self._lock:
            return {
                "total_cost": self.total_cost,
                "total_tokens": self.total_tokens,
                "judgment_count": self.judgment_count,
                "average_cost_per_judgment": (
                    self.total_cost / self.judgment_count
                    if self.judgment_count > 0
                    else 0.0
                ),
                "costs_by_model": self.get_costs_by_model(),
                "usage_by_model": self.get_usage_by_model(),
            }

    def reset(self):
        """Reset all tracked costs and usage."""
        with self._lock:
            self._judgments.clear()

    def __repr__(self) -> str:
        """String representation of the tracker."""
        return (
            f"CostTracker(judgments={self.judgment_count}, "
            f"total_cost=${self.total_cost:.4f}, "
            f"total_tokens={self.total_tokens})"
        )


# Global cost tracker instance
_global_tracker: Optional[CostTracker] = None
_tracker_lock = threading.Lock()


def get_global_tracker() -> CostTracker:
    """Get the global cost tracker instance.

    Returns:
        Global CostTracker instance

    Example:
        >>> from agenttrace.evals.judge import get_global_tracker
        >>> tracker = get_global_tracker()
        >>> print(tracker.get_summary())
    """
    global _global_tracker

    if _global_tracker is None:
        with _tracker_lock:
            if _global_tracker is None:
                _global_tracker = CostTracker()

    return _global_tracker


def reset_global_tracker():
    """Reset the global cost tracker (primarily for testing)."""
    global _global_tracker

    with _tracker_lock:
        _global_tracker = None
