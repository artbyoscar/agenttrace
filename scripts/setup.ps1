# AgentTrace Setup Script for Windows
# This script helps set up the AgentTrace development environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AgentTrace Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.9 or higher." -ForegroundColor Red
    exit 1
}

# Check Node.js
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js not found. Please install Node.js 18 or higher." -ForegroundColor Red
    exit 1
}

# Check Go (optional)
$goVersion = go version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Go found: $goVersion" -ForegroundColor Green
} else {
    Write-Host "! Go not found. This is optional but required for ingestion service." -ForegroundColor Yellow
}

# Check PostgreSQL
$pgVersion = psql --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ PostgreSQL found: $pgVersion" -ForegroundColor Green
} else {
    Write-Host "! PostgreSQL not found. Required for running the API." -ForegroundColor Yellow
}

# Check Redis
$redisVersion = redis-cli --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Redis found: $redisVersion" -ForegroundColor Green
} else {
    Write-Host "! Redis not found. Required for caching." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installation Options" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Install Python SDK only" -ForegroundColor White
Write-Host "2. Install API dependencies" -ForegroundColor White
Write-Host "3. Install Dashboard dependencies" -ForegroundColor White
Write-Host "4. Install everything (full setup)" -ForegroundColor White
Write-Host "5. Setup environment files" -ForegroundColor White
Write-Host "6. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Installing Python SDK..." -ForegroundColor Yellow
        Set-Location "packages\sdk-python"
        pip install -e ".[dev]"
        Write-Host "✓ Python SDK installed!" -ForegroundColor Green
    }
    "2" {
        Write-Host ""
        Write-Host "Installing API dependencies..." -ForegroundColor Yellow
        Set-Location "apps\api"
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        Write-Host "✓ API dependencies installed!" -ForegroundColor Green
    }
    "3" {
        Write-Host ""
        Write-Host "Installing Dashboard dependencies..." -ForegroundColor Yellow
        Set-Location "apps\dashboard"
        npm install
        Write-Host "✓ Dashboard dependencies installed!" -ForegroundColor Green
    }
    "4" {
        Write-Host ""
        Write-Host "Installing all dependencies..." -ForegroundColor Yellow

        # Python SDK
        Write-Host "Installing Python SDK..." -ForegroundColor Yellow
        Set-Location "packages\sdk-python"
        pip install -e ".[dev]"
        Set-Location "..\..\"

        # API
        Write-Host "Installing API dependencies..." -ForegroundColor Yellow
        Set-Location "apps\api"
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        Set-Location "..\..\"

        # Dashboard
        Write-Host "Installing Dashboard dependencies..." -ForegroundColor Yellow
        Set-Location "apps\dashboard"
        npm install
        Set-Location "..\..\"

        # Ingestion (if Go is available)
        if ($goVersion) {
            Write-Host "Installing Ingestion service dependencies..." -ForegroundColor Yellow
            Set-Location "apps\ingestion"
            go mod download
            Set-Location "..\..\"
        }

        Write-Host "✓ All dependencies installed!" -ForegroundColor Green
    }
    "5" {
        Write-Host ""
        Write-Host "Setting up environment files..." -ForegroundColor Yellow

        if (Test-Path ".env") {
            Write-Host ".env file already exists. Skipping..." -ForegroundColor Yellow
        } else {
            Copy-Item ".env.example" ".env"
            Write-Host "✓ Created .env file from .env.example" -ForegroundColor Green
            Write-Host "Please edit .env with your configuration!" -ForegroundColor Yellow
        }

        # Dashboard .env.local
        if (Test-Path "apps\dashboard\.env.local") {
            Write-Host "Dashboard .env.local already exists. Skipping..." -ForegroundColor Yellow
        } else {
            Copy-Item ".env.example" "apps\dashboard\.env.local"
            Write-Host "✓ Created apps\dashboard\.env.local" -ForegroundColor Green
        }

        Write-Host "✓ Environment files setup complete!" -ForegroundColor Green
    }
    "6" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "Invalid choice. Exiting..." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Configure your .env file with database and API settings" -ForegroundColor White
Write-Host "2. Start PostgreSQL and Redis services" -ForegroundColor White
Write-Host "3. Run the API:" -ForegroundColor White
Write-Host "   cd apps\api" -ForegroundColor Gray
Write-Host "   python main.py" -ForegroundColor Gray
Write-Host "4. Run the Dashboard:" -ForegroundColor White
Write-Host "   cd apps\dashboard" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "For more information, see the README.md or docs/getting-started.md" -ForegroundColor White
Write-Host ""
