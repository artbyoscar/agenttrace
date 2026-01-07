"""Main client for AgentTrace SDK"""

import os
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import functools

from .config import Config
from .tracer import Tracer, Span
from .http_client import HTTPClient


class AgentTrace:
    """Main AgentTrace client for tracing AI agents"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project: Optional[str] = None,
        api_url: Optional[str] = None,
        environment: str = "development",
        tags: Optional[List[str]] = None,
        enabled: bool = True,
    ):
        """
        Initialize AgentTrace client

        Args:
            api_key: API key for authentication
            project: Project identifier
            api_url: API endpoint URL
            environment: Environment name (development, staging, production)
            tags: Default tags for all traces
            enabled: Whether tracing is enabled
        """
        self.config = Config(
            api_key=api_key or os.getenv("AGENTTRACE_API_KEY", ""),
            project=project or os.getenv("AGENTTRACE_PROJECT", "default"),
            api_url=api_url or os.getenv("AGENTTRACE_API_URL", "http://localhost:8000"),
            environment=environment,
            tags=tags or [],
            enabled=enabled,
        )
        self.http_client = HTTPClient(self.config)
        self.tracer = Tracer(self.http_client, self.config)

    def trace_agent(
        self,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Decorator to trace agent functions

        Args:
            name: Custom name for the trace
            metadata: Additional metadata
            tags: Tags for this trace

        Example:
            @trace.trace_agent(name="my-agent", tags=["production"])
            def my_agent():
                return "result"
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                trace_name = name or func.__name__
                with self.start_trace(trace_name, metadata=metadata, tags=tags):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    @contextmanager
    def start_trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Context manager to start a trace

        Args:
            name: Trace name
            metadata: Additional metadata
            tags: Tags for this trace

        Example:
            with trace.start_trace("my-trace") as span:
                span.log("Processing...")
                result = process()
        """
        span = self.tracer.start_span(name, metadata=metadata, tags=tags)
        try:
            yield span
        except Exception as e:
            span.record_error(e)
            raise
        finally:
            span.end()

    def flush(self):
        """Flush all pending traces"""
        self.tracer.flush()
