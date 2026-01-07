"""
Configuration management for AgentTrace SDK.

Provides comprehensive configuration with environment variable loading,
validation, and sensible defaults for all SDK settings.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ExportMode(str, Enum):
    """Export mode for spans."""

    SYNC = "sync"  # Synchronous export
    ASYNC = "async"  # Asynchronous export with batching
    DISABLED = "disabled"  # No export (useful for testing)


class LogLevel(str, Enum):
    """Logging levels for SDK internal logging."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AgentTraceConfig:
    """
    Comprehensive configuration for AgentTrace SDK.

    This configuration can be initialized directly or loaded from environment
    variables. Environment variables take precedence over default values.

    Environment Variables:
        AGENTTRACE_API_KEY: API key for authentication
        AGENTTRACE_PROJECT_ID: Project identifier
        AGENTTRACE_API_URL: API endpoint URL
        AGENTTRACE_ENVIRONMENT: Environment name (dev, staging, prod)
        AGENTTRACE_ENABLED: Enable/disable tracing (true/false)
        AGENTTRACE_TAGS: Comma-separated tags
        AGENTTRACE_EXPORT_MODE: Export mode (sync/async/disabled)
        AGENTTRACE_BATCH_SIZE: Batch size for async export
        AGENTTRACE_FLUSH_INTERVAL: Flush interval in seconds
        AGENTTRACE_MAX_QUEUE_SIZE: Maximum queue size for async export
        AGENTTRACE_TIMEOUT: HTTP request timeout in seconds
        AGENTTRACE_MAX_RETRIES: Maximum number of retries
        AGENTTRACE_CAPTURE_INPUT: Capture input data (true/false)
        AGENTTRACE_CAPTURE_OUTPUT: Capture output data (true/false)
        AGENTTRACE_MAX_ATTRIBUTE_LENGTH: Max length for attribute values
        AGENTTRACE_LOG_LEVEL: SDK log level

    Example:
        >>> config = AgentTraceConfig.from_env()
        >>> config = AgentTraceConfig(
        ...     api_key="my-key",
        ...     project_id="my-project",
        ...     environment="production"
        ... )
    """

    # Authentication & Project
    api_key: str = ""
    project_id: str = "default"

    # API Configuration
    api_url: str = "http://localhost:8000"
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

    # Environment & Tags
    environment: str = "development"
    tags: List[str] = field(default_factory=list)

    # Enable/Disable
    enabled: bool = True

    # Export Configuration
    export_mode: ExportMode = ExportMode.ASYNC
    batch_size: int = 10  # spans per batch
    flush_interval: float = 5.0  # seconds
    max_queue_size: int = 1000  # maximum spans in queue

    # Data Capture
    capture_input: bool = True
    capture_output: bool = True
    capture_headers: bool = False  # Capture HTTP headers
    max_attribute_length: int = 4096  # Maximum length for attribute values
    max_events_per_span: int = 100  # Maximum events per span

    # Sampling (future feature)
    sample_rate: float = 1.0  # 0.0 to 1.0

    # SDK Behavior
    log_level: LogLevel = LogLevel.WARNING
    console_export: bool = False  # Also export to console (for debugging)
    file_export: bool = False  # Also export to file
    file_export_path: str = "./traces"

    # Performance
    async_worker_threads: int = 1

    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate configuration settings.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate API key (warn if missing, but don't fail)
        if self.enabled and not self.api_key and self.export_mode != ExportMode.DISABLED:
            import warnings
            warnings.warn(
                "AGENTTRACE_API_KEY not set. Tracing will be disabled.",
                UserWarning
            )

        # Validate project_id
        if not self.project_id:
            raise ValueError("project_id cannot be empty")

        # Validate timeout
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        # Validate max_retries
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")

        # Validate batch_size
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")

        # Validate flush_interval
        if self.flush_interval <= 0:
            raise ValueError("flush_interval must be positive")

        # Validate max_queue_size
        if self.max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")

        # Validate sample_rate
        if not 0.0 <= self.sample_rate <= 1.0:
            raise ValueError("sample_rate must be between 0.0 and 1.0")

        # Validate max_attribute_length
        if self.max_attribute_length <= 0:
            raise ValueError("max_attribute_length must be positive")

        # Validate max_events_per_span
        if self.max_events_per_span <= 0:
            raise ValueError("max_events_per_span must be positive")

        # Validate async_worker_threads
        if self.async_worker_threads <= 0:
            raise ValueError("async_worker_threads must be positive")

    @classmethod
    def from_env(cls, **kwargs) -> "AgentTraceConfig":
        """
        Create configuration from environment variables.

        Environment variables are merged with provided kwargs,
        with kwargs taking precedence.

        Args:
            **kwargs: Override specific configuration values

        Returns:
            AgentTraceConfig: Configuration instance

        Example:
            >>> config = AgentTraceConfig.from_env()
            >>> config = AgentTraceConfig.from_env(environment="production")
        """
        # Load from environment
        env_config = {
            "api_key": os.getenv("AGENTTRACE_API_KEY", ""),
            "project_id": os.getenv("AGENTTRACE_PROJECT_ID", "default"),
            "api_url": os.getenv("AGENTTRACE_API_URL", "http://localhost:8000"),
            "environment": os.getenv("AGENTTRACE_ENVIRONMENT", "development"),
            "enabled": _parse_bool(os.getenv("AGENTTRACE_ENABLED", "true")),
            "timeout": int(os.getenv("AGENTTRACE_TIMEOUT", "30")),
            "max_retries": int(os.getenv("AGENTTRACE_MAX_RETRIES", "3")),
            "retry_delay": float(os.getenv("AGENTTRACE_RETRY_DELAY", "1.0")),
            "batch_size": int(os.getenv("AGENTTRACE_BATCH_SIZE", "10")),
            "flush_interval": float(os.getenv("AGENTTRACE_FLUSH_INTERVAL", "5.0")),
            "max_queue_size": int(os.getenv("AGENTTRACE_MAX_QUEUE_SIZE", "1000")),
            "capture_input": _parse_bool(os.getenv("AGENTTRACE_CAPTURE_INPUT", "true")),
            "capture_output": _parse_bool(os.getenv("AGENTTRACE_CAPTURE_OUTPUT", "true")),
            "capture_headers": _parse_bool(os.getenv("AGENTTRACE_CAPTURE_HEADERS", "false")),
            "max_attribute_length": int(os.getenv("AGENTTRACE_MAX_ATTRIBUTE_LENGTH", "4096")),
            "max_events_per_span": int(os.getenv("AGENTTRACE_MAX_EVENTS_PER_SPAN", "100")),
            "sample_rate": float(os.getenv("AGENTTRACE_SAMPLE_RATE", "1.0")),
            "console_export": _parse_bool(os.getenv("AGENTTRACE_CONSOLE_EXPORT", "false")),
            "file_export": _parse_bool(os.getenv("AGENTTRACE_FILE_EXPORT", "false")),
            "file_export_path": os.getenv("AGENTTRACE_FILE_EXPORT_PATH", "./traces"),
            "async_worker_threads": int(os.getenv("AGENTTRACE_ASYNC_WORKER_THREADS", "1")),
        }

        # Parse tags
        tags_str = os.getenv("AGENTTRACE_TAGS", "")
        if tags_str:
            env_config["tags"] = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

        # Parse export mode
        export_mode_str = os.getenv("AGENTTRACE_EXPORT_MODE", "async").lower()
        if export_mode_str == "sync":
            env_config["export_mode"] = ExportMode.SYNC
        elif export_mode_str == "async":
            env_config["export_mode"] = ExportMode.ASYNC
        elif export_mode_str == "disabled":
            env_config["export_mode"] = ExportMode.DISABLED

        # Parse log level
        log_level_str = os.getenv("AGENTTRACE_LOG_LEVEL", "warning").lower()
        if log_level_str == "debug":
            env_config["log_level"] = LogLevel.DEBUG
        elif log_level_str == "info":
            env_config["log_level"] = LogLevel.INFO
        elif log_level_str == "warning":
            env_config["log_level"] = LogLevel.WARNING
        elif log_level_str == "error":
            env_config["log_level"] = LogLevel.ERROR
        elif log_level_str == "critical":
            env_config["log_level"] = LogLevel.CRITICAL

        # Merge with kwargs (kwargs take precedence)
        env_config.update(kwargs)

        return cls(**env_config)

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.

        Returns:
            dict: Configuration as dictionary
        """
        return {
            "api_key": "***" if self.api_key else "",  # Redact API key
            "project_id": self.project_id,
            "api_url": self.api_url,
            "environment": self.environment,
            "enabled": self.enabled,
            "export_mode": self.export_mode.value,
            "tags": self.tags,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "batch_size": self.batch_size,
            "flush_interval": self.flush_interval,
            "max_queue_size": self.max_queue_size,
            "capture_input": self.capture_input,
            "capture_output": self.capture_output,
            "sample_rate": self.sample_rate,
            "log_level": self.log_level.value,
        }


def _parse_bool(value: str) -> bool:
    """
    Parse a string as a boolean.

    Args:
        value: String value to parse

    Returns:
        bool: Parsed boolean value

    Examples:
        >>> _parse_bool("true")
        True
        >>> _parse_bool("false")
        False
        >>> _parse_bool("1")
        True
        >>> _parse_bool("0")
        False
    """
    return value.lower() in ("true", "1", "yes", "on")


# Backwards compatibility
Config = AgentTraceConfig
