"""
Submission models for benchmark evaluation requests.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ...categories import BenchmarkCategory


@dataclass
class AgentEndpoint:
    """Configuration for invoking an agent."""
    endpoint_type: str  # "http", "grpc", "local"
    url: Optional[str] = None  # For HTTP/gRPC
    module_path: Optional[str] = None  # For local Python
    function_name: Optional[str] = None  # For local Python

    # Authentication
    auth_type: Optional[str] = None  # "bearer", "api_key", "none"
    auth_credentials: Optional[Dict[str, str]] = None

    # Retry configuration
    max_retries: int = 3
    timeout_seconds: float = 300.0


@dataclass
class SubmissionConstraints:
    """Rate limits and constraints for submissions."""
    max_submissions_per_day: int = 5
    max_submissions_per_week: int = 20
    min_hours_between_submissions: float = 1.0
    max_concurrent_executions: int = 1


@dataclass
class BenchmarkSubmission:
    """
    Complete specification for a benchmark evaluation submission.

    This represents an agent's request to be evaluated on the benchmark.
    """
    submission_id: str = field(default_factory=lambda: str(uuid4()))

    # Agent identification
    agent_name: str = ""
    agent_version: str = ""
    organization: Optional[str] = None
    contact_email: str = ""

    # Agent invocation
    agent_endpoint: AgentEndpoint = field(default_factory=lambda: AgentEndpoint(endpoint_type="http"))
    agent_config: Dict[str, Any] = field(default_factory=dict)

    # Evaluation scope
    categories: List[BenchmarkCategory] = field(default_factory=list)  # Empty = all
    max_tasks_per_category: Optional[int] = None  # For testing/debugging
    use_held_out_set: bool = False  # Requires admin approval

    # Submission metadata
    submitted_at: datetime = field(default_factory=datetime.utcnow)
    submitted_by: str = ""  # User ID or API key

    # Compliance
    terms_accepted: bool = False
    terms_version: str = "1.0.0"
    allow_public_listing: bool = True
    allow_research_use: bool = True

    # Priority and scheduling
    priority: int = 0  # Higher = earlier execution
    scheduled_for: Optional[datetime] = None  # For delayed execution

    # Status tracking
    status: str = "pending"  # pending, validated, queued, running, completed, failed
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate submission after initialization."""
        if not self.agent_name:
            raise ValueError("agent_name is required")
        if not self.agent_version:
            raise ValueError("agent_version is required")
        if not self.contact_email:
            raise ValueError("contact_email is required")
        if not self.terms_accepted:
            raise ValueError("terms_of_service must be accepted")

    def is_valid(self) -> bool:
        """Check if submission passed validation."""
        return len(self.validation_errors) == 0

    def categories_to_evaluate(self) -> List[BenchmarkCategory]:
        """Get list of categories to evaluate (all if empty)."""
        if not self.categories:
            return list(BenchmarkCategory)
        return self.categories


@dataclass
class ValidationResult:
    """
    Result of submission validation.
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_performed: Dict[str, bool] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add validation warning (doesn't invalidate)."""
        self.warnings.append(message)

    def add_check(self, check_name: str, passed: bool) -> None:
        """Record validation check result."""
        self.checks_performed[check_name] = passed
        if not passed:
            self.is_valid = False


@dataclass
class SubmissionQuota:
    """
    Tracks submission quota usage for rate limiting.
    """
    user_id: str
    organization: Optional[str] = None

    # Usage tracking
    submissions_today: int = 0
    submissions_this_week: int = 0
    last_submission_at: Optional[datetime] = None

    # Quota limits
    constraints: SubmissionConstraints = field(default_factory=SubmissionConstraints)

    def can_submit(self) -> tuple[bool, Optional[str]]:
        """
        Check if user can submit based on rate limits.

        Returns:
            (can_submit: bool, reason: Optional[str])
        """
        # Check daily limit
        if self.submissions_today >= self.constraints.max_submissions_per_day:
            return False, f"Daily limit exceeded ({self.constraints.max_submissions_per_day})"

        # Check weekly limit
        if self.submissions_this_week >= self.constraints.max_submissions_per_week:
            return False, f"Weekly limit exceeded ({self.constraints.max_submissions_per_week})"

        # Check minimum time between submissions
        if self.last_submission_at:
            hours_since_last = (datetime.utcnow() - self.last_submission_at).total_seconds() / 3600
            if hours_since_last < self.constraints.min_hours_between_submissions:
                return False, f"Please wait {self.constraints.min_hours_between_submissions - hours_since_last:.1f} more hours"

        return True, None

    def record_submission(self) -> None:
        """Record a new submission."""
        self.submissions_today += 1
        self.submissions_this_week += 1
        self.last_submission_at = datetime.utcnow()


__all__ = [
    "AgentEndpoint",
    "SubmissionConstraints",
    "BenchmarkSubmission",
    "ValidationResult",
    "SubmissionQuota",
]
