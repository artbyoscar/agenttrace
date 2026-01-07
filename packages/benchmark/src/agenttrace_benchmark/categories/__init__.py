"""
Benchmark Category Definitions for AgentTrace

This module defines the core evaluation categories used to assess AI agent capabilities.
Each category represents a fundamental dimension of agent performance with clear
evaluation criteria grounded in cognitive science and AI research.

Academic Foundation:
- REASONING: Based on dual-process theory (Kahneman, 2011) and computational models
  of human reasoning (Johnson-Laird, 2010)
- TOOL_USE: Grounded in instrumental action theory and tool affordance research
  (Gibson, 1979; Norman, 1988)
- PLANNING: Built on hierarchical task network (HTN) planning literature (Erol et al., 1994)
  and Bayesian models of planning under uncertainty (Botvinick & Weinstein, 2014)
- GROUNDING: Based on symbol grounding problem (Harnad, 1990) and semantic web research
- ROBUSTNESS: Informed by adversarial ML literature (Goodfellow et al., 2014) and
  distributional shift research (Quionero-Candela et al., 2009)
- EFFICIENCY: Grounded in computational complexity theory and bounded rationality
  (Simon, 1972)
"""

from enum import Enum
from typing import Dict, List
from dataclasses import dataclass


class BenchmarkCategory(str, Enum):
    """
    Primary evaluation categories for AI agent capabilities.

    Each category represents a distinct cognitive capability that can be
    independently measured and optimized. Categories are designed to be:
    - Mutually exclusive in their core focus
    - Collectively exhaustive of agent capabilities
    - Operationally measurable with objective criteria
    - Relevant to both academic research and industry applications
    """

    REASONING = "reasoning"
    TOOL_USE = "tool_use"
    PLANNING = "planning"
    GROUNDING = "grounding"
    ROBUSTNESS = "robustness"
    EFFICIENCY = "efficiency"


@dataclass
class CategoryDefinition:
    """
    Comprehensive definition of a benchmark category including evaluation criteria.

    Attributes:
        name: Category identifier
        display_name: Human-readable category name
        description: Detailed explanation of what this category measures
        subcategories: Specific skills within this category
        evaluation_dimensions: Metrics used to assess performance
        academic_references: Key papers establishing theoretical foundation
        example_tasks: Representative task types in this category
        weight: Default weight in composite scoring (sum to 1.0 across categories)
    """

    name: BenchmarkCategory
    display_name: str
    description: str
    subcategories: List[str]
    evaluation_dimensions: List[str]
    academic_references: List[str]
    example_tasks: List[str]
    weight: float


# Complete category specifications with academic rigor
CATEGORY_DEFINITIONS: Dict[BenchmarkCategory, CategoryDefinition] = {
    BenchmarkCategory.REASONING: CategoryDefinition(
        name=BenchmarkCategory.REASONING,
        display_name="Multi-Step Reasoning",
        description=(
            "Evaluates the agent's ability to perform logical inference, decompose "
            "complex problems into sub-problems, and chain together reasoning steps "
            "to reach valid conclusions. Distinguishes between System 1 (fast, intuitive) "
            "and System 2 (slow, deliberate) reasoning patterns."
        ),
        subcategories=[
            "deductive_reasoning",      # Logical deduction from premises
            "inductive_reasoning",       # Pattern recognition and generalization
            "abductive_reasoning",       # Inference to best explanation
            "analogical_reasoning",      # Transfer from similar problems
            "causal_reasoning",          # Understanding cause-effect relationships
            "counterfactual_reasoning",  # Reasoning about hypotheticals
            "mathematical_reasoning",    # Quantitative problem solving
            "spatial_reasoning",         # Mental rotation and spatial relationships
        ],
        evaluation_dimensions=[
            "correctness",               # Logical validity of conclusions
            "reasoning_depth",           # Number of inference steps
            "premise_tracking",          # Accurate use of given information
            "consistency",               # Freedom from contradictions
            "completeness",              # Coverage of solution space
        ],
        academic_references=[
            "Kahneman, D. (2011). Thinking, Fast and Slow.",
            "Johnson-Laird, P. N. (2010). Mental models and human reasoning.",
            "Rips, L. J. (1994). The Psychology of Proof.",
            "Wei, J. et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in LLMs.",
        ],
        example_tasks=[
            "Multi-hop question answering requiring inference chains",
            "Mathematical word problems with implicit constraints",
            "Logic puzzles (Einstein's riddle, Knights and Knaves)",
            "Code debugging requiring backward reasoning",
        ],
        weight=0.20,
    ),

    BenchmarkCategory.TOOL_USE: CategoryDefinition(
        name=BenchmarkCategory.TOOL_USE,
        display_name="Tool Selection and Orchestration",
        description=(
            "Assesses the agent's capability to select appropriate tools from a toolkit, "
            "compose tools into workflows, handle tool failures gracefully, and recover "
            "from errors. Evaluates understanding of tool affordances, preconditions, "
            "and postconditions."
        ),
        subcategories=[
            "tool_selection",            # Choosing correct tool for task
            "parameter_binding",         # Correctly specifying tool inputs
            "tool_composition",          # Chaining multiple tools
            "error_detection",           # Recognizing tool failures
            "error_recovery",            # Adapting when tools fail
            "tool_learning",             # Understanding new tools from documentation
            "parallel_execution",        # Using multiple tools concurrently
            "resource_management",       # Managing API quotas, rate limits
        ],
        evaluation_dimensions=[
            "tool_appropriateness",      # Selecting optimal tool for task
            "parameter_accuracy",        # Correct argument specification
            "error_handling",            # Graceful failure recovery
            "efficiency",                # Minimal tool calls to completion
            "creativity",                # Novel tool combinations
        ],
        academic_references=[
            "Gibson, J. J. (1979). The Ecological Approach to Visual Perception.",
            "Norman, D. A. (1988). The Psychology of Everyday Things.",
            "Schick, K. D., & Toth, N. (1993). Making Silent Stones Speak.",
            "Schick, T. et al. (2023). Toolformer: Language Models Can Teach Themselves to Use Tools.",
        ],
        example_tasks=[
            "API composition tasks requiring authentication and data transformation",
            "File system operations with permission handling",
            "Database queries with fallback strategies",
            "Multi-modal tasks combining vision, code, and search tools",
        ],
        weight=0.20,
    ),

    BenchmarkCategory.PLANNING: CategoryDefinition(
        name=BenchmarkCategory.PLANNING,
        display_name="Goal-Directed Planning",
        description=(
            "Measures the agent's ability to decompose high-level goals into executable "
            "action sequences, track progress toward goals, replan when circumstances "
            "change, and handle uncertainty in outcomes. Tests hierarchical planning, "
            "partial observability, and plan optimization."
        ),
        subcategories=[
            "task_decomposition",        # Breaking goals into subgoals
            "action_sequencing",         # Ordering actions correctly
            "goal_tracking",             # Monitoring progress
            "replanning",                # Adapting to failures
            "partial_observability",     # Planning with incomplete information
            "resource_optimization",     # Minimizing costs while achieving goals
            "multi_agent_coordination",  # Planning with other agents
            "temporal_planning",         # Scheduling with time constraints
        ],
        evaluation_dimensions=[
            "goal_achievement",          # Successfully reaching objectives
            "plan_quality",              # Optimality of action sequence
            "adaptability",              # Successful replanning rate
            "foresight",                 # Anticipating obstacles
            "efficiency",                # Plan length and resource usage
        ],
        academic_references=[
            "Erol, K. et al. (1994). HTN Planning: Complexity and Expressivity.",
            "Botvinick, M., & Weinstein, A. (2014). Model-based hierarchical RL.",
            "Ghallab, M. et al. (2004). Automated Planning: Theory and Practice.",
            "Yao, S. et al. (2023). Tree of Thoughts: Deliberate Problem Solving with LLMs.",
        ],
        example_tasks=[
            "Travel itinerary planning with budget constraints",
            "Software refactoring with backward compatibility requirements",
            "Research task planning with unknown paper availability",
            "Resource allocation in multi-objective optimization",
        ],
        weight=0.18,
    ),

    BenchmarkCategory.GROUNDING: CategoryDefinition(
        name=BenchmarkCategory.GROUNDING,
        display_name="Factual Grounding and Attribution",
        description=(
            "Evaluates the agent's commitment to factual accuracy, ability to cite "
            "sources, distinguish between known facts and speculation, and resist "
            "hallucination. Tests calibration of confidence with correctness and "
            "appropriate handling of knowledge boundaries."
        ),
        subcategories=[
            "factual_accuracy",          # Correctness of factual claims
            "source_attribution",        # Citing information sources
            "hallucination_resistance",  # Avoiding fabricated information
            "knowledge_boundaries",      # Recognizing unknowns
            "confidence_calibration",    # Matching confidence to accuracy
            "claim_verification",        # Checking facts before stating
            "temporal_awareness",        # Knowing when information is outdated
            "context_sensitivity",       # Using relevant context correctly
        ],
        evaluation_dimensions=[
            "factual_correctness",       # Percentage of accurate claims
            "citation_accuracy",         # Correct source attribution
            "hallucination_rate",        # Frequency of fabrications
            "calibration_error",         # ECE between confidence and accuracy
            "appropriate_uncertainty",   # Expressing doubt when warranted
        ],
        academic_references=[
            "Harnad, S. (1990). The Symbol Grounding Problem.",
            "Grice, H. P. (1975). Logic and Conversation.",
            "Maynez, J. et al. (2020). On Faithfulness and Factuality in Abstractive Summarization.",
            "Lin, S. et al. (2022). TruthfulQA: Measuring How Models Mimic Human Falsehoods.",
        ],
        example_tasks=[
            "Multi-source fact verification with conflicting information",
            "Historical question answering requiring temporal reasoning",
            "Scientific claim validation with citation requirements",
            "News article summarization preserving factual accuracy",
        ],
        weight=0.18,
    ),

    BenchmarkCategory.ROBUSTNESS: CategoryDefinition(
        name=BenchmarkCategory.ROBUSTNESS,
        display_name="Adversarial Robustness",
        description=(
            "Tests the agent's performance under distribution shift, adversarial inputs, "
            "edge cases, and deliberately misleading prompts. Measures consistency across "
            "paraphrases, resistance to prompt injection, and graceful degradation under "
            "challenging conditions."
        ),
        subcategories=[
            "adversarial_resistance",    # Handling malicious inputs
            "prompt_injection_defense",  # Resisting instruction hijacking
            "distribution_shift",        # Performance on OOD inputs
            "edge_case_handling",        # Dealing with unusual scenarios
            "consistency",               # Stable outputs for equivalent inputs
            "input_validation",          # Recognizing invalid requests
            "graceful_degradation",      # Failing safely
            "security_awareness",        # Avoiding harmful behaviors
        ],
        evaluation_dimensions=[
            "adversarial_accuracy",      # Correctness on adversarial inputs
            "consistency_score",         # Agreement across paraphrases
            "injection_resistance",      # Rejection of prompt attacks
            "safety_compliance",         # Avoiding harmful outputs
            "ood_performance",           # Accuracy on shifted distributions
        ],
        academic_references=[
            "Goodfellow, I. J. et al. (2014). Explaining and Harnessing Adversarial Examples.",
            "Quionero-Candela, J. et al. (2009). Dataset Shift in Machine Learning.",
            "Perez, F., & Ribeiro, I. (2022). Ignore Previous Prompt: Attack Techniques.",
            "Zou, A. et al. (2023). Universal and Transferable Adversarial Attacks on Aligned LLMs.",
        ],
        example_tasks=[
            "Question answering with adversarial context insertion",
            "Code generation with malicious requirements embedded",
            "Instruction following with prompt injection attempts",
            "Classification under distributional shift",
        ],
        weight=0.12,
    ),

    BenchmarkCategory.EFFICIENCY: CategoryDefinition(
        name=BenchmarkCategory.EFFICIENCY,
        display_name="Resource Efficiency",
        description=(
            "Quantifies the agent's ability to achieve goals with minimal resource "
            "expenditure including tokens, API calls, time, and compute. Evaluates "
            "whether agents can solve problems efficiently without sacrificing quality, "
            "implementing principles of bounded rationality."
        ),
        subcategories=[
            "token_economy",             # Minimal tokens to solution
            "latency_optimization",      # Fast response times
            "api_call_minimization",     # Fewest external calls
            "caching_utilization",       # Reusing prior computations
            "parallel_execution",        # Concurrent operations
            "early_termination",         # Stopping when sufficient
            "lazy_evaluation",           # Computing only what's needed
            "resource_budgeting",        # Operating within constraints
        ],
        evaluation_dimensions=[
            "token_efficiency",          # Tokens used / baseline
            "time_efficiency",           # Completion time / baseline
            "call_efficiency",           # API calls / baseline
            "quality_maintained",        # No accuracy sacrifice
            "scalability",               # Performance on larger inputs
        ],
        academic_references=[
            "Simon, H. A. (1972). Theories of Bounded Rationality.",
            "Russell, S., & Wefald, E. (1991). Principles of Metareasoning.",
            "Zilberstein, S. (1996). Using Anytime Algorithms in Intelligent Systems.",
            "Khattab, O. et al. (2023). DSPy: Compiling Declarative Language Model Calls.",
        ],
        example_tasks=[
            "Information retrieval with token budgets",
            "Code optimization under latency constraints",
            "Data processing with API rate limits",
            "Question answering with early stopping criteria",
        ],
        weight=0.12,
    ),
}


def get_category_definition(category: BenchmarkCategory) -> CategoryDefinition:
    """
    Retrieve the complete definition for a benchmark category.

    Args:
        category: The category to look up

    Returns:
        Complete category definition with evaluation criteria

    Raises:
        KeyError: If category is not defined
    """
    return CATEGORY_DEFINITIONS[category]


def list_all_subcategories() -> Dict[BenchmarkCategory, List[str]]:
    """
    Get mapping of all categories to their subcategories.

    Returns:
        Dictionary mapping each category to its list of subcategories
    """
    return {
        category: definition.subcategories
        for category, definition in CATEGORY_DEFINITIONS.items()
    }


def validate_category_weights() -> bool:
    """
    Verify that category weights sum to 1.0 for composite scoring.

    Returns:
        True if weights are valid, False otherwise
    """
    total_weight = sum(defn.weight for defn in CATEGORY_DEFINITIONS.values())
    return abs(total_weight - 1.0) < 1e-6


__all__ = [
    "BenchmarkCategory",
    "CategoryDefinition",
    "CATEGORY_DEFINITIONS",
    "get_category_definition",
    "list_all_subcategories",
    "validate_category_weights",
]
