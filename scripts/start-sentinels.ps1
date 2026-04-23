<#
.SYNOPSIS
    SENTINELS v2.0 — One-Click Startup Script
    Starts: Healer Agent (5000), Metrics Aggregator (5050), Dashboard (3000)
    
.DESCRIPTION
    This script creates virtual environments, installs dependencies,
    and starts all three SENTINELS services in separate terminal windows.
    
.NOTES
    Run from: E:\Projects\SENTINAL
    Requires: Python 3.13+, Node.js 18+
#>

param(
    [switch]$SkipInstall,
    [switch]$DashboardOnly
)

$ErrorActionPreference = "Continue"
$ROOT = $PSScriptRoot | Split-Path -Parent
$HEALER_DIR = "$ROOT\apps\sentinels\healer"
$METRICS_DIR = "$ROOT\apps\sentinels\metrics-aggregator"
$DASHBOARD_DIR = "$ROOT\apps\sentinels\dashboard"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  SENTINELS v2.0 — Command Center Startup        ║" -ForegroundColor Cyan
Write-Host "║  Healer :5000 | Metrics :5050 | Dashboard :3000 ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─── Helper: Create venv + install deps ──────────────────────
function Setup-PythonService {
    param([string]$Dir, [string]$Name)
    
    Write-Host "[$Name] Setting up..." -ForegroundColor Yellow
    
    $venvPath = "$Dir\.venv"
    
    if (-not (Test-Path "$venvPath\Scripts\python.exe")) {
        Write-Host "[$Name] Creating virtual environment..." -ForegroundColor DarkGray
        python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[$Name] ERROR: Failed to create venv" -ForegroundColor Red
            return $false
        }
    }
    
    if (-not $SkipInstall) {
        Write-Host "[$Name] Installing dependencies..." -ForegroundColor DarkGray
        & "$venvPath\Scripts\pip.exe" install --upgrade pip --quiet 2>$null
        & "$venvPath\Scripts\pip.exe" install -r "$Dir\requirements.txt" --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[$Name] ERROR: pip install failed — check requirements.txt" -ForegroundColor Red
            & "$venvPath\Scripts\pip.exe" install -r "$Dir\requirements.txt"
            return $false
        }
    }
    
    Write-Host "[$Name] Ready ✓" -ForegroundColor Green
    return $true
}

# ─── Step 1: Setup Python services ──────────────────────────
if (-not $DashboardOnly) {
    $healerOk = Setup-PythonService -Dir $HEALER_DIR -Name "Healer Agent"
    $metricsOk = Setup-PythonService -Dir $METRICS_DIR -Name "Metrics Aggregator"
    
    if (-not $healerOk -or -not $metricsOk) {
        Write-Host ""
        Write-Host "Some services failed to install. Attempting to continue..." -ForegroundColor Yellow
    }
}

# ─── Step 2: Setup Dashboard ────────────────────────────────
if (-not (Test-Path "$DASHBOARD_DIR\node_modules")) {
    Write-Host "[Dashboard] Installing npm dependencies..." -ForegroundColor Yellow
    Push-Location $DASHBOARD_DIR
    npm install --silent 2>$null
    Pop-Location
}
Write-Host "[Dashboard] Ready ✓" -ForegroundColor Green

# ─── Step 3: Start services in separate terminals ───────────
Write-Host ""
Write-Host "Starting services..." -ForegroundColor Cyan

if (-not $DashboardOnly) {
    # Healer Agent (Port 5000)
    $healerCmd = "cd '$HEALER_DIR'; .venv\Scripts\activate; Write-Host 'SENTINELS Healer Agent starting on :5000...' -ForegroundColor Cyan; python main.py"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $healerCmd -WindowStyle Normal
    Write-Host "  ✓ Healer Agent    → http://127.0.0.1:5000" -ForegroundColor Green
    
    # Wait 2s for healer to start before metrics (metrics depends on healer)
    Start-Sleep -Seconds 2
    
    # Metrics Aggregator (Port 5050)
    $metricsCmd = "cd '$METRICS_DIR'; .venv\Scripts\activate; Write-Host 'SENTINELS Metrics Aggregator starting on :5050...' -ForegroundColor Cyan; python main.py"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $metricsCmd -WindowStyle Normal
    Write-Host "  ✓ Metrics Aggregator → http://127.0.0.1:5050" -ForegroundColor Green
    
    # Wait for backends to boot
    Start-Sleep -Seconds 3
}

# Dashboard (Port 3000)
$dashCmd = "cd '$DASHBOARD_DIR'; Write-Host 'SENTINELS Dashboard starting on :3000...' -ForegroundColor Cyan; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $dashCmd -WindowStyle Normal
Write-Host "  ✓ Dashboard       → http://127.0.0.1:3000" -ForegroundColor Green

Write-Host ""
Write-Host "══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  All services started! Open http://localhost:3000" -ForegroundColor Green
Write-Host "  3 terminal windows opened — one per service" -ForegroundColor DarkGray
Write-Host "  Close the terminal windows to stop services" -ForegroundColor DarkGray
Write-Host "══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
