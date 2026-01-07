"""
Tests for health and metrics endpoints.
"""

import pytest
from fastapi.testclient import TestClient

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


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "version" in data
        assert "uptime" in data
        assert "queue_size" in data
        assert "processed_total" in data
        assert "errors_total" in data

    def test_simple_health_check(self, client):
        """Test simple health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestMetricsEndpoint:
    """Tests for metrics endpoint."""

    def test_metrics(self, client):
        """Test metrics endpoint."""
        response = client.get("/v1/metrics")

        assert response.status_code == 200
        data = response.json()

        # Check all required metrics are present
        assert "spans_received_total" in data
        assert "spans_accepted_total" in data
        assert "spans_rejected_total" in data
        assert "batches_processed_total" in data
        assert "queue_size_current" in data
        assert "processing_duration_seconds" in data
        assert "storage_errors_total" in data

        # All should be non-negative
        for key, value in data.items():
            assert value >= 0

    def test_metrics_after_ingestion(self, client):
        """Test metrics after ingesting spans."""
        # Ingest some spans
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

        client.post("/v1/traces", json=request_data)

        # Check metrics
        response = client.get("/v1/metrics")
        data = response.json()

        assert data["spans_received_total"] >= 1
        assert data["spans_accepted_total"] >= 1


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
