# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for the AgentTrace monorepo.

## Workflows

### 🔄 CI Workflow (`ci.yml`)

The main Continuous Integration workflow that runs on every push to `main` and on all pull requests.

#### Triggers
- Push to `main` branch
- Pull requests targeting `main` branch

#### Jobs Overview

**Python SDK** (`packages/sdk-python/`)
- ✅ **sdk-test**: Run pytest with coverage reporting
- ✅ **sdk-lint**: Lint code with Ruff
- ✅ **sdk-typecheck**: Type checking with mypy

**Dashboard** (`apps/dashboard/`)
- ✅ **dashboard-test**: Run Jest tests
- ✅ **dashboard-lint**: Lint with ESLint
- ✅ **dashboard-typecheck**: TypeScript type checking
- ✅ **dashboard-build**: Build Next.js application

**API** (`apps/api/`)
- ✅ **api-test**: Run pytest with PostgreSQL and Redis services
- ✅ **api-lint**: Lint code with Ruff

**Docker**
- ✅ **docker-build**: Build Docker images (PR only)

**Status**
- ✅ **ci-success**: Final check that all jobs passed

#### Job Details

##### SDK Test & Coverage
```yaml
- Python 3.11
- Install dependencies from pyproject.toml
- Run pytest with coverage
- Upload coverage to Codecov
```

**Commands run:**
```bash
cd packages/sdk-python
pip install -e ".[dev]"
pytest tests/ --cov=agenttrace --cov-report=xml -v
```

##### SDK Lint
```yaml
- Python 3.11
- Install Ruff
- Check code style and formatting
```

**Commands run:**
```bash
cd packages/sdk-python
ruff check src/ tests/
ruff format --check src/ tests/
```

##### SDK Type Check
```yaml
- Python 3.11
- Install dependencies + mypy
- Run mypy type checker
```

**Commands run:**
```bash
cd packages/sdk-python
pip install -e ".[dev]"
mypy src/
```

##### Dashboard Test
```yaml
- Node.js 20
- Install dependencies with npm ci
- Run Jest tests
```

**Commands run:**
```bash
cd apps/dashboard
npm ci
npm test -- --passWithNoTests
```

##### Dashboard Lint
```yaml
- Node.js 20
- Install dependencies
- Run ESLint
```

**Commands run:**
```bash
cd apps/dashboard
npm ci
npm run lint
```

##### Dashboard Type Check
```yaml
- Node.js 20
- Install dependencies
- Run TypeScript compiler in check mode
```

**Commands run:**
```bash
cd apps/dashboard
npm ci
npx tsc --noEmit
```

##### Dashboard Build
```yaml
- Node.js 20
- Install dependencies
- Build Next.js application
```

**Commands run:**
```bash
cd apps/dashboard
npm ci
npm run build
```

##### API Test
```yaml
- Python 3.11
- PostgreSQL 14 service
- Redis 6 service
- Install dependencies
- Run pytest
```

**Services:**
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

**Commands run:**
```bash
cd apps/api
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest tests/ -v
```

**Environment:**
- `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agenttrace_test`
- `REDIS_URL=redis://localhost:6379`
- `JWT_SECRET=test-secret-key`

##### API Lint
```yaml
- Python 3.11
- Install Ruff
- Check code style
```

**Commands run:**
```bash
cd apps/api
ruff check src/
ruff format --check src/
```

##### Docker Build
```yaml
- Only runs on Pull Requests
- Build API Docker image
- Build Dashboard Docker image
- Uses GitHub Actions cache for layers
```

**Images built:**
- `agenttrace-api:test`
- `agenttrace-dashboard:test`

##### CI Success
```yaml
- Depends on all other jobs
- Only runs if all jobs pass
- Provides single status check for branch protection
```

---

### 🚀 Release Workflow (`release.yml`)

Workflow for publishing releases when version tags are pushed.

#### Triggers
- Push of tags matching `v*` (e.g., `v0.1.0`, `v1.0.0`)

#### Jobs
- **release-pypi**: Publish SDK to PyPI
- **release-docker**: Publish Docker images
- **create-github-release**: Create GitHub release

#### Usage
```bash
# Tag a new version
git tag v0.1.0
git push origin v0.1.0

# GitHub Actions will automatically:
# 1. Build and publish SDK to PyPI
# 2. Build and publish Docker images
# 3. Create GitHub release
```

---

## Status Badges

Add these to your README.md:

```markdown
[![CI](https://github.com/artbyoscar/agenttrace/actions/workflows/ci.yml/badge.svg)](https://github.com/artbyoscar/agenttrace/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/artbyoscar/agenttrace/branch/main/graph/badge.svg)](https://codecov.io/gh/artbyoscar/agenttrace)
```

---

## Branch Protection Rules

Recommended branch protection settings for `main`:

1. **Require a pull request before merging**
   - Require approvals: 1
   - Dismiss stale approvals when new commits are pushed

2. **Require status checks to pass before merging**
   - Require branches to be up to date before merging
   - Status checks that are required:
     - `CI Success`

3. **Require conversation resolution before merging**

4. **Do not allow bypassing the above settings**

### Setting up branch protection

1. Go to: `https://github.com/artbyoscar/agenttrace/settings/branches`
2. Click "Add rule"
3. Branch name pattern: `main`
4. Enable settings above
5. Save changes

---

## Secrets Required

Configure these secrets in your GitHub repository settings:

### For CI Workflow
- `CODECOV_TOKEN` (optional): For code coverage reporting
  - Get from: https://codecov.io/

### For Release Workflow
- `PYPI_API_TOKEN`: For publishing to PyPI
  - Get from: https://pypi.org/manage/account/token/

- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password or access token
  - Get from: https://hub.docker.com/settings/security

### Setting secrets

1. Go to: `https://github.com/artbyoscar/agenttrace/settings/secrets/actions`
2. Click "New repository secret"
3. Add each secret listed above
4. Save

---

## Caching Strategy

The workflow uses several caching mechanisms to speed up builds:

### Python Dependencies
```yaml
- uses: actions/setup-python@v5
  with:
    cache: 'pip'
    cache-dependency-path: packages/sdk-python/pyproject.toml
```

### Node.js Dependencies
```yaml
- uses: actions/setup-node@v4
  with:
    cache: 'npm'
    cache-dependency-path: apps/dashboard/package-lock.json
```

### Docker Layers
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

This significantly reduces workflow run times on subsequent runs.

---

## Local Testing

Run the same checks locally before pushing:

### SDK
```bash
cd packages/sdk-python

# Tests
pytest tests/ --cov=agenttrace -v

# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Type check
mypy src/
```

### Dashboard
```bash
cd apps/dashboard

# Tests
npm test

# Lint
npm run lint

# Type check
npx tsc --noEmit

# Build
npm run build
```

### API
```bash
cd apps/api

# Tests (requires PostgreSQL and Redis)
pytest tests/ -v

# Lint
ruff check src/
ruff format --check src/
```

---

## Troubleshooting

### Common Issues

**Issue: Test failures in CI but passes locally**
- Ensure you're using the same Python/Node version
- Check for missing dependencies
- Verify environment variables are set

**Issue: Linting failures**
- Run `ruff format .` locally to auto-fix
- Check `ruff.toml` for configuration

**Issue: Type checking failures**
- Run `mypy src/` locally
- Add type stubs for missing packages
- Use `# type: ignore` sparingly with comments

**Issue: Docker build failures**
- Test Docker build locally:
  ```bash
  docker build -f apps/api/Dockerfile .
  docker build -f apps/dashboard/Dockerfile .
  ```

**Issue: Coverage upload failures**
- Check `CODECOV_TOKEN` is set
- Verify coverage.xml is generated
- Check Codecov service status

---

## Workflow Optimization Tips

1. **Use caching** - Already enabled for pip, npm, and Docker
2. **Parallel jobs** - Jobs run in parallel by default
3. **Conditional execution** - Docker builds only on PRs
4. **Fail fast** - Jobs fail immediately on error
5. **Minimal dependencies** - Only install what's needed per job

---

## Monitoring

### View Workflow Runs
- All runs: `https://github.com/artbyoscar/agenttrace/actions`
- CI runs: `https://github.com/artbyoscar/agenttrace/actions/workflows/ci.yml`
- Release runs: `https://github.com/artbyoscar/agenttrace/actions/workflows/release.yml`

### Metrics to Monitor
- ✅ Pass rate: Should be >95%
- ⏱️ Run time: Should be <10 minutes
- 💰 Minutes used: Monitor monthly quota
- 📊 Coverage: Should trend upward

---

## Contributing to Workflows

When modifying workflows:

1. Test in a fork first
2. Use `act` for local testing (https://github.com/nektos/act)
3. Document changes in this README
4. Update version in workflow if needed
5. Follow GitHub Actions best practices

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Actions](https://github.com/actions/setup-python)
- [Node.js Actions](https://github.com/actions/setup-node)
- [Docker Actions](https://github.com/docker/build-push-action)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
