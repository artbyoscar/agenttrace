# ADR-003: SDK Instrumentation Approach

## Status

**Status:** accepted

**Date:** 2025-01-06

**Deciders:** Oscar Nuñez, AgentTrace Core Team

---

## Context

### Background

The AgentTrace Python SDK needs to instrument AI agent frameworks (LangChain, CrewAI, OpenAI Agents) to capture execution traces. Users expect minimal code changes for instrumentation while maintaining flexibility for custom agents.

Different frameworks have different APIs:
- **LangChain**: Callback-based architecture
- **CrewAI**: Built on LangChain, similar callback model
- **OpenAI Agents**: Assistant API with polling
- **Custom agents**: Varied implementations

### Problem Statement

What instrumentation approach should the SDK use to balance:
1. Zero-config experience for popular frameworks
2. Flexibility for custom agent implementations
3. Performance overhead minimization
4. Maintainability as frameworks evolve
5. User control over what gets traced

### Goals and Constraints

**Goals:**
- Support major frameworks with minimal user code changes
- Provide manual instrumentation for custom agents
- Keep performance overhead <5% of execution time
- Make instrumentation optional and controllable
- Capture comprehensive trace data (spans, metadata, errors)
- Support both sync and async code

**Constraints:**
- Cannot modify framework source code
- Must work with multiple framework versions
- Need to handle breaking changes in frameworks
- Should not require framework-specific configuration
- Must be compatible with existing framework middleware/callbacks

**Assumptions:**
- Users will primarily use 3-4 major frameworks
- Custom agents are less common but important
- Performance is less critical than completeness for observability
- Framework APIs are relatively stable
- Users want "magic" auto-instrumentation when possible

---

## Decision

**We will use monkey-patching for auto-instrumentation of popular frameworks, combined with decorators and context managers for manual instrumentation.**

### Implementation Details

**Two-tier approach:**

**1. Auto-instrumentation (Monkey-patching)**

For supported frameworks (LangChain, CrewAI, OpenAI):

```python
from agenttrace import init

# Automatically patches supported frameworks
init(api_key="key", project="proj", auto_instrument=["langchain", "openai"])

# Framework code now automatically traced
from langchain.chains import LLMChain
chain = LLMChain(...)  # Automatically instrumented
result = chain.run("prompt")  # Traces captured
```

**Implementation:**
- Patch framework entry points on import
- Wrap methods with tracing logic
- Use framework's native callback system when available
- Fallback to method wrapping when callbacks unavailable

**2. Manual instrumentation (Decorators + Context Managers)**

For custom agents or fine-grained control:

```python
from agenttrace import trace_agent, AgentTrace

tracer = AgentTrace(api_key="key", project="proj")

# Decorator approach
@tracer.trace_agent(name="my-agent")
def my_custom_agent(input_data):
    # Your agent logic
    return result

# Context manager approach (more control)
with tracer.start_trace(name="custom-operation") as span:
    span.log("Starting processing")
    span.set_metadata("input_tokens", 100)
    result = process_data()
    span.log("Completed")
```

### Key Components

**Auto-instrumentation module** (`agenttrace/auto/`):
```python
auto/
├── __init__.py          # Registration and initialization
├── langchain.py         # LangChain monkey patches
├── crewai.py            # CrewAI patches (extends LangChain)
├── openai.py            # OpenAI Assistant API patches
└── registry.py          # Framework detection and patching
```

**Manual instrumentation** (`agenttrace/`):
- `client.py`: AgentTrace main class with decorators
- `tracer.py`: Tracer and Span classes for context managers
- `context.py`: Thread-local context management

**Patching strategy:**
1. Detect framework import
2. Wrap key methods with trace capturing
3. Preserve original method signatures and behavior
4. Handle exceptions gracefully (fail-safe)
5. Allow disabling per-framework or globally

---

## Consequences

### Positive Consequences

- ✅ **Zero-config experience**: Users can enable tracing with one line
- ✅ **Framework coverage**: Can support popular frameworks comprehensively
- ✅ **Flexibility**: Manual instrumentation for custom cases
- ✅ **Gradual adoption**: Can start with auto, move to manual for control
- ✅ **No framework changes**: Works with unmodified framework code
- ✅ **Comprehensive traces**: Can capture all framework operations
- ✅ **User control**: Can disable auto-instrumentation selectively
- ✅ **Debugging friendly**: Easy to see what's being traced

### Negative Consequences

- ⚠️ **Fragility**: Monkey patches can break with framework updates
- ⚠️ **Maintenance burden**: Need to update patches for each framework version
- ⚠️ **Potential conflicts**: May interfere with other instrumentation tools
- ⚠️ **Hidden behavior**: Monkey-patching makes code behavior less obvious
- ⚠️ **Testing complexity**: Need to test against multiple framework versions
- ⚠️ **Performance overhead**: Wrapping adds slight performance cost
- ⚠️ **Import order dependencies**: Patching must happen before framework import

### Risks and Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|-------------------|
| Framework update breaks patches | High | High | Version pinning, comprehensive test matrix, graceful degradation |
| Conflicts with other tools | Medium | Medium | Namespace isolation, allow disabling patches, check for conflicts |
| Performance degradation | Medium | Low | Minimize wrapping overhead, add performance benchmarks, make opt-in |
| User confusion about patching | Medium | Medium | Clear documentation, verbose logging, explicit initialization |
| Async/await handling issues | High | Medium | Thorough async testing, use asyncio.create_task wrapping |

---

## Alternatives Considered

### Alternative 1: Callback/Plugin System Only

**Description:** Only use framework-native callback or plugin systems, no monkey-patching.

**Pros:**
- More stable across framework versions
- Explicit and transparent
- No risk of breaking framework behavior
- Easier to maintain

**Cons:**
- Requires user to configure callbacks for each framework
- Not zero-config
- Inconsistent experience across frameworks
- Some frameworks don't have callback systems
- More user code required

**Reason for rejection:** Fails the zero-config goal. While more stable, this approach puts too much burden on users to configure callbacks for each framework. Many users want observability "just to work" without learning framework-specific callback APIs.

### Alternative 2: OpenTelemetry Integration

**Description:** Build on OpenTelemetry's auto-instrumentation framework.

**Pros:**
- Standards-based approach
- Existing ecosystem and tooling
- Better interoperability with other observability tools
- Proven patterns for instrumentation

**Cons:**
- Limited coverage of AI frameworks (LangChain, etc. not supported)
- Heavier dependency (OTEL SDK is large)
- More complex setup for users
- Overkill for AI agent-specific tracing
- Harder to customize for agent-specific metadata

**Reason for rejection:** While OpenTelemetry is excellent for traditional apps, it lacks specific support for AI frameworks. Adding AI framework instrumentation to OTEL would require monkey-patching anyway, and we'd inherit a heavy dependency and complex API. Better to focus on AI-specific tracing with simpler API.

### Alternative 3: Agent Framework Forks

**Description:** Maintain forks of popular frameworks with built-in tracing.

**Pros:**
- Most reliable instrumentation (native integration)
- Best performance (no wrapping overhead)
- Can add AI-specific features
- No monkey-patching fragility

**Cons:**
- Massive maintenance burden (keeping forks up-to-date)
- Users must switch to forked versions
- Confusing for ecosystem
- Difficult to get adoption
- Cannot support closed-source frameworks

**Reason for rejection:** Completely impractical. Maintaining forks of rapidly-evolving frameworks like LangChain would consume all development resources. Users won't adopt forked versions when official versions are actively maintained.

### Alternative 4: AST (Abstract Syntax Tree) Transformation

**Description:** Use AST manipulation to inject tracing at import time or build time.

**Pros:**
- More robust than monkey-patching
- Can instrument at any level
- No runtime overhead from wrapping
- Can analyze code statically

**Cons:**
- Extremely complex to implement
- Difficult to debug
- Requires custom import hooks or build step
- Poor IDE support
- Breaks with minified/compiled code
- Hard to test

**Reason for rejection:** Over-engineered for the problem. AST transformation is powerful but introduces massive complexity for marginal benefits over monkey-patching. Debugging would be nearly impossible, and the user experience would be poor.

### Alternative 5: Proxy/Wrapper Objects

**Description:** Provide wrapped versions of framework classes that users import instead.

**Pros:**
- Explicit and transparent
- No monkey-patching
- User has full control
- Easy to debug

**Cons:**
- Requires changing imports throughout user code
- Not zero-config
- Must maintain wrappers for all framework APIs
- Breaks type checking
- Difficult to keep up with framework changes

**Example:**
```python
# Instead of:
from langchain.chains import LLMChain

# Users would do:
from agenttrace.integrations.langchain import LLMChain
```

**Reason for rejection:** Too invasive and fails the zero-config goal. Requiring users to change all their imports is a non-starter. This approach also breaks IDE autocompletion and type checking.

---

## References

### Technical Documentation

- [Python Import Hooks](https://docs.python.org/3/reference/import.html#import-hooks)
- [Decorators and Context Managers](https://docs.python.org/3/library/contextlib.html)
- [LangChain Callbacks](https://python.langchain.com/docs/modules/callbacks/)
- [OpenTelemetry Python Auto-instrumentation](https://opentelemetry.io/docs/instrumentation/python/automatic/)

### Related ADRs

- ADR-001: Monorepo vs Multi-repo (affects SDK development workflow)
- ADR-002: Trace Storage Backend (affects data collected by SDK)

### Supporting Research

- [Monkey Patching Best Practices](https://martinfowler.com/bliki/MonkeyPatching.html)
- [Python Import System Deep Dive](https://tenthousandmeters.com/blog/python-behind-the-scenes-11-how-the-python-import-system-works/)
- [OpenTelemetry Instrumentation Patterns](https://opentelemetry.io/docs/reference/specification/trace/sdk/)

### Industry Examples

- **Sentry SDK**: Uses monkey-patching for framework integration
- **New Relic**: Monkey-patches popular Python frameworks
- **DataDog APM**: Auto-instruments with monkey-patching
- **OpenTelemetry**: Mix of monkey-patching and native integrations
- **Weights & Biases**: Uses decorators for ML experiment tracking

---

## Notes

### Timeline

- **2025-01-06:** Decision proposed and accepted
- **2025-01-15:** Planned implementation start
- **2025-02-15:** Target MVP (LangChain + manual instrumentation)
- **2025-03-01:** CrewAI and OpenAI support

### Review Schedule

This decision should be reviewed when:
- A major framework releases breaking changes
- Performance overhead exceeds 5%
- User feedback indicates issues with auto-instrumentation
- Alternative instrumentation methods become available

**Scheduled review date:** 2025-07-01 (6 months)

### Success Metrics

How will we measure if this decision was successful?

- **Adoption rate**: >50% of users enable auto-instrumentation
- **Framework coverage**: Support for top 3 frameworks maintained
- **Performance overhead**: <5% average overhead
- **User satisfaction**: >4/5 rating for ease of use
- **Maintenance burden**: <20% of development time on patches
- **Issue rate**: <5 issues per month related to patching

### Framework Support Matrix

| Framework | Auto-instrumentation | Manual Required | Priority |
|-----------|---------------------|----------------|----------|
| LangChain | ✅ Yes (callbacks + patching) | Optional | High |
| CrewAI | ✅ Yes (extends LangChain) | Optional | High |
| OpenAI Agents | ✅ Yes (API wrapping) | Optional | High |
| AutoGPT | 🔄 Planned | Yes | Medium |
| Custom Agents | ❌ No | Yes (decorators) | High |
| LlamaIndex | 🔄 Planned | Yes | Medium |

### Implementation Phases

**Phase 1: Manual Instrumentation (Week 1-2)**
- Implement decorators (`@trace_agent`)
- Implement context managers (`with start_trace()`)
- Add span logging and metadata
- Write comprehensive tests

**Phase 2: LangChain Auto-instrumentation (Week 3-4)**
- Implement callback-based tracing
- Add method wrapping for edge cases
- Test with LangChain versions 0.1.x
- Documentation and examples

**Phase 3: OpenAI Auto-instrumentation (Week 5)**
- Wrap OpenAI client methods
- Capture Assistant API interactions
- Test with different OpenAI SDK versions

**Phase 4: CrewAI Support (Week 6)**
- Extend LangChain instrumentation
- Add CrewAI-specific metadata
- Test multi-agent scenarios

**Phase 5: Polish and Optimization (Week 7-8)**
- Performance optimization
- Error handling improvements
- Comprehensive documentation
- Video tutorials

### Patch Update Strategy

**When framework updates are released:**

1. **Detect change**:
   - Monitor framework release notes
   - Run test suite against new version
   - Check for API changes

2. **Assess impact**:
   - Does patch still work?
   - Are new features un-instrumented?
   - Are there breaking changes?

3. **Update patch**:
   - Modify patching code
   - Add tests for new version
   - Update compatibility matrix
   - Release patch version of SDK

4. **Communicate**:
   - Update documentation
   - Notify users via changelog
   - Provide migration guide if needed

**Version support policy:**
- Support last 3 minor versions of each framework
- Drop support for versions >1 year old
- Security patches for all supported versions

---

## Appendix: Code Examples

### Auto-instrumentation Example

```python
from agenttrace import init

# One-line setup
init(
    api_key="your-api-key",
    project="my-project",
    auto_instrument=["langchain", "openai"],  # Enable auto-instrumentation
    auto_instrument_exclude=["langchain.vectorstores"]  # Optionally exclude
)

# Now all LangChain and OpenAI calls are automatically traced
from langchain.chains import LLMChain
from langchain.llms import OpenAI

llm = OpenAI(temperature=0.9)
chain = LLMChain(llm=llm, prompt=prompt)

# This is automatically traced - no additional code needed!
result = chain.run("What is AI?")
```

### Manual Instrumentation Example

```python
from agenttrace import AgentTrace

tracer = AgentTrace(api_key="key", project="proj")

@tracer.trace_agent(name="custom-agent", tags=["production"])
def my_agent(query: str) -> str:
    # Your custom agent logic
    response = call_llm(query)
    return response

# With context manager for fine-grained control
with tracer.start_trace(name="complex-operation") as span:
    span.log("Starting data processing")
    span.set_metadata("input_size", len(data))

    # Step 1
    span.add_child_span("step-1")
    result1 = step1(data)

    # Step 2
    span.add_child_span("step-2")
    result2 = step2(result1)

    span.set_metadata("output_size", len(result2))
    span.log("Processing complete")
```

### Selective Patching Example

```python
from agenttrace import init

# Fine-grained control over what gets patched
init(
    api_key="key",
    project="proj",
    auto_instrument={
        "langchain": {
            "enabled": True,
            "patch_chains": True,
            "patch_llms": True,
            "patch_agents": True,
            "patch_vectorstores": False,  # Disable vectorstore tracing
        },
        "openai": {
            "enabled": True,
            "patch_completions": True,
            "patch_embeddings": False,  # Disable embedding tracing
        }
    }
)
```

---

**Last Updated:** 2025-01-06

**Authors:** Oscar Nuñez
