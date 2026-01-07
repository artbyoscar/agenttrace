"""
Health check and metrics API endpoints.

Provides service health status and Prometheus-compatible metrics.
"""

import logging
from fastapi import APIRouter, Depends

from ..models.requests import HealthResponse, MetricsResponse
from ..services.ingestion import IngestionService
from .traces import get_ingestion_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/v1/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Get service health status and basic metrics.",
)
async def health_check(
    service: IngestionService = Depends(get_ingestion_service),
) -> HealthResponse:
    """
    Health check endpoint.

    Returns service status, uptime, and basic metrics.

    Args:
        service: Injected ingestion service

    Returns:
        HealthResponse: Health status and metrics
    """
    stats = service.get_stats()
    health_status = service.get_health_status()

    logger.debug(f"Health check: status={health_status}")

    return HealthResponse(
        status=health_status,
        version="1.0.0",  # TODO: Load from package version
        uptime=stats["uptime_seconds"],
        queue_size=stats["queue_size_current"],
        processed_total=stats["spans_accepted_total"],
        errors_total=stats["spans_rejected_total"] + stats["storage_errors_total"],
    )


@router.get(
    "/v1/metrics",
    response_model=MetricsResponse,
    summary="Prometheus metrics",
    description="Get detailed metrics in Prometheus-compatible format.",
)
async def get_metrics(
    service: IngestionService = Depends(get_ingestion_service),
) -> MetricsResponse:
    """
    Metrics endpoint.

    Returns detailed metrics for monitoring and alerting.

    Args:
        service: Injected ingestion service

    Returns:
        MetricsResponse: Detailed metrics
    """
    stats = service.get_stats()

    logger.debug("Metrics requested")

    return MetricsResponse(
        spans_received_total=stats["spans_received_total"],
        spans_accepted_total=stats["spans_accepted_total"],
        spans_rejected_total=stats["spans_rejected_total"],
        batches_processed_total=stats["batches_processed_total"],
        queue_size_current=stats["queue_size_current"],
        processing_duration_seconds=stats["processing_duration_seconds"],
        storage_errors_total=stats["storage_errors_total"],
    )


@router.get(
    "/health",
    response_model=dict,
    include_in_schema=False,
    summary="Simple health check",
    description="Simple health check without auth (for load balancers).",
)
async def simple_health() -> dict:
    """
    Simple health check endpoint.

    Returns a simple OK status without requiring authentication.
    Useful for load balancers and simple monitoring.

    Returns:
        dict: Simple status message
    """
    return {"status": "ok"}
