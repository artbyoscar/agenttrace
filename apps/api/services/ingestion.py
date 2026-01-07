"""
Async span ingestion service with batch processing.

Provides background processing of spans with automatic batching and flushing.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any
from collections import defaultdict
from dataclasses import dataclass, field

from ..models.requests import SpanRequest
from .storage import StorageBackend

logger = logging.getLogger(__name__)


@dataclass
class IngestionStats:
    """Statistics for ingestion service."""

    spans_received: int = 0
    spans_accepted: int = 0
    spans_rejected: int = 0
    batches_processed: int = 0
    storage_errors: int = 0
    processing_time_total: float = 0.0
    start_time: float = field(default_factory=time.time)

    @property
    def uptime(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self.start_time

    @property
    def average_processing_time(self) -> float:
        """Get average processing time per batch."""
        if self.batches_processed == 0:
            return 0.0
        return self.processing_time_total / self.batches_processed


class IngestionService:
    """
    Async ingestion service with background batch processing.

    Features:
    - Async span ingestion (non-blocking)
    - Automatic batching by project/environment
    - Background worker for batch processing
    - Periodic flushing (time-based)
    - Size-based flushing (batch size)
    - Graceful shutdown

    Usage:
        service = IngestionService(storage, batch_size=1000, flush_interval=5.0)
        await service.start()
        await service.ingest_span(span, project_id, environment)
        await service.shutdown()
    """

    def __init__(
        self,
        storage: StorageBackend,
        batch_size: int = 1000,
        flush_interval: float = 5.0,
        max_queue_size: int = 10000,
    ):
        """
        Initialize ingestion service.

        Args:
            storage: Storage backend for persisting spans
            batch_size: Maximum spans per batch before auto-flush
            flush_interval: Maximum seconds before auto-flush
            max_queue_size: Maximum spans in queue
        """
        self.storage = storage
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_queue_size = max_queue_size

        # Batches organized by (project_id, environment)
        self.batches: Dict[tuple, List[SpanRequest]] = defaultdict(list)
        self.batch_timestamps: Dict[tuple, float] = {}

        # Queue for incoming spans
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)

        # Worker task
        self.worker_task: asyncio.Task = None
        self.shutdown_event = asyncio.Event()

        # Statistics
        self.stats = IngestionStats()

        # Lock for batch operations
        self.batch_lock = asyncio.Lock()

        logger.info(
            f"Initialized IngestionService with batch_size={batch_size}, "
            f"flush_interval={flush_interval}s"
        )

    async def start(self) -> None:
        """
        Start the background worker.

        Must be called before ingesting spans.
        """
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Started ingestion worker")

    async def ingest_span(
        self, span: SpanRequest, project_id: str, environment: str
    ) -> None:
        """
        Ingest a single span (async, non-blocking).

        Adds the span to the queue for background processing.

        Args:
            span: Span to ingest
            project_id: Project identifier
            environment: Environment name

        Raises:
            asyncio.QueueFull: If queue is full
        """
        try:
            # Non-blocking put
            self.queue.put_nowait((span, project_id, environment))
            self.stats.spans_received += 1
        except asyncio.QueueFull:
            logger.warning("Ingestion queue is full, dropping span")
            self.stats.spans_rejected += 1
            raise

    async def ingest_batch(
        self, spans: List[SpanRequest], project_id: str, environment: str
    ) -> None:
        """
        Ingest multiple spans (async, non-blocking).

        Args:
            spans: List of spans to ingest
            project_id: Project identifier
            environment: Environment name

        Raises:
            asyncio.QueueFull: If queue is full
        """
        for span in spans:
            await self.ingest_span(span, project_id, environment)

    async def _worker_loop(self) -> None:
        """
        Background worker loop.

        Processes spans from the queue and manages batch flushing.
        """
        logger.info("Worker loop started")

        while not self.shutdown_event.is_set():
            try:
                # Process queued spans with timeout
                try:
                    span, project_id, environment = await asyncio.wait_for(
                        self.queue.get(), timeout=1.0
                    )

                    # Add to batch
                    await self._add_to_batch(span, project_id, environment)

                except asyncio.TimeoutError:
                    # No items in queue, check for time-based flush
                    pass

                # Check for flush conditions
                await self._check_and_flush()

            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)

        # Flush remaining spans on shutdown
        logger.info("Worker shutting down, flushing remaining spans")
        await self._flush_all()
        logger.info("Worker loop stopped")

    async def _add_to_batch(
        self, span: SpanRequest, project_id: str, environment: str
    ) -> None:
        """
        Add span to appropriate batch.

        Args:
            span: Span to add
            project_id: Project identifier
            environment: Environment name
        """
        async with self.batch_lock:
            batch_key = (project_id, environment)

            # Initialize batch if needed
            if batch_key not in self.batch_timestamps:
                self.batch_timestamps[batch_key] = time.time()

            # Add span to batch
            self.batches[batch_key].append(span)
            self.stats.spans_accepted += 1

            logger.debug(
                f"Added span to batch {batch_key}, "
                f"batch size: {len(self.batches[batch_key])}"
            )

    async def _check_and_flush(self) -> None:
        """
        Check flush conditions and flush batches if needed.

        Flushes based on:
        - Batch size (if batch reaches max size)
        - Time (if batch is older than flush interval)
        """
        async with self.batch_lock:
            now = time.time()
            batches_to_flush = []

            for batch_key, spans in self.batches.items():
                batch_age = now - self.batch_timestamps[batch_key]

                # Check size-based flush
                if len(spans) >= self.batch_size:
                    batches_to_flush.append(batch_key)
                    logger.debug(
                        f"Flushing batch {batch_key} due to size "
                        f"({len(spans)} >= {self.batch_size})"
                    )

                # Check time-based flush
                elif batch_age >= self.flush_interval:
                    batches_to_flush.append(batch_key)
                    logger.debug(
                        f"Flushing batch {batch_key} due to age "
                        f"({batch_age:.1f}s >= {self.flush_interval}s)"
                    )

            # Flush selected batches
            for batch_key in batches_to_flush:
                await self._flush_batch(batch_key)

    async def _flush_batch(self, batch_key: tuple) -> None:
        """
        Flush a specific batch to storage.

        Args:
            batch_key: (project_id, environment) tuple
        """
        project_id, environment = batch_key
        spans = self.batches[batch_key]

        if not spans:
            return

        start_time = time.time()

        try:
            # Store spans
            await self.storage.store(spans, project_id, environment)

            # Update stats
            self.stats.batches_processed += 1
            self.stats.processing_time_total += time.time() - start_time

            logger.info(
                f"Flushed batch {batch_key}: {len(spans)} spans in "
                f"{time.time() - start_time:.3f}s"
            )

            # Clear batch
            self.batches[batch_key] = []
            self.batch_timestamps[batch_key] = time.time()

        except Exception as e:
            logger.error(f"Failed to flush batch {batch_key}: {e}", exc_info=True)
            self.stats.storage_errors += 1

            # Keep spans in batch for retry
            # In production, implement retry logic or dead letter queue

    async def _flush_all(self) -> None:
        """Flush all batches."""
        async with self.batch_lock:
            batch_keys = list(self.batches.keys())

        for batch_key in batch_keys:
            await self._flush_batch(batch_key)

    async def flush(self) -> None:
        """
        Manually trigger flush of all batches.

        Useful for checkpoints or graceful shutdown.
        """
        await self._flush_all()

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the ingestion service.

        Stops the worker and flushes all pending spans.
        """
        logger.info("Shutting down ingestion service")

        # Signal shutdown
        self.shutdown_event.set()

        # Wait for worker to finish
        if self.worker_task and not self.worker_task.done():
            await self.worker_task

        logger.info("Ingestion service shutdown complete")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.

        Returns:
            dict: Statistics dictionary
        """
        return {
            "spans_received_total": self.stats.spans_received,
            "spans_accepted_total": self.stats.spans_accepted,
            "spans_rejected_total": self.stats.spans_rejected,
            "batches_processed_total": self.stats.batches_processed,
            "storage_errors_total": self.stats.storage_errors,
            "queue_size_current": self.queue.qsize(),
            "processing_duration_seconds": self.stats.average_processing_time,
            "uptime_seconds": self.stats.uptime,
        }

    def get_health_status(self) -> str:
        """
        Get health status.

        Returns:
            str: 'healthy', 'degraded', or 'unhealthy'
        """
        queue_size = self.queue.qsize()
        error_rate = (
            self.stats.spans_rejected / max(1, self.stats.spans_received)
            if self.stats.spans_received > 0
            else 0
        )

        # Unhealthy if worker is dead
        if self.worker_task and self.worker_task.done():
            return "unhealthy"

        # Degraded if queue is >80% full or error rate >5%
        if queue_size > self.max_queue_size * 0.8 or error_rate > 0.05:
            return "degraded"

        return "healthy"
