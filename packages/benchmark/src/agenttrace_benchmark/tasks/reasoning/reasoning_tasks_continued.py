"""
REASONING Category Tasks - Continued (Tasks 13-20)
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
)
from ...categories import BenchmarkCategory


# Task 13: Deductive Logic - Formal Logic
REASONING_013 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="deductive_reasoning",
    difficulty=DifficultyLevel.EXPERT,
    name="Formal Logic Proof",
    description="Construct formal logical proof",
    prompt="""
Prove the following using formal logic rules:

Given:
1. If it rains, the ground gets wet. (R → W)
2. If the ground is wet, it's slippery. (W → S)
3. It rained. (R)

Prove: It's slippery. (S)

Show each step with the rule applied (Modus Ponens, etc.).
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"steps": "list[dict]", "conclusion": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_conclusion",
            description="Derives S correctly",
            weight=0.4,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="valid_steps",
            description="Each inference step is valid",
            weight=0.4,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="rule_naming",
            description="Correctly names logical rules used",
            weight=0.2,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=180,
    token_budget=500,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["formal_logic", "proof", "deduction", "expert"],
    ),
)

# Task 14: Combinatorial Reasoning
REASONING_014 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="mathematical_reasoning",
    difficulty=DifficultyLevel.ADVANCED,
    name="Meeting Scheduling",
    description="Combinatorial problem with constraints",
    prompt="""
5 people (A, B, C, D, E) need to schedule a meeting. Each person has availability constraints:

- A: Available Monday, Wednesday, Friday
- B: Available Monday, Tuesday, Thursday
- C: Available Tuesday, Wednesday, Thursday
- D: Available Monday, Thursday, Friday
- E: Available Wednesday, Thursday, Friday

Find all possible days when all 5 can meet. If no such day exists, find the maximum
number of people who can meet on each day.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"all_available": "list", "max_per_day": "dict"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="all_available_days",
            description="Correctly identifies days all can meet (Thursday)",
            weight=0.5,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="max_attendance",
            description="Correctly counts max attendance per day",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="method",
            description="Shows systematic approach (set intersection, etc.)",
            weight=0.2,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=180,
    token_budget=600,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["combinatorial", "scheduling", "constraints", "advanced"],
    ),
)

# Task 15: Causal Chains
REASONING_015 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="causal_reasoning",
    difficulty=DifficultyLevel.ADVANCED,
    name="Environmental Cascade",
    description="Trace multi-step causal chain",
    prompt="""
Given: A factory releases pollutants into a river.

Trace the causal chain through at least 5 steps to potential human health impacts.
For each step, explain the mechanism of causation.

Example format:
Step 1: Factory pollutants enter river → [mechanism] → Step 2: ...
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"causal_chain": "list[dict]"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="chain_length",
            description="Provides at least 5 connected steps",
            weight=0.3,
            measurement_type="discrete",
        ),
        EvaluationCriterion(
            name="causal_validity",
            description="Each causal link is scientifically plausible",
            weight=0.4,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="mechanism_explanation",
            description="Explains HOW each step causes the next",
            weight=0.3,
            measurement_type="continuous",
        ),
    ],
    time_limit_seconds=300,
    token_budget=800,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["causal", "environment", "chain", "advanced"],
    ),
)

# Task 16: Analogical Transfer
REASONING_016 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="analogical_reasoning",
    difficulty=DifficultyLevel.EXPERT,
    name="Problem Solution Transfer",
    description="Apply solution from one domain to analogous problem in another",
    prompt="""
Consider this solved problem:

PROBLEM A (Computer Science):
A distributed system has 5 nodes that need to agree on a value. Some nodes may be
faulty. Solution: Use Byzantine Fault Tolerance with 3f+1 nodes where f is max faults.

Now solve this analogous problem:

PROBLEM B (Government):
A committee of 7 members needs to make decisions, but some members may be corrupt.
How many members are needed to guarantee honest majority decisions if up to 2 members
might be corrupt?

Explain the analogy and solution transfer.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"answer": "int", "analogy_mapping": "dict", "explanation": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_answer",
            description="Identifies need for at least 7 members (3*2+1)",
            weight=0.4,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="analogy_mapping",
            description="Maps concepts correctly (nodes→members, faulty→corrupt, etc.)",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="formula_transfer",
            description="Correctly applies 3f+1 formula to new domain",
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
        tags=["analogy", "transfer", "cross_domain", "expert"],
    ),
)

# Task 17: Inductive Generalization
REASONING_017 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="inductive_reasoning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Rule Induction from Examples",
    description="Induce general rule from specific examples",
    prompt="""
Observe these examples:

Input: "cat" → Output: "atcay"
Input: "dog" → Output: "ogday"
Input: "apple" → Output: "appleay"
Input: "egg" → Output: "eggay"

What is the rule? Apply it to: "string"
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"rule": "str", "application": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_rule",
            description="Identifies Pig Latin rule correctly",
            weight=0.5,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="correct_application",
            description="Applies to 'string' correctly (ingstray or ingstray)",
            weight=0.5,
            measurement_type="binary",
        ),
    ],
    time_limit_seconds=120,
    token_budget=400,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["inductive", "rule_learning", "pattern", "intermediate"],
    ),
)

# Task 18: Multi-Step Logic Puzzle
REASONING_018 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="deductive_reasoning",
    difficulty=DifficultyLevel.EXPERT,
    name="Einstein's Riddle Simplified",
    description="Complex deductive puzzle with multiple constraints",
    prompt="""
Five houses in a row, each a different color. In each lives a person of different nationality.

Clues:
1. The Brit lives in the red house
2. The Swede keeps dogs
3. The Dane drinks tea
4. The green house is immediately to the left of the white house
5. The green house's owner drinks coffee
6. The Norwegian lives in the first house
7. The German owns the fish

Which nationality drinks water? Which nationality owns the horse?

Show your deduction process.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"water_drinker": "str", "horse_owner": "str", "deduction": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_answers",
            description="Both answers correct",
            weight=0.6,
            measurement_type="discrete",
        ),
        EvaluationCriterion(
            name="systematic_approach",
            description="Shows systematic constraint propagation",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="verification",
            description="Verifies solution against all clues",
            weight=0.1,
            measurement_type="binary",
        ),
    ],
    time_limit_seconds=600,
    token_budget=1500,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["logic_puzzle", "constraints", "einstein_riddle", "expert"],
    ),
)

# Task 19: Proportional Reasoning
REASONING_019 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="mathematical_reasoning",
    difficulty=DifficultyLevel.BASIC,
    name="Recipe Scaling",
    description="Apply proportional reasoning to real-world scenario",
    prompt="""
A recipe for 4 servings requires:
- 2 cups flour
- 3 eggs
- 1.5 cups milk
- 0.5 cup sugar

How much of each ingredient for 10 servings? Show your calculation.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"ingredients": "dict", "calculation": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_scaling",
            description="All ingredients scaled correctly (multiply by 2.5)",
            weight=0.7,
            measurement_type="discrete",
        ),
        EvaluationCriterion(
            name="method_shown",
            description="Shows proportion calculation",
            weight=0.3,
            measurement_type="binary",
        ),
    ],
    time_limit_seconds=90,
    token_budget=300,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["proportion", "math", "scaling", "basic"],
    ),
)

# Task 20: Temporal Reasoning
REASONING_020 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.REASONING,
    subcategory="temporal_reasoning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Time Zone Scheduling",
    description="Reason about time zones and simultaneity",
    prompt="""
A virtual meeting needs to be scheduled for participants in:
- New York (EST, UTC-5)
- London (GMT, UTC+0)
- Tokyo (JST, UTC+9)
- Sydney (AEDT, UTC+11)

The meeting should be:
- During working hours (9 AM - 6 PM) for everyone
- On a weekday

Find all possible meeting times in 24-hour format. If none exist, explain why and
suggest the best compromise.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"possible_times": "list", "explanation": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="time_zone_calculation",
            description="Correctly calculates time differences",
            weight=0.4,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="constraint_checking",
            description="Checks all constraints for each potential time",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="solution_or_compromise",
            description="Provides solution or reasonable compromise",
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
        tags=["temporal", "time_zones", "scheduling", "intermediate"],
    ),
)


def get_reasoning_tasks_continued():
    """Return additional reasoning tasks."""
    return [
        REASONING_013,
        REASONING_014,
        REASONING_015,
        REASONING_016,
        REASONING_017,
        REASONING_018,
        REASONING_019,
        REASONING_020,
    ]
