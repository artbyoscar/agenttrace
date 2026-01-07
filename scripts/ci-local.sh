#!/bin/bash
# Local CI Check Script - Linux/macOS version
# Run the same checks that GitHub Actions runs

set -e

COMPONENT="${1:-all}"
ERROR_COUNT=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo -e "  AgentTrace - Local CI Checks"
echo -e "========================================${NC}"
echo ""

run_check() {
    local name=$1
    local directory=$2
    local command=$3

    echo -e "${YELLOW}▶ Running: ${name}${NC}"
    echo -e "${GRAY}  Location: ${directory}${NC}"

    cd "$directory"

    if eval "$command"; then
        echo -e "${GREEN}✅ PASSED: ${name}${NC}"
    else
        echo -e "${RED}❌ FAILED: ${name}${NC}"
        ((ERROR_COUNT++))
    fi

    cd - > /dev/null
    echo ""
}

# =============================================================================
# Python SDK Checks
# =============================================================================

if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "sdk" ]; then
    echo -e "${CYAN}📦 Python SDK Checks"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # SDK: Tests with coverage
    run_check \
        "SDK Tests & Coverage" \
        "packages/sdk-python" \
        "pytest tests/ --cov=agenttrace --cov-report=term-missing --cov-report=html -v"

    # SDK: Ruff check
    run_check \
        "SDK Lint (Ruff Check)" \
        "packages/sdk-python" \
        "ruff check src/ tests/"

    # SDK: Ruff format
    run_check \
        "SDK Format Check (Ruff)" \
        "packages/sdk-python" \
        "ruff format --check src/ tests/"

    # SDK: Type check
    run_check \
        "SDK Type Check (mypy)" \
        "packages/sdk-python" \
        "mypy src/"
fi

# =============================================================================
# Dashboard Checks
# =============================================================================

if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "dashboard" ]; then
    echo -e "${CYAN}⚛️  Dashboard Checks"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Dashboard: Tests
    run_check \
        "Dashboard Tests" \
        "apps/dashboard" \
        "npm test -- --passWithNoTests"

    # Dashboard: Lint
    run_check \
        "Dashboard Lint (ESLint)" \
        "apps/dashboard" \
        "npm run lint"

    # Dashboard: Type check
    run_check \
        "Dashboard Type Check (TypeScript)" \
        "apps/dashboard" \
        "npx tsc --noEmit"

    # Dashboard: Build
    run_check \
        "Dashboard Build" \
        "apps/dashboard" \
        "NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build"
fi

# =============================================================================
# API Checks
# =============================================================================

if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "api" ]; then
    echo -e "${CYAN}🔌 API Checks"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    echo -e "${YELLOW}⚠️  Note: API tests require PostgreSQL and Redis to be running${NC}"
    echo ""

    # API: Tests
    run_check \
        "API Tests" \
        "apps/api" \
        "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agenttrace_test REDIS_URL=redis://localhost:6379 JWT_SECRET=test-secret-key pytest tests/ -v"

    # API: Ruff check
    run_check \
        "API Lint (Ruff Check)" \
        "apps/api" \
        "ruff check src/"

    # API: Ruff format
    run_check \
        "API Format Check (Ruff)" \
        "apps/api" \
        "ruff format --check src/"
fi

# =============================================================================
# Summary
# =============================================================================

echo -e "${CYAN}========================================"
echo -e "  Summary"
echo -e "========================================${NC}"
echo ""

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo -e "${GREEN}You're ready to commit and push! 🚀${NC}"
    exit 0
else
    echo -e "${RED}❌ ${ERROR_COUNT} check(s) failed${NC}"
    echo ""
    echo -e "${YELLOW}Please fix the errors before committing.${NC}"
    exit 1
fi
