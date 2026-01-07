"""Tests for AgentTrace client"""

import pytest
from agenttrace import AgentTrace


def test_client_initialization():
    """Test client initialization"""
    client = AgentTrace(
        api_key="test-key",
        project="test-project",
        api_url="http://localhost:8000"
    )

    assert client.config.api_key == "test-key"
    assert client.config.project == "test-project"
    assert client.config.api_url == "http://localhost:8000"


def test_trace_decorator():
    """Test trace decorator"""
    client = AgentTrace(
        api_key="test-key",
        project="test-project",
        enabled=False  # Disable for testing
    )

    @client.trace_agent(name="test-trace")
    def test_function():
        return "result"

    result = test_function()
    assert result == "result"


def test_context_manager():
    """Test context manager"""
    client = AgentTrace(
        api_key="test-key",
        project="test-project",
        enabled=False
    )

    with client.start_trace("test-trace") as span:
        span.log("Test log")
        assert span.name == "test-trace"
        assert len(span.logs) == 1
