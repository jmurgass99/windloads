# Ejecuta pytest con coverage. Falla si gate < 75%.
param([switch]$Open, [switch]$IncludeSlow)

$ErrorActionPreference = "Stop"

if ($IncludeSlow) {
    $markFilter = ""
} else {
    $markFilter = "not slow"
}

if ($markFilter -eq "") {
    python -m pytest --cov --cov-report=term-missing --cov-report=html --cov-report=xml -q
} else {
    python -m pytest --cov --cov-report=term-missing --cov-report=html --cov-report=xml -q -m "$markFilter"
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Coverage gate (75%) o tests fallaron" -ForegroundColor Red
    exit 1
}
Write-Host "Coverage OK (>=75%)" -ForegroundColor Green
if ($Open) { Start-Process "htmlcov/index.html" }
