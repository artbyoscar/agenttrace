"""
Span export interfaces for AgentTrace SDK.

Provides abstract base class and concrete implementations for exporting
spans to various destinations (console, file, HTTP, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime
from pathlib import Path
import httpx

from .schema import Span as SchemaSpan
from .config import AgentTraceConfig


class SpanExporter(ABC):
    """
    Abstract base class for span exporters.

    Exporters are responsible for sending spans to their destination,
    whether that's console, file, HTTP endpoint, or other storage.

    Subclasses must implement the export() and shutdown() methods.
    """

    @abstractmethod
    def export(self, spans: List[SchemaSpan]) -> bool:
        """
        Export a batch of spans.

        Args:
            spans: List of spans to export

        Returns:
            bool: True if export succeeded, False otherwise
        """
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """
        Shutdown the exporter and cleanup resources.

        This method should be called when the exporter is no longer needed.
        """
        pass

    def force_flush(self) -> bool:
        """
        Force flush any pending spans.

        Default implementation does nothing. Override if needed.

        Returns:
            bool: True if flush succeeded
        """
        return True


class ConsoleExporter(SpanExporter):
    """
    Console exporter for development and debugging.

    Prints spans to console in a human-readable format with optional
    JSON output for detailed inspection.

    Example:
        >>> exporter = ConsoleExporter(pretty=True, verbose=True)
        >>> exporter.export([span])
    """

    def __init__(
        self,
        pretty: bool = True,
        verbose: bool = False,
        include_input_output: bool = True,
    ):
        """
        Initialize console exporter.

        Args:
            pretty: Pretty print JSON output
            verbose: Include all span details
            include_input_output: Include input/output in console output
        """
        self.pretty = pretty
        self.verbose = verbose
        self.include_input_output = include_input_output

    def export(self, spans: List[SchemaSpan]) -> bool:
        """
        Export spans to console.

        Args:
            spans: List of spans to export

        Returns:
            bool: Always returns True
        """
        for span in spans:
            self._print_span(span)
        return True

    def _print_span(self, span: SchemaSpan) -> None:
        """Print a single span to console."""
        span_dict = span.to_dict()

        if self.verbose:
            # Print full JSON
            if self.pretty:
                print(json.dumps(span_dict, indent=2, default=str))
            else:
                print(json.dumps(span_dict, default=str))
        else:
            # Print summary
            duration_ms = span.duration * 1000 if span.duration else 0
            status_symbol = "✓" if span.status.value == "ok" else "✗" if span.status.value == "error" else "○"

            print(f"{status_symbol} [{span.span_type.value}] {span.name}")
            print(f"  Trace ID: {span.trace_id}")
            print(f"  Span ID:  {span.span_id}")
            if span.parent_span_id:
                print(f"  Parent:   {span.parent_span_id}")
            print(f"  Duration: {duration_ms:.2f}ms")
            print(f"  Status:   {span.status.value}")

            if self.include_input_output:
                if span.input:
                    print(f"  Input:    {self._truncate(str(span.input), 100)}")
                if span.output:
                    print(f"  Output:   {self._truncate(str(span.output), 100)}")

            if span.llm:
                print(f"  Model:    {span.llm.model}")
                if span.llm.usage:
                    print(f"  Tokens:   {span.llm.usage.total_tokens}")

            if span.error:
                print(f"  Error:    {span.error['type']}: {span.error['message']}")

            print()

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def shutdown(self) -> None:
        """Shutdown console exporter (no-op)."""
        pass


class FileExporter(SpanExporter):
    """
    File exporter for local storage.

    Writes spans to JSON files organized by date or trace ID.
    Useful for local development and testing.

    Example:
        >>> exporter = FileExporter(
        ...     directory="./traces",
        ...     organize_by="date"
        ... )
        >>> exporter.export([span])
    """

    def __init__(
        self,
        directory: str = "./traces",
        organize_by: str = "date",  # "date" or "trace"
        file_extension: str = ".json",
        pretty: bool = True,
    ):
        """
        Initialize file exporter.

        Args:
            directory: Directory to write trace files
            organize_by: How to organize files ("date" or "trace")
            file_extension: File extension to use
            pretty: Pretty print JSON
        """
        self.directory = Path(directory)
        self.organize_by = organize_by
        self.file_extension = file_extension
        self.pretty = pretty

        # Create directory if it doesn't exist
        self.directory.mkdir(parents=True, exist_ok=True)

    def export(self, spans: List[SchemaSpan]) -> bool:
        """
        Export spans to file.

        Args:
            spans: List of spans to export

        Returns:
            bool: True if export succeeded
        """
        try:
            if self.organize_by == "date":
                self._export_by_date(spans)
            elif self.organize_by == "trace":
                self._export_by_trace(spans)
            else:
                raise ValueError(f"Invalid organize_by: {self.organize_by}")

            return True
        except Exception as e:
            print(f"Error exporting to file: {e}")
            return False

    def _export_by_date(self, spans: List[SchemaSpan]) -> None:
        """Export spans organized by date."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        date_dir = self.directory / today
        date_dir.mkdir(parents=True, exist_ok=True)

        for span in spans:
            filename = f"{span.span_id}{self.file_extension}"
            filepath = date_dir / filename
            self._write_span(filepath, span)

    def _export_by_trace(self, spans: List[SchemaSpan]) -> None:
        """Export spans organized by trace ID."""
        # Group spans by trace_id
        traces: Dict[str, List[SchemaSpan]] = {}
        for span in spans:
            if span.trace_id not in traces:
                traces[span.trace_id] = []
            traces[span.trace_id].append(span)

        # Write each trace to a file
        for trace_id, trace_spans in traces.items():
            trace_dir = self.directory / trace_id
            trace_dir.mkdir(parents=True, exist_ok=True)

            # Write trace file with all spans
            filename = f"trace{self.file_extension}"
            filepath = trace_dir / filename

            trace_data = {
                "trace_id": trace_id,
                "spans": [span.to_dict() for span in trace_spans],
            }

            with open(filepath, "w") as f:
                if self.pretty:
                    json.dump(trace_data, f, indent=2, default=str)
                else:
                    json.dump(trace_data, f, default=str)

    def _write_span(self, filepath: Path, span: SchemaSpan) -> None:
        """Write a single span to file."""
        with open(filepath, "w") as f:
            if self.pretty:
                json.dump(span.to_dict(), f, indent=2, default=str)
            else:
                json.dump(span.to_dict(), f, default=str)

    def shutdown(self) -> None:
        """Shutdown file exporter (no-op)."""
        pass


class HTTPExporter(SpanExporter):
    """
    HTTP exporter for remote ingestion.

    Sends spans to the AgentTrace API endpoint via HTTP POST.
    Supports retries and error handling.

    Example:
        >>> config = AgentTraceConfig(
        ...     api_key="my-key",
        ...     project_id="my-project"
        ... )
        >>> exporter = HTTPExporter(config)
        >>> exporter.export([span])
    """

    def __init__(self, config: AgentTraceConfig):
        """
        Initialize HTTP exporter.

        Args:
            config: AgentTrace configuration
        """
        self.config = config
        self.client = httpx.Client(
            base_url=config.api_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            timeout=config.timeout,
        )

    def export(self, spans: List[SchemaSpan]) -> bool:
        """
        Export spans via HTTP.

        Args:
            spans: List of spans to export

        Returns:
            bool: True if export succeeded
        """
        if not self.config.enabled:
            return True

        if not self.config.api_key:
            print("Warning: API key not set, skipping HTTP export")
            return False

        try:
            # Convert spans to dict format
            spans_data = [span.to_dict() for span in spans]

            # Send to API
            response = self.client.post(
                "/api/v1/traces",
                json={
                    "project_id": self.config.project_id,
                    "environment": self.config.environment,
                    "spans": spans_data,
                },
            )

            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            print(f"HTTP error exporting spans: {e.response.status_code} - {e.response.text}")
            return False
        except httpx.RequestError as e:
            print(f"Network error exporting spans: {e}")
            return False
        except Exception as e:
            print(f"Error exporting spans: {e}")
            return False

    def shutdown(self) -> None:
        """Shutdown HTTP exporter and close client."""
        self.client.close()


class CompositeExporter(SpanExporter):
    """
    Composite exporter that exports to multiple destinations.

    Useful for exporting to both console and HTTP, or file and HTTP.

    Example:
        >>> exporter = CompositeExporter([
        ...     ConsoleExporter(),
        ...     HTTPExporter(config)
        ... ])
        >>> exporter.export([span])
    """

    def __init__(self, exporters: List[SpanExporter]):
        """
        Initialize composite exporter.

        Args:
            exporters: List of exporters to use
        """
        self.exporters = exporters

    def export(self, spans: List[SchemaSpan]) -> bool:
        """
        Export spans to all exporters.

        Args:
            spans: List of spans to export

        Returns:
            bool: True if all exports succeeded
        """
        results = []
        for exporter in self.exporters:
            try:
                result = exporter.export(spans)
                results.append(result)
            except Exception as e:
                print(f"Error in exporter {exporter.__class__.__name__}: {e}")
                results.append(False)

        return all(results)

    def force_flush(self) -> bool:
        """Force flush all exporters."""
        results = []
        for exporter in self.exporters:
            try:
                result = exporter.force_flush()
                results.append(result)
            except Exception as e:
                print(f"Error flushing exporter {exporter.__class__.__name__}: {e}")
                results.append(False)

        return all(results)

    def shutdown(self) -> None:
        """Shutdown all exporters."""
        for exporter in self.exporters:
            try:
                exporter.shutdown()
            except Exception as e:
                print(f"Error shutting down exporter {exporter.__class__.__name__}: {e}")


def create_exporter(config: AgentTraceConfig) -> SpanExporter:
    """
    Create an exporter based on configuration.

    Automatically creates the appropriate exporter(s) based on config settings.
    Can create a composite exporter if multiple export destinations are enabled.

    Args:
        config: AgentTrace configuration

    Returns:
        SpanExporter: Configured exporter

    Example:
        >>> config = AgentTraceConfig.from_env()
        >>> exporter = create_exporter(config)
    """
    exporters: List[SpanExporter] = []

    # Add console exporter if enabled
    if config.console_export:
        exporters.append(ConsoleExporter(pretty=True, verbose=False))

    # Add file exporter if enabled
    if config.file_export:
        exporters.append(
            FileExporter(
                directory=config.file_export_path,
                organize_by="trace",
                pretty=True,
            )
        )

    # Add HTTP exporter (primary export destination)
    if config.enabled and config.api_key:
        exporters.append(HTTPExporter(config))

    # Return composite if multiple exporters, otherwise return single exporter
    if len(exporters) == 0:
        # No exporters configured, use console as fallback
        return ConsoleExporter()
    elif len(exporters) == 1:
        return exporters[0]
    else:
        return CompositeExporter(exporters)
