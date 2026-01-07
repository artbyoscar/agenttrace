"""Tests for judge configuration."""

import os
import pytest
from agenttrace.evals.judge.config import (
    JudgeConfig,
    get_default_config,
    create_config_from_env,
    DEFAULT_CONFIGS,
)


class TestJudgeConfig:
    """Tests for JudgeConfig class."""

    def test_create_config_basic(self):
        """Test creating basic configuration."""
        # Mock environment variable
        os.environ["OPENAI_API_KEY"] = "test-key"

        config = JudgeConfig(provider="openai", model="gpt-4o-mini")

        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.0
        assert config.max_tokens == 1000
        assert config.api_key == "test-key"

        # Cleanup
        del os.environ["OPENAI_API_KEY"]

    def test_create_config_with_api_key(self):
        """Test creating config with explicit API key."""
        config = JudgeConfig(
            provider="openai", model="gpt-4o-mini", api_key="explicit-key"
        )

        assert config.api_key == "explicit-key"

    def test_invalid_provider(self):
        """Test that invalid provider raises error."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        with pytest.raises(ValueError, match="Invalid provider"):
            JudgeConfig(provider="invalid", model="model")

        del os.environ["OPENAI_API_KEY"]

    def test_missing_api_key(self):
        """Test that missing API key raises error."""
        # Ensure key is not in environment
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        with pytest.raises(ValueError, match="API key not provided"):
            JudgeConfig(provider="openai", model="gpt-4o-mini")

    def test_invalid_temperature(self):
        """Test that invalid temperature raises error."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        with pytest.raises(ValueError, match="Temperature must be"):
            JudgeConfig(provider="openai", model="gpt-4o-mini", temperature=3.0)

        del os.environ["OPENAI_API_KEY"]

    def test_invalid_max_tokens(self):
        """Test that invalid max_tokens raises error."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        with pytest.raises(ValueError, match="max_tokens must be"):
            JudgeConfig(provider="openai", model="gpt-4o-mini", max_tokens=0)

        del os.environ["OPENAI_API_KEY"]

    def test_to_dict(self):
        """Test converting config to dictionary."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        config_dict = config.to_dict()

        assert config_dict["provider"] == "openai"
        assert config_dict["model"] == "gpt-4o-mini"
        assert "api_key" not in config_dict  # Should be excluded

        del os.environ["OPENAI_API_KEY"]

    def test_anthropic_api_key_env(self):
        """Test Anthropic API key from environment."""
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        config = JudgeConfig(provider="anthropic", model="claude-3-opus-20240229")

        assert config.api_key == "test-key"

        del os.environ["ANTHROPIC_API_KEY"]

    def test_together_api_key_env(self):
        """Test Together API key from environment."""
        os.environ["TOGETHER_API_KEY"] = "test-key"

        config = JudgeConfig(provider="together", model="meta-llama/Llama-2-70b")

        assert config.api_key == "test-key"

        del os.environ["TOGETHER_API_KEY"]


class TestDefaultConfigs:
    """Tests for default configurations."""

    def test_get_default_config_fast(self):
        """Test getting fast preset."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        config = get_default_config("fast")

        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"

        del os.environ["OPENAI_API_KEY"]

    def test_get_default_config_balanced(self):
        """Test getting balanced preset."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        config = get_default_config("balanced")

        assert config.provider == "openai"
        assert config.model == "gpt-4o"

        del os.environ["OPENAI_API_KEY"]

    def test_get_default_config_best(self):
        """Test getting best preset."""
        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        config = get_default_config("best")

        assert config.provider == "anthropic"
        assert config.model == "claude-3-opus-20240229"

        del os.environ["ANTHROPIC_API_KEY"]

    def test_get_default_config_invalid(self):
        """Test that invalid preset raises error."""
        with pytest.raises(ValueError, match="Unknown preset"):
            get_default_config("invalid")

    def test_default_configs_are_copies(self):
        """Test that returned configs are copies, not references."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        config1 = get_default_config("fast")
        config2 = get_default_config("fast")

        # Modify one
        config1.temperature = 1.0

        # Other should be unaffected
        assert config2.temperature == 0.0

        del os.environ["OPENAI_API_KEY"]


class TestCreateConfigFromEnv:
    """Tests for environment-based configuration."""

    def test_create_from_env_defaults(self):
        """Test creating config with all defaults."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        # Remove custom env vars if they exist
        for key in ["JUDGE_PROVIDER", "JUDGE_MODEL", "JUDGE_TEMPERATURE"]:
            if key in os.environ:
                del os.environ[key]

        config = create_config_from_env()

        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.0

        del os.environ["OPENAI_API_KEY"]

    def test_create_from_env_custom(self):
        """Test creating config with custom environment variables."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["JUDGE_PROVIDER"] = "openai"
        os.environ["JUDGE_MODEL"] = "gpt-4o"
        os.environ["JUDGE_TEMPERATURE"] = "0.5"
        os.environ["JUDGE_MAX_TOKENS"] = "500"

        config = create_config_from_env()

        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.temperature == 0.5
        assert config.max_tokens == 500

        # Cleanup
        for key in [
            "OPENAI_API_KEY",
            "JUDGE_PROVIDER",
            "JUDGE_MODEL",
            "JUDGE_TEMPERATURE",
            "JUDGE_MAX_TOKENS",
        ]:
            if key in os.environ:
                del os.environ[key]

    def test_create_from_env_cache_disabled(self):
        """Test disabling cache via environment."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["JUDGE_CACHE"] = "false"

        config = create_config_from_env()

        assert config.cache_judgments is False

        # Cleanup
        del os.environ["OPENAI_API_KEY"]
        del os.environ["JUDGE_CACHE"]
