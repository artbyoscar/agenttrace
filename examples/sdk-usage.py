"""
AgentTrace Python SDK - Comprehensive Usage Examples

This file demonstrates all the ways to use AgentTrace for observing AI agents,
from zero-config local development to production deployments with advanced features.

Learn more: https://docs.agenttrace.dev
"""

# ============================================================================
# EXAMPLE 1: Basic Initialization - Local Mode (Zero Config)
# ============================================================================
# Perfect for development - no API key needed, traces output to console

from agenttrace import AgentTrace

# Initialize with zero configuration
# Automatically uses local mode with console output
trace = AgentTrace.init()

# That's it! Now all your traces will be captured and displayed locally


# ============================================================================
# EXAMPLE 2: Hosted Mode - Production Deployment
# ============================================================================
# Send traces to AgentTrace cloud or self-hosted instance

trace = AgentTrace.init(
    api_key="at_xxx",  # Get from https://app.agenttrace.dev
    project_id="my-project",
    environment="production",  # or "development", "staging"
    tags=["v2", "experiment-123"],  # Optional tags for filtering
)


# ============================================================================
# EXAMPLE 3: Configuration from Environment Variables
# ============================================================================
# Best practice for production - keep secrets out of code

import os

# Set environment variables:
# export AGENTTRACE_API_KEY=at_xxx
# export AGENTTRACE_PROJECT_ID=my-project
# export AGENTTRACE_ENVIRONMENT=production

trace = AgentTrace.init()  # Automatically loads from env


# ============================================================================
# EXAMPLE 4: Auto-Instrumentation - LangChain
# ============================================================================
# Automatically trace all LangChain operations with zero code changes

from agenttrace import AgentTrace
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

# Enable auto-instrumentation for LangChain
AgentTrace.init()
AgentTrace.instrument_langchain()

# Now all LangChain operations are automatically traced!
llm = OpenAI(temperature=0.7)
prompt = PromptTemplate.from_template("What is {topic}?")
chain = LLMChain(llm=llm, prompt=prompt)

# This will be automatically traced with full context
result = chain.run(topic="AI observability")


# ============================================================================
# EXAMPLE 5: Auto-Instrumentation - OpenAI
# ============================================================================
# Automatically trace all OpenAI API calls

from agenttrace import AgentTrace
import openai

AgentTrace.init()
AgentTrace.instrument_openai()

# All OpenAI calls are now automatically traced
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)


# ============================================================================
# EXAMPLE 6: Auto-Instrumentation - CrewAI
# ============================================================================
# Automatically trace all CrewAI agent operations

from agenttrace import AgentTrace
from crewai import Agent, Task, Crew

AgentTrace.init()
AgentTrace.instrument_crewai()

# Define your crew - it will be automatically traced
researcher = Agent(
    role="Researcher",
    goal="Research AI topics",
    backstory="Expert researcher",
)

task = Task(
    description="Research AI observability",
    agent=researcher,
)

crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()  # Automatically traced!


# ============================================================================
# EXAMPLE 7: Manual Instrumentation - Function Decorator
# ============================================================================
# Use decorators for fine-grained control over tracing

from agenttrace import AgentTrace, Framework

trace = AgentTrace.init()


@trace.trace_agent(name="research_agent", framework=Framework.CUSTOM)
def research_agent(query: str) -> str:
    """
    Research agent that processes queries.

    This entire function execution will be traced as a single operation.
    Input and output are automatically captured.
    """
    # Your agent logic here
    results = search_knowledge_base(query)
    answer = synthesize_answer(results)
    return answer


# Call the agent - automatically traced
answer = research_agent("What is observability?")


# ============================================================================
# EXAMPLE 8: Manual Instrumentation - LLM Decorator
# ============================================================================
# Specialized decorator for LLM calls with automatic metadata capture

from agenttrace import AgentTrace, Message, TokenUsage

trace = AgentTrace.init()


@trace.trace_llm(name="gpt4_call", model="gpt-4")
def call_gpt4(messages: list[Message]) -> str:
    """
    Call GPT-4 with automatic LLM metadata capture.

    Automatically captures:
    - Model name
    - Messages (input)
    - Response (output)
    - Token usage
    - Latency
    """
    # Your LLM call logic
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages
    )

    return response.choices[0].message.content


# Use the decorated function
result = call_gpt4([
    Message(role="user", content="Explain AI observability")
])


# ============================================================================
# EXAMPLE 9: Manual Instrumentation - Tool Decorator
# ============================================================================
# Trace tool invocations (API calls, database queries, etc.)

from agenttrace import AgentTrace

trace = AgentTrace.init()


@trace.trace_tool(name="web_search", tool_name="google_search")
def search_web(query: str) -> dict:
    """
    Search the web using Google.

    Automatically captures:
    - Tool name
    - Input parameters
    - Output results
    - Execution time
    - Any errors
    """
    # Your tool logic
    results = google.search(query, num_results=10)
    return {"results": results}


@trace.trace_tool(name="database_query", tool_name="postgres")
def query_database(sql: str) -> list:
    """Query PostgreSQL database."""
    # Your database logic
    cursor.execute(sql)
    return cursor.fetchall()


# ============================================================================
# EXAMPLE 10: Context Manager - Span Creation
# ============================================================================
# Use context managers for manual span creation with full control

from agenttrace import AgentTrace, SpanType

trace = AgentTrace.init()


def complex_operation(data: dict):
    """
    Complex operation with multiple traced steps.

    Context managers give you full control over span lifecycle
    and metadata.
    """
    # Create a parent span for the entire operation
    with trace.span("complex_operation", SpanType.AGENT_STEP) as parent:
        parent.set_input(data)
        parent.set_attribute("complexity", "high")

        # Step 1: Data preprocessing
        with trace.span("preprocess", SpanType.PREPROCESSING) as step1:
            step1.set_attribute("method", "normalize")
            processed = preprocess_data(data)
            step1.set_output(processed)

        # Step 2: LLM call
        with trace.span("llm_inference", SpanType.LLM_CALL) as step2:
            step2.set_llm_metadata(
                model="gpt-4",
                provider="openai",
                temperature=0.7,
            )
            result = call_llm(processed)
            step2.set_output(result)

        # Step 3: Postprocessing
        with trace.span("postprocess", SpanType.POSTPROCESSING) as step3:
            final = postprocess_result(result)
            step3.set_output(final)

        parent.set_output(final)
        return final


# ============================================================================
# EXAMPLE 11: Trace Context Manager - Root Span
# ============================================================================
# Create a trace with a root span for end-to-end operation tracking

from agenttrace import AgentTrace, Framework

trace = AgentTrace.init()


def run_agent_pipeline(query: str):
    """
    Run a complete agent pipeline with full tracing.

    The trace context manager creates a root span and establishes
    a trace context for all child operations.
    """
    with trace.trace("agent_pipeline", framework=Framework.CUSTOM) as root:
        # Set metadata on the root span
        root.set_attribute("user_id", "user_123")
        root.set_attribute("version", "2.0")
        root.set_input({"query": query})

        # All spans created inside this context are automatically
        # children of the root span
        with trace.span("retrieve_context") as retrieval:
            context = retrieve_relevant_context(query)
            retrieval.set_output(context)

        with trace.span("generate_response") as generation:
            response = generate_response(query, context)
            generation.set_output(response)

        root.set_output(response)
        return response


# ============================================================================
# EXAMPLE 12: Async Support - Async Functions
# ============================================================================
# Full support for async/await with automatic context propagation

from agenttrace import AgentTrace
import asyncio

trace = AgentTrace.init()


@trace.trace_agent(name="async_agent")
async def async_research_agent(query: str) -> str:
    """
    Async agent with automatic tracing.

    Context is properly propagated across async boundaries.
    """
    # Async operations are traced correctly
    results = await async_search(query)
    answer = await async_synthesize(results)
    return answer


@trace.trace_llm(name="async_llm_call")
async def async_call_llm(prompt: str) -> str:
    """Async LLM call with tracing."""
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


async def main():
    """Async main function with tracing."""
    with trace.trace("async_pipeline") as root:
        # Multiple async operations
        task1 = async_research_agent("What is AI?")
        task2 = async_call_llm("Explain observability")

        # Await them concurrently
        results = await asyncio.gather(task1, task2)

        return results


# Run the async pipeline
asyncio.run(main())


# ============================================================================
# EXAMPLE 13: Error Handling - Automatic Capture
# ============================================================================
# Errors are automatically captured and recorded in spans

from agenttrace import AgentTrace

trace = AgentTrace.init()


@trace.trace_agent(name="error_prone_agent")
def agent_that_might_fail(data: dict):
    """
    Agent that might fail.

    Errors are automatically captured with:
    - Exception type
    - Error message
    - Full stack trace
    - Span marked as ERROR status
    """
    if not data.get("valid"):
        raise ValueError("Invalid input data")

    # This error will be automatically captured
    result = risky_operation(data)
    return result


# The error is automatically recorded in the trace
try:
    agent_that_might_fail({"valid": False})
except ValueError:
    pass  # Error is already captured in trace


# ============================================================================
# EXAMPLE 14: Error Handling - Manual Recording
# ============================================================================
# Manually record errors for more control

from agenttrace import AgentTrace

trace = AgentTrace.init()


def safe_agent(data: dict):
    """
    Agent with manual error handling and recording.

    Use this when you want to handle errors but still record them
    in traces for observability.
    """
    with trace.span("safe_operation") as span:
        try:
            result = risky_operation(data)
            span.set_output(result)
            return result

        except Exception as e:
            # Manually record the exception
            span.record_exception(e)

            # Handle the error gracefully
            fallback_result = fallback_operation(data)
            span.set_output(fallback_result)
            span.set_attribute("fallback_used", True)

            return fallback_result


# ============================================================================
# EXAMPLE 15: Rich Metadata - LLM Calls
# ============================================================================
# Capture rich metadata for LLM operations

from agenttrace import AgentTrace, Message, TokenUsage

trace = AgentTrace.init()


def advanced_llm_call(prompt: str):
    """LLM call with comprehensive metadata capture."""

    with trace.span("gpt4_call", SpanType.LLM_CALL) as span:
        # Set LLM-specific metadata
        span.set_llm_metadata(
            model="gpt-4",
            provider="openai",
            temperature=0.7,
            max_tokens=500,
            messages=[
                Message(role="system", content="You are a helpful assistant"),
                Message(role="user", content=prompt),
            ]
        )

        # Make the call
        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0.7,
            max_tokens=500,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ]
        )

        # Update metadata with response details
        if span.llm:
            span.llm.response = response.choices[0].message.content
            span.llm.finish_reason = response.choices[0].finish_reason
            span.llm.usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            # Add cost calculation (example pricing)
            span.llm.cost_usd = calculate_cost(response.usage)

        return response.choices[0].message.content


# ============================================================================
# EXAMPLE 16: Rich Metadata - Tool Calls
# ============================================================================
# Capture detailed tool invocation metadata

from agenttrace import AgentTrace

trace = AgentTrace.init()


def execute_tool(tool_name: str, **kwargs):
    """Execute a tool with detailed tracing."""

    with trace.span(f"tool_{tool_name}", SpanType.TOOL_CALL) as span:
        # Set tool metadata
        span.set_tool_metadata(
            tool_name=tool_name,
            tool_input=kwargs,
        )

        try:
            # Execute the tool
            result = tools[tool_name](**kwargs)

            # Record success
            if span.tool:
                span.tool.tool_output = result

            return result

        except Exception as e:
            # Record error
            if span.tool:
                span.tool.tool_error = str(e)
            raise


# ============================================================================
# EXAMPLE 17: Rich Metadata - Retrieval (RAG)
# ============================================================================
# Capture vector search and retrieval metadata

from agenttrace import AgentTrace, SpanType

trace = AgentTrace.init()


def retrieve_context(query: str, top_k: int = 5):
    """Retrieve relevant context using vector search."""

    with trace.span("vector_search", SpanType.RETRIEVAL) as span:
        # Set retrieval metadata
        span.set_retrieval_metadata(
            query=query,
            collection="knowledge_base",
            top_k=top_k,
            score_threshold=0.7,
        )

        # Perform search
        results = vector_db.search(
            query=query,
            collection="knowledge_base",
            top_k=top_k,
            score_threshold=0.7,
        )

        # Update with results
        if span.retrieval:
            span.retrieval.num_results = len(results)
            span.retrieval.results = [
                {"id": r.id, "text": r.text, "metadata": r.metadata}
                for r in results
            ]
            span.retrieval.scores = [r.score for r in results]

        return results


# ============================================================================
# EXAMPLE 18: Custom Attributes and Tags
# ============================================================================
# Add custom metadata for filtering and analysis

from agenttrace import AgentTrace

trace = AgentTrace.init()


def agent_with_metadata(query: str, user_id: str):
    """Agent with rich custom metadata."""

    with trace.span("custom_agent") as span:
        # Add custom attributes
        span.set_attribute("user_id", user_id)
        span.set_attribute("query_length", len(query))
        span.set_attribute("language", "en")
        span.set_attribute("model_version", "v2.1")

        # Add tags for filtering
        span.add_tag("production")
        span.add_tag("premium_user")
        span.add_tag("experiment_a")

        # Set multiple attributes at once
        span.set_attributes({
            "region": "us-east-1",
            "cluster": "prod-cluster-1",
            "request_id": "req_123456",
        })

        # Your logic here
        result = process_query(query)

        return result


# ============================================================================
# EXAMPLE 19: Nested Agent Workflows
# ============================================================================
# Complex multi-agent workflows with hierarchical tracing

from agenttrace import AgentTrace, Framework

trace = AgentTrace.init()


@trace.trace_agent(name="researcher", framework=Framework.CUSTOM)
def researcher_agent(topic: str) -> dict:
    """Research a topic using multiple sources."""

    with trace.span("web_search") as span:
        web_results = search_web(topic)
        span.set_output(web_results)

    with trace.span("paper_search") as span:
        paper_results = search_papers(topic)
        span.set_output(paper_results)

    return {
        "web": web_results,
        "papers": paper_results,
    }


@trace.trace_agent(name="synthesizer", framework=Framework.CUSTOM)
def synthesizer_agent(research: dict) -> str:
    """Synthesize research into a coherent answer."""

    with trace.span("combine_sources") as span:
        combined = combine_sources(research)
        span.set_output(combined)

    with trace.span("generate_answer") as span:
        answer = generate_answer(combined)
        span.set_output(answer)

    return answer


@trace.trace_agent(name="coordinator", framework=Framework.CUSTOM)
def coordinator_agent(query: str) -> str:
    """
    Coordinate multiple agents to answer a query.

    This creates a hierarchical trace:
    - coordinator (root)
      - researcher
        - web_search
        - paper_search
      - synthesizer
        - combine_sources
        - generate_answer
    """
    # Research phase
    research = researcher_agent(query)

    # Synthesis phase
    answer = synthesizer_agent(research)

    return answer


# Run the coordinator - creates a full trace tree
result = coordinator_agent("What is AI observability?")


# ============================================================================
# EXAMPLE 20: Configuration Options
# ============================================================================
# Advanced configuration for production deployments

from agenttrace import AgentTrace, AgentTraceConfig, ExportMode, LogLevel

# Create a custom configuration
config = AgentTraceConfig(
    # Authentication
    api_key="at_xxx",
    project_id="my-project",

    # Environment
    environment="production",
    tags=["v2.0", "us-east-1"],

    # Export settings
    export_mode=ExportMode.ASYNC,  # or SYNC, DISABLED
    batch_size=20,  # Spans per batch
    flush_interval=10.0,  # Seconds
    max_queue_size=2000,  # Max spans in queue

    # Data capture
    capture_input=True,  # Capture function inputs
    capture_output=True,  # Capture function outputs
    max_attribute_length=8192,  # Max length for values

    # Sampling (reduce volume in production)
    sample_rate=0.1,  # Trace 10% of requests

    # Local export (debugging)
    console_export=True,  # Also log to console
    file_export=True,  # Also save to files
    file_export_path="./traces",

    # Performance
    timeout=30,  # HTTP timeout in seconds
    max_retries=3,  # Retry failed exports

    # Logging
    log_level=LogLevel.WARNING,
)

# Initialize with custom config
trace = AgentTrace.init(config=config)


# ============================================================================
# EXAMPLE 21: Environment-Specific Configuration
# ============================================================================
# Different configs for dev, staging, production

from agenttrace import AgentTrace, AgentTraceConfig, ExportMode
import os

def get_trace_config():
    """Get environment-specific configuration."""

    env = os.getenv("ENVIRONMENT", "development")

    if env == "development":
        return AgentTraceConfig(
            project_id="my-project-dev",
            export_mode=ExportMode.DISABLED,
            console_export=True,  # Console only for dev
            enabled=True,
        )

    elif env == "staging":
        return AgentTraceConfig(
            api_key=os.getenv("AGENTTRACE_API_KEY"),
            project_id="my-project-staging",
            environment="staging",
            sample_rate=0.5,  # Sample 50% in staging
        )

    else:  # production
        return AgentTraceConfig(
            api_key=os.getenv("AGENTTRACE_API_KEY"),
            project_id="my-project-prod",
            environment="production",
            sample_rate=0.1,  # Sample 10% in production
            tags=["prod"],
        )


# Initialize with environment-specific config
trace = AgentTrace.init(config=get_trace_config())


# ============================================================================
# EXAMPLE 22: Cleanup and Shutdown
# ============================================================================
# Proper cleanup when your application shuts down

from agenttrace import AgentTrace
import atexit

trace = AgentTrace.init()

# Register cleanup on exit
atexit.register(trace.shutdown)

# Or use context manager for automatic cleanup
def main():
    with AgentTrace.init() as trace:
        # Your application code
        run_agent_pipeline()

    # Automatically flushed and shutdown on exit


# Manual flush (e.g., at checkpoints)
def critical_checkpoint():
    """Force flush at critical points."""
    # Do important work
    result = important_operation()

    # Ensure all traces are sent before continuing
    trace.flush()

    return result


# Manual shutdown
def graceful_shutdown():
    """Gracefully shutdown the application."""
    print("Shutting down...")

    # Flush pending traces
    trace.flush()

    # Shutdown the trace client
    trace.shutdown()

    print("Shutdown complete")


# ============================================================================
# EXAMPLE 23: Framework-Specific Best Practices - LangChain
# ============================================================================
# Best practices for using AgentTrace with LangChain

from agenttrace import AgentTrace, Framework
from langchain.chains import LLMChain
from langchain.agents import AgentExecutor, create_openai_functions_agent

# Initialize and auto-instrument
trace = AgentTrace.init()
AgentTrace.instrument_langchain()

# Optional: Add custom metadata to auto-instrumented traces
def langchain_callback(span):
    """Custom callback to enrich auto-instrumented spans."""
    span.add_tag("langchain")
    span.set_attribute("app_version", "2.0")

AgentTrace.configure_langchain(callback=langchain_callback)

# Your LangChain code runs normally - everything is traced!
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
result = agent_executor.invoke({"input": "What is AI?"})


# ============================================================================
# EXAMPLE 24: Testing and Development
# ============================================================================
# Use AgentTrace during testing without side effects

from agenttrace import AgentTrace, ExportMode
import pytest

# Disable tracing for tests
@pytest.fixture(autouse=True)
def disable_tracing():
    """Disable tracing during tests."""
    trace = AgentTrace.init(export_mode=ExportMode.DISABLED)
    yield
    trace.shutdown()


# Or use console export for debugging tests
def test_agent_with_traces():
    """Test with console traces for debugging."""
    trace = AgentTrace.init(
        export_mode=ExportMode.DISABLED,
        console_export=True,  # See traces in test output
    )

    result = my_agent("test query")

    assert result is not None
    trace.shutdown()


# ============================================================================
# EXAMPLE 25: Production Monitoring
# ============================================================================
# Monitor agent performance in production

from agenttrace import AgentTrace
import time

trace = AgentTrace.init(
    api_key="at_xxx",
    project_id="prod-agents",
    environment="production",
    tags=["v2", "high-priority"],
)


@trace.trace_agent(name="production_agent")
def production_agent(query: str, user_id: str):
    """
    Production agent with comprehensive monitoring.

    Automatically captures:
    - Latency
    - Token usage and costs
    - Error rates
    - Success/failure status
    - Custom business metrics
    """
    with trace.span("validate_input") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("query_length", len(query))
        validate_query(query)

    with trace.span("llm_call", SpanType.LLM_CALL) as span:
        start = time.time()
        response = call_llm(query)
        duration = time.time() - start

        # Track performance metrics
        span.set_attribute("latency_ms", duration * 1000)
        span.set_attribute("model", "gpt-4")

        # Business metrics
        span.set_attribute("user_tier", get_user_tier(user_id))
        span.set_attribute("cost_center", "research")

    return response


# ============================================================================
# END OF EXAMPLES
# ============================================================================

"""
Summary of Usage Patterns:

1. Two-line setup:
   from agenttrace import AgentTrace
   trace = AgentTrace.init()

2. Auto-instrumentation (zero code changes):
   AgentTrace.instrument_langchain()
   AgentTrace.instrument_openai()
   AgentTrace.instrument_crewai()

3. Decorators (minimal changes):
   @trace.trace_agent(name="my_agent")
   @trace.trace_llm(name="llm_call")
   @trace.trace_tool(name="tool_call")

4. Context managers (full control):
   with trace.span("operation") as span:
       span.set_attribute("key", "value")

5. Rich metadata:
   span.set_llm_metadata(model="gpt-4", ...)
   span.set_tool_metadata(tool_name="search", ...)
   span.set_retrieval_metadata(query="...", ...)

6. Error handling:
   Automatic capture in decorators/context managers
   Manual: span.record_exception(e)

7. Async support:
   Full support for async/await patterns

8. Production features:
   - Sampling
   - Batching
   - Custom tags and attributes
   - Environment-specific configs
   - Multiple export destinations

For more examples and documentation:
https://docs.agenttrace.dev
"""
