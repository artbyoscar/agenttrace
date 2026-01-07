"""Tests for judgment parser."""

import pytest
from agenttrace.evals.judge.parser import JudgmentParser, Judgment, parse_judgment


class TestJudgmentParser:
    """Tests for JudgmentParser class."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        response = '{"score": 8, "reasoning": "Good response"}'
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.score == 0.8
        assert judgment.reasoning == "Good response"
        assert judgment.raw_score == 8.0

    def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        response = '''```json
{
    "score": 9,
    "reasoning": "Excellent work"
}
```'''
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.score == 0.9
        assert judgment.reasoning == "Excellent work"

    def test_parse_json_with_confidence(self):
        """Test parsing JSON with confidence field."""
        response = '{"score": 7, "reasoning": "Decent", "confidence": 0.95}'
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.score == 0.7
        assert judgment.confidence == 0.95

    def test_parse_json_with_metadata(self):
        """Test parsing JSON with additional metadata."""
        response = '{"score": 8, "reasoning": "Good", "category": "test", "details": "extra"}'
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.score == 0.8
        assert "category" in judgment.metadata
        assert judgment.metadata["category"] == "test"

    def test_parse_score_with_slash(self):
        """Test parsing pattern like 'Score: 8/10'."""
        response = "Score: 8/10\nReasoning: This is good"
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.score == 0.8
        assert "good" in judgment.reasoning.lower()

    def test_parse_score_out_of(self):
        """Test parsing pattern like 'Score: 7 out of 10'."""
        response = "Score: 7 out of 10\nReasoning: Acceptable quality"
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.score == 0.7

    def test_parse_simple_score(self):
        """Test parsing simple score pattern."""
        response = "Score: 9\nReasoning: Excellent response"
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.score == 0.9

    def test_parse_fallback_number(self):
        """Test fallback parsing finds numbers in text."""
        response = "The quality is 8 out of 10 based on criteria"
        parser = JudgmentParser()
        judgment = parser.parse(response)

        # Should find the 8 and normalize it
        assert 0.0 <= judgment.score <= 1.0

    def test_parse_normalized_score(self):
        """Test parsing already normalized score (0.0-1.0)."""
        response = '{"score": 0.85, "reasoning": "Very good"}'
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.score == 0.85

    def test_parse_percentage_score(self):
        """Test parsing percentage (0-100)."""
        response = '{"score": 85, "reasoning": "85% quality"}'
        parser = JudgmentParser(expected_max_score=100)
        judgment = parser.parse(response)

        assert judgment.score == 0.85

    def test_parse_empty_response(self):
        """Test that empty response raises error."""
        parser = JudgmentParser()
        with pytest.raises(ValueError, match="Empty response"):
            parser.parse("")

    def test_parse_invalid_response(self):
        """Test that unparseable response raises error."""
        response = "This is completely invalid with no score"
        parser = JudgmentParser()

        with pytest.raises(ValueError):
            parser.parse(response)

    def test_parse_alternative_keys(self):
        """Test parsing with alternative JSON keys."""
        response = '{"rating": 9, "explanation": "Great work"}'
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.score == 0.9
        assert "great" in judgment.reasoning.lower()

    def test_score_validation(self):
        """Test that invalid scores raise errors."""
        with pytest.raises(ValueError):
            Judgment(score=1.5, reasoning="test", raw_score=15)

        with pytest.raises(ValueError):
            Judgment(score=-0.1, reasoning="test", raw_score=-1)

    def test_confidence_validation(self):
        """Test that invalid confidence raises errors."""
        with pytest.raises(ValueError):
            Judgment(score=0.8, reasoning="test", raw_score=8, confidence=1.5)

    def test_parse_judgment_convenience_function(self):
        """Test the convenience function."""
        response = '{"score": 7, "reasoning": "Good"}'
        judgment = parse_judgment(response)

        assert judgment.score == 0.7
        assert judgment.reasoning == "Good"

    def test_custom_max_score(self):
        """Test custom maximum score normalization."""
        response = '{"score": 4, "reasoning": "Half way"}'
        parser = JudgmentParser(expected_max_score=5)
        judgment = parser.parse(response)

        assert judgment.score == 0.8  # 4/5

    def test_raw_response_preserved(self):
        """Test that raw response is preserved."""
        response = '{"score": 8, "reasoning": "Good"}'
        parser = JudgmentParser()
        judgment = parser.parse(response)

        assert judgment.raw_response == response
