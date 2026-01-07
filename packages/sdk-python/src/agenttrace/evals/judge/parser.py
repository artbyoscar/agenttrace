"""Parsing and validation of LLM judge responses."""

import json
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Judgment:
    """Parsed judgment from LLM judge.

    Attributes:
        score: Normalized score (0.0-1.0)
        reasoning: Explanation for the score
        raw_score: Original score before normalization
        confidence: Optional confidence level (0.0-1.0)
        metadata: Additional metadata from the judgment
        raw_response: Original LLM response
    """

    score: float
    reasoning: str
    raw_score: float
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = None
    raw_response: str = ""

    def __post_init__(self):
        """Validate score ranges."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")

        if self.confidence is not None:
            if not 0.0 <= self.confidence <= 1.0:
                raise ValueError(
                    f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
                )

        if self.metadata is None:
            self.metadata = {}


class JudgmentParser:
    """Parser for LLM judge responses with multiple fallback strategies.

    Handles JSON responses, plain text with scores, and malformed responses.

    Example:
        >>> parser = JudgmentParser()
        >>> response = '{"score": 8, "reasoning": "Good response"}'
        >>> judgment = parser.parse(response)
        >>> judgment.score
        0.8
    """

    def __init__(self, expected_max_score: int = 10):
        """Initialize the parser.

        Args:
            expected_max_score: Maximum score value for normalization (default: 10)
        """
        self.expected_max_score = expected_max_score

    def parse(self, response: str) -> Judgment:
        """Parse LLM response into a Judgment object.

        Tries multiple parsing strategies in order:
        1. JSON parsing (preferred)
        2. Pattern matching for score/reasoning
        3. Fallback heuristics

        Args:
            response: Raw LLM response

        Returns:
            Parsed Judgment object

        Raises:
            ValueError: If response cannot be parsed

        Example:
            >>> parser = JudgmentParser()
            >>> judgment = parser.parse('{"score": 9, "reasoning": "Excellent"}')
            >>> judgment.score
            0.9
        """
        if not response or not response.strip():
            raise ValueError("Empty response from judge")

        # Strategy 1: Try JSON parsing first (preferred)
        try:
            return self._parse_json(response)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            pass  # Fall through to next strategy

        # Strategy 2: Try pattern matching
        try:
            return self._parse_with_patterns(response)
        except ValueError:
            pass  # Fall through to next strategy

        # Strategy 3: Fallback heuristics
        try:
            return self._parse_fallback(response)
        except ValueError as e:
            raise ValueError(
                f"Could not parse judgment from response. "
                f"Response preview: {response[:200]}..."
            ) from e

    def _parse_json(self, response: str) -> Judgment:
        """Parse JSON response.

        Expected format:
        {
            "score": 8,
            "reasoning": "The response is...",
            "confidence": 0.9  // optional
        }

        Args:
            response: JSON response string

        Returns:
            Judgment object

        Raises:
            json.JSONDecodeError: If not valid JSON
            KeyError: If required fields missing
            ValueError: If score invalid
        """
        # Try to extract JSON from markdown code blocks if present
        json_text = response.strip()
        if "```json" in json_text:
            match = re.search(r"```json\s*(\{.*?\})\s*```", json_text, re.DOTALL)
            if match:
                json_text = match.group(1)
        elif "```" in json_text:
            match = re.search(r"```\s*(\{.*?\})\s*```", json_text, re.DOTALL)
            if match:
                json_text = match.group(1)

        data = json.loads(json_text)

        # Extract score (required)
        raw_score = self._extract_score_from_dict(data)

        # Normalize score to 0.0-1.0
        score = self._normalize_score(raw_score)

        # Extract reasoning (required)
        reasoning = data.get("reasoning") or data.get("explanation") or data.get("reason")

        if not reasoning:
            raise KeyError("No reasoning field found in JSON response")

        # Extract optional fields
        confidence = data.get("confidence")
        if confidence is not None:
            confidence = float(confidence)

        # Extract additional metadata
        metadata = {k: v for k, v in data.items() if k not in ["score", "reasoning", "confidence"]}

        return Judgment(
            score=score,
            reasoning=reasoning,
            raw_score=raw_score,
            confidence=confidence,
            metadata=metadata,
            raw_response=response,
        )

    def _parse_with_patterns(self, response: str) -> Judgment:
        """Parse response using regex patterns.

        Looks for patterns like:
        - "Score: 8/10"
        - "Rating: 8"
        - "Score: 0.8"

        Args:
            response: Response text

        Returns:
            Judgment object

        Raises:
            ValueError: If patterns don't match
        """
        # Pattern 1: Score: X/Y or Score: X out of Y
        pattern1 = r"(?:score|rating):\s*(\d+\.?\d*)\s*(?:/|out of)\s*(\d+\.?\d*)"
        match = re.search(pattern1, response, re.IGNORECASE)

        if match:
            score_val = float(match.group(1))
            max_val = float(match.group(2))
            raw_score = score_val
            score = score_val / max_val  # Normalize

            # Extract reasoning (everything after the score line)
            reasoning_match = re.search(
                r"(?:reasoning|explanation|justification):\s*(.+)",
                response,
                re.IGNORECASE | re.DOTALL,
            )
            reasoning = reasoning_match.group(1).strip() if reasoning_match else response

            return Judgment(
                score=score,
                reasoning=reasoning,
                raw_score=raw_score,
                raw_response=response,
            )

        # Pattern 2: Score: X (single number)
        pattern2 = r"(?:score|rating):\s*(\d+\.?\d*)"
        match = re.search(pattern2, response, re.IGNORECASE)

        if match:
            raw_score = float(match.group(1))
            score = self._normalize_score(raw_score)

            # Extract reasoning
            reasoning_match = re.search(
                r"(?:reasoning|explanation|justification):\s*(.+)",
                response,
                re.IGNORECASE | re.DOTALL,
            )
            reasoning = reasoning_match.group(1).strip() if reasoning_match else response

            return Judgment(
                score=score,
                reasoning=reasoning,
                raw_score=raw_score,
                raw_response=response,
            )

        raise ValueError("No score pattern found in response")

    def _parse_fallback(self, response: str) -> Judgment:
        """Fallback parser using heuristics.

        Looks for any number that could be a score.

        Args:
            response: Response text

        Returns:
            Judgment object

        Raises:
            ValueError: If no score can be extracted
        """
        # Look for any number between 0-10 or 0.0-1.0
        numbers = re.findall(r"\b(\d+\.?\d*)\b", response)

        for num_str in numbers:
            num = float(num_str)

            # Check if it's a valid score
            if 0 <= num <= self.expected_max_score or 0.0 <= num <= 1.0:
                raw_score = num
                score = self._normalize_score(num)

                return Judgment(
                    score=score,
                    reasoning=response,  # Use full response as reasoning
                    raw_score=raw_score,
                    raw_response=response,
                )

        raise ValueError("No valid score found in response")

    def _extract_score_from_dict(self, data: Dict[str, Any]) -> float:
        """Extract score from dictionary with multiple possible keys.

        Args:
            data: Dictionary potentially containing score

        Returns:
            Score value

        Raises:
            KeyError: If no score field found
        """
        score_keys = ["score", "rating", "value", "judgment"]

        for key in score_keys:
            if key in data:
                return float(data[key])

        raise KeyError(f"No score field found. Tried keys: {score_keys}")

    def _normalize_score(self, raw_score: float) -> float:
        """Normalize score to 0.0-1.0 range.

        Args:
            raw_score: Raw score value

        Returns:
            Normalized score (0.0-1.0)

        Raises:
            ValueError: If score is invalid
        """
        # If already in 0.0-1.0 range, return as-is
        if 0.0 <= raw_score <= 1.0:
            return raw_score

        # If in 0-expected_max_score range, normalize
        if 0 <= raw_score <= self.expected_max_score:
            return raw_score / self.expected_max_score

        # If in 0-100 range (percentage), convert
        if 0 <= raw_score <= 100:
            return raw_score / 100.0

        raise ValueError(
            f"Score {raw_score} is outside valid ranges: "
            f"0.0-1.0, 0-{self.expected_max_score}, or 0-100"
        )


def parse_judgment(response: str, expected_max_score: int = 10) -> Judgment:
    """Convenience function to parse a judgment.

    Args:
        response: Raw LLM response
        expected_max_score: Maximum score for normalization

    Returns:
        Parsed Judgment

    Example:
        >>> judgment = parse_judgment('{"score": 7, "reasoning": "Good"}')
        >>> judgment.score
        0.7
    """
    parser = JudgmentParser(expected_max_score=expected_max_score)
    return parser.parse(response)
