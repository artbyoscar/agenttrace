# LangChain + AgentTrace Example

This example demonstrates how to integrate AgentTrace with LangChain.

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

1. Creates a LangChain LLMChain
2. Adds AgentTrace callback handler
3. Runs a simple question-answering task
4. Automatically traces the execution
5. Sends trace data to AgentTrace

## View Traces

Open [http://localhost:3000](http://localhost:3000) to view your traces in the AgentTrace dashboard.

## Advanced Usage

Check out the [advanced_example.py](advanced_example.py) for:
- Multi-step chains
- Agent executors
- Custom metadata
- Error handling
