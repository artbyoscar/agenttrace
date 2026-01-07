"""
Orchestration layer for benchmark execution.

Manages the complete lifecycle of benchmark submissions:
- Queue management with priority ordering
- Worker pool coordination
- Retry logic and circuit breakers
- Real-time progress updates
- Error recovery
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable
from uuid import UUID

from .submission import SubmissionHandler
from .executor import TaskExecutor
from .agent_interface import create_agent_interface
from .models.submission import BenchmarkSubmission
from .models.execution import BenchmarkExecution, ExecutionStatus, ExecutionProgress

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker for protecting against repeatedly failing agents.

    Prevents wasting resources on agents that are consistently failing.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 300,  # 5 minutes
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes needed to close circuit
            timeout_seconds: Time before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None

    def record_success(self) -> None:
        """Record a successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker closing after recovery")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset on success

    def record_failure(self) -> None:
        """Record a failed execution."""
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker opening after {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN

        elif self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker reopening after failed recovery attempt")
            self.state = CircuitState.OPEN
            self.success_count = 0

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    logger.info("Circuit breaker entering half-open state")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True

            return False

        # HALF_OPEN: allow execution to test recovery
        return True


class BenchmarkOrchestrator:
    """
    Orchestrates benchmark execution across multiple workers.

    Responsibilities:
    - Manage execution queue with priority
    - Coordinate worker pool
    - Handle retries and circuit breaking
    - Provide progress updates
    - Store results
    """

    def __init__(
        self,
        submission_handler: SubmissionHandler,
        executor: TaskExecutor,
        num_workers: int = 3,
        enable_circuit_breaker: bool = True,
    ):
        """
        Initialize orchestrator.

        Args:
            submission_handler: Handler for submissions
            executor: Task executor
            num_workers: Number of concurrent workers
            enable_circuit_breaker: Whether to use circuit breaker
        """
        self.submission_handler = submission_handler
        self.executor = executor
        self.num_workers = num_workers
        self.enable_circuit_breaker = enable_circuit_breaker

        # State tracking
        self.running = False
        self.workers: List[asyncio.Task] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.active_executions: Dict[str, BenchmarkExecution] = {}
        self.completed_executions: Dict[str, BenchmarkExecution] = {}

        # Progress callbacks
        self.progress_callbacks: List[Callable] = []

    async def start(self) -> None:
        """Start the orchestrator and worker pool."""
        if self.running:
            logger.warning("Orchestrator already running")
            return

        logger.info(f"Starting orchestrator with {self.num_workers} workers")
        self.running = True

        # Start worker tasks
        for i in range(self.num_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        logger.info("Orchestrator started successfully")

    async def stop(self, graceful: bool = True) -> None:
        """
        Stop the orchestrator.

        Args:
            graceful: If True, wait for current executions to complete
        """
        logger.info("Stopping orchestrator")
        self.running = False

        if graceful:
            # Wait for active executions to complete
            if self.active_executions:
                logger.info(f"Waiting for {len(self.active_executions)} executions to complete")
                await asyncio.sleep(1)  # Give them time

        # Cancel workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        logger.info("Orchestrator stopped")

    async def _worker(self, worker_id: int) -> None:
        """
        Worker task that processes submissions from queue.

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")

        while self.running:
            try:
                # Get next submission from queue
                submission = await self.submission_handler.get_next_submission()

                if submission is None:
                    # No submissions available, sleep briefly
                    await asyncio.sleep(1)
                    continue

                logger.info(f"Worker {worker_id} processing submission {submission.submission_id}")

                # Check circuit breaker
                if self.enable_circuit_breaker:
                    breaker = self._get_circuit_breaker(submission.agent_name)
                    if not breaker.can_execute():
                        logger.warning(
                            f"Circuit breaker open for {submission.agent_name}, skipping"
                        )
                        submission.status = "failed"
                        submission.validation_errors.append("Circuit breaker open")
                        continue

                # Execute benchmark
                try:
                    execution = await self._execute_submission(submission)

                    # Update circuit breaker
                    if self.enable_circuit_breaker:
                        breaker = self._get_circuit_breaker(submission.agent_name)
                        if execution.status == ExecutionStatus.COMPLETED:
                            breaker.record_success()
                        else:
                            breaker.record_failure()

                except Exception as e:
                    logger.error(
                        f"Execution failed for submission {submission.submission_id}: {str(e)}",
                        exc_info=True
                    )
                    if self.enable_circuit_breaker:
                        breaker = self._get_circuit_breaker(submission.agent_name)
                        breaker.record_failure()

            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}", exc_info=True)
                await asyncio.sleep(5)  # Back off on error

        logger.info(f"Worker {worker_id} stopped")

    async def _execute_submission(
        self,
        submission: BenchmarkSubmission
    ) -> BenchmarkExecution:
        """
        Execute a benchmark submission.

        Args:
            submission: Submission to execute

        Returns:
            BenchmarkExecution with results
        """
        logger.info(f"Executing submission {submission.submission_id}")

        # Create agent interface
        agent = create_agent_interface(submission.agent_endpoint)

        # Track active execution
        execution_id = submission.submission_id
        self.active_executions[execution_id] = None  # Placeholder

        try:
            # Execute with progress callback
            execution = await self.executor.execute_full_benchmark(
                agent=agent,
                submission=submission,
                progress_callback=self._create_progress_callback(submission),
            )

            # Store results
            self.active_executions.pop(execution_id, None)
            self.completed_executions[execution_id] = execution

            logger.info(
                f"Submission {submission.submission_id} completed: "
                f"{execution.completed_tasks}/{execution.total_tasks} tasks, "
                f"score {execution.overall_score:.1f}"
            )

            return execution

        except Exception as e:
            logger.error(f"Execution error: {str(e)}", exc_info=True)
            self.active_executions.pop(execution_id, None)
            raise

    def _create_progress_callback(
        self,
        submission: BenchmarkSubmission
    ) -> Callable:
        """Create progress callback for a submission."""

        async def callback(progress: ExecutionProgress) -> None:
            """Update progress and notify callbacks."""
            logger.debug(
                f"Progress update for {submission.submission_id}: "
                f"{progress.progress_percentage():.1f}% complete"
            )

            # Notify registered callbacks
            for cb in self.progress_callbacks:
                try:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(progress)
                    else:
                        cb(progress)
                except Exception as e:
                    logger.error(f"Progress callback failed: {str(e)}")

        return callback

    def _get_circuit_breaker(self, agent_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for an agent."""
        if agent_name not in self.circuit_breakers:
            self.circuit_breakers[agent_name] = CircuitBreaker()
        return self.circuit_breakers[agent_name]

    def register_progress_callback(self, callback: Callable) -> None:
        """
        Register callback for progress updates.

        Args:
            callback: Function to call with ExecutionProgress updates
        """
        self.progress_callbacks.append(callback)

    def get_execution(self, execution_id: str) -> Optional[BenchmarkExecution]:
        """
        Get execution by ID.

        Args:
            execution_id: Execution ID to look up

        Returns:
            BenchmarkExecution if found, None otherwise
        """
        # Check active first
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]

        # Then completed
        return self.completed_executions.get(execution_id)

    def get_queue_status(self) -> Dict[str, any]:
        """
        Get current orchestrator status.

        Returns:
            Dictionary with status information
        """
        return {
            "running": self.running,
            "num_workers": self.num_workers,
            "active_workers": sum(1 for w in self.workers if not w.done()),
            "queue_size": self.submission_handler.get_queue_size(),
            "active_executions": len(self.active_executions),
            "completed_executions": len(self.completed_executions),
            "circuit_breakers": {
                name: breaker.state.value
                for name, breaker in self.circuit_breakers.items()
            },
        }


__all__ = ["BenchmarkOrchestrator", "CircuitBreaker", "CircuitState"]
