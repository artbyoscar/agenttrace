# CI/CD Guide for AgentTrace

Complete guide to the Continuous Integration and Continuous Deployment setup for AgentTrace.

---

## 📊 CI/CD Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Push to main / PR                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI Workflow                   │
└─────────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Python SDK  │    │  Dashboard   │    │     API      │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        ├─ Test             ├─ Test              ├─ Test
        ├─ Lint (Ruff)      ├─ Lint (ESLint)     ├─ Lint (Ruff)
        └─ Type Check       ├─ Type Check (TS)   └─ (with services)
                            └─ Build
                                   │
                                   ▼
                          ┌──────────────┐
                          │ Docker Build │
                          │  (PR only)   │
                          └──────────────┘
                                   │
                                   ▼
                          ┌──────────────┐
                          │ CI Success   │
                          │  ✅ or ❌    │
                          └──────────────┘
```

---

## 🎯 What Gets Checked

### Python SDK (`packages/sdk-python/`)

| Check | Tool | Command | Pass Criteria |
|-------|------|---------|---------------|
| **Tests** | pytest | `pytest tests/ --cov=agenttrace -v` | All tests pass, >80% coverage |
| **Lint** | Ruff | `ruff check src/ tests/` | No linting errors |
| **Format** | Ruff | `ruff format --check src/ tests/` | Code follows format rules |
| **Type Check** | mypy | `mypy src/` | No type errors |

### Dashboard (`apps/dashboard/`)

| Check | Tool | Command | Pass Criteria |
|-------|------|---------|---------------|
| **Tests** | Jest | `npm test` | All tests pass |
| **Lint** | ESLint | `npm run lint` | No linting errors |
| **Type Check** | TypeScript | `npx tsc --noEmit` | No type errors |
| **Build** | Next.js | `npm run build` | Build succeeds |

### API (`apps/api/`)

| Check | Tool | Command | Pass Criteria |
|-------|------|---------|---------------|
| **Tests** | pytest | `pytest tests/ -v` | All tests pass (with DB/Redis) |
| **Lint** | Ruff | `ruff check src/` | No linting errors |
| **Format** | Ruff | `ruff format --check src/` | Code follows format rules |

---

## 🔧 Configuration Files

### 1. Main CI Workflow

**File:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

Key features:
- ✅ Runs on push to `main` and all PRs
- ✅ 9 parallel jobs for fast execution
- ✅ Caching for pip, npm, and Docker layers
- ✅ Services (PostgreSQL, Redis) for API tests
- ✅ Coverage reporting to Codecov
- ✅ Final status check job

### 2. Ruff Configuration

**File:** [`ruff.toml`](ruff.toml)

Shared linting configuration for Python code across SDK and API:
- Line length: 100 characters
- Python version: 3.9+
- Rules: pycodestyle, pyflakes, isort, flake8-bugbear, pylint, etc.
- Format: Double quotes, space indentation

### 3. Dependabot

**File:** [`.github/dependabot.yml`](.github/dependabot.yml)

Automated dependency updates:
- Weekly schedule (Mondays at 9 AM EST)
- Separate configs for Python, npm, Go, GitHub Actions, Docker
- Auto-labeling and reviewer assignment
- Ignores major version updates for core frameworks

### 4. Pull Request Template

**File:** [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md)

Standardized PR format with:
- Description and change type
- Related issues
- Testing checklist
- Manual testing notes
- Reviewer guidelines

---

## 🚀 Running Checks Locally

### Quick Run - All Checks

**Windows (PowerShell):**
```powershell
.\scripts\ci-local.ps1
```

**Linux/macOS:**
```bash
chmod +x scripts/ci-local.sh
./scripts/ci-local.sh
```

### Run Specific Component

**Windows:**
```powershell
# SDK only
.\scripts\ci-local.ps1 -Component sdk

# API only
.\scripts\ci-local.ps1 -Component api

# Dashboard only
.\scripts\ci-local.ps1 -Component dashboard
```

**Linux/macOS:**
```bash
# SDK only
./scripts/ci-local.sh sdk

# API only
./scripts/ci-local.sh api

# Dashboard only
./scripts/ci-local.sh dashboard
```

### Manual Checks

#### Python SDK

```bash
cd packages/sdk-python

# Install dependencies
pip install -e ".[dev]"

# Run all checks
pytest tests/ --cov=agenttrace --cov-report=term-missing -v
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/

# Auto-fix formatting
ruff format src/ tests/
```

#### Dashboard

```bash
cd apps/dashboard

# Install dependencies
npm ci

# Run all checks
npm test
npm run lint
npx tsc --noEmit
npm run build

# Auto-fix formatting
npm run lint -- --fix
```

#### API

```bash
cd apps/api

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start services (if not using Docker)
docker run -d --name agenttrace-postgres-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agenttrace_test \
  -p 5432:5432 postgres:14

docker run -d --name agenttrace-redis-test \
  -p 6379:6379 redis:6-alpine

# Run checks
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agenttrace_test
export REDIS_URL=redis://localhost:6379
export JWT_SECRET=test-secret-key
pytest tests/ -v
ruff check src/
ruff format --check src/

# Auto-fix formatting
ruff format src/
```

---

## 📋 Pre-Commit Checklist

Before committing, ensure:

1. ✅ **All tests pass locally**
   ```bash
   # Run local CI script
   ./scripts/ci-local.sh
   ```

2. ✅ **Code is formatted**
   ```bash
   # Python
   ruff format packages/sdk-python/src apps/api/src

   # TypeScript
   cd apps/dashboard && npm run lint -- --fix
   ```

3. ✅ **No type errors**
   ```bash
   # Python
   mypy packages/sdk-python/src

   # TypeScript
   cd apps/dashboard && npx tsc --noEmit
   ```

4. ✅ **Coverage is maintained**
   - SDK: Keep >80% coverage
   - Check coverage report after running tests

5. ✅ **Documentation updated**
   - Update docstrings
   - Update README if needed
   - Add examples if appropriate

6. ✅ **Commit message follows convention**
   - Format: `type(scope): description`
   - Examples:
     - `feat(sdk): add custom evaluator support`
     - `fix(api): resolve database connection leak`
     - `docs(readme): update installation instructions`

---

## 🔐 Required Secrets

Configure these in GitHub repository settings:

### For CI Workflow

1. **CODECOV_TOKEN** (Optional)
   - Purpose: Upload coverage reports
   - Get from: https://codecov.io/
   - Settings: `Settings → Secrets → Actions → New repository secret`

### For Release Workflow

1. **PYPI_API_TOKEN**
   - Purpose: Publish SDK to PyPI
   - Get from: https://pypi.org/manage/account/token/
   - Scope: Entire account or specific project

2. **DOCKER_USERNAME**
   - Purpose: Push Docker images
   - Value: Your Docker Hub username

3. **DOCKER_PASSWORD**
   - Purpose: Authenticate to Docker Hub
   - Value: Docker Hub access token (recommended) or password
   - Get from: https://hub.docker.com/settings/security

---

## 🛡️ Branch Protection

Recommended settings for `main` branch:

### Setup Instructions

1. Go to: `https://github.com/artbyoscar/agenttrace/settings/branches`
2. Click "Add rule"
3. Branch name pattern: `main`
4. Enable the following:

#### Required Settings

✅ **Require a pull request before merging**
- Require approvals: 1
- Dismiss stale pull request approvals when new commits are pushed
- Require review from Code Owners

✅ **Require status checks to pass before merging**
- Require branches to be up to date before merging
- Status checks that are required:
  - `CI Success` (this is the final check job)
  - `sdk-test`
  - `sdk-lint`
  - `sdk-typecheck`
  - `dashboard-lint`
  - `dashboard-typecheck`
  - `dashboard-build`
  - `api-test`
  - `api-lint`

✅ **Require conversation resolution before merging**

✅ **Require linear history**

✅ **Do not allow bypassing the above settings**

#### Optional Settings

⬜ **Require deployments to succeed before merging**
⬜ **Lock branch** (only for production branches)

---

## 📊 Monitoring CI/CD

### View Workflow Runs

- **All workflows**: https://github.com/artbyoscar/agenttrace/actions
- **CI workflow**: https://github.com/artbyoscar/agenttrace/actions/workflows/ci.yml
- **Failed runs**: https://github.com/artbyoscar/agenttrace/actions?query=is%3Afailure

### CI Metrics to Track

| Metric | Target | How to Check |
|--------|--------|--------------|
| **Pass Rate** | >95% | Actions tab → Insights |
| **Average Duration** | <10 min | Workflow run history |
| **Failed Checks** | <5% | Filter by status |
| **Coverage Trend** | Increasing | Codecov dashboard |

### Troubleshooting Failed Runs

1. **Check the logs**
   - Click on failed job
   - Expand failed step
   - Read error message

2. **Reproduce locally**
   - Run local CI script: `./scripts/ci-local.sh`
   - Or run specific check that failed

3. **Common Issues**

   **Issue: Linting failures**
   ```bash
   # Auto-fix
   ruff format .
   ruff check . --fix
   ```

   **Issue: Type errors**
   ```bash
   # Check locally
   mypy src/
   # Add type annotations or # type: ignore
   ```

   **Issue: Test failures**
   ```bash
   # Run with verbose output
   pytest tests/ -vv
   # Debug specific test
   pytest tests/test_file.py::test_name -vv
   ```

   **Issue: Build failures (Dashboard)**
   ```bash
   # Clear cache and rebuild
   rm -rf .next node_modules
   npm install
   npm run build
   ```

---

## 🔄 CI/CD Workflow Lifecycle

### 1. Development

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ...

# Run local checks
./scripts/ci-local.sh

# Commit and push
git add .
git commit -m "feat(scope): my feature"
git push origin feature/my-feature
```

### 2. Pull Request

```bash
# Create PR on GitHub
# CI automatically runs on PR

# View checks
# GitHub PR page → Checks tab

# If checks fail
# - Fix issues locally
# - Push fix
# - CI re-runs automatically
```

### 3. Merge

```bash
# After approval and CI passes
# Merge PR via GitHub UI

# CI runs on main branch
# All checks must pass on main too
```

### 4. Release

```bash
# Tag a release
git tag v0.1.0
git push origin v0.1.0

# Release workflow automatically:
# - Builds and publishes SDK to PyPI
# - Builds and publishes Docker images
# - Creates GitHub release
```

---

## 🎨 Customizing the CI Pipeline

### Adding New Checks

Edit [`.github/workflows/ci.yml`](.github/workflows/ci.yml):

```yaml
new-check:
  name: My New Check
  runs-on: ubuntu-latest

  steps:
    - uses: actions/checkout@v4

    - name: Run my check
      run: |
        # Your check command
        echo "Running custom check"

    # Add to ci-success needs
```

### Changing Python Version

Update all Python setup steps:

```yaml
- name: Set up Python 3.12  # Changed from 3.11
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'  # Changed from 3.11
```

### Adding New Linting Rules

Edit [`ruff.toml`](ruff.toml):

```toml
[lint]
select = [
    "E",
    "W",
    "F",
    "YOUR_NEW_RULE",  # Add here
]
```

---

## 📚 Resources

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Ruff Docs**: https://docs.astral.sh/ruff/
- **pytest Docs**: https://docs.pytest.org/
- **ESLint Docs**: https://eslint.org/docs/
- **TypeScript Docs**: https://www.typescriptlang.org/docs/
- **Codecov Docs**: https://docs.codecov.com/

---

## 💡 Best Practices

1. **Keep workflows fast**
   - Use caching for dependencies
   - Run jobs in parallel when possible
   - Only run necessary checks

2. **Make checks deterministic**
   - Pin dependency versions in CI
   - Use fixed test data
   - Avoid time-dependent tests

3. **Fail fast**
   - Run quick checks first (linting)
   - Run expensive checks later (e2e tests)

4. **Monitor and improve**
   - Track CI duration
   - Optimize slow jobs
   - Update dependencies regularly

5. **Keep it simple**
   - Don't over-engineer
   - Document complex workflows
   - Make it easy to run locally

---

*Last updated: January 2025*
