"""
AgentTrace Quick Start - Get Started in 2 Lines of Code

This is the fastest way to add observability to your AI agents.
"""

# ============================================================================
# QUICK START 1: Local Development (Zero Config)
# ============================================================================

from agenttrace import AgentTrace

# One line to initialize - uses local console output
trace = AgentTrace.init()

# One decorator to trace your agent
@trace.trace_agent(name="my_first_agent")
def my_agent(query: str) -> str:
    """Your agent logic here."""
    return f"Processed: {query}"

# That's it! Call your agent and see traces in the console
result = my_agent("Hello, AgentTrace!")


# ============================================================================
# QUICK START 2: Production Setup (With API Key)
# ============================================================================

from agenttrace import AgentTrace

# Initialize with your API key (get one at app.agenttrace.dev)
trace = AgentTrace.init(
    api_key="at_xxx",
    project_id="my-project"
)

@trace.trace_agent(name="production_agent")
def my_agent(query: str) -> str:
    """Your agent logic here."""
    return f"Processed: {query}"

# All traces now sent to AgentTrace dashboard
result = my_agent("Hello from production!")


# ============================================================================
# QUICK START 3: LangChain Auto-Instrumentation
# ============================================================================

from agenttrace import AgentTrace
from langchain.chains import LLMChain
from langchain.llms import OpenAI

# Initialize and auto-instrument LangChain
trace = AgentTrace.init()
AgentTrace.instrument_langchain()

# Your LangChain code works unchanged - now with full observability!
llm = OpenAI(temperature=0.7)
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run("What is AI observability?")


# ============================================================================
# QUICK START 4: Manual Tracing with Context Managers
# ============================================================================

from agenttrace import AgentTrace, SpanType

trace = AgentTrace.init()

def my_workflow(query: str):
    """Multi-step workflow with detailed tracing."""

    with trace.trace("my_workflow") as root:
        # Step 1: Retrieval
        with trace.span("retrieve_context", SpanType.RETRIEVAL) as span:
            context = retrieve_documents(query)
            span.set_output(context)

        # Step 2: LLM Call
        with trace.span("generate_answer", SpanType.LLM_CALL) as span:
            span.set_llm_metadata(model="gpt-4", temperature=0.7)
            answer = generate_answer(query, context)
            span.set_output(answer)

        return answer


# ============================================================================
# QUICK START 5: Async Agents
# ============================================================================

from agenttrace import AgentTrace
import asyncio

trace = AgentTrace.init()

@trace.trace_agent(name="async_agent")
async def async_agent(query: str) -> str:
    """Async agent with automatic tracing."""
    result = await async_process(query)
    return result

# Run async agent
asyncio.run(async_agent("Async query"))


# ============================================================================
# QUICK START 6: Error Handling
# ============================================================================

from agenttrace import AgentTrace

trace = AgentTrace.init()

@trace.trace_agent(name="safe_agent")
def safe_agent(data: dict):
    """Agent with automatic error capture."""
    if not data.get("valid"):
        # This error is automatically captured in traces
        raise ValueError("Invalid input")

    return process_data(data)


# ============================================================================
# Next Steps
# ============================================================================

"""
You're all set! Here's what to do next:

1. View your traces:
   - Local: Check your console output
   - Hosted: Visit app.agenttrace.dev

2. Explore features:
   - See examples/sdk-usage.py for comprehensive examples
   - Read the docs at docs.agenttrace.dev

3. Instrument your framework:
   - LangChain: AgentTrace.instrument_langchain()
   - OpenAI: AgentTrace.instrument_openai()
   - CrewAI: AgentTrace.instrument_crewai()

4. Advanced usage:
   - Add custom attributes: span.set_attribute("key", "value")
   - Add tags: span.add_tag("production")
   - Record metadata: span.set_llm_metadata(...)

5. Production ready:
   - Use environment variables for config
   - Enable sampling for high-volume apps
   - Set up alerts in the dashboard

Happy tracing! 🚀
"""
