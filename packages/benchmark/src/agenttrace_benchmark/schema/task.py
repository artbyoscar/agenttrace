"""
Task Schema Definition for AgentTrace Benchmark

This module defines the comprehensive schema for benchmark tasks, ensuring
consistency, reproducibility, and academic rigor across all evaluations.

The schema is designed to support:
- Automated evaluation with objective metrics
- Human evaluation when necessary
- Version control and task evolution
- Statistical analysis and meta-learning
- Fair comparison across different agent architectures
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from ..categories import BenchmarkCategory


class DifficultyLevel(str, Enum):
    """
    Task difficulty classification based on cognitive load and solution complexity.

    Levels are calibrated such that:
    - BASIC: Single-step tasks, minimal reasoning, common patterns
    - INTERMEDIATE: Multi-step tasks, moderate reasoning, some edge cases
    - ADVANCED: Complex tasks, deep reasoning, multiple edge cases, domain knowledge
    - EXPERT: Research-level tasks, novel problem solving, significant uncertainty
    """

    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class EvaluationType(str, Enum):
    """
    Method used to evaluate task completion.

    - EXACT_MATCH: Output must match reference exactly (string comparison)
    - SEMANTIC_MATCH: Output must be semantically equivalent (embedding similarity)
    - FUNCTIONAL_MATCH: Output must produce correct behavior (unit tests)
    - RUBRIC_BASED: Output evaluated against detailed rubric (may include human eval)
    - CUSTOM: Task-specific evaluation function provided
    """

    EXACT_MATCH = "exact_match"
    SEMANTIC_MATCH = "semantic_match"
    FUNCTIONAL_MATCH = "functional_match"
    RUBRIC_BASED = "rubric_based"
    CUSTOM = "custom"


class TaskStatus(str, Enum):
    """
    Lifecycle status of a benchmark task.

    - DRAFT: Under development, not yet validated
    - REVIEW: Pending expert review
    - ACTIVE: In public benchmark suite
    - HELD_OUT: In private test set (never publicly released)
    - DEPRECATED: Removed from active use (but retained for historical analysis)
    - RETIRED: Permanently removed due to data leakage or other issues
    """

    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    HELD_OUT = "held_out"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass
class ToolRequirement:
    """
    Specification of a tool that must be available to the agent.

    Attributes:
        tool_name: Identifier for the tool (e.g., "web_search", "calculator")
        tool_type: Category of tool (e.g., "api", "function", "retrieval")
        version: Specific version requirement if applicable
        configuration: Required configuration parameters
        required: Whether task is impossible without this tool
    """

    tool_name: str
    tool_type: str
    version: Optional[str] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    required: bool = True


@dataclass
class EvaluationCriterion:
    """
    A single dimension on which task performance is measured.

    Attributes:
        name: Identifier for this criterion
        description: What aspect of performance this measures
        weight: Importance in overall task score (weights should sum to 1.0)
        measurement_type: How this is quantified (e.g., "binary", "continuous", "discrete")
        rubric: Detailed scoring guidelines for human evaluators
        automated_check: Optional function name for automated evaluation
    """

    name: str
    description: str
    weight: float
    measurement_type: str
    rubric: Optional[str] = None
    automated_check: Optional[str] = None


@dataclass
class TaskMetadata:
    """
    Versioning and provenance information for a task.

    Attributes:
        version: Semantic version of this task (MAJOR.MINOR.PATCH)
        created_at: ISO timestamp of initial task creation
        updated_at: ISO timestamp of most recent modification
        author: Primary task author(s)
        reviewers: Experts who validated this task
        citations: Academic papers or resources that inspired task
        changelog: Version history and modifications
        tags: Searchable keywords for task categorization
    """

    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    author: List[str] = field(default_factory=list)
    reviewers: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    changelog: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class ReferenceSolution:
    """
    Gold standard solution used for evaluation (held out from public release).

    Attributes:
        solution_text: The reference answer or approach
        reasoning_trace: Step-by-step reasoning that leads to solution
        tool_calls: Expected sequence of tool invocations
        alternative_solutions: Other valid approaches to solving the task
        common_errors: Typical mistakes agents make on this task
        solution_hash: SHA-256 hash of solution for verification without exposure
    """

    solution_text: Optional[str] = None
    reasoning_trace: Optional[List[str]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    alternative_solutions: List[str] = field(default_factory=list)
    common_errors: List[str] = field(default_factory=list)
    solution_hash: Optional[str] = None


@dataclass
class BenchmarkTask:
    """
    Complete specification of a benchmark evaluation task.

    This is the core data structure for all benchmark tasks. It includes everything
    needed to:
    1. Present the task to an agent
    2. Execute the agent's solution
    3. Evaluate the quality of the output
    4. Track task provenance and evolution
    5. Enable meta-analysis across tasks

    Design Principles:
    - Self-contained: All information needed for evaluation is present
    - Versioned: Changes are tracked with semantic versioning
    - Reproducible: Identical setup across different evaluation runs
    - Extensible: New fields can be added without breaking existing tasks
    - Privacy-preserving: Reference solutions can be held out

    Attributes:
        task_id: Unique identifier (UUID v4)
        category: Primary evaluation category
        subcategory: Specific skill being assessed
        difficulty: Cognitive complexity level
        name: Short, descriptive task name
        description: Detailed explanation of what the task evaluates
        prompt: The actual task presented to the agent
        input_format: Expected structure of task inputs
        output_format: Expected structure of task outputs
        evaluation_type: Method used to score outputs
        evaluation_criteria: Detailed scoring dimensions
        reference_solution: Gold standard answer (may be held out)
        time_limit_seconds: Maximum wall-clock time allowed
        token_budget: Maximum tokens agent may use (input + output)
        required_tools: Tools that must be available
        context_files: Additional files/data provided to agent
        status: Current lifecycle status
        metadata: Versioning and provenance
        custom_evaluator: Optional custom evaluation function
        examples: Few-shot examples (if applicable)
        constraints: Additional requirements or restrictions
    """

    # Core identification
    task_id: UUID = field(default_factory=uuid4)
    category: BenchmarkCategory = BenchmarkCategory.REASONING
    subcategory: str = ""
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE

    # Task content
    name: str = ""
    description: str = ""
    prompt: str = ""

    # Format specifications
    input_format: Dict[str, Any] = field(default_factory=dict)
    output_format: Dict[str, Any] = field(default_factory=dict)

    # Evaluation
    evaluation_type: EvaluationType = EvaluationType.EXACT_MATCH
    evaluation_criteria: List[EvaluationCriterion] = field(default_factory=list)
    reference_solution: Optional[ReferenceSolution] = None

    # Resource constraints
    time_limit_seconds: int = 300  # 5 minutes default
    token_budget: Optional[int] = None

    # Tool requirements
    required_tools: List[ToolRequirement] = field(default_factory=list)

    # Additional context
    context_files: Dict[str, str] = field(default_factory=dict)
    examples: List[Dict[str, str]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    # Lifecycle
    status: TaskStatus = TaskStatus.DRAFT
    metadata: TaskMetadata = field(default_factory=TaskMetadata)

    # Extensibility
    custom_evaluator: Optional[str] = None
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate task specification after initialization."""
        self._validate_criteria_weights()
        self._validate_resource_constraints()

    def _validate_criteria_weights(self) -> None:
        """Ensure evaluation criteria weights sum to 1.0."""
        if self.evaluation_criteria:
            total_weight = sum(c.weight for c in self.evaluation_criteria)
            if abs(total_weight - 1.0) > 1e-6:
                raise ValueError(
                    f"Evaluation criteria weights must sum to 1.0, got {total_weight}"
                )

    def _validate_resource_constraints(self) -> None:
        """Check that resource constraints are reasonable."""
        if self.time_limit_seconds <= 0:
            raise ValueError("time_limit_seconds must be positive")
        if self.token_budget is not None and self.token_budget <= 0:
            raise ValueError("token_budget must be positive if specified")

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize task to dictionary format.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "task_id": str(self.task_id),
            "category": self.category.value,
            "subcategory": self.subcategory,
            "difficulty": self.difficulty.value,
            "name": self.name,
            "description": self.description,
            "prompt": self.prompt,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "evaluation_type": self.evaluation_type.value,
            "evaluation_criteria": [
                {
                    "name": c.name,
                    "description": c.description,
                    "weight": c.weight,
                    "measurement_type": c.measurement_type,
                    "rubric": c.rubric,
                    "automated_check": c.automated_check,
                }
                for c in self.evaluation_criteria
            ],
            "time_limit_seconds": self.time_limit_seconds,
            "token_budget": self.token_budget,
            "required_tools": [
                {
                    "tool_name": t.tool_name,
                    "tool_type": t.tool_type,
                    "version": t.version,
                    "configuration": t.configuration,
                    "required": t.required,
                }
                for t in self.required_tools
            ],
            "context_files": self.context_files,
            "examples": self.examples,
            "constraints": self.constraints,
            "status": self.status.value,
            "metadata": {
                "version": self.metadata.version,
                "created_at": self.metadata.created_at.isoformat(),
                "updated_at": self.metadata.updated_at.isoformat(),
                "author": self.metadata.author,
                "reviewers": self.metadata.reviewers,
                "citations": self.metadata.citations,
                "changelog": self.metadata.changelog,
                "tags": self.metadata.tags,
            },
            "custom_evaluator": self.custom_evaluator,
            "extra_fields": self.extra_fields,
        }

    def is_public(self) -> bool:
        """Check if this task is in the public benchmark suite."""
        return self.status in [TaskStatus.ACTIVE, TaskStatus.DEPRECATED]

    def is_held_out(self) -> bool:
        """Check if this task is in the private test set."""
        return self.status == TaskStatus.HELD_OUT

    def get_difficulty_score(self) -> int:
        """
        Get numeric difficulty score for analysis.

        Returns:
            Integer from 1-4 representing difficulty
        """
        difficulty_map = {
            DifficultyLevel.BASIC: 1,
            DifficultyLevel.INTERMEDIATE: 2,
            DifficultyLevel.ADVANCED: 3,
            DifficultyLevel.EXPERT: 4,
        }
        return difficulty_map[self.difficulty]


@dataclass
class TaskSuite:
    """
    Collection of related benchmark tasks with aggregate metadata.

    Attributes:
        suite_id: Unique identifier for this suite
        name: Descriptive name (e.g., "Q1 2024 Public Benchmark")
        description: Purpose and scope of this suite
        tasks: List of tasks in this suite
        version: Suite version
        created_at: When suite was assembled
        is_public: Whether this suite is publicly available
        category_distribution: Target distribution across categories
    """

    suite_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    tasks: List[BenchmarkTask] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_public: bool = True
    category_distribution: Optional[Dict[BenchmarkCategory, float]] = None

    def get_tasks_by_category(self, category: BenchmarkCategory) -> List[BenchmarkTask]:
        """Get all tasks in a specific category."""
        return [task for task in self.tasks if task.category == category]

    def get_tasks_by_difficulty(self, difficulty: DifficultyLevel) -> List[BenchmarkTask]:
        """Get all tasks at a specific difficulty level."""
        return [task for task in self.tasks if task.difficulty == difficulty]

    def validate_distribution(self) -> bool:
        """
        Check if task distribution matches target distribution.

        Returns:
            True if distribution is within acceptable tolerance
        """
        if not self.category_distribution:
            return True

        actual_dist = {}
        for category in BenchmarkCategory:
            count = len(self.get_tasks_by_category(category))
            actual_dist[category] = count / len(self.tasks) if self.tasks else 0

        # Check if actual distribution is within 5% of target
        for category, target_pct in self.category_distribution.items():
            actual_pct = actual_dist.get(category, 0)
            if abs(actual_pct - target_pct) > 0.05:
                return False

        return True


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
