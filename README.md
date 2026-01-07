# AgentTrace

[![CI](https://github.com/artbyoscar/agenttrace/actions/workflows/ci.yml/badge.svg)](https://github.com/artbyoscar/agenttrace/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/artbyoscar/agenttrace/branch/main/graph/badge.svg)](https://codecov.io/gh/artbyoscar/agenttrace)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Open-source observability and tracing platform for AI agents.

## Overview

AgentTrace provides comprehensive observability for AI agent frameworks like LangChain, CrewAI, and OpenAI Agents. Track execution flows, monitor performance, debug issues, and gain insights into your agent's behavior.

## Features

- **Real-time Tracing**: Capture detailed execution traces of agent runs
- **Performance Monitoring**: Track latency, token usage, and costs
- **Error Tracking**: Identify and debug failures in agent workflows
- **Multi-framework Support**: Works with LangChain, CrewAI, OpenAI Agents, and more
- **Beautiful Dashboard**: Visualize traces with an intuitive Next.js interface
- **Python SDK**: Easy integration with just a few lines of code

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agenttrace.git
cd agenttrace
```

2. Install dependencies:
```bash
# Install Python SDK
cd packages/sdk-python
pip install -e .

# Install dashboard dependencies
cd ../../apps/dashboard
npm install

# Install API dependencies
cd ../api
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start services:
```bash
# Using Docker
docker-compose up

# Or manually
# Start API
cd apps/api
python -m uvicorn main:app --reload

# Start dashboard
cd apps/dashboard
npm run dev
```

### Usage

```python
from agenttrace import trace_agent

# Decorate your agent function
@trace_agent(project="my-project")
def my_agent():
    # Your agent code here
    pass

# Or use context manager
with trace_agent(project="my-project") as tracer:
    # Your agent code
    pass
```

## Project Structure

```
agenttrace/
├── apps/
│   ├── api/            # FastAPI backend
│   ├── ingestion/      # Ingestion service
│   └── dashboard/      # Next.js frontend
├── packages/
│   ├── sdk-python/     # Python SDK
│   └── trace-schema/   # Shared schemas
├── docs/               # Documentation
└── examples/           # Example integrations
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [SDK Reference](docs/sdk-reference.md)
- [Architecture](docs/architecture.md)

## Examples

Check out the [examples](examples/) directory for integrations with:
- LangChain
- CrewAI
- OpenAI Agents

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourusername/agenttrace/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/agenttrace/discussions)
