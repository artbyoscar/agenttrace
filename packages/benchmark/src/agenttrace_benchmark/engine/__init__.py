"""
Benchmark Execution Engine

This module provides the complete infrastructure for running benchmark
evaluations on submitted agents.

Components:
- Submission handling and validation
- Task execution with sandboxing
- Orchestration and queue management
- Reproducibility guarantees
- Progress tracking and monitoring

Usage:
    from agenttrace_benchmark.engine import (
        SubmissionHandler,
        TaskExecutor,
        BenchmarkOrchestrator,
        create_agent_interface,
    )

    # Create components
    handler = SubmissionHandler()
    executor = TaskExecutor()
    orchestrator = BenchmarkOrchestrator(handler, executor)

    # Start processing
    await orchestrator.start()
"""

# Models
from .models.submission import (
    BenchmarkSubmission,
    AgentEndpoint,
    SubmissionConstraints,
    ValidationResult,
    SubmissionQuota,
)

from .models.execution import (
    TaskExecution,
    CategoryExecution,
    BenchmarkExecution,
    ExecutionStatus,
    ExecutionProgress,
    FailureReason,
    ResourceUsage,
    ToolCall,
)

# Core components
from .submission import SubmissionHandler
from .executor import TaskExecutor
from .agent_interface import (
    AgentInterface,
    HTTPAgentInterface,
    LocalAgentInterface,
    create_agent_interface,
    AgentResponse,
)
from .orchestrator import BenchmarkOrchestrator, CircuitBreaker

# Utilities
from .utils.reproducibility import (
    EnvironmentSnapshot,
    DeterministicTaskOrdering,
    ExecutionRecorder,
    ReproducibilityVerifier,
)

__all__ = [
    # Models - Submission
    "BenchmarkSubmission",
    "AgentEndpoint",
    "SubmissionConstraints",
    "ValidationResult",
    "SubmissionQuota",
    # Models - Execution
    "TaskExecution",
    "CategoryExecution",
    "BenchmarkExecution",
    "ExecutionStatus",
    "ExecutionProgress",
    "FailureReason",
    "ResourceUsage",
    "ToolCall",
    # Core Components
    "SubmissionHandler",
    "TaskExecutor",
    "AgentInterface",
    "HTTPAgentInterface",
    "LocalAgentInterface",
    "create_agent_interface",
    "AgentResponse",
    "BenchmarkOrchestrator",
    "CircuitBreaker",
    # Utilities
    "EnvironmentSnapshot",
    "DeterministicTaskOrdering",
    "ExecutionRecorder",
    "ReproducibilityVerifier",
]
