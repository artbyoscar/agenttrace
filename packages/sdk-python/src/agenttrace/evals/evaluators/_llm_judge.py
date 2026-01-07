"""LLM-as-judge helper for evaluators that need LLM-based assessment."""

from typing import Optional, Dict, Any, Protocol
from dataclasses import dataclass


class LLMClient(Protocol):
    """Protocol for LLM clients used in judge evaluators."""

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional arguments for the LLM

        Returns:
            The LLM response as a string
        """
        ...


@dataclass
class JudgeConfig:
    """Configuration for LLM-as-judge evaluators.

    Attributes:
        model: Model identifier (e.g., "gpt-4", "claude-3-opus")
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        client: Optional custom LLM client
    """

    model: str = "gpt-4"
    temperature: float = 0.0
    max_tokens: int = 500
    client: Optional[LLMClient] = None


class SimpleLLMClient:
    """Simple mock LLM client for testing and fallback.

    This is a placeholder that returns deterministic responses.
    In production, replace with actual LLM client (OpenAI, Anthropic, etc.).
    """

    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        """Initialize the simple LLM client.

        Args:
            model: Model identifier
            api_key: API key for the LLM service
        """
        self.model = model
        self.api_key = api_key

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a mock response.

        Args:
            prompt: The prompt
            **kwargs: Additional arguments

        Returns:
            A mock response
        """
        # This is a placeholder implementation
        # In production, this would call actual LLM API
        return "Score: 0.8\nReasoning: This is a mock evaluation."


async def judge_with_llm(
    prompt: str,
    config: JudgeConfig,
) -> Dict[str, Any]:
    """Use an LLM to judge quality and extract structured results.

    Args:
        prompt: The evaluation prompt
        config: LLM judge configuration

    Returns:
        Dictionary with 'score' (float) and 'reasoning' (str)

    Raises:
        ValueError: If LLM response cannot be parsed
    """
    client = config.client or SimpleLLMClient(model=config.model)

    response = await client.generate(
        prompt,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    # Parse the response to extract score and reasoning
    # Expected format: "Score: X.XX\nReasoning: ..."
    score = None
    reasoning = ""

    lines = response.strip().split("\n")
    for line in lines:
        if line.startswith("Score:"):
            try:
                score_str = line.replace("Score:", "").strip()
                score = float(score_str)
            except ValueError:
                continue
        elif line.startswith("Reasoning:"):
            reasoning = line.replace("Reasoning:", "").strip()

    # If we couldn't parse a proper score, try to find it anywhere in the response
    if score is None:
        import re

        score_match = re.search(r"(\d+\.?\d*)\s*/\s*(?:1\.0|10|100)", response)
        if score_match:
            score = float(score_match.group(1))
            # Normalize to 0.0-1.0 if it's out of 10 or 100
            if score > 1.0:
                if score <= 10.0:
                    score = score / 10.0
                elif score <= 100.0:
                    score = score / 100.0

    if score is None:
        raise ValueError(
            f"Could not parse score from LLM response: {response[:100]}"
        )

    # Clamp score to valid range
    score = max(0.0, min(1.0, score))

    if not reasoning:
        reasoning = response

    return {"score": score, "reasoning": reasoning}


def create_judge_prompt(
    task: str,
    input_text: str,
    output_text: str,
    criteria: str,
) -> str:
    """Create a standardized prompt for LLM-as-judge evaluation.

    Args:
        task: Description of what's being evaluated
        input_text: The input/query that was given
        output_text: The output/response to evaluate
        criteria: Evaluation criteria

    Returns:
        Formatted prompt for the judge LLM
    """
    prompt = f"""You are an expert evaluator assessing AI agent outputs.

Task: {task}

Input:
{input_text}

Output:
{output_text}

Evaluation Criteria:
{criteria}

Please provide your evaluation in the following format:
Score: [A number between 0.0 and 1.0]
Reasoning: [Your explanation for the score]

Score should be:
- 1.0: Perfect, meets all criteria excellently
- 0.8-0.9: Very good, meets most criteria well
- 0.6-0.7: Adequate, meets basic criteria
- 0.4-0.5: Below average, missing some criteria
- 0.0-0.3: Poor, fails to meet criteria

Provide your evaluation now:"""

    return prompt
