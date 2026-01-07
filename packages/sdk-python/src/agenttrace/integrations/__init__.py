"""
Framework integrations for automatic instrumentation.

This module provides auto-instrumentation for popular AI frameworks,
enabling zero-code-change observability.
"""

from typing import Optional, Callable
import warnings


class FrameworkIntegration:
    """
    Base class for framework integrations.

    Subclasses implement framework-specific instrumentation logic.
    """

    def __init__(self, trace_client):
        """
        Initialize integration with trace client.

        Args:
            trace_client: AgentTrace client instance
        """
        self.trace_client = trace_client
        self._enabled = False
        self._original_methods = {}

    def enable(self) -> None:
        """Enable instrumentation by patching framework methods."""
        if self._enabled:
            return

        try:
            self._patch()
            self._enabled = True
        except ImportError as e:
            warnings.warn(
                f"Could not enable {self.__class__.__name__}: {e}. "
                f"Make sure the framework is installed.",
                UserWarning
            )
        except Exception as e:
            warnings.warn(
                f"Error enabling {self.__class__.__name__}: {e}",
                UserWarning
            )

    def disable(self) -> None:
        """Disable instrumentation by restoring original methods."""
        if not self._enabled:
            return

        self._unpatch()
        self._enabled = False

    def _patch(self) -> None:
        """
        Patch framework methods for instrumentation.

        Subclasses must implement this method.
        """
        raise NotImplementedError

    def _unpatch(self) -> None:
        """
        Restore original framework methods.

        Subclasses must implement this method.
        """
        raise NotImplementedError


class LangChainIntegration(FrameworkIntegration):
    """
    Auto-instrumentation for LangChain.

    Automatically traces:
    - LLM calls
    - Chain executions
    - Agent steps
    - Tool invocations
    - Retriever queries
    """

    def _patch(self) -> None:
        """Patch LangChain methods."""
        # Import LangChain
        try:
            from langchain.schema import BaseLanguageModel
            from langchain.chains.base import Chain
        except ImportError:
            raise ImportError(
                "LangChain is not installed. "
                "Install it with: pip install langchain"
            )

        # TODO: Implement LangChain patching
        # This would monkey-patch LangChain's core methods to add tracing
        warnings.warn(
            "LangChain instrumentation is not yet implemented. "
            "Use manual instrumentation with decorators for now.",
            UserWarning
        )

    def _unpatch(self) -> None:
        """Restore LangChain methods."""
        # TODO: Implement unpatching
        pass


class OpenAIIntegration(FrameworkIntegration):
    """
    Auto-instrumentation for OpenAI API.

    Automatically traces:
    - ChatCompletion calls
    - Completion calls
    - Embedding calls
    - All OpenAI API interactions
    """

    def _patch(self) -> None:
        """Patch OpenAI methods."""
        try:
            import openai
        except ImportError:
            raise ImportError(
                "OpenAI is not installed. "
                "Install it with: pip install openai"
            )

        # TODO: Implement OpenAI patching
        # This would wrap openai.ChatCompletion.create, etc.
        warnings.warn(
            "OpenAI instrumentation is not yet implemented. "
            "Use manual instrumentation with decorators for now.",
            UserWarning
        )

    def _unpatch(self) -> None:
        """Restore OpenAI methods."""
        # TODO: Implement unpatching
        pass


class CrewAIIntegration(FrameworkIntegration):
    """
    Auto-instrumentation for CrewAI.

    Automatically traces:
    - Agent executions
    - Task executions
    - Crew workflows
    - Tool invocations
    """

    def _patch(self) -> None:
        """Patch CrewAI methods."""
        try:
            from crewai import Agent, Task, Crew
        except ImportError:
            raise ImportError(
                "CrewAI is not installed. "
                "Install it with: pip install crewai"
            )

        # TODO: Implement CrewAI patching
        warnings.warn(
            "CrewAI instrumentation is not yet implemented. "
            "Use manual instrumentation with decorators for now.",
            UserWarning
        )

    def _unpatch(self) -> None:
        """Restore CrewAI methods."""
        # TODO: Implement unpatching
        pass


# Integration registry
_integrations = {}


def get_integration(name: str, trace_client) -> FrameworkIntegration:
    """
    Get or create a framework integration.

    Args:
        name: Integration name (langchain, openai, crewai)
        trace_client: AgentTrace client instance

    Returns:
        FrameworkIntegration: The integration instance
    """
    if name not in _integrations:
        if name == "langchain":
            _integrations[name] = LangChainIntegration(trace_client)
        elif name == "openai":
            _integrations[name] = OpenAIIntegration(trace_client)
        elif name == "crewai":
            _integrations[name] = CrewAIIntegration(trace_client)
        else:
            raise ValueError(f"Unknown integration: {name}")

    return _integrations[name]


__all__ = [
    "FrameworkIntegration",
    "LangChainIntegration",
    "OpenAIIntegration",
    "CrewAIIntegration",
    "get_integration",
]
