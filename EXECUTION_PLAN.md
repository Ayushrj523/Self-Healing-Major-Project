# SENTINELS v2.0 — Execution Plan

> **Status:** ACTIVE  
> **Created:** 2026-04-23  
> **Total Files:** ~120+ files to create  
> **Architecture:** Complete rewrite from v1.0 Docker-based to v2.0 Kubernetes-based

---

## Pre-Build Analysis

### Existing Codebase (v1.0 — will be archived)
| File | Purpose | Status |
|------|---------|--------|
| `netflix/app.py` | Flask Netflix clone (monolithic) | **REPLACED** — new 8 FastAPI microservices |
| `healer/healer.py` | Docker-based healer with IsolationForest | **REPLACED** — new K8s-based healer |
| `dashboard/app.py` | Flask-SocketIO dashboard | **REPLACED** — new React+Three.js dashboard |
| `docker-compose.yml` | v1 compose (patient, nginx, dashboard, healer) | **REPLACED** — new dev compose |
| `nginx/` | Reverse proxy | **REMOVED** — K8s handles routing |

### Windows-Specific Adaptations
- Scripts: PowerShell (.ps1) primary, bash (.sh) for K8s/Docker contexts
- Python: venv via `python -m venv .venv`
- Docker Desktop for Windows with k3d
- All paths in code use forward slashes

---

## PHASE A: Infrastructure Foundation (Tasks 1-6)

### Task 1: Repository Structure & Makefile
**Files:**
- `Makefile` — convenience commands (dev, build, deploy, test)
- `.gitignore` — updated for new structure
- `apps/` directory structure

**Verification:** `make help` shows all commands

### Task 2: Docker Compose for Local Development
**Files:**
- `docker-compose.dev.yml` — PostgreSQL, Redis, all Netflix services, PrimeOS, dashboard

**Verification:** `docker-compose -f docker-compose.dev.yml config` validates

### Task 3: PostgreSQL Init Scripts
**Files:**
- `scripts/init-db/01-create-databases.sql`
- `scripts/init-db/02-netflix-schema.sql` (users, content tables)
- `scripts/init-db/03-prime-schema.sql` (users, content tables)
- `scripts/init-db/04-sentinels-schema.sql` (healing_audit_log, anomaly_records)
- `scripts/init-db/05-seed-netflix-content.sql` (50 movies with YouTube IDs)
- `scripts/init-db/06-seed-prime-content.sql` (50 different movies)
- `scripts/init-db/07-seed-users.sql` (demo users)

**Verification:** Connect to PostgreSQL, verify all tables exist with correct schemas

### Task 4: Redis Configuration
**Files:**
- `config/redis.conf`

**Verification:** Redis container starts, accepts connections

### Task 5: k3d Cluster Creation Script
**Files:**
- `scripts/create-cluster.ps1` (Windows PowerShell)
- `scripts/create-cluster.sh` (Linux/Mac)
- `kubernetes/namespaces/all-namespaces.yaml`

**Verification:** `kubectl get namespaces` shows all 6 namespaces

### Task 6: RBAC Configurations
**Files:**
- `kubernetes/rbac/healer-rbac.yaml`
- `kubernetes/rbac/dashboard-rbac.yaml`
- `kubernetes/rbac/netflix-sa.yaml`

**Verification:** `kubectl apply --dry-run=client -f kubernetes/rbac/`

---

## PHASE B: Netflix Microservices (Tasks 7-15)

### Standard per-service files:
Each service creates: `main.py`, `models.py`, `database.py`, `requirements.txt`, `Dockerfile`

### Task 7: Netflix User Service (Port 8002)
**Dir:** `apps/netflix/user-service/`
**Files:** main.py, models.py, database.py, requirements.txt, Dockerfile
**Features:** Registration, login (JWT), profile, watch history
**Seed:** 5 demo users (user1-5@netflix.com / sentinels123)
**Verification:** `GET /health → 200`, `POST /auth/login → JWT`, `GET /metrics → prometheus`

### Task 8: Netflix Content Service (Port 8003)
**Dir:** `apps/netflix/content-service/`
**Files:** main.py, models.py, database.py, seed_data.py, requirements.txt, Dockerfile
**Features:** Movie catalog, browse by category, 50 seeded movies with YouTube IDs
**Categories:** Action(10), Drama(10), Comedy(10), Documentary(10), Sci-Fi(10)
**Verification:** `GET /content/browse → 50 movies`, `GET /content/1 → movie with youtube_id`

### Task 9: Netflix Search Service (Port 8005)
**Dir:** `apps/netflix/search-service/`
**Files:** main.py, models.py, requirements.txt, Dockerfile
**Features:** SQLite FTS5 full-text search
**Verification:** `GET /search?q=action → ranked results`

### Task 10: Netflix Streaming Service (Port 8004)
**Dir:** `apps/netflix/streaming-service/`
**Files:** main.py, models.py, requirements.txt, Dockerfile
**Features:** Play endpoint returns YouTube embed URL, Redis watch tracking
**Verification:** `POST /stream/play → {youtube_id, embed_url}`

### Task 11: Netflix Recommendation Service (Port 8006)
**Dir:** `apps/netflix/recommendation-service/`
**Files:** main.py, requirements.txt, Dockerfile
**Features:** Pre-computed recommendations in Redis, cosine similarity
**Verification:** `GET /recommend/user/1 → list of movies`

### Task 12: Netflix Payment Service (Port 8007)
**Dir:** `apps/netflix/payment-service/`
**Files:** main.py, models.py, requirements.txt, Dockerfile
**Features:** Simulated subscription plans, fake payment processing
**Verification:** `POST /payment/subscribe → success (simulated)`

### Task 13: Netflix Notification Service (Port 8008)
**Dir:** `apps/netflix/notification-service/`
**Files:** main.py, models.py, requirements.txt, Dockerfile
**Features:** Simulated email/push notifications, logged to DB
**Verification:** `POST /notify → logged notification`

### Task 14: Netflix API Gateway (Port 8001)
**Dir:** `apps/netflix/api-gateway/`
**Files:** main.py, requirements.txt, Dockerfile
**Features:** Route all requests, JWT validation, rate limiting, graceful degradation
**Verification:** All routes proxy correctly, 503 when downstream service down

### Task 15: Netflix React Frontend (Port 3001)
**Dir:** `apps/netflix/frontend/`
**Files:** Full React 18 + TypeScript app (Vite-based)
**Design:** Netflix dark (#000, #E50914), Bebas Neue, card hover, YouTube embed modal
**Key Components:** NavBar, HeroSection, ContentRow, ContentCard, VideoModal, SearchBar, AuthPages
**Verification:** `npm run dev → opens at :3001`, browse/search/play all functional

---

## PHASE C: PrimeOS Monolith (Tasks 16-17)

### Task 16: PrimeOS Django Backend (Port 8020)
**Dir:** `apps/prime/backend/`
**Files:** Django project (primeOS/settings.py, urls.py, wsgi.py), 5 apps (auth_module, content_module, search_module, stream_module, recommend_module), manage.py, requirements.txt, Dockerfile
**Features:** All-in-one monolith, SQLite DB, django-prometheus metrics, 50 seeded movies
**Verification:** `python manage.py runserver → starts`, all API endpoints work

### Task 17: PrimeOS React Frontend (Port 3002)
**Dir:** `apps/prime/frontend/`
**Files:** Full React 18 + TypeScript app (Vite-based)
**Design:** Prime navy (#0F171E), blue (#00A8E1), gold (#F5E72E), Montserrat font
**Features:** Browse, search, play, full-page outage screen on service down
**Verification:** `npm run dev → opens at :3002`, kills Django → full outage screen

---

## PHASE D: Kubernetes Manifests (Tasks 18-23)

### Task 18: Dockerfiles for All Services
**Files:** 12 Dockerfiles (8 Netflix + 1 Netflix frontend + 1 Prime backend + 1 Prime frontend + 1 Dashboard)
**Standard:** Multi-stage, non-root user, python:3.12-slim base
**Verification:** `docker build` succeeds for all

### Task 19: Kubernetes Deployment/Service YAMLs
**Dir:** `kubernetes/`
**Files:** deployment + service YAML for every service (~20 files)
**Verification:** `kubectl apply --dry-run=client` for all

### Task 20: Helm Charts
**Dir:** `kubernetes/helm-charts/`
**Files:** netflix/, prime/, sentinels/, dashboard/ charts (Chart.yaml, values.yaml, templates/)
**Verification:** `helm lint` passes for all

### Task 21: kube-prometheus-stack values.yaml
**File:** `monitoring/prometheus/values.yaml`
**Verification:** Valid YAML, correct webhook URL

### Task 22: PrometheusRule CRDs
**File:** `monitoring/prometheus/rules/sentinels-alerts.yaml`
**Rules:** HighCPUUsage, HighMemoryUsage, PodCrashLooping, PodNotReady, DeploymentReplicasMismatch, HighErrorRate
**Verification:** YAML valid, expressions correct

### Task 23: PodDisruptionBudgets
**File:** `kubernetes/netflix/pdbs.yaml`
**Verification:** `kubectl apply --dry-run=client`

---

## PHASE E: SENTINELS Core Engine (Tasks 24-34)

### Task 24: Feature Engineering
**File:** `sentinels/healer-agent/ml/feature_engineering.py`
**Features:** 20-dimension feature vector, rolling stats, z-scores, rate of change
**Verification:** Unit test with synthetic data

### Task 25: Anomaly Detector
**File:** `sentinels/healer-agent/ml/anomaly_detector.py`
**Features:** IsolationForest (200 trees, 0.02 contamination), severity classification, incremental retrain
**Verification:** Train on test data, score anomaly vs normal

### Task 26: Prometheus Collector
**File:** `sentinels/healer-agent/ml/prometheus_collector.py`
**Features:** PromQL queries for CPU, memory, error rate, restart count
**Verification:** Queries build correctly

### Task 27: Healing Policy (Rego)
**File:** `sentinels/opa-policies/healing_policy.rego`
**Rules:** 5 rules (high CPU, high memory, crash loop, replica mismatch, high error rate)
**Verification:** `opa eval` with test inputs

### Task 28: Safety Policy (Rego)
**File:** `sentinels/opa-policies/safety_policy.rego`
**Rules:** 6 checks (circuit breaker, cooldown, blast radius, PDB, namespace protection)
**Verification:** `opa eval` with test inputs

### Task 29: Circuit Breaker
**File:** `sentinels/healer-agent/safety/circuit_breaker.py`
**Features:** CLOSED/OPEN/HALF_OPEN states in Redis, configurable thresholds
**Verification:** Unit test state transitions

### Task 30: Cooldown Manager
**File:** `sentinels/healer-agent/safety/cooldown_manager.py`
**Features:** Redis-backed per-pod cooldown timers
**Verification:** Unit test cooldown enforcement

### Task 31: Database Models
**File:** `sentinels/healer-agent/models/database.py`
**Features:** SQLAlchemy async, healing_audit_log table, CRUD operations
**Verification:** Connect to PostgreSQL, create tables

### Task 32: OPA Client
**File:** `sentinels/healer-agent/policy/opa_client.py`
**Features:** Async HTTP client to OPA server, fallback policy
**Verification:** Query OPA endpoint

### Task 33: Healer Agent Main (Port 5000)
**File:** `sentinels/healer-agent/main.py`
**Features:** Complete 8-step MAPE-K loop, AlertManager webhook, Socket.IO broadcast
**Verification:** POST /alerts → full pipeline executes, /health returns 200

### Task 34: Metrics Aggregator (Port 5050)
**File:** `sentinels/metrics-aggregator/main.py`
**Features:** F1, MTTD, MTTR, FPR calculations from PostgreSQL + Prometheus
**Verification:** GET /api/metrics → calculated scores

---

## PHASE F: Dashboard (Tasks 35-43)

### Task 35: Dashboard Backend
**File:** `dashboard/backend/main.py`
**Features:** Topology API (/api/topology), attack launcher, K8s client, Socket.IO proxy
**Verification:** GET /api/topology → pod graph data

### Task 36: useWebSocket Hook
**File:** `dashboard/frontend/src/hooks/useWebSocket.ts`
**Features:** Socket.IO connection, auto-reconnect, event typing
**Verification:** Connects to backend WebSocket

### Task 37: useTopology Hook
**File:** `dashboard/frontend/src/hooks/useTopology.ts`
**Features:** Polls /api/topology every 2s, maps to graph data
**Verification:** Returns node/edge data

### Task 38: TopologyGraph3D Component
**Dir:** `dashboard/frontend/src/components/TopologyGraph3D/`
**Features:** React Three Fiber 3D force graph, colored spheres, orbit controls, attack/healing particles, SENTINELS core node
**Verification:** 3D graph renders without WebGL errors

### Task 39: AttackLauncher Component
**Dir:** `dashboard/frontend/src/components/AttackLauncher/`
**Features:** Target dropdown, attack type, intensity slider, duration, launch button, active attacks list, emergency stop
**Verification:** Sends POST to /api/attacks/launch

### Task 40: HealingLog Component
**Dir:** `dashboard/frontend/src/components/HealingLog/`
**Features:** Real-time event feed, Socket.IO events, color-coded entries
**Verification:** Displays events from WebSocket

### Task 41: MetricsScorecard Component
**Dir:** `dashboard/frontend/src/components/MetricsScorecard/`
**Features:** F1, MTTD, MTTR, FPR gauges with traffic lights and sparklines
**Verification:** Displays data from /api/metrics

### Task 42: GrafanaEmbed Component
**Dir:** `dashboard/frontend/src/components/GrafanaEmbed/`
**Features:** Tabbed iframe for 3 Grafana dashboards
**Verification:** Iframe loads Grafana

### Task 43: Dashboard App Assembly
**File:** `dashboard/frontend/src/App.tsx`
**Features:** Full layout with all 5 panels, responsive, mission control aesthetic
**Verification:** Full dashboard renders at :3000

---

## PHASE G: Chaos Engineering (Tasks 44-46)

### Task 44: Chaos Mesh Experiment Templates
**Dir:** `chaos/experiments/`
**Files:** 10 YAML templates (pod-kill, cpu-stress, memory-stress, network-latency, network-partition, http-flood, disk-io, dns-failure, container-oom, cascading-failure)
**Verification:** Valid YAML

### Task 45: k6 HTTP Flood Script
**File:** `chaos/k6-scripts/http-flood.js`
**Features:** Configurable VUs, duration, multi-endpoint flood
**Verification:** Script syntax valid

### Task 46: Chaos Mesh Helm Values
**File:** `chaos/values.yaml`
**Verification:** `helm lint`

---

## PHASE H: Final Integration (Tasks 47-52)

### Task 47: Grafana Dashboard JSONs
**Dir:** `monitoring/grafana/dashboards/`
**Files:** netflix-red.json, sentinels-healer.json, infrastructure-use.json
**Verification:** Import into Grafana successfully

### Task 48: Loki Configuration
**File:** `monitoring/loki/values.yaml`
**Verification:** Valid YAML

### Task 49: Setup Script
**Files:** `scripts/setup.ps1`, `scripts/setup.sh`
**Features:** One-command k3d + Helm deploy of entire system
**Verification:** Script runs without errors

### Task 50: Evaluation Suite
**File:** `scripts/run-evaluation-suite.ps1`
**Features:** Automated 30-trial evaluation across 8 fault types
**Verification:** Script structure valid

### Task 51: README.md
**File:** `README.md` — complete rewrite for v2.0
**Verification:** Renders correctly on GitHub

### Task 52: Integration Tests
**File:** `tests/integration/test_full_cycle.py`
**Features:** Launch attack → verify detection → verify healing → verify metrics
**Verification:** Test passes end-to-end

---

## Build Execution Strategy

Given context window limits, I will build in this order:
1. **Tasks 1-6**: Infrastructure foundation (fast, small files)
2. **Tasks 7-14**: Netflix backend services (all 8 FastAPI services)
3. **Task 15**: Netflix React frontend
4. **Task 16-17**: PrimeOS backend + frontend
5. **Tasks 24-34**: SENTINELS core engine (ML + safety + healer)
6. **Tasks 35-43**: Dashboard (React Three.js + backend)
7. **Tasks 18-23**: Kubernetes manifests + Helm charts
8. **Tasks 44-52**: Chaos engineering + integration + scripts

Each service follows the pattern:
1. Write the code
2. Create requirements.txt
3. Create Dockerfile
4. Verify it starts and responds to /health
