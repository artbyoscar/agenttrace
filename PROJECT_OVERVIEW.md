# AgentTrace - Project Overview

**Open-source observability platform for AI agents**

📍 **Location:** `C:\Users\OscarNuñez\Desktop\agenttrace`
🔗 **GitHub:** https://github.com/artbyoscar/agenttrace

---

## 🏗️ Monorepo Structure

```
agenttrace/
├── 📦 packages/              # Reusable packages
│   ├── sdk-python/          # Python SDK for PyPI
│   └── trace-schema/        # Shared data schemas
├── 🚀 apps/                  # Application services
│   ├── api/                 # FastAPI backend
│   ├── ingestion/           # Go ingestion service
│   └── dashboard/           # Next.js frontend
├── 📚 docs/                  # Documentation
├── 💡 examples/              # Integration examples
├── 🔧 scripts/               # Setup & utility scripts
└── 🐳 docker-compose.yml    # Local development setup
```

---

## 📦 1. Python SDK Package

**Location:** `packages/sdk-python/`

### Critical Files

#### `pyproject.toml`
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "agenttrace"
version = "0.1.0"
description = "Python SDK for AgentTrace - AI Agent Observability Platform"
requires-python = ">=3.9"
dependencies = [
    "httpx>=0.26.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.23.0", "black>=24.0.0", "ruff>=0.1.0"]
langchain = ["langchain>=0.1.0"]
crewai = ["crewai>=0.1.0"]
```

#### `src/agenttrace/__init__.py`
```python
"""AgentTrace Python SDK - AI Agent Observability Platform"""

__version__ = "0.1.0"

from .client import AgentTrace
from .tracer import Tracer, Span
from .config import Config

__all__ = ["AgentTrace", "Tracer", "Span", "Config"]
```

#### `src/agenttrace/client.py`
Main client class with:
- `@trace_agent()` decorator for automatic tracing
- `start_trace()` context manager
- Integration with HTTP client for API communication

#### `src/agenttrace/evals/` - Evaluation Framework
Existing comprehensive evaluation system with:
- **`models.py`**: `EvalScore`, `EvalResult`, `EvalSummary`
- **`base.py`**: `Evaluator` abstract class, `FunctionEvaluator`
- **`registry.py`**: `EvaluatorRegistry` for managing evaluators
- **`runner.py`**: Orchestrates evaluator execution

### Test Configuration

Located in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "-v --cov=agenttrace --cov-report=term-missing"
```

### Installation

```bash
# Development installation
cd packages/sdk-python
pip install -e ".[dev]"

# With framework integrations
pip install -e ".[langchain,crewai]"
```

---

## 🚀 2. Next.js Dashboard

**Location:** `apps/dashboard/`

### Critical Files

#### `package.json`
```json
{
  "name": "agenttrace-dashboard",
  "version": "0.1.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.17.19",
    "tailwindcss": "^3.4.1",
    "recharts": "^2.10.4"
  }
}
```

#### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "noEmit": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

#### `tailwind.config.js`
```javascript
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
      },
    },
  },
}
```

#### App Router Structure

```
src/app/
├── layout.tsx        # Root layout with Inter font
├── page.tsx          # Homepage
└── globals.css       # Tailwind imports + global styles
```

**`src/app/layout.tsx`**:
```tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AgentTrace - AI Agent Observability',
  description: 'Observability and tracing platform for AI agents',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
```

### Running Locally

```bash
cd apps/dashboard
npm install
npm run dev
# Opens at http://localhost:3000
```

---

## 🔌 3. FastAPI Service

**Location:** `apps/api/`

### Critical Files

#### `main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AgentTrace API",
    description="API for AI agent tracing and observability",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AgentTrace API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

#### `requirements.txt`
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.0.0
pydantic-settings==2.1.0
sqlalchemy==2.0.25
asyncpg==0.29.0
redis==5.0.1
httpx==0.26.0
```

#### Project Structure

```
apps/api/
├── main.py                  # Entry point
├── src/
│   ├── api/
│   │   └── routes/         # API endpoints
│   │       ├── traces.py
│   │       ├── projects.py
│   │       └── analytics.py
│   ├── models/             # Database models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── config.py           # Configuration
├── requirements.txt
├── requirements-dev.txt
└── Dockerfile
```

#### `src/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### Running Locally

```bash
cd apps/api
pip install -r requirements.txt
python main.py
# Runs at http://localhost:8000
# Docs at http://localhost:8000/docs
```

---

## 🔧 4. Root Configuration

### `.gitignore`

Comprehensive coverage for:
- Python (`__pycache__/`, `*.pyc`, `venv/`)
- Node.js (`node_modules/`, `.next/`)
- Go (`*.exe`, `*.out`)
- IDEs (`.vscode/`, `.idea/`)
- Environment files (`.env`, `.env.local`)

### `README.md`

```markdown
# AgentTrace

Open-source observability and tracing platform for AI agents.

## Quick Start

1. Clone: `git clone https://github.com/artbyoscar/agenttrace.git`
2. Install SDK: `cd packages/sdk-python && pip install -e .`
3. Start services: `docker-compose up`
4. Visit dashboard: http://localhost:3000

## Usage

\```python
from agenttrace import AgentTrace

trace = AgentTrace(api_key="your-key", project="my-project")

@trace.trace_agent()
def my_agent():
    return "result"
\```

See [docs/getting-started.md](docs/getting-started.md) for full documentation.
```

### `LICENSE`

MIT License with standard terms.

### `.env.example`

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/agenttrace
REDIS_URL=redis://localhost:6379

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
JWT_SECRET=your-secret-key-here

# Dashboard
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=your-nextauth-secret

# SDK
AGENTTRACE_API_KEY=your-api-key
AGENTTRACE_PROJECT=default
```

### `docker-compose.yml`

Services configured:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Kafka + Zookeeper
- API (port 8000)
- Dashboard (port 3000)
- Ingestion service (port 8001)

---

## 🎯 Quick Commands

### Setup Everything
```powershell
.\scripts\setup.ps1
```

### Start Development Environment
```bash
# Option 1: Docker (recommended)
docker-compose up -d

# Option 2: Manual
# Terminal 1: API
cd apps/api && python main.py

# Terminal 2: Dashboard
cd apps/dashboard && npm run dev

# Terminal 3: Ingestion
cd apps/ingestion && go run main.go
```

### Install SDK Only
```bash
cd packages/sdk-python
pip install -e ".[dev]"
```

### Run Tests
```bash
# Python SDK tests
cd packages/sdk-python
pytest

# API tests
cd apps/api
pytest tests/

# Dashboard tests
cd apps/dashboard
npm test
```

---

## 📊 Project Status

✅ **Completed:**
- Monorepo structure
- Python SDK with evaluations framework
- FastAPI backend with routes
- Next.js dashboard with Tailwind
- Docker setup
- CI/CD workflows
- Documentation
- Example integrations (LangChain, CrewAI, OpenAI)

🚧 **Next Steps:**
1. Implement database models and migrations
2. Build dashboard UI components
3. Add authentication system
4. Implement real-time trace streaming
5. Create analytics engine
6. Add more evaluator types
7. Publish SDK to PyPI

---

## 📚 Documentation

- **[Getting Started](docs/getting-started.md)** - Setup and first trace
- **[SDK Reference](docs/sdk-reference.md)** - Complete SDK documentation
- **[Architecture](docs/architecture.md)** - System architecture overview

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🔗 Links

- **GitHub**: https://github.com/artbyoscar/agenttrace
- **Issues**: https://github.com/artbyoscar/agenttrace/issues
- **Discussions**: https://github.com/artbyoscar/agenttrace/discussions

---

*Built with ❤️ for the AI agent community*
