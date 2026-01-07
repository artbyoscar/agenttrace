"""
Task executor for running benchmark tasks against agents.

Handles execution of individual tasks, categories, and complete benchmarks
with proper resource tracking, error handling, and scoring.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from ..schema import BenchmarkTask
from ..categories import BenchmarkCategory
from ..scoring import ScoringEngine, TaskScore
from ..tasks import get_tasks_by_category, get_all_tasks

from .agent_interface import AgentInterface, AgentResponse
from .models.execution import (
    TaskExecution,
    CategoryExecution,
    BenchmarkExecution,
    ExecutionStatus,
    FailureReason,
    ResourceUsage,
    ExecutionProgress,
)
from .models.submission import BenchmarkSubmission

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    Executes benchmark tasks against submitted agents.

    Handles:
    - Single task execution with timeout and resource tracking
    - Category execution with controlled parallelism
    - Full benchmark execution
    - Scoring and evaluation
    - Error handling and retry logic
    """

    def __init__(
        self,
        scoring_engine: Optional[ScoringEngine] = None,
        default_parallelism: int = 3,
        enable_retries: bool = True,
        max_retries: int = 2,
    ):
        """
        Initialize task executor.

        Args:
            scoring_engine: Engine for scoring task outputs
            default_parallelism: Default number of concurrent tasks
            enable_retries: Whether to retry failed tasks
            max_retries: Maximum retry attempts per task
        """
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.default_parallelism = default_parallelism
        self.enable_retries = enable_retries
        self.max_retries = max_retries

    async def execute_task(
        self,
        agent: AgentInterface,
        task: BenchmarkTask,
        submission_id: str,
        timeout: Optional[float] = None,
        retry_count: int = 0,
    ) -> TaskExecution:
        """
        Execute a single benchmark task against an agent.

        Args:
            agent: Agent interface to invoke
            task: Task to execute
            submission_id: ID of the submission
            timeout: Override task time limit
            retry_count: Current retry attempt

        Returns:
            TaskExecution with complete execution trace
        """
        execution = TaskExecution(
            execution_id=uuid4(),
            task_id=task.task_id,
            submission_id=submission_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow(),
            agent_input=task.prompt,
        )

        logger.info(
            f"Executing task {task.name} (attempt {retry_count + 1}) "
            f"for submission {submission_id}"
        )

        try:
            # Use task's time limit or override
            time_limit = timeout or task.time_limit_seconds

            # Invoke agent
            response = await agent.invoke(
                prompt=task.prompt,
                config={},  # Could pass task-specific config
                timeout=time_limit,
            )

            # Update execution with response
            execution.agent_output = response.output
            execution.tool_calls = response.tool_calls

            # Track resource usage
            execution.resource_usage = ResourceUsage(
                tokens_input=agent._count_tokens(task.prompt),
                tokens_output=agent._count_tokens(response.output),
                tokens_total=response.tokens_used,
                execution_time_seconds=response.execution_time,
                tool_calls_count=len(response.tool_calls),
                api_calls_count=len([tc for tc in response.tool_calls if tc.tool_name in ["api_call", "web_search"]]),
                memory_peak_mb=0.0,  # Would need memory profiling
            )

            # Check if execution was successful
            if not response.success:
                execution.status = ExecutionStatus.FAILED
                execution.failure_reason = FailureReason.AGENT_ERROR
                execution.error_message = response.error
                execution.completed_at = datetime.utcnow()

                # Retry if enabled and attempts remaining
                if self.enable_retries and retry_count < self.max_retries:
                    logger.warning(f"Task failed, retrying ({retry_count + 1}/{self.max_retries})")
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                    return await self.execute_task(
                        agent, task, submission_id, timeout, retry_count + 1
                    )

                return execution

            # Check resource budget violations
            if task.token_budget and response.tokens_used > task.token_budget:
                execution.failure_reason = FailureReason.RESOURCE_EXCEEDED
                execution.error_message = (
                    f"Token budget exceeded: {response.tokens_used} > {task.token_budget}"
                )
                logger.warning(f"Token budget exceeded for task {task.name}")

            if response.execution_time > time_limit:
                execution.status = ExecutionStatus.TIMEOUT
                execution.failure_reason = FailureReason.AGENT_TIMEOUT
                execution.error_message = (
                    f"Time limit exceeded: {response.execution_time:.1f}s > {time_limit}s"
                )
                logger.warning(f"Time limit exceeded for task {task.name}")

            # Score the output
            try:
                task_score = self.scoring_engine.score_task(
                    task=task,
                    agent_output=response.output,
                    execution_time=response.execution_time,
                    tokens_used=response.tokens_used,
                    tool_calls=len(response.tool_calls),
                )

                execution.raw_score = task_score.raw_score
                execution.normalized_score = task_score.normalized_score
                execution.criterion_scores = task_score.criterion_scores

                # Mark as completed if no failures
                if not execution.failure_reason:
                    execution.status = ExecutionStatus.COMPLETED

                logger.info(
                    f"Task {task.name} completed with score {task_score.normalized_score:.1f}/100"
                )

            except Exception as e:
                logger.error(f"Scoring failed for task {task.name}: {str(e)}")
                execution.failure_reason = FailureReason.INTERNAL_ERROR
                execution.error_message = f"Scoring error: {str(e)}"
                execution.status = ExecutionStatus.FAILED

        except asyncio.TimeoutError:
            logger.error(f"Task {task.name} timed out")
            execution.status = ExecutionStatus.TIMEOUT
            execution.failure_reason = FailureReason.AGENT_TIMEOUT
            execution.error_message = "Agent did not respond within timeout"

        except Exception as e:
            logger.error(f"Task execution failed with exception: {str(e)}", exc_info=True)
            execution.status = ExecutionStatus.FAILED
            execution.failure_reason = FailureReason.INTERNAL_ERROR
            execution.error_message = str(e)

        finally:
            execution.completed_at = datetime.utcnow()

        return execution

    async def execute_category(
        self,
        agent: AgentInterface,
        category: BenchmarkCategory,
        submission_id: str,
        parallelism: Optional[int] = None,
        max_tasks: Optional[int] = None,
    ) -> CategoryExecution:
        """
        Execute all tasks in a category with controlled parallelism.

        Args:
            agent: Agent interface
            category: Category to execute
            submission_id: Submission ID
            parallelism: Number of concurrent tasks (default: self.default_parallelism)
            max_tasks: Maximum tasks to run (for testing)

        Returns:
            CategoryExecution with all task results
        """
        category_exec = CategoryExecution(
            category=category.value,
            submission_id=submission_id,
            started_at=datetime.utcnow(),
        )

        logger.info(f"Starting category execution: {category.value}")

        # Get tasks for this category
        tasks = get_tasks_by_category(category)

        if max_tasks:
            tasks = tasks[:max_tasks]

        category_exec.total_tasks = len(tasks)

        # Execute tasks with semaphore for concurrency control
        parallelism = parallelism or self.default_parallelism
        semaphore = asyncio.Semaphore(parallelism)

        async def execute_with_semaphore(task: BenchmarkTask) -> TaskExecution:
            async with semaphore:
                return await self.execute_task(agent, task, submission_id)

        # Run tasks concurrently
        task_executions = await asyncio.gather(*[
            execute_with_semaphore(task) for task in tasks
        ])

        category_exec.task_executions = task_executions

        # Calculate aggregate metrics
        category_exec.completed_tasks = sum(
            1 for te in task_executions if te.is_successful()
        )
        category_exec.failed_tasks = sum(
            1 for te in task_executions if not te.is_successful()
        )

        # Calculate average score
        successful_scores = [
            te.normalized_score for te in task_executions
            if te.is_successful() and te.normalized_score is not None
        ]
        if successful_scores:
            category_exec.average_score = sum(successful_scores) / len(successful_scores)

        category_exec.completed_at = datetime.utcnow()

        logger.info(
            f"Category {category.value} completed: "
            f"{category_exec.completed_tasks}/{category_exec.total_tasks} successful, "
            f"avg score {category_exec.average_score:.1f}"
        )

        return category_exec

    async def execute_full_benchmark(
        self,
        agent: AgentInterface,
        submission: BenchmarkSubmission,
        progress_callback: Optional[callable] = None,
    ) -> BenchmarkExecution:
        """
        Execute complete benchmark suite.

        Args:
            agent: Agent interface
            submission: Benchmark submission
            progress_callback: Optional callback for progress updates

        Returns:
            BenchmarkExecution with complete results
        """
        benchmark_exec = BenchmarkExecution(
            execution_id=uuid4(),
            submission_id=submission.submission_id,
            agent_name=submission.agent_name,
            agent_version=submission.agent_version,
            organization=submission.organization,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow(),
            benchmark_version="0.1.0",  # Would come from package version
        )

        logger.info(
            f"Starting full benchmark execution for {submission.agent_name} "
            f"v{submission.agent_version}"
        )

        # Determine categories to execute
        categories = submission.categories_to_evaluate()
        benchmark_exec.categories_executed = [c.value for c in categories]

        # Execute each category
        for i, category in enumerate(categories):
            try:
                category_exec = await self.execute_category(
                    agent=agent,
                    category=category,
                    submission_id=submission.submission_id,
                    max_tasks=submission.max_tasks_per_category,
                )

                benchmark_exec.add_category_execution(category_exec)

                # Update progress
                if progress_callback:
                    progress = ExecutionProgress(
                        execution_id=benchmark_exec.execution_id,
                        submission_id=submission.submission_id,
                        total_tasks=benchmark_exec.total_tasks,
                        completed_tasks=benchmark_exec.completed_tasks,
                        failed_tasks=benchmark_exec.failed_tasks,
                        current_task=f"Category {category.value}",
                        status=ExecutionStatus.RUNNING,
                        status_message=f"Completed {i + 1}/{len(categories)} categories",
                    )
                    await progress_callback(progress)

            except Exception as e:
                logger.error(f"Category {category.value} failed: {str(e)}", exc_info=True)
                benchmark_exec.status = ExecutionStatus.FAILED

        # Calculate overall metrics
        if benchmark_exec.completed_tasks > 0:
            all_scores = []
            for cat_exec in benchmark_exec.category_executions.values():
                for task_exec in cat_exec.task_executions:
                    if task_exec.is_successful() and task_exec.normalized_score:
                        all_scores.append(task_exec.normalized_score)

            if all_scores:
                benchmark_exec.overall_score = sum(all_scores) / len(all_scores)

        # Aggregate resource usage
        for cat_exec in benchmark_exec.category_executions.values():
            for task_exec in cat_exec.task_executions:
                if task_exec.resource_usage:
                    benchmark_exec.total_tokens += task_exec.resource_usage.tokens_total
                    benchmark_exec.total_time_seconds += task_exec.resource_usage.execution_time_seconds
                    benchmark_exec.total_api_calls += task_exec.resource_usage.api_calls_count

        benchmark_exec.completed_at = datetime.utcnow()

        if benchmark_exec.status == ExecutionStatus.RUNNING:
            benchmark_exec.status = ExecutionStatus.COMPLETED

        logger.info(
            f"Benchmark execution completed: "
            f"{benchmark_exec.completed_tasks}/{benchmark_exec.total_tasks} successful, "
            f"overall score {benchmark_exec.overall_score:.1f}"
        )

        return benchmark_exec


__all__ = ["TaskExecutor"]
