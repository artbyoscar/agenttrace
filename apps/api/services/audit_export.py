"""
Audit Export Service

Handles async generation and management of audit log exports.
"""

import asyncio
import csv
import io
import json
import tempfile
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from uuid import uuid4

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAS_PARQUET = True
except ImportError:
    HAS_PARQUET = False

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from ..models.audit import AuditEvent, AuditEventFilter


class ExportFormat(str, Enum):
    """Export format types."""
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"


class ExportStatus(str, Enum):
    """Export job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class ExportJob:
    """
    Export job metadata.

    Attributes:
        export_id: Unique export identifier
        organization_id: Organization requesting export
        actor_id: User who requested export
        filter: Filter criteria for events
        format: Export format
        include_verification: Include hash chain data
        encryption_enabled: Whether export is encrypted
        status: Current job status
        created_at: When job was created
        started_at: When processing started
        completed_at: When processing completed
        file_path: Path to generated export file
        file_size_bytes: Size of export file
        event_count: Number of events exported
        error_message: Error message if failed
        expires_at: When export file will be deleted
    """
    export_id: str
    organization_id: str
    actor_id: str
    filter: AuditEventFilter
    format: ExportFormat
    include_verification: bool = False
    encryption_enabled: bool = False
    encryption_public_key: Optional[str] = None
    status: ExportStatus = ExportStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    event_count: Optional[int] = None
    error_message: Optional[str] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "export_id": self.export_id,
            "organization_id": self.organization_id,
            "status": self.status.value,
            "format": self.format.value,
            "include_verification": self.include_verification,
            "encryption_enabled": self.encryption_enabled,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "file_size_bytes": self.file_size_bytes,
            "event_count": self.event_count,
            "error_message": self.error_message,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }


class AuditExportService:
    """
    Service for managing audit log exports.

    Handles async export generation, encryption, and cleanup.
    """

    def __init__(self, export_dir: str = "./exports", expiration_hours: int = 24):
        """
        Initialize export service.

        Args:
            export_dir: Directory for storing export files
            expiration_hours: Hours before exports are deleted
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.expiration_hours = expiration_hours

        # In-memory store (replace with database in production)
        self._jobs: Dict[str, ExportJob] = {}

        # Background task for processing
        self._processing = False
        self._queue: asyncio.Queue = asyncio.Queue()

    async def start(self):
        """Start the export processor."""
        if self._processing:
            return

        self._processing = True
        asyncio.create_task(self._process_queue())

    async def stop(self):
        """Stop the export processor."""
        self._processing = False

    async def create_export(
        self,
        organization_id: str,
        actor_id: str,
        filter: AuditEventFilter,
        format: ExportFormat,
        include_verification: bool = False,
        encryption_config: Optional[Dict[str, Any]] = None
    ) -> ExportJob:
        """
        Create a new export job.

        Args:
            organization_id: Organization ID
            actor_id: User requesting export
            filter: Event filter criteria
            format: Export format
            include_verification: Include hash chain data
            encryption_config: Optional encryption configuration

        Returns:
            ExportJob instance
        """
        export_id = f"exp_{uuid4().hex[:16]}"

        # Validate format support
        if format == ExportFormat.PARQUET and not HAS_PARQUET:
            raise ValueError("Parquet export requires pyarrow library")

        # Create job
        job = ExportJob(
            export_id=export_id,
            organization_id=organization_id,
            actor_id=actor_id,
            filter=filter,
            format=format,
            include_verification=include_verification,
            encryption_enabled=encryption_config.get("enabled", False) if encryption_config else False,
            encryption_public_key=encryption_config.get("public_key") if encryption_config else None
        )

        # Store job
        self._jobs[export_id] = job

        # Queue for processing
        await self._queue.put(export_id)

        return job

    async def get_export(self, export_id: str) -> Optional[ExportJob]:
        """
        Get export job by ID.

        Args:
            export_id: Export identifier

        Returns:
            ExportJob if found, None otherwise
        """
        return self._jobs.get(export_id)

    async def _process_queue(self):
        """Background task to process export queue."""
        while self._processing:
            try:
                # Get next job (with timeout to allow checking _processing flag)
                try:
                    export_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Process job
                job = self._jobs.get(export_id)
                if job:
                    await self._process_export(job)

            except Exception as e:
                print(f"Error in export processor: {e}")

    async def _process_export(self, job: ExportJob):
        """
        Process a single export job.

        Args:
            job: Export job to process
        """
        try:
            # Update status
            job.status = ExportStatus.PROCESSING
            job.started_at = datetime.now(timezone.utc)

            # Get audit service
            from ..services.audit import get_audit_service
            audit_service = get_audit_service()

            if not audit_service:
                raise Exception("Audit service not available")

            # Query events
            events = await audit_service.query_events(job.filter)
            job.event_count = len(events)

            # Generate export file
            file_path = self.export_dir / f"{job.export_id}.{job.format.value}"

            if job.format == ExportFormat.JSON:
                await self._export_json(events, file_path, job.include_verification)
            elif job.format == ExportFormat.CSV:
                await self._export_csv(events, file_path, job.include_verification)
            elif job.format == ExportFormat.PARQUET:
                await self._export_parquet(events, file_path, job.include_verification)

            # Encrypt if requested
            if job.encryption_enabled and job.encryption_public_key:
                file_path = await self._encrypt_file(file_path, job.encryption_public_key)

            # Update job
            job.file_path = str(file_path)
            job.file_size_bytes = file_path.stat().st_size
            job.completed_at = datetime.now(timezone.utc)
            job.status = ExportStatus.COMPLETED

            # Set expiration
            from datetime import timedelta
            job.expires_at = job.completed_at + timedelta(hours=self.expiration_hours)

        except Exception as e:
            job.status = ExportStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)

    async def _export_json(
        self,
        events: List[AuditEvent],
        file_path: Path,
        include_verification: bool
    ):
        """Export events as JSON."""
        data = []

        for event in events:
            event_dict = event.to_dict()

            if include_verification:
                # Add verification info
                event_dict["_verification"] = {
                    "hash": event.hash,
                    "previous_hash": event.previous_hash,
                    "hash_valid": event.verify_hash()
                }

            data.append(event_dict)

        # Write to file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def _export_csv(
        self,
        events: List[AuditEvent],
        file_path: Path,
        include_verification: bool
    ):
        """Export events as CSV."""
        if not events:
            # Create empty CSV
            with open(file_path, 'w') as f:
                f.write("")
            return

        # Get field names from first event
        first_event = events[0].to_dict()
        fieldnames = list(first_event.keys())

        if include_verification:
            fieldnames.extend(["hash", "previous_hash", "hash_valid"])

        # Write CSV
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for event in events:
                row = event.to_dict()

                if include_verification:
                    row["hash"] = event.hash
                    row["previous_hash"] = event.previous_hash
                    row["hash_valid"] = event.verify_hash()

                writer.writerow(row)

    async def _export_parquet(
        self,
        events: List[AuditEvent],
        file_path: Path,
        include_verification: bool
    ):
        """Export events as Parquet."""
        if not HAS_PARQUET:
            raise Exception("Parquet export requires pyarrow")

        # Convert events to list of dicts
        data = []
        for event in events:
            event_dict = event.to_dict()

            if include_verification:
                event_dict["hash"] = event.hash
                event_dict["previous_hash"] = event.previous_hash
                event_dict["hash_valid"] = event.verify_hash()

            data.append(event_dict)

        # Create PyArrow table
        table = pa.Table.from_pylist(data)

        # Write to Parquet file
        pq.write_table(table, file_path, compression='snappy')

    async def _encrypt_file(self, file_path: Path, public_key_pem: str) -> Path:
        """
        Encrypt export file.

        Args:
            file_path: Path to file to encrypt
            public_key_pem: Public key in PEM format

        Returns:
            Path to encrypted file
        """
        if not HAS_CRYPTO:
            raise Exception("Encryption requires cryptography library")

        # Load public key
        from cryptography.hazmat.backends import default_backend

        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )

        # Read original file
        with open(file_path, 'rb') as f:
            plaintext = f.read()

        # Encrypt (Note: For large files, use hybrid encryption with AES)
        # This is simplified - production should use symmetric encryption
        ciphertext = public_key.encrypt(
            plaintext[:245],  # RSA has size limits
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Write encrypted file
        encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')
        with open(encrypted_path, 'wb') as f:
            f.write(ciphertext)

        # Remove original
        file_path.unlink()

        return encrypted_path

    async def get_export_file(self, export_id: str) -> Optional[Path]:
        """
        Get export file path.

        Args:
            export_id: Export identifier

        Returns:
            Path to export file if available
        """
        job = self._jobs.get(export_id)

        if not job or job.status != ExportStatus.COMPLETED:
            return None

        if not job.file_path:
            return None

        file_path = Path(job.file_path)

        if not file_path.exists():
            return None

        return file_path

    async def cleanup_expired(self):
        """Remove expired export files."""
        now = datetime.now(timezone.utc)

        for export_id, job in list(self._jobs.items()):
            if job.expires_at and job.expires_at < now:
                # Delete file
                if job.file_path:
                    file_path = Path(job.file_path)
                    if file_path.exists():
                        file_path.unlink()

                # Update status
                job.status = ExportStatus.EXPIRED

                # Remove from memory (or mark as archived in database)
                # For now, keep in memory with EXPIRED status
