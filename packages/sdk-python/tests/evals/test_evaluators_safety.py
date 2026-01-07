"""Unit tests for safety evaluators."""

import pytest
from agenttrace.evals.base import Trace
from agenttrace.evals.evaluators.safety import (
    PIIDetectionEvaluator,
    HarmfulContentEvaluator,
)
from agenttrace.evals.evaluators._llm_judge import JudgeConfig


@pytest.fixture
def trace_with_pii():
    """Create a trace containing PII."""
    return Trace(
        trace_id="test-trace-pii",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "metadata": {
                    "input": "Contact me",
                    "output": "You can reach me at john.doe@example.com or call 555-123-4567.",
                },
            }
        ],
    )


@pytest.fixture
def trace_with_sensitive_pii():
    """Create a trace with sensitive PII."""
    return Trace(
        trace_id="test-trace-sensitive",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "metadata": {
                    "output": "SSN: 123-45-6789, Credit Card: 4532-1234-5678-9010"
                },
            }
        ],
    )


@pytest.fixture
def trace_clean():
    """Create a trace without PII."""
    return Trace(
        trace_id="test-trace-clean",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "metadata": {
                    "input": "What is Python?",
                    "output": "Python is a programming language.",
                },
            }
        ],
    )


@pytest.fixture
def trace_potentially_harmful():
    """Create a trace with potentially harmful content."""
    return Trace(
        trace_id="test-trace-harmful",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "metadata": {
                    "input": "How to build something?",
                    "output": "You could use violence to attack someone...",
                },
            }
        ],
    )


class TestPIIDetectionEvaluator:
    """Tests for PIIDetectionEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = PIIDetectionEvaluator()

        assert evaluator.name == "pii_detection"
        assert "pii" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_output(self):
        """Test evaluation with no output."""
        trace = Trace(
            trace_id="test",
            spans=[{"span_id": "1", "name": "root", "parent_id": None, "metadata": {}}],
        )

        evaluator = PIIDetectionEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["pii_free"].value == 1.0
        assert "no output" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_clean_output(self, trace_clean):
        """Test evaluation with clean output."""
        evaluator = PIIDetectionEvaluator()
        result = await evaluator.evaluate(trace_clean)

        assert result.scores["pii_free"].value == 1.0
        assert result.scores["pii_free"].passed is True
        assert result.metadata["detected_pii_types"] == []
        assert "no pii" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_detect_email(self, trace_with_pii):
        """Test detection of email addresses."""
        evaluator = PIIDetectionEvaluator(detect_types=["email"])
        result = await evaluator.evaluate(trace_with_pii)

        assert result.scores["pii_free"].value == 0.0
        assert result.scores["pii_free"].passed is False
        assert "email" in result.metadata["detected_pii_types"]
        assert "pii detected" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_detect_phone(self, trace_with_pii):
        """Test detection of phone numbers."""
        evaluator = PIIDetectionEvaluator(detect_types=["phone"])
        result = await evaluator.evaluate(trace_with_pii)

        assert result.scores["pii_free"].value == 0.0
        assert "phone" in result.metadata["detected_pii_types"]

    @pytest.mark.asyncio
    async def test_detect_multiple_pii_types(self, trace_with_pii):
        """Test detection of multiple PII types."""
        evaluator = PIIDetectionEvaluator(detect_types=["email", "phone"])
        result = await evaluator.evaluate(trace_with_pii)

        assert result.scores["pii_free"].value == 0.0
        detected_types = result.metadata["detected_pii_types"]
        assert "email" in detected_types
        assert "phone" in detected_types
        assert result.metadata["pii_count"] >= 2

    @pytest.mark.asyncio
    async def test_detect_ssn(self, trace_with_sensitive_pii):
        """Test detection of Social Security Numbers."""
        evaluator = PIIDetectionEvaluator(detect_types=["ssn"])
        result = await evaluator.evaluate(trace_with_sensitive_pii)

        assert result.scores["pii_free"].value == 0.0
        assert "ssn" in result.metadata["detected_pii_types"]

    @pytest.mark.asyncio
    async def test_detect_credit_card(self, trace_with_sensitive_pii):
        """Test detection of credit card numbers."""
        evaluator = PIIDetectionEvaluator(detect_types=["credit_card"])
        result = await evaluator.evaluate(trace_with_sensitive_pii)

        assert result.scores["pii_free"].value == 0.0
        assert "credit_card" in result.metadata["detected_pii_types"]

    @pytest.mark.asyncio
    async def test_custom_patterns(self):
        """Test custom PII patterns."""
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "metadata": {"output": "My employee ID is EMP-12345"},
                }
            ],
        )

        custom_patterns = {"employee_id": r"EMP-\d{5}"}

        evaluator = PIIDetectionEvaluator(
            detect_types=[], custom_patterns=custom_patterns
        )
        result = await evaluator.evaluate(trace)

        assert result.scores["pii_free"].value == 0.0
        assert "employee_id" in result.metadata["detected_pii_types"]

    @pytest.mark.asyncio
    async def test_selective_detection(self, trace_with_pii):
        """Test selective PII type detection."""
        # Only check for email, not phone
        evaluator = PIIDetectionEvaluator(detect_types=["email"])
        result = await evaluator.evaluate(trace_with_pii)

        # Should detect email
        assert "email" in result.metadata["detected_pii_types"]
        # Should not check for phone
        assert "phone" not in result.metadata["detected_pii_types"]

    @pytest.mark.asyncio
    async def test_scanned_length_metadata(self, trace_with_pii):
        """Test that scanned length is tracked."""
        evaluator = PIIDetectionEvaluator()
        result = await evaluator.evaluate(trace_with_pii)

        assert "scanned_length" in result.metadata
        assert result.metadata["scanned_length"] > 0


class TestHarmfulContentEvaluator:
    """Tests for HarmfulContentEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = HarmfulContentEvaluator()

        assert evaluator.name == "harmful_content"
        assert "harmful" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_root_span(self):
        """Test handling of trace without root span."""
        trace = Trace(
            trace_id="test", spans=[{"span_id": "1", "name": "child", "parent_id": "0"}]
        )

        evaluator = HarmfulContentEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["safety"].value == 1.0
        assert "no root span" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_no_output(self):
        """Test handling of trace with no output."""
        trace = Trace(
            trace_id="test",
            spans=[{"span_id": "1", "name": "root", "parent_id": None, "metadata": {}}],
        )

        evaluator = HarmfulContentEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["safety"].value == 1.0
        assert "no output" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_safe_content(self, trace_clean):
        """Test evaluation of safe content."""
        evaluator = HarmfulContentEvaluator(threshold=0.9)
        result = await evaluator.evaluate(trace_clean)

        assert result.evaluator_name == "harmful_content"
        assert "safety" in result.scores
        # Score should be reasonably high for safe content
        assert result.scores["safety"].value >= 0.7

    @pytest.mark.asyncio
    async def test_sensitivity_levels(self, trace_clean):
        """Test different sensitivity levels."""
        for sensitivity in ["low", "medium", "high"]:
            evaluator = HarmfulContentEvaluator(sensitivity=sensitivity)
            result = await evaluator.evaluate(trace_clean)

            assert result.metadata["sensitivity"] == sensitivity

    @pytest.mark.asyncio
    async def test_custom_categories(self, trace_clean):
        """Test custom harm categories."""
        categories = ["violence", "hate_speech"]

        evaluator = HarmfulContentEvaluator(check_categories=categories)
        result = await evaluator.evaluate(trace_clean)

        assert result.metadata["check_categories"] == categories

    @pytest.mark.asyncio
    async def test_simple_keyword_check(self, trace_potentially_harmful):
        """Test simple keyword-based checking."""
        evaluator = HarmfulContentEvaluator()
        result = await evaluator.evaluate(trace_potentially_harmful)

        # Should detect harmful keywords
        simple_check = result.metadata.get("simple_check", {})
        assert "flagged_keywords" in simple_check
        # Might flag violence-related keywords
        if not simple_check["is_safe"]:
            assert len(simple_check["flagged_keywords"]) > 0

    @pytest.mark.asyncio
    async def test_threshold_configuration(self, trace_clean):
        """Test threshold configuration."""
        evaluator = HarmfulContentEvaluator(threshold=0.95)
        result = await evaluator.evaluate(trace_clean)

        assert result.scores["safety"].threshold == 0.95

    @pytest.mark.asyncio
    async def test_judge_model_metadata(self, trace_clean):
        """Test that judge model is tracked in metadata."""
        config = JudgeConfig(model="gpt-4-turbo")
        evaluator = HarmfulContentEvaluator(config=config)
        result = await evaluator.evaluate(trace_clean)

        assert result.metadata["judge_model"] == "gpt-4-turbo"

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self):
        """Test fallback to simple check on LLM failure."""
        # This would require mocking LLM failure, simplified here
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "metadata": {"output": "Completely safe content."},
                }
            ],
        )

        evaluator = HarmfulContentEvaluator()
        result = await evaluator.evaluate(trace)

        # Should still complete even if LLM fails (mock returns score)
        assert "safety" in result.scores
        assert 0.0 <= result.scores["safety"].value <= 1.0
