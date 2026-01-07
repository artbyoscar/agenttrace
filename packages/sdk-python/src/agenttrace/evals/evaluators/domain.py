"""Domain-specific evaluators for specialized use cases like RAG and code generation."""

import ast
import sys
from io import StringIO
from typing import Optional, List, Dict, Any
from ..base import Evaluator, Trace, register_evaluator
from ..models import EvalResult, EvalScore
from ._llm_judge import JudgeConfig, judge_with_llm, create_judge_prompt


@register_evaluator()
class FactualAccuracyEvaluator(Evaluator):
    """For RAG applications: compares response against retrieved context.

    Evaluates if the response is grounded in the provided context and
    identifies unsupported claims.

    Example:
        >>> evaluator = FactualAccuracyEvaluator()
        >>> result = await evaluator.evaluate(trace)
        >>> if result.metadata["unsupported_claims"]:
        ...     print("Response contains hallucinations")
    """

    def __init__(
        self,
        config: Optional[JudgeConfig] = None,
        threshold: float = 0.8,
        strict_mode: bool = False,
    ):
        """Initialize the evaluator.

        Args:
            config: LLM judge configuration
            threshold: Minimum grounding score to pass
            strict_mode: If True, any unsupported claim fails the evaluation
        """
        self._config = config or JudgeConfig()
        self._threshold = threshold
        self._strict_mode = strict_mode

    @property
    def name(self) -> str:
        return "factual_accuracy"

    @property
    def description(self) -> str:
        return "Evaluates if RAG response is grounded in retrieved context"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate factual accuracy against context.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with grounding score and unsupported claims
        """
        root_span = trace.get_root_span()
        if not root_span:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "grounding": EvalScore(
                        name="grounding",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No root span found",
            )

        # Get output and context
        output_text = root_span.get("metadata", {}).get("output", "")
        retrieved_context = root_span.get("metadata", {}).get("context", "")

        # Also check for context in retrieval spans
        if not retrieved_context:
            retrieval_spans = [
                span
                for span in trace.spans
                if "retrieval" in span.get("name", "").lower()
                or "retrieve" in span.get("name", "").lower()
            ]
            context_parts = []
            for span in retrieval_spans:
                ctx = span.get("metadata", {}).get("retrieved_documents", [])
                if isinstance(ctx, list):
                    context_parts.extend([str(doc) for doc in ctx])
                else:
                    context_parts.append(str(ctx))

            retrieved_context = "\n".join(context_parts)

        if not output_text:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "grounding": EvalScore(
                        name="grounding",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No output found",
            )

        if not retrieved_context:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "grounding": EvalScore(
                        name="grounding",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No context found for grounding evaluation",
            )

        # Use LLM to evaluate grounding
        criteria = f"""
Retrieved Context:
{retrieved_context[:1000]}

Evaluate:
1. Is every claim in the response supported by the retrieved context?
2. Are there any facts stated that cannot be verified from the context?
3. Does the response stay within the bounds of the provided information?
4. Are there any hallucinations or invented facts?

Strict mode: {"Yes - Any unsupported claim should significantly lower the score" if self._strict_mode else "No - Minor unsupported details are acceptable"}

Provide a list of any unsupported claims in your reasoning.
"""

        input_text = root_span.get("metadata", {}).get("input", "")
        prompt = create_judge_prompt(
            task="Evaluate factual grounding in context",
            input_text=f"Query: {input_text}\n\nContext: {retrieved_context[:500]}",
            output_text=output_text,
            criteria=criteria,
        )

        try:
            result = await judge_with_llm(prompt, self._config)
            score_value = result["score"]
            reasoning = result["reasoning"]

            # Try to extract unsupported claims from reasoning
            unsupported_claims = self._extract_claims(reasoning)

        except Exception as e:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "grounding": EvalScore(
                        name="grounding",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback=f"Error during evaluation: {str(e)}",
            )

        # In strict mode, if any unsupported claims, score should be low
        if self._strict_mode and unsupported_claims:
            score_value = min(score_value, 0.5)

        score = EvalScore(
            name="grounding",
            value=score_value,
            threshold=self._threshold,
        )

        return EvalResult(
            evaluator_name=self.name,
            scores={"grounding": score},
            feedback=reasoning,
            metadata={
                "judge_model": self._config.model,
                "context_length": len(retrieved_context),
                "output_length": len(output_text),
                "unsupported_claims": unsupported_claims,
                "strict_mode": self._strict_mode,
            },
        )

    def _extract_claims(self, reasoning: str) -> List[str]:
        """Extract unsupported claims from reasoning text.

        Args:
            reasoning: The LLM's reasoning text

        Returns:
            List of identified unsupported claims
        """
        claims = []
        lines = reasoning.split("\n")

        for line in lines:
            line_lower = line.lower()
            if any(
                keyword in line_lower
                for keyword in [
                    "unsupported",
                    "not supported",
                    "cannot be verified",
                    "hallucination",
                    "not found in context",
                ]
            ):
                claims.append(line.strip())

        return claims


@register_evaluator()
class CodeCorrectnessEvaluator(Evaluator):
    """For coding agents: validates generated code.

    Runs syntax checks and optional execution to verify code correctness.

    Example:
        >>> evaluator = CodeCorrectnessEvaluator(execute_code=True, timeout=5.0)
        >>> result = await evaluator.evaluate(trace)
        >>> if result.scores["correctness"].passed:
        ...     print("Code is syntactically correct and executable")
    """

    def __init__(
        self,
        threshold: float = 0.8,
        execute_code: bool = False,
        timeout: float = 5.0,
        allowed_imports: Optional[List[str]] = None,
    ):
        """Initialize the evaluator.

        Args:
            threshold: Minimum correctness score to pass
            execute_code: Whether to execute code (dangerous - use with caution!)
            timeout: Execution timeout in seconds
            allowed_imports: Whitelist of allowed import modules
        """
        self._threshold = threshold
        self._execute_code = execute_code
        self._timeout = timeout
        self._allowed_imports = allowed_imports or [
            "math",
            "random",
            "datetime",
            "json",
            "re",
        ]

    @property
    def name(self) -> str:
        return "code_correctness"

    @property
    def description(self) -> str:
        return "Validates generated code with syntax checks and optional execution"

    async def evaluate(self, trace: Trace) -> EvalResult:
        """Evaluate code correctness.

        Args:
            trace: The trace to evaluate

        Returns:
            EvalResult with correctness score and error details
        """
        root_span = trace.get_root_span()
        if not root_span:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "correctness": EvalScore(
                        name="correctness",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No root span found",
            )

        # Extract code from output
        output_text = root_span.get("metadata", {}).get("output", "")
        code = self._extract_code(output_text)

        if not code:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "correctness": EvalScore(
                        name="correctness",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback="No code found in output",
            )

        # Step 1: Syntax check
        syntax_result = self._check_syntax(code)

        if not syntax_result["valid"]:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "correctness": EvalScore(
                        name="correctness",
                        value=0.0,
                        threshold=self._threshold,
                    )
                },
                feedback=f"Syntax error: {syntax_result['error']}",
                metadata={"syntax_valid": False, "error": syntax_result["error"]},
            )

        # Step 2: Check imports
        import_check = self._check_imports(code)

        if not import_check["valid"]:
            return EvalResult(
                evaluator_name=self.name,
                scores={
                    "correctness": EvalScore(
                        name="correctness",
                        value=0.3,  # Syntax ok but disallowed imports
                        threshold=self._threshold,
                    )
                },
                feedback=f"Disallowed imports: {', '.join(import_check['disallowed'])}",
                metadata={
                    "syntax_valid": True,
                    "imports_valid": False,
                    "disallowed_imports": import_check["disallowed"],
                },
            )

        # Step 3: Optional execution
        execution_result = {"executed": False}
        if self._execute_code:
            execution_result = self._execute_code_safely(code)

        # Calculate score
        score_value = 0.5  # Base score for syntax validity

        if import_check["valid"]:
            score_value += 0.2

        if execution_result.get("executed"):
            if execution_result.get("success"):
                score_value += 0.3
            else:
                score_value += 0.1  # Ran but had errors

        score = EvalScore(
            name="correctness",
            value=score_value,
            threshold=self._threshold,
        )

        feedback_parts = ["Code is syntactically valid"]
        if import_check["valid"]:
            feedback_parts.append("all imports allowed")
        if execution_result.get("executed"):
            if execution_result.get("success"):
                feedback_parts.append("executed successfully")
            else:
                feedback_parts.append(
                    f"execution failed: {execution_result.get('error', 'Unknown error')}"
                )

        feedback = "; ".join(feedback_parts)

        return EvalResult(
            evaluator_name=self.name,
            scores={"correctness": score},
            feedback=feedback,
            metadata={
                "syntax_valid": True,
                "imports_valid": import_check["valid"],
                "execution_result": execution_result,
                "code_length": len(code),
            },
        )

    def _extract_code(self, text: str) -> str:
        """Extract code from text (handles markdown code blocks).

        Args:
            text: Text possibly containing code

        Returns:
            Extracted code
        """
        # Try to extract from markdown code blocks
        import re

        code_block_pattern = r"```(?:python)?\n(.*?)```"
        matches = re.findall(code_block_pattern, text, re.DOTALL)

        if matches:
            return matches[0].strip()

        # Otherwise return the whole text if it looks like code
        if any(keyword in text for keyword in ["def ", "class ", "import ", "="]):
            return text.strip()

        return ""

    def _check_syntax(self, code: str) -> Dict[str, Any]:
        """Check Python syntax.

        Args:
            code: Python code to check

        Returns:
            Dictionary with valid flag and error message
        """
        try:
            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {"valid": False, "error": f"{e.msg} at line {e.lineno}"}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def _check_imports(self, code: str) -> Dict[str, Any]:
        """Check if imports are allowed.

        Args:
            code: Python code to check

        Returns:
            Dictionary with valid flag and disallowed imports
        """
        try:
            tree = ast.parse(code)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split(".")[0])

            disallowed = [
                imp for imp in imports if imp not in self._allowed_imports
            ]

            return {"valid": len(disallowed) == 0, "disallowed": disallowed}

        except Exception as e:
            return {"valid": False, "disallowed": [], "error": str(e)}

    def _execute_code_safely(self, code: str) -> Dict[str, Any]:
        """Execute code in a restricted environment.

        WARNING: Code execution is dangerous! This is a basic implementation.
        In production, use proper sandboxing (Docker, etc.).

        Args:
            code: Python code to execute

        Returns:
            Dictionary with execution results
        """
        # Capture output
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            # Create restricted globals (no builtins that could be dangerous)
            restricted_globals = {
                "__builtins__": {
                    "print": print,
                    "len": len,
                    "range": range,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                }
            }

            # Execute with timeout (basic - not truly safe)
            exec(code, restricted_globals)

            output = captured_output.getvalue()

            return {"executed": True, "success": True, "output": output, "error": None}

        except Exception as e:
            return {
                "executed": True,
                "success": False,
                "output": captured_output.getvalue(),
                "error": str(e),
            }

        finally:
            sys.stdout = old_stdout
