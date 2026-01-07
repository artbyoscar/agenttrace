"""Schema definitions for benchmark tasks and evaluations."""

from .task import (
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

__all__ = [
    "BenchmarkTask",
    "TaskSuite",
    "DifficultyLevel",
    "EvaluationType",
    "TaskStatus",
    "ToolRequirement",
    "EvaluationCriterion",
    "TaskMetadata",
    "ReferenceSolution",
]
