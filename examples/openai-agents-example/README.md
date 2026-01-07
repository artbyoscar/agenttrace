# OpenAI Agents + AgentTrace Example

This example demonstrates how to integrate AgentTrace with OpenAI Assistants API.

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

1. Creates an OpenAI Assistant
2. Wraps the assistant execution with AgentTrace
3. Runs a math tutoring task
4. Tracks the entire execution
5. Sends trace data to AgentTrace
6. Cleans up resources

## Features Traced

- Assistant creation
- Thread management
- Message exchanges
- Run status changes
- Completion time
- Token usage

## View Traces

Open [http://localhost:3000](http://localhost:3000) to view your traces in the AgentTrace dashboard.

## Advanced Features

The example includes:
- Code interpreter tool usage
- Step-by-step execution tracking
- Error handling
- Resource cleanup

## Benefits

With AgentTrace, you can:
- Monitor assistant performance
- Track token usage and costs
- Debug assistant behavior
- Analyze response quality
- Compare different assistant configurations
