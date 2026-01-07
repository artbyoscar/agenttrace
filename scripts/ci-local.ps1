# Local CI Check Script
# Run the same checks that GitHub Actions runs

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "sdk", "api", "dashboard")]
    [string]$Component = "all"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AgentTrace - Local CI Checks" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0
$WarningCount = 0

function Run-Check {
    param(
        [string]$Name,
        [string]$Directory,
        [scriptblock]$Command
    )

    Write-Host "▶ Running: $Name" -ForegroundColor Yellow
    Write-Host "  Location: $Directory" -ForegroundColor Gray

    Push-Location $Directory

    try {
        & $Command
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ PASSED: $Name" -ForegroundColor Green
        } else {
            Write-Host "❌ FAILED: $Name" -ForegroundColor Red
            $script:ErrorCount++
        }
    }
    catch {
        Write-Host "❌ ERROR: $Name - $_" -ForegroundColor Red
        $script:ErrorCount++
    }
    finally {
        Pop-Location
    }

    Write-Host ""
}

# =============================================================================
# Python SDK Checks
# =============================================================================

if ($Component -eq "all" -or $Component -eq "sdk") {
    Write-Host "📦 Python SDK Checks" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""

    # SDK: Tests with coverage
    Run-Check `
        -Name "SDK Tests & Coverage" `
        -Directory "packages\sdk-python" `
        -Command {
            pytest tests/ --cov=agenttrace --cov-report=term-missing --cov-report=html -v
        }

    # SDK: Ruff check
    Run-Check `
        -Name "SDK Lint (Ruff Check)" `
        -Directory "packages\sdk-python" `
        -Command {
            ruff check src/ tests/
        }

    # SDK: Ruff format
    Run-Check `
        -Name "SDK Format Check (Ruff)" `
        -Directory "packages\sdk-python" `
        -Command {
            ruff format --check src/ tests/
        }

    # SDK: Type check
    Run-Check `
        -Name "SDK Type Check (mypy)" `
        -Directory "packages\sdk-python" `
        -Command {
            mypy src/
        }
}

# =============================================================================
# Dashboard Checks
# =============================================================================

if ($Component -eq "all" -or $Component -eq "dashboard") {
    Write-Host "⚛️  Dashboard Checks" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""

    # Dashboard: Tests
    Run-Check `
        -Name "Dashboard Tests" `
        -Directory "apps\dashboard" `
        -Command {
            npm test -- --passWithNoTests
        }

    # Dashboard: Lint
    Run-Check `
        -Name "Dashboard Lint (ESLint)" `
        -Directory "apps\dashboard" `
        -Command {
            npm run lint
        }

    # Dashboard: Type check
    Run-Check `
        -Name "Dashboard Type Check (TypeScript)" `
        -Directory "apps\dashboard" `
        -Command {
            npx tsc --noEmit
        }

    # Dashboard: Build
    Run-Check `
        -Name "Dashboard Build" `
        -Directory "apps\dashboard" `
        -Command {
            $env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
            npm run build
        }
}

# =============================================================================
# API Checks
# =============================================================================

if ($Component -eq "all" -or $Component -eq "api") {
    Write-Host "🔌 API Checks" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""

    # API: Tests
    Write-Host "⚠️  Note: API tests require PostgreSQL and Redis to be running" -ForegroundColor Yellow
    Write-Host ""

    Run-Check `
        -Name "API Tests" `
        -Directory "apps\api" `
        -Command {
            $env:DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/agenttrace_test"
            $env:REDIS_URL = "redis://localhost:6379"
            $env:JWT_SECRET = "test-secret-key"
            pytest tests/ -v
        }

    # API: Ruff check
    Run-Check `
        -Name "API Lint (Ruff Check)" `
        -Directory "apps\api" `
        -Command {
            ruff check src/
        }

    # API: Ruff format
    Run-Check `
        -Name "API Format Check (Ruff)" `
        -Directory "apps\api" `
        -Command {
            ruff format --check src/
        }
}

# =============================================================================
# Summary
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($ErrorCount -eq 0) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You're ready to commit and push! 🚀" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ $ErrorCount check(s) failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the errors before committing." -ForegroundColor Yellow
    exit 1
}
