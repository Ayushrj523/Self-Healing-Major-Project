# ═══════════════════════════════════════════════════════════════
# SENTINELS v2.0 — One-Command Setup Script (Windows PowerShell)
# Usage: .\scripts\setup.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "  SENTINELS v2.0 — Setup" -ForegroundColor White
Write-Host "  ======================" -ForegroundColor DarkGray
Write-Host ""

# ─── Step 1: Prerequisites Check ────────────────────────────
Write-Host "[1/7] Checking prerequisites..." -ForegroundColor DarkGray

$prerequisites = @("docker", "kubectl", "helm", "k3d", "python", "node", "npm")
$missing = @()

foreach ($cmd in $prerequisites) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        $missing += $cmd
    }
}

if ($missing.Count -gt 0) {
    Write-Host "  Missing: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "  Install these tools and try again." -ForegroundColor Red
    exit 1
}
Write-Host "  All prerequisites found." -ForegroundColor Green

# ─── Step 2: Start Docker Infrastructure ─────────────────────
Write-Host "[2/7] Starting Docker infrastructure (PostgreSQL + Redis)..." -ForegroundColor DarkGray
Set-Location $ROOT
docker compose -f docker-compose.dev.yml up -d postgres redis
Start-Sleep -Seconds 5

# Wait for PostgreSQL
$maxRetries = 30
$retry = 0
while ($retry -lt $maxRetries) {
    $result = docker exec sentinels-postgres pg_isready -U sentinels 2>$null
    if ($LASTEXITCODE -eq 0) { break }
    $retry++
    Start-Sleep -Seconds 1
}
if ($retry -eq $maxRetries) {
    Write-Host "  PostgreSQL failed to start." -ForegroundColor Red
    exit 1
}
Write-Host "  PostgreSQL and Redis are ready." -ForegroundColor Green

# ─── Step 3: Setup Python Virtual Environments ───────────────
Write-Host "[3/7] Setting up Python virtual environments..." -ForegroundColor DarkGray

$pythonServices = @(
    "apps\sentinels\healer",
    "apps\sentinels\metrics-aggregator"
)

foreach ($svc in $pythonServices) {
    $svcPath = Join-Path $ROOT $svc
    $venvPath = Join-Path $svcPath ".venv"
    $reqPath = Join-Path $svcPath "requirements.txt"

    if (-not (Test-Path $venvPath)) {
        Write-Host "  Creating venv: $svc" -ForegroundColor DarkGray
        python -m venv $venvPath
    }

    $pipPath = Join-Path $venvPath "Scripts\pip.exe"
    if (Test-Path $reqPath) {
        & $pipPath install -r $reqPath --quiet 2>$null
    }
}
Write-Host "  Virtual environments ready." -ForegroundColor Green

# ─── Step 4: Install Dashboard Dependencies ──────────────────
Write-Host "[4/7] Installing dashboard dependencies..." -ForegroundColor DarkGray
$dashboardPath = Join-Path $ROOT "apps\sentinels\dashboard"
Set-Location $dashboardPath
if (-not (Test-Path "node_modules")) {
    npm install --silent 2>$null
}
Write-Host "  Dashboard dependencies installed." -ForegroundColor Green

# ─── Step 5: Start SENTINELS Services ────────────────────────
Write-Host "[5/7] Starting SENTINELS services..." -ForegroundColor DarkGray

# Healer Agent
$healerPath = Join-Path $ROOT "apps\sentinels\healer"
$healerVenv = Join-Path $healerPath ".venv\Scripts\python.exe"
Start-Process -FilePath $healerVenv -ArgumentList "main.py" -WorkingDirectory $healerPath -WindowStyle Minimized
Write-Host "  Healer Agent started on :5000" -ForegroundColor DarkGray

Start-Sleep -Seconds 2

# Metrics Aggregator
$metricsPath = Join-Path $ROOT "apps\sentinels\metrics-aggregator"
$metricsVenv = Join-Path $metricsPath ".venv\Scripts\python.exe"
Start-Process -FilePath $metricsVenv -ArgumentList "main.py" -WorkingDirectory $metricsPath -WindowStyle Minimized
Write-Host "  Metrics Aggregator started on :5050" -ForegroundColor DarkGray

Start-Sleep -Seconds 2

# Dashboard
Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory $dashboardPath -WindowStyle Minimized
Write-Host "  Dashboard started on :3000" -ForegroundColor DarkGray

Write-Host "  All services started." -ForegroundColor Green

# ─── Step 6: Health Checks ───────────────────────────────────
Write-Host "[6/7] Running health checks..." -ForegroundColor DarkGray
Start-Sleep -Seconds 5

$endpoints = @(
    @{ Name = "Healer Agent"; Url = "http://127.0.0.1:5000/health" },
    @{ Name = "Metrics Aggregator"; Url = "http://127.0.0.1:5050/health" }
)

foreach ($ep in $endpoints) {
    try {
        $response = Invoke-RestMethod -Uri $ep.Url -TimeoutSec 5
        Write-Host "  $($ep.Name): OK" -ForegroundColor Green
    } catch {
        Write-Host "  $($ep.Name): FAILED" -ForegroundColor Red
    }
}

# ─── Step 7: Summary ────────────────────────────────────────
Write-Host ""
Write-Host "[7/7] Setup complete." -ForegroundColor Green
Write-Host ""
Write-Host "  Services:" -ForegroundColor White
Write-Host "    Dashboard:          http://localhost:3000" -ForegroundColor DarkGray
Write-Host "    Healer Agent:       http://127.0.0.1:5000" -ForegroundColor DarkGray
Write-Host "    Metrics Aggregator: http://127.0.0.1:5050" -ForegroundColor DarkGray
Write-Host "    PostgreSQL:         127.0.0.1:5432" -ForegroundColor DarkGray
Write-Host "    Redis:              127.0.0.1:6379" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Open http://localhost:3000 in your browser." -ForegroundColor White
Write-Host ""
