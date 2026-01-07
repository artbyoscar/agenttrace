"""Unit tests for tool usage evaluators."""

import pytest
from agenttrace.evals.base import Trace
from agenttrace.evals.evaluators.tools import (
    ToolCallAccuracyEvaluator,
    ToolSelectionEvaluator,
)
from agenttrace.evals.evaluators._llm_judge import JudgeConfig


@pytest.fixture
def trace_with_tools():
    """Create a trace with successful tool calls."""
    return Trace(
        trace_id="test-trace-tools",
        spans=[
            {
                "span_id": "1",
                "name": "agent_run",
                "parent_id": None,
                "metadata": {
                    "input": "Search for Python tutorials",
                    "output": "Here are some Python tutorials...",
                },
            },
            {
                "span_id": "2",
                "name": "tool_call",
                "parent_id": "1",
                "status": "completed",
                "metadata": {"tool_name": "web_search", "input": "Python tutorials"},
            },
            {
                "span_id": "3",
                "name": "tool_use",
                "parent_id": "1",
                "status": "completed",
                "metadata": {"tool_name": "calculator", "input": "2+2"},
            },
        ],
    )


@pytest.fixture
def trace_with_failed_tools():
    """Create a trace with failed tool calls."""
    return Trace(
        trace_id="test-trace-failed",
        spans=[
            {
                "span_id": "1",
                "name": "agent_run",
                "parent_id": None,
                "metadata": {"input": "Calculate something", "output": "Error occurred"},
            },
            {
                "span_id": "2",
                "name": "tool_call",
                "parent_id": "1",
                "status": "completed",
                "metadata": {"tool_name": "calculator", "input": "1+1"},
            },
            {
                "span_id": "3",
                "name": "tool_use",
                "parent_id": "1",
                "status": "error",
                "metadata": {"tool_name": "web_search"},
                "error": {"message": "Connection timeout"},
            },
            {
                "span_id": "4",
                "name": "tool_call",
                "parent_id": "1",
                "status": "error",
                "metadata": {"tool_name": "database_query"},
                "error": {"message": "Database unavailable"},
            },
        ],
    )


@pytest.fixture
def trace_no_tools():
    """Create a trace without any tool calls."""
    return Trace(
        trace_id="test-trace-no-tools",
        spans=[
            {
                "span_id": "1",
                "name": "agent_run",
                "parent_id": None,
                "metadata": {"input": "Hello", "output": "Hi there!"},
            }
        ],
    )


class TestToolCallAccuracyEvaluator:
    """Tests for ToolCallAccuracyEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = ToolCallAccuracyEvaluator()

        assert evaluator.name == "tool_call_accuracy"
        assert "tool" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_tool_calls(self, trace_no_tools):
        """Test evaluation with no tool calls."""
        evaluator = ToolCallAccuracyEvaluator()
        result = await evaluator.evaluate(trace_no_tools)

        assert result.evaluator_name == "tool_call_accuracy"
        assert result.scores["tool_success_rate"].value == 1.0  # No tools = no failures
        assert result.metadata["total_tool_calls"] == 0
        assert "no tool calls" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_all_tools_successful(self, trace_with_tools):
        """Test evaluation with all successful tool calls."""
        evaluator = ToolCallAccuracyEvaluator(threshold=0.9)
        result = await evaluator.evaluate(trace_with_tools)

        assert result.scores["tool_success_rate"].value == 1.0
        assert result.metadata["total_tool_calls"] == 2
        assert result.metadata["successful_calls"] == 2
        assert result.metadata["failed_calls"] == 0
        assert result.scores["tool_success_rate"].passed is True

    @pytest.mark.asyncio
    async def test_some_tools_failed(self, trace_with_failed_tools):
        """Test evaluation with some failed tool calls."""
        evaluator = ToolCallAccuracyEvaluator(threshold=0.9)
        result = await evaluator.evaluate(trace_with_failed_tools)

        # 1 successful, 2 failed = 1/3 = 0.333...
        assert result.scores["tool_success_rate"].value == pytest.approx(0.333, abs=0.01)
        assert result.metadata["total_tool_calls"] == 3
        assert result.metadata["successful_calls"] == 1
        assert result.metadata["failed_calls"] == 2
        assert result.scores["tool_success_rate"].passed is False

    @pytest.mark.asyncio
    async def test_failed_tools_metadata(self, trace_with_failed_tools):
        """Test that failed tools are identified in metadata."""
        evaluator = ToolCallAccuracyEvaluator()
        result = await evaluator.evaluate(trace_with_failed_tools)

        failed_tools = result.metadata["failed_tools"]
        assert "web_search" in failed_tools
        assert "database_query" in failed_tools

        # Check error details
        errors = result.metadata["errors"]
        assert len(errors) == 2
        assert any("timeout" in e["error"].lower() for e in errors)

    @pytest.mark.asyncio
    async def test_feedback_message(self, trace_with_failed_tools):
        """Test feedback message includes failure details."""
        evaluator = ToolCallAccuracyEvaluator()
        result = await evaluator.evaluate(trace_with_failed_tools)

        assert "1/3" in result.feedback or "33" in result.feedback
        assert "failed tools" in result.feedback.lower()


class TestToolSelectionEvaluator:
    """Tests for ToolSelectionEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = ToolSelectionEvaluator()

        assert evaluator.name == "tool_selection"
        assert "selection" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_root_span(self):
        """Test handling of trace without root span."""
        trace = Trace(
            trace_id="test",
            spans=[{"span_id": "1", "name": "child", "parent_id": "0"}],
        )

        evaluator = ToolSelectionEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["appropriateness"].value == 0.0
        assert "no root span" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_with_tools(self, trace_with_tools):
        """Test evaluation with tool usage."""
        evaluator = ToolSelectionEvaluator(threshold=0.7)
        result = await evaluator.evaluate(trace_with_tools)

        assert result.evaluator_name == "tool_selection"
        assert "appropriateness" in result.scores
        assert 0.0 <= result.scores["appropriateness"].value <= 1.0

        # Check metadata
        assert "tools_used" in result.metadata
        assert result.metadata["tool_count"] == 2
        assert "web_search" in result.metadata["tools_used"]
        assert "calculator" in result.metadata["tools_used"]

    @pytest.mark.asyncio
    async def test_no_tools_used(self, trace_no_tools):
        """Test evaluation when no tools were used."""
        evaluator = ToolSelectionEvaluator()
        result = await evaluator.evaluate(trace_no_tools)

        assert result.metadata["tool_count"] == 0
        assert result.metadata["tools_used"] == []

    @pytest.mark.asyncio
    async def test_with_available_tools_list(self, trace_with_tools):
        """Test evaluation with available tools list."""
        available_tools = ["web_search", "calculator", "file_reader", "code_executor"]

        evaluator = ToolSelectionEvaluator(available_tools=available_tools)
        result = await evaluator.evaluate(trace_with_tools)

        assert result.metadata["available_tools"] == available_tools

    @pytest.mark.asyncio
    async def test_custom_judge_config(self, trace_with_tools):
        """Test custom judge configuration."""
        config = JudgeConfig(model="gpt-4-turbo", temperature=0.2)
        evaluator = ToolSelectionEvaluator(config=config)
        result = await evaluator.evaluate(trace_with_tools)

        assert result.metadata["judge_model"] == "gpt-4-turbo"

    @pytest.mark.asyncio
    async def test_threshold_configuration(self, trace_with_tools):
        """Test threshold configuration."""
        evaluator = ToolSelectionEvaluator(threshold=0.85)
        result = await evaluator.evaluate(trace_with_tools)

        assert result.scores["appropriateness"].threshold == 0.85
