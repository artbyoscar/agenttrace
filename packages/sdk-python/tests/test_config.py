"""Unit tests for config module."""

import os
import pytest
from agenttrace.config import AgentTraceConfig, ExportMode, LogLevel, _parse_bool


class TestAgentTraceConfig:
    """Tests for AgentTraceConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AgentTraceConfig()

        assert config.api_key == ""
        assert config.project_id == "default"
        assert config.api_url == "http://localhost:8000"
        assert config.environment == "development"
        assert config.enabled is True
        assert config.export_mode == ExportMode.ASYNC
        assert config.batch_size == 10
        assert config.flush_interval == 5.0

    def test_custom_config(self):
        """Test configuration with custom values."""
        config = AgentTraceConfig(
            api_key="test-key",
            project_id="test-project",
            api_url="https://api.example.com",
            environment="production",
            batch_size=20,
        )

        assert config.api_key == "test-key"
        assert config.project_id == "test-project"
        assert config.api_url == "https://api.example.com"
        assert config.environment == "production"
        assert config.batch_size == 20

    def test_validation_errors(self):
        """Test configuration validation errors."""
        # Empty project_id
        with pytest.raises(ValueError, match="project_id cannot be empty"):
            AgentTraceConfig(project_id="")

        # Invalid timeout
        with pytest.raises(ValueError, match="timeout must be positive"):
            AgentTraceConfig(timeout=0)

        # Invalid batch_size
        with pytest.raises(ValueError, match="batch_size must be positive"):
            AgentTraceConfig(batch_size=-1)

        # Invalid sample_rate
        with pytest.raises(ValueError, match="sample_rate must be between 0.0 and 1.0"):
            AgentTraceConfig(sample_rate=1.5)

    def test_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        # Set environment variables
        monkeypatch.setenv("AGENTTRACE_API_KEY", "env-key")
        monkeypatch.setenv("AGENTTRACE_PROJECT_ID", "env-project")
        monkeypatch.setenv("AGENTTRACE_API_URL", "https://env.example.com")
        monkeypatch.setenv("AGENTTRACE_ENVIRONMENT", "staging")
        monkeypatch.setenv("AGENTTRACE_ENABLED", "true")
        monkeypatch.setenv("AGENTTRACE_TAGS", "tag1,tag2,tag3")
        monkeypatch.setenv("AGENTTRACE_BATCH_SIZE", "25")
        monkeypatch.setenv("AGENTTRACE_EXPORT_MODE", "sync")

        config = AgentTraceConfig.from_env()

        assert config.api_key == "env-key"
        assert config.project_id == "env-project"
        assert config.api_url == "https://env.example.com"
        assert config.environment == "staging"
        assert config.enabled is True
        assert config.tags == ["tag1", "tag2", "tag3"]
        assert config.batch_size == 25
        assert config.export_mode == ExportMode.SYNC

    def test_from_env_with_override(self, monkeypatch):
        """Test that kwargs override environment variables."""
        monkeypatch.setenv("AGENTTRACE_API_KEY", "env-key")
        monkeypatch.setenv("AGENTTRACE_PROJECT_ID", "env-project")

        config = AgentTraceConfig.from_env(
            api_key="override-key",
            project_id="override-project",
        )

        assert config.api_key == "override-key"
        assert config.project_id == "override-project"

    def test_to_dict(self):
        """Test configuration serialization to dict."""
        config = AgentTraceConfig(
            api_key="secret-key",
            project_id="test-project",
            tags=["tag1", "tag2"],
        )

        config_dict = config.to_dict()

        assert config_dict["api_key"] == "***"  # Redacted
        assert config_dict["project_id"] == "test-project"
        assert config_dict["tags"] == ["tag1", "tag2"]
        assert config_dict["enabled"] is True


class TestParseBool:
    """Tests for _parse_bool helper function."""

    def test_true_values(self):
        """Test parsing true values."""
        assert _parse_bool("true") is True
        assert _parse_bool("True") is True
        assert _parse_bool("TRUE") is True
        assert _parse_bool("1") is True
        assert _parse_bool("yes") is True
        assert _parse_bool("on") is True

    def test_false_values(self):
        """Test parsing false values."""
        assert _parse_bool("false") is False
        assert _parse_bool("False") is False
        assert _parse_bool("0") is False
        assert _parse_bool("no") is False
        assert _parse_bool("off") is False
        assert _parse_bool("anything_else") is False


class TestExportMode:
    """Tests for ExportMode enum."""

    def test_export_mode_values(self):
        """Test ExportMode enum values."""
        assert ExportMode.SYNC.value == "sync"
        assert ExportMode.ASYNC.value == "async"
        assert ExportMode.DISABLED.value == "disabled"


class TestLogLevel:
    """Tests for LogLevel enum."""

    def test_log_level_values(self):
        """Test LogLevel enum values."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.CRITICAL.value == "critical"
