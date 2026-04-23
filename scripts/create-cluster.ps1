# ═══════════════════════════════════════════════════════════════
# SENTINELS v2.0 — k3d Cluster Creation Script (PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File scripts/create-cluster.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  SENTINELS v2.0 — Cluster Setup          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check prerequisites
Write-Host "[PRE] Checking prerequisites..." -ForegroundColor Yellow

$tools = @("docker", "k3d", "kubectl", "helm")
foreach ($tool in $tools) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        Write-Host "  ERROR: '$tool' not found in PATH. Please install it first." -ForegroundColor Red
        exit 1
    }
    Write-Host "  OK: $tool found" -ForegroundColor Green
}

# Check if Docker is running
try {
    docker info 2>&1 | Out-Null
    Write-Host "  OK: Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Docker is not running. Start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if cluster already exists
$existing = k3d cluster list -o json 2>$null | ConvertFrom-Json
$clusterExists = $existing | Where-Object { $_.name -eq "sentinels" }

if ($clusterExists) {
    Write-Host "`n[1/4] Cluster 'sentinels' already exists. Starting if stopped..." -ForegroundColor Yellow
    k3d cluster start sentinels 2>$null
} else {
    Write-Host "`n[1/4] Creating k3d cluster 'sentinels'..." -ForegroundColor Yellow
    k3d cluster create sentinels `
        --servers 1 `
        --agents 2 `
        --port "127.0.0.1:3000:30000@loadbalancer" `
        --port "127.0.0.1:3001:30001@loadbalancer" `
        --port "127.0.0.1:3002:30002@loadbalancer" `
        --port "127.0.0.1:3003:30003@loadbalancer" `
        --port "127.0.0.1:9090:30090@loadbalancer" `
        --k3s-arg "--disable=traefik@server:0"
    
    Write-Host "  Cluster created successfully!" -ForegroundColor Green
}

# Verify cluster
Write-Host "`n[2/4] Verifying cluster connectivity..." -ForegroundColor Yellow
kubectl cluster-info
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Cannot connect to cluster" -ForegroundColor Red
    exit 1
}
Write-Host "  Cluster is reachable" -ForegroundColor Green

# Create namespaces
Write-Host "`n[3/4] Creating Kubernetes namespaces..." -ForegroundColor Yellow
$namespaces = @("netflix", "prime", "monitoring", "sentinels-system", "chaos", "dashboard")
foreach ($ns in $namespaces) {
    kubectl create namespace $ns --dry-run=client -o yaml | kubectl apply -f - 2>$null
    Write-Host "  Created namespace: $ns" -ForegroundColor Green
}

# Label namespaces for network policy selectors
kubectl label namespace monitoring kubernetes.io/metadata.name=monitoring --overwrite 2>$null
kubectl label namespace dashboard kubernetes.io/metadata.name=dashboard --overwrite 2>$null
kubectl label namespace sentinels-system kubernetes.io/metadata.name=sentinels-system --overwrite 2>$null

# Add Helm repos
Write-Host "`n[4/4] Adding Helm repositories..." -ForegroundColor Yellow
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>$null
helm repo add grafana https://grafana.github.io/helm-charts 2>$null
helm repo add chaos-mesh https://charts.chaos-mesh.org 2>$null
helm repo update

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Cluster 'sentinels' is READY             ║" -ForegroundColor Green
Write-Host "║                                           ║" -ForegroundColor Green
Write-Host "║  Namespaces: netflix, prime, monitoring,  ║" -ForegroundColor Green
Write-Host "║    sentinels-system, chaos, dashboard     ║" -ForegroundColor Green
Write-Host "║                                           ║" -ForegroundColor Green
Write-Host "║  Next: make deploy                        ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor Green
