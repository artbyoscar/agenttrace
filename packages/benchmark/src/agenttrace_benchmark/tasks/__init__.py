"""
AgentTrace Benchmark Task Library

This module provides access to all benchmark tasks across all categories.

Usage:
    from agenttrace_benchmark.tasks import get_all_tasks, get_tasks_by_category

    # Get all tasks
    all_tasks = get_all_tasks()

    # Get tasks for specific category
    reasoning_tasks = get_tasks_by_category(BenchmarkCategory.REASONING)
"""

from typing import List, Dict
from ..schema import BenchmarkTask
from ..categories import BenchmarkCategory

# Import reasoning tasks
from .reasoning.reasoning_tasks import get_all_reasoning_tasks
from .reasoning.reasoning_tasks_continued import get_reasoning_tasks_continued

# Import tool use tasks
from .tool_use.tool_use_tasks import get_tool_use_tasks_part1


def get_all_reasoning_tasks_combined() -> List[BenchmarkTask]:
    """Get all 20 reasoning tasks."""
    return get_all_reasoning_tasks() + get_reasoning_tasks_continued()


def get_all_tool_use_tasks_combined() -> List[BenchmarkTask]:
    """Get all tool use tasks (currently 13, with 12 more to be added)."""
    return get_tool_use_tasks_part1()


def get_all_tasks() -> List[BenchmarkTask]:
    """
    Get all benchmark tasks across all categories.

    Returns:
        List of all BenchmarkTask objects
    """
    all_tasks = []

    # Add reasoning tasks (20 tasks)
    all_tasks.extend(get_all_reasoning_tasks_combined())

    # Add tool use tasks (13 currently implemented, 12 more in progress)
    all_tasks.extend(get_all_tool_use_tasks_combined())

    # TODO: Add planning tasks (20 tasks)
    # TODO: Add grounding tasks (20 tasks)
    # TODO: Add robustness tasks (15 tasks)
    # TODO: Add efficiency tasks (10 tasks)

    return all_tasks


def get_tasks_by_category(category: BenchmarkCategory) -> List[BenchmarkTask]:
    """
    Get all tasks for a specific category.

    Args:
        category: The benchmark category

    Returns:
        List of tasks in that category
    """
    all_tasks = get_all_tasks()
    return [task for task in all_tasks if task.category == category]


def get_tasks_by_difficulty(difficulty) -> List[BenchmarkTask]:
    """
    Get all tasks at a specific difficulty level.

    Args:
        difficulty: The difficulty level

    Returns:
        List of tasks at that difficulty
    """
    all_tasks = get_all_tasks()
    return [task for task in all_tasks if task.difficulty == difficulty]


def get_task_count_by_category() -> Dict[BenchmarkCategory, int]:
    """
    Get count of tasks in each category.

    Returns:
        Dictionary mapping category to task count
    """
    counts = {}
    for category in BenchmarkCategory:
        counts[category] = len(get_tasks_by_category(category))
    return counts


def get_task_statistics() -> Dict[str, any]:
    """
    Get comprehensive statistics about the task library.

    Returns:
        Dictionary with various statistics
    """
    all_tasks = get_all_tasks()

    return {
        "total_tasks": len(all_tasks),
        "by_category": get_task_count_by_category(),
        "by_difficulty": {
            "BASIC": len([t for t in all_tasks if t.difficulty.value == "basic"]),
            "INTERMEDIATE": len([t for t in all_tasks if t.difficulty.value == "intermediate"]),
            "ADVANCED": len([t for t in all_tasks if t.difficulty.value == "advanced"]),
            "EXPERT": len([t for t in all_tasks if t.difficulty.value == "expert"]),
        },
        "avg_time_limit": sum(t.time_limit_seconds for t in all_tasks) / len(all_tasks) if all_tasks else 0,
        "avg_token_budget": sum(t.token_budget for t in all_tasks if t.token_budget) / len([t for t in all_tasks if t.token_budget]) if all_tasks else 0,
    }


__all__ = [
    "get_all_tasks",
    "get_tasks_by_category",
    "get_tasks_by_difficulty",
    "get_task_count_by_category",
    "get_task_statistics",
    "get_all_reasoning_tasks_combined",
    "get_all_tool_use_tasks_combined",
]
