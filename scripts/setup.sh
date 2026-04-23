#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# SENTINELS v2.0 — One-Command Setup Script (Linux/Mac)
# Usage: bash scripts/setup.sh
# ═══════════════════════════════════════════════════════════════

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ""
echo "  SENTINELS v2.0 — Setup"
echo "  ======================"
echo ""

# ─── Step 1: Prerequisites ──────────────────────────────────
echo "[1/7] Checking prerequisites..."
for cmd in docker kubectl helm k3d python3 node npm; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "  ERROR: $cmd not found. Install it and try again."
    exit 1
  fi
done
echo "  All prerequisites found."

# ─── Step 2: Docker Infrastructure ──────────────────────────
echo "[2/7] Starting Docker infrastructure..."
cd "$ROOT"
docker compose -f docker-compose.dev.yml up -d postgres redis
sleep 5
echo "  PostgreSQL and Redis are ready."

# ─── Step 3: Python Virtual Environments ────────────────────
echo "[3/7] Setting up Python virtual environments..."
for svc in apps/sentinels/healer apps/sentinels/metrics-aggregator; do
  svc_path="$ROOT/$svc"
  if [ ! -d "$svc_path/.venv" ]; then
    python3 -m venv "$svc_path/.venv"
  fi
  if [ -f "$svc_path/requirements.txt" ]; then
    "$svc_path/.venv/bin/pip" install -r "$svc_path/requirements.txt" -q
  fi
done
echo "  Virtual environments ready."

# ─── Step 4: Dashboard Dependencies ─────────────────────────
echo "[4/7] Installing dashboard dependencies..."
cd "$ROOT/apps/sentinels/dashboard"
[ -d "node_modules" ] || npm install --silent
echo "  Dashboard dependencies installed."

# ─── Step 5: Start Services ─────────────────────────────────
echo "[5/7] Starting SENTINELS services..."

cd "$ROOT/apps/sentinels/healer"
.venv/bin/python main.py &
HEALER_PID=$!
echo "  Healer Agent started (PID: $HEALER_PID)"
sleep 2

cd "$ROOT/apps/sentinels/metrics-aggregator"
.venv/bin/python main.py &
METRICS_PID=$!
echo "  Metrics Aggregator started (PID: $METRICS_PID)"
sleep 2

cd "$ROOT/apps/sentinels/dashboard"
npm run dev &
DASH_PID=$!
echo "  Dashboard started (PID: $DASH_PID)"
sleep 3

echo "  All services started."

# ─── Step 6: Health Checks ──────────────────────────────────
echo "[6/7] Running health checks..."
for url in "http://127.0.0.1:5000/health" "http://127.0.0.1:5050/health"; do
  if curl -sf "$url" > /dev/null 2>&1; then
    echo "  $url: OK"
  else
    echo "  $url: FAILED"
  fi
done

# ─── Step 7: Summary ────────────────────────────────────────
echo ""
echo "[7/7] Setup complete."
echo ""
echo "  Services:"
echo "    Dashboard:          http://localhost:3000"
echo "    Healer Agent:       http://127.0.0.1:5000"
echo "    Metrics Aggregator: http://127.0.0.1:5050"
echo ""
echo "  Open http://localhost:3000 in your browser."
echo ""
echo "  To stop: kill $HEALER_PID $METRICS_PID $DASH_PID"
