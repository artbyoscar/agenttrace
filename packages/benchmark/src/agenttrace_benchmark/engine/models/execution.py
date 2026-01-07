"""
Execution result models for benchmark runs.

These models capture the complete execution trace of benchmark tasks,
enabling detailed analysis, debugging, and reproducibility.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class ExecutionStatus(str, Enum):
    """Status of a benchmark execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class FailureReason(str, Enum):
    """Categorized reasons for execution failure."""
    AGENT_ERROR = "agent_error"              # Agent raised exception
    AGENT_TIMEOUT = "agent_timeout"          # Exceeded time limit
    AGENT_UNREACHABLE = "agent_unreachable"  # Network error
    RESOURCE_EXCEEDED = "resource_exceeded"  # Token/memory limit
    INVALID_OUTPUT = "invalid_output"        # Malformed response
    SECURITY_VIOLATION = "security_violation" # Attempted prohibited operation
    INTERNAL_ERROR = "internal_error"        # Evaluation system error


@dataclass
class ToolCall:
    """Record of a single tool invocation during task execution."""
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: datetime
    duration_seconds: float
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class ResourceUsage:
    """Resource consumption during task execution."""
    tokens_input: int
    tokens_output: int
    tokens_total: int
    execution_time_seconds: float
    tool_calls_count: int
    api_calls_count: int
    memory_peak_mb: float

    def exceeds_budget(self, token_budget: Optional[int], time_budget: float) -> bool:
        """Check if resource usage exceeds budgets."""
        if token_budget and self.tokens_total > token_budget:
            return True
        if self.execution_time_seconds > time_budget:
            return True
        return False


@dataclass
class TaskExecution:
    """
    Complete record of executing a single task against an agent.

    Captures everything needed for evaluation, debugging, and reproducibility.
    """
    execution_id: UUID = field(default_factory=uuid4)
    task_id: UUID = field(default=UUID(int=0))
    submission_id: str = ""

    # Execution lifecycle
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Agent interaction
    agent_input: str = ""
    agent_output: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)

    # Resource tracking
    resource_usage: Optional[ResourceUsage] = None

    # Error handling
    failure_reason: Optional[FailureReason] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    # Evaluation (populated by scoring engine)
    raw_score: Optional[float] = None
    normalized_score: Optional[float] = None
    criterion_scores: Dict[str, float] = field(default_factory=dict)

    # Reproducibility
    environment_snapshot: Dict[str, Any] = field(default_factory=dict)
    random_seed: Optional[int] = None

    def duration_seconds(self) -> float:
        """Calculate total execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == ExecutionStatus.COMPLETED and self.failure_reason is None


@dataclass
class CategoryExecution:
    """
    Execution results for all tasks in a category.
    """
    category: str
    submission_id: str

    # Task executions
    task_executions: List[TaskExecution] = field(default_factory=list)

    # Aggregate metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    average_score: float = 0.0

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def success_rate(self) -> float:
        """Calculate percentage of successfully completed tasks."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    def total_duration_seconds(self) -> float:
        """Total execution time for category."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


@dataclass
class BenchmarkExecution:
    """
    Complete execution record for a full benchmark run.
    """
    execution_id: UUID = field(default_factory=uuid4)
    submission_id: str = ""

    # Agent details
    agent_name: str = ""
    agent_version: str = ""
    organization: Optional[str] = None

    # Execution scope
    categories_executed: List[str] = field(default_factory=list)
    category_executions: Dict[str, CategoryExecution] = field(default_factory=dict)

    # Overall status
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Aggregated results
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    overall_score: Optional[float] = None

    # Resource totals
    total_tokens: int = 0
    total_time_seconds: float = 0.0
    total_api_calls: int = 0

    # Reproducibility
    benchmark_version: str = ""
    execution_environment: Dict[str, Any] = field(default_factory=dict)

    def add_category_execution(self, category_exec: CategoryExecution) -> None:
        """Add category execution results."""
        self.category_executions[category_exec.category] = category_exec
        self.total_tasks += category_exec.total_tasks
        self.completed_tasks += category_exec.completed_tasks
        self.failed_tasks += category_exec.failed_tasks

    def overall_success_rate(self) -> float:
        """Calculate overall success rate across all categories."""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100

    def total_duration_seconds(self) -> float:
        """Total benchmark execution time."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


@dataclass
class ExecutionProgress:
    """
    Real-time progress information for ongoing executions.
    """
    execution_id: UUID
    submission_id: str

    # Progress metrics
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    current_task: Optional[str] = None

    # Timing estimates
    started_at: datetime = field(default_factory=datetime.utcnow)
    estimated_completion: Optional[datetime] = None

    # Current status
    status: ExecutionStatus = ExecutionStatus.RUNNING
    status_message: str = ""

    def progress_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_tasks == 0:
            return 0.0
        return ((self.completed_tasks + self.failed_tasks) / self.total_tasks) * 100

    def tasks_remaining(self) -> int:
        """Number of tasks still to execute."""
        return self.total_tasks - self.completed_tasks - self.failed_tasks


__all__ = [
    "ExecutionStatus",
    "FailureReason",
    "ToolCall",
    "ResourceUsage",
    "TaskExecution",
    "CategoryExecution",
    "BenchmarkExecution",
    "ExecutionProgress",
]
