"""
AgentTrace Benchmark - Academic-Grade AI Agent Evaluation Suite

This package provides a comprehensive, statistically rigorous benchmark for
evaluating AI agent capabilities across multiple dimensions of performance.

The benchmark is designed to:
1. Provide reliable, reproducible measurements of agent capabilities
2. Support academic research and industry applications
3. Prevent overfitting and gaming through robust anti-gaming measures
4. Enable fair comparison across different agent architectures
5. Track progress in AI agent development over time

Quick Start:
    >>> from agenttrace_benchmark import BenchmarkTask, ScoringEngine
    >>> from agenttrace_benchmark.categories import BenchmarkCategory
    >>>
    >>> # Create a benchmark task
    >>> task = BenchmarkTask(
    ...     category=BenchmarkCategory.REASONING,
    ...     name="Multi-hop QA",
    ...     prompt="Answer the following question..."
    ... )
    >>>
    >>> # Evaluate an agent
    >>> engine = ScoringEngine()
    >>> score = engine.score_task(task, agent_output, execution_time, tokens, tool_calls)

For more information, see the documentation at:
https://docs.agenttrace.dev/benchmark
"""

__version__ = "0.1.0"

# Core categories
from .categories import (
    BenchmarkCategory,
    CategoryDefinition,
    CATEGORY_DEFINITIONS,
    get_category_definition,
)

# Task schema
from .schema import (
    BenchmarkTask,
    DifficultyLevel,
    EvaluationCriterion,
    EvaluationType,
    ReferenceSolution,
    TaskMetadata,
    TaskStatus,
    TaskSuite,
    ToolRequirement,
)

# Scoring framework
from .scoring import CategoryScore, CompositeScore, ScoringEngine, TaskScore

# Anti-gaming measures
from .utils import (
    AnomalyDetector,
    AntiGamingReport,
    ContaminationDetector,
    DiversityChecker,
    HeldOutTestSet,
    SubmissionPolicy,
    TaskRotationManager,
)

__all__ = [
    # Version
    "__version__",
    # Categories
    "BenchmarkCategory",
    "CategoryDefinition",
    "CATEGORY_DEFINITIONS",
    "get_category_definition",
    # Schema
    "BenchmarkTask",
    "TaskSuite",
    "DifficultyLevel",
    "EvaluationType",
    "TaskStatus",
    "ToolRequirement",
    "EvaluationCriterion",
    "TaskMetadata",
    "ReferenceSolution",
    # Scoring
    "ScoringEngine",
    "TaskScore",
    "CategoryScore",
    "CompositeScore",
    # Anti-gaming
    "SubmissionPolicy",
    "HeldOutTestSet",
    "TaskRotationManager",
    "AnomalyDetector",
    "DiversityChecker",
    "ContaminationDetector",
    "AntiGamingReport",
]
