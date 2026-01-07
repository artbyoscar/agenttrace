# Getting Started with AgentTrace

This guide will help you get started with AgentTrace, the open-source observability platform for AI agents.

## Prerequisites

Before you begin, make sure you have:

- Python 3.9 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- Redis 6 or higher
- Docker (optional, for containerized deployment)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/agenttrace.git
cd agenttrace
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/agenttrace
REDIS_URL=redis://localhost:6379
API_PORT=8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start with Docker (Recommended)

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis cache
- API service
- Ingestion service
- Dashboard

### 4. Manual Setup

If you prefer to run services manually:

#### Start the API

```bash
cd apps/api
pip install -r requirements.txt
python main.py
```

#### Start the Dashboard

```bash
cd apps/dashboard
npm install
npm run dev
```

#### Start the Ingestion Service

```bash
cd apps/ingestion
go run main.go
```

## Install the Python SDK

```bash
pip install agenttrace
```

Or install from source:

```bash
cd packages/sdk-python
pip install -e .
```

## Your First Trace

### 1. Configure the SDK

```python
from agenttrace import AgentTrace

trace = AgentTrace(
    api_key="your-api-key",  # Get this from the dashboard
    project="my-first-project",
    api_url="http://localhost:8000"
)
```

### 2. Trace a Function

```python
@trace.trace_agent(name="hello-agent")
def hello_agent(name: str):
    return f"Hello, {name}!"

result = hello_agent("World")
print(result)  # Hello, World!
```

### 3. View in Dashboard

Open [http://localhost:3000](http://localhost:3000) in your browser to see your traces.

## Framework Integrations

### LangChain

```python
from agenttrace.integrations.langchain import LangChainTracer
from langchain.chains import LLMChain
from langchain.llms import OpenAI

tracer = LangChainTracer(
    api_key="your-api-key",
    project="langchain-project"
)

llm = OpenAI(temperature=0.9)
chain = LLMChain(
    llm=llm,
    callbacks=[tracer]
)

result = chain.run("What is AI?")
```

### CrewAI

```python
from agenttrace.integrations.crewai import CrewAITracer
from crewai import Crew, Agent, Task

tracer = CrewAITracer(
    api_key="your-api-key",
    project="crewai-project"
)

crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    callbacks=[tracer]
)

result = crew.kickoff()
```

## Next Steps

- [SDK Reference](sdk-reference.md) - Learn about all SDK features
- [Architecture](architecture.md) - Understand how AgentTrace works
- Check out [examples](../examples/) for more use cases

## Troubleshooting

### Connection Refused

Make sure all services are running:

```bash
# Check API
curl http://localhost:8000/health

# Check dashboard
curl http://localhost:3000
```

### Database Connection Error

Verify PostgreSQL is running and the connection string is correct:

```bash
psql postgresql://user:password@localhost:5432/agenttrace
```

### Redis Connection Error

Check if Redis is running:

```bash
redis-cli ping
# Should return PONG
```

## Getting Help

- [GitHub Issues](https://github.com/yourusername/agenttrace/issues)
- [Discussions](https://github.com/yourusername/agenttrace/discussions)
- [Documentation](https://docs.agenttrace.dev)
