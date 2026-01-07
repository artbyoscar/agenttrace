"""
Audit Event Storage Backend

This module provides storage backends for audit events with write-once-read-many
(WORM) guarantees for compliance and tamper-proof audit trails.

Supported backends:
- LocalAuditStorage: File-based storage for development and testing
- S3AuditStorage: AWS S3 with Object Lock for production WORM compliance
"""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import uuid4

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ..models.audit import AuditEvent, AuditEventFilter


class AuditStorage(ABC):
    """
    Abstract base class for audit event storage backends.

    All implementations must provide write-once semantics to ensure
    audit trail immutability.
    """

    @abstractmethod
    async def write_event(self, event: AuditEvent) -> bool:
        """
        Write a single audit event to storage.

        Args:
            event: The audit event to store

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def write_events_batch(self, events: List[AuditEvent]) -> int:
        """
        Write multiple audit events in a batch for efficiency.

        Args:
            events: List of audit events to store

        Returns:
            Number of events successfully written
        """
        pass

    @abstractmethod
    async def read_event(self, event_id: str) -> Optional[AuditEvent]:
        """
        Read a single audit event by ID.

        Args:
            event_id: The event ID to retrieve

        Returns:
            The audit event if found, None otherwise
        """
        pass

    @abstractmethod
    async def query_events(
        self, filter: AuditEventFilter
    ) -> List[AuditEvent]:
        """
        Query audit events based on filter criteria.

        Args:
            filter: Filter criteria for the query

        Returns:
            List of matching audit events
        """
        pass

    @abstractmethod
    async def verify_integrity(
        self, organization_id: str, start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Verify the integrity of the audit chain.

        Args:
            organization_id: Organization to verify
            start_time: Optional start of time range
            end_time: Optional end of time range

        Returns:
            Dictionary with verification results
        """
        pass


class LocalAuditStorage(AuditStorage):
    """
    File-based audit storage for development and testing.

    Events are stored as JSON files in a directory structure organized
    by organization and date. This implementation provides append-only
    semantics by never modifying existing files.

    Note: This is NOT suitable for production compliance requirements.
    Use S3AuditStorage with Object Lock for production.
    """

    def __init__(self, base_path: str = "./audit_logs"):
        """
        Initialize local audit storage.

        Args:
            base_path: Base directory for storing audit logs
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_event_path(self, organization_id: str, event_id: str, timestamp: datetime) -> Path:
        """
        Get the file path for an audit event.

        Events are organized as: base_path/org_id/YYYY/MM/DD/event_id.json
        """
        date = timestamp.date()
        org_dir = self.base_path / organization_id / str(date.year) / f"{date.month:02d}" / f"{date.day:02d}"
        org_dir.mkdir(parents=True, exist_ok=True)
        return org_dir / f"{event_id}.json"

    async def write_event(self, event: AuditEvent) -> bool:
        """Write a single audit event to a JSON file."""
        try:
            event_path = self._get_event_path(
                event.organization_id, event.event_id, event.timestamp
            )

            # Check if event already exists (prevent overwrites)
            if event_path.exists():
                print(f"Warning: Audit event {event.event_id} already exists, skipping write")
                return False

            # Write event as JSON
            with open(event_path, 'w', encoding='utf-8') as f:
                json.dump(event.to_dict(), f, indent=2, default=str)

            # Make file read-only (simulates WORM)
            os.chmod(event_path, 0o444)

            return True

        except Exception as e:
            print(f"Error writing audit event {event.event_id}: {e}")
            return False

    async def write_events_batch(self, events: List[AuditEvent]) -> int:
        """Write multiple audit events in batch."""
        successful = 0
        for event in events:
            if await self.write_event(event):
                successful += 1
        return successful

    async def read_event(self, event_id: str) -> Optional[AuditEvent]:
        """
        Read a single audit event by ID.

        Note: This requires searching through the directory structure.
        For production, use a database index.
        """
        try:
            # Search through all organization directories
            for org_dir in self.base_path.iterdir():
                if not org_dir.is_dir():
                    continue

                # Search through year/month/day structure
                for year_dir in org_dir.iterdir():
                    if not year_dir.is_dir():
                        continue
                    for month_dir in year_dir.iterdir():
                        if not month_dir.is_dir():
                            continue
                        for day_dir in month_dir.iterdir():
                            if not day_dir.is_dir():
                                continue

                            event_path = day_dir / f"{event_id}.json"
                            if event_path.exists():
                                with open(event_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                return AuditEvent.from_dict(data)

            return None

        except Exception as e:
            print(f"Error reading audit event {event_id}: {e}")
            return None

    async def query_events(self, filter: AuditEventFilter) -> List[AuditEvent]:
        """
        Query audit events based on filter criteria.

        Note: This is a simple implementation. For production, use a
        database with proper indexing.
        """
        events = []

        try:
            # If organization_id is specified, only search that org
            if filter.organization_id:
                org_dirs = [self.base_path / filter.organization_id]
            else:
                org_dirs = [d for d in self.base_path.iterdir() if d.is_dir()]

            for org_dir in org_dirs:
                if not org_dir.exists():
                    continue

                # Walk through all event files
                for event_file in org_dir.rglob("*.json"):
                    try:
                        with open(event_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        event = AuditEvent.from_dict(data)

                        # Apply filters
                        if not self._matches_filter(event, filter):
                            continue

                        events.append(event)

                    except Exception as e:
                        print(f"Error reading event file {event_file}: {e}")
                        continue

            # Sort by timestamp (descending)
            events.sort(key=lambda e: e.timestamp, reverse=True)

            # Apply limit and offset
            start = filter.offset
            end = start + filter.limit
            return events[start:end]

        except Exception as e:
            print(f"Error querying audit events: {e}")
            return []

    def _matches_filter(self, event: AuditEvent, filter: AuditEventFilter) -> bool:
        """Check if an event matches the filter criteria."""
        if filter.organization_id and event.organization_id != filter.organization_id:
            return False
        if filter.project_id and event.project_id != filter.project_id:
            return False
        if filter.actor_type and event.actor_type != filter.actor_type:
            return False
        if filter.actor_id and event.actor_id != filter.actor_id:
            return False
        if filter.actor_email and event.actor_email != filter.actor_email:
            return False
        if filter.event_category and event.event_category != filter.event_category:
            return False
        if filter.event_type and event.event_type != filter.event_type:
            return False
        if filter.event_severity and event.event_severity != filter.event_severity:
            return False
        if filter.resource_type and event.resource_type != filter.resource_type:
            return False
        if filter.resource_id and event.resource_id != filter.resource_id:
            return False
        if filter.action and event.action != filter.action:
            return False
        if filter.start_time and event.timestamp < filter.start_time:
            return False
        if filter.end_time and event.timestamp > filter.end_time:
            return False

        return True

    async def verify_integrity(
        self, organization_id: str, start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Verify the integrity of the audit chain.

        Checks:
        1. Each event's hash matches its content
        2. Each event's previous_hash matches the previous event's hash
        """
        filter = AuditEventFilter(
            organization_id=organization_id,
            start_time=start_time,
            end_time=end_time,
            limit=10000  # Large limit for integrity check
        )

        events = await self.query_events(filter)

        if not events:
            return {
                "valid": True,
                "total_events": 0,
                "errors": []
            }

        # Sort by timestamp (ascending) for chain verification
        events.sort(key=lambda e: e.timestamp)

        errors = []

        # Verify each event's hash
        for event in events:
            if not event.verify_hash():
                errors.append({
                    "event_id": event.event_id,
                    "error": "Hash verification failed",
                    "timestamp": event.timestamp.isoformat()
                })

        # Verify chain integrity
        for i in range(1, len(events)):
            if not events[i].verify_chain(events[i - 1]):
                errors.append({
                    "event_id": events[i].event_id,
                    "error": "Chain verification failed",
                    "timestamp": events[i].timestamp.isoformat(),
                    "expected_previous_hash": events[i - 1].hash,
                    "actual_previous_hash": events[i].previous_hash
                })

        return {
            "valid": len(errors) == 0,
            "total_events": len(events),
            "verified_events": len(events) - len(errors),
            "errors": errors
        }


class S3AuditStorage(AuditStorage):
    """
    AWS S3 audit storage with Object Lock for WORM compliance.

    This implementation uses S3 Object Lock in COMPLIANCE mode to provide
    legally-binding immutability guarantees for audit events.

    Requirements:
    - S3 bucket with Object Lock enabled
    - Appropriate IAM permissions
    - boto3 library installed

    Configuration:
    - S3_BUCKET: Bucket name
    - S3_REGION: AWS region
    - S3_ACCESS_KEY: AWS access key
    - S3_SECRET_KEY: AWS secret key
    - S3_RETENTION_DAYS: Object Lock retention period (default: 7 years / 2555 days)
    """

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        retention_days: int = 2555  # 7 years for compliance
    ):
        """
        Initialize S3 audit storage.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key: AWS access key (optional, uses default credentials if not provided)
            secret_key: AWS secret key (optional)
            retention_days: Object Lock retention period in days
        """
        if not HAS_BOTO3:
            raise ImportError(
                "boto3 is required for S3AuditStorage. "
                "Install it with: pip install boto3"
            )

        self.bucket_name = bucket_name
        self.region = region
        self.retention_days = retention_days

        # Initialize S3 client
        session_kwargs = {"region_name": region}
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key

        self.s3_client = boto3.client('s3', **session_kwargs)

        # Verify bucket exists and has Object Lock enabled
        self._verify_bucket_config()

    def _verify_bucket_config(self):
        """Verify that the S3 bucket exists and has Object Lock enabled."""
        try:
            response = self.s3_client.get_object_lock_configuration(
                Bucket=self.bucket_name
            )
            if response['ObjectLockConfiguration']['ObjectLockEnabled'] != 'Enabled':
                print(f"Warning: Object Lock is not enabled on bucket {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ObjectLockConfigurationNotFoundError':
                print(f"Warning: Object Lock is not configured on bucket {self.bucket_name}")
            else:
                print(f"Warning: Could not verify Object Lock configuration: {e}")

    def _get_s3_key(self, organization_id: str, event_id: str, timestamp: datetime) -> str:
        """
        Generate S3 key for an audit event.

        Format: audit/{org_id}/{YYYY}/{MM}/{DD}/{event_id}.json
        """
        date = timestamp.date()
        return f"audit/{organization_id}/{date.year}/{date.month:02d}/{date.day:02d}/{event_id}.json"

    async def write_event(self, event: AuditEvent) -> bool:
        """Write a single audit event to S3 with Object Lock."""
        try:
            s3_key = self._get_s3_key(
                event.organization_id, event.event_id, event.timestamp
            )

            # Serialize event to JSON
            event_json = json.dumps(event.to_dict(), indent=2, default=str)

            # Calculate retention date
            from datetime import timedelta
            retention_date = datetime.now() + timedelta(days=self.retention_days)

            # Upload to S3 with Object Lock
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=event_json.encode('utf-8'),
                    ContentType='application/json',
                    ObjectLockMode='COMPLIANCE',
                    ObjectLockRetainUntilDate=retention_date,
                    Metadata={
                        'event_id': event.event_id,
                        'organization_id': event.organization_id,
                        'event_type': event.event_type,
                        'timestamp': event.timestamp.isoformat()
                    }
                )
            )

            return True

        except Exception as e:
            print(f"Error writing audit event to S3 {event.event_id}: {e}")
            return False

    async def write_events_batch(self, events: List[AuditEvent]) -> int:
        """Write multiple audit events in batch."""
        # S3 doesn't have a native batch API, so we write sequentially
        # For better performance, could use asyncio.gather with concurrency limit
        successful = 0
        tasks = [self.write_event(event) for event in events]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, bool) and result:
                successful += 1

        return successful

    async def read_event(self, event_id: str) -> Optional[AuditEvent]:
        """
        Read a single audit event by ID from S3.

        Note: This requires searching or using a metadata index.
        For production, maintain a database index.
        """
        # This is inefficient - in production, use DynamoDB or similar for indexing
        print("Warning: read_event with S3 requires a metadata index for efficiency")
        return None

    async def query_events(self, filter: AuditEventFilter) -> List[AuditEvent]:
        """
        Query audit events from S3.

        Note: S3 is not optimized for querying. For production,
        use S3 for immutable storage and maintain a queryable index
        in DynamoDB or PostgreSQL.
        """
        print("Warning: query_events with S3 requires a metadata index for efficiency")
        return []

    async def verify_integrity(
        self, organization_id: str, start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Verify integrity using S3 Object Lock metadata.

        This checks that objects are properly locked and cannot be modified.
        """
        try:
            prefix = f"audit/{organization_id}/"

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix
                )
            )

            total_objects = response.get('KeyCount', 0)
            locked_objects = 0

            if 'Contents' in response:
                for obj in response['Contents']:
                    try:
                        retention = await loop.run_in_executor(
                            None,
                            lambda: self.s3_client.get_object_retention(
                                Bucket=self.bucket_name,
                                Key=obj['Key']
                            )
                        )
                        if retention.get('Retention', {}).get('Mode') == 'COMPLIANCE':
                            locked_objects += 1
                    except ClientError:
                        # Object may not have retention set
                        pass

            return {
                "valid": total_objects == locked_objects,
                "total_events": total_objects,
                "locked_events": locked_objects,
                "errors": []
            }

        except Exception as e:
            return {
                "valid": False,
                "total_events": 0,
                "locked_events": 0,
                "errors": [{"error": str(e)}]
            }
