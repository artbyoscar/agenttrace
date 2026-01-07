"""
Pydantic models for API requests and responses.

These models provide validation and serialization for the API.
"""

from typing import Optional, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


# Request Models

class SpanRequest(BaseModel):
    """
    Request model for a single span.

    Matches the schema defined in packages/trace-schema/span.schema.json
    """

    # Core OpenTelemetry fields
    trace_id: str = Field(..., description="Unique trace identifier")
    span_id: str = Field(..., description="Unique span identifier")
    parent_span_id: Optional[str] = Field(None, description="Parent span ID")
    name: str = Field(..., min_length=1, max_length=256, description="Span name")
    start_time: str = Field(..., description="Start time (ISO 8601)")
    end_time: Optional[str] = Field(None, description="End time (ISO 8601)")
    duration: Optional[float] = Field(None, ge=0, description="Duration in seconds")

    # Status
    status: Literal["unset", "ok", "error"] = Field("unset", description="Span status")
    status_message: Optional[str] = Field(None, max_length=1024)

    # AI agent fields
    span_type: Literal[
        "llm_call",
        "embedding",
        "agent_step",
        "chain",
        "workflow",
        "tool_call",
        "retrieval",
        "search",
        "preprocessing",
        "postprocessing",
        "transformation",
        "memory_read",
        "memory_write",
        "span",
        "root",
    ] = Field(..., description="Type of operation")

    framework: Literal[
        "langchain",
        "crewai",
        "autogen",
        "openai_agents",
        "llamaindex",
        "semantic_kernel",
        "haystack",
        "custom",
        "unknown",
    ] = Field("unknown", description="Framework")

    # Input/Output
    input: Optional[Any] = Field(None, description="Input data")
    output: Optional[Any] = Field(None, description="Output data")

    # Type-specific metadata
    llm: Optional[dict] = Field(None, description="LLM metadata")
    tool: Optional[dict] = Field(None, description="Tool metadata")
    retrieval: Optional[dict] = Field(None, description="Retrieval metadata")

    # OpenTelemetry context
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[dict] = Field(default_factory=list)
    links: list[dict] = Field(default_factory=list)

    # Error
    error: Optional[dict] = Field(None, description="Error information")

    # Metadata
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("trace_id", "span_id", "parent_span_id")
    def validate_id_format(cls, v):
        """Validate ID format (should be UUID)."""
        if v is None:
            return v
        # Basic validation - could be stricter
        if not v or len(v) < 8:
            raise ValueError("Invalid ID format")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "span_id": "550e8400-e29b-41d4-a716-446655440001",
                "parent_span_id": None,
                "name": "llm_call",
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-01T00:00:01Z",
                "duration": 1.0,
                "status": "ok",
                "span_type": "llm_call",
                "framework": "langchain",
                "llm": {
                    "model": "gpt-4",
                    "provider": "openai",
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 20,
                        "total_tokens": 30,
                    },
                },
                "attributes": {"temperature": 0.7},
                "tags": ["production"],
            }
        }


class BatchSpanRequest(BaseModel):
    """
    Request model for batch span ingestion.

    Accepts multiple spans in a single request.
    """

    project_id: str = Field(..., description="Project identifier")
    environment: str = Field("development", description="Environment name")
    spans: list[SpanRequest] = Field(..., min_items=1, description="Array of spans")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "my-project",
                "environment": "production",
                "spans": [
                    {
                        "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                        "span_id": "550e8400-e29b-41d4-a716-446655440001",
                        "name": "llm_call",
                        "start_time": "2024-01-01T00:00:00Z",
                        "span_type": "llm_call",
                        "framework": "langchain",
                    }
                ],
            }
        }


class SingleSpanRequest(BaseModel):
    """
    Request model for single span ingestion.

    Includes project metadata.
    """

    project_id: str = Field(..., description="Project identifier")
    environment: str = Field("development", description="Environment name")
    span: SpanRequest = Field(..., description="Span data")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "my-project",
                "environment": "production",
                "span": {
                    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                    "span_id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "llm_call",
                    "start_time": "2024-01-01T00:00:00Z",
                    "span_type": "llm_call",
                    "framework": "langchain",
                },
            }
        }


# Response Models


class SpanError(BaseModel):
    """Error information for a rejected span."""

    span_id: Optional[str] = Field(None, description="Span ID if available")
    index: Optional[int] = Field(None, description="Index in batch")
    error: str = Field(..., description="Error message")
    field: Optional[str] = Field(None, description="Field that caused error")


class IngestionResponse(BaseModel):
    """
    Response model for span ingestion.

    Returns counts and errors for partial success.
    """

    accepted: int = Field(..., ge=0, description="Number of accepted spans")
    rejected: int = Field(..., ge=0, description="Number of rejected spans")
    errors: list[SpanError] = Field(default_factory=list, description="Error details")
    message: Optional[str] = Field(None, description="Additional message")

    class Config:
        json_schema_extra = {
            "example": {
                "accepted": 98,
                "rejected": 2,
                "errors": [
                    {
                        "span_id": "invalid-id",
                        "index": 5,
                        "error": "Invalid span_id format",
                        "field": "span_id",
                    },
                    {
                        "index": 10,
                        "error": "Missing required field: trace_id",
                        "field": "trace_id",
                    },
                ],
                "message": "Partial success",
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Health status"
    )
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="Uptime in seconds")
    queue_size: int = Field(..., description="Current queue size")
    processed_total: int = Field(..., description="Total spans processed")
    errors_total: int = Field(..., description="Total errors")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.5,
                "queue_size": 42,
                "processed_total": 1000000,
                "errors_total": 10,
            }
        }


class MetricsResponse(BaseModel):
    """Metrics response."""

    spans_received_total: int = Field(..., description="Total spans received")
    spans_accepted_total: int = Field(..., description="Total spans accepted")
    spans_rejected_total: int = Field(..., description="Total spans rejected")
    batches_processed_total: int = Field(..., description="Total batches processed")
    queue_size_current: int = Field(..., description="Current queue size")
    processing_duration_seconds: float = Field(
        ..., description="Average processing duration"
    )
    storage_errors_total: int = Field(..., description="Total storage errors")

    class Config:
        json_schema_extra = {
            "example": {
                "spans_received_total": 1000000,
                "spans_accepted_total": 998000,
                "spans_rejected_total": 2000,
                "batches_processed_total": 1000,
                "queue_size_current": 42,
                "processing_duration_seconds": 0.005,
                "storage_errors_total": 5,
            }
        }
