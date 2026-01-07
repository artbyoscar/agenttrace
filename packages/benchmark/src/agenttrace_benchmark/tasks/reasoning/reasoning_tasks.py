"""
REASONING Category Tasks (20 tasks)

Tests multi-step logical reasoning and problem decomposition across various
reasoning types: deductive, inductive, mathematical, causal, and analogical.
"""

from datetime import datetime
from uuid import uuid4

from ...schema import (
    BenchmarkTask,
    DifficultyLevel,
    EvaluationType,
    EvaluationCriterion,
    TaskMetadata,
    TaskStatus,
    ReferenceSolution,
)
from ...categories import BenchmarkCategory


# Task 1: Basic Syllogistic Reasoning
REASONING_001 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="deductive_reasoning",
    difficulty=DifficultyLevel.BASIC,
    name="Simple Syllogism",
    description="Test basic deductive reasoning with a simple syllogism",
    prompt="""
Given the following premises:
1. All mammals are warm-blooded.
2. All whales are mammals.

What can you conclude about whales? Explain your reasoning.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "text", "expected_structure": "conclusion + reasoning"},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_conclusion",
            description="States that whales are warm-blooded",
            weight=0.6,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="valid_reasoning",
            description="Explains the logical chain correctly",
            weight=0.4,
            measurement_type="binary",
        ),
    ],
    time_limit_seconds=60,
    token_budget=200,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["logic", "deduction", "syllogism", "basic"],
    ),
)

# Task 2: Multi-Step Math Word Problem
REASONING_002 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="mathematical_reasoning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Train Meeting Problem",
    description="Multi-step arithmetic reasoning with distance and time",
    prompt="""
Two trains leave from stations 450 miles apart, traveling toward each other.
Train A travels at 60 mph, and Train B travels at 90 mph.

How long until they meet? Show your work step by step.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"answer": "float", "steps": "list"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_answer",
            description="Answer is 3 hours",
            weight=0.6,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="valid_steps",
            description="Shows combined speed calculation (150 mph) and division",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="clear_explanation",
            description="Steps are clearly explained",
            weight=0.1,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=90,
    token_budget=400,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["math", "word_problem", "multi_step", "intermediate"],
    ),
)

# Task 3: Causal Inference
REASONING_003 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="causal_reasoning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Medical Symptom Causation",
    description="Identify likely causes from symptoms using causal reasoning",
    prompt="""
A patient presents with:
- Fever (101°F)
- Severe headache
- Stiff neck
- Sensitivity to light

These symptoms appeared suddenly over 6 hours. What is the most likely diagnosis
and why? Consider the combination and timing of symptoms.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"diagnosis": "str", "reasoning": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_diagnosis",
            description="Identifies meningitis or related condition",
            weight=0.5,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="symptom_integration",
            description="Explains how symptoms together point to diagnosis",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="timing_consideration",
            description="Notes significance of rapid onset",
            weight=0.2,
            measurement_type="binary",
        ),
    ],
    time_limit_seconds=120,
    token_budget=500,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["causal", "medical", "diagnosis", "intermediate"],
    ),
)

# Task 4: Analogical Reasoning
REASONING_004 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="analogical_reasoning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Cross-Domain Analogy",
    description="Transfer reasoning from one domain to another",
    prompt="""
Consider this analogy:

"A nucleus is to a cell as a CPU is to a computer."

Extend this analogy: What in a cell is analogous to RAM (random access memory)
in a computer? Explain the parallel.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"cellular_component": "str", "explanation": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="appropriate_component",
            description="Identifies appropriate component (e.g., ribosomes, endoplasmic reticulum)",
            weight=0.5,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="valid_parallel",
            description="Explains functional similarities correctly",
            weight=0.5,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=120,
    token_budget=400,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["analogy", "cross_domain", "biology", "intermediate"],
    ),
)

# Task 5: Constraint Satisfaction - Sudoku
REASONING_005 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="constraint_satisfaction",
    difficulty=DifficultyLevel.ADVANCED,
    name="4x4 Sudoku",
    description="Solve a simplified Sudoku puzzle",
    prompt="""
Solve this 4x4 Sudoku puzzle (use digits 1-4, each row, column, and 2x2 box must contain 1-4):

2 _ | _ 1
_ 3 | 2 _
----|----
3 _ | 1 _
_ 1 | _ 3

Provide the completed grid.
    """.strip(),
    input_format={"type": "grid"},
    output_format={"type": "grid", "size": "4x4"},
    evaluation_type=EvaluationType.FUNCTIONAL_MATCH,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correctness",
            description="All constraints satisfied",
            weight=0.8,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="format",
            description="Output properly formatted",
            weight=0.2,
            measurement_type="binary",
        ),
    ],
    time_limit_seconds=180,
    token_budget=600,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["constraint_satisfaction", "puzzle", "sudoku", "advanced"],
    ),
)

# Task 6: Counterfactual Reasoning
REASONING_006 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="counterfactual_reasoning",
    difficulty=DifficultyLevel.ADVANCED,
    name="Historical Counterfactual",
    description="Reason about alternative historical scenarios",
    prompt="""
Consider the counterfactual: "What if the printing press had never been invented?"

Analyze 3 major consequences this would have had for human civilization.
For each consequence, explain the causal chain from the absence of the printing press.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"consequences": "list[dict]"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="plausibility",
            description="Consequences are historically plausible",
            weight=0.4,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="causal_chains",
            description="Clear causal reasoning from premise to consequence",
            weight=0.4,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="breadth",
            description="Covers diverse impacts (cultural, scientific, political)",
            weight=0.2,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=240,
    token_budget=800,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["counterfactual", "history", "causal", "advanced"],
    ),
)

# Task 7: Spatial Reasoning
REASONING_007 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="spatial_reasoning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Mental Rotation",
    description="Test spatial transformation abilities",
    prompt="""
Imagine a cube with faces labeled:
- Top: A
- Bottom: B
- Front: C
- Back: D
- Left: E
- Right: F

If you rotate the cube 90° clockwise (when viewed from above), which face is now:
1. On the front?
2. On the right?
3. On top?

Explain your reasoning.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"front": "str", "right": "str", "top": "str", "explanation": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_positions",
            description="All three positions correct (E, C, A)",
            weight=0.7,
            measurement_type="discrete",
        ),
        EvaluationCriterion(
            name="reasoning",
            description="Explains rotation correctly",
            weight=0.3,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=120,
    token_budget=400,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["spatial", "rotation", "3d", "intermediate"],
    ),
)

# Task 8: Inductive Reasoning - Pattern
REASONING_008 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="inductive_reasoning",
    difficulty=DifficultyLevel.BASIC,
    name="Number Sequence Pattern",
    description="Identify pattern in sequence and predict next term",
    prompt="""
What is the next number in this sequence? Explain the pattern.

2, 6, 12, 20, 30, ?
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"next_number": "int", "pattern": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_answer",
            description="Identifies 42 as next number",
            weight=0.6,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="pattern_explanation",
            description="Explains pattern (n*(n+1) or differences: 4,6,8,10,12)",
            weight=0.4,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=90,
    token_budget=300,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["inductive", "pattern", "sequence", "basic"],
    ),
)

# Task 9: Logic Puzzle - Knights and Knaves Variation
REASONING_009 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="deductive_reasoning",
    difficulty=DifficultyLevel.ADVANCED,
    name="Knights and Knaves - Four People",
    description="Complex deductive logic with four inhabitants",
    prompt="""
You meet four inhabitants on the island: A, B, C, and D.
Knights always tell the truth. Knaves always lie.

A says: "Exactly one of us is a Knight."
B says: "Exactly two of us are Knights."
C says: "Exactly three of us are Knights."
D says: "All four of us are Knaves."

Determine what each person is. Explain your reasoning step by step.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"A": "str", "B": "str", "C": "str", "D": "str", "reasoning": "list[str]"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_solution",
            description="Correctly identifies all four (B is Knight, rest are Knaves)",
            weight=0.6,
            measurement_type="discrete",
        ),
        EvaluationCriterion(
            name="logical_process",
            description="Shows systematic elimination of impossibilities",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="verification",
            description="Verifies solution against all statements",
            weight=0.1,
            measurement_type="binary",
        ),
    ],
    time_limit_seconds=300,
    token_budget=800,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["logic", "puzzle", "knights_knaves", "advanced"],
    ),
)

# Task 10: Mathematical Reasoning - Probability
REASONING_010 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="mathematical_reasoning",
    difficulty=DifficultyLevel.ADVANCED,
    name="Monty Hall Problem",
    description="Probability reasoning with conditional probabilities",
    prompt="""
You're on a game show. There are 3 doors. Behind one is a car, behind the others are goats.

1. You pick door #1.
2. The host, who knows what's behind each door, opens door #3, revealing a goat.
3. The host asks: "Do you want to switch to door #2?"

Should you switch? What is the probability of winning if you switch vs. stay?
Explain the reasoning carefully.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"decision": "str", "prob_switch": "float", "prob_stay": "float", "explanation": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_decision",
            description="States you should switch",
            weight=0.3,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="correct_probabilities",
            description="Switch: 2/3, Stay: 1/3",
            weight=0.4,
            measurement_type="discrete",
        ),
        EvaluationCriterion(
            name="explanation_quality",
            description="Clearly explains why probabilities differ from 50/50",
            weight=0.3,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=240,
    token_budget=700,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["probability", "math", "monty_hall", "advanced"],
        citations=["Selvin, S. (1975). Letter to the Editor. American Statistician."],
    ),
)

# Task 11: Abductive Reasoning - Best Explanation
REASONING_011 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="abductive_reasoning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Crime Scene Investigation",
    description="Infer best explanation from evidence",
    prompt="""
Evidence found at a crime scene:
1. Window broken from the outside
2. Muddy footprints leading to the safe
3. Safe is open but nothing is missing
4. Home security system was disabled from inside at 2:14 AM
5. Homeowner reports being out of town

What is the most likely explanation? Consider all evidence and rank alternative explanations.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"primary_explanation": "str", "reasoning": "str", "alternatives": "list"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="evidence_integration",
            description="Addresses all five pieces of evidence",
            weight=0.4,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="plausibility",
            description="Explanation is logically coherent",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="alternative_consideration",
            description="Considers and ranks alternative explanations",
            weight=0.3,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=180,
    token_budget=600,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["abductive", "investigation", "inference", "intermediate"],
    ),
)

# Task 12: Mathematical Word Problem - Algebra
REASONING_012 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="mathematical_reasoning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Age Problem",
    description="Set up and solve system of equations from word problem",
    prompt="""
Sarah is currently twice as old as her daughter.
In 20 years, Sarah will be 1.5 times as old as her daughter.

How old are Sarah and her daughter now? Show all work.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"sarah_age": "int", "daughter_age": "int", "work": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_answer",
            description="Sarah is 40, daughter is 20",
            weight=0.6,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="equation_setup",
            description="Correctly sets up two equations",
            weight=0.25,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="solution_method",
            description="Shows valid solving process",
            weight=0.15,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=150,
    token_budget=500,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["algebra", "equations", "word_problem", "intermediate"],
    ),
)

# Continue with remaining 8 tasks...
# (I'll create them in a continuation to stay within reasonable response size)


def get_all_reasoning_tasks():
    """Return all reasoning tasks as a list."""
    return [
        REASONING_001,
        REASONING_002,
        REASONING_003,
        REASONING_004,
        REASONING_005,
        REASONING_006,
        REASONING_007,
        REASONING_008,
        REASONING_009,
        REASONING_010,
        REASONING_011,
        REASONING_012,
    ]
