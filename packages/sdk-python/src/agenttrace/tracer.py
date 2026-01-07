"""Tracer implementation for AgentTrace"""

import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime


class Span:
    """Represents a single trace span"""

    def __init__(
        self,
        trace_id: str,
        span_id: str,
        name: str,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ):
        self.trace_id = trace_id
        self.span_id = span_id
        self.name = name
        self.parent_id = parent_id
        self.metadata = metadata or {}
        self.tags = tags or []
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = "running"
        self.logs: List[Dict[str, Any]] = []
        self.error: Optional[Dict[str, Any]] = None

    def log(self, message: str, level: str = "info", **kwargs):
        """Add a log entry to the span"""
        self.logs.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "level": level,
                **kwargs,
            }
        )

    def set_metadata(self, key: str, value: Any):
        """Set metadata on the span"""
        self.metadata[key] = value

    def add_tag(self, tag: str):
        """Add a tag to the span"""
        if tag not in self.tags:
            self.tags.append(tag)

    def record_error(self, error: Exception):
        """Record an error on the span"""
        self.status = "error"
        self.error = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": "",  # TODO: Add traceback
        }

    def end(self):
        """End the span"""
        self.end_time = time.time()
        if self.status == "running":
            self.status = "completed"

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "parent_id": self.parent_id,
            "metadata": self.metadata,
            "tags": self.tags,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time if self.end_time else None,
            "status": self.status,
            "logs": self.logs,
            "error": self.error,
        }


class Tracer:
    """Main tracer class for creating and managing spans"""

    def __init__(self, http_client, config):
        self.http_client = http_client
        self.config = config
        self.active_spans: Dict[str, Span] = {}

    def start_span(
        self,
        name: str,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Span:
        """Start a new span"""
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        all_tags = list(self.config.tags)
        if tags:
            all_tags.extend(tags)

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            parent_id=parent_id,
            metadata=metadata,
            tags=all_tags,
        )

        self.active_spans[span_id] = span
        return span

    def end_span(self, span: Span):
        """End a span and send it to the API"""
        span.end()
        if self.config.enabled:
            self.http_client.send_trace(span.to_dict())
        if span.span_id in self.active_spans:
            del self.active_spans[span.span_id]

    def flush(self):
        """Flush all active spans"""
        for span in list(self.active_spans.values()):
            self.end_span(span)
