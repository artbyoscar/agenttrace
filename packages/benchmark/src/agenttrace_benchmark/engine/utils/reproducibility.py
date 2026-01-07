"""
Reproducibility utilities for benchmark execution.

Ensures benchmark runs can be exactly reproduced by:
- Deterministic task ordering
- Environment snapshots
- Version pinning
- Execution replay
"""

import hashlib
import json
import logging
import platform
import random
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentSnapshot:
    """
    Snapshot of execution environment for reproducibility.

    Captures all relevant environment details needed to reproduce
    an execution exactly.
    """
    # Python environment
    python_version: str
    python_implementation: str
    platform_system: str
    platform_release: str
    platform_machine: str

    # Package versions
    package_versions: Dict[str, str]

    # Benchmark configuration
    benchmark_version: str
    scoring_version: str

    # Execution configuration
    random_seed: int
    timestamp: datetime

    @classmethod
    def capture(cls, random_seed: Optional[int] = None) -> "EnvironmentSnapshot":
        """
        Capture current environment snapshot.

        Args:
            random_seed: Random seed to use (generated if not provided)

        Returns:
            EnvironmentSnapshot with current environment
        """
        if random_seed is None:
            random_seed = random.randint(0, 2**32 - 1)

        # Get package versions
        package_versions = cls._get_package_versions()

        return cls(
            python_version=sys.version,
            python_implementation=platform.python_implementation(),
            platform_system=platform.system(),
            platform_release=platform.release(),
            platform_machine=platform.machine(),
            package_versions=package_versions,
            benchmark_version="0.1.0",  # Would come from package
            scoring_version="0.1.0",
            random_seed=random_seed,
            timestamp=datetime.utcnow(),
        )

    @staticmethod
    def _get_package_versions() -> Dict[str, str]:
        """Get versions of installed packages."""
        versions = {}

        try:
            import pkg_resources
            installed_packages = pkg_resources.working_set
            for package in installed_packages:
                versions[package.project_name] = package.version
        except Exception as e:
            logger.warning(f"Could not get package versions: {e}")

        return versions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "python_version": self.python_version,
            "python_implementation": self.python_implementation,
            "platform_system": self.platform_system,
            "platform_release": self.platform_release,
            "platform_machine": self.platform_machine,
            "package_versions": self.package_versions,
            "benchmark_version": self.benchmark_version,
            "scoring_version": self.scoring_version,
            "random_seed": self.random_seed,
            "timestamp": self.timestamp.isoformat(),
        }

    def compute_hash(self) -> str:
        """Compute hash of environment for change detection."""
        # Create deterministic string representation
        env_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(env_str.encode()).hexdigest()


class DeterministicTaskOrdering:
    """
    Ensures deterministic ordering of tasks for reproducibility.

    Uses submission ID as seed to generate consistent ordering
    across runs.
    """

    @staticmethod
    def order_tasks(tasks: List[Any], seed: int) -> List[Any]:
        """
        Order tasks deterministically based on seed.

        Args:
            tasks: List of tasks to order
            seed: Seed for random ordering

        Returns:
            Ordered list of tasks
        """
        # Create random number generator with seed
        rng = random.Random(seed)

        # Create list of (task, random_value) pairs
        tasks_with_random = [(task, rng.random()) for task in tasks]

        # Sort by random value
        tasks_with_random.sort(key=lambda x: x[1])

        # Extract tasks
        return [task for task, _ in tasks_with_random]

    @staticmethod
    def seed_from_submission_id(submission_id: str) -> int:
        """
        Generate deterministic seed from submission ID.

        Args:
            submission_id: Submission UUID

        Returns:
            Integer seed
        """
        # Hash submission ID
        hash_digest = hashlib.sha256(submission_id.encode()).digest()

        # Convert first 4 bytes to int
        seed = int.from_bytes(hash_digest[:4], byteorder='big')

        return seed


class ExecutionRecorder:
    """
    Records execution traces for replay.

    Captures all inputs and outputs to enable exact replay
    of executions.
    """

    def __init__(self):
        """Initialize execution recorder."""
        self.recordings: List[Dict[str, Any]] = []

    def record_agent_invocation(
        self,
        task_id: str,
        prompt: str,
        config: Dict[str, Any],
        response: str,
        duration: float,
        timestamp: datetime,
    ) -> None:
        """
        Record an agent invocation.

        Args:
            task_id: Task being executed
            prompt: Input prompt
            config: Agent configuration
            response: Agent response
            duration: Execution duration
            timestamp: When invocation occurred
        """
        self.recordings.append({
            "type": "agent_invocation",
            "task_id": task_id,
            "prompt": prompt,
            "config": config,
            "response": response,
            "duration": duration,
            "timestamp": timestamp.isoformat(),
        })

    def record_tool_call(
        self,
        task_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Any,
        duration: float,
        timestamp: datetime,
    ) -> None:
        """
        Record a tool call.

        Args:
            task_id: Task being executed
            tool_name: Tool that was called
            parameters: Tool parameters
            result: Tool result
            duration: Execution duration
            timestamp: When call occurred
        """
        self.recordings.append({
            "type": "tool_call",
            "task_id": task_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "duration": duration,
            "timestamp": timestamp.isoformat(),
        })

    def save_to_file(self, filepath: str) -> None:
        """
        Save recordings to file.

        Args:
            filepath: Path to save recordings
        """
        with open(filepath, 'w') as f:
            json.dump(self.recordings, f, indent=2, default=str)

        logger.info(f"Saved {len(self.recordings)} recordings to {filepath}")

    def load_from_file(self, filepath: str) -> None:
        """
        Load recordings from file.

        Args:
            filepath: Path to load from
        """
        with open(filepath, 'r') as f:
            self.recordings = json.load(f)

        logger.info(f"Loaded {len(self.recordings)} recordings from {filepath}")


class ReproducibilityVerifier:
    """
    Verifies that executions are reproducible.

    Compares two execution runs to ensure they produce identical results.
    """

    @staticmethod
    def verify_executions_match(
        exec1: Dict[str, Any],
        exec2: Dict[str, Any],
        tolerance: float = 0.01,
    ) -> tuple[bool, List[str]]:
        """
        Verify two executions match.

        Args:
            exec1: First execution result
            exec2: Second execution result
            tolerance: Floating point comparison tolerance

        Returns:
            (matches: bool, differences: List[str])
        """
        differences = []

        # Check environment matches
        if exec1.get("environment") != exec2.get("environment"):
            differences.append("Environment snapshots differ")

        # Check same number of tasks
        tasks1 = exec1.get("task_executions", [])
        tasks2 = exec2.get("task_executions", [])

        if len(tasks1) != len(tasks2):
            differences.append(
                f"Different number of tasks: {len(tasks1)} vs {len(tasks2)}"
            )
            return False, differences

        # Check each task matches
        for i, (t1, t2) in enumerate(zip(tasks1, tasks2)):
            task_diff = ReproducibilityVerifier._compare_task_executions(
                t1, t2, tolerance
            )
            if task_diff:
                differences.append(f"Task {i}: {task_diff}")

        matches = len(differences) == 0
        return matches, differences

    @staticmethod
    def _compare_task_executions(
        task1: Dict[str, Any],
        task2: Dict[str, Any],
        tolerance: float,
    ) -> Optional[str]:
        """
        Compare two task executions.

        Returns:
            Difference description if different, None if same
        """
        # Check task IDs match
        if task1.get("task_id") != task2.get("task_id"):
            return "Different task IDs"

        # Check outputs match
        if task1.get("agent_output") != task2.get("agent_output"):
            return "Different agent outputs"

        # Check scores match (within tolerance)
        score1 = task1.get("normalized_score", 0)
        score2 = task2.get("normalized_score", 0)

        if abs(score1 - score2) > tolerance:
            return f"Different scores: {score1} vs {score2}"

        return None


__all__ = [
    "EnvironmentSnapshot",
    "DeterministicTaskOrdering",
    "ExecutionRecorder",
    "ReproducibilityVerifier",
]
