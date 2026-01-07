"""
Configuration management for AgentTrace API.

Loads configuration from environment variables with sensible defaults.
"""

import os
from typing import Literal
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables:
        API_HOST: Host to bind to (default: 0.0.0.0)
        API_PORT: Port to bind to (default: 8000)
        API_WORKERS: Number of worker processes (default: 4)
        API_RELOAD: Enable auto-reload for development (default: false)
        LOG_LEVEL: Logging level (default: info)
        CORS_ORIGINS: Comma-separated allowed origins (default: *)
        STORAGE_BACKEND: Storage backend type (default: local)
        STORAGE_PATH: Path for local storage (default: ./data/traces)
        S3_BUCKET: S3 bucket name for S3 storage
        S3_REGION: S3 region (default: us-east-1)
        BATCH_SIZE: Max spans per batch (default: 1000)
        BATCH_TIMEOUT: Max seconds before flush (default: 5.0)
        MAX_QUEUE_SIZE: Max spans in queue (default: 10000)
    """

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False

    # Logging
    log_level: Literal["debug", "info", "warning", "error", "critical"] = "info"

    # CORS
    cors_origins: str = "*"  # Comma-separated origins

    # Storage
    storage_backend: Literal["local", "s3"] = "local"
    storage_path: str = "./data/traces"

    # S3 Configuration (if using S3 backend)
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # Batch Processing
    batch_size: int = 1000  # Max spans per batch
    batch_timeout: float = 5.0  # Seconds
    max_queue_size: int = 10000  # Max spans in queue

    # Metrics
    enable_metrics: bool = True
    metrics_port: int = 9090

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def validate_config(self) -> None:
        """
        Validate configuration settings.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.storage_backend == "s3" and not self.s3_bucket:
            raise ValueError("S3_BUCKET must be set when using S3 storage backend")

        if self.batch_size <= 0:
            raise ValueError("BATCH_SIZE must be positive")

        if self.batch_timeout <= 0:
            raise ValueError("BATCH_TIMEOUT must be positive")

        if self.max_queue_size <= 0:
            raise ValueError("MAX_QUEUE_SIZE must be positive")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure singleton pattern.

    Returns:
        Settings: Application settings
    """
    settings = Settings()
    settings.validate_config()
    return settings
