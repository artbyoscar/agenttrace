"""
Submission handler for benchmark evaluation requests.

Handles validation, quota enforcement, and queueing of benchmark submissions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

import httpx

from .models.submission import (
    BenchmarkSubmission,
    ValidationResult,
    SubmissionQuota,
    SubmissionConstraints,
)
from ..categories import BenchmarkCategory

logger = logging.getLogger(__name__)


class SubmissionHandler:
    """
    Handles validation and queueing of benchmark submissions.

    Responsibilities:
    - Validate submissions before execution
    - Enforce rate limits and quotas
    - Queue validated submissions for execution
    - Track submission history
    """

    def __init__(
        self,
        default_constraints: Optional[SubmissionConstraints] = None,
        enable_quota_enforcement: bool = True,
    ):
        """
        Initialize submission handler.

        Args:
            default_constraints: Default rate limit constraints
            enable_quota_enforcement: Whether to enforce rate limits
        """
        self.default_constraints = default_constraints or SubmissionConstraints()
        self.enable_quota_enforcement = enable_quota_enforcement

        # In-memory storage (would be database in production)
        self.quotas: Dict[str, SubmissionQuota] = {}
        self.submissions: Dict[str, BenchmarkSubmission] = {}
        self.queue: asyncio.Queue = asyncio.Queue()

    async def validate_submission(
        self,
        submission: BenchmarkSubmission
    ) -> ValidationResult:
        """
        Comprehensive validation of benchmark submission.

        Checks:
        1. Required fields present
        2. Agent endpoint reachable
        3. Rate limits not exceeded
        4. Terms of service accepted
        5. Valid categories specified

        Args:
            submission: The submission to validate

        Returns:
            ValidationResult with detailed findings
        """
        logger.info(f"Validating submission {submission.submission_id} for {submission.agent_name}")
        result = ValidationResult(is_valid=True)

        # Check required fields
        self._validate_required_fields(submission, result)

        # Check terms acceptance
        self._validate_terms(submission, result)

        # Check rate limits
        if self.enable_quota_enforcement:
            await self._validate_quota(submission, result)

        # Validate agent endpoint
        await self._validate_endpoint(submission, result)

        # Validate categories
        self._validate_categories(submission, result)

        # Validate configuration
        self._validate_config(submission, result)

        logger.info(
            f"Validation complete for {submission.submission_id}: "
            f"valid={result.is_valid}, errors={len(result.errors)}, warnings={len(result.warnings)}"
        )

        return result

    def _validate_required_fields(
        self,
        submission: BenchmarkSubmission,
        result: ValidationResult
    ) -> None:
        """Check all required fields are present and valid."""
        result.add_check("required_fields", True)

        if not submission.agent_name:
            result.add_error("agent_name is required")

        if not submission.agent_version:
            result.add_error("agent_version is required")

        if not submission.contact_email:
            result.add_error("contact_email is required")
        elif "@" not in submission.contact_email:
            result.add_error("contact_email must be valid email address")

        if not submission.submitted_by:
            result.add_error("submitted_by (user ID) is required")

    def _validate_terms(
        self,
        submission: BenchmarkSubmission,
        result: ValidationResult
    ) -> None:
        """Verify terms of service acceptance."""
        if not submission.terms_accepted:
            result.add_error("Terms of service must be accepted")
            result.add_check("terms_accepted", False)
        else:
            result.add_check("terms_accepted", True)

        # Check terms version is current
        current_version = "1.0.0"  # Would come from config
        if submission.terms_version != current_version:
            result.add_warning(
                f"Terms version {submission.terms_version} != current {current_version}"
            )

    async def _validate_quota(
        self,
        submission: BenchmarkSubmission,
        result: ValidationResult
    ) -> None:
        """Check rate limits and quotas."""
        user_id = submission.submitted_by
        quota = self.quotas.get(user_id)

        if not quota:
            # First submission from this user
            quota = SubmissionQuota(
                user_id=user_id,
                organization=submission.organization,
                constraints=self.default_constraints,
            )
            self.quotas[user_id] = quota

        can_submit, reason = quota.can_submit()
        result.add_check("quota_available", can_submit)

        if not can_submit:
            result.add_error(f"Rate limit exceeded: {reason}")

    async def _validate_endpoint(
        self,
        submission: BenchmarkSubmission,
        result: ValidationResult
    ) -> None:
        """
        Verify agent endpoint is reachable.

        Performs a lightweight health check to ensure the agent can be invoked.
        """
        endpoint = submission.agent_endpoint

        if endpoint.endpoint_type == "http":
            await self._validate_http_endpoint(endpoint, result)
        elif endpoint.endpoint_type == "grpc":
            result.add_warning("gRPC endpoint validation not yet implemented")
            result.add_check("endpoint_reachable", True)
        elif endpoint.endpoint_type == "local":
            await self._validate_local_endpoint(endpoint, result)
        else:
            result.add_error(f"Unknown endpoint type: {endpoint.endpoint_type}")
            result.add_check("endpoint_reachable", False)

    async def _validate_http_endpoint(
        self,
        endpoint,
        result: ValidationResult
    ) -> None:
        """Validate HTTP endpoint is reachable."""
        if not endpoint.url:
            result.add_error("HTTP endpoint requires url")
            result.add_check("endpoint_reachable", False)
            return

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try a HEAD request first (lightweight)
                response = await client.head(endpoint.url)

                if response.status_code >= 500:
                    result.add_error(
                        f"Endpoint returned server error: {response.status_code}"
                    )
                    result.add_check("endpoint_reachable", False)
                elif response.status_code == 404:
                    result.add_warning("Endpoint returned 404, may not have health check")
                    result.add_check("endpoint_reachable", True)
                else:
                    result.add_check("endpoint_reachable", True)

        except httpx.ConnectError:
            result.add_error(f"Cannot connect to endpoint: {endpoint.url}")
            result.add_check("endpoint_reachable", False)
        except httpx.TimeoutException:
            result.add_error(f"Endpoint timeout: {endpoint.url}")
            result.add_check("endpoint_reachable", False)
        except Exception as e:
            result.add_error(f"Endpoint validation failed: {str(e)}")
            result.add_check("endpoint_reachable", False)

    async def _validate_local_endpoint(
        self,
        endpoint,
        result: ValidationResult
    ) -> None:
        """Validate local Python module endpoint."""
        if not endpoint.module_path or not endpoint.function_name:
            result.add_error("Local endpoint requires module_path and function_name")
            result.add_check("endpoint_reachable", False)
            return

        try:
            # Try to import the module
            import importlib
            module = importlib.import_module(endpoint.module_path)

            # Check if function exists
            if not hasattr(module, endpoint.function_name):
                result.add_error(
                    f"Function {endpoint.function_name} not found in {endpoint.module_path}"
                )
                result.add_check("endpoint_reachable", False)
            else:
                result.add_check("endpoint_reachable", True)

        except ImportError as e:
            result.add_error(f"Cannot import module {endpoint.module_path}: {str(e)}")
            result.add_check("endpoint_reachable", False)
        except Exception as e:
            result.add_error(f"Module validation failed: {str(e)}")
            result.add_check("endpoint_reachable", False)

    def _validate_categories(
        self,
        submission: BenchmarkSubmission,
        result: ValidationResult
    ) -> None:
        """Validate requested categories are valid."""
        if not submission.categories:
            # Empty means all categories - this is valid
            result.add_check("categories_valid", True)
            return

        invalid_categories = []
        valid_categories = set(BenchmarkCategory)

        for category in submission.categories:
            if category not in valid_categories:
                invalid_categories.append(category)

        if invalid_categories:
            result.add_error(
                f"Invalid categories: {invalid_categories}. "
                f"Valid: {[c.value for c in BenchmarkCategory]}"
            )
            result.add_check("categories_valid", False)
        else:
            result.add_check("categories_valid", True)

    def _validate_config(
        self,
        submission: BenchmarkSubmission,
        result: ValidationResult
    ) -> None:
        """Validate agent configuration."""
        config = submission.agent_config

        # Check for potentially dangerous configurations
        dangerous_keys = ["allow_code_execution", "allow_file_write", "disable_sandbox"]
        found_dangerous = [key for key in dangerous_keys if config.get(key)]

        if found_dangerous:
            result.add_warning(
                f"Configuration contains potentially dangerous settings: {found_dangerous}"
            )

        result.add_check("config_valid", True)

    async def queue_submission(
        self,
        submission: BenchmarkSubmission
    ) -> str:
        """
        Queue a validated submission for execution.

        Args:
            submission: Validated submission

        Returns:
            Submission ID

        Raises:
            ValueError: If submission is not valid
        """
        if submission.status != "pending":
            raise ValueError(f"Submission {submission.submission_id} already processed")

        # Update quota
        if self.enable_quota_enforcement:
            user_id = submission.submitted_by
            if user_id in self.quotas:
                self.quotas[user_id].record_submission()

        # Store submission
        self.submissions[submission.submission_id] = submission
        submission.status = "queued"

        # Add to queue
        await self.queue.put(submission)

        logger.info(
            f"Queued submission {submission.submission_id} for {submission.agent_name}"
        )

        return submission.submission_id

    async def get_next_submission(self) -> Optional[BenchmarkSubmission]:
        """
        Get next submission from queue.

        Returns:
            Next submission or None if queue is empty
        """
        try:
            submission = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            return submission
        except asyncio.TimeoutError:
            return None

    def get_submission(self, submission_id: str) -> Optional[BenchmarkSubmission]:
        """Retrieve submission by ID."""
        return self.submissions.get(submission_id)

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()

    def get_quota_info(self, user_id: str) -> Optional[SubmissionQuota]:
        """Get quota information for a user."""
        return self.quotas.get(user_id)

    async def reset_daily_quotas(self) -> None:
        """Reset daily submission counts (called by scheduler)."""
        for quota in self.quotas.values():
            quota.submissions_today = 0
        logger.info("Reset daily quotas")

    async def reset_weekly_quotas(self) -> None:
        """Reset weekly submission counts (called by scheduler)."""
        for quota in self.quotas.values():
            quota.submissions_this_week = 0
        logger.info("Reset weekly quotas")


__all__ = ["SubmissionHandler"]
