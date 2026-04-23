# SENTINELS v2.0

**AI-Driven Self-Healing Cloud Deployment System**

An autonomous Kubernetes self-healing engine that detects anomalies using Isolation Forest ML, evaluates healing policies through OPA (Open Policy Agent), enforces safety constraints, and executes remediation — all in real-time. Includes a 3D command center for topology visualization and chaos engineering.

---

## Architecture

```
                    +-------------------+
                    |   3D Dashboard    |
                    | React + Three.js  |
                    |    Port 3000      |
                    +--------+----------+
                             |
              +--------------+---------------+
              |                              |
    +---------v----------+      +-----------v---------+
    |   Healer Agent     |      | Metrics Aggregator  |
    |  FastAPI + SocketIO|      |   FastAPI            |
    |    Port 5000       |      |   Port 5050          |
    +--------+-----------+      +-----------+----------+
             |                              |
    +--------v-----------+     +------------v----------+
    |   OPA Server       |     |    PostgreSQL         |
    |   Port 8181        |     |    Port 5432          |
    +--------------------+     +-----------------------+
             |
    +--------v-------------------------------------------+
    |              Kubernetes Cluster (k3d)               |
    |                                                     |
    |   +------------+   +------------+   +------------+  |
    |   |  Netflix   |   |  PrimeOS   |   | SENTINELS  |  |
    |   |  8 svcs    |   |  Monolith  |   |  System    |  |
    |   +------------+   +------------+   +------------+  |
    +-----------------------------------------------------+
```

---

## Services

| Service | Port | Stack | Purpose |
|---------|------|-------|---------|
| Netflix API Gateway | 8001 | FastAPI | Request routing, JWT validation |
| Netflix User Service | 8002 | FastAPI | Auth, profiles, watch history |
| Netflix Content Service | 8003 | FastAPI | Movie catalog (50 seeded) |
| Netflix Streaming Service | 8004 | FastAPI | YouTube embed playback |
| Netflix Search Service | 8005 | FastAPI | FTS5 full-text search |
| Netflix Recommendation Service | 8006 | FastAPI | Cosine similarity engine |
| Netflix Payment Service | 8007 | FastAPI | Subscription simulation |
| Netflix Notification Service | 8008 | FastAPI | Event notification logging |
| Netflix Frontend | 3001 | React + Vite | Netflix UI clone |
| PrimeOS Backend | 8020 | Django 5.0 | Monolith (all-in-one) |
| PrimeOS Frontend | 3002 | React + Vite | Prime Video UI clone |
| Healer Agent | 5000 | FastAPI + Socket.IO | ML anomaly detection + healing |
| Metrics Aggregator | 5050 | FastAPI | F1, MTTR, MTTD computation |
| OPA Server | 8181 | OPA | Healing + safety policy engine |
| Dashboard | 3000 | React + Three.js | 3D command center |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker Desktop
- k3d, kubectl, Helm (for K8s deployment)

### Local Development (3 Terminals)

**Terminal 1 — Healer Agent:**
```powershell
cd apps\sentinels\healer
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Terminal 2 — Metrics Aggregator:**
```powershell
cd apps\sentinels\metrics-aggregator
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

**Terminal 3 — Dashboard:**
```powershell
cd apps\sentinels\dashboard
npm install
npm run dev
```

Open http://localhost:3000

### One-Command Setup

```powershell
.\scripts\setup.ps1
```

---

## MAPE-K Healing Pipeline

The healer agent implements the IBM MAPE-K autonomic computing loop:

1. **Monitor** — Prometheus metrics collection (CPU, memory, error rate, restarts)
2. **Analyze** — Isolation Forest anomaly detection (200 trees, 20-dim feature vector)
3. **Plan** — OPA policy evaluation (5 healing rules + 6 safety checks)
4. **Execute** — Kubernetes API remediation (restart, scale, cordon, rollback)
5. **Knowledge** — PostgreSQL audit log + incremental model retraining

### Anomaly Detection

- **Algorithm:** Isolation Forest (scikit-learn)
- **Features:** 20-dimension vector (CPU, memory, network, error rates, z-scores, rolling stats)
- **Contamination:** 0.02 (2% expected anomaly rate)
- **Threshold:** -0.30 anomaly score

### Policy Engine (OPA)

**Healing Rules:**
- `high_cpu` → restart_pod
- `high_memory` → restart_pod
- `crash_loop` → rollback_deployment
- `replica_mismatch` → scale_up
- `high_error_rate` → restart_pod

**Safety Checks:**
- Circuit breaker (CLOSED/OPEN/HALF_OPEN)
- Per-pod cooldown timers
- Blast radius limits
- PodDisruptionBudget compliance
- Namespace protection
- Action rate limiting

---

## Chaos Engineering

### Chaos Mesh Experiments

10 pre-built experiment templates in `chaos/experiments/`:

| Experiment | Type | Target |
|------------|------|--------|
| pod-kill | PodChaos | Random Netflix pod |
| cpu-stress | StressChaos | 80% CPU for 60s |
| memory-stress | StressChaos | 256Mi allocation |
| network-latency | NetworkChaos | 200ms delay |
| network-partition | NetworkChaos | Gateway isolation |
| http-flood | HTTPChaos | Request abort |
| disk-io | IOChaos | 100ms I/O delay |
| dns-failure | DNSChaos | Resolution failure |
| container-oom | StressChaos | OOM simulation |
| cascading-failure | Workflow | Sequential pod kills |

### k6 Load Testing

```powershell
k6 run --vus 50 --duration 60s chaos\k6-scripts\http-flood.js
```

---

## Evaluation

Run the automated 30-trial evaluation suite:

```powershell
.\scripts\run-evaluation-suite.ps1
```

Results are saved to `evaluation_results.jsonl` with per-trial F1, MTTR, and MTTD measurements.

---

## Monitoring

### Grafana Dashboards

Three pre-built dashboards in `monitoring/grafana/dashboards/`:

- **Netflix RED** — Rate, Errors, Duration per service
- **SENTINELS Healer** — F1 score, MTTR, healing actions, safety blocks
- **Infrastructure USE** — CPU, memory, network, disk I/O

### Prometheus Rules

Alert rules in `monitoring/prometheus/rules/`:
- HighCPUUsage (>80% for 5m)
- HighMemoryUsage (>85% for 5m)
- PodCrashLooping (>3 restarts in 15m)
- PodNotReady (>5m)
- DeploymentReplicasMismatch (>5m)
- HighErrorRate (>5% for 5m)

---

## Project Structure

```
SENTINAL/
├── apps/
│   ├── netflix/              # 8 FastAPI microservices + React frontend
│   │   ├── api-gateway/
│   │   ├── user-service/
│   │   ├── content-service/
│   │   ├── streaming-service/
│   │   ├── search-service/
│   │   ├── recommendation-service/
│   │   ├── payment-service/
│   │   ├── notification-service/
│   │   └── frontend/
│   ├── prime/                # Django monolith + React frontend
│   │   ├── backend/
│   │   └── frontend/
│   └── sentinels/            # Core engine
│       ├── healer/           # ML + policy + safety + K8s healer
│       ├── metrics-aggregator/
│       └── dashboard/        # React + Three.js 3D command center
├── chaos/
│   ├── experiments/          # 10 Chaos Mesh YAML templates
│   ├── k6-scripts/           # k6 load testing
│   └── values.yaml           # Chaos Mesh Helm values
├── kubernetes/
│   ├── namespaces/
│   ├── rbac/
│   └── helm-charts/
├── monitoring/
│   ├── grafana/dashboards/   # 3 dashboard JSONs
│   ├── loki/                 # Log aggregation config
│   └── prometheus/           # Alert rules
├── scripts/
│   ├── init-db/              # PostgreSQL schema + seed data
│   ├── setup.ps1             # Windows one-command setup
│   ├── setup.sh              # Linux/Mac one-command setup
│   ├── create-cluster.ps1    # k3d cluster creation
│   └── run-evaluation-suite.ps1
├── tests/
│   └── integration/
├── docker-compose.dev.yml
├── Makefile
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Engine | scikit-learn (Isolation Forest), NumPy |
| Policy Engine | Open Policy Agent (Rego) |
| API Layer | FastAPI, Socket.IO |
| Frontend | React 18, TypeScript, Vite |
| 3D Visualization | Three.js, React Three Fiber, Drei |
| Charts | Recharts |
| Icons | Lucide React |
| Database | PostgreSQL 16, Redis 7.2 |
| Container | Docker, k3d (K3s in Docker) |
| Orchestration | Kubernetes |
| Monitoring | Prometheus, Grafana, Loki |
| Chaos Engineering | Chaos Mesh, k6 |
| Package Management | Helm |

---

## License

MIT
