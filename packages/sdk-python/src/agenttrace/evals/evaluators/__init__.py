"""Built-in evaluators for common agent quality dimensions.

This module provides a comprehensive suite of evaluators covering:
- Response quality (completeness, relevance, coherence)
- Tool usage (accuracy, selection appropriateness)
- Efficiency (token usage, latency, trajectory optimality)
- Safety (PII detection, harmful content)
- Domain-specific (factual accuracy for RAG, code correctness)

All evaluators inherit from the base Evaluator class and are automatically
registered when imported.

Example:
    >>> from agenttrace.evals.evaluators import ResponseCompletenessEvaluator
    >>> from agenttrace.evals import get_registry
    >>>
    >>> # Evaluator is automatically registered
    >>> registry = get_registry()
    >>> evaluator = registry.get("response_completeness")
    >>>
    >>> # Or create directly
    >>> evaluator = ResponseCompletenessEvaluator()
    >>> result = await evaluator.evaluate(trace)
"""

# Response quality evaluators
from .response import (
    ResponseCompletenessEvaluator,
    ResponseRelevanceEvaluator,
    ResponseCoherenceEvaluator,
)

# Tool usage evaluators
from .tools import (
    ToolCallAccuracyEvaluator,
    ToolSelectionEvaluator,
)

# Efficiency evaluators
from .efficiency import (
    TokenEfficiencyEvaluator,
    LatencyEvaluator,
    TrajectoryOptimalityEvaluator,
)

# Safety evaluators
from .safety import (
    PIIDetectionEvaluator,
    HarmfulContentEvaluator,
)

# Domain-specific evaluators
from .domain import (
    FactualAccuracyEvaluator,
    CodeCorrectnessEvaluator,
)

# LLM judge utilities (for advanced users)
from ._llm_judge import (
    JudgeConfig,
    LLMClient,
    SimpleLLMClient,
    judge_with_llm,
    create_judge_prompt,
)

__all__ = [
    # Response quality
    "ResponseCompletenessEvaluator",
    "ResponseRelevanceEvaluator",
    "ResponseCoherenceEvaluator",
    # Tool usage
    "ToolCallAccuracyEvaluator",
    "ToolSelectionEvaluator",
    # Efficiency
    "TokenEfficiencyEvaluator",
    "LatencyEvaluator",
    "TrajectoryOptimalityEvaluator",
    # Safety
    "PIIDetectionEvaluator",
    "HarmfulContentEvaluator",
    # Domain-specific
    "FactualAccuracyEvaluator",
    "CodeCorrectnessEvaluator",
    # LLM judge utilities
    "JudgeConfig",
    "LLMClient",
    "SimpleLLMClient",
    "judge_with_llm",
    "create_judge_prompt",
]
