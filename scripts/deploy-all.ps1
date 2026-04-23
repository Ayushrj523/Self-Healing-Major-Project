# ═══════════════════════════════════════════════════════════════
# SENTINELS v2.0 — K8s Deploy Script (PowerShell)
# Deploys all manifests to the k3d cluster
# Usage: powershell -ExecutionPolicy Bypass -File scripts/deploy-all.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  SENTINELS v2.0 — Deploying to k3d       ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor Cyan

# 1. Namespaces
Write-Host "[1/6] Creating namespaces..." -ForegroundColor Yellow
kubectl apply -f kubernetes/namespaces/all-namespaces.yaml
Write-Host "  OK" -ForegroundColor Green

# 2. RBAC
Write-Host "[2/6] Applying RBAC..." -ForegroundColor Yellow
kubectl apply -f kubernetes/rbac/healer-rbac.yaml
Write-Host "  OK" -ForegroundColor Green

# 3. Infrastructure
Write-Host "[3/6] Deploying infrastructure..." -ForegroundColor Yellow
kubectl apply -f kubernetes/monitoring/infra.yaml
Write-Host "  OK: Postgres + Redis" -ForegroundColor Green

# 4. Netflix secrets + services
Write-Host "[4/6] Deploying Netflix microservices..." -ForegroundColor Yellow
kubectl apply -f kubernetes/netflix/secrets.yaml
kubectl apply -f kubernetes/netflix/deployments.yaml
Write-Host "  OK: 9 Netflix services" -ForegroundColor Green

# 5. PrimeOS
Write-Host "[5/6] Deploying PrimeOS monolith..." -ForegroundColor Yellow
kubectl apply -f kubernetes/prime/deployments.yaml
Write-Host "  OK: Prime backend + frontend" -ForegroundColor Green

# 6. PDBs + Monitoring
Write-Host "[6/6] Applying PDBs and monitoring rules..." -ForegroundColor Yellow
kubectl apply -f kubernetes/pdbs.yaml
kubectl apply -f kubernetes/monitoring/prometheus-rules.yaml 2>$null
Write-Host "  OK" -ForegroundColor Green

# Wait for rollouts
Write-Host "`nWaiting for rollouts..." -ForegroundColor Yellow
$deployments = @(
    @{Name="api-gateway"; NS="netflix"},
    @{Name="content-service"; NS="netflix"},
    @{Name="user-service"; NS="netflix"},
    @{Name="prime-backend"; NS="prime"}
)
foreach ($d in $deployments) {
    Write-Host "  Waiting: $($d.Name)..." -NoNewline
    kubectl rollout status deployment/$($d.Name) -n $($d.NS) --timeout=120s 2>$null
    Write-Host " Ready" -ForegroundColor Green
}

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Deployment Complete!                     ║" -ForegroundColor Green
Write-Host "║                                           ║" -ForegroundColor Green
Write-Host "║  Netflix: http://127.0.0.1:3000           ║" -ForegroundColor Green
Write-Host "║  PrimeOS: http://127.0.0.1:3002           ║" -ForegroundColor Green
Write-Host "║  Gateway: http://127.0.0.1:3001/api       ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor Green
