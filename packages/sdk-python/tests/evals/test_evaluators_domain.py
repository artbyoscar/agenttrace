"""Unit tests for domain-specific evaluators."""

import pytest
from agenttrace.evals.base import Trace
from agenttrace.evals.evaluators.domain import (
    FactualAccuracyEvaluator,
    CodeCorrectnessEvaluator,
)
from agenttrace.evals.evaluators._llm_judge import JudgeConfig


@pytest.fixture
def rag_trace_with_context():
    """Create a RAG trace with context."""
    return Trace(
        trace_id="test-rag-trace",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "metadata": {
                    "input": "What is Python?",
                    "output": "Python is a high-level programming language known for its simplicity.",
                    "context": "Python is a high-level, interpreted programming language. It emphasizes code readability and simplicity.",
                },
            }
        ],
    )


@pytest.fixture
def rag_trace_with_retrieval_spans():
    """Create a RAG trace with retrieval spans."""
    return Trace(
        trace_id="test-rag-retrieval",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "metadata": {
                    "input": "Tell me about AI",
                    "output": "AI stands for Artificial Intelligence.",
                },
            },
            {
                "span_id": "2",
                "name": "retrieval",
                "parent_id": "1",
                "metadata": {
                    "retrieved_documents": [
                        "Artificial Intelligence (AI) is the simulation of human intelligence.",
                        "AI systems can learn and adapt.",
                    ]
                },
            },
        ],
    )


@pytest.fixture
def code_trace_valid():
    """Create a trace with valid Python code."""
    return Trace(
        trace_id="test-code-valid",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "metadata": {
                    "input": "Write a function to add two numbers",
                    "output": """```python
def add(a, b):
    return a + b
```""",
                },
            }
        ],
    )


@pytest.fixture
def code_trace_syntax_error():
    """Create a trace with code containing syntax errors."""
    return Trace(
        trace_id="test-code-error",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "metadata": {
                    "output": """```python
def add(a, b)
    return a + b
```"""
                },
            }
        ],
    )


@pytest.fixture
def code_trace_disallowed_imports():
    """Create a trace with disallowed imports."""
    return Trace(
        trace_id="test-code-imports",
        spans=[
            {
                "span_id": "1",
                "name": "root",
                "parent_id": None,
                "metadata": {
                    "output": """```python
import os
import sys

def dangerous_function():
    os.system('rm -rf /')
```"""
                },
            }
        ],
    )


class TestFactualAccuracyEvaluator:
    """Tests for FactualAccuracyEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = FactualAccuracyEvaluator()

        assert evaluator.name == "factual_accuracy"
        assert "rag" in evaluator.description.lower() or "grounding" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_root_span(self):
        """Test handling of trace without root span."""
        trace = Trace(
            trace_id="test", spans=[{"span_id": "1", "name": "child", "parent_id": "0"}]
        )

        evaluator = FactualAccuracyEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["grounding"].value == 0.0
        assert "no root span" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_no_output(self):
        """Test handling of trace with no output."""
        trace = Trace(
            trace_id="test",
            spans=[{"span_id": "1", "name": "root", "parent_id": None, "metadata": {}}],
        )

        evaluator = FactualAccuracyEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["grounding"].value == 0.0
        assert "no output" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_no_context(self):
        """Test handling of trace with no context."""
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "metadata": {"output": "Some response"},
                }
            ],
        )

        evaluator = FactualAccuracyEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["grounding"].value == 0.0
        assert "no context" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_with_context_in_metadata(self, rag_trace_with_context):
        """Test evaluation with context in metadata."""
        evaluator = FactualAccuracyEvaluator(threshold=0.8)
        result = await evaluator.evaluate(rag_trace_with_context)

        assert result.evaluator_name == "factual_accuracy"
        assert "grounding" in result.scores
        assert 0.0 <= result.scores["grounding"].value <= 1.0
        assert result.metadata["context_length"] > 0

    @pytest.mark.asyncio
    async def test_with_retrieval_spans(self, rag_trace_with_retrieval_spans):
        """Test evaluation with retrieval spans."""
        evaluator = FactualAccuracyEvaluator()
        result = await evaluator.evaluate(rag_trace_with_retrieval_spans)

        # Should find context in retrieval spans
        assert "grounding" in result.scores
        assert 0.0 <= result.scores["grounding"].value <= 1.0

    @pytest.mark.asyncio
    async def test_strict_mode(self, rag_trace_with_context):
        """Test strict mode enforcement."""
        evaluator = FactualAccuracyEvaluator(strict_mode=True, threshold=0.8)
        result = await evaluator.evaluate(rag_trace_with_context)

        assert result.metadata["strict_mode"] is True

    @pytest.mark.asyncio
    async def test_unsupported_claims_metadata(self, rag_trace_with_context):
        """Test that unsupported claims are tracked."""
        evaluator = FactualAccuracyEvaluator()
        result = await evaluator.evaluate(rag_trace_with_context)

        assert "unsupported_claims" in result.metadata
        # Should be a list
        assert isinstance(result.metadata["unsupported_claims"], list)

    @pytest.mark.asyncio
    async def test_custom_judge_config(self, rag_trace_with_context):
        """Test custom judge configuration."""
        config = JudgeConfig(model="claude-3-opus")
        evaluator = FactualAccuracyEvaluator(config=config)
        result = await evaluator.evaluate(rag_trace_with_context)

        assert result.metadata["judge_model"] == "claude-3-opus"


class TestCodeCorrectnessEvaluator:
    """Tests for CodeCorrectnessEvaluator."""

    @pytest.mark.asyncio
    async def test_evaluator_properties(self):
        """Test evaluator name and description."""
        evaluator = CodeCorrectnessEvaluator()

        assert evaluator.name == "code_correctness"
        assert "code" in evaluator.description.lower()

    @pytest.mark.asyncio
    async def test_no_root_span(self):
        """Test handling of trace without root span."""
        trace = Trace(
            trace_id="test", spans=[{"span_id": "1", "name": "child", "parent_id": "0"}]
        )

        evaluator = CodeCorrectnessEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["correctness"].value == 0.0
        assert "no root span" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_no_code_found(self):
        """Test handling when no code is found."""
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "metadata": {"output": "This is just text, not code."},
                }
            ],
        )

        evaluator = CodeCorrectnessEvaluator()
        result = await evaluator.evaluate(trace)

        assert result.scores["correctness"].value == 0.0
        assert "no code" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_valid_code(self, code_trace_valid):
        """Test evaluation of valid code."""
        evaluator = CodeCorrectnessEvaluator(threshold=0.8)
        result = await evaluator.evaluate(code_trace_valid)

        assert result.evaluator_name == "code_correctness"
        assert result.scores["correctness"].value > 0.0
        assert result.metadata["syntax_valid"] is True
        assert "valid" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_syntax_error(self, code_trace_syntax_error):
        """Test detection of syntax errors."""
        evaluator = CodeCorrectnessEvaluator()
        result = await evaluator.evaluate(code_trace_syntax_error)

        assert result.scores["correctness"].value == 0.0
        assert result.metadata["syntax_valid"] is False
        assert "syntax error" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_disallowed_imports(self, code_trace_disallowed_imports):
        """Test detection of disallowed imports."""
        evaluator = CodeCorrectnessEvaluator(
            allowed_imports=["math", "json"]  # os and sys not allowed
        )
        result = await evaluator.evaluate(code_trace_disallowed_imports)

        # Syntax is valid but imports are not allowed
        assert result.metadata["syntax_valid"] is True
        assert result.metadata["imports_valid"] is False
        assert "disallowed imports" in result.feedback.lower()

        disallowed = result.metadata.get("disallowed_imports", [])
        assert "os" in disallowed
        assert "sys" in disallowed

    @pytest.mark.asyncio
    async def test_allowed_imports(self, code_trace_valid):
        """Test that allowed imports pass."""
        # The valid code trace has no imports
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "metadata": {
                        "output": """```python
import math

def calculate():
    return math.pi * 2
```"""
                    },
                }
            ],
        )

        evaluator = CodeCorrectnessEvaluator(allowed_imports=["math"])
        result = await evaluator.evaluate(trace)

        assert result.metadata["syntax_valid"] is True
        assert result.metadata["imports_valid"] is True

    @pytest.mark.asyncio
    async def test_code_extraction_from_markdown(self, code_trace_valid):
        """Test code extraction from markdown code blocks."""
        evaluator = CodeCorrectnessEvaluator()
        result = await evaluator.evaluate(code_trace_valid)

        # Should extract code from ```python ``` blocks
        assert result.metadata["code_length"] > 0

    @pytest.mark.asyncio
    async def test_code_execution_disabled_by_default(self, code_trace_valid):
        """Test that code execution is disabled by default."""
        evaluator = CodeCorrectnessEvaluator(execute_code=False)
        result = await evaluator.evaluate(code_trace_valid)

        exec_result = result.metadata.get("execution_result", {})
        assert exec_result.get("executed", False) is False

    @pytest.mark.asyncio
    async def test_code_execution_enabled(self, code_trace_valid):
        """Test code execution when enabled."""
        evaluator = CodeCorrectnessEvaluator(execute_code=True)
        result = await evaluator.evaluate(code_trace_valid)

        exec_result = result.metadata.get("execution_result", {})
        assert exec_result.get("executed", False) is True
        # Should execute successfully
        assert exec_result.get("success", False) is True

    @pytest.mark.asyncio
    async def test_execution_with_runtime_error(self):
        """Test execution of code with runtime errors."""
        trace = Trace(
            trace_id="test",
            spans=[
                {
                    "span_id": "1",
                    "name": "root",
                    "parent_id": None,
                    "metadata": {
                        "output": """```python
def divide(a, b):
    return a / b

result = divide(10, 0)  # Division by zero
```"""
                    },
                }
            ],
        )

        evaluator = CodeCorrectnessEvaluator(execute_code=True)
        result = await evaluator.evaluate(trace)

        exec_result = result.metadata.get("execution_result", {})
        assert exec_result.get("executed", False) is True
        assert exec_result.get("success", False) is False
        assert "error" in exec_result

    @pytest.mark.asyncio
    async def test_threshold_configuration(self, code_trace_valid):
        """Test threshold configuration."""
        evaluator = CodeCorrectnessEvaluator(threshold=0.9)
        result = await evaluator.evaluate(code_trace_valid)

        assert result.scores["correctness"].threshold == 0.9

    @pytest.mark.asyncio
    async def test_scoring_system(self, code_trace_valid):
        """Test the scoring system."""
        # Without execution
        evaluator_no_exec = CodeCorrectnessEvaluator(execute_code=False)
        result_no_exec = await evaluator_no_exec.evaluate(code_trace_valid)

        # With execution
        evaluator_with_exec = CodeCorrectnessEvaluator(execute_code=True)
        result_with_exec = await evaluator_with_exec.evaluate(code_trace_valid)

        # Executed code should have higher score
        assert result_with_exec.scores["correctness"].value >= result_no_exec.scores[
            "correctness"
        ].value
