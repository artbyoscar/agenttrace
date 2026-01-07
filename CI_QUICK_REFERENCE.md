# CI/CD Quick Reference Card

Quick commands and tips for working with the AgentTrace CI/CD pipeline.

---

## 🚀 Run All CI Checks Locally

**Before pushing**, run this:

```powershell
# Windows
.\scripts\ci-local.ps1

# Linux/macOS
./scripts/ci-local.sh
```

---

## 🔧 Component-Specific Checks

### Python SDK

```bash
cd packages/sdk-python

# Tests with coverage
pytest tests/ --cov=agenttrace --cov-report=term-missing -v

# Lint
ruff check src/ tests/

# Format (auto-fix)
ruff format src/ tests/

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

# Lint (auto-fix)
npm run lint -- --fix

# Type check
npx tsc --noEmit

# Build
npm run build
```

### API

```bash
cd apps/api

# Tests (requires PostgreSQL + Redis)
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agenttrace_test
export REDIS_URL=redis://localhost:6379
pytest tests/ -v

# Lint
ruff check src/

# Format (auto-fix)
ruff format src/
```

---

## 🎯 Pre-commit Hooks (Optional)

**One-time setup:**
```bash
pip install pre-commit
pre-commit install
```

**Manual run:**
```bash
pre-commit run --all-files
```

**Auto-runs on:**
- `git commit`

---

## 📊 CI Pipeline Status

**View all runs:**
https://github.com/artbyoscar/agenttrace/actions

**View CI workflow:**
https://github.com/artbyoscar/agenttrace/actions/workflows/ci.yml

---

## ✅ CI Jobs Overview

| Component | Jobs | Duration |
|-----------|------|----------|
| **SDK** | test, lint, typecheck | ~3 min |
| **Dashboard** | test, lint, typecheck, build | ~4 min |
| **API** | test, lint | ~2.5 min |
| **Docker** | build (PR only) | ~5 min |
| **Total** | 10 jobs (parallel) | ~6-8 min |

---

## 🐛 Quick Fixes

### Linting errors

```bash
# Python (auto-fix)
ruff format .
ruff check . --fix

# TypeScript (auto-fix)
cd apps/dashboard && npm run lint -- --fix
```

### Type errors

```bash
# Python
mypy src/
# Add type annotations or # type: ignore

# TypeScript
npx tsc --noEmit
# Fix type issues in code
```

### Test failures

```bash
# Python - run specific test
pytest tests/test_file.py::test_name -vv

# TypeScript - run specific test
npm test -- test_file.test.ts
```

### Build failures (Dashboard)

```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

---

## 📝 Commit Message Format

```
type(scope): description

body (optional)

footer (optional)
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting
- `refactor` - Code restructuring
- `test` - Tests
- `chore` - Maintenance
- `ci` - CI/CD changes

**Examples:**
```bash
git commit -m "feat(sdk): add custom evaluator support"
git commit -m "fix(api): resolve database connection leak"
git commit -m "docs(readme): update installation instructions"
git commit -m "ci(workflow): add TypeScript type checking"
```

---

## 🔒 Required Secrets (GitHub Settings)

| Secret | Purpose | Get From |
|--------|---------|----------|
| `CODECOV_TOKEN` | Coverage reports | https://codecov.io/ |
| `PYPI_API_TOKEN` | PyPI releases | https://pypi.org/manage/account/token/ |
| `DOCKER_USERNAME` | Docker Hub | Your Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub | https://hub.docker.com/settings/security |

**Add at:** `Settings → Secrets → Actions → New repository secret`

---

## 🛡️ Branch Protection (Recommended)

**For `main` branch:**

✅ Require pull request (1 approval)
✅ Require status checks: `CI Success`
✅ Require conversation resolution
✅ Require linear history

**Setup at:** `Settings → Branches → Add rule`

---

## 📦 Before Creating PR

**Checklist:**

- [ ] Run `./scripts/ci-local.sh` ✅
- [ ] All tests pass locally
- [ ] Code is formatted
- [ ] No type errors
- [ ] Commit messages follow convention
- [ ] Branch is up to date with main

**Create PR:**
```bash
git push origin feature/my-feature
# Then create PR on GitHub
```

---

## 🚢 Release Process

**Create release:**
```bash
# Tag version
git tag v0.1.0

# Push tag
git push origin v0.1.0

# GitHub Actions automatically:
# - Publishes SDK to PyPI
# - Publishes Docker images
# - Creates GitHub release
```

---

## 📚 Documentation Links

| Document | Purpose |
|----------|---------|
| [`CI_CD_GUIDE.md`](CI_CD_GUIDE.md) | Complete guide |
| [`CI_CD_SETUP_SUMMARY.md`](CI_CD_SETUP_SUMMARY.md) | Setup summary |
| [`.github/workflows/README.md`](.github/workflows/README.md) | Workflow docs |
| [`CICD_FILES_CREATED.md`](CICD_FILES_CREATED.md) | File list |

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Tests fail in CI only** | Check Python/Node versions match |
| **Linting fails** | Run `ruff format .` or `npm run lint -- --fix` |
| **Type errors** | Run `mypy src/` or `npx tsc --noEmit` |
| **Build fails** | Clear cache: `rm -rf .next node_modules && npm install` |
| **Coverage not uploading** | Check `CODECOV_TOKEN` is set |
| **Pre-commit fails** | Run `pre-commit run --all-files` to see details |

---

## 💡 Pro Tips

1. **Run checks before pushing**
   ```bash
   ./scripts/ci-local.sh
   ```

2. **Use pre-commit hooks**
   ```bash
   pre-commit install
   ```

3. **Check CI status before requesting review**
   - Wait for all checks to pass
   - Fix any failures before requesting review

4. **Keep PRs small**
   - Easier to review
   - Faster CI runs
   - Less likely to conflict

5. **Write good commit messages**
   - Clear and descriptive
   - Follow convention
   - Reference issues: `Closes #123`

---

## 🎨 Code Style

### Python
- Line length: 100
- Format: `ruff format`
- Lint: `ruff check`
- Type hints required

### TypeScript
- ESLint config: Next.js
- Format: Prettier
- Strict mode enabled

### Commit Style
- Conventional commits
- Present tense
- Lowercase except proper nouns

---

## ⚡ Performance Tips

1. **Use caching**
   - CI caches pip, npm, Docker
   - Pre-commit caches environments

2. **Run focused tests**
   ```bash
   # Python
   pytest tests/test_specific.py

   # TypeScript
   npm test -- test_specific.test.ts
   ```

3. **Skip slow tests locally** (if needed)
   ```bash
   pytest -m "not slow"
   ```

---

## 📞 Getting Help

1. Check documentation (see links above)
2. Review CI logs on GitHub
3. Run checks locally
4. Check GitHub Actions documentation
5. Ask in team chat/discussions

---

## 🎯 Quick Commands Summary

| Task | Command |
|------|---------|
| **Run all CI checks** | `./scripts/ci-local.sh` |
| **Format Python** | `ruff format .` |
| **Format TypeScript** | `npm run lint -- --fix` |
| **Run tests** | `pytest` / `npm test` |
| **Type check** | `mypy src/` / `npx tsc --noEmit` |
| **Install pre-commit** | `pre-commit install` |
| **View CI runs** | Visit Actions tab on GitHub |

---

**Keep this reference handy!** 📌

*Updated: January 2025*
