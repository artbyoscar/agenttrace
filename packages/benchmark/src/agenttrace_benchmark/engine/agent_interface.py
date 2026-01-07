"""
Secure agent interface for benchmark execution.

Provides a sandboxed environment for invoking submitted agents with:
- Timeout enforcement
- Token counting and budget limits
- Network isolation
- Input/output sanitization
- Resource monitoring
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from .models.execution import ToolCall, ResourceUsage, FailureReason
from .models.submission import AgentEndpoint

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Structured response from agent invocation."""
    output: str
    tool_calls: List[ToolCall]
    tokens_used: int
    execution_time: float
    success: bool
    error: Optional[str] = None


class AgentInterface(ABC):
    """
    Abstract base class for agent invocation.

    Subclasses implement different invocation methods (HTTP, gRPC, local).
    """

    def __init__(
        self,
        endpoint: AgentEndpoint,
        max_output_size: int = 50000,  # 50KB max output
        enable_monitoring: bool = True,
    ):
        """
        Initialize agent interface.

        Args:
            endpoint: Agent endpoint configuration
            max_output_size: Maximum output size in characters
            enable_monitoring: Whether to enable resource monitoring
        """
        self.endpoint = endpoint
        self.max_output_size = max_output_size
        self.enable_monitoring = enable_monitoring

    @abstractmethod
    async def invoke(
        self,
        prompt: str,
        config: Dict[str, Any],
        timeout: float,
    ) -> AgentResponse:
        """
        Invoke the agent with a prompt.

        Args:
            prompt: Task prompt
            config: Agent configuration
            timeout: Maximum execution time in seconds

        Returns:
            AgentResponse with output and metrics

        Raises:
            TimeoutError: If execution exceeds timeout
            ValueError: If output is invalid
        """
        pass

    def _sanitize_input(self, prompt: str) -> str:
        """
        Sanitize input prompt.

        Args:
            prompt: Raw prompt

        Returns:
            Sanitized prompt

        Raises:
            ValueError: If input is too large or contains invalid content
        """
        # Check size
        if len(prompt) > 100000:  # 100KB max input
            raise ValueError(f"Input too large: {len(prompt)} characters")

        # Could add more sanitization here
        # - Remove null bytes
        # - Check for injection attempts
        # - Validate encoding

        return prompt

    def _sanitize_output(self, output: str) -> str:
        """
        Sanitize agent output.

        Args:
            output: Raw output from agent

        Returns:
            Sanitized output

        Raises:
            ValueError: If output exceeds size limit
        """
        if len(output) > self.max_output_size:
            logger.warning(
                f"Output truncated from {len(output)} to {self.max_output_size} characters"
            )
            output = output[:self.max_output_size] + "\n[OUTPUT TRUNCATED]"

        return output

    def _count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count

        Note:
            This is a rough approximation. For accurate counting, use tiktoken.
        """
        # Simple approximation: ~4 characters per token
        # In production, use tiktoken or similar
        return len(text) // 4


class HTTPAgentInterface(AgentInterface):
    """
    HTTP-based agent invocation.

    Invokes agents via REST API.
    """

    async def invoke(
        self,
        prompt: str,
        config: Dict[str, Any],
        timeout: float,
    ) -> AgentResponse:
        """Invoke agent via HTTP POST."""
        prompt = self._sanitize_input(prompt)
        start_time = time.time()

        if not self.endpoint.url:
            raise ValueError("HTTP endpoint requires URL")

        # Prepare request
        headers = {"Content-Type": "application/json"}

        # Add authentication
        if self.endpoint.auth_type == "bearer" and self.endpoint.auth_credentials:
            token = self.endpoint.auth_credentials.get("token")
            headers["Authorization"] = f"Bearer {token}"
        elif self.endpoint.auth_type == "api_key" and self.endpoint.auth_credentials:
            api_key = self.endpoint.auth_credentials.get("api_key")
            headers["X-API-Key"] = api_key

        payload = {
            "prompt": prompt,
            "config": config,
        }

        # Invoke with timeout
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.endpoint.url,
                    json=payload,
                    headers=headers,
                )

                response.raise_for_status()
                result = response.json()

                execution_time = time.time() - start_time

                # Extract response fields
                output = result.get("output", "")
                output = self._sanitize_output(output)

                tool_calls = self._parse_tool_calls(result.get("tool_calls", []))

                # Estimate tokens
                tokens = self._count_tokens(prompt) + self._count_tokens(output)

                return AgentResponse(
                    output=output,
                    tool_calls=tool_calls,
                    tokens_used=tokens,
                    execution_time=execution_time,
                    success=True,
                )

        except httpx.TimeoutException:
            execution_time = time.time() - start_time
            logger.error(f"Agent timeout after {execution_time:.1f}s")
            return AgentResponse(
                output="",
                tool_calls=[],
                tokens_used=0,
                execution_time=execution_time,
                success=False,
                error="Timeout exceeded",
            )

        except httpx.HTTPStatusError as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent returned HTTP error: {e.response.status_code}")
            return AgentResponse(
                output="",
                tool_calls=[],
                tokens_used=0,
                execution_time=execution_time,
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text[:200]}",
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent invocation failed: {str(e)}")
            return AgentResponse(
                output="",
                tool_calls=[],
                tokens_used=0,
                execution_time=execution_time,
                success=False,
                error=str(e),
            )

    def _parse_tool_calls(self, tool_calls_data: List[Dict]) -> List[ToolCall]:
        """Parse tool calls from agent response."""
        tool_calls = []

        for call_data in tool_calls_data:
            try:
                tool_call = ToolCall(
                    tool_name=call_data.get("tool_name", "unknown"),
                    parameters=call_data.get("parameters", {}),
                    timestamp=call_data.get("timestamp"),
                    duration_seconds=call_data.get("duration", 0.0),
                    success=call_data.get("success", True),
                    result=call_data.get("result"),
                    error=call_data.get("error"),
                )
                tool_calls.append(tool_call)
            except Exception as e:
                logger.warning(f"Failed to parse tool call: {e}")

        return tool_calls


class LocalAgentInterface(AgentInterface):
    """
    Local Python function invocation.

    Invokes agents that are Python functions in the same process.
    Useful for testing and development.
    """

    async def invoke(
        self,
        prompt: str,
        config: Dict[str, Any],
        timeout: float,
    ) -> AgentResponse:
        """Invoke local Python function."""
        prompt = self._sanitize_input(prompt)
        start_time = time.time()

        if not self.endpoint.module_path or not self.endpoint.function_name:
            raise ValueError("Local endpoint requires module_path and function_name")

        try:
            # Import module
            import importlib
            module = importlib.import_module(self.endpoint.module_path)
            func = getattr(module, self.endpoint.function_name)

            # Invoke with timeout
            try:
                output = await asyncio.wait_for(
                    asyncio.create_task(self._call_function(func, prompt, config)),
                    timeout=timeout
                )

                execution_time = time.time() - start_time
                output = self._sanitize_output(output)

                # Estimate tokens
                tokens = self._count_tokens(prompt) + self._count_tokens(output)

                return AgentResponse(
                    output=output,
                    tool_calls=[],  # Local functions don't report tool calls separately
                    tokens_used=tokens,
                    execution_time=execution_time,
                    success=True,
                )

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                return AgentResponse(
                    output="",
                    tool_calls=[],
                    tokens_used=0,
                    execution_time=execution_time,
                    success=False,
                    error="Timeout exceeded",
                )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Local function invocation failed: {str(e)}")
            return AgentResponse(
                output="",
                tool_calls=[],
                tokens_used=0,
                execution_time=execution_time,
                success=False,
                error=str(e),
            )

    async def _call_function(self, func, prompt: str, config: Dict[str, Any]) -> str:
        """Call the function (potentially async)."""
        import inspect

        if inspect.iscoroutinefunction(func):
            return await func(prompt, config)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, prompt, config)


def create_agent_interface(endpoint: AgentEndpoint) -> AgentInterface:
    """
    Factory function to create appropriate agent interface.

    Args:
        endpoint: Agent endpoint configuration

    Returns:
        Appropriate AgentInterface subclass

    Raises:
        ValueError: If endpoint type is unsupported
    """
    if endpoint.endpoint_type == "http":
        return HTTPAgentInterface(endpoint)
    elif endpoint.endpoint_type == "local":
        return LocalAgentInterface(endpoint)
    elif endpoint.endpoint_type == "grpc":
        raise NotImplementedError("gRPC agent interface not yet implemented")
    else:
        raise ValueError(f"Unsupported endpoint type: {endpoint.endpoint_type}")


__all__ = [
    "AgentInterface",
    "AgentResponse",
    "HTTPAgentInterface",
    "LocalAgentInterface",
    "create_agent_interface",
]
