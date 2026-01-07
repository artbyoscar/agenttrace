```markdown
# LLM-as-Judge Infrastructure

Production-ready infrastructure for using LLMs to evaluate AI agent outputs.

## Overview

The AgentTrace judge system provides a robust, multi-provider LLM-as-judge implementation with:

- **Multi-Provider Support**: OpenAI, Anthropic, Together.ai
- **Async Execution**: Full async/await support
- **Retry Logic**: Exponential backoff on failures
- **Rate Limiting**: Built-in semaphore-based rate limiting
- **Caching**: Automatic caching of identical judgments
- **Cost Tracking**: Comprehensive token usage and cost monitoring
- **Structured Prompts**: Pre-built templates with few-shot examples
- **Robust Parsing**: Multiple fallback strategies for response parsing

## Quick Start

### Basic Usage

```python
from agenttrace.evals.judge import JudgeClient, JudgeConfig, COMPLETENESS_PROMPT

# Configure the judge
config = JudgeConfig(
    provider="openai",
    model="gpt-4o-mini"
)

# Create client
client = JudgeClient(config)

# Format a prompt
prompt = COMPLETENESS_PROMPT.format(
    input="What is Python?",
    output="Python is a programming language."
)

# Get judgment
judgment = await client.judge(prompt)

print(f"Score: {judgment.score:.2f}")  # 0.0-1.0
print(f"Reasoning: {judgment.reasoning}")
```

### Using Presets

```python
from agenttrace.evals.judge import get_default_config, JudgeClient

# Fast (gpt-4o-mini)
config = get_default_config("fast")

# Balanced (gpt-4o)
config = get_default_config("balanced")

# Best (claude-3-opus)
config = get_default_config("best")

client = JudgeClient(config)
```

### Environment-Based Configuration

```bash
# Set environment variables
export OPENAI_API_KEY=sk-...
export JUDGE_PROVIDER=openai
export JUDGE_MODEL=gpt-4o
export JUDGE_TEMPERATURE=0.0
```

```python
from agenttrace.evals.judge import create_config_from_env, JudgeClient

config = create_config_from_env()
client = JudgeClient(config)
```

## Configuration

### JudgeConfig

```python
from agenttrace.evals.judge import JudgeConfig

config = JudgeConfig(
    provider="openai",              # "openai", "anthropic", "together"
    model="gpt-4o-mini",            # Model identifier
    temperature=0.0,                 # Sampling temperature (0.0 for consistency)
    max_tokens=1000,                 # Max response tokens
    timeout_seconds=30,              # Request timeout
    max_retries=3,                   # Retry attempts on failure
    api_key="sk-...",               # API key (or from env)
    cache_judgments=True,            # Enable caching
)
```

### Environment Variables

The system automatically uses these environment variables:

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `TOGETHER_API_KEY`: Together.ai API key
- `JUDGE_PROVIDER`: Provider name (default: "openai")
- `JUDGE_MODEL`: Model name (default: "gpt-4o-mini")
- `JUDGE_TEMPERATURE`: Temperature (default: "0.0")
- `JUDGE_MAX_TOKENS`: Max tokens (default: "1000")
- `JUDGE_TIMEOUT`: Timeout seconds (default: "30")
- `JUDGE_MAX_RETRIES`: Max retries (default: "3")
- `JUDGE_CACHE`: Enable caching (default: "true")

## Supported Providers

### OpenAI

```python
config = JudgeConfig(
    provider="openai",
    model="gpt-4o-mini"  # or "gpt-4o", "gpt-4o-2024-11-20"
)
```

**Requires:** `pip install openai`

### Anthropic

```python
config = JudgeConfig(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022"
    # or "claude-3-opus-20240229", "claude-3-5-haiku-20241022"
)
```

**Requires:** `pip install anthropic`

### Together.ai

```python
config = JudgeConfig(
    provider="together",
    model="meta-llama/Llama-2-70b-chat-hf"
)
```

**Requires:** `pip install together`

## Prompt Templates

Pre-built prompts for common evaluation tasks:

### Completeness

```python
from agenttrace.evals.judge import COMPLETENESS_PROMPT, format_prompt

prompt = format_prompt(
    COMPLETENESS_PROMPT,
    input="What is Python and why is it popular?",
    output="Python is a programming language."
)
```

### Relevance

```python
from agenttrace.evals.judge import RELEVANCE_PROMPT

prompt = RELEVANCE_PROMPT.format(
    input="How do I sort a list?",
    output="Python is a great language..."
)
```

### Coherence

```python
from agenttrace.evals.judge import COHERENCE_PROMPT

prompt = COHERENCE_PROMPT.format(
    output="The sky is blue. Therefore plants need water..."
)
```

### Tool Selection

```python
from agenttrace.evals.judge import TOOL_SELECTION_PROMPT

prompt = TOOL_SELECTION_PROMPT.format(
    input="Search for Python tutorials",
    available_tools="web_search, calculator, file_reader",
    tools_used="web_search, calculator"
)
```

### Factual Accuracy (RAG)

```python
from agenttrace.evals.judge import FACTUAL_ACCURACY_PROMPT

prompt = FACTUAL_ACCURACY_PROMPT.format(
    context="Python is a high-level programming language...",
    input="What is Python?",
    output="Python is a language for AI and machine learning."
)
```

### Trajectory Optimality

```python
from agenttrace.evals.judge import TRAJECTORY_OPTIMALITY_PROMPT

prompt = TRAJECTORY_OPTIMALITY_PROMPT.format(
    goal="Find and display weather data",
    steps="search -> retry -> search -> process -> display"
)
```

## Response Format

All prompts request JSON responses:

```json
{
    "score": 8,
    "reasoning": "The response addresses most aspects...",
    "confidence": 0.9
}
```

The parser handles:
- Clean JSON
- JSON in markdown code blocks
- Pattern matching ("Score: 8/10")
- Fallback heuristics

## Judgment Object

```python
judgment = await client.judge(prompt)

# Attributes
judgment.score          # float 0.0-1.0 (normalized)
judgment.reasoning      # str (explanation)
judgment.raw_score      # float (original score before normalization)
judgment.confidence     # Optional[float] 0.0-1.0
judgment.metadata       # Dict[str, Any] (additional fields)
judgment.raw_response   # str (full LLM response)
```

## Cost Tracking

### Global Tracker

```python
from agenttrace.evals.judge import get_global_tracker

# Costs are automatically tracked
tracker = get_global_tracker()

print(f"Total cost: ${tracker.total_cost:.4f}")
print(f"Total tokens: {tracker.total_tokens}")
print(f"Judgments: {tracker.judgment_count}")

# Get detailed breakdown
summary = tracker.get_summary()
print(summary["costs_by_model"])
print(summary["usage_by_model"])

# Reset for new session
tracker.reset()
```

### Cost Thresholds

```python
from agenttrace.evals.judge import CostTracker

# Create tracker with threshold
tracker = CostTracker(cost_threshold=1.0)  # Warn at $1

# Will warn if threshold exceeded
tracker.record_judgment(model, usage)
```

### Model Pricing

Current pricing (per 1M tokens):

| Model | Input | Output |
|-------|-------|--------|
| gpt-4o | $2.50 | $10.00 |
| gpt-4o-mini | $0.15 | $0.60 |
| claude-3-opus | $15.00 | $75.00 |
| claude-3.5-sonnet | $3.00 | $15.00 |
| claude-3.5-haiku | $0.80 | $4.00 |

## Caching

Identical prompts are automatically cached (default: enabled, 1-hour TTL):

```python
# First call - hits API
judgment1 = await client.judge(prompt)

# Second call - uses cache
judgment2 = await client.judge(prompt)

# Disable caching
judgment3 = await client.judge(prompt, use_cache=False)

# Clear cache
client.clear_cache()

# Get cache stats
stats = client.get_cache_stats()
```

## Error Handling

The client includes automatic retry with exponential backoff:

```python
config = JudgeConfig(
    provider="openai",
    model="gpt-4o-mini",
    max_retries=3,          # Try up to 3 times
    timeout_seconds=30      # 30 second timeout per request
)
```

Retry delays: 1s, 2s, 4s (exponential backoff)

## Testing

### Mock Client

For testing without API calls:

```python
from agenttrace.evals.judge import MockJudgeClient, JudgeConfig

config = JudgeConfig(provider="openai", model="gpt-4o-mini")
client = MockJudgeClient(
    config,
    default_score=0.8,
    default_reasoning="Mock evaluation"
)

# Returns deterministic results
judgment = await client.judge("Test prompt")
assert judgment.score == 0.8

# Track call count
assert client.call_count == 1
```

### Running Tests

```bash
# All judge tests
pytest tests/evals/judge/ -v

# Specific module
pytest tests/evals/judge/test_parser.py -v
pytest tests/evals/judge/test_config.py -v
pytest tests/evals/judge/test_costs.py -v
pytest tests/evals/judge/test_client.py -v

# With coverage
pytest tests/evals/judge/ --cov=agenttrace.evals.judge --cov-report=html
```

## Advanced Usage

### Custom System Prompts

```python
custom_system = """You are a strict evaluator.
Use a 1-5 scale where 5 is perfect."""

judgment = await client.judge(
    prompt,
    system_prompt=custom_system
)
```

### Rate Limiting

Built-in semaphore limits concurrent requests:

```python
# Default: 10 concurrent requests
# Controlled automatically in client._semaphore
```

### Custom Parsing

```python
from agenttrace.evals.judge import JudgmentParser

parser = JudgmentParser(expected_max_score=5)  # 1-5 scale
judgment = parser.parse(response)
```

## Best Practices

1. **Use appropriate models**: `gpt-4o-mini` for most cases, `claude-3-opus` for critical evaluations
2. **Enable caching**: Reduces costs for repeated evaluations
3. **Monitor costs**: Use `get_global_tracker()` to track spending
4. **Set timeouts**: Prevent hanging on slow responses
5. **Use structured prompts**: Leverage built-in templates for consistency
6. **Temperature 0**: Use `temperature=0.0` for consistent evaluations
7. **Validate API keys**: Ensure environment variables are set correctly

## Integration with Evaluators

Update existing evaluators to use the new infrastructure:

```python
from agenttrace.evals.judge import JudgeClient, get_default_config, COMPLETENESS_PROMPT

class ResponseCompletenessEvaluator(Evaluator):
    def __init__(self, config=None):
        self.config = config or get_default_config("fast")
        self.client = JudgeClient(self.config)

    async def evaluate(self, trace: Trace) -> EvalResult:
        prompt = COMPLETENESS_PROMPT.format(
            input=trace.get_root_span()["metadata"]["input"],
            output=trace.get_root_span()["metadata"]["output"]
        )

        judgment = await self.client.judge(prompt)

        return EvalResult(
            evaluator_name=self.name,
            scores={"completeness": EvalScore("completeness", judgment.score)},
            feedback=judgment.reasoning
        )
```

## Troubleshooting

### API Key Issues

```python
# Explicit API key
config = JudgeConfig(
    provider="openai",
    model="gpt-4o-mini",
    api_key="sk-..."  # Don't hardcode in production!
)

# Or use environment variable
os.environ["OPENAI_API_KEY"] = "sk-..."
```

### Parsing Failures

The parser has multiple fallback strategies. If parsing still fails:

```python
# Check raw response
try:
    judgment = await client.judge(prompt)
except Exception as e:
    print(f"Parse error: {e}")
    # Check cache or logs for raw_response
```

### Rate Limits

If hitting provider rate limits:

```python
# Reduce concurrency
client._semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

# Or add delays between calls
await asyncio.sleep(1)
```

## License

MIT License - See LICENSE file for details.
```
