"""
Trace ingestion API endpoints.

Handles span ingestion with validation and error handling.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import ValidationError

from ..models.requests import (
    BatchSpanRequest,
    SingleSpanRequest,
    SpanRequest,
    IngestionResponse,
    SpanError,
)
from ..services.ingestion import IngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/traces", tags=["traces"])

# Global ingestion service instance (set in main.py)
_ingestion_service: IngestionService = None


def set_ingestion_service(service: IngestionService) -> None:
    """
    Set the global ingestion service.

    Called from main.py during startup.

    Args:
        service: IngestionService instance
    """
    global _ingestion_service
    _ingestion_service = service


def get_ingestion_service() -> IngestionService:
    """
    Dependency to get ingestion service.

    Returns:
        IngestionService: Global ingestion service instance

    Raises:
        HTTPException: If service is not initialized
    """
    if _ingestion_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion service not initialized",
        )
    return _ingestion_service


@router.post(
    "",
    response_model=IngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch span ingestion",
    description="Ingest multiple spans in a single request. "
    "Accepts partial batches - valid spans are accepted, invalid ones rejected.",
)
async def ingest_batch(
    request: BatchSpanRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> IngestionResponse:
    """
    Ingest a batch of spans.

    Returns counts and error details for partial success.

    Args:
        request: Batch span request with project_id, environment, and spans
        service: Injected ingestion service

    Returns:
        IngestionResponse: Accepted/rejected counts with error details
    """
    accepted = 0
    rejected = 0
    errors: List[SpanError] = []

    logger.info(
        f"Received batch ingestion request: {len(request.spans)} spans "
        f"for project {request.project_id}/{request.environment}"
    )

    # Process each span
    for index, span in enumerate(request.spans):
        try:
            # Attempt to ingest span
            await service.ingest_span(span, request.project_id, request.environment)
            accepted += 1

        except asyncio.QueueFull:
            # Queue is full
            rejected += 1
            errors.append(
                SpanError(
                    span_id=span.span_id,
                    index=index,
                    error="Ingestion queue is full, please retry later",
                )
            )
            logger.warning(f"Rejected span {span.span_id}: queue full")

        except Exception as e:
            # Unexpected error
            rejected += 1
            errors.append(
                SpanError(
                    span_id=getattr(span, "span_id", None),
                    index=index,
                    error=f"Failed to ingest span: {str(e)}",
                )
            )
            logger.error(f"Error ingesting span at index {index}: {e}", exc_info=True)

    # Prepare response
    message = None
    if rejected > 0:
        message = f"Partial success: {accepted} accepted, {rejected} rejected"
    else:
        message = f"Success: all {accepted} spans accepted"

    logger.info(
        f"Batch ingestion complete: {accepted} accepted, {rejected} rejected"
    )

    return IngestionResponse(
        accepted=accepted,
        rejected=rejected,
        errors=errors,
        message=message,
    )


@router.post(
    "/single",
    response_model=IngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Single span ingestion",
    description="Ingest a single span.",
)
async def ingest_single(
    request: SingleSpanRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> IngestionResponse:
    """
    Ingest a single span.

    Args:
        request: Single span request with project_id, environment, and span
        service: Injected ingestion service

    Returns:
        IngestionResponse: Acceptance status with error details if failed
    """
    logger.info(
        f"Received single span ingestion: {request.span.span_id} "
        f"for project {request.project_id}/{request.environment}"
    )

    try:
        # Ingest span
        await service.ingest_span(
            request.span, request.project_id, request.environment
        )

        logger.info(f"Successfully ingested span {request.span.span_id}")

        return IngestionResponse(
            accepted=1,
            rejected=0,
            errors=[],
            message="Span accepted",
        )

    except asyncio.QueueFull:
        # Queue is full
        logger.warning(f"Rejected span {request.span.span_id}: queue full")

        return IngestionResponse(
            accepted=0,
            rejected=1,
            errors=[
                SpanError(
                    span_id=request.span.span_id,
                    error="Ingestion queue is full, please retry later",
                )
            ],
            message="Span rejected",
        )

    except Exception as e:
        # Unexpected error
        logger.error(
            f"Error ingesting span {request.span.span_id}: {e}", exc_info=True
        )

        return IngestionResponse(
            accepted=0,
            rejected=1,
            errors=[
                SpanError(
                    span_id=request.span.span_id,
                    error=f"Failed to ingest span: {str(e)}",
                )
            ],
            message="Span rejected",
        )


# Import asyncio for queue handling
import asyncio
