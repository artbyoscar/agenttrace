"""Tool usage evaluators for assessing agent tool selection and execution."""

from typing import Optional, List, Dict, Any
from ..base import Evaluator, Trace, register_evaluator
from ..models import EvalResult, EvalScore
from ._llm_judge import JudgeConfig, judge_with_llm, create_judge_prompt


@register_evaluator()
class ToolCallAccuracyEvaluator(Evaluator):
    """Measures successful vs failed tool calls.

    Analyzes tool execution spans to calculate success rate and identify
    problematic tools.

    Example:
        >>> evaluator = ToolCallAccuracyEvaluator(threshold=0.9)
        >>> result = await evaluator.evaluate(trace)
        >>> print(result.metadata["failed_tools"])
        ["web_search", "calculator"]
    """

    def __init__(self, threshold: float = 0.9):
        """Initialize the evaluator.

        Args:
            threshold: Minimum success rate to pass (0.0-1.0)
        """
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "tool_call_accuracy"

    @property
    def description(self) -> str:
        return "Measures successful vs failed tool calls"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate tool call accuracy.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with tool success rate and failure details
        """
        # Find all tool-related spans
        tool_spans = self._find_tool_spans(trace)

        if not tool_spans:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "tool_success_rate": EvalScore(
                        name="tool_success_rate",
                        value=1.0,  # No tools = no failures
                        threshold=self._threshold,
                    )
                },
                feedback="No tool calls found in trace",
                metadata={"total_tool_calls": 0},
            )

        # Count successes and failures
        total_calls = len(tool_spans)
        successful_calls = sum(
            1 for span in tool_spans if span.get("status") == "completed"
        )
        failed_calls = total_calls - successful_calls

        success_rate = successful_calls / total_calls if total_calls > 0 else 1.0

        # Identify which tools failed
        failed_tools = [
            span.get("metadata", {}).get("tool_name", span.get("name"))
            for span in tool_spans
            if span.get("status") != "completed"
        ]

        # Get error details
        errors = [
            {
                "tool": span.get("metadata", {}).get("tool_name", span.get("name")),
                "error": span.get("error", {}).get("message", "Unknown error"),
            }
            for span in tool_spans
            if span.get("status") == "error"
        ]

        score = EvalScore(
            name="tool_success_rate",
            value=success_rate,
            threshold=self._threshold,
        )

        feedback = (
            f"Tool calls: {successful_calls}/{total_calls} successful "
            f"({success_rate:.1%} success rate)"
        )
        if failed_tools:
            feedback += f"\nFailed tools: {', '.join(set(failed_tools))}"

        return EvalResult(
            evaluator_name=self.name,
            scores={"tool_success_rate": score},
            feedback=feedback,
            metadata={
                "total_tool_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "failed_tools": list(set(failed_tools)),
                "errors": errors,
            },
        )

    def _find_tool_spans(self, trace: Trace) -> List[Dict[str, Any]]:
        """Find all tool-related spans in the trace.

        Args:
            trace: The trace to search

        Returns:
            List of tool span dictionaries
        """
        tool_spans = []
        for span in trace.spans:
            name = span.get("name", "").lower()
            tags = span.get("tags", [])

            # Check if this is a tool span
            if (
                "tool" in name
                or "tool_call" in name
                or "tool_use" in name
                or "tool" in tags
            ):
                tool_spans.append(span)

        return tool_spans


@register_evaluator()
class ToolSelectionEvaluator(Evaluator):
    """Uses LLM to judge if correct tools were selected for the task.

    Evaluates tool selection appropriateness and identifies unnecessary
    or missing tool calls.

    Example:
        >>> config = JudgeConfig(model="gpt-4")
        >>> evaluator = ToolSelectionEvaluator(config=config)
        >>> result = await evaluator.evaluate(trace)
    """

    def __init__(
        self,
        config: Optional[JudgeConfig] = None,
        threshold: float = 0.75,
        available_tools: Optional[List[str]] = None,
    ):
        """Initialize the evaluator.

        Args:
            config: LLM judge configuration
            threshold: Minimum score to pass
            available_tools: List of tools available to the agent
        """
        self._config = config or JudgeConfig()
        self._threshold = threshold
        self._available_tools = available_tools or []

    @property
    def name(self) -> str:
        return "tool_selection"

    @property
    def description(self) -> str:
        return "Evaluates if correct tools were selected for the task using LLM judge"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate tool selection appropriateness.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with appropriateness score and recommendations
        """
        root_span = trace.get_root_span()
        if not root_span:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "appropriateness": EvalScore(
                        name="appropriateness",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No root span found",
            )

        # Get input and output
        input_text = root_span.get("metadata", {}).get("input", "")
        output_text = root_span.get("metadata", {}).get("output", "")

        # Find tool calls
        tool_spans = []
        for span in trace.spans:
            name = span.get("name", "").lower()
            if "tool" in name:
                tool_spans.append(span)

        # Build tool usage summary
        tools_used = []
        for span in tool_spans:
            tool_name = span.get("metadata", {}).get("tool_name", span.get("name"))
            tool_input = span.get("metadata", {}).get("input", "")
            tool_output = span.get("metadata", {}).get("output", "")
            tools_used.append(
                {
                    "name": tool_name,
                    "input": tool_input[:100],  # Truncate for brevity
                    "output": tool_output[:100],
                    "status": span.get("status"),
                }
            )

        # Build evaluation context
        tools_summary = "\n".join(
            [
                f"- {t['name']}: {t['status']} (input: {t['input']})"
                for t in tools_used
            ]
        )

        if not tools_summary:
            tools_summary = "[No tools were used]"

        available_tools_str = (
            "\n".join([f"- {tool}" for tool in self._available_tools])
            if self._available_tools
            else "[Tool list not provided]"
        )

        criteria = f"""
Available tools:
{available_tools_str}

Tools used in this trace:
{tools_summary}

Evaluate:
1. Were the right tools selected for the task?
2. Were any necessary tools missing?
3. Were any unnecessary tools used?
4. Was the sequence of tool calls logical?
5. Could the task have been accomplished more efficiently with different tool choices?
"""

        prompt = create_judge_prompt(
            task="Evaluate tool selection appropriateness",
            input_text=input_text or "[Task not specified]",
            output_text=output_text or "[Output not captured]",
            criteria=criteria,
        )

        try:
            result = await judge_with_llm(prompt, self._config)
            score_value = result["score"]
            reasoning = result["reasoning"]
        except Exception as e:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "appropriateness": EvalScore(
                        name="appropriateness",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback=f"Error during evaluation: {str(e)}",
            )

        score = EvalScore(
            name="appropriateness",
            value=score_value,
            threshold=self._threshold,
        )

        return EvalResult(
            evaluator_name=self.name,
            scores={"appropriateness": score},
            feedback=reasoning,
            metadata={
                "judge_model": self._config.model,
                "tools_used": [t["name"] for t in tools_used],
                "tool_count": len(tools_used),
                "available_tools": self._available_tools,
            },
        )
