# ═══════════════════════════════════════════════════════════════
# SENTINELS v2.0 — Docker Build Script (PowerShell)
# Builds all service images and optionally loads into k3d
# Usage: powershell -ExecutionPolicy Bypass -File scripts/build-all.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"
$registry = "sentinels"

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  SENTINELS v2.0 — Building All Images    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor Cyan

$services = @(
    @{ Name="netflix-user-service"; Path="apps/netflix/user-service" },
    @{ Name="netflix-content-service"; Path="apps/netflix/content-service" },
    @{ Name="netflix-search-service"; Path="apps/netflix/search-service" },
    @{ Name="netflix-streaming-service"; Path="apps/netflix/streaming-service" },
    @{ Name="netflix-recommendation-service"; Path="apps/netflix/recommendation-service" },
    @{ Name="netflix-payment-service"; Path="apps/netflix/payment-service" },
    @{ Name="netflix-notification-service"; Path="apps/netflix/notification-service" },
    @{ Name="netflix-api-gateway"; Path="apps/netflix/api-gateway" },
    @{ Name="netflix-frontend"; Path="apps/netflix/frontend" },
    @{ Name="prime-backend"; Path="apps/prime/backend" },
    @{ Name="prime-frontend"; Path="apps/prime/frontend" }
)

$failed = @()
$i = 0
foreach ($svc in $services) {
    $i++
    $tag = "$registry/$($svc.Name):latest"
    Write-Host "[$i/$($services.Count)] Building $tag..." -ForegroundColor Yellow
    
    try {
        docker build -t $tag -f "$($svc.Path)/Dockerfile" $svc.Path 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Build failed" }
        Write-Host "  OK: $tag" -ForegroundColor Green
    } catch {
        Write-Host "  FAILED: $tag" -ForegroundColor Red
        $failed += $svc.Name
    }
}

# Load into k3d if cluster exists
$clusterExists = k3d cluster list -o json 2>$null | ConvertFrom-Json | Where-Object { $_.name -eq "sentinels" }
if ($clusterExists) {
    Write-Host "`nLoading images into k3d cluster..." -ForegroundColor Yellow
    foreach ($svc in $services) {
        $tag = "$registry/$($svc.Name):latest"
        k3d image import $tag --cluster sentinels 2>$null
        Write-Host "  Loaded: $tag" -ForegroundColor Green
    }
}

# Summary
Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor $(if ($failed.Count -eq 0) {"Green"} else {"Yellow"})
Write-Host "║  Build Complete                           ║" -ForegroundColor $(if ($failed.Count -eq 0) {"Green"} else {"Yellow"})
Write-Host "║  Success: $($services.Count - $failed.Count)/$($services.Count)                           ║" -ForegroundColor $(if ($failed.Count -eq 0) {"Green"} else {"Yellow"})
if ($failed.Count -gt 0) {
    Write-Host "║  Failed: $($failed -join ', ')" -ForegroundColor Red
}
Write-Host "╚══════════════════════════════════════════╝`n" -ForegroundColor $(if ($failed.Count -eq 0) {"Green"} else {"Yellow"})
