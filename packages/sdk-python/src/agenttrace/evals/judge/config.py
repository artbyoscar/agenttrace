"""Configuration for LLM-as-judge infrastructure."""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class JudgeConfig:
    """Configuration for LLM judge clients.

    Attributes:
        provider: LLM provider ("openai", "anthropic", "together")
        model: Model identifier (e.g., "gpt-4o", "claude-3-opus-20240229")
        temperature: Sampling temperature (0.0 for consistency)
        max_tokens: Maximum tokens in response
        timeout_seconds: Request timeout
        max_retries: Maximum retry attempts on failure
        api_key: API key (defaults to environment variable)
        base_url: Optional custom base URL
        extra_headers: Additional HTTP headers
        cache_judgments: Whether to cache identical judgments

    Example:
        >>> config = JudgeConfig(
        ...     provider="openai",
        ...     model="gpt-4o-mini",
        ...     temperature=0.0
        ... )
    """

    provider: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 1000
    timeout_seconds: int = 30
    max_retries: int = 3
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None
    cache_judgments: bool = True

    def __post_init__(self):
        """Validate configuration and set defaults from environment."""
        # Validate provider
        valid_providers = ["openai", "anthropic", "together"]
        if self.provider not in valid_providers:
            raise ValueError(
                f"Invalid provider '{self.provider}'. Must be one of: {valid_providers}"
            )

        # Set API key from environment if not provided
        if self.api_key is None:
            env_key = self._get_env_key_name()
            self.api_key = os.getenv(env_key)
            if self.api_key is None:
                raise ValueError(
                    f"API key not provided and {env_key} environment variable not set"
                )

        # Validate temperature range
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")

        # Validate max_tokens
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")

    def _get_env_key_name(self) -> str:
        """Get the environment variable name for the API key.

        Returns:
            Environment variable name
        """
        env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "together": "TOGETHER_API_KEY",
        }
        return env_map.get(self.provider, f"{self.provider.upper()}_API_KEY")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dictionary representation (excluding sensitive data)
        """
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "cache_judgments": self.cache_judgments,
        }


# Default configurations for common use cases

DEFAULT_CONFIGS = {
    # Fast, cost-effective for most evaluations
    "fast": JudgeConfig(
        provider="openai",
        model="gpt-4o-mini",
        temperature=0.0,
        max_tokens=500,
    ),
    # Balanced quality and cost
    "balanced": JudgeConfig(
        provider="openai",
        model="gpt-4o",
        temperature=0.0,
        max_tokens=1000,
    ),
    # Highest quality for critical evaluations
    "best": JudgeConfig(
        provider="anthropic",
        model="claude-3-opus-20240229",
        temperature=0.0,
        max_tokens=1500,
    ),
    # Anthropic Sonnet - good balance
    "sonnet": JudgeConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        temperature=0.0,
        max_tokens=1000,
    ),
    # Anthropic Haiku - fastest
    "haiku": JudgeConfig(
        provider="anthropic",
        model="claude-3-5-haiku-20241022",
        temperature=0.0,
        max_tokens=500,
    ),
}


def get_default_config(preset: str = "fast") -> JudgeConfig:
    """Get a default judge configuration.

    Args:
        preset: Configuration preset name

    Returns:
        JudgeConfig instance

    Raises:
        ValueError: If preset is not found

    Example:
        >>> config = get_default_config("fast")
        >>> config.model
        'gpt-4o-mini'
    """
    if preset not in DEFAULT_CONFIGS:
        available = ", ".join(DEFAULT_CONFIGS.keys())
        raise ValueError(
            f"Unknown preset '{preset}'. Available presets: {available}"
        )

    # Return a copy to avoid modifying the default
    default = DEFAULT_CONFIGS[preset]
    return JudgeConfig(
        provider=default.provider,
        model=default.model,
        temperature=default.temperature,
        max_tokens=default.max_tokens,
        timeout_seconds=default.timeout_seconds,
        max_retries=default.max_retries,
        cache_judgments=default.cache_judgments,
    )


def create_config_from_env() -> JudgeConfig:
    """Create configuration from environment variables.

    Environment variables:
        JUDGE_PROVIDER: Provider name (default: "openai")
        JUDGE_MODEL: Model name (default: "gpt-4o-mini")
        JUDGE_TEMPERATURE: Temperature (default: "0.0")
        JUDGE_MAX_TOKENS: Max tokens (default: "1000")
        JUDGE_TIMEOUT: Timeout in seconds (default: "30")
        JUDGE_MAX_RETRIES: Max retries (default: "3")
        JUDGE_CACHE: Enable caching (default: "true")

    Returns:
        JudgeConfig instance

    Example:
        >>> os.environ["JUDGE_MODEL"] = "gpt-4o"
        >>> config = create_config_from_env()
        >>> config.model
        'gpt-4o'
    """
    provider = os.getenv("JUDGE_PROVIDER", "openai")
    model = os.getenv("JUDGE_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("JUDGE_TEMPERATURE", "0.0"))
    max_tokens = int(os.getenv("JUDGE_MAX_TOKENS", "1000"))
    timeout = int(os.getenv("JUDGE_TIMEOUT", "30"))
    max_retries = int(os.getenv("JUDGE_MAX_RETRIES", "3"))
    cache = os.getenv("JUDGE_CACHE", "true").lower() == "true"

    return JudgeConfig(
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_seconds=timeout,
        max_retries=max_retries,
        cache_judgments=cache,
    )
