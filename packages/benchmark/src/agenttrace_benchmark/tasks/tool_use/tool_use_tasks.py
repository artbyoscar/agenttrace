"""
TOOL_USE Category Tasks (Part 1: Tasks 1-13 of 25)

Tests appropriate tool selection, composition, error handling, and orchestration.
"""

from uuid import uuid4

from ...schema import (
    BenchmarkTask,
    DifficultyLevel,
    EvaluationType,
    EvaluationCriterion,
    TaskMetadata,
    TaskStatus,
    ToolRequirement,
)
from ...categories import BenchmarkCategory


# Task 1: Single Tool Selection - Basic
TOOL_USE_001 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="tool_selection",
    difficulty=DifficultyLevel.BASIC,
    name="Simple Calculation",
    description="Select and use calculator tool for basic arithmetic",
    prompt="""
Calculate the following: (25 * 4) + (100 / 5) - 7

Use the available calculator tool to compute the answer.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"answer": "float", "tool_used": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_tool",
            description="Uses calculator tool",
            weight=0.3,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="correct_answer",
            description="Gets correct answer (113)",
            weight=0.7,
            measurement_type="binary",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="calculator", tool_type="function", required=True),
    ],
    time_limit_seconds=30,
    token_budget=200,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["tool_selection", "calculator", "basic"],
    ),
)

# Task 2: Tool Selection from Multiple Options
TOOL_USE_002 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="tool_selection",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Information Retrieval Choice",
    description="Choose appropriate tool for information needs",
    prompt="""
You need to find the current population of Tokyo.

Available tools:
- calculator: Performs mathematical calculations
- web_search: Searches the internet
- file_read: Reads local files
- database_query: Queries databases

Which tool should you use and why? Then use it to find the answer.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"tool_choice": "str", "rationale": "str", "answer": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="appropriate_tool",
            description="Selects web_search",
            weight=0.4,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="rationale",
            description="Explains why web_search is appropriate",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="execution",
            description="Successfully uses the tool",
            weight=0.3,
            measurement_type="binary",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="web_search", tool_type="api", required=True),
        ToolRequirement(tool_name="calculator", tool_type="function", required=False),
        ToolRequirement(tool_name="file_read", tool_type="function", required=False),
        ToolRequirement(tool_name="database_query", tool_type="function", required=False),
    ],
    time_limit_seconds=90,
    token_budget=400,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["tool_selection", "decision_making", "intermediate"],
    ),
)

# Task 3: Parameter Binding
TOOL_USE_003 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="parameter_binding",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="API Call with Correct Parameters",
    description="Construct API call with proper parameter formatting",
    prompt="""
Make an API call to retrieve weather data for New York City for the next 7 days.

API endpoint: https://api.weather.com/forecast
Required parameters:
- location: city name
- days: number of days
- units: temperature units (celsius or fahrenheit)
- api_key: will be provided by system

Construct the proper API call with correct parameters.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"tool": "str", "parameters": "dict"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_tool",
            description="Uses api_call tool",
            weight=0.2,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="correct_endpoint",
            description="Specifies correct endpoint URL",
            weight=0.2,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="correct_parameters",
            description="All required parameters present and correct",
            weight=0.6,
            measurement_type="continuous",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="api_call", tool_type="api", required=True),
    ],
    time_limit_seconds=120,
    token_budget=400,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["parameter_binding", "api", "intermediate"],
    ),
)

# Task 4: Simple Tool Composition
TOOL_USE_004 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="tool_composition",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Search and Calculate",
    description="Compose two tools to solve problem",
    prompt="""
Find the GDP of France and Germany, then calculate the difference.

Use web_search to find the values, then calculator to compute the difference.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"france_gdp": "float", "germany_gdp": "float", "difference": "float", "tools_used": "list"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="tool_sequence",
            description="Uses both tools in correct order",
            weight=0.3,
            measurement_type="discrete",
        ),
        EvaluationCriterion(
            name="data_extraction",
            description="Correctly extracts GDP values from search",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="calculation",
            description="Correctly calculates difference",
            weight=0.4,
            measurement_type="binary",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="web_search", tool_type="api", required=True),
        ToolRequirement(tool_name="calculator", tool_type="function", required=True),
    ],
    time_limit_seconds=180,
    token_budget=600,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["tool_composition", "search", "calculator", "intermediate"],
    ),
)

# Task 5: Error Handling - Tool Failure
TOOL_USE_005 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="error_detection",
    difficulty=DifficultyLevel.ADVANCED,
    name="Handle File Not Found",
    description="Detect and handle file read errors appropriately",
    prompt="""
Read the contents of the file at path: "/data/nonexistent_file.txt"

The file doesn't exist. Detect this error and provide an appropriate response
explaining what went wrong and what alternative actions could be taken.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"error_detected": "bool", "error_type": "str", "alternative_actions": "list"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="error_detection",
            description="Recognizes FileNotFoundError",
            weight=0.4,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="error_explanation",
            description="Clearly explains what went wrong",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="alternatives",
            description="Suggests reasonable alternatives (check path, create file, etc.)",
            weight=0.3,
            measurement_type="continuous",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="file_read", tool_type="function", required=True),
    ],
    time_limit_seconds=120,
    token_budget=500,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["error_handling", "file_operations", "advanced"],
    ),
)

# Task 6: Tool Retry Strategy
TOOL_USE_006 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="error_recovery",
    difficulty=DifficultyLevel.ADVANCED,
    name="API Retry with Backoff",
    description="Implement retry strategy for failing API calls",
    prompt="""
You need to fetch data from an API that is intermittently failing with 503 Service Unavailable errors.

Design and describe a retry strategy that:
1. Attempts up to 3 retries
2. Uses exponential backoff (1s, 2s, 4s)
3. Returns an error if all retries fail

Then explain how you would implement this with the api_call tool.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"strategy": "str", "implementation": "str", "max_attempts": "int"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="retry_logic",
            description="Describes 3 retry attempts correctly",
            weight=0.3,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="backoff_strategy",
            description="Implements exponential backoff correctly",
            weight=0.4,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="failure_handling",
            description="Handles final failure appropriately",
            weight=0.3,
            measurement_type="binary",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="api_call", tool_type="api", required=True),
    ],
    time_limit_seconds=180,
    token_budget=600,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["error_recovery", "retry", "api", "advanced"],
    ),
)

# Task 7: Complex Tool Orchestration
TOOL_USE_007 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="tool_composition",
    difficulty=DifficultyLevel.ADVANCED,
    name="Data Pipeline",
    description="Orchestrate multiple tools in a data processing pipeline",
    prompt="""
Create a data processing pipeline that:

1. Reads customer data from file: "/data/customers.csv"
2. Queries database to get their order history
3. Calculates total revenue per customer
4. Writes results to file: "/output/customer_revenue.csv"

Describe the sequence of tool calls and their parameters.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"pipeline_steps": "list[dict]", "tool_sequence": "list"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="complete_pipeline",
            description="All 4 steps present",
            weight=0.3,
            measurement_type="discrete",
        ),
        EvaluationCriterion(
            name="correct_sequence",
            description="Steps in logical order with dependencies",
            weight=0.3,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="parameter_correctness",
            description="Proper parameters for each tool",
            weight=0.4,
            measurement_type="continuous",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="file_read", tool_type="function", required=True),
        ToolRequirement(tool_name="database_query", tool_type="function", required=True),
        ToolRequirement(tool_name="calculator", tool_type="function", required=True),
        ToolRequirement(tool_name="file_write", tool_type="function", required=True),
    ],
    time_limit_seconds=300,
    token_budget=800,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["orchestration", "pipeline", "data_processing", "advanced"],
    ),
)

# Task 8: Tool Output Parsing
TOOL_USE_008 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="output_parsing",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Parse Search Results",
    description="Extract specific information from tool output",
    prompt="""
Search for "Python 3.11 release date" and extract:
1. The exact release date
2. The source URL
3. Key features mentioned

Parse the search results to extract this information.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"release_date": "str", "source_url": "str", "key_features": "list"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="uses_search",
            description="Uses web_search tool appropriately",
            weight=0.2,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="extraction_accuracy",
            description="Correctly extracts requested information",
            weight=0.5,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="output_format",
            description="Structures output as requested",
            weight=0.3,
            measurement_type="binary",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="web_search", tool_type="api", required=True),
    ],
    time_limit_seconds=150,
    token_budget=600,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["parsing", "extraction", "search", "intermediate"],
    ),
)

# Task 9: Tool with Validation
TOOL_USE_009 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="input_validation",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Validate Before Execution",
    description="Validate inputs before using tools",
    prompt="""
You need to send an email with these details:

To: "invalid.email.format"
Subject: "Test Email"
Body: "This is a test"

Before using the email_send tool, validate the email address format.
If invalid, explain the issue and suggest correction.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"valid": "bool", "issue": "str", "suggestion": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="detects_invalid_email",
            description="Identifies email format is invalid",
            weight=0.5,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="explains_issue",
            description="Clearly explains what's wrong",
            weight=0.25,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="provides_solution",
            description="Suggests how to fix the email",
            weight=0.25,
            measurement_type="continuous",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="email_send", tool_type="function", required=True),
    ],
    time_limit_seconds=120,
    token_budget=400,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["validation", "email", "error_prevention", "intermediate"],
    ),
)

# Task 10: Parallel Tool Execution
TOOL_USE_010 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="parallel_execution",
    difficulty=DifficultyLevel.ADVANCED,
    name="Concurrent API Calls",
    description="Identify and execute independent tool calls in parallel",
    prompt="""
You need to gather the following information:
1. Weather forecast for London
2. Current stock price of AAPL
3. News headlines about AI

These are independent queries. Design a strategy to fetch all three concurrently
to minimize total time.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"strategy": "str", "parallel_calls": "list", "expected_speedup": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="identifies_independence",
            description="Recognizes queries are independent",
            weight=0.3,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="parallel_strategy",
            description="Describes concurrent execution approach",
            weight=0.4,
            measurement_type="continuous",
        ),
        EvaluationCriterion(
            name="speedup_reasoning",
            description="Explains time savings from parallelization",
            weight=0.3,
            measurement_type="continuous",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="api_call", tool_type="api", required=True),
    ],
    time_limit_seconds=180,
    token_budget=600,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["parallel", "concurrent", "optimization", "advanced"],
    ),
)

# Task 11: Graceful Degradation
TOOL_USE_011 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="graceful_degradation",
    difficulty=DifficultyLevel.ADVANCED,
    name="Fallback Strategy",
    description="Implement fallback when primary tool fails",
    prompt="""
You need to find the definition of "quixotic".

Primary strategy: Use dictionary API
Fallback 1: Use web search
Fallback 2: Use general knowledge

The dictionary API is currently unavailable (returns 503 error).
Demonstrate how you would gracefully fall back to alternatives.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"attempted_tools": "list", "definition": "str", "source": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="attempts_primary",
            description="Tries dictionary API first",
            weight=0.2,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="handles_failure",
            description="Detects API failure and moves to fallback",
            weight=0.3,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="successful_fallback",
            description="Uses alternative successfully",
            weight=0.3,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="explains_strategy",
            description="Documents the fallback chain",
            weight=0.2,
            measurement_type="continuous",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="api_call", tool_type="api", required=True),
        ToolRequirement(tool_name="web_search", tool_type="api", required=True),
    ],
    time_limit_seconds=180,
    token_budget=600,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["graceful_degradation", "fallback", "resilience", "advanced"],
    ),
)

# Task 12: Tool Learning from Documentation
TOOL_USE_012 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="tool_learning",
    difficulty=DifficultyLevel.INTERMEDIATE,
    name="Use New Tool from Spec",
    description="Learn to use unfamiliar tool from documentation",
    prompt="""
You have access to a new tool called "code_execute" with this specification:

```
name: code_execute
description: Execute Python code in sandbox
parameters:
  - code (required, string): Python code to execute
  - timeout (optional, int, default=30): Max execution time in seconds
returns: dict with keys: stdout, stderr, return_value
errors: TimeoutError, RuntimeError, SecurityError
constraints: No network access, no file writes, 100MB memory limit
```

Use this tool to calculate the factorial of 10.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"tool_call": "dict", "result": "int"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="correct_tool_use",
            description="Uses code_execute tool correctly",
            weight=0.3,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="proper_parameters",
            description="Provides required code parameter",
            weight=0.3,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="correct_result",
            description="Gets factorial(10) = 3628800",
            weight=0.4,
            measurement_type="binary",
        ),
    ],
    required_tools=[
        ToolRequirement(tool_name="code_execute", tool_type="sandbox", required=True),
    ],
    time_limit_seconds=120,
    token_budget=500,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["tool_learning", "documentation", "code_execution", "intermediate"],
    ),
)

# Task 13: Resource Management - Rate Limits
TOOL_USE_013 = BenchmarkTask(
    task_id=uuid4(),
    category=BenchmarkCategory.TOOL_USE,
    subcategory="resource_management",
    difficulty=DifficultyLevel.ADVANCED,
    name="Respect API Rate Limits",
    description="Design tool usage that respects rate limits",
    prompt="""
You need to search for information about 50 different companies.

The web_search tool has a rate limit of 10 requests per minute.

Design a strategy to complete all searches while respecting the rate limit.
Calculate the minimum time required.
    """.strip(),
    input_format={"type": "text"},
    output_format={"type": "structured", "schema": {"strategy": "str", "min_time_minutes": "int", "batching_approach": "str"}},
    evaluation_type=EvaluationType.RUBRIC_BASED,
    evaluation_criteria=[
        EvaluationCriterion(
            name="respects_rate_limit",
            description="Strategy doesn't exceed 10 req/min",
            weight=0.4,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="correct_time_calculation",
            description="Calculates 5 minutes minimum correctly",
            weight=0.3,
            measurement_type="binary",
        ),
        EvaluationCriterion(
            name="batching_strategy",
            description="Describes reasonable batching approach",
            weight=0.3,
            measurement_type="continuous",
        ),
    ],
    required_tools=[
        ToolRequirement(
            tool_name="web_search",
            tool_type="api",
            required=True,
            configuration={"rate_limit": "10/minute"},
        ),
    ],
    time_limit_seconds=180,
    token_budget=600,
    status=TaskStatus.ACTIVE,
    metadata=TaskMetadata(
        version="1.0.0",
        author=["AgentTrace Team"],
        tags=["rate_limiting", "resource_management", "batching", "advanced"],
    ),
)


def get_tool_use_tasks_part1():
    """Return first 13 tool use tasks."""
    return [
        TOOL_USE_001,
        TOOL_USE_002,
        TOOL_USE_003,
        TOOL_USE_004,
        TOOL_USE_005,
        TOOL_USE_006,
        TOOL_USE_007,
        TOOL_USE_008,
        TOOL_USE_009,
        TOOL_USE_010,
        TOOL_USE_011,
        TOOL_USE_012,
        TOOL_USE_013,
    ]
