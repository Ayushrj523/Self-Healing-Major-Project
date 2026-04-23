# ═══════════════════════════════════════════════════════════════
# SENTINELS v2.0 — Automated Evaluation Suite
# Runs 30 trials across 8 fault types and records F1/MTTR/MTTD
# Usage: .\scripts\run-evaluation-suite.ps1
# ═══════════════════════════════════════════════════════════════

$ErrorActionPreference = "Continue"
$ROOT = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "  SENTINELS v2.0 — Evaluation Suite" -ForegroundColor White
Write-Host "  ==================================" -ForegroundColor DarkGray
Write-Host ""

$HEALER_URL = "http://127.0.0.1:5000"
$METRICS_URL = "http://127.0.0.1:5050"
$RESULTS_FILE = Join-Path $ROOT "evaluation_results.jsonl"

# Clear previous results
if (Test-Path $RESULTS_FILE) { Remove-Item $RESULTS_FILE }

# ─── Fault Types ─────────────────────────────────────────────
$faultTypes = @(
    @{ Type = "high_cpu"; Namespace = "netflix"; Pod = "api-gateway" },
    @{ Type = "high_cpu"; Namespace = "netflix"; Pod = "search-service" },
    @{ Type = "high_memory"; Namespace = "netflix"; Pod = "content-service" },
    @{ Type = "high_memory"; Namespace = "netflix"; Pod = "streaming-service" },
    @{ Type = "crash_loop"; Namespace = "netflix"; Pod = "user-service" },
    @{ Type = "crash_loop"; Namespace = "netflix"; Pod = "payment-service" },
    @{ Type = "high_error_rate"; Namespace = "netflix"; Pod = "notification-service" },
    @{ Type = "traffic_spike"; Namespace = "prime"; Pod = "primeos-monolith" }
)

$totalTrials = 30
$trialResults = @()

Write-Host "  Running $totalTrials trials across $($faultTypes.Count) fault types..." -ForegroundColor DarkGray
Write-Host ""

for ($trial = 1; $trial -le $totalTrials; $trial++) {
    $fault = $faultTypes[($trial - 1) % $faultTypes.Count]
    $startTime = Get-Date

    Write-Host "  Trial $trial/$totalTrials | $($fault.Type) -> $($fault.Namespace)/$($fault.Pod)" -NoNewline -ForegroundColor DarkGray

    try {
        # Send attack
        $body = @{
            anomaly_type = $fault.Type
            namespace = $fault.Namespace
            pod = $fault.Pod
        } | ConvertTo-Json

        $attackResult = Invoke-RestMethod -Uri "$HEALER_URL/api/simulate" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 30

        # Wait for metrics to update
        Start-Sleep -Seconds 3

        # Fetch current scores
        $scores = Invoke-RestMethod -Uri "$METRICS_URL/api/scores" -TimeoutSec 10

        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds

        $result = @{
            trial = $trial
            timestamp = $startTime.ToString("o")
            fault_type = $fault.Type
            namespace = $fault.Namespace
            pod = $fault.Pod
            result = $attackResult.result
            recovery_time_ms = $attackResult.recovery_time_ms
            detection_time_ms = $attackResult.detection_time_ms
            anomaly_score = $attackResult.anomaly_score
            f1_score = $scores.f1_score
            mttr_seconds = $scores.mttr_seconds
            mttd_seconds = $scores.mttd_seconds
            recovery_rate = $scores.recovery_rate
            false_positive_rate = $scores.false_positive_rate
            trial_duration_seconds = [math]::Round($duration, 2)
        }

        $trialResults += $result
        $result | ConvertTo-Json -Compress | Out-File -Append -FilePath $RESULTS_FILE -Encoding utf8

        $status = if ($attackResult.result -eq "SUCCESS") { "HEALED" } else { "FAILED" }
        $color = if ($attackResult.result -eq "SUCCESS") { "Green" } else { "Red" }
        Write-Host " | $status | F1=$([math]::Round($scores.f1_score * 100, 1))% | MTTR=$([math]::Round($scores.mttr_seconds, 1))s" -ForegroundColor $color

    } catch {
        Write-Host " | ERROR: $($_.Exception.Message)" -ForegroundColor Red
        $trialResults += @{ trial = $trial; error = $_.Exception.Message }
    }

    # Brief pause between trials
    Start-Sleep -Seconds 1
}

# ─── Summary ────────────────────────────────────────────────
Write-Host ""
Write-Host "  ═══════════════════════════════════" -ForegroundColor DarkGray
Write-Host "  EVALUATION SUMMARY" -ForegroundColor White
Write-Host "  ═══════════════════════════════════" -ForegroundColor DarkGray

$successful = ($trialResults | Where-Object { $_.result -eq "SUCCESS" }).Count
$failed = ($trialResults | Where-Object { $_.result -ne "SUCCESS" -and -not $_.error }).Count
$errors = ($trialResults | Where-Object { $_.error }).Count

$avgF1 = ($trialResults | Where-Object { $_.f1_score } | ForEach-Object { $_.f1_score } | Measure-Object -Average).Average
$avgMTTR = ($trialResults | Where-Object { $_.mttr_seconds } | ForEach-Object { $_.mttr_seconds } | Measure-Object -Average).Average
$avgMTTD = ($trialResults | Where-Object { $_.mttd_seconds } | ForEach-Object { $_.mttd_seconds } | Measure-Object -Average).Average

Write-Host ""
Write-Host "  Total Trials:    $totalTrials" -ForegroundColor DarkGray
Write-Host "  Successful:      $successful" -ForegroundColor Green
Write-Host "  Failed:          $failed" -ForegroundColor Red
Write-Host "  Errors:          $errors" -ForegroundColor Yellow
Write-Host "  Avg F1 Score:    $([math]::Round($avgF1 * 100, 2))%" -ForegroundColor White
Write-Host "  Avg MTTR:        $([math]::Round($avgMTTR, 2))s" -ForegroundColor White
Write-Host "  Avg MTTD:        $([math]::Round($avgMTTD, 2))s" -ForegroundColor White
Write-Host ""
Write-Host "  Results saved to: $RESULTS_FILE" -ForegroundColor DarkGray
Write-Host ""
