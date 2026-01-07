"""Unit tests for exporter module."""

import pytest
import json
from pathlib import Path
from agenttrace.exporter import (
    ConsoleExporter,
    FileExporter,
    HTTPExporter,
    CompositeExporter,
    create_exporter,
)
from agenttrace.config import AgentTraceConfig, ExportMode
from agenttrace.span import Span
from agenttrace.schema import SpanType


class TestConsoleExporter:
    """Tests for ConsoleExporter."""

    def test_console_exporter_creation(self):
        """Test creating console exporter."""
        exporter = ConsoleExporter(pretty=True, verbose=True)

        assert exporter.pretty is True
        assert exporter.verbose is True

    def test_console_exporter_export(self, capsys):
        """Test exporting to console."""
        exporter = ConsoleExporter(pretty=False, verbose=False)
        span = Span(trace_id="trace-123", name="test-span")
        span.end()

        result = exporter.export([span])

        assert result is True

        # Check console output
        captured = capsys.readouterr()
        assert "test-span" in captured.out
        assert "trace-123" in captured.out

    def test_console_exporter_shutdown(self):
        """Test shutting down console exporter."""
        exporter = ConsoleExporter()
        exporter.shutdown()  # Should not raise


class TestFileExporter:
    """Tests for FileExporter."""

    def test_file_exporter_creation(self, tmp_path):
        """Test creating file exporter."""
        exporter = FileExporter(directory=str(tmp_path))

        assert exporter.directory == tmp_path
        assert exporter.directory.exists()

    def test_file_exporter_export_by_date(self, tmp_path):
        """Test exporting to file organized by date."""
        exporter = FileExporter(
            directory=str(tmp_path),
            organize_by="date",
        )

        span = Span(trace_id="trace-123", name="test-span")
        span.end()

        result = exporter.export([span])

        assert result is True

        # Check file was created
        files = list(tmp_path.rglob("*.json"))
        assert len(files) > 0

    def test_file_exporter_export_by_trace(self, tmp_path):
        """Test exporting to file organized by trace."""
        exporter = FileExporter(
            directory=str(tmp_path),
            organize_by="trace",
        )

        span1 = Span(trace_id="trace-123", name="span1")
        span2 = Span(trace_id="trace-123", name="span2")
        span1.end()
        span2.end()

        result = exporter.export([span1, span2])

        assert result is True

        # Check trace file was created
        trace_file = tmp_path / "trace-123" / "trace.json"
        assert trace_file.exists()

        # Verify content
        with open(trace_file) as f:
            data = json.load(f)
            assert data["trace_id"] == "trace-123"
            assert len(data["spans"]) == 2

    def test_file_exporter_shutdown(self, tmp_path):
        """Test shutting down file exporter."""
        exporter = FileExporter(directory=str(tmp_path))
        exporter.shutdown()  # Should not raise


class TestHTTPExporter:
    """Tests for HTTPExporter."""

    def test_http_exporter_creation(self):
        """Test creating HTTP exporter."""
        config = AgentTraceConfig(
            api_key="test-key",
            project_id="test-project",
        )
        exporter = HTTPExporter(config)

        assert exporter.config == config

    def test_http_exporter_disabled_when_no_api_key(self):
        """Test HTTP exporter when API key is missing."""
        config = AgentTraceConfig(
            api_key="",
            project_id="test-project",
        )
        exporter = HTTPExporter(config)

        span = Span(trace_id="trace-123", name="test")
        span.end()

        result = exporter.export([span])

        assert result is False

    def test_http_exporter_disabled_config(self):
        """Test HTTP exporter when config is disabled."""
        config = AgentTraceConfig(
            api_key="test-key",
            project_id="test-project",
            enabled=False,
        )
        exporter = HTTPExporter(config)

        span = Span(trace_id="trace-123", name="test")
        span.end()

        result = exporter.export([span])

        assert result is True  # Returns True but doesn't actually export

    def test_http_exporter_shutdown(self):
        """Test shutting down HTTP exporter."""
        config = AgentTraceConfig(
            api_key="test-key",
            project_id="test-project",
        )
        exporter = HTTPExporter(config)
        exporter.shutdown()  # Should close client


class TestCompositeExporter:
    """Tests for CompositeExporter."""

    def test_composite_exporter_creation(self):
        """Test creating composite exporter."""
        console = ConsoleExporter()
        exporter = CompositeExporter([console])

        assert len(exporter.exporters) == 1

    def test_composite_exporter_export(self, tmp_path, capsys):
        """Test exporting with composite exporter."""
        console = ConsoleExporter(verbose=False)
        file_exp = FileExporter(directory=str(tmp_path), organize_by="date")
        exporter = CompositeExporter([console, file_exp])

        span = Span(trace_id="trace-123", name="test")
        span.end()

        result = exporter.export([span])

        assert result is True

        # Check console output
        captured = capsys.readouterr()
        assert "test" in captured.out

        # Check file was created
        files = list(tmp_path.rglob("*.json"))
        assert len(files) > 0

    def test_composite_exporter_shutdown(self):
        """Test shutting down composite exporter."""
        console = ConsoleExporter()
        exporter = CompositeExporter([console])

        exporter.shutdown()  # Should not raise


class TestCreateExporter:
    """Tests for create_exporter helper function."""

    def test_create_exporter_default(self):
        """Test creating exporter with default config."""
        config = AgentTraceConfig(
            api_key="test-key",
            project_id="test-project",
        )

        exporter = create_exporter(config)

        assert exporter is not None
        assert isinstance(exporter, HTTPExporter)

    def test_create_exporter_console(self):
        """Test creating exporter with console enabled."""
        config = AgentTraceConfig(
            api_key="test-key",
            project_id="test-project",
            console_export=True,
        )

        exporter = create_exporter(config)

        assert isinstance(exporter, CompositeExporter)

    def test_create_exporter_file(self, tmp_path):
        """Test creating exporter with file enabled."""
        config = AgentTraceConfig(
            api_key="test-key",
            project_id="test-project",
            file_export=True,
            file_export_path=str(tmp_path),
        )

        exporter = create_exporter(config)

        assert isinstance(exporter, CompositeExporter)

    def test_create_exporter_no_api_key(self):
        """Test creating exporter without API key."""
        config = AgentTraceConfig(
            api_key="",
            project_id="test-project",
        )

        exporter = create_exporter(config)

        # Should return console exporter as fallback
        assert isinstance(exporter, ConsoleExporter)
