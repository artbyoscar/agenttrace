"""
Storage abstraction layer for AgentTrace spans.

Provides pluggable storage backends (local file system, S3, etc.)
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import logging

from ..models.requests import SpanRequest

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.

    All storage backends must implement the store() method.
    """

    @abstractmethod
    async def store(
        self, spans: List[SpanRequest], project_id: str, environment: str
    ) -> None:
        """
        Store spans to the backend.

        Args:
            spans: List of spans to store
            project_id: Project identifier
            environment: Environment name

        Raises:
            StorageError: If storage operation fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if storage backend is healthy.

        Returns:
            bool: True if healthy, False otherwise
        """
        pass


class StorageError(Exception):
    """Exception raised when storage operation fails."""

    pass


class LocalFileStorage(StorageBackend):
    """
    Local file system storage backend.

    Stores spans as JSON files organized by:
    - Project ID
    - Environment
    - Date
    - Trace ID

    Directory structure:
        {base_path}/{project_id}/{environment}/{YYYY-MM-DD}/{trace_id}.json
    """

    def __init__(self, base_path: str = "./data/traces"):
        """
        Initialize local file storage.

        Args:
            base_path: Base directory for storing traces
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized LocalFileStorage at {self.base_path}")

    async def store(
        self, spans: List[SpanRequest], project_id: str, environment: str
    ) -> None:
        """
        Store spans to local file system.

        Groups spans by trace_id and stores each trace in a separate file.

        Args:
            spans: List of spans to store
            project_id: Project identifier
            environment: Environment name

        Raises:
            StorageError: If file write fails
        """
        try:
            # Group spans by trace_id
            traces = {}
            for span in spans:
                trace_id = span.trace_id
                if trace_id not in traces:
                    traces[trace_id] = []
                traces[trace_id].append(span.dict())

            # Store each trace
            today = datetime.utcnow().strftime("%Y-%m-%d")

            for trace_id, trace_spans in traces.items():
                # Create directory structure
                trace_dir = (
                    self.base_path / project_id / environment / today / trace_id
                )
                trace_dir.mkdir(parents=True, exist_ok=True)

                # Write trace file
                trace_file = trace_dir / "trace.json"
                trace_data = {
                    "trace_id": trace_id,
                    "project_id": project_id,
                    "environment": environment,
                    "stored_at": datetime.utcnow().isoformat(),
                    "span_count": len(trace_spans),
                    "spans": trace_spans,
                }

                # Append to existing file if it exists
                if trace_file.exists():
                    with open(trace_file, "r") as f:
                        existing_data = json.load(f)
                    existing_data["spans"].extend(trace_spans)
                    existing_data["span_count"] = len(existing_data["spans"])
                    existing_data["updated_at"] = datetime.utcnow().isoformat()
                    trace_data = existing_data

                with open(trace_file, "w") as f:
                    json.dump(trace_data, f, indent=2, default=str)

                logger.debug(
                    f"Stored {len(trace_spans)} spans for trace {trace_id} "
                    f"in {trace_file}"
                )

            logger.info(
                f"Stored {len(spans)} spans across {len(traces)} traces "
                f"for project {project_id}/{environment}"
            )

        except Exception as e:
            logger.error(f"Failed to store spans: {e}")
            raise StorageError(f"Failed to store spans: {e}")

    async def health_check(self) -> bool:
        """
        Check if local storage is accessible.

        Returns:
            bool: True if directory is writable
        """
        try:
            # Try to write a test file
            test_file = self.base_path / ".health_check"
            test_file.write_text("ok")
            test_file.unlink()
            return True
        except Exception as e:
            logger.error(f"Local storage health check failed: {e}")
            return False


class S3Storage(StorageBackend):
    """
    S3 storage backend.

    Stores spans as JSON files in S3 bucket organized by:
    - Project ID
    - Environment
    - Date
    - Trace ID

    S3 key structure:
        {project_id}/{environment}/{YYYY-MM-DD}/{trace_id}.json
    """

    def __init__(
        self,
        bucket: str,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        """
        Initialize S3 storage.

        Args:
            bucket: S3 bucket name
            region: AWS region
            access_key: AWS access key (optional, uses IAM role if not provided)
            secret_key: AWS secret key (optional, uses IAM role if not provided)
        """
        try:
            import boto3
            from botocore.exceptions import ClientError

            self.ClientError = ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. "
                "Install it with: pip install boto3"
            )

        self.bucket = bucket
        self.region = region

        # Initialize S3 client
        session_kwargs = {"region_name": region}
        if access_key and secret_key:
            session_kwargs.update(
                {
                    "aws_access_key_id": access_key,
                    "aws_secret_access_key": secret_key,
                }
            )

        self.s3_client = boto3.client("s3", **session_kwargs)
        logger.info(f"Initialized S3Storage for bucket {bucket} in {region}")

    async def store(
        self, spans: List[SpanRequest], project_id: str, environment: str
    ) -> None:
        """
        Store spans to S3.

        Groups spans by trace_id and stores each trace as a separate object.

        Args:
            spans: List of spans to store
            project_id: Project identifier
            environment: Environment name

        Raises:
            StorageError: If S3 upload fails
        """
        try:
            # Group spans by trace_id
            traces = {}
            for span in spans:
                trace_id = span.trace_id
                if trace_id not in traces:
                    traces[trace_id] = []
                traces[trace_id].append(span.dict())

            # Upload each trace
            today = datetime.utcnow().strftime("%Y-%m-%d")

            for trace_id, trace_spans in traces.items():
                # Create S3 key
                key = f"{project_id}/{environment}/{today}/{trace_id}.json"

                trace_data = {
                    "trace_id": trace_id,
                    "project_id": project_id,
                    "environment": environment,
                    "stored_at": datetime.utcnow().isoformat(),
                    "span_count": len(trace_spans),
                    "spans": trace_spans,
                }

                # Upload to S3
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=json.dumps(trace_data, default=str),
                    ContentType="application/json",
                )

                logger.debug(f"Stored {len(trace_spans)} spans to s3://{self.bucket}/{key}")

            logger.info(
                f"Stored {len(spans)} spans across {len(traces)} traces "
                f"to S3 for project {project_id}/{environment}"
            )

        except self.ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise StorageError(f"S3 upload failed: {e}")
        except Exception as e:
            logger.error(f"Failed to store spans to S3: {e}")
            raise StorageError(f"Failed to store spans to S3: {e}")

    async def health_check(self) -> bool:
        """
        Check if S3 bucket is accessible.

        Returns:
            bool: True if bucket is accessible
        """
        try:
            # Try to head the bucket
            self.s3_client.head_bucket(Bucket=self.bucket)
            return True
        except self.ClientError as e:
            logger.error(f"S3 health check failed: {e}")
            return False
        except Exception as e:
            logger.error(f"S3 health check error: {e}")
            return False


def create_storage_backend(
    backend_type: str,
    storage_path: Optional[str] = None,
    s3_bucket: Optional[str] = None,
    s3_region: Optional[str] = None,
    s3_access_key: Optional[str] = None,
    s3_secret_key: Optional[str] = None,
) -> StorageBackend:
    """
    Factory function to create storage backend.

    Args:
        backend_type: Type of backend ('local' or 's3')
        storage_path: Path for local storage
        s3_bucket: S3 bucket name
        s3_region: S3 region
        s3_access_key: S3 access key
        s3_secret_key: S3 secret key

    Returns:
        StorageBackend: Configured storage backend

    Raises:
        ValueError: If backend_type is invalid or required parameters missing
    """
    if backend_type == "local":
        return LocalFileStorage(base_path=storage_path or "./data/traces")
    elif backend_type == "s3":
        if not s3_bucket:
            raise ValueError("s3_bucket is required for S3 storage backend")
        return S3Storage(
            bucket=s3_bucket,
            region=s3_region or "us-east-1",
            access_key=s3_access_key,
            secret_key=s3_secret_key,
        )
    else:
        raise ValueError(f"Unknown storage backend: {backend_type}")
