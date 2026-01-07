# AgentTrace - Quick Start Guide

Get up and running with AgentTrace in 5 minutes! ⚡

---

## 📋 Prerequisites

Ensure you have installed:
- ✅ Python 3.9 or higher
- ✅ Node.js 18 or higher
- ✅ PostgreSQL 14 or higher
- ✅ Redis 6 or higher
- ✅ Docker (optional, but recommended)

---

## 🚀 Method 1: Docker (Recommended)

**Fastest way to get started!**

### Step 1: Setup Environment

```bash
# Navigate to project
cd C:\Users\OscarNuñez\Desktop\agenttrace

# Copy environment file
cp .env.example .env

# Edit .env if needed (optional for local dev)
```

### Step 2: Start All Services

```bash
docker-compose up -d
```

This starts:
- PostgreSQL (localhost:5432)
- Redis (localhost:6379)
- API (localhost:8000)
- Dashboard (localhost:3000)
- Ingestion (localhost:8001)

### Step 3: Verify Services

```bash
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f

# Test API
curl http://localhost:8000/health

# Test Dashboard
# Open: http://localhost:3000
```

### Step 4: Install SDK

```bash
cd packages/sdk-python
pip install -e ".[dev]"
```

### Step 5: Run Your First Trace

```python
from agenttrace import AgentTrace

trace = AgentTrace(
    api_key="dev-key",
    project="quickstart",
    api_url="http://localhost:8000"
)

@trace.trace_agent(name="hello-world")
def hello_agent():
    return "Hello from AgentTrace!"

result = hello_agent()
print(result)

# View trace at: http://localhost:3000
```

**✅ You're done! Visit http://localhost:3000 to see your traces.**

---

## 🛠️ Method 2: Manual Setup

**More control, requires manual service management**

### Step 1: Setup Environment

```bash
cd C:\Users\OscarNuñez\Desktop\agenttrace
cp .env.example .env
```

Edit `.env`:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agenttrace
REDIS_URL=redis://localhost:6379
API_PORT=8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Step 2: Start Database Services

```bash
# Start PostgreSQL
# Windows: Use PostgreSQL service or run via Docker
docker run -d --name agenttrace-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agenttrace \
  -p 5432:5432 \
  postgres:14

# Start Redis
docker run -d --name agenttrace-redis \
  -p 6379:6379 \
  redis:6-alpine
```

### Step 3: Install Dependencies

```powershell
# Run the setup script
.\scripts\setup.ps1

# Or manually:

# Install SDK
cd packages\sdk-python
pip install -e ".[dev]"

# Install API dependencies
cd ..\..\apps\api
pip install -r requirements.txt

# Install Dashboard dependencies
cd ..\dashboard
npm install
```

### Step 4: Start Services (3 Terminals)

**Terminal 1 - API:**
```bash
cd apps/api
python main.py
# Runs at: http://localhost:8000
```

**Terminal 2 - Dashboard:**
```bash
cd apps/dashboard
npm run dev
# Runs at: http://localhost:3000
```

**Terminal 3 - Ingestion (Optional):**
```bash
cd apps/ingestion
go run main.go
# Runs at: http://localhost:8001
```

### Step 5: Verify Setup

```bash
# Test API
curl http://localhost:8000/health
# Response: {"status":"healthy"}

# Test API docs
# Open: http://localhost:8000/docs

# Test Dashboard
# Open: http://localhost:3000
```

### Step 6: Your First Trace

Create `test_trace.py`:

```python
from agenttrace import AgentTrace

# Initialize client
trace = AgentTrace(
    api_key="dev-key",
    project="my-first-project",
    api_url="http://localhost:8000"
)

# Method 1: Decorator
@trace.trace_agent(name="calculator", tags=["math"])
def calculate(a: int, b: int) -> int:
    return a + b

result = calculate(5, 3)
print(f"Result: {result}")

# Method 2: Context Manager
with trace.start_trace("manual-trace") as span:
    span.log("Starting computation")
    span.set_metadata("operation", "multiply")

    result = 10 * 5

    span.set_metadata("result", result)
    span.log("Computation complete")

print("✅ Traces sent! Check http://localhost:3000")
```

Run it:
```bash
python test_trace.py
```

---

## 📚 Next Steps

### 1. Try Framework Integrations

#### LangChain Example

```bash
cd examples/langchain-example
pip install -r requirements.txt

# Set your OpenAI key
export OPENAI_API_KEY=your-key

# Run example
python main.py
```

#### CrewAI Example

```bash
cd examples/crewai-example
pip install -r requirements.txt
python main.py
```

#### OpenAI Agents Example

```bash
cd examples/openai-agents-example
pip install -r requirements.txt
python main.py
```

### 2. Explore the Evaluations Framework

```python
from agenttrace.evals import (
    Evaluator,
    EvalResult,
    EvalScore,
    register_evaluator
)

# Create a custom evaluator
@register_evaluator(name="quality", description="Checks output quality")
async def quality_evaluator(trace):
    # Your evaluation logic
    score = EvalScore(
        name="quality",
        value=0.85,  # 0.0 to 1.0
        threshold=0.7
    )

    return EvalResult(
        evaluator_name="quality",
        scores={"quality": score},
        feedback="Good quality output"
    )
```

### 3. Build Your First Dashboard Page

Create `apps/dashboard/src/app/traces/page.tsx`:

```tsx
export default function TracesPage() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Traces</h1>
      <div className="grid grid-cols-3 gap-4">
        <div className="p-6 bg-white rounded-lg shadow">
          <h2 className="text-xl font-semibold">Total Traces</h2>
          <p className="text-3xl mt-2">1,234</p>
        </div>
        {/* Add more cards */}
      </div>
    </div>
  )
}
```

Visit: http://localhost:3000/traces

### 4. Add API Endpoints

Create `apps/api/src/api/routes/custom.py`:

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/custom")
async def custom_endpoint():
    return {"message": "My custom endpoint"}
```

Add to `apps/api/main.py`:

```python
from src.api.routes import custom
app.include_router(custom.router, prefix="/api/v1/custom", tags=["custom"])
```

---

## 🧪 Running Tests

```bash
# SDK tests
cd packages/sdk-python
pytest tests/ -v

# API tests
cd apps/api
pytest tests/ -v

# Dashboard tests
cd apps/dashboard
npm test
```

---

## 🐛 Troubleshooting

### Issue: Port already in use

```bash
# Find process using port
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill process
taskkill /PID <PID> /F
```

### Issue: Database connection failed

```bash
# Check PostgreSQL is running
docker ps | findstr postgres

# Check connection
psql postgresql://postgres:postgres@localhost:5432/agenttrace
```

### Issue: Module not found

```bash
# Reinstall SDK in development mode
cd packages/sdk-python
pip install -e ".[dev]"
```

### Issue: Docker containers won't start

```bash
# View logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🎯 Development Workflow

### Daily Development

```bash
# Start everything
docker-compose up -d

# View logs
docker-compose logs -f api
docker-compose logs -f dashboard

# Stop everything
docker-compose down
```

### Making Changes

**SDK Changes:**
```bash
cd packages/sdk-python
# Make changes
pytest  # Test
black . # Format
```

**API Changes:**
```bash
cd apps/api
# Make changes
# API auto-reloads with uvicorn --reload
```

**Dashboard Changes:**
```bash
cd apps/dashboard
# Make changes
# Next.js auto-reloads in dev mode
```

### Before Committing

```bash
# Format Python code
black packages/sdk-python/src apps/api/src
ruff check packages/sdk-python/src apps/api/src

# Format TypeScript
cd apps/dashboard
npm run lint

# Run all tests
pytest  # In SDK and API directories
npm test  # In dashboard directory
```

---

## 📖 Documentation

- 📘 **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Complete project overview
- 📗 **[CRITICAL_FILES_REFERENCE.md](CRITICAL_FILES_REFERENCE.md)** - File-by-file reference
- 📕 **[Getting Started](docs/getting-started.md)** - Detailed setup guide
- 📙 **[SDK Reference](docs/sdk-reference.md)** - SDK API documentation
- 📔 **[Architecture](docs/architecture.md)** - System architecture

---

## 💡 VS Code Setup

Open the workspace file for best experience:

```bash
code agenttrace.code-workspace
```

This configures:
- Multi-root workspace
- Python formatting (Black + Ruff)
- TypeScript formatting (Prettier)
- Debugging configurations
- Recommended extensions
- Tasks for common operations

---

## 🚢 Deployment

### Deploy to Production

**SDK to PyPI:**
```bash
cd packages/sdk-python
python -m build
twine upload dist/*
```

**API to Cloud:**
```bash
cd apps/api
docker build -t agenttrace-api .
# Push to your container registry
```

**Dashboard to Vercel:**
```bash
cd apps/dashboard
npm run build
vercel deploy --prod
```

---

## 🆘 Getting Help

- 📝 **GitHub Issues:** https://github.com/artbyoscar/agenttrace/issues
- 💬 **Discussions:** https://github.com/artbyoscar/agenttrace/discussions
- 📧 **Email:** support@agenttrace.dev

---

## 🎉 You're All Set!

You now have a fully functional AgentTrace development environment!

**What to do next:**
1. ✅ Run the example traces
2. ✅ Explore the dashboard
3. ✅ Try the evaluations framework
4. ✅ Build your first integration
5. ✅ Read the architecture docs

Happy tracing! 🚀
