"""Structured prompt templates for LLM-as-judge evaluations."""

# Base system prompt for all judgments
SYSTEM_PROMPT = """You are an expert evaluator assessing AI agent outputs.
Your task is to provide objective, consistent evaluations based on specific criteria.

IMPORTANT: You must respond in JSON format with this exact structure:
{
    "score": <number from 1-10>,
    "reasoning": "<detailed explanation of your score>",
    "confidence": <optional number from 0.0-1.0>
}

Be specific, fair, and consistent in your evaluations."""

# Response Completeness
COMPLETENESS_PROMPT = """# Task: Evaluate Response Completeness

## Input
User Query: {input}

## Output to Evaluate
{output}

## Evaluation Criteria
Assess how completely the output addresses the input query:

1. **All Aspects Addressed** (Score 9-10)
   - Every part of the query is answered
   - No significant gaps or omissions
   - Appropriate level of detail for each aspect

2. **Mostly Complete** (Score 7-8)
   - Major aspects covered well
   - Minor aspects may be brief or missing
   - Core questions answered satisfactorily

3. **Partially Complete** (Score 5-6)
   - Some aspects well-covered
   - Other aspects missing or superficial
   - Key information present but incomplete

4. **Incomplete** (Score 3-4)
   - Many aspects not addressed
   - Important questions left unanswered
   - Significant gaps in coverage

5. **Severely Incomplete** (Score 1-2)
   - Few or no aspects addressed
   - Fails to answer the query
   - Off-topic or irrelevant

## Few-Shot Examples

### Example 1
Input: "What is Python and why is it popular?"
Output: "Python is a programming language."
Score: 4
Reasoning: "Only addresses what Python is, but completely ignores why it's popular. Incomplete response."

### Example 2
Input: "What is Python and why is it popular?"
Output: "Python is a high-level, interpreted programming language known for its simplicity and readability. It's popular because of its easy-to-learn syntax, extensive libraries, strong community support, and versatility across domains like web development, data science, and automation."
Score: 10
Reasoning: "Fully addresses both what Python is and why it's popular with specific, relevant details."

## Your Evaluation
Provide your evaluation in JSON format."""

# Response Relevance
RELEVANCE_PROMPT = """# Task: Evaluate Response Relevance

## Input
User Query: {input}

## Output to Evaluate
{output}

## Evaluation Criteria
Assess how relevant the output is to the input query:

1. **Highly Relevant** (Score 9-10)
   - Directly addresses the query
   - All content is on-topic
   - No tangential information

2. **Mostly Relevant** (Score 7-8)
   - Primarily on-topic
   - Minor tangential content
   - Core relevance maintained

3. **Moderately Relevant** (Score 5-6)
   - Partially on-topic
   - Some off-topic content
   - Mix of relevant and irrelevant

4. **Low Relevance** (Score 3-4)
   - Mostly off-topic
   - Limited connection to query
   - Significant irrelevant content

5. **Not Relevant** (Score 1-2)
   - Completely off-topic
   - No connection to query
   - Wrong subject matter

## Few-Shot Examples

### Example 1
Input: "How do I sort a list in Python?"
Output: "Python is a great language for beginners. It was created by Guido van Rossum in 1991. Many companies use Python..."
Score: 2
Reasoning: "Completely off-topic. Discusses Python history instead of answering the sorting question."

### Example 2
Input: "How do I sort a list in Python?"
Output: "You can sort a list using the sort() method or sorted() function. Example: my_list.sort() modifies in-place, while sorted(my_list) returns a new sorted list."
Score: 10
Reasoning: "Directly and concisely answers the question with clear examples. Fully relevant."

## Your Evaluation
Provide your evaluation in JSON format."""

# Response Coherence
COHERENCE_PROMPT = """# Task: Evaluate Response Coherence

## Output to Evaluate
{output}

## Evaluation Criteria
Assess the logical flow and internal consistency:

1. **Highly Coherent** (Score 9-10)
   - Clear logical structure
   - Ideas flow naturally
   - No contradictions
   - Smooth transitions

2. **Mostly Coherent** (Score 7-8)
   - Generally logical
   - Minor flow issues
   - Consistent overall
   - Few awkward transitions

3. **Moderately Coherent** (Score 5-6)
   - Some logical flow
   - Noticeable gaps
   - Minor contradictions
   - Choppy transitions

4. **Low Coherence** (Score 3-4)
   - Poor logical structure
   - Significant gaps
   - Some contradictions
   - Confusing flow

5. **Incoherent** (Score 1-2)
   - No clear structure
   - Multiple contradictions
   - Illogical flow
   - Incomprehensible

## Few-Shot Examples

### Example 1
Output: "The sky is blue. Therefore, plants need water. However, the sky is actually red."
Score: 1
Reasoning: "Multiple contradictions (sky is blue vs red), illogical reasoning (sky color to plant water), completely incoherent."

### Example 2
Output: "Machine learning is a subset of AI that enables systems to learn from data. As these systems process more data, they improve their performance. This iterative improvement makes ML particularly effective for tasks like image recognition."
Score: 9
Reasoning: "Clear logical flow from definition to mechanism to application. Each idea builds on the previous one."

## Your Evaluation
Provide your evaluation in JSON format."""

# Tool Selection
TOOL_SELECTION_PROMPT = """# Task: Evaluate Tool Selection Appropriateness

## Input
User Query: {input}
Available Tools: {available_tools}

## Tools Used
{tools_used}

## Evaluation Criteria
Assess whether the right tools were selected:

1. **Excellent Selection** (Score 9-10)
   - Perfect tool choices
   - No unnecessary tools
   - No missing tools
   - Optimal sequence

2. **Good Selection** (Score 7-8)
   - Appropriate tools chosen
   - Minor inefficiencies
   - Could be slightly optimized

3. **Adequate Selection** (Score 5-6)
   - Acceptable tools
   - Some unnecessary usage
   - Or some better alternatives exist

4. **Poor Selection** (Score 3-4)
   - Suboptimal choices
   - Missing critical tools
   - Or excessive unnecessary tools

5. **Inappropriate** (Score 1-2)
   - Wrong tools used
   - Critical tools missing
   - Task could not be completed properly

## Your Evaluation
Consider:
- Were the necessary tools used?
- Were any tools unnecessary?
- Was the sequence logical?
- Could the task be done more efficiently?

Provide your evaluation in JSON format."""

# Factual Accuracy (for RAG)
FACTUAL_ACCURACY_PROMPT = """# Task: Evaluate Factual Grounding

## Retrieved Context
{context}

## User Query
{input}

## Generated Response
{output}

## Evaluation Criteria
Assess how well the response is grounded in the provided context:

1. **Fully Grounded** (Score 9-10)
   - All claims supported by context
   - No hallucinations
   - Accurate representation of context
   - Appropriate confidence

2. **Mostly Grounded** (Score 7-8)
   - Most claims supported
   - Minor unsupported details
   - Overall accurate
   - Mostly appropriate confidence

3. **Partially Grounded** (Score 5-6)
   - Some claims supported
   - Some unsupported claims
   - Mix of accurate and hallucinated
   - Unclear confidence

4. **Poorly Grounded** (Score 3-4)
   - Few claims supported
   - Many hallucinations
   - Misrepresents context
   - Overconfident

5. **Not Grounded** (Score 1-2)
   - Claims not in context
   - Pure hallucination
   - Contradicts context
   - Inappropriately confident

## Your Evaluation
List any unsupported claims in your reasoning.
Provide your evaluation in JSON format."""

# Trajectory Optimality
TRAJECTORY_OPTIMALITY_PROMPT = """# Task: Evaluate Trajectory Optimality

## Goal
{goal}

## Steps Taken
{steps}

## Evaluation Criteria
Assess whether the agent took an optimal path:

1. **Optimal Path** (Score 9-10)
   - Direct path to goal
   - No redundant steps
   - No loops or retries
   - Efficient execution

2. **Near-Optimal** (Score 7-8)
   - Generally efficient
   - 1-2 extra steps
   - Minor redundancies
   - One retry acceptable

3. **Suboptimal** (Score 5-6)
   - Reaches goal but inefficient
   - Several extra steps
   - Some redundancy
   - Multiple retries

4. **Inefficient** (Score 3-4)
   - Many unnecessary steps
   - Significant redundancy
   - Loops detected
   - Wasteful execution

5. **Very Inefficient** (Score 1-2)
   - Extremely wasteful
   - Circular reasoning
   - Excessive retries
   - Poor planning

## Your Evaluation
Identify specific inefficiencies in your reasoning.
Provide your evaluation in JSON format."""


def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template with provided values.

    Args:
        template: Prompt template string
        **kwargs: Values to format into template

    Returns:
        Formatted prompt

    Example:
        >>> prompt = format_prompt(COMPLETENESS_PROMPT, input="What is AI?", output="AI is...")
    """
    return template.format(**kwargs)


def get_prompt_for_task(task: str) -> str:
    """Get the appropriate prompt template for a task.

    Args:
        task: Task name ("completeness", "relevance", etc.)

    Returns:
        Prompt template string

    Raises:
        ValueError: If task is unknown
    """
    prompts = {
        "completeness": COMPLETENESS_PROMPT,
        "relevance": RELEVANCE_PROMPT,
        "coherence": COHERENCE_PROMPT,
        "tool_selection": TOOL_SELECTION_PROMPT,
        "factual_accuracy": FACTUAL_ACCURACY_PROMPT,
        "trajectory_optimality": TRAJECTORY_OPTIMALITY_PROMPT,
    }

    if task not in prompts:
        raise ValueError(
            f"Unknown task '{task}'. Available tasks: {list(prompts.keys())}"
        )

    return prompts[task]
