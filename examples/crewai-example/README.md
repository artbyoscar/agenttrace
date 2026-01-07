# CrewAI + AgentTrace Example

This example demonstrates how to integrate AgentTrace with CrewAI.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set environment variables:

```bash
export OPENAI_API_KEY=your-openai-key
export AGENTTRACE_API_KEY=your-agenttrace-key
export AGENTTRACE_API_URL=http://localhost:8000
```

Or create a `.env` file:

```env
OPENAI_API_KEY=your-openai-key
AGENTTRACE_API_KEY=your-agenttrace-key
AGENTTRACE_API_URL=http://localhost:8000
```

3. Run the example:

```bash
python main.py
```

## What This Example Does

1. Creates multiple CrewAI agents (Researcher and Writer)
2. Defines tasks for each agent
3. Adds AgentTrace callback handler
4. Runs the crew
5. Automatically traces all agent interactions
6. Sends trace data to AgentTrace

## Features Traced

- Agent executions
- Task completions
- Agent communications
- LLM calls
- Errors and retries

## View Traces

Open [http://localhost:3000](http://localhost:3000) to view your traces in the AgentTrace dashboard.

## Benefits

With AgentTrace, you can:
- Debug multi-agent interactions
- Monitor crew performance
- Track token usage and costs
- Identify bottlenecks
- Analyze agent behavior
