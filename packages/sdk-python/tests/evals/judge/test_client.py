"""Tests for judge client."""

import pytest
import os
from agenttrace.evals.judge.client import JudgeClient, MockJudgeClient
from agenttrace.evals.judge.config import JudgeConfig
from agenttrace.evals.judge.parser import Judgment
from agenttrace.evals.judge.costs import get_global_tracker, reset_global_tracker


class TestMockJudgeClient:
    """Tests for MockJudgeClient."""

    @pytest.mark.asyncio
    async def test_mock_client_basic(self):
        """Test basic mock client usage."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client = MockJudgeClient(config)

        judgment = await client.judge("Test prompt")

        assert isinstance(judgment, Judgment)
        assert 0.0 <= judgment.score <= 1.0
        assert judgment.reasoning is not None

        del os.environ["OPENAI_API_KEY"]

    @pytest.mark.asyncio
    async def test_mock_client_custom_score(self):
        """Test mock client with custom score."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client = MockJudgeClient(
            config, default_score=0.95, default_reasoning="Perfect!"
        )

        judgment = await client.judge("Test prompt")

        assert judgment.score == 0.95
        assert judgment.reasoning == "Perfect!"

        del os.environ["OPENAI_API_KEY"]

    @pytest.mark.asyncio
    async def test_mock_client_call_count(self):
        """Test that mock client tracks calls."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client = MockJudgeClient(config)

        assert client.call_count == 0

        await client.judge("Test 1")
        assert client.call_count == 1

        await client.judge("Test 2")
        assert client.call_count == 2

        del os.environ["OPENAI_API_KEY"]

    @pytest.mark.asyncio
    async def test_mock_client_tracks_costs(self):
        """Test that mock client tracks costs."""
        reset_global_tracker()
        os.environ["OPENAI_API_KEY"] = "test-key"

        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client = MockJudgeClient(config)

        tracker = get_global_tracker()
        initial_count = tracker.judgment_count

        await client.judge("Test prompt")

        assert tracker.judgment_count == initial_count + 1
        assert tracker.total_tokens > 0

        del os.environ["OPENAI_API_KEY"]


class TestJudgeClient:
    """Tests for JudgeClient (using mock mode)."""

    @pytest.mark.asyncio
    async def test_client_caching(self):
        """Test that identical prompts are cached."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini", cache_judgments=True)
        client = MockJudgeClient(config)

        prompt = "Evaluate this"

        # First call
        judgment1 = await client.judge(prompt)
        call_count_1 = client.call_count

        # Second call with same prompt
        judgment2 = await client.judge(prompt)
        call_count_2 = client.call_count

        # Should be cached, no new API call
        assert call_count_2 == call_count_1  # No new call
        assert judgment1.score == judgment2.score

        del os.environ["OPENAI_API_KEY"]

    @pytest.mark.asyncio
    async def test_client_no_caching(self):
        """Test that caching can be disabled."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini", cache_judgments=False)
        client = MockJudgeClient(config)

        prompt = "Evaluate this"

        # First call
        await client.judge(prompt)
        call_count_1 = client.call_count

        # Second call with same prompt
        await client.judge(prompt)
        call_count_2 = client.call_count

        # Should NOT be cached, new API call made
        assert call_count_2 > call_count_1

        del os.environ["OPENAI_API_KEY"]

    @pytest.mark.asyncio
    async def test_client_clear_cache(self):
        """Test clearing the cache."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client = MockJudgeClient(config)

        # Make a call
        await client.judge("Test")

        # Clear cache
        client.clear_cache()

        stats = client.get_cache_stats()
        assert stats["size"] == 0

        del os.environ["OPENAI_API_KEY"]

    @pytest.mark.asyncio
    async def test_client_cache_stats(self):
        """Test getting cache statistics."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client = MockJudgeClient(config)

        # Make some calls
        await client.judge("Test 1")
        await client.judge("Test 2")

        stats = client.get_cache_stats()

        assert stats["size"] == 2
        assert len(stats["entries"]) == 2

        del os.environ["OPENAI_API_KEY"]

    @pytest.mark.asyncio
    async def test_client_different_prompts(self):
        """Test that different prompts are not cached together."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client = MockJudgeClient(config)

        await client.judge("Prompt 1")
        call_count_1 = client.call_count

        await client.judge("Prompt 2")
        call_count_2 = client.call_count

        # Should make a new call for different prompt
        assert call_count_2 > call_count_1

        del os.environ["OPENAI_API_KEY"]

    @pytest.mark.asyncio
    async def test_client_retry_logic(self):
        """Test that retry logic would work (using mock)."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(
            provider="openai", model="gpt-4o-mini", max_retries=3
        )
        client = MockJudgeClient(config)

        # Mock client should succeed on first try
        judgment = await client.judge("Test")

        assert judgment is not None

        del os.environ["OPENAI_API_KEY"]

    @pytest.mark.asyncio
    async def test_client_custom_system_prompt(self):
        """Test using custom system prompt."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client = MockJudgeClient(config)

        custom_system = "You are a strict evaluator."

        judgment = await client.judge("Test", system_prompt=custom_system)

        assert judgment is not None

        del os.environ["OPENAI_API_KEY"]


class TestJudgeClientConfig:
    """Tests for client configuration."""

    def test_client_initialization(self):
        """Test client initialization with config."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client = JudgeClient(config)

        assert client.config == config
        assert client.parser is not None

        del os.environ["OPENAI_API_KEY"]

    def test_client_with_different_providers(self):
        """Test client with different providers."""
        # OpenAI
        os.environ["OPENAI_API_KEY"] = "test-key"
        config_openai = JudgeConfig(provider="openai", model="gpt-4o-mini")
        client_openai = JudgeClient(config_openai)
        assert client_openai.config.provider == "openai"
        del os.environ["OPENAI_API_KEY"]

        # Anthropic
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        config_anthropic = JudgeConfig(
            provider="anthropic", model="claude-3-opus-20240229"
        )
        client_anthropic = JudgeClient(config_anthropic)
        assert client_anthropic.config.provider == "anthropic"
        del os.environ["ANTHROPIC_API_KEY"]

        # Together
        os.environ["TOGETHER_API_KEY"] = "test-key"
        config_together = JudgeConfig(provider="together", model="llama-2-70b")
        client_together = JudgeClient(config_together)
        assert client_together.config.provider == "together"
        del os.environ["TOGETHER_API_KEY"]
