# Critical Files Reference

Quick reference for the most important files in your AgentTrace monorepo.

---

## 🐍 Python SDK - PyPI Package

### 1. `packages/sdk-python/pyproject.toml`

**Purpose:** Python package configuration for PyPI publishing

**Key Sections:**
- Package metadata (name, version, description)
- Dependencies management
- Build system configuration
- Optional dependencies for frameworks (langchain, crewai)
- Tool configurations (pytest, black, ruff, mypy)

**To publish to PyPI:**
```bash
cd packages/sdk-python
python -m build
twine upload dist/*
```

---

### 2. `packages/sdk-python/src/agenttrace/__init__.py`

**Purpose:** SDK entry point and version declaration

```python
"""AgentTrace Python SDK - AI Agent Observability Platform"""

__version__ = "0.1.0"

from .client import AgentTrace
from .tracer import Tracer, Span
from .config import Config

__all__ = ["AgentTrace", "Tracer", "Span", "Config"]
```

**Usage:**
```python
from agenttrace import AgentTrace

trace = AgentTrace(api_key="...", project="...")
```

---

### 3. `packages/sdk-python/src/agenttrace/client.py`

**Purpose:** Main SDK client with decorator and context manager

**Key Features:**
- `@trace_agent()` decorator
- `start_trace()` context manager
- Automatic error tracking
- Metadata and tags support

**Example Usage:**
```python
from agenttrace import AgentTrace

trace = AgentTrace(api_key="key", project="proj")

# Decorator
@trace.trace_agent(name="my-agent", tags=["prod"])
def my_function():
    return "result"

# Context manager
with trace.start_trace("operation") as span:
    span.log("Processing...")
    span.set_metadata("user_id", 123)
```

---

### 4. `packages/sdk-python/src/agenttrace/evals/` - Evaluations Framework

**Already Implemented! ✅**

Your evaluation framework includes:

#### `evals/models.py`
- `EvalScore`: Individual score with threshold support
- `EvalResult`: Single evaluator result
- `EvalSummary`: Aggregated results across evaluators

#### `evals/base.py`
- `Evaluator`: Abstract base class
- `FunctionEvaluator`: Function-based evaluator wrapper
- `@register_evaluator` decorator

#### `evals/registry.py`
- `EvaluatorRegistry`: Central registry for all evaluators
- Global registry access via `get_registry()`

**Example Usage:**
```python
from agenttrace.evals import Evaluator, EvalResult, EvalScore, Trace

class AccuracyEvaluator(Evaluator):
    @property
    def name(self) -> str:
        return "accuracy"

    @property
    def description(self) -> str:
        return "Evaluates response accuracy"

    async def evaluate(self, trace: Trace) -> EvalResult:
        score = EvalScore(name="accuracy", value=0.95, threshold=0.8)
        return EvalResult(
            evaluator_name=self.name,
            scores={"accuracy": score}
        )
```

---

## ⚛️ Next.js Dashboard

### 5. `apps/dashboard/package.json`

**Purpose:** Node.js package configuration

**Key Dependencies:**
- `next@14.1.0` - App Router
- `react@18.2.0`
- `tailwindcss@3.4.1`
- `@tanstack/react-query@5.17.19` - Data fetching
- `recharts@2.10.4` - Charts

**Scripts:**
```json
{
  "dev": "next dev",          // Development server
  "build": "next build",      // Production build
  "start": "next start",      // Production server
  "lint": "next lint"         // ESLint
}
```

---

### 6. `apps/dashboard/tsconfig.json`

**Purpose:** TypeScript configuration

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "jsx": "preserve",
    "paths": {
      "@/*": ["./src/*"]   // Path alias for imports
    }
  }
}
```

**Usage of path aliases:**
```typescript
import { Button } from '@/components/Button'  // Instead of '../../../components/Button'
```

---

### 7. `apps/dashboard/src/app/layout.tsx`

**Purpose:** Root layout component (App Router)

```tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AgentTrace - AI Agent Observability',
  description: 'Observability and tracing platform for AI agents',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
```

**Key Points:**
- Defines global metadata (title, description)
- Loads Google Fonts
- Wraps all pages with consistent layout

---

### 8. `apps/dashboard/tailwind.config.js`

**Purpose:** Tailwind CSS configuration

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
          50: '#f0f9ff',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
      },
    },
  },
}
```

**Usage:**
```tsx
<button className="bg-primary-500 hover:bg-primary-600">
  Click me
</button>
```

---

## 🔌 FastAPI Backend

### 9. `apps/api/main.py`

**Purpose:** FastAPI application entry point

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AgentTrace API",
    description="API for AI agent tracing and observability",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from src.api.routes import traces, projects, analytics
app.include_router(traces.router, prefix="/api/v1/traces", tags=["traces"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])

@app.get("/")
async def root():
    return {"message": "AgentTrace API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Access API docs:** http://localhost:8000/docs

---

### 10. `apps/api/src/config.py`

**Purpose:** Application configuration with Pydantic Settings

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

**Loads from `.env` automatically!**

---

### 11. `apps/api/requirements.txt`

**Purpose:** Python dependencies for API service

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.6.0
pydantic-settings==2.1.0
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
redis==5.0.1
httpx==0.26.0
python-jose[cryptography]==3.3.0
```

**Install:**
```bash
pip install -r requirements.txt
```

---

## 🔧 Root Configuration

### 12. `.gitignore`

**Purpose:** Prevent committing sensitive/generated files

**Covers:**
- Python: `__pycache__/`, `*.pyc`, `venv/`, `*.egg-info/`
- Node: `node_modules/`, `.next/`, `npm-debug.log`
- Go: `*.exe`, `*.out`
- IDEs: `.vscode/`, `.idea/`, `.DS_Store`
- Env: `.env`, `.env.local`, `.env.*.local`

---

### 13. `.env.example`

**Purpose:** Template for environment variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/agenttrace
REDIS_URL=redis://localhost:6379

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
JWT_SECRET=your-secret-key-here

# Dashboard Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=your-nextauth-secret

# SDK Configuration
AGENTTRACE_API_KEY=your-api-key
AGENTTRACE_PROJECT=default
```

**Setup:**
```bash
cp .env.example .env
# Edit .env with real values
```

---

### 14. `README.md`

**Purpose:** Project introduction and quick start

**Sections:**
- Project overview
- Features
- Quick start guide
- Installation instructions
- Usage examples
- Documentation links
- Contributing guidelines

---

### 15. `LICENSE`

**Purpose:** MIT License

Standard MIT license text - allows commercial use, modification, distribution.

---

### 16. `docker-compose.yml`

**Purpose:** Local development environment

**Services:**
- `postgres` - Database (port 5432)
- `redis` - Cache (port 6379)
- `kafka` + `zookeeper` - Message queue
- `api` - FastAPI backend (port 8000)
- `ingestion` - Go service (port 8001)
- `dashboard` - Next.js frontend (port 3000)

**Usage:**
```bash
docker-compose up -d     # Start all services
docker-compose logs -f   # View logs
docker-compose down      # Stop all services
```

---

## 🎯 Common Development Tasks

### Start Development Environment

```bash
# Full stack with Docker
docker-compose up -d

# Or manual (3 terminals)
# Terminal 1
cd apps/api && python main.py

# Terminal 2
cd apps/dashboard && npm run dev

# Terminal 3
cd apps/ingestion && go run main.go
```

### Install SDK for Development

```bash
cd packages/sdk-python
pip install -e ".[dev]"
pytest  # Run tests
```

### Build Dashboard for Production

```bash
cd apps/dashboard
npm run build
npm start
```

### Run Tests

```bash
# SDK tests
cd packages/sdk-python && pytest

# API tests
cd apps/api && pytest tests/

# Dashboard tests
cd apps/dashboard && npm test
```

### Format Code

```bash
# Python
black packages/sdk-python/src
ruff check packages/sdk-python/src

# TypeScript
cd apps/dashboard
npm run lint
```

---

## 🚀 Deployment Checklist

### Before Publishing SDK to PyPI:

1. ✅ Update version in `pyproject.toml`
2. ✅ Update `__version__` in `__init__.py`
3. ✅ Run tests: `pytest`
4. ✅ Build: `python -m build`
5. ✅ Publish: `twine upload dist/*`

### Before Deploying API:

1. ✅ Set production environment variables
2. ✅ Run database migrations
3. ✅ Build Docker image
4. ✅ Test health endpoint
5. ✅ Configure monitoring

### Before Deploying Dashboard:

1. ✅ Set `NEXT_PUBLIC_API_URL`
2. ✅ Build: `npm run build`
3. ✅ Test production build locally
4. ✅ Deploy to Vercel/Netlify
5. ✅ Configure custom domain

---

## 📚 Additional Resources

- **Full Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **GitHub**: https://github.com/artbyoscar/agenttrace

---

*Last updated: 2025*
