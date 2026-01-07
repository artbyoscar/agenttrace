"""LLM judge client with multi-provider support."""

import asyncio
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .config import JudgeConfig
from .parser import Judgment, JudgmentParser
from .costs import TokenUsage, get_global_tracker
from .prompts import SYSTEM_PROMPT


class JudgeClient:
    """Async LLM client for judgment operations.

    Supports multiple providers with retry logic, rate limiting, and caching.

    Example:
        >>> from agenttrace.evals.judge import JudgeClient, JudgeConfig
        >>> config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        >>> client = JudgeClient(config)
        >>> judgment = await client.judge("Evaluate this response...")
    """

    def __init__(self, config: JudgeConfig):
        """Initialize the judge client.

        Args:
            config: Judge configuration
        """
        self.config = config
        self.parser = JudgmentParser()
        self._cache: Dict[str, Judgment] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._provider_client = None
        self._semaphore = asyncio.Semaphore(10)  # Rate limiting

    async def judge(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_cache: Optional[bool] = None,
    ) -> Judgment:
        """Execute a judgment request.

        Args:
            prompt: The evaluation prompt
            system_prompt: Optional custom system prompt
            use_cache: Whether to use caching (defaults to config setting)

        Returns:
            Judgment object with score and reasoning

        Raises:
            Exception: If all retries fail

        Example:
            >>> judgment = await client.judge("Evaluate: {output}")
            >>> print(f"Score: {judgment.score}")
        """
        # Determine if caching should be used
        use_cache = use_cache if use_cache is not None else self.config.cache_judgments

        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(prompt, system_prompt)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached

        # Execute with retries
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                async with self._semaphore:  # Rate limiting
                    judgment = await self._execute_judgment(prompt, system_prompt)

                    # Cache the result
                    if use_cache:
                        self._add_to_cache(cache_key, judgment)

                    return judgment

            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                continue

        # All retries failed
        raise Exception(
            f"Judge request failed after {self.config.max_retries} attempts: {last_exception}"
        )

    async def _execute_judgment(
        self, prompt: str, system_prompt: Optional[str]
    ) -> Judgment:
        """Execute a single judgment request.

        Args:
            prompt: Evaluation prompt
            system_prompt: Optional system prompt

        Returns:
            Judgment object

        Raises:
            Exception: If request fails
        """
        # Use provided system prompt or default
        sys_prompt = system_prompt or SYSTEM_PROMPT

        # Call the appropriate provider
        if self.config.provider == "openai":
            response, usage = await self._call_openai(prompt, sys_prompt)
        elif self.config.provider == "anthropic":
            response, usage = await self._call_anthropic(prompt, sys_prompt)
        elif self.config.provider == "together":
            response, usage = await self._call_together(prompt, sys_prompt)
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

        # Parse the response
        judgment = self.parser.parse(response)

        # Track costs
        if usage:
            tracker = get_global_tracker()
            tracker.record_judgment(self.config.model, usage)

        return judgment

    async def _call_openai(self, prompt: str, system_prompt: str) -> tuple:
        """Call OpenAI API.

        Args:
            prompt: User prompt
            system_prompt: System prompt

        Returns:
            Tuple of (response_text, TokenUsage)

        Raises:
            Exception: If API call fails
        """
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai package required for OpenAI provider. "
                "Install with: pip install openai"
            )

        # Initialize client
        client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
        )

        # Make request
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            response_format={"type": "json_object"},
        )

        # Extract response and usage
        content = response.choices[0].message.content
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )

        return content, usage

    async def _call_anthropic(self, prompt: str, system_prompt: str) -> tuple:
        """Call Anthropic API.

        Args:
            prompt: User prompt
            system_prompt: System prompt

        Returns:
            Tuple of (response_text, TokenUsage)

        Raises:
            Exception: If API call fails
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package required for Anthropic provider. "
                "Install with: pip install anthropic"
            )

        # Initialize client
        client = anthropic.AsyncAnthropic(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout_seconds,
        )

        # Make request
        response = await client.messages.create(
            model=self.config.model,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Extract response and usage
        content = response.content[0].text
        usage = TokenUsage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
        )

        return content, usage

    async def _call_together(self, prompt: str, system_prompt: str) -> tuple:
        """Call Together.ai API.

        Args:
            prompt: User prompt
            system_prompt: System prompt

        Returns:
            Tuple of (response_text, TokenUsage)

        Raises:
            Exception: If API call fails
        """
        try:
            import together
        except ImportError:
            raise ImportError(
                "together package required for Together provider. "
                "Install with: pip install together"
            )

        # Initialize client
        together.api_key = self.config.api_key
        if self.config.base_url:
            together.api_base = self.config.base_url

        # Make request (Together uses OpenAI-compatible API)
        response = await together.Complete.acreate(
            model=self.config.model,
            prompt=f"{system_prompt}\n\n{prompt}",
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Extract response and usage
        content = response.choices[0].text
        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens or 0,
            completion_tokens=response.usage.completion_tokens or 0,
        )

        return content, usage

    def _get_cache_key(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Generate cache key from prompt.

        Args:
            prompt: User prompt
            system_prompt: System prompt

        Returns:
            Cache key string
        """
        # Include model and prompts in key
        content = f"{self.config.model}:{system_prompt}:{prompt}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Judgment]:
        """Get judgment from cache if available and not expired.

        Args:
            cache_key: Cache key

        Returns:
            Cached judgment or None

        """
        if cache_key not in self._cache:
            return None

        # Check if cache entry is still valid (1 hour TTL)
        timestamp = self._cache_timestamps.get(cache_key)
        if timestamp and datetime.utcnow() - timestamp > timedelta(hours=1):
            # Expired, remove from cache
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None

        return self._cache[cache_key]

    def _add_to_cache(self, cache_key: str, judgment: Judgment):
        """Add judgment to cache.

        Args:
            cache_key: Cache key
            judgment: Judgment to cache
        """
        self._cache[cache_key] = judgment
        self._cache_timestamps[cache_key] = datetime.utcnow()

    def clear_cache(self):
        """Clear the judgment cache."""
        self._cache.clear()
        self._cache_timestamps.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            "size": len(self._cache),
            "entries": list(self._cache.keys()),
        }


class MockJudgeClient(JudgeClient):
    """Mock judge client for testing.

    Returns deterministic responses without calling real APIs.

    Example:
        >>> from agenttrace.evals.judge import MockJudgeClient, JudgeConfig
        >>> config = JudgeConfig(provider="openai", model="gpt-4o-mini")
        >>> client = MockJudgeClient(config, default_score=0.8)
        >>> judgment = await client.judge("Test prompt")
        >>> judgment.score
        0.8
    """

    def __init__(
        self,
        config: JudgeConfig,
        default_score: float = 0.8,
        default_reasoning: str = "Mock evaluation result",
    ):
        """Initialize mock client.

        Args:
            config: Judge configuration
            default_score: Default score to return (0.0-1.0)
            default_reasoning: Default reasoning text
        """
        super().__init__(config)
        self.default_score = default_score
        self.default_reasoning = default_reasoning
        self.call_count = 0

    async def _execute_judgment(
        self, prompt: str, system_prompt: Optional[str]
    ) -> Judgment:
        """Return a mock judgment.

        Args:
            prompt: Prompt (ignored)
            system_prompt: System prompt (ignored)

        Returns:
            Mock Judgment
        """
        self.call_count += 1

        # Create mock usage
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50)

        # Track costs
        tracker = get_global_tracker()
        tracker.record_judgment(self.config.model, usage)

        # Return deterministic judgment
        return Judgment(
            score=self.default_score,
            reasoning=self.default_reasoning,
            raw_score=self.default_score * 10,
            raw_response=json.dumps(
                {"score": self.default_score * 10, "reasoning": self.default_reasoning}
            ),
        )
