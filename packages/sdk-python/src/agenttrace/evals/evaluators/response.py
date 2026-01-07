"""Response quality evaluators for assessing agent output quality."""

from typing import Optional
from ..base import Evaluator, Trace, register_evaluator
from ..models import EvalResult, EvalScore
from ._llm_judge import JudgeConfig, judge_with_llm, create_judge_prompt


@register_evaluator()
class ResponseCompletenessEvaluator(Evaluator):
    """Evaluates if response addresses all aspects of the input query.

    Uses LLM-as-judge pattern to assess response completeness with reasoning.

    Example:
        >>> config = JudgeConfig(model="gpt-4", temperature=0.0)
        >>> evaluator = ResponseCompletenessEvaluator(config=config)
        >>> result = await evaluator.evaluate(trace)
        >>> print(result.scores["completeness"].value)
        0.85
    """

    def __init__(
        self,
        config: Optional[JudgeConfig] = None,
        threshold: float = 0.7,
    ):
        """Initialize the evaluator.

        Args:
            config: LLM judge configuration
            threshold: Minimum score to pass (0.0-1.0)
        """
        self._config = config or JudgeConfig()
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "response_completeness"

    @property
    def description(self) -> str:
        return "Assesses if response addresses all aspects of input using LLM-as-judge"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate response completeness.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with completeness score and reasoning
        """
        # Extract input and output from trace
        root_span = trace.get_root_span()
        if not root_span:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "completeness": EvalScore(
                        name="completeness",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No root span found in trace",
            )

        input_text = root_span.get("metadata", {}).get("input", "")
        output_text = root_span.get("metadata", {}).get("output", "")

        if not input_text or not output_text:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "completeness": EvalScore(
                        name="completeness",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="Missing input or output in trace metadata",
            )

        # Create evaluation prompt
        criteria = """
1. Does the response address all parts of the input query?
2. Are all questions answered?
3. Are all requested tasks completed?
4. Is any important aspect of the input ignored or overlooked?
5. Is the response thorough without being unnecessarily verbose?
"""

        prompt = create_judge_prompt(
            task="Evaluate response completeness",
            input_text=input_text,
            output_text=output_text,
            criteria=criteria,
        )

        # Get LLM judgment
        try:
            result = await judge_with_llm(prompt, self._config)
            score_value = result["score"]
            reasoning = result["reasoning"]
        except Exception as e:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "completeness": EvalScore(
                        name="completeness",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback=f"Error during LLM evaluation: {str(e)}",
            )

        score = EvalScore(
            name="completeness",
            value=score_value,
            threshold=self._threshold,
        )

        return EvalResult(
            evaluator_name=self.name,
            scores={"completeness": score},
            feedback=reasoning,
            metadata={
                "judge_model": self._config.model,
                "input_length": len(input_text),
                "output_length": len(output_text),
            },
        )


@register_evaluator()
class ResponseRelevanceEvaluator(Evaluator):
    """Measures how relevant the response is to the query.

    Penalizes off-topic content and evaluates focus on the actual question.

    Example:
        >>> evaluator = ResponseRelevanceEvaluator(threshold=0.8)
        >>> result = await evaluator.evaluate(trace)
    """

    def __init__(
        self,
        config: Optional[JudgeConfig] = None,
        threshold: float = 0.75,
    ):
        """Initialize the evaluator.

        Args:
            config: LLM judge configuration
            threshold: Minimum score to pass
        """
        self._config = config or JudgeConfig()
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "response_relevance"

    @property
    def description(self) -> str:
        return "Measures how relevant the response is to the input query"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate response relevance.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with relevance score
        """
        root_span = trace.get_root_span()
        if not root_span:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "relevance": EvalScore(
                        name="relevance",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No root span found",
            )

        input_text = root_span.get("metadata", {}).get("input", "")
        output_text = root_span.get("metadata", {}).get("output", "")

        if not input_text or not output_text:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "relevance": EvalScore(
                        name="relevance",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="Missing input or output in trace",
            )

        criteria = """
1. Is the response directly relevant to the input query?
2. Does the response stay on topic throughout?
3. Is there any off-topic or tangential content?
4. Does the response focus on what was actually asked?
5. Is unnecessary information minimized?
"""

        prompt = create_judge_prompt(
            task="Evaluate response relevance",
            input_text=input_text,
            output_text=output_text,
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
                    "relevance": EvalScore(
                        name="relevance",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback=f"Error during evaluation: {str(e)}",
            )

        score = EvalScore(
            name="relevance",
            value=score_value,
            threshold=self._threshold,
        )

        return EvalResult(
            evaluator_name=self.name,
            scores={"relevance": score},
            feedback=reasoning,
            metadata={"judge_model": self._config.model},
        )


@register_evaluator()
class ResponseCoherenceEvaluator(Evaluator):
    """Evaluates logical flow and consistency within the response.

    Checks for contradictions and ensures the response maintains coherence.

    Example:
        >>> evaluator = ResponseCoherenceEvaluator()
        >>> result = await evaluator.evaluate(trace)
        >>> if not result.all_passed():
        ...     print("Response has coherence issues")
    """

    def __init__(
        self,
        config: Optional[JudgeConfig] = None,
        threshold: float = 0.7,
    ):
        """Initialize the evaluator.

        Args:
            config: LLM judge configuration
            threshold: Minimum score to pass
        """
        self._config = config or JudgeConfig()
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "response_coherence"

    @property
    def description(self) -> str:
        return "Evaluates logical flow and consistency within the response"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate response coherence.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with coherence score
        """
        root_span = trace.get_root_span()
        if not root_span:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "coherence": EvalScore(
                        name="coherence",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No root span found",
            )

        output_text = root_span.get("metadata", {}).get("output", "")
        input_text = root_span.get("metadata", {}).get("input", "")

        if not output_text:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "coherence": EvalScore(
                        name="coherence",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="Missing output in trace",
            )

        criteria = """
1. Is the response logically organized and easy to follow?
2. Do ideas flow naturally from one to the next?
3. Are there any contradictions within the response?
4. Is the response internally consistent?
5. Does the response maintain a coherent narrative or argument?
6. Are transitions between topics smooth and logical?
"""

        prompt = create_judge_prompt(
            task="Evaluate response coherence and logical consistency",
            input_text=input_text or "[No input provided]",
            output_text=output_text,
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
                    "coherence": EvalScore(
                        name="coherence",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback=f"Error during evaluation: {str(e)}",
            )

        score = EvalScore(
            name="coherence",
            value=score_value,
            threshold=self._threshold,
        )

        return EvalResult(
            evaluator_name=self.name,
            scores={"coherence": score},
            feedback=reasoning,
            metadata={
                "judge_model": self._config.model,
                "output_length": len(output_text),
            },
        )
