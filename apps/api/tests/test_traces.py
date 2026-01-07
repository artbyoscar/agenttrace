"""
Tests for trace ingestion endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
import asyncio

from ..ingestion_api import app
from ..services.ingestion import IngestionService
from ..services.storage import LocalFileStorage
from ..routers import traces


@pytest.fixture
def storage(tmp_path):
    """Create a temporary local storage."""
    return LocalFileStorage(base_path=str(tmp_path))


@pytest.fixture
async def ingestion_service(storage):
    """Create an ingestion service for testing."""
    service = IngestionService(
        storage=storage,
        batch_size=10,
        flush_interval=1.0,
        max_queue_size=100,
    )
    await service.start()
    yield service
    await service.shutdown()


@pytest.fixture
def client(ingestion_service):
    """Create a test client."""
    traces.set_ingestion_service(ingestion_service)
    return TestClient(app)


class TestBatchIngestion:
    """Tests for batch span ingestion."""

    def test_batch_ingestion_success(self, client):
        """Test successful batch ingestion."""
        request_data = {
            "project_id": "test-project",
            "environment": "test",
            "spans": [
                {
                    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                    "span_id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "test-span",
                    "start_time": "2024-01-01T00:00:00Z",
                    "span_type": "llm_call",
                    "framework": "langchain",
                }
            ],
        }

        response = client.post("/v1/traces", json=request_data)

        assert response.status_code == 202
        data = response.json()
        assert data["accepted"] == 1
        assert data["rejected"] == 0
        assert len(data["errors"]) == 0

    def test_batch_ingestion_multiple_spans(self, client):
        """Test batch ingestion with multiple spans."""
        request_data = {
            "project_id": "test-project",
            "environment": "test",
            "spans": [
                {
                    "trace_id": f"550e8400-e29b-41d4-a716-44665544000{i}",
                    "span_id": f"550e8400-e29b-41d4-a716-44665544100{i}",
                    "name": f"test-span-{i}",
                    "start_time": "2024-01-01T00:00:00Z",
                    "span_type": "llm_call",
                    "framework": "langchain",
                }
                for i in range(5)
            ],
        }

        response = client.post("/v1/traces", json=request_data)

        assert response.status_code == 202
        data = response.json()
        assert data["accepted"] == 5
        assert data["rejected"] == 0

    def test_batch_ingestion_validation_error(self, client):
        """Test batch ingestion with invalid span."""
        request_data = {
            "project_id": "test-project",
            "environment": "test",
            "spans": [
                {
                    # Missing required fields
                    "span_id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "test-span",
                }
            ],
        }

        response = client.post("/v1/traces", json=request_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "errors" in data or "detail" in data

    def test_batch_ingestion_empty_spans(self, client):
        """Test batch ingestion with empty spans array."""
        request_data = {
            "project_id": "test-project",
            "environment": "test",
            "spans": [],
        }

        response = client.post("/v1/traces", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_batch_ingestion_with_llm_metadata(self, client):
        """Test batch ingestion with LLM metadata."""
        request_data = {
            "project_id": "test-project",
            "environment": "test",
            "spans": [
                {
                    "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                    "span_id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "llm-call",
                    "start_time": "2024-01-01T00:00:00Z",
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
                }
            ],
        }

        response = client.post("/v1/traces", json=request_data)

        assert response.status_code == 202
        data = response.json()
        assert data["accepted"] == 1


class TestSingleIngestion:
    """Tests for single span ingestion."""

    def test_single_ingestion_success(self, client):
        """Test successful single span ingestion."""
        request_data = {
            "project_id": "test-project",
            "environment": "test",
            "span": {
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "span_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "test-span",
                "start_time": "2024-01-01T00:00:00Z",
                "span_type": "tool_call",
                "framework": "custom",
            },
        }

        response = client.post("/v1/traces/single", json=request_data)

        assert response.status_code == 202
        data = response.json()
        assert data["accepted"] == 1
        assert data["rejected"] == 0

    def test_single_ingestion_with_tool_metadata(self, client):
        """Test single span ingestion with tool metadata."""
        request_data = {
            "project_id": "test-project",
            "environment": "test",
            "span": {
                "trace_id": "550e8400-e29b-41d4-a716-446655440000",
                "span_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "tool-call",
                "start_time": "2024-01-01T00:00:00Z",
                "span_type": "tool_call",
                "framework": "custom",
                "tool": {
                    "tool_name": "calculator",
                    "tool_input": {"operation": "add", "a": 1, "b": 2},
                    "tool_output": {"result": 3},
                },
            },
        }

        response = client.post("/v1/traces/single", json=request_data)

        assert response.status_code == 202
        data = response.json()
        assert data["accepted"] == 1

    def test_single_ingestion_validation_error(self, client):
        """Test single span ingestion with invalid data."""
        request_data = {
            "project_id": "test-project",
            "environment": "test",
            "span": {
                # Missing required fields
                "name": "test-span",
            },
        }

        response = client.post("/v1/traces/single", json=request_data)

        assert response.status_code == 422  # Validation error


class TestPartialSuccess:
    """Tests for partial batch success scenarios."""

    @pytest.mark.asyncio
    async def test_queue_full_handling(self, storage):
        """Test handling of queue full scenario."""
        # Create service with very small queue
        service = IngestionService(
            storage=storage,
            batch_size=10,
            flush_interval=1.0,
            max_queue_size=2,  # Very small queue
        )
        await service.start()

        traces.set_ingestion_service(service)
        client = TestClient(app)

        # Try to ingest more spans than queue can hold
        request_data = {
            "project_id": "test-project",
            "environment": "test",
            "spans": [
                {
                    "trace_id": f"550e8400-e29b-41d4-a716-44665544000{i}",
                    "span_id": f"550e8400-e29b-41d4-a716-44665544100{i}",
                    "name": f"test-span-{i}",
                    "start_time": "2024-01-01T00:00:00Z",
                    "span_type": "llm_call",
                    "framework": "langchain",
                }
                for i in range(10)
            ],
        }

        response = client.post("/v1/traces", json=request_data)

        # Some should be rejected due to queue full
        data = response.json()
        assert data["rejected"] > 0
        assert len(data["errors"]) > 0

        await service.shutdown()
