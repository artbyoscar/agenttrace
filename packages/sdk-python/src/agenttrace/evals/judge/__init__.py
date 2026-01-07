"""LLM-as-Judge infrastructure for AgentTrace evaluators.

This module provides a robust, production-ready system for using LLMs to evaluate
AI agent outputs. It supports multiple providers (OpenAI, Anthropic, Together.ai),
includes retry logic, rate limiting, cost tracking, and response caching.

Core Components:
    - JudgeClient: Main client for making judgment requests
    - JudgeConfig: Configuration for judge clients
    - Judgment: Parsed judgment result with score and reasoning
    - Prompt templates: Pre-built prompts for common evaluation tasks
    - Cost tracking: Automatic tracking of token usage and costs

Example:
    Basic usage with OpenAI:
        >>> from agenttrace.evals.judge import JudgeClient, JudgeConfig, COMPLETENESS_PROMPT
        >>>
        >>> config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        >>> client = JudgeClient(config)
        >>>
        >>> prompt = COMPLETENESS_PROMPT.format(
        ...     input="What is Python?",
        ...     output="Python is a programming language."
        ... )
        >>>
        >>> judgment = await client.judge(prompt)
        >>> print(f"Score: {judgment.score:.2f}")
        >>> print(f"Reasoning: {judgment.reasoning}")

    Using preset configurations:
        >>> from agenttrace.evals.judge import get_default_config
        >>>
        >>> config = get_default_config("fast")  # Uses gpt-4o-mini
        >>> client = JudgeClient(config)

    Tracking costs:
        >>> from agenttrace.evals.judge import get_global_tracker
        >>>
        >>> tracker = get_global_tracker()
        >>> print(f"Total cost: ${tracker.total_cost:.4f}")
        >>> print(tracker.get_summary())

    Environment-based configuration:
        >>> # Set environment variables:
        >>> # OPENAI_API_KEY=sk-...
        >>> # JUDGE_MODEL=gpt-4o
        >>>
        >>> config = create_config_from_env()
        >>> client = JudgeClient(config)
"""

from .config import (
    JudgeConfig,
    DEFAULT_CONFIGS,
    get_default_config,
    create_config_from_env,
)

from .client import (
    JudgeClient,
    MockJudgeClient,
)

from .parser import (
    Judgment,
    JudgmentParser,
    parse_judgment,
)

from .costs import (
    TokenUsage,
    JudgmentCost,
    CostTracker,
    get_global_tracker,
    reset_global_tracker,
    MODEL_PRICING,
)

from .prompts import (
    SYSTEM_PROMPT,
    COMPLETENESS_PROMPT,
    RELEVANCE_PROMPT,
    COHERENCE_PROMPT,
    TOOL_SELECTION_PROMPT,
    FACTUAL_ACCURACY_PROMPT,
    TRAJECTORY_OPTIMALITY_PROMPT,
    format_prompt,
    get_prompt_for_task,
)

__all__ = [
    # Configuration
    "JudgeConfig",
    "DEFAULT_CONFIGS",
    "get_default_config",
    "create_config_from_env",
    # Client
    "JudgeClient",
    "MockJudgeClient",
    # Parser
    "Judgment",
    "JudgmentParser",
    "parse_judgment",
    # Costs
    "TokenUsage",
    "JudgmentCost",
    "CostTracker",
    "get_global_tracker",
    "reset_global_tracker",
    "MODEL_PRICING",
    # Prompts
    "SYSTEM_PROMPT",
    "COMPLETENESS_PROMPT",
    "RELEVANCE_PROMPT",
    "COHERENCE_PROMPT",
    "TOOL_SELECTION_PROMPT",
    "FACTUAL_ACCURACY_PROMPT",
    "TRAJECTORY_OPTIMALITY_PROMPT",
    "format_prompt",
    "get_prompt_for_task",
]

__version__ = "0.1.0"
