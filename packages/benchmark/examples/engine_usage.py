"""
Example usage of the AgentTrace Benchmark Execution Engine.

This script demonstrates how to:
1. Create and validate a benchmark submission
2. Execute tasks against an agent
3. Run complete benchmarks with orchestration
4. Monitor progress and retrieve results
"""

import asyncio
import logging
from datetime import datetime

from agenttrace_benchmark.engine import (
    BenchmarkSubmission,
    AgentEndpoint,
    SubmissionHandler,
    TaskExecutor,
    BenchmarkOrchestrator,
    ExecutionProgress,
    create_agent_interface,
)
from agenttrace_benchmark.categories import BenchmarkCategory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Example 1: Simple mock agent for testing
def mock_agent_function(prompt: str, config: dict) -> str:
    """
    Simple mock agent that returns a placeholder response.

    In production, this would be your actual agent implementation.
    """
    return f"Mock response to: {prompt[:50]}..."


# Example 2: Create and validate a submission
async def example_create_submission():
    """Example: Create and validate a benchmark submission."""
    print("\n" + "="*80)
    print("Example 1: Creating and Validating a Submission")
    print("="*80)

    # Create submission handler
    handler = SubmissionHandler()

    # Create a submission for a local Python agent
    submission = BenchmarkSubmission(
        agent_name="TestAgent",
        agent_version="1.0.0",
        organization="TestOrg",
        contact_email="test@example.com",
        agent_endpoint=AgentEndpoint(
            endpoint_type="local",
            module_path="examples.engine_usage",
            function_name="mock_agent_function",
        ),
        categories=[BenchmarkCategory.REASONING],  # Only test reasoning
        terms_accepted=True,
        allow_public_listing=True,
        submitted_by="user_123",
    )

    print(f"\nSubmission ID: {submission.submission_id}")
    print(f"Agent: {submission.agent_name} v{submission.agent_version}")

    # Validate submission
    print("\nValidating submission...")
    validation_result = await handler.validate_submission(submission)

    print(f"\nValidation Result: {'✓ VALID' if validation_result.is_valid else '✗ INVALID'}")
    print(f"Checks performed: {len(validation_result.checks_performed)}")

    for check_name, passed in validation_result.checks_performed.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")

    if validation_result.errors:
        print(f"\nErrors ({len(validation_result.errors)}):")
        for error in validation_result.errors:
            print(f"  - {error}")

    if validation_result.warnings:
        print(f"\nWarnings ({len(validation_result.warnings)}):")
        for warning in validation_result.warnings:
            print(f"  - {warning}")

    # Queue if valid
    if validation_result.is_valid:
        print("\n✓ Submission is valid and ready for queueing")
        await handler.queue_submission(submission)
        print(f"✓ Submission queued (queue size: {handler.get_queue_size()})")

    return submission


# Example 3: Execute a single task
async def example_execute_task():
    """Example: Execute a single task against an agent."""
    print("\n" + "="*80)
    print("Example 2: Executing a Single Task")
    print("="*80)

    # Import a task
    from agenttrace_benchmark.tasks.reasoning import get_all_reasoning_tasks
    tasks = get_all_reasoning_tasks()
    task = tasks[0]  # Simple syllogism task

    print(f"\nTask: {task.name}")
    print(f"Category: {task.category.value}")
    print(f"Difficulty: {task.difficulty.value}")
    print(f"Time limit: {task.time_limit_seconds}s")
    print(f"Token budget: {task.token_budget}")

    # Create agent interface
    agent = create_agent_interface(AgentEndpoint(
        endpoint_type="local",
        module_path="examples.engine_usage",
        function_name="mock_agent_function",
    ))

    # Create executor
    executor = TaskExecutor()

    # Execute task
    print("\nExecuting task...")
    task_execution = await executor.execute_task(
        agent=agent,
        task=task,
        submission_id="test-001",
    )

    # Display results
    print(f"\n{'='*80}")
    print("Execution Results")
    print("="*80)
    print(f"Status: {task_execution.status.value}")
    print(f"Success: {task_execution.is_successful()}")
    print(f"Duration: {task_execution.duration_seconds():.2f}s")

    if task_execution.resource_usage:
        print(f"\nResource Usage:")
        print(f"  Tokens: {task_execution.resource_usage.tokens_total}")
        print(f"  Time: {task_execution.resource_usage.execution_time_seconds:.2f}s")
        print(f"  Tool calls: {task_execution.resource_usage.tool_calls_count}")

    if task_execution.normalized_score is not None:
        print(f"\nScore: {task_execution.normalized_score:.1f}/100")

    if task_execution.error_message:
        print(f"\nError: {task_execution.error_message}")


# Example 4: Execute a category
async def example_execute_category():
    """Example: Execute all tasks in a category."""
    print("\n" + "="*80)
    print("Example 3: Executing a Category")
    print("="*80)

    # Create agent interface
    agent = create_agent_interface(AgentEndpoint(
        endpoint_type="local",
        module_path="examples.engine_usage",
        function_name="mock_agent_function",
    ))

    # Create executor
    executor = TaskExecutor()

    # Execute category (limit to 3 tasks for demo)
    print(f"\nExecuting REASONING category (limited to 3 tasks)...")
    category_execution = await executor.execute_category(
        agent=agent,
        category=BenchmarkCategory.REASONING,
        submission_id="test-002",
        max_tasks=3,  # Limit for demo
    )

    # Display results
    print(f"\n{'='*80}")
    print("Category Results")
    print("="*80)
    print(f"Category: {category_execution.category}")
    print(f"Total tasks: {category_execution.total_tasks}")
    print(f"Completed: {category_execution.completed_tasks}")
    print(f"Failed: {category_execution.failed_tasks}")
    print(f"Success rate: {category_execution.success_rate():.1f}%")
    print(f"Average score: {category_execution.average_score:.1f}/100")
    print(f"Duration: {category_execution.total_duration_seconds():.2f}s")

    print(f"\nPer-task breakdown:")
    for i, task_exec in enumerate(category_execution.task_executions, 1):
        status_icon = "✓" if task_exec.is_successful() else "✗"
        score_str = f"{task_exec.normalized_score:.1f}/100" if task_exec.normalized_score else "N/A"
        print(f"  {status_icon} Task {i}: {score_str} ({task_exec.duration_seconds():.2f}s)")


# Example 5: Full orchestrated execution
async def example_orchestrated_execution():
    """Example: Full benchmark execution with orchestration."""
    print("\n" + "="*80)
    print("Example 4: Orchestrated Benchmark Execution")
    print("="*80)

    # Create submission handler and executor
    handler = SubmissionHandler()
    executor = TaskExecutor()

    # Create orchestrator
    orchestrator = BenchmarkOrchestrator(
        submission_handler=handler,
        executor=executor,
        num_workers=2,
    )

    # Register progress callback
    def progress_callback(progress: ExecutionProgress):
        """Print progress updates."""
        print(
            f"Progress: {progress.progress_percentage():.1f}% "
            f"({progress.completed_tasks + progress.failed_tasks}/{progress.total_tasks}) "
            f"- {progress.current_task}"
        )

    orchestrator.register_progress_callback(progress_callback)

    # Create and submit a submission
    submission = BenchmarkSubmission(
        agent_name="TestAgent",
        agent_version="1.0.0",
        contact_email="test@example.com",
        agent_endpoint=AgentEndpoint(
            endpoint_type="local",
            module_path="examples.engine_usage",
            function_name="mock_agent_function",
        ),
        categories=[BenchmarkCategory.REASONING],
        max_tasks_per_category=3,  # Limit for demo
        terms_accepted=True,
        submitted_by="user_123",
    )

    # Validate and queue
    print("\nValidating and queueing submission...")
    validation = await handler.validate_submission(submission)

    if validation.is_valid:
        await handler.queue_submission(submission)
        print("✓ Submission queued")
    else:
        print("✗ Submission invalid:", validation.errors)
        return

    # Start orchestrator
    print("\nStarting orchestrator...")
    await orchestrator.start()

    # Wait for execution to complete
    print("\nWaiting for execution to complete...")
    await asyncio.sleep(2)  # Give it time to process

    # Check results
    execution = orchestrator.get_execution(submission.submission_id)

    if execution:
        print(f"\n{'='*80}")
        print("Final Results")
        print("="*80)
        print(f"Status: {execution.status.value}")
        print(f"Completed: {execution.completed_tasks}/{execution.total_tasks}")
        print(f"Overall score: {execution.overall_score:.1f}/100" if execution.overall_score else "Overall score: N/A")
        print(f"Total time: {execution.total_duration_seconds():.2f}s")
        print(f"Total tokens: {execution.total_tokens:,}")

    # Stop orchestrator
    print("\nStopping orchestrator...")
    await orchestrator.stop()
    print("✓ Orchestrator stopped")

    # Get final status
    status = orchestrator.get_queue_status()
    print(f"\nFinal queue status:")
    print(f"  Completed executions: {status['completed_executions']}")
    print(f"  Active executions: {status['active_executions']}")


# Example 6: HTTP agent submission
async def example_http_agent():
    """Example: Submit an HTTP-based agent."""
    print("\n" + "="*80)
    print("Example 5: HTTP Agent Submission")
    print("="*80)

    submission = BenchmarkSubmission(
        agent_name="MyHTTPAgent",
        agent_version="2.0.0",
        organization="MyCompany",
        contact_email="agent@mycompany.com",
        agent_endpoint=AgentEndpoint(
            endpoint_type="http",
            url="https://api.mycompany.com/agent/invoke",
            auth_type="bearer",
            auth_credentials={"token": "your-api-token-here"},
            timeout_seconds=300.0,
        ),
        categories=[],  # Empty = all categories
        terms_accepted=True,
        allow_public_listing=True,
        submitted_by="user_456",
    )

    print(f"\nAgent: {submission.agent_name}")
    print(f"Endpoint: {submission.agent_endpoint.url}")
    print(f"Auth: {submission.agent_endpoint.auth_type}")
    print(f"Categories: All" if not submission.categories else f"Categories: {submission.categories}")

    # Would validate and execute similarly to previous examples
    print("\n(Validation and execution would proceed similarly to other examples)")


# Main function to run all examples
async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("AgentTrace Benchmark Engine - Usage Examples")
    print("="*80)

    # Run examples
    await example_create_submission()
    await example_execute_task()
    await example_execute_category()
    # await example_orchestrated_execution()  # Commented - longer running
    await example_http_agent()

    print("\n" + "="*80)
    print("Examples completed!")
    print("="*80)

    print("\nNext steps:")
    print("  1. Implement your agent following the AgentInterface specification")
    print("  2. Create a BenchmarkSubmission with your agent endpoint")
    print("  3. Validate and submit for evaluation")
    print("  4. Monitor progress and retrieve results")
    print("\nDocumentation: https://docs.agenttrace.dev/benchmark/engine")


if __name__ == "__main__":
    asyncio.run(main())
