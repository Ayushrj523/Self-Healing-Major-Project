# SENTINELS v2.0 — Complete Master Blueprint & Development Bible
## Self-Healing ENTerprise INtelligent ELastic System

> **Document Authority:** This is the single source of truth for all SENTINELS v2.0 development.  
> **Version:** 2.0.0 — Complete Rewrite with Triple-Application Architecture  
> **Status:** FINAL — Ready for Execution  
> **Target:** Local laptop development → University capstone demonstration

---

# PREFACE — CTO's Analysis & Decision Summary

Before any line of code is written, I need you to understand every architectural decision and why it was made. This is not a random collection of tools — every choice has a reason, every edge case has a mitigation, and every component connects to every other component deliberately.

## What Ayush Proposed (Raw Vision, Translated)

You proposed building three things:
1. A Netflix clone running as **microservices** (to prove SENTINELS works on distributed architectures)
2. An Amazon Prime clone running as a **monolith** (to prove SENTINELS works on single-unit architectures)
3. A **3D Command Dashboard** that visualizes attacks, healing, metrics, and system state in real-time — inspired by Obsidian's graph view — with attack tools built in

This is **architecturally brilliant** as a demonstration strategy. Here's why: every real-world evaluator will ask "but does this work with different architectures?" By showing microservices AND monolith, you pre-answer that question with a live demo. No other student project does this.

## What You Did NOT Say (But I'm Adding As CTO)

After deep analysis, I identified seven things you implied but didn't explicitly state that are critical:

1. **YouTube IFrame API as mock streaming** — Since we can't host actual video files locally, we use YouTube's IFrame API to embed publicly available trailers and content. The UI will look identical to Netflix/Prime; the videos just come from YouTube. This is legal, practical, and actually demonstrates a real-world pattern (content delivery via CDN/external service).

2. **Service Discovery between microservices** — Netflix clone's 8 microservices need to find each other inside Kubernetes. We use Kubernetes built-in DNS (service names as hostnames). No external service mesh needed at this scale.

3. **Fault injection CANNOT use Chaos Mesh alone for HTTP floods** — Chaos Mesh handles infrastructure faults (CPU, memory, network, pod kill). For HTTP flood/DDoS simulation, we need a separate load generator. We'll use **k6** (Grafana's load testing tool) running as a Kubernetes Job, triggered by the dashboard.

4. **The 3D graph is a LIVE topology map** — Not a static diagram. It reads the actual Kubernetes pod state every 2 seconds and renders it. When a pod dies, its node goes red in the 3D graph in real-time. When SENTINELS heals it, the node transitions through orange → yellow → green with a repair animation.

5. **Scores panel needs a dedicated scoring service** — The F1 score, MTTD, MTTR, etc. cannot be calculated on the frontend. We need a dedicated **Metrics Aggregator Service** that queries Prometheus, calculates scores, and exposes them via REST API. The dashboard consumes this.

6. **Port assignment must be LOCKED** — Nothing is worse than port conflicts during a demo. I've assigned fixed ports for every service in this document. These are non-negotiable.

7. **All three apps must run on a SINGLE laptop** — This means resource budgets are tight. Total Kubernetes resource budget: 8GB RAM, 6 CPU cores (for a laptop with 16GB/8-core). Every service has hard resource limits in this document.

---

# PART 0 — PHILOSOPHY & DESIGN PRINCIPLES

## The Five Laws of SENTINELS

Every architectural decision in this document is governed by five laws. If any feature request violates a law, the feature must be redesigned.

**LAW 1 — Explainability Over Performance**  
Every healing action must produce a human-readable audit trail. "Pod restarted because CPU anomaly score -0.42 exceeded threshold -0.3, matching policy rule HIGH_CPU_CRITICAL" is acceptable. "Neural network decided to restart pod" is not.

**LAW 2 — Safety Over Speed**  
Circuit breakers, cooldown timers, and blast radius controls ALWAYS execute before any remediation action. A 2-second delay in healing is infinitely better than healing-induced cascading failure.

**LAW 3 — Observe Before Acting**  
The system must be monitoring for at least 60 seconds of baseline data before any anomaly detection runs. Cold-start false positives ruin demonstrations.

**LAW 4 — Fail Gracefully, Always**  
If the healer itself crashes, the monitored applications must continue running. SENTINELS is the observer, not the load-bearing wall.

**LAW 5 — Demonstration Clarity**  
Every technical decision must consider "can I show this working in under 5 minutes to a professor?" If a feature cannot be demonstrated clearly, it is over-engineered.

---

# PART 1 — SYSTEM OVERVIEW & COMPLETE ARCHITECTURE

## 1.1 What Is SENTINELS v2.0?

SENTINELS is an AI-driven, self-healing Kubernetes platform that:

- **Continuously monitors** two different application architectures (microservices + monolith) using Prometheus metrics, collected every 15 seconds
- **Detects anomalies** using Isolation Forest ML — a lightweight unsupervised algorithm that identifies abnormal CPU, memory, network, and error-rate patterns without needing labeled training data
- **Makes explainable decisions** using an OPA/Rego policy engine — a deterministic rule system that maps anomaly type + severity to a specific healing action
- **Executes healing** via a Kubernetes Operator (Kopf) — a Python-native framework that calls the Kubernetes API to restart pods, scale deployments, or roll back to stable versions
- **Visualizes everything** in a 3D Command Center dashboard with live attack simulation, real-time topology graphs, and quantitative performance metrics (F1 score, MTTD, MTTR)

SENTINELS occupies the intersection of three domains:
```
    AIOps              ←────────── SENTINELS ──────────→          SRE Platform
(Anomaly Detection)                                         (Kubernetes Operations)
         ↑                                                              ↑
         └────────────── Chaos Engineering Validation ─────────────────┘
```

## 1.2 The Three Applications

### Application A: NetflixOS (Microservices Architecture)
- **Port:** 3001 (frontend), 8001-8008 (backend services)
- **Architecture:** 8 independent FastAPI microservices, each in its own Docker container, each with its own Kubernetes Deployment
- **Purpose:** Represents real-world distributed systems (companies like Netflix, Uber, Airbnb)
- **Why Microservices:** Allows SENTINELS to demonstrate targeted healing — kill the Search Service, and only the search feature breaks. The rest of Netflix continues working.
- **YouTube Integration:** Movies and shows are rendered as cards. Clicking "Play" embeds a YouTube IFrame from a curated list of movie trailers

### Application B: PrimeOS (Monolithic Architecture)  
- **Port:** 3002 (single frontend+backend app)
- **Architecture:** Single Django application with all features (auth, content, streaming, search, recommendations) in one process, one container, one Kubernetes Deployment
- **Purpose:** Represents traditional applications (legacy enterprise software, small company stacks)
- **Why Monolith:** Demonstrates that when SENTINELS kills the single pod, the ENTIRE PrimeOS goes down — all features disappear simultaneously. SENTINELS must restart the whole monolith. This contrast is visually dramatic during demos.

### Application C: SENTINELS Command Center (The Dashboard)
- **Port:** 3000 (React SPA)
- **Architecture:** React frontend + FastAPI backend + Socket.IO real-time layer
- **Purpose:** The "God View" — monitors both Netflix and Prime simultaneously, launches attacks, visualizes healing, displays metrics
- **3D Visualization:** React Three Fiber (Three.js wrapper) renders a live force-directed 3D graph of all pods and their network connections

## 1.3 Complete System Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                         SENTINELS v2.0 SYSTEM ARCHITECTURE                      ║
║                         (All running on laptop via k3d)                         ║
╚══════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────┐
│                        KUBERNETES CLUSTER (k3d)                                  │
│                                                                                   │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                        │
│  │   NAMESPACE: netflix     │  │   NAMESPACE: prime       │                        │
│  │                          │  │                          │                        │
│  │  ┌────────────────────┐  │  │  ┌────────────────────┐ │                        │
│  │  │  API Gateway :8001 │  │  │  │  PrimeOS App :8020 │ │                        │
│  │  │  User Svc    :8002 │  │  │  │  (Monolith)        │ │                        │
│  │  │  Content Svc :8003 │  │  │  │  - Auth Module     │ │                        │
│  │  │  Stream Svc  :8004 │  │  │  │  - Content Module  │ │                        │
│  │  │  Search Svc  :8005 │  │  │  │  - Search Module   │ │                        │
│  │  │  Rec. Svc    :8006 │  │  │  │  - Recommend Module│ │                        │
│  │  │  Payment Svc :8007 │  │  │  └────────────────────┘ │                        │
│  │  │  Notif. Svc  :8008 │  │  │                          │                        │
│  │  │  React UI    :3001 │  │  │  React UI        :3002   │                        │
│  │  └────────────────────┘  │  └─────────────────────────┘                        │
│  └─────────────────────────┘                                                      │
│              │                              │                                      │
│              └──────────────┬──────────────┘                                      │
│                             ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │                     NAMESPACE: monitoring                                     │ │
│  │                                                                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  ┌──────────────────┐  │ │
│  │  │  Prometheus  │  │ AlertManager│  │    Grafana     │  │  Loki (Logs)     │  │ │
│  │  │  :9090       │  │  :9093      │  │    :3003       │  │  :3100           │  │ │
│  │  │  Scrapes     │  │  Routes     │  │  Dashboards    │  │  Log aggregation │  │ │
│  │  │  every 15s   │  │  alerts to  │  │  SRE view      │  │  + queries       │  │ │
│  │  └──────┬───────┘  │  healer     │  └───────────────┘  └──────────────────┘  │ │
│  │         │          └──────┬──────┘                                            │ │
│  │         │                 │                                                    │ │
│  └─────────┼─────────────────┼────────────────────────────────────────────────── ┘ │
│            │                 │                                                      │
│            ▼                 ▼                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │                     NAMESPACE: sentinels-system                               │ │
│  │                                                                               │ │
│  │  ┌───────────────────────────────────────────────────────────────────────┐   │ │
│  │  │                    HEALER AGENT (FastAPI :5000)                        │   │ │
│  │  │                                                                        │   │ │
│  │  │  AlertManager Webhook → [1] Receive Alert                             │   │ │
│  │  │                         [2] Extract anomaly context                   │   │ │
│  │  │                         [3] Isolation Forest → Anomaly Score          │   │ │
│  │  │                         [4] OPA Policy Engine → Action Decision       │   │ │
│  │  │                         [5] Safety Stack (circuit breaker, cooldown)  │   │ │
│  │  │                         [6] Kopf Operator → K8s API → Execute Action  │   │ │
│  │  │                         [7] Verify Recovery → Update Metrics          │   │ │
│  │  │                         [8] Socket.IO → Broadcast to Dashboard        │   │ │
│  │  └───────────────────────────────────────────────────────────────────────┘   │ │
│  │                                                                               │ │
│  │  ┌─────────────────┐  ┌────────────────┐  ┌────────────────────────────┐    │ │
│  │  │  OPA Server      │  │  Redis         │  │  PostgreSQL                │    │ │
│  │  │  :8181           │  │  :6379         │  │  :5432                     │    │ │
│  │  │  Policy Engine   │  │  Circuit State │  │  Audit Logs / History      │    │ │
│  │  └─────────────────┘  │  Cooldown Timers│  │  Anomaly Records           │    │ │
│  │                        │  Pub/Sub Events │  │  Metric Snapshots          │    │ │
│  │                        └────────────────┘  └────────────────────────────┘    │ │
│  │                                                                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐     │ │
│  │  │               METRICS AGGREGATOR SERVICE (FastAPI :5050)            │     │ │
│  │  │               Calculates: F1, MTTD, MTTR, FPR, Recovery Rate       │     │ │
│  │  └─────────────────────────────────────────────────────────────────────┘     │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                           │
│                                        ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │               NAMESPACE: chaos                                                │ │
│  │  ┌────────────────────┐  ┌─────────────────────┐                            │ │
│  │  │  Chaos Mesh :2334   │  │  k6 Load Generator   │                            │ │
│  │  │  Infrastructure     │  │  HTTP Flood / DDoS   │                            │ │
│  │  │  Faults             │  │  Attacks             │                            │ │
│  │  └────────────────────┘  └─────────────────────┘                            │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
│                                        │                                           │
│                                        ▼                                           │
│  ┌──────────────────────────────────────────────────────────────────────────────┐ │
│  │               NAMESPACE: dashboard                                            │ │
│  │  ┌─────────────────────────────────────────────────────────────────────┐     │ │
│  │  │         SENTINELS COMMAND CENTER  (React + Three.js) :3000          │     │ │
│  │  │  - 3D Force-Graph Topology (live pod states)                        │     │ │
│  │  │  - Attack Launcher (target: Netflix/Prime, fault type)              │     │ │
│  │  │  - Real-time Healing Log feed                                       │     │ │
│  │  │  - Metrics Scorecard (F1, MTTD, MTTR, FPR)                        │     │ │
│  │  │  - Grafana embed (iframe)                                           │     │ │
│  │  └─────────────────────────────────────────────────────────────────────┘     │ │
│  └──────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## 1.4 The Master Event Journey (Metric-to-Action Flow)

This is the complete data journey from the moment a fault is injected to the moment the system recovers. Every developer must memorize this flow.

```
ATTACK INJECTED (e.g., CPU Stress on Netflix Search Service)
     │
     ▼ t=0s
[Chaos Mesh / k6] Injects StressChaos → CPU of search-svc pod spikes to 95%
     │
     ▼ t=15s (next Prometheus scrape)
[Prometheus] Scrapes container_cpu_usage_seconds_total from kubelet/cAdvisor
             Detects: cpu_percent(search-svc) = 0.95 (95% of limit)
             PrometheusRule "HighCPUUsage" evaluates: avg over 5min > 0.90 → TRUE
             [BUT WAIT: must be high for 5min to fire — see tuning below]
     │
     ▼ t=~90s (for speed-tuned alert: 1min evaluation window)
[AlertManager] HighCPUUsage alert FIRES
               Routes to: healer-webhook-receiver
               Sends HTTP POST to: http://healer-agent.sentinels-system.svc:5000/alerts
               Payload: {alertname: "HighCPUUsage", pod: "search-svc-xxx", 
                         namespace: "netflix", severity: "critical",
                         labels: {healing_action: "restart_pod"}}
     │
     ▼ t=~91s
[Healer Agent] Receives webhook payload
               Step 1 — Context Extraction:
                 namespace="netflix", pod="search-svc-xxx", anomaly_type="high_cpu"
               Step 2 — Feature Engineering:
                 Queries Prometheus: last 5min of CPU, memory, restart_count for pod
                 Computes: rolling_mean_cpu, rolling_std_cpu, rate_of_change, z_score
               Step 3 — Isolation Forest Scoring:
                 Passes feature vector to pre-trained model
                 Returns: anomaly_score = -0.47 (threshold: -0.30)
                 Verdict: ANOMALOUS (score below threshold = anomaly confirmed)
               Step 4 — OPA Policy Query:
                 Sends: {anomaly_type: "high_cpu", severity: "critical", 
                         anomaly_score: -0.47, duration_minutes: 2}
                 OPA Returns: {action: "restart_pod", reason: "CPU>90% confirmed 
                               by IF score -0.47, CRITICAL severity, duration 2min"}
               Step 5 — Safety Stack Check:
                 ✓ Circuit breaker: CLOSED (no recent failures)
                 ✓ Cooldown: 0 recent restarts (last restart: >10min ago)
                 ✓ Blast radius: 7/8 pods healthy (>75% threshold)  
                 ✓ PDB check: maxUnavailable=1, currently 0 unavailable → OK
                 ALL CHECKS PASS → Proceed
               Step 6 — Execute via Kopf/K8s API:
                 DELETE pod/search-svc-xxx -n netflix
                 Kubernetes ReplicaSet immediately creates search-svc-yyy
                 (Container restart takes ~5-10 seconds)
               Step 7 — Verification:
                 Polls pod status every 3s for max 60s
                 Wait for: pod status = Running AND readiness probe = pass
                 CPU metrics: normalizing toward baseline
               Step 8 — Broadcast to Dashboard:
                 Socket.IO emit "healing_event": {
                   timestamp, action, target_pod, anomaly_type, anomaly_score,
                   policy_id, safety_checks, recovery_time_ms, result: "SUCCESS"
                 }
               Step 9 — Record in PostgreSQL:
                 INSERT healing_audit_log (correlation_id, all fields above)
               Step 10 — Update Prometheus metrics:
                 healing_actions_total{action="restart_pod", result="success"}++
                 healing_action_duration_seconds.observe(duration)
     │
     ▼ t=~105s
[Dashboard] Receives Socket.IO event
            3D Graph: search-svc node flashes RED → transitions to BLUE (healing)
                      Animated repair particles stream from SENTINELS core node
                      Node transitions to GREEN after verification succeeds
            Healing Log: "✅ 14s | search-svc restarted | CPU anomaly -0.47 | CRITICAL"
            Metrics update: MTTD = 91s, MTTR = 14s, Success Rate = 97.3%
     │
     ▼ t=~106s
[Netflix Frontend] Search service responds again
                   User browsing Netflix: brief 503 during restart → then normal
     │
[TOTAL INCIDENT DURATION: ~106 seconds from attack to full recovery]
[SENTINELS DETECTION TIME (MTTD): ~91 seconds]  
[SENTINELS HEALING TIME (MTTR): ~14 seconds]
```

## 1.5 Port Assignment — LOCKED AND FINAL

| Service | Port | Protocol | Notes |
|---|---|---|---|
| SENTINELS Command Center (React) | **3000** | HTTP | Main dashboard |
| NetflixOS React Frontend | **3001** | HTTP | Netflix UI |
| PrimeOS React Frontend | **3002** | HTTP | Prime UI |
| Grafana | **3003** | HTTP | SRE dashboards |
| Healer Agent API | **5000** | HTTP/WS | AlertManager webhook |
| Metrics Aggregator | **5050** | HTTP | Score calculations |
| NetflixOS API Gateway | **8001** | HTTP | Routes to microservices |
| Netflix User Service | **8002** | HTTP | Internal |
| Netflix Content Service | **8003** | HTTP | Internal |
| Netflix Streaming Service | **8004** | HTTP | Internal |
| Netflix Search Service | **8005** | HTTP | Internal |
| Netflix Recommendation Service | **8006** | HTTP | Internal |
| Netflix Payment Service | **8007** | HTTP | Internal |
| Netflix Notification Service | **8008** | HTTP | Internal |
| PrimeOS Monolith | **8020** | HTTP | Single service |
| Prometheus | **9090** | HTTP | Metrics store |
| AlertManager | **9093** | HTTP | Alert routing |
| OPA Server | **8181** | HTTP | Policy queries |
| Redis | **6379** | TCP | Cache / pub-sub |
| PostgreSQL | **5432** | TCP | Audit database |
| Loki | **3100** | HTTP | Log aggregation |
| Chaos Mesh Dashboard | **2334** | HTTP | Chaos control |

---

# PART 2 — TECH STACK DECISIONS (FINAL, WITH RATIONALE)

## 2.1 Why Each Technology Was Chosen

### Frontend: React 18 + TypeScript + Three.js (React Three Fiber) + Tailwind CSS

**React 18** — Component-based architecture maps perfectly to our multi-panel dashboard. React's virtual DOM efficiently handles the 60fps 3D visualization updates from Socket.IO events without re-rendering the entire page.

**TypeScript** — When you have 20+ WebSocket event types, Prometheus API responses, and Kubernetes object schemas flowing through your frontend, TypeScript's type safety catches 80% of data mapping bugs before runtime. This is non-negotiable for a complex dashboard.

**React Three Fiber (R3F)** — This is Three.js wrapped as React components. Three.js is the industry standard for WebGL 3D in browsers. R3F lets us write the 3D graph as React components instead of raw WebGL. `@react-three/drei` provides helpers (OrbitControls, labels, particles). `@react-three/postprocessing` adds bloom effects for the glowing nodes.

**Why NOT Flutter/Dart** — Flutter compiles to native mobile code first, web second. Three.js WebGL integration in Flutter is painful and poorly documented. For a browser-based dashboard with complex WebGL, React + R3F is the correct choice.

**Tailwind CSS** — Utility-first CSS allows rapid UI construction. The SENTINELS dashboard has a dark cyberpunk aesthetic (deep black backgrounds, cyan/blue accents, neon green status indicators). Tailwind's dark mode and arbitrary value support handles this perfectly.

### Backend: Python 3.12 + FastAPI

**Python** — The entire ML pipeline (scikit-learn Isolation Forest), the Kubernetes operator (Kopf), and the Prometheus client library are all Python-native. Mixing languages would create unnecessary complexity.

**FastAPI** — Async Python web framework with automatic OpenAPI documentation. 10x faster than Flask for concurrent requests. Critical because the Healer Agent receives AlertManager webhooks (potentially multiple simultaneously), queries Prometheus, calls OPA, AND manages Socket.IO connections — all concurrently. FastAPI's async/await handles this natively.

**Why NOT Go/Rust** — While Go is excellent for Kubernetes controllers, our ML pipeline requires Python. Writing the healer in Go and the ML in Python with a gRPC bridge adds complexity without benefit for a university project.

**Why NOT Node.js** — The scikit-learn Isolation Forest has no equivalent Node.js library that's production-ready. Python is the correct choice.

### Demo Applications: FastAPI (Netflix Microservices) + Django (Amazon Prime Monolith)

**Netflix Microservices in FastAPI** — Each of the 8 services is a small, independent FastAPI app. FastAPI's lightweight nature means each service consumes only ~50-100MB RAM. Total Netflix stack: ~600-800MB RAM. Acceptable for a laptop.

**Amazon Prime Monolith in Django** — Django is THE monolith framework. It has a built-in ORM (SQLite locally), admin panel, session management, and URL routing — everything a monolith needs in one framework. This intentional choice of Django vs FastAPI also demonstrates architectural contrast at the framework level.

**Why NOT Java/Spring Boot** — Spring Boot consumes 500MB+ RAM per instance. On a laptop running Kubernetes + monitoring + both apps + dashboard, Java would exhaust memory in minutes.

### Database: PostgreSQL + Redis + Prometheus TSDB

**PostgreSQL** — Relational database for audit logs, healing history, user data (for Netflix/Prime), and anomaly records. ACID compliance ensures healing records are never lost.

**Redis** — Two roles: (1) Circuit breaker state and cooldown timer storage (millisecond access required — Redis is 10x faster than PostgreSQL for these), (2) Socket.IO message broker for real-time event broadcasting to multiple dashboard clients.

**Prometheus TSDB** — Time series data ONLY lives in Prometheus. We do NOT store metrics in PostgreSQL. Prometheus is purpose-built for this and has PromQL for complex metric queries.

### Infrastructure: Docker + k3d + Helm 4 + Kopf

**Docker** — Containerizes every service. Non-negotiable for Kubernetes deployment.

**k3d** — k3s (lightweight Kubernetes) running inside Docker containers. Creates a full multi-node Kubernetes cluster on a laptop using minimal resources. `k3d cluster create sentinels --servers 1 --agents 2` gives us a 3-node cluster (1 control plane + 2 workers) consuming only ~600MB base RAM.

**Why NOT Minikube** — Minikube creates a VM which adds overhead. k3d runs k3s in Docker containers directly, using less memory and starting 10x faster.

**Why NOT Kind** — Kind is excellent for CI/CD testing but has known issues with LoadBalancer services locally. k3d handles port mapping to localhost more cleanly.

**Helm 4.1.1** — Packages all SENTINELS Kubernetes manifests into installable charts. Enables one-command deployment of the entire system.

**Kopf (Kubernetes Operator Pythonic Framework)** — Python-native operator framework. Since our healer is Python, using Kopf means zero language switching. Production-ready at v1.x.

### ML: scikit-learn 1.4+ (Isolation Forest)

As documented in the original TRD, Isolation Forest wins for this use case. `contamination=0.02`, `n_estimators=200`, `max_samples=256`, `random_state=42` (for reproducibility in demos). Model is trained on the first 5 minutes of baseline metrics after startup, then updated every 30 minutes.

### Monitoring: kube-prometheus-stack + Loki + Jaeger (OpenTelemetry)

**kube-prometheus-stack** — Single Helm install for Prometheus + AlertManager + Grafana + kube-state-metrics + node-exporter.

**Loki** — Log aggregation for all container logs. Integrates with Grafana (same datasource panel). This is our alternative to Elasticsearch — Loki is 10x less resource-hungry, making it laptop-safe.

**Jaeger** — Distributed tracing for Netflix microservices. When the Search Service calls the Content Service, Jaeger traces the full request chain. This is important for the demo: show a request trace that spans 3 microservices.

**Why NOT ELK Stack** — Elasticsearch alone requires 4GB+ RAM. On a laptop running everything else, this is impossible. Loki uses ~100MB.

### Chaos Engineering: Chaos Mesh v2.7.3 + k6

**Chaos Mesh v2.7.3** — Infrastructure fault injection (CPU stress, memory stress, pod kill, network chaos). Kubernetes-native via CRDs.

**k6** — HTTP load generator for DDoS/flood simulation. Runs as a Kubernetes Job. The dashboard sends a k6 script as a ConfigMap and creates the Job. k6 supports JavaScript-based test scripts with configurable VUs (virtual users) and duration.

### Security: OPA/Rego + mTLS + RBAC

**OPA/Rego** — CNCF-graduated policy engine. Every healing decision passes through OPA. Version-controlled policies in Git.

**cert-manager** — Automatic TLS certificate management for mTLS between AlertManager and Healer.

---

# PART 3 — NETFLIXOS: MICROSERVICES ARCHITECTURE (APPLICATION A)

## 3.1 NetflixOS Service Map

NetflixOS is designed to look and feel exactly like Netflix (2024 design). It has 8 backend services and one React frontend.

```
                            NETFLIXOS MICROSERVICES
                            
Browser → React UI (:3001)
               │
               ▼
        API Gateway (:8001)  ←── JWT validation, rate limiting, routing
               │
    ┌──────────┼──────────────────────────────────┐
    │          │           │          │            │
    ▼          ▼           ▼          ▼            ▼
User Svc   Content Svc  Search Svc  Stream Svc  Recommend Svc
(:8002)    (:8003)      (:8005)     (:8004)     (:8006)
    │          │                       │
    │          │                       ▼
    │          │               [YouTube IFrame API]
    │          │               (External - video playback)
    ▼          ▼
PostgreSQL  PostgreSQL      ┌────────────────────┐
(users)     (content)       │  Payment Svc (:8007)│  ← Simulated (no real payments)
                            │  Notif. Svc  (:8008)│  ← Simulated (email/push fake)
                            └────────────────────┘
```

## 3.2 Netflix Microservices — Detailed Specifications

### Service 1: API Gateway (Port 8001)
- **Framework:** FastAPI + httpx (async HTTP client for proxying)
- **Responsibilities:** Route all frontend requests to correct backend service; validate JWT tokens; rate limit (100 req/min per user); return 503 if downstream service is unavailable (graceful degradation)
- **Critical behavior:** If Search Service (:8005) is down, return `{"error": "Search temporarily unavailable", "available": false}` — Netflix UI shows "Search unavailable" message, but browsing and playback continue. This demonstrates microservice isolation.
- **Kubernetes:** 2 replicas for high availability, HPA configured (scale 2→5 on CPU>70%)

### Service 2: User Service (Port 8002)
- **Framework:** FastAPI
- **Responsibilities:** User registration, login (JWT issuance), profile management, watch history
- **Database:** PostgreSQL table `netflix_users`
- **Pre-seeded data:** 5 fake user accounts (user1@netflix.com through user5@netflix.com, password: "sentinels123") for demo purposes
- **Kubernetes:** 1 replica (stateless auth is idempotent)

### Service 3: Content Service (Port 8003)
- **Framework:** FastAPI
- **Responsibilities:** Movie/show catalog (title, description, genre, rating, YouTube video ID); Browse by category; Content metadata management
- **Database:** PostgreSQL table `netflix_content` with 50 pre-seeded movies
- **YouTube Mapping:** Each "movie" has a `youtube_id` field (e.g., "dQw4w9WgXcQ" maps to a trailer). The content service returns this ID; the React frontend uses YouTube IFrame API to embed it.
- **Pre-seeded categories:** Action, Drama, Comedy, Documentary, Sci-Fi (10 titles each)
- **Kubernetes:** 1 replica

### Service 4: Streaming Service (Port 8004)
- **Framework:** FastAPI
- **Responsibilities:** "Play" button handler — records view start event; Returns YouTube embed URL to frontend; Tracks watch progress in Redis (key: `watch:{user_id}:{content_id}`)
- **Important:** This service does NOT stream actual video. It delegates to YouTube IFrame API. But it logs every "stream start" event to Prometheus: `stream_starts_total{service="streaming", content_id="xxx"}`
- **Kubernetes:** 2 replicas (most-hit service during demos)

### Service 5: Search Service (Port 8005)
- **Framework:** FastAPI
- **Responsibilities:** Full-text search across movie titles and descriptions; returns ranked results
- **Implementation:** Simple SQLite FTS5 (Full-Text Search) — lightweight, no Elasticsearch needed
- **Why SQLite here:** SQLite FTS5 provides good-enough search for a demo with 50 movies. Adding Elasticsearch would consume 2GB RAM we don't have.
- **Chaos Target:** This is the PRIMARY target for attack demos. Killing it shows microservice fault isolation visually.
- **Kubernetes:** 1 replica (deliberately fragile for demo effect)

### Service 6: Recommendation Service (Port 8006)
- **Framework:** FastAPI
- **Responsibilities:** Returns "recommended" movies based on user watch history; Simple collaborative filtering using cosine similarity on pre-computed vectors
- **Pre-computed recommendations:** Stored as JSON in Redis on startup. No real-time ML (too slow for a service that must respond in <50ms)
- **Kubernetes:** 1 replica

### Service 7: Payment Service (Port 8007)
- **Framework:** FastAPI
- **Responsibilities:** Subscription plan display; SIMULATED payment (always succeeds); Subscription status check
- **Important:** No real payment processing. This service exists purely for architectural completeness and to demonstrate that even critical services like payments can be isolated and healed.
- **Kubernetes:** 1 replica

### Service 8: Notification Service (Port 8008)
- **Framework:** FastAPI
- **Responsibilities:** SIMULATED email/push notifications; Logs notification events to PostgreSQL; Used by User Service to "send welcome emails"
- **Kubernetes:** 1 replica

### Netflix React Frontend (Port 3001)
- **Framework:** React 18 + TypeScript + Tailwind CSS
- **Design:** Netflix's exact dark red (#E50914) color scheme, Bebas Neue title font, card-based browsing layout, hover preview cards, category row scrolling
- **Key pages:** Landing/Browse, Movie Detail Modal (with YouTube IFrame embed), Search Results, My List, Profile
- **Authentication:** JWT stored in localStorage; all API calls go through API Gateway (:8001)
- **Fault-resilient UI:** If a backend service returns 503, show graceful "Service temporarily unavailable" message for that section only — rest of page renders normally

## 3.3 Netflix Content Database Seed (50 Movies)

The 50 pre-seeded movies use public YouTube video IDs (trailers, public domain films, Creative Commons content). The seeding script runs automatically on first startup.

Categories and sample mappings:
- **Action:** "Inception Trailer", "The Dark Knight Rises Trailer", etc. (YouTube trailer IDs)
- **Documentary:** Public domain documentaries available on YouTube
- **Comedy, Drama, Sci-Fi:** Mix of trailers and public domain films

---

# PART 4 — PRIMEOS: MONOLITHIC ARCHITECTURE (APPLICATION B)

## 4.1 PrimeOS Architecture

PrimeOS is a SINGLE Django 5.x application that includes ALL features in one codebase, one process, one Docker container.

```
                            PRIMEOS MONOLITH
                            
Browser → React UI (:3002)
               │
               ▼
        Django App (:8020)  ← Single process, all features here
        │
        ├── /api/auth/         ← Authentication module
        ├── /api/content/      ← Content/catalog module  
        ├── /api/search/       ← Search module
        ├── /api/recommend/    ← Recommendations module
        ├── /api/stream/       ← Streaming module (YouTube IFrame delegation)
        ├── /api/payment/      ← Payment module (simulated)
        └── /api/notifications/← Notification module (simulated)
               │
        SQLite Database        ← Single file database (demo simplicity)
        (prime.db)             ← All tables in one file
```

### Why Django for Monolith?
Django enforces monolithic patterns by design: single settings file, single URL router, shared ORM models, shared middleware. It's the perfect demonstration of a traditional web application that predates microservices.

### The Key Demo Contrast
- Kill Netflix's Search Service → Only search breaks, everything else works
- Kill PrimeOS pod → **ENTIRE AMAZON PRIME GOES DOWN** — browse, search, stream, everything returns 503

This visual contrast IS the proof that microservices provide better fault isolation, which is a core research finding SENTINELS can demonstrate live.

## 4.2 PrimeOS React Frontend (Port 3002)
- **Design:** Amazon Prime Video aesthetic — dark navy (#0F171E), yellow/gold (#F5E72E) accents, card-based content grid
- **Features:** Browse, Search, Watch (YouTube IFrame), Profile, Watchlist
- **Fault behavior:** When the single monolith pod is killed, ALL pages show "Amazon Prime Video is temporarily unavailable. We're working to restore service." — full blackout, no graceful degradation possible

---

# PART 5 — SENTINELS COMMAND CENTER: 3D DASHBOARD

## 5.1 Dashboard Architecture

The SENTINELS Command Center is a React SPA with five main panels:

```
╔══════════════════════════════════════════════════════════════════════════╗
║          SENTINELS COMMAND CENTER v2.0                    [LIVE] ●       ║
╠══════════════════════════════════════════╦═══════════════════════════════╣
║                                          ║   ATTACK LAUNCHER             ║
║                                          ║                               ║
║        3D TOPOLOGY GRAPH                 ║   Target: [Netflix▼][Prime▼]  ║
║                                          ║   Attack: [Pod Kill  ▼]       ║
║   (Force-directed 3D visualization)      ║   Intensity: [●●●○○]          ║
║   Nodes = Pods (colored by health)       ║   [  LAUNCH ATTACK  ]         ║
║   Edges = Service connections            ║                               ║
║   Particles = Active healing             ║   Active Attacks:             ║
║                                          ║   ● CPU Stress on search-svc  ║
║                                          ║   ○ No active attacks         ║
║                                          ╠═══════════════════════════════╣
║                                          ║   HEALING LOG                 ║
╠══════════════════════════════════════════╣                               ║
║   METRICS SCORECARD                      ║   [14:23:01] ✅ search-svc   ║
║                                          ║   restarted | CPU -0.47       ║
║   MTTD  │ 91s    │ Target: <60s  │ 🟡   ║   CRITICAL → RESOLVED        ║
║   MTTR  │ 14s    │ Target: <5min │ ✅   ║                               ║
║   F1    │ 0.94   │ Target: >0.90 │ ✅   ║   [14:22:10] 🔴 ATTACK       ║
║   FPR   │ 3.2%   │ Target: <5%   │ ✅   ║   CPU Stress → search-svc    ║
║   Avail │ 99.87% │ Target: >99.9 │ 🟡   ║   Injected by Dashboard      ║
║   Recov │ 97.3%  │ Target: >95%  │ ✅   ║                               ║
╠══════════════════════════════════════════╩═══════════════════════════════╣
║               GRAFANA EMBEDDED DASHBOARD (iframe)                        ║
║               [Netflix RED Dashboard] [Prime USE Dashboard] [Healer]     ║
╚══════════════════════════════════════════════════════════════════════════╝
```

## 5.2 3D Topology Graph — Technical Specification

**Library Stack:** React Three Fiber + @react-three/drei + @react-three/postprocessing + three-forcegraph (or react-force-graph-3d)

**Node Representation:**
Every Kubernetes pod is a sphere in 3D space:
- Node size: proportional to pod's resource usage (larger = more CPU)
- Node color states (smooth transitions via lerp):
  - `#00FF88` (neon green) = Healthy
  - `#FFD700` (gold) = Warning (anomaly detected, monitoring)
  - `#FF6600` (orange) = Degraded (anomaly confirmed, action pending)
  - `#FF0000` (red) = Critical (pod in CrashLoopBackOff or OOMKilled)
  - `#0088FF` (electric blue) = Healing (action executing)
  - `#FFFFFF` → fade to green = Recovered
  - `#444444` (dark gray) = Pod missing/terminated

**Edge Representation:**
Service-to-service connections as animated lines:
- Healthy traffic: thin white lines with subtle flow particles
- Under attack: thick red pulsing lines
- Broken (service unreachable): dashed red lines

**SENTINELS Core Node:**
At the center of the graph, a special node representing the Healer Agent:
- Animated spinning ring (torus geometry)
- Color: cyan/teal (#00CCCC)
- When healing: emits blue particle streams toward target node

**Attack Visualization:**
When an attack is launched from the dashboard:
- A red "lightning bolt" particle system emanates from a "ATTACKER" node (positioned at the edge of the graph)
- Particles flow along the network edges toward the target service
- Target node immediately changes color to orange, then red
- The node wobbles/pulses to indicate stress

**Healing Visualization:**
When SENTINELS detects and heals:
- Blue particle stream from SENTINELS core node → target node
- Target node pulses blue during healing
- After recovery: green ring burst effect (like an explosion but in green)

**Obsidian-Style Graph Features:**
- Orbit controls (drag to rotate, scroll to zoom)
- Node labels on hover (pod name, namespace, CPU%, memory%, status)
- Click on node to open pod details sidebar
- Graph auto-arranges via force simulation (pods in same namespace cluster together)

**3D Graph Data Source:**
The graph state is updated by polling the SENTINELS Dashboard Backend API every 2 seconds:
```
GET /api/topology
Response: {
  nodes: [{id, name, namespace, status, cpu_percent, memory_percent, type}],
  edges: [{source, target, traffic_rate, error_rate}],
  attacks: [{target_pod, attack_type, started_at}],
  healing_events: [{pod, action, status, started_at}]
}
```
The backend reads this from: Kubernetes API (pod states) + Prometheus (metrics) + Redis (active attacks/healing)

## 5.3 Attack Launcher Module

10 attack types, each with configurable parameters:

| Attack Name | Type | Description | Implementation |
|---|---|---|---|
| **Pod Kill** | Infrastructure | Instantly terminates the target pod | Chaos Mesh PodChaos (action: pod-kill) |
| **CPU Stress** | Resource | Saturates CPU cores to X% | Chaos Mesh StressChaos (cpu.workers, load) |
| **Memory Leak** | Resource | Gradually consumes memory until OOM | Chaos Mesh StressChaos (memory.size) |
| **Network Latency** | Network | Adds Xms delay to all traffic | Chaos Mesh NetworkChaos (action: delay) |
| **Network Partition** | Network | Drops all network traffic | Chaos Mesh NetworkChaos (action: partition) |
| **HTTP Flood (DDoS)** | Application | Sends X concurrent requests/sec | k6 Job (configurable VUs, duration) |
| **Disk I/O Stress** | Storage | Saturates disk read/write | Chaos Mesh IOChaos (action: latency) |
| **DNS Failure** | Network | Corrupts DNS responses | Chaos Mesh DNSChaos |
| **Container OOM** | Resource | Instantly exhausts all memory | Chaos Mesh StressChaos (memory exhaustion) |
| **Cascading Failure** | Complex | Chain: latency → CPU spike → OOM | Chaos Mesh Workflow CRD (serial phases) |

**Attack Launcher UI Flow:**
1. Select Target: dropdown [Netflix (All Services) / Netflix Search / Netflix Streaming / Netflix User / PrimeOS]
2. Select Attack Type: dropdown of 10 attacks
3. Configure Intensity: slider (1-5, maps to chaos parameters)
4. Select Duration: 30s / 60s / 120s / 300s
5. Click "LAUNCH ATTACK" button
6. Dashboard sends POST to `/api/attacks/launch` on SENTINELS backend
7. Backend creates Chaos Mesh CRD via Kubernetes API
8. Dashboard shows attack as active in Attack Status panel
9. 3D graph immediately starts showing the attack visualization

**Safety Controls for Dashboard:**
- Cannot launch a new attack if >2 attacks already active (prevents cluster destruction)
- Cannot attack SENTINELS system namespace (healer is protected)
- Cannot attack Prometheus/monitoring namespace
- All attacks auto-expire after max 300 seconds (Chaos Mesh `duration` field)
- "EMERGENCY STOP" button: immediately deletes ALL Chaos CRDs and k6 Jobs

## 5.4 Metrics Scorecard Module

**Metrics Aggregator Service** (FastAPI, Port 5050) calculates all academic metrics:

### F1 Score Calculation
```python
# Queries Prometheus for ground truth (attack active) vs healer predictions
attacks = query_prometheus("chaos_mesh_experiment_status == 1")  # Attack windows
alerts_fired = query_prometheus("ALERTS{alertstate='firing'}")   # Healer detections

# Classification matrix:
# True Positive (TP): Attack active AND alert fired
# False Positive (FP): No attack AND alert fired  
# False Negative (FN): Attack active AND no alert fired
# True Negative (TN): No attack AND no alert

precision = TP / (TP + FP)
recall = TP / (TP + FN)
f1 = 2 * (precision * recall) / (precision + recall)
```

### MTTD (Mean Time to Detect)
```python
# For each attack event, query PostgreSQL healing_audit_log:
# MTTD = AVG(alert_fired_at - chaos_experiment_start_at)
mttd = query_db("SELECT AVG(EXTRACT(EPOCH FROM (detection_time - fault_injection_time))) FROM healing_audit_log WHERE result='SUCCESS'")
```

### MTTR (Mean Time to Recover)
```python
# MTTR = AVG(recovery_confirmed_at - alert_fired_at)
mttr = query_db("SELECT AVG(EXTRACT(EPOCH FROM (recovery_time - detection_time))) FROM healing_audit_log WHERE result='SUCCESS'")
```

All metrics are exposed via REST API AND emitted via Socket.IO every 10 seconds to the dashboard.

---
---

# PART 6 — DEVELOPMENT ROADMAP: 3 BLOCKS, 12 PHASES

The entire project is divided into 3 Blocks and 12 Phases. Each phase has clear deliverables, a definition of done, a chaos checklist, and resource estimates.

**TOTAL ESTIMATED DEVELOPMENT TIME:** 8-10 weeks for a solo developer following this document.

---

## BLOCK 1 — FOUNDATION & DEMO APPLICATIONS
### Phases 1 through 4 | Estimated: 2-3 weeks

**Goal of Block 1:** By the end of Block 1, you have two fully functional streaming applications (Netflix + Prime) running locally in Docker Compose. No Kubernetes yet. No SENTINELS yet. Just two real web apps you can browse, search, and "watch" videos on. This is the foundation everything else builds on.

---

### PHASE 1: Local Development Environment Setup
**Duration:** 2-3 days  
**Deliverable:** Laptop running k3d Kubernetes cluster + all tools installed

#### 1.1 Required Tools Installation (in exact order)

**Step 1: Install Docker Desktop or Docker Engine**
- MacOS: Install Docker Desktop from docker.com (includes Docker Compose)
- Windows: Install Docker Desktop with WSL2 backend enabled
- Linux: `sudo apt install docker.io docker-compose-v2`
- Verify: `docker --version` (expect 24.x or 25.x)

**Step 2: Install kubectl**
- Follow official docs: kubernetes.io/docs/tasks/tools
- MacOS: `brew install kubectl`
- Verify: `kubectl version --client`

**Step 3: Install k3d**
- Run: `curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash`
- Verify: `k3d version` (expect v5.7+)

**Step 4: Install Helm 4**
- MacOS: `brew install helm`
- Linux: Follow helm.sh/docs/intro/install
- Verify: `helm version` (ensure 4.x)

**Step 5: Install Python 3.12+**
- MacOS: `brew install python@3.12`
- Linux: `sudo apt install python3.12 python3.12-venv`
- Verify: `python3.12 --version`

**Step 6: Install Node.js 20+ (for React frontends)**
- Recommended: Install via nvm (Node Version Manager)
- `nvm install 20 && nvm use 20`
- Verify: `node --version` (expect 20.x)

**Step 7: Install k9s (optional but highly recommended)**
- k9s is a terminal UI for Kubernetes cluster management
- MacOS: `brew install k9s`
- Makes debugging Kubernetes pods 10x faster during development

#### 1.2 Create k3d Kubernetes Cluster

```bash
# Create cluster with port mappings for all our services
k3d cluster create sentinels \
  --servers 1 \
  --agents 2 \
  --port "3000:30000@loadbalancer" \
  --port "3001:30001@loadbalancer" \
  --port "3002:30002@loadbalancer" \
  --port "3003:30003@loadbalancer" \
  --port "9090:30090@loadbalancer" \
  --port "9093:30093@loadbalancer" \
  --k3s-arg "--disable=traefik@server:0" \
  --memory "10g"

# Verify cluster is running
kubectl get nodes
# Expected: 3 nodes (1 server, 2 agents) in Ready state
```

#### 1.3 Repository Structure

All code lives in a single monorepo with this exact structure:
```
sentinels-v2/                          # Root of Git repository
├── README.md
├── docker-compose.dev.yml             # For Phase 1-2 local development
├── Makefile                           # Convenience commands
│
├── apps/
│   ├── netflix/                       # NetflixOS Application
│   │   ├── frontend/                  # React frontend (Port 3001)
│   │   │   ├── src/
│   │   │   ├── package.json
│   │   │   └── Dockerfile
│   │   ├── api-gateway/               # FastAPI gateway (Port 8001)
│   │   ├── user-service/              # FastAPI (Port 8002)
│   │   ├── content-service/           # FastAPI (Port 8003)
│   │   ├── streaming-service/         # FastAPI (Port 8004)
│   │   ├── search-service/            # FastAPI (Port 8005)
│   │   ├── recommendation-service/    # FastAPI (Port 8006)
│   │   ├── payment-service/           # FastAPI (Port 8007)
│   │   └── notification-service/      # FastAPI (Port 8008)
│   │
│   └── prime/                         # PrimeOS Application
│       ├── frontend/                  # React frontend (Port 3002)
│       │   ├── src/
│       │   ├── package.json
│       │   └── Dockerfile
│       └── backend/                   # Django monolith (Port 8020)
│           ├── primeOS/               # Django project
│           ├── manage.py
│           ├── requirements.txt
│           └── Dockerfile
│
├── sentinels/                         # SENTINELS Core System
│   ├── healer-agent/                  # FastAPI healer (Port 5000)
│   │   ├── main.py
│   │   ├── ml/                        # Isolation Forest pipeline
│   │   ├── policy/                    # OPA integration
│   │   ├── operator/                  # Kopf operator handlers
│   │   ├── safety/                    # Circuit breaker, cooldown
│   │   ├── models/                    # PostgreSQL schemas
│   │   └── Dockerfile
│   ├── metrics-aggregator/            # FastAPI metrics (Port 5050)
│   │   ├── main.py
│   │   └── Dockerfile
│   └── opa-policies/                  # Rego policy files
│       ├── healing_policy.rego
│       └── safety_policy.rego
│
├── dashboard/                         # SENTINELS Command Center
│   ├── frontend/                      # React + Three.js (Port 3000)
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── TopologyGraph3D/   # Three.js graph
│   │   │   │   ├── AttackLauncher/    # Attack controls
│   │   │   │   ├── HealingLog/        # Live event feed
│   │   │   │   ├── MetricsScorecard/  # F1, MTTD, MTTR
│   │   │   │   └── GrafanaEmbed/      # Grafana iframe
│   │   │   ├── hooks/
│   │   │   │   ├── useWebSocket.ts    # Socket.IO connection
│   │   │   │   └── useTopology.ts     # Kubernetes topology polling
│   │   │   └── App.tsx
│   │   ├── package.json
│   │   └── Dockerfile
│   └── backend/                       # FastAPI dashboard API (port 3000/api)
│       ├── main.py                    # Topology API, Attack launcher
│       └── Dockerfile
│
├── monitoring/                        # Monitoring configuration
│   ├── prometheus/
│   │   ├── values.yaml               # kube-prometheus-stack Helm values
│   │   └── rules/                    # PrometheusRule CRDs
│   ├── grafana/
│   │   └── dashboards/               # Grafana dashboard JSONs
│   └── alertmanager/
│       └── config.yaml
│
├── kubernetes/                        # Kubernetes manifests
│   ├── namespaces/
│   ├── rbac/
│   ├── network-policies/
│   └── helm-charts/
│       ├── sentinels/                 # Umbrella chart
│       ├── netflix/                   # Netflix chart
│       └── prime/                     # Prime chart
│
├── chaos/                             # Chaos engineering
│   ├── experiments/                   # Chaos Mesh CRD YAMLs
│   └── k6-scripts/                    # k6 load test scripts
│
└── scripts/                           # Utility scripts
    ├── setup.sh                       # One-command setup
    ├── seed-db.py                     # Seed databases
    └── demo-run.sh                    # Demo sequence script
```

#### Phase 1 Chaos Checklist
- [ ] Run `kubectl get nodes` — all 3 nodes show Ready
- [ ] Run `kubectl get namespaces` — shows default, kube-system
- [ ] Run `docker stats` — cluster using <2GB RAM baseline
- [ ] Run `helm version` — shows 4.x
- [ ] Run `python3.12 -c "import sklearn; print(sklearn.__version__)"` — shows 1.4+

---

### PHASE 2: NetflixOS — Microservices Application
**Duration:** 5-7 days  
**Deliverable:** Fully functional Netflix-like streaming UI with 8 backend microservices

#### 2.1 Backend Services (Each service follows this pattern)

**Standard FastAPI Service Structure:**
```
service-name/
├── main.py              # FastAPI app + routes
├── models.py            # Pydantic request/response schemas
├── database.py          # SQLAlchemy setup
├── requirements.txt     # Dependencies
├── Dockerfile
└── tests/
    └── test_api.py
```

**Standard Dependencies (all services):**
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.30
asyncpg==0.29.0           # For async PostgreSQL
prometheus-client==0.20.0 # Metrics exposure
python-jose[cryptography] # JWT handling
httpx==0.27.0              # Async HTTP client (for gateway)
redis==5.0.0               # Redis client
```

**Every service MUST expose these Prometheus metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', 
                        ['method', 'endpoint', 'status_code', 'service'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency',
                            ['method', 'endpoint', 'service'])
ACTIVE_REQUESTS = Gauge('http_requests_active', 'Active requests', ['service'])

# Mount metrics endpoint at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

**Every service MUST have health check endpoint:**
```python
@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow()}

@app.get("/ready")
async def ready():
    # Check database connection, Redis connection
    # Returns 200 if ready, 503 if not
```

#### 2.2 NetflixOS React Frontend Design

**Design Direction: "Netflix Dark — Precision Cinematic"**
- Background: `#000000` (pure black)
- Primary accent: `#E50914` (Netflix red)
- Secondary: `#FFFFFF` text
- Tertiary: `#141414` (card backgrounds)
- Fonts: `Bebas Neue` (titles), `Inter` (body)
- Card hover: 1.1x scale + shadow + info overlay (CSS transition 200ms)

**Key UI Components:**
- `<HeroSection>` — Full-width banner with featured content, YouTube trailer autoplay on hover
- `<ContentRow>` — Horizontal scrollable row with 20 cards per category
- `<ContentCard>` — Movie/show card with hover-expand behavior
- `<VideoModal>` — Full-screen modal with YouTube IFrame embed
- `<SearchBar>` — Debounced search (300ms) calling Search Service
- `<NavBar>` — Netflix-style top navigation with profile menu

**YouTube Integration Pattern:**
```typescript
// ContentCard.tsx
const handlePlay = async (contentId: string) => {
  const response = await fetch(`/api/stream/${contentId}/play`);
  const { youtube_id, title } = await response.json();
  setVideoModal({ 
    open: true, 
    youtubeId: youtube_id,
    title 
  });
};

// VideoModal.tsx  
<iframe
  src={`https://www.youtube.com/embed/${youtubeId}?autoplay=1&controls=1`}
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope"
  allowFullScreen
/>
```

#### Phase 2 Chaos Checklist
- [ ] Open http://localhost:3001 — Netflix UI loads correctly
- [ ] Login with user1@netflix.com / sentinels123 — Works
- [ ] Browse content — 50 movies visible in correct categories
- [ ] Search for "action" — Returns relevant results in <500ms
- [ ] Click "Play" on any movie — YouTube IFrame loads and plays
- [ ] Kill `search-service` container: `docker stop netflix-search` — Browse/stream still work, search shows "temporarily unavailable"
- [ ] Restart search service — Search resumes
- [ ] All 8 services expose /health endpoints returning 200

---

### PHASE 3: PrimeOS — Monolithic Application
**Duration:** 3-4 days  
**Deliverable:** Functional Amazon Prime Video-like app as a single Django monolith

#### 3.1 Django Monolith Structure

```
prime/backend/
├── primeOS/                # Django project directory
│   ├── settings.py         # All config here
│   ├── urls.py             # All routes here (single router)
│   └── wsgi.py
├── apps/                   # Django apps (all in one process)
│   ├── auth_module/        # models.py, views.py, urls.py for auth
│   ├── content_module/     # All content management
│   ├── search_module/      # Search functionality
│   ├── stream_module/      # Streaming delegation
│   └── recommend_module/   # Recommendations
├── requirements.txt
│   # django==5.0
│   # djangorestframework==3.15
│   # django-prometheus          # Auto-instruments Django with metrics
│   # django-cors-headers
├── Dockerfile
└── manage.py
```

**Key Django Configuration for Observability:**
```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_prometheus',  # Auto-generates prometheus metrics for all Django views
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',  # MUST BE FIRST
    ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',   # MUST BE LAST
]
```

**`django-prometheus` automatically generates:**
- `django_http_requests_total_by_method_total` — Request counts by HTTP method
- `django_http_responses_total_by_status_total` — Response counts by status code
- `django_http_requests_latency_seconds` — Request latency histogram
- `django_db_execute_total` — Database query count

This single package gives PrimeOS the same level of observability as the Netflix microservices — crucial for SENTINELS to monitor it.

#### 3.2 PrimeOS React Frontend Design

**Design Direction: "Prime Video — Deep Space Navy"**
- Background: `#0F171E` (deep navy)
- Primary accent: `#00A8E1` (Prime blue)
- Secondary accent: `#F5E72E` (Amazon yellow)
- Fonts: `Amazon Ember` (substitute: `Montserrat`) for body
- Card hover: Brightness increase + border glow in Prime blue
- Content grid: 5-column grid (vs Netflix's horizontal scroll rows)

**Fault Display Behavior:**
When the monolith pod is killed, ALL fetch requests fail. The frontend catches this:
```typescript
// api.ts - Global error handler
const handleApiError = (error: Error) => {
  if (error.message.includes('503') || error.message.includes('network')) {
    // Show full-page outage screen
    window.dispatchEvent(new CustomEvent('SERVICE_OUTAGE'));
  }
};

// App.tsx
const [serviceOutage, setServiceOutage] = useState(false);
useEffect(() => {
  window.addEventListener('SERVICE_OUTAGE', () => setServiceOutage(true));
  window.addEventListener('SERVICE_RESTORED', () => setServiceOutage(false));
}, []);

if (serviceOutage) return <FullPageOutageScreen />; // Shows "temporarily unavailable"
```

#### Phase 3 Chaos Checklist
- [ ] Open http://localhost:3002 — Prime UI loads with navy/blue design
- [ ] Browse content — Different 50 movies from Netflix (non-overlapping catalog)
- [ ] Search works — Returns results from Django's FTS
- [ ] Play works — YouTube IFrame embeds
- [ ] Kill the Django container — ENTIRE Prime site shows outage screen
- [ ] Restart Django — After 10-15 seconds, site returns fully
- [ ] Compare with Netflix behavior — Observe the architectural difference clearly

---

### PHASE 4: Kubernetes Deployment of Both Applications
**Duration:** 3-4 days  
**Deliverable:** Both apps running in k3d cluster, accessible via localhost ports

#### 4.1 Kubernetes Namespace Strategy

```yaml
# kubernetes/namespaces/all-namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: netflix
  labels:
    sentinels-monitored: "true"
    app: netflix
---
apiVersion: v1
kind: Namespace
metadata:
  name: prime
  labels:
    sentinels-monitored: "true"
    app: prime
---
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
---
apiVersion: v1
kind: Namespace
metadata:
  name: sentinels-system
  labels:
    sentinels-protected: "true"  # SENTINELS cannot attack its own namespace
---
apiVersion: v1
kind: Namespace
metadata:
  name: chaos
---
apiVersion: v1
kind: Namespace
metadata:
  name: dashboard
```

#### 4.2 Standard Kubernetes Deployment Template

Every microservice follows this exact Kubernetes Deployment structure:

```yaml
# kubernetes/netflix/search-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: search-service
  namespace: netflix
  labels:
    app: search-service
    version: "1.0"
    sentinels-target: "true"  # Marks this as a SENTINELS monitoring target
spec:
  replicas: 1                  # Search service runs 1 replica (deliberately fragile for demos)
  selector:
    matchLabels:
      app: search-service
  template:
    metadata:
      labels:
        app: search-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8005"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: netflix-sa  # Minimal RBAC
      containers:
      - name: search-service
        image: sentinels/netflix-search:latest
        ports:
        - containerPort: 8005
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: netflix-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: netflix-secrets
              key: redis-url
        resources:
          requests:             # MINIMUM resources Kubernetes must allocate
            memory: "64Mi"
            cpu: "50m"          # 50 millicores = 0.05 CPU
          limits:               # MAXIMUM resources container can use
            memory: "256Mi"     # OOM kill if exceeded (triggers SENTINELS)
            cpu: "500m"         # Throttled if exceeded (triggers CPU alert)
        livenessProbe:          # If this fails, Kubernetes restarts the container
          httpGet:
            path: /health
            port: 8005
          initialDelaySeconds: 15
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:         # If this fails, pod removed from load balancer
          httpGet:
            path: /ready
            port: 8005
          initialDelaySeconds: 5
          periodSeconds: 5
          failureThreshold: 3
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        readOnlyRootFilesystem: true
```

#### 4.3 Resource Budget Planning (CRITICAL for laptop)

Total cluster memory budget: 8GB (leaving 8GB for OS, Docker, browser)

| Component | Memory Request | Memory Limit |
|---|---|---|
| Netflix API Gateway | 64Mi | 256Mi |
| Netflix User Service | 64Mi | 256Mi |
| Netflix Content Service | 64Mi | 256Mi |
| Netflix Search Service | 64Mi | 256Mi |
| Netflix Streaming Service | 64Mi | 256Mi |
| Netflix Recommendation Service | 64Mi | 256Mi |
| Netflix Payment Service | 32Mi | 128Mi |
| Netflix Notification Service | 32Mi | 128Mi |
| Netflix Frontend | 64Mi | 256Mi |
| PrimeOS Backend | 128Mi | 512Mi |
| PrimeOS Frontend | 64Mi | 256Mi |
| PostgreSQL (shared) | 256Mi | 1Gi |
| Redis | 128Mi | 512Mi |
| Prometheus | 512Mi | 1Gi |
| AlertManager | 64Mi | 128Mi |
| Grafana | 128Mi | 256Mi |
| Loki | 128Mi | 512Mi |
| Healer Agent | 256Mi | 512Mi |
| OPA Server | 64Mi | 256Mi |
| Metrics Aggregator | 64Mi | 256Mi |
| Dashboard Backend | 64Mi | 256Mi |
| Dashboard Frontend | 64Mi | 256Mi |
| Chaos Mesh | 256Mi | 512Mi |
| k3d overhead | ~600Mi | — |
| **TOTAL** | **~3.7Gi** | **~8.3Gi** |

This fits within an 8GB budget with ~200-300MB headroom.

#### Phase 4 Chaos Checklist
- [ ] `kubectl get pods -n netflix` — All 9 pods in Running state
- [ ] `kubectl get pods -n prime` — All 2 pods in Running state
- [ ] Access http://localhost:3001 — Netflix loads from Kubernetes
- [ ] Access http://localhost:3002 — Prime loads from Kubernetes
- [ ] `kubectl delete pod -n netflix -l app=search-service` — Pod recreated within 15s
- [ ] `kubectl delete pod -n prime -l app=primeos-backend` — Pod recreated within 15s, site outage during restart
- [ ] `kubectl top pods -n netflix` — Resource usage shows correct ranges
- [ ] `kubectl logs -n netflix -l app=search-service` — Logs visible and formatted as JSON

---

## BLOCK 2 — SENTINELS CORE ENGINE
### Phases 5 through 8 | Estimated: 3-4 weeks

**Goal of Block 2:** The automated self-healing brain. By the end of Block 2, SENTINELS actively monitors both applications, detects anomalies using ML, decides what to do using policies, and executes healing actions automatically — without any human intervention.

---

### PHASE 5: Monitoring Stack
**Duration:** 3-4 days  
**Deliverable:** Full Prometheus + AlertManager + Grafana + Loki stack collecting metrics from all services

#### 5.1 kube-prometheus-stack Installation

```bash
# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm install kube-prometheus-stack \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values monitoring/prometheus/values.yaml \
  --version 82.10.x

# Install Loki for log aggregation
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set promtail.enabled=true \
  --set grafana.enabled=false  # We use the Grafana from kube-prometheus-stack
```

#### 5.2 Critical Prometheus Custom Values (monitoring/prometheus/values.yaml)

```yaml
# monitoring/prometheus/values.yaml
prometheus:
  prometheusSpec:
    scrapeInterval: "15s"
    evaluationInterval: "15s"
    retention: "7d"
    retentionSize: "5GB"
    
    # CRITICAL: Tell Prometheus to discover ServiceMonitors in ALL namespaces
    serviceMonitorSelectorNilUsesHelmValues: false
    serviceMonitorSelector: {}
    serviceMonitorNamespaceSelector: {}
    podMonitorSelector: {}
    podMonitorNamespaceSelector: {}
    ruleSelector: {}
    ruleNamespaceSelector: {}
    
    # Additional scrape configs for direct pod annotation scraping
    additionalScrapeConfigs:
    - job_name: 'kubernetes-pods-custom'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: (.+)
        target_label: __address__
        replacement: $1

alertmanager:
  alertmanagerSpec:
    config:
      global:
        resolve_timeout: 5m
      
      route:
        group_by: ['alertname', 'namespace', 'pod']
        group_wait: 10s       # REDUCED for faster demo response
        group_interval: 30s   # REDUCED for faster demo response
        repeat_interval: 5m
        receiver: 'sentinels-healer'
        routes:
        - receiver: 'sentinels-healer'
          match_re:
            severity: "warning|critical"
          continue: true
      
      receivers:
      - name: 'sentinels-healer'
        webhook_configs:
        - url: 'http://healer-agent.sentinels-system.svc.cluster.local:5000/alerts'
          send_resolved: true
          http_config:
            bearer_token: "sentinels-webhook-token-change-in-production"

grafana:
  adminPassword: "sentinels2024"
  sidecar:
    dashboards:
      enabled: true
      searchNamespace: ALL
  grafana.ini:
    server:
      domain: localhost
      root_url: "%(protocol)s://%(domain)s:3003"
    security:
      allow_embedding: true  # Required for dashboard iframe embedding
```

#### 5.3 PrometheusRule CRDs (Alert Definitions)

```yaml
# monitoring/prometheus/rules/sentinels-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: sentinels-healing-rules
  namespace: monitoring
  labels:
    app: kube-prometheus-stack
    release: kube-prometheus-stack
spec:
  groups:
  
  - name: sentinels.cpu
    interval: 15s
    rules:
    - alert: HighCPUUsage
      expr: |
        (sum(rate(container_cpu_usage_seconds_total{namespace=~"netflix|prime",
          container!=""}[2m])) by (namespace, pod, container) /
         sum(kube_pod_container_resource_limits{namespace=~"netflix|prime",
          resource="cpu"}) by (namespace, pod, container)) > 0.80
      for: 1m          # REDUCED to 1min for faster demo response
      labels:
        severity: critical
        healing_action: restart_pod
      annotations:
        summary: "High CPU usage on {{ $labels.pod }}"
        description: "CPU usage is {{ $value | humanizePercentage }} on pod {{ $labels.pod }} in {{ $labels.namespace }}"
  
  - name: sentinels.memory
    interval: 15s
    rules:
    - alert: HighMemoryUsage
      expr: |
        (container_memory_working_set_bytes{namespace=~"netflix|prime", container!=""}
         / kube_pod_container_resource_limits{namespace=~"netflix|prime", resource="memory"}) > 0.85
      for: 1m
      labels:
        severity: critical
        healing_action: restart_pod
      annotations:
        summary: "High memory usage on {{ $labels.pod }}"
  
  - name: sentinels.crashes
    interval: 15s
    rules:
    - alert: PodCrashLooping
      expr: |
        increase(kube_pod_container_status_restarts_total{
          namespace=~"netflix|prime"}[5m]) > 2
      for: 30s          # Very fast detection for crash loops
      labels:
        severity: critical
        healing_action: redeploy
      annotations:
        summary: "Pod {{ $labels.pod }} is crash-looping"
  
  - name: sentinels.availability
    interval: 15s
    rules:
    - alert: PodNotReady
      expr: |
        kube_pod_status_ready{namespace=~"netflix|prime", condition="true"} == 0
      for: 30s
      labels:
        severity: warning
        healing_action: restart_pod
      annotations:
        summary: "Pod {{ $labels.pod }} is not ready"
    
    - alert: DeploymentReplicasMismatch
      expr: |
        kube_deployment_spec_replicas{namespace=~"netflix|prime"} 
        != kube_deployment_status_available_replicas{namespace=~"netflix|prime"}
      for: 1m
      labels:
        severity: warning
        healing_action: scale_up
      annotations:
        summary: "Deployment {{ $labels.deployment }} has fewer replicas than desired"
  
  - name: sentinels.errors
    interval: 15s
    rules:
    - alert: HighErrorRate
      expr: |
        (sum(rate(http_requests_total{namespace=~"netflix|prime", status_code=~"5.."}[2m]))
         by (namespace, service)) /
        (sum(rate(http_requests_total{namespace=~"netflix|prime"}[2m]))
         by (namespace, service)) > 0.10
      for: 1m
      labels:
        severity: warning
        healing_action: restart_pod
      annotations:
        summary: "High error rate on {{ $labels.service }}"
```

#### 5.4 Grafana Dashboards

Three dashboards are pre-configured as Grafana Dashboard JSONs stored in `monitoring/grafana/dashboards/`:

**Dashboard 1: Netflix RED Dashboard** (`netflix-red.json`)
- Row 1: Request Rate per service (requests/sec)
- Row 2: Error Rate per service (% of 5xx)
- Row 3: Request Latency (p50, p95, p99 per service)
- Row 4: Pod Status Timeline (healthy/degraded/down)

**Dashboard 2: SENTINELS Healer Performance** (`sentinels-healer.json`)
- Row 1: MTTD gauge, MTTR gauge, Success Rate stat, Availability stat
- Row 2: Healing Actions Over Time (timeline panel, color-coded by action type)
- Row 3: Anomaly Score Distribution (histogram)
- Row 4: Circuit Breaker State Timeline
- Row 5: Recent Healing Events Table (last 50 events from PostgreSQL)

**Dashboard 3: Infrastructure USE** (`infrastructure-use.json`)
- CPU Utilization, Memory Utilization, Disk I/O, Network for all nodes

#### Phase 5 Chaos Checklist
- [ ] http://localhost:9090 — Prometheus UI shows all targets as UP
- [ ] http://localhost:9090/alerts — All alert rules listed
- [ ] http://localhost:3003 — Grafana loads with all 3 dashboards
- [ ] Search Service receives CPU stress manually → `HighCPUUsage` fires in AlertManager within 90s
- [ ] AlertManager routes alert to healer webhook endpoint (check healer logs)
- [ ] `kubectl get servicemonitors -n monitoring` — All service monitors listed
- [ ] Prometheus shows metrics from all Netflix microservices and PrimeOS

---

### PHASE 6: ML Anomaly Detection Pipeline
**Duration:** 4-5 days  
**Deliverable:** Isolation Forest model trained on baseline metrics, anomaly scoring pipeline

#### 6.1 Isolation Forest Implementation

The ML pipeline lives in `sentinels/healer-agent/ml/`:

```python
# sentinels/healer-agent/ml/feature_engineering.py

from dataclasses import dataclass
from typing import List, Dict
import numpy as np
import pandas as pd
from prometheus_client import start_http_server
import httpx

@dataclass
class MetricSnapshot:
    """Structured representation of a pod's metric state"""
    pod: str
    namespace: str
    timestamp: float
    cpu_percent: float
    memory_percent: float
    restart_count: int
    request_rate: float     # requests/sec from http_requests_total
    error_rate: float       # % 5xx responses
    latency_p95: float      # 95th percentile latency in seconds

class FeatureEngineer:
    """
    Transforms raw Prometheus metrics into ML-ready feature vectors.
    
    Feature engineering is the most critical part of anomaly detection quality.
    Bad features = bad detection, regardless of algorithm choice.
    """
    
    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.history: Dict[str, List[MetricSnapshot]] = {}  # pod -> history
    
    def add_snapshot(self, snapshot: MetricSnapshot):
        """Add a new metric snapshot to the pod's history"""
        if snapshot.pod not in self.history:
            self.history[snapshot.pod] = []
        self.history[snapshot.pod].append(snapshot)
        # Keep only last 60 minutes of data
        cutoff = snapshot.timestamp - 3600
        self.history[snapshot.pod] = [
            s for s in self.history[snapshot.pod] 
            if s.timestamp > cutoff
        ]
    
    def compute_features(self, pod: str) -> np.ndarray | None:
        """
        Compute feature vector for a pod from its recent history.
        Returns None if insufficient history (<12 data points = <3 minutes)
        
        Feature vector (20 dimensions):
        [0]  cpu_mean_5m          - Rolling mean CPU (5min window)
        [1]  cpu_std_5m           - Rolling std CPU  
        [2]  cpu_max_5m           - Rolling max CPU
        [3]  cpu_rate_of_change   - (current - 5min_ago) / 5min_ago
        [4]  cpu_zscore           - Z-score vs 1hr baseline
        [5]  memory_mean_5m       
        [6]  memory_std_5m
        [7]  memory_rate_of_change
        [8]  memory_zscore
        [9]  error_rate_mean_5m
        [10] error_rate_max_5m
        [11] latency_p95_mean_5m
        [12] latency_p95_max_5m
        [13] restart_count_delta  - Restarts in last 5min
        [14] request_rate_mean_5m
        [15] request_rate_cv      - Coefficient of variation (std/mean)
        [16] hour_sin             - Cyclical encoding: sin(2π * hour/24)
        [17] hour_cos             - Cyclical encoding: cos(2π * hour/24)
        [18] cpu_lag_15m          - CPU mean 15 minutes ago (trend feature)
        [19] memory_lag_15m       - Memory mean 15 minutes ago
        """
        history = self.history.get(pod, [])
        if len(history) < 12:  # Need at least 3 minutes of data
            return None
        
        now = history[-1].timestamp
        recent = [s for s in history if s.timestamp > now - 300]    # last 5min
        lag_15m = [s for s in history if now - 900 < s.timestamp < now - 600]
        hour_of_day = pd.Timestamp(now, unit='s').hour
        
        cpu_values = [s.cpu_percent for s in recent]
        mem_values = [s.memory_percent for s in recent]
        err_values = [s.error_rate for s in recent]
        lat_values = [s.latency_p95 for s in recent]
        
        # CPU Z-score baseline (last 1 hour)
        all_cpu = [s.cpu_percent for s in history]
        cpu_baseline_mean = np.mean(all_cpu)
        cpu_baseline_std = np.std(all_cpu) or 1.0  # Avoid division by zero
        cpu_zscore = (np.mean(cpu_values) - cpu_baseline_mean) / cpu_baseline_std
        
        # Memory Z-score
        all_mem = [s.memory_percent for s in history]
        mem_baseline_mean = np.mean(all_mem)
        mem_baseline_std = np.std(all_mem) or 1.0
        mem_zscore = (np.mean(mem_values) - mem_baseline_mean) / mem_baseline_std
        
        # Rate of change (delta from 5 min ago)
        if len(recent) >= 2:
            cpu_roc = (recent[-1].cpu_percent - recent[0].cpu_percent) / max(recent[0].cpu_percent, 0.01)
            mem_roc = (recent[-1].memory_percent - recent[0].memory_percent) / max(recent[0].memory_percent, 0.01)
        else:
            cpu_roc = 0.0
            mem_roc = 0.0
        
        lag_cpu = np.mean([s.cpu_percent for s in lag_15m]) if lag_15m else np.mean(cpu_values)
        lag_mem = np.mean([s.memory_percent for s in lag_15m]) if lag_15m else np.mean(mem_values)
        
        request_mean = np.mean([s.request_rate for s in recent])
        request_std = np.std([s.request_rate for s in recent])
        request_cv = request_std / request_mean if request_mean > 0 else 0.0
        
        restart_delta = history[-1].restart_count - (history[-12].restart_count if len(history) >= 12 else 0)
        
        return np.array([
            np.mean(cpu_values),        # [0]
            np.std(cpu_values),         # [1]
            np.max(cpu_values),         # [2]
            cpu_roc,                    # [3]
            cpu_zscore,                 # [4]
            np.mean(mem_values),        # [5]
            np.std(mem_values),         # [6]
            mem_roc,                    # [7]
            mem_zscore,                 # [8]
            np.mean(err_values),        # [9]
            np.max(err_values),         # [10]
            np.mean(lat_values),        # [11]
            np.max(lat_values),         # [12]
            float(restart_delta),       # [13]
            request_mean,               # [14]
            request_cv,                 # [15]
            np.sin(2 * np.pi * hour_of_day / 24),  # [16]
            np.cos(2 * np.pi * hour_of_day / 24),  # [17]
            lag_cpu,                    # [18]
            lag_mem,                    # [19]
        ])
```

```python
# sentinels/healer-agent/ml/anomaly_detector.py

import numpy as np
import pickle
import logging
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    Isolation Forest-based anomaly detector for Kubernetes pod metrics.
    
    Critical design decisions:
    - contamination=0.02: Assumes 2% of observations are anomalous
      (appropriate for infrastructure: roughly 30min of abnormal behavior per day)
    - n_estimators=200: Balance between accuracy and speed (200 trees)
    - max_samples=256: Subsample size per tree (speed optimization)
    - random_state=42: Fixed seed for reproducible demo results
    """
    
    MODEL_PATH = Path("/tmp/sentinels_model.pkl")
    SCALER_PATH = Path("/tmp/sentinels_scaler.pkl")
    
    # Anomaly score threshold: scores below this are classified as anomalies
    # Isolation Forest returns scores in range [-1, 0], where more negative = more anomalous
    # -0.1 threshold: catches significant anomalies while avoiding false positives
    ANOMALY_THRESHOLD = -0.10
    
    # Severity thresholds based on anomaly score
    SEVERITY_THRESHOLDS = {
        "CRITICAL": -0.35,  # Very anomalous
        "WARNING":  -0.20,  # Moderately anomalous
        "MINOR":    -0.10,  # Slightly anomalous
    }
    
    def __init__(self):
        self.model: IsolationForest | None = None
        self.scaler: StandardScaler = StandardScaler()
        self.training_data: list[np.ndarray] = []
        self.is_trained = False
        self.training_samples_required = 60  # Need 60 samples (~15min baseline)
        self.last_retrain: datetime | None = None
    
    def add_training_sample(self, features: np.ndarray):
        """Add a feature vector to the training buffer"""
        self.training_data.append(features)
        
        # Auto-train when we have enough baseline data
        if len(self.training_data) >= self.training_samples_required and not self.is_trained:
            self.train()
        
        # Periodic retraining every 30 minutes
        if (self.is_trained and self.last_retrain and 
            (datetime.utcnow() - self.last_retrain).seconds > 1800):
            self.retrain_incremental()
    
    def train(self):
        """Initial training on baseline data"""
        X = np.array(self.training_data)
        
        # Normalize features to zero mean, unit variance
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            n_estimators=200,
            contamination=0.02,     # 2% expected anomaly rate
            max_samples=256,        # Fast subsampling
            random_state=42,        # Reproducibility
            n_jobs=-1,              # Use all CPU cores
            warm_start=False        # Full training initially
        )
        self.model.fit(X_scaled)
        self.is_trained = True
        self.last_retrain = datetime.utcnow()
        
        # Save model to disk for persistence
        with open(self.MODEL_PATH, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.SCALER_PATH, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        logger.info(f"Isolation Forest trained on {len(X)} samples. "
                   f"Estimated contamination: {self.model.contamination}")
    
    def retrain_incremental(self):
        """
        Incremental retraining for concept drift adaptation.
        Uses warm_start=True to add trees without discarding existing ones.
        Keeps only last 2 hours of training data to adapt to drift.
        """
        # Keep only recent data (concept drift: recent patterns matter more)
        recent_data = self.training_data[-480:]  # ~2 hours at 15s intervals
        X = np.array(recent_data)
        X_scaled = self.scaler.transform(X)  # Use existing scaler
        
        # Incremental: add 50 new trees to existing model
        self.model.set_params(
            n_estimators=self.model.n_estimators + 50,
            warm_start=True
        )
        self.model.fit(X_scaled)
        self.last_retrain = datetime.utcnow()
        logger.info(f"Incremental retrain complete. Trees: {self.model.n_estimators}")
    
    def score(self, features: np.ndarray) -> dict:
        """
        Score a feature vector. Returns anomaly assessment.
        
        Returns:
            {
                'is_anomaly': bool,
                'anomaly_score': float (more negative = more anomalous),
                'severity': 'CRITICAL' | 'WARNING' | 'MINOR' | 'NORMAL',
                'confidence': float (0-1, how confident we are),
                'model_ready': bool
            }
        """
        if not self.is_trained:
            return {
                'is_anomaly': False, 
                'anomaly_score': 0.0,
                'severity': 'NORMAL',
                'confidence': 0.0,
                'model_ready': False
            }
        
        X = features.reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # decision_function returns anomaly score (negative = anomalous)
        score = float(self.model.decision_function(X_scaled)[0])
        
        # Determine severity
        severity = 'NORMAL'
        for level, threshold in self.SEVERITY_THRESHOLDS.items():
            if score <= threshold:
                severity = level
                break
        
        # Confidence based on distance from threshold
        confidence = min(abs(score - self.ANOMALY_THRESHOLD) / 0.3, 1.0)
        
        return {
            'is_anomaly': score <= self.ANOMALY_THRESHOLD,
            'anomaly_score': score,
            'severity': severity,
            'confidence': confidence,
            'model_ready': True
        }
```

#### 6.2 Prometheus Query Service (metrics collection)

```python
# sentinels/healer-agent/ml/prometheus_collector.py

import httpx
import asyncio
from typing import Optional

PROMETHEUS_URL = "http://kube-prometheus-stack-prometheus.monitoring.svc:9090"

async def query_prometheus(query: str) -> Optional[float]:
    """Execute a PromQL query and return the scalar result"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query}
        )
        data = response.json()
        if data["status"] == "success" and data["data"]["result"]:
            return float(data["data"]["result"][0]["value"][1])
    return None

async def collect_pod_metrics(pod: str, namespace: str) -> Optional[MetricSnapshot]:
    """
    Collect current metrics for a specific pod from Prometheus.
    All queries use the pod label for exact pod targeting.
    """
    cpu_pct = await query_prometheus(
        f'sum(rate(container_cpu_usage_seconds_total{{pod="{pod}", namespace="{namespace}", container!=""}}[2m])) '
        f'/ sum(kube_pod_container_resource_limits{{pod="{pod}", namespace="{namespace}", resource="cpu"}})'
    )
    
    memory_pct = await query_prometheus(
        f'sum(container_memory_working_set_bytes{{pod="{pod}", namespace="{namespace}", container!=""}}) '
        f'/ sum(kube_pod_container_resource_limits{{pod="{pod}", namespace="{namespace}", resource="memory"}})'
    )
    
    error_rate = await query_prometheus(
        f'sum(rate(http_requests_total{{pod="{pod}", status_code=~"5.."}}[2m])) '
        f'/ sum(rate(http_requests_total{{pod="{pod}"}}[2m]))'
    )
    
    restart_count = await query_prometheus(
        f'sum(kube_pod_container_status_restarts_total{{pod="{pod}", namespace="{namespace}"}})'
    )
    
    return MetricSnapshot(
        pod=pod,
        namespace=namespace,
        timestamp=asyncio.get_event_loop().time(),
        cpu_percent=cpu_pct or 0.0,
        memory_percent=memory_pct or 0.0,
        restart_count=int(restart_count or 0),
        request_rate=0.0,  # Populated separately
        error_rate=error_rate or 0.0,
        latency_p95=0.0    # Populated separately
    )
```

#### Phase 6 Chaos Checklist
- [ ] Inject CPU stress on search-service → `detector.score(features)` returns anomaly_score < -0.30
- [ ] Baseline period (no attacks): All scores return NORMAL (> -0.10)
- [ ] Memory stress → anomaly detected within 2 scoring cycles (30s)
- [ ] After chaos stops → anomaly score returns to NORMAL within 3 cycles (45s)
- [ ] Model saves to disk: `/tmp/sentinels_model.pkl` exists after 15 minutes
- [ ] Incremental retrain runs without errors after 30 minutes of operation

---

### PHASE 7: Policy Engine — OPA/Rego Decision System
**Duration:** 3-4 days  
**Deliverable:** OPA server running with Rego policies, all healing decisions fully explainable

#### 7.1 OPA Policy Structure

```
sentinels/opa-policies/
├── healing_policy.rego      # Main healing decision logic
├── safety_policy.rego       # Safety checks (circuit breaker, PDB, cooldown)
└── data/
    ├── action_catalog.json  # Available actions and their risk levels
    └── thresholds.json      # Configurable thresholds
```

#### 7.2 Main Healing Policy (healing_policy.rego)

```rego
# sentinels/opa-policies/healing_policy.rego

package sentinels.healing

import future.keywords.if
import future.keywords.in

# Default: escalate to human if no rule matches
# This is the SAFETY DEFAULT — unknown situations go to humans, never auto-remediated
default action := {"type": "alert_human", "reason": "no_matching_policy", "tier": 2}

# ────────────────────────────────────────────
# RULE 1: High CPU — Restart Pod
# Condition: CPU > 80%, anomaly confirmed by ML, severity CRITICAL or WARNING
# Action: Restart the specific pod (Tier 1 — automatic)
# ────────────────────────────────────────────
action := {
    "type": "restart_pod",
    "target": input.pod,
    "namespace": input.namespace,
    "reason": sprintf("CPU anomaly (score: %.2f) exceeds threshold. CPU: %.1f%%. Policy: HIGH_CPU_RESTART", 
                     [input.anomaly_score, input.cpu_percent]),
    "tier": 1,
    "policy_id": "HIGH_CPU_001",
    "policy_version": "1.0.0"
} if {
    input.anomaly_type == "high_cpu"
    input.anomaly_score <= -0.20
    input.cpu_percent >= 80
    input.severity in {"CRITICAL", "WARNING"}
    not input.pod == ""          # Pod must be identified
}

# ────────────────────────────────────────────
# RULE 2: Memory Pressure — Restart Pod  
# Condition: Memory > 85%, anomaly confirmed
# ────────────────────────────────────────────
action := {
    "type": "restart_pod",
    "target": input.pod,
    "namespace": input.namespace,
    "reason": sprintf("Memory anomaly (score: %.2f). Memory: %.1f%%. Policy: HIGH_MEM_RESTART", 
                     [input.anomaly_score, input.memory_percent]),
    "tier": 1,
    "policy_id": "HIGH_MEM_001",
    "policy_version": "1.0.0"
} if {
    input.anomaly_type in {"high_memory", "memory_leak"}
    input.anomaly_score <= -0.20
    input.memory_percent >= 85
}

# ────────────────────────────────────────────
# RULE 3: Crash Loop — Force Redeploy
# Condition: Pod has restarted >3 times in 5 minutes
# Action: Delete pod (Kubernetes recreates from ReplicaSet definition)
# ────────────────────────────────────────────
action := {
    "type": "force_redeploy",
    "target": input.pod,
    "namespace": input.namespace,
    "reason": sprintf("CrashLoopBackOff detected. %d restarts in last 5 minutes. Policy: CRASH_LOOP_REDEPLOY", 
                     [input.restart_count_delta]),
    "tier": 1,
    "policy_id": "CRASH_LOOP_001",
    "policy_version": "1.0.0"
} if {
    input.anomaly_type == "crash_loop"
    input.restart_count_delta >= 3
}

# ────────────────────────────────────────────
# RULE 4: Deployment Missing Replicas — Scale Up
# Condition: Available replicas < desired replicas
# Action: Patch deployment to restore desired replica count
# ────────────────────────────────────────────
action := {
    "type": "scale_to_desired",
    "target": input.deployment,
    "namespace": input.namespace,
    "desired_replicas": input.desired_replicas,
    "reason": sprintf("Deployment %s has %d/%d replicas. Policy: REPLICA_RESTORE",
                     [input.deployment, input.available_replicas, input.desired_replicas]),
    "tier": 1,
    "policy_id": "REPLICA_001",
    "policy_version": "1.0.0"
} if {
    input.anomaly_type == "replica_mismatch"
    input.available_replicas < input.desired_replicas
    input.desired_replicas > 0
}

# ────────────────────────────────────────────
# RULE 5: High Error Rate — Rollback (Tier 2 — Approval)
# Condition: Error rate >20% AND anomaly score very low
# Action: Rollback to previous deployment revision
# Note: This is Tier 2 — requires human approval or 30s timeout auto-approval
# ────────────────────────────────────────────
action := {
    "type": "rollback",
    "target": input.deployment,
    "namespace": input.namespace,
    "reason": sprintf("Error rate %.1f%% exceeds 20%% threshold. Anomaly score: %.2f. Policy: HIGH_ERROR_ROLLBACK",
                     [input.error_rate * 100, input.anomaly_score]),
    "tier": 2,                   # REQUIRES APPROVAL
    "policy_id": "HIGH_ERR_001",
    "policy_version": "1.0.0",
    "approval_timeout_seconds": 300  # Auto-approve after 5 minutes if no response
} if {
    input.anomaly_type == "high_error_rate"
    input.anomaly_score <= -0.35
    input.error_rate >= 0.20
    input.severity == "CRITICAL"
}
```

```rego
# sentinels/opa-policies/safety_policy.rego

package sentinels.safety

import future.keywords.if

# Safety check: ALL must pass before executing ANY healing action
# Returns deny reasons if any check fails

# Check 1: Circuit breaker
deny["circuit_breaker_open"] if {
    input.circuit_breaker_state == "open"
}

# Check 2: Cooldown period  
deny["cooldown_active"] if {
    input.seconds_since_last_action < 300  # 5 minute minimum between actions on same pod
}

# Check 3: Blast radius — never heal if too few healthy pods
deny["blast_radius_exceeded"] if {
    # For microservices: ensure >50% of all Netflix or Prime pods remain healthy
    input.healthy_pod_count < (input.total_pod_count * 0.5)
}

# Check 4: PDB (Pod Disruption Budget) check
deny["pdb_violation"] if {
    input.pdb_disruptions_allowed == 0  # PDB says no pods can be disrupted right now
}

# Check 5: SENTINELS cannot heal its own namespace
deny["protected_namespace"] if {
    input.namespace == "sentinels-system"
}

# Check 6: Cannot heal monitoring namespace
deny["monitoring_protected"] if {
    input.namespace == "monitoring"
}

# Aggregate: is this action safe?
safe if {
    count(deny) == 0
}

# Generate human-readable safety report
safety_report := {
    "safe": safe,
    "denied_reasons": deny,
    "checks_performed": [
        "circuit_breaker", "cooldown", "blast_radius", 
        "pdb", "namespace_protection"
    ]
}
```

#### Phase 7 Chaos Checklist
- [ ] OPA server running: `curl http://localhost:8181/health` returns 200
- [ ] Policy test: send high_cpu input → returns restart_pod action
- [ ] Safety check: circuit breaker open → returns deny["circuit_breaker_open"]
- [ ] All 5 policy rules tested with positive and negative inputs
- [ ] Policy version tracked: changing Rego file and reloading OPA updates version
- [ ] Audit log shows policy_id and policy_version for every decision

---

### PHASE 8: Kopf Operator — Healing Executor
**Duration:** 4-5 days  
**Deliverable:** Full SENTINELS healer running end-to-end: receive alert → ML score → OPA decide → execute → verify → broadcast

#### 8.1 Healer Agent Main Application

```python
# sentinels/healer-agent/main.py — COMPLETE HEALER AGENT

import asyncio
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import socketio
from kubernetes import client as k8s_client, config as k8s_config
import kopf

from ml.anomaly_detector import AnomalyDetector
from ml.feature_engineering import FeatureEngineer
from ml.prometheus_collector import collect_pod_metrics
from policy.opa_client import query_opa
from safety.circuit_breaker import CircuitBreaker
from safety.cooldown_manager import CooldownManager
from models.database import init_db, save_healing_event
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# ── Initialize FastAPI app ──────────────────────────────────────────────────
app = FastAPI(title="SENTINELS Healer Agent", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# ── Initialize Socket.IO ────────────────────────────────────────────────────
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*',
                            message_queue='redis://redis.sentinels-system.svc:6379')
socket_app = socketio.ASGIApp(sio, app)

# ── Initialize ML components ────────────────────────────────────────────────
detector = AnomalyDetector()
engineer = FeatureEngineer()

# ── Initialize Safety components ────────────────────────────────────────────
circuit_breaker = CircuitBreaker(redis_url="redis://redis.sentinels-system.svc:6379")
cooldown_mgr = CooldownManager(redis_url="redis://redis.sentinels-system.svc:6379")

# ── Prometheus metrics exposed by the healer itself ────────────────────────
HEALING_ACTIONS = Counter('healing_actions_total', 
    'Total healing actions', ['action', 'namespace', 'severity', 'result'])
ANOMALY_SCORE = Gauge('healing_anomaly_score', 
    'Current anomaly score per pod', ['pod', 'namespace'])
ACTION_DURATION = Histogram('healing_action_duration_seconds', 
    'Time to execute healing action', ['action'])
FALSE_POSITIVES = Counter('healing_false_positives_total', 
    'Actions where metrics normalized without intervention')

# ── AlertManager Webhook Endpoint ──────────────────────────────────────────
@app.post("/alerts")
async def receive_alerts(request: Request):
    """
    Receives AlertManager webhook payloads.
    This is the primary entry point for the healing loop.
    AlertManager sends: {"version": "4", "alerts": [{...}], "commonLabels": {...}}
    """
    payload = await request.json()
    
    for alert in payload.get("alerts", []):
        if alert.get("status") == "firing":
            asyncio.create_task(process_alert(alert))
    
    return {"status": "received", "alert_count": len(payload.get("alerts", []))}

async def process_alert(alert: dict):
    """
    Full healing pipeline for a single alert.
    This is the core of SENTINELS — the complete MAPE-K loop.
    """
    correlation_id = f"heal-{alert['labels'].get('pod', 'unknown')}-{int(asyncio.get_event_loop().time())}"
    
    logger.info(f"[{correlation_id}] Processing alert: {alert['labels'].get('alertname')}")
    
    # ── STEP 1: MONITOR — Extract context from alert ──────────────────────
    pod = alert["labels"].get("pod", "")
    namespace = alert["labels"].get("namespace", "")
    alertname = alert["labels"].get("alertname", "")
    severity = alert["labels"].get("severity", "warning").upper()
    
    # Map AlertManager alert names to anomaly types
    anomaly_type_map = {
        "HighCPUUsage": "high_cpu",
        "HighMemoryUsage": "high_memory",
        "PodCrashLooping": "crash_loop",
        "PodNotReady": "pod_unavailable",
        "DeploymentReplicasMismatch": "replica_mismatch",
        "HighErrorRate": "high_error_rate"
    }
    anomaly_type = anomaly_type_map.get(alertname, "unknown")
    
    if not pod or not namespace:
        logger.warning(f"[{correlation_id}] Alert missing pod/namespace context, skipping")
        return
    
    # ── STEP 2: ANALYZE — Collect metrics and score with Isolation Forest ─
    snapshot = await collect_pod_metrics(pod, namespace)
    if snapshot:
        engineer.add_snapshot(snapshot)
        features = engineer.compute_features(pod)
        
        if features is not None:
            ml_result = detector.score(features)
            anomaly_score = ml_result['anomaly_score']
            ANOMALY_SCORE.labels(pod=pod, namespace=namespace).set(anomaly_score)
        else:
            # Insufficient history — trust AlertManager's assessment
            anomaly_score = -0.30
            ml_result = {'anomaly_score': anomaly_score, 'severity': severity, 
                        'model_ready': False}
        
        # Add training sample for model improvement
        if features is not None:
            detector.add_training_sample(features)
    else:
        anomaly_score = -0.30  # Default for missing metrics
        ml_result = {'anomaly_score': anomaly_score, 'model_ready': False}
    
    # Broadcast anomaly detection event to dashboard immediately
    await sio.emit('anomaly_detected', {
        'correlation_id': correlation_id,
        'pod': pod,
        'namespace': namespace,
        'anomaly_type': anomaly_type,
        'anomaly_score': anomaly_score,
        'severity': severity,
        'timestamp': asyncio.get_event_loop().time()
    })
    
    # ── STEP 3: PLAN — Query OPA for healing decision ─────────────────────
    opa_input = {
        "pod": pod,
        "namespace": namespace,
        "anomaly_type": anomaly_type,
        "anomaly_score": anomaly_score,
        "severity": severity,
        "cpu_percent": snapshot.cpu_percent if snapshot else 0.0,
        "memory_percent": snapshot.memory_percent if snapshot else 0.0,
        "error_rate": snapshot.error_rate if snapshot else 0.0,
        "restart_count_delta": 0,  # Populated from Prometheus for crash loop alerts
        "deployment": alertname,   # Simplified: map alert to deployment name
        "available_replicas": 0,   # Populated for replica mismatch alerts
        "desired_replicas": 0
    }
    
    decision = await query_opa("/v1/data/sentinels/healing/action", opa_input)
    
    if not decision:
        logger.error(f"[{correlation_id}] OPA query failed, defaulting to alert_human")
        decision = {"type": "alert_human", "reason": "opa_unavailable", "tier": 2}
    
    logger.info(f"[{correlation_id}] OPA decision: {decision['type']} (Tier {decision.get('tier', 1)})")
    
    # ── STEP 4a: SAFETY CHECK — Run safety policy ─────────────────────────
    # Collect safety context
    all_pods = await get_namespace_pod_health(namespace)
    healthy_count = sum(1 for p in all_pods if p['status'] == 'Running')
    total_count = len(all_pods)
    pdb_allowed = await check_pdb_disruptions(pod, namespace)
    
    safety_input = {
        "namespace": namespace,
        "pod": pod,
        "circuit_breaker_state": circuit_breaker.get_state(namespace),
        "seconds_since_last_action": cooldown_mgr.seconds_since_last(pod),
        "healthy_pod_count": healthy_count,
        "total_pod_count": total_count,
        "pdb_disruptions_allowed": pdb_allowed
    }
    
    safety_result = await query_opa("/v1/data/sentinels/safety/safety_report", safety_input)
    
    if not safety_result or not safety_result.get('safe', False):
        denied_reasons = safety_result.get('denied_reasons', ['unknown']) if safety_result else ['opa_error']
        logger.warning(f"[{correlation_id}] Safety check FAILED: {denied_reasons}")
        
        await sio.emit('healing_blocked', {
            'correlation_id': correlation_id,
            'pod': pod,
            'decision': decision,
            'blocked_reasons': list(denied_reasons),
            'timestamp': asyncio.get_event_loop().time()
        })
        return
    
    # ── STEP 4b: TIER 2 CHECK — Does this need human approval? ───────────
    if decision.get('tier', 1) == 2:
        # For demo: auto-approve Tier 2 after 30 seconds
        # In production: send Slack notification and wait for webhook response
        logger.info(f"[{correlation_id}] Tier 2 action — auto-approving after 30s delay")
        await asyncio.sleep(30)  # Simulated approval wait
    
    # ── STEP 5: EXECUTE — Perform the healing action ──────────────────────
    action_start = asyncio.get_event_loop().time()
    
    await sio.emit('healing_started', {
        'correlation_id': correlation_id,
        'pod': pod,
        'namespace': namespace,
        'action': decision['type'],
        'reason': decision.get('reason', ''),
        'policy_id': decision.get('policy_id', ''),
        'timestamp': action_start
    })
    
    execution_result = await execute_healing_action(decision, pod, namespace, correlation_id)
    
    action_duration = asyncio.get_event_loop().time() - action_start
    ACTION_DURATION.labels(action=decision['type']).observe(action_duration)
    
    # ── STEP 6: VERIFY — Confirm recovery ────────────────────────────────
    if execution_result['success']:
        recovery_confirmed = await verify_recovery(pod, namespace, anomaly_type)
        
        # Update circuit breaker
        if recovery_confirmed:
            circuit_breaker.record_success(namespace)
        else:
            circuit_breaker.record_failure(namespace)
    else:
        recovery_confirmed = False
        circuit_breaker.record_failure(namespace)
    
    # ── STEP 7: RECORD — Persist to PostgreSQL ────────────────────────────
    healing_record = {
        'correlation_id': correlation_id,
        'alert_name': alertname,
        'pod': pod,
        'namespace': namespace,
        'anomaly_type': anomaly_type,
        'anomaly_score': anomaly_score,
        'severity': severity,
        'policy_id': decision.get('policy_id', 'UNKNOWN'),
        'action': decision['type'],
        'result': 'SUCCESS' if execution_result['success'] else 'FAILED',
        'recovery_confirmed': recovery_confirmed,
        'action_duration_ms': int(action_duration * 1000),
        'detection_time': asyncio.get_event_loop().time() - float(alert.get('startsAt', 0) or 0),
    }
    await save_healing_event(healing_record)
    
    # Update Prometheus metrics
    HEALING_ACTIONS.labels(
        action=decision['type'],
        namespace=namespace,
        severity=severity,
        result='success' if execution_result['success'] else 'failed'
    ).inc()
    
    # ── STEP 8: BROADCAST — Send to dashboard ─────────────────────────────
    await sio.emit('healing_complete', {
        **healing_record,
        'execution_details': execution_result,
        'recovery_confirmed': recovery_confirmed,
        'total_duration_ms': int(action_duration * 1000)
    })
    
    logger.info(f"[{correlation_id}] Healing complete: {decision['type']} → "
               f"{'✅ SUCCESS' if execution_result['success'] else '❌ FAILED'} "
               f"({int(action_duration * 1000)}ms)")

async def execute_healing_action(decision: dict, pod: str, namespace: str, correlation_id: str) -> dict:
    """Execute the healing action via Kubernetes API"""
    
    # Load Kubernetes config (in-cluster when running in K8s)
    try:
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        k8s_config.load_kube_config()  # Fallback for local development
    
    v1 = k8s_client.CoreV1Api()
    apps_v1 = k8s_client.AppsV1Api()
    
    action_type = decision['type']
    
    # Record cooldown timer
    cooldown_mgr.record_action(pod)
    
    try:
        if action_type == "restart_pod":
            # Delete pod — ReplicaSet automatically creates a replacement
            v1.delete_namespaced_pod(name=pod, namespace=namespace)
            return {"success": True, "action": "pod_deleted", 
                   "message": f"Pod {pod} deleted, ReplicaSet will recreate"}
        
        elif action_type == "force_redeploy":
            # Patch deployment with a restart annotation (rolling restart)
            patch = {"spec": {"template": {"metadata": {
                "annotations": {"kubectl.kubernetes.io/restartedAt": 
                               str(asyncio.get_event_loop().time())}
            }}}}
            deployment_name = pod.rsplit('-', 2)[0]  # Extract deployment name from pod name
            apps_v1.patch_namespaced_deployment(
                name=deployment_name, namespace=namespace, body=patch)
            return {"success": True, "action": "deployment_restarted"}
        
        elif action_type == "scale_to_desired":
            # Patch deployment replica count
            patch = {"spec": {"replicas": decision['desired_replicas']}}
            apps_v1.patch_namespaced_deployment(
                name=decision['target'], namespace=namespace, body=patch)
            return {"success": True, "action": "scaled", 
                   "replicas": decision['desired_replicas']}
        
        elif action_type == "rollback":
            # Execute kubectl rollout undo equivalent
            # Note: Requires RBAC permission on deployments/rollback
            import subprocess
            result = subprocess.run(
                ["kubectl", "rollout", "undo", f"deployment/{decision['target']}", 
                 "-n", namespace],
                capture_output=True, text=True, timeout=30
            )
            return {"success": result.returncode == 0, 
                   "action": "rollback",
                   "output": result.stdout}
        
        elif action_type == "alert_human":
            # Log for human attention — no automated action
            logger.warning(f"[{correlation_id}] Human attention required: {decision.get('reason')}")
            return {"success": True, "action": "human_alerted",
                   "message": "Incident logged for human review"}
        
        else:
            return {"success": False, "action": action_type, 
                   "message": f"Unknown action type: {action_type}"}
    
    except Exception as e:
        logger.error(f"[{correlation_id}] Action execution failed: {e}")
        return {"success": False, "action": action_type, "error": str(e)}

async def verify_recovery(pod: str, namespace: str, anomaly_type: str) -> bool:
    """
    Verify that the healing action actually resolved the anomaly.
    Polls pod status for up to 60 seconds.
    """
    v1 = k8s_client.CoreV1Api()
    
    for attempt in range(20):  # 20 attempts × 3s = 60s maximum wait
        await asyncio.sleep(3)
        try:
            pod_list = v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={pod.rsplit('-', 2)[0]}"
            )
            for p in pod_list.items:
                if p.status.phase == "Running":
                    # Check readiness
                    for condition in (p.status.conditions or []):
                        if condition.type == "Ready" and condition.status == "True":
                            logger.info(f"Recovery verified for {pod} after {(attempt+1)*3}s")
                            return True
        except Exception:
            pass
    
    logger.warning(f"Recovery verification failed for {pod} after 60s")
    return False
```

#### Phase 8 Chaos Checklist
- [ ] Start healer agent: no errors in startup logs
- [ ] Inject CPU stress on search-service → healer receives AlertManager webhook within 90s
- [ ] Healer logs show all 8 steps: receive → features → ML score → OPA → safety → execute → verify → broadcast
- [ ] Dashboard receives Socket.IO events: anomaly_detected, healing_started, healing_complete
- [ ] Healing audit record appears in PostgreSQL: `SELECT * FROM healing_audit_log ORDER BY created_at DESC LIMIT 1`
- [ ] Circuit breaker: trigger 5 consecutive failed healings → state changes to OPEN → subsequent alerts blocked
- [ ] Circuit breaker half-open: after 300s cooldown, one test action allowed
- [ ] Cooldown: second attack on same pod within 5min → blocked by cooldown
- [ ] Blast radius: kill 6/8 Netflix pods simultaneously → further healing blocked
- [ ] Full end-to-end: attack → detect → heal → verify → dashboard shows SUCCESS

---

## BLOCK 3 — COMMAND DASHBOARD & VALIDATION
### Phases 9 through 12 | Estimated: 2-3 weeks

---

### PHASE 9: SENTINELS Command Center — 3D Dashboard
**Duration:** 5-7 days  
**Deliverable:** Fully functional React dashboard with 3D topology graph, attack launcher, healing log, metrics scorecard

#### 9.1 Dashboard Tech Stack and Dependencies

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "typescript": "^5.4.0",
    "@react-three/fiber": "^8.16.0",
    "@react-three/drei": "^9.109.0",
    "@react-three/postprocessing": "^2.16.0",
    "three": "^0.166.0",
    "react-force-graph-3d": "^1.24.0",
    "socket.io-client": "^4.7.0",
    "tailwindcss": "^3.4.0",
    "framer-motion": "^11.2.0",
    "recharts": "^2.12.0",
    "@tanstack/react-query": "^5.45.0",
    "zustand": "^4.5.0",
    "date-fns": "^3.6.0",
    "lucide-react": "^0.400.0"
  }
}
```

#### 9.2 Dashboard Backend API Endpoints

The dashboard backend (`dashboard/backend/main.py`) exposes:

```
GET  /api/topology         → Current pod graph (nodes + edges + active events)
GET  /api/pods             → All pods with their current status
POST /api/attacks/launch   → Launch a Chaos Mesh experiment
DELETE /api/attacks/{id}   → Stop a specific attack
GET  /api/attacks/active   → Currently active chaos experiments
POST /api/attacks/stop-all → Emergency stop — delete all chaos CRDs
GET  /api/metrics          → Current F1, MTTD, MTTR, FPR scores
GET  /api/healing/history  → Last 100 healing events from PostgreSQL
WebSocket → Socket.IO events from healer agent (proxied through Redis pub/sub)
```

#### 9.3 Color System and Design Language

The SENTINELS Command Center uses **"Mission Control Dark"** aesthetic:
- Background: `#050A14` (near-black with blue tint)
- Panel background: `#0D1B2A` (dark navy)
- Panel border: `#1E3A5F` (medium blue)
- Accent primary: `#00D4FF` (electric cyan)
- Accent secondary: `#00FF88` (neon green for healthy states)
- Warning: `#FFB800` (amber)
- Critical: `#FF3E3E` (red)
- Healing: `#4444FF` (electric blue)
- Text primary: `#E8EDF3` (near-white)
- Text secondary: `#7A8FA6` (muted blue-gray)
- Font: `JetBrains Mono` for metrics/code, `Inter` for labels

#### Phase 9 Chaos Checklist
- [ ] Dashboard loads at http://localhost:3000 with dark mission-control aesthetic
- [ ] 3D graph renders all Netflix and Prime pods as colored spheres
- [ ] Pods show correct colors: green (healthy), red (down), blue (healing)
- [ ] Can rotate/zoom/pan the 3D graph with mouse
- [ ] Hover over node shows pod name, CPU%, memory%, status tooltip
- [ ] Click node opens pod detail sidebar
- [ ] SENTINELS core node (teal spinning ring) visible at center
- [ ] Healing log shows real events (not placeholder text)
- [ ] Metrics scorecard shows real calculated values
- [ ] Grafana iframe loads embedded Netflix RED dashboard

---

### PHASE 10: Attack Simulation Module
**Duration:** 3-4 days  
**Deliverable:** Full attack launcher with all 10 attack types, safety controls, 3D attack visualization

#### 10.1 Attack CRD Templates

```yaml
# chaos/experiments/cpu-stress-template.yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: "cpu-stress-${TARGET_POD}-${TIMESTAMP}"
  namespace: chaos
spec:
  mode: one
  selector:
    namespaces:
    - ${NAMESPACE}
    labelSelectors:
      app: ${SERVICE_NAME}
  stressors:
    cpu:
      workers: ${WORKERS}      # 1-4 based on intensity
      load: ${LOAD}            # 50-100 based on intensity
  duration: "${DURATION}s"
```

The backend substitutes template variables when creating experiments:
```python
# dashboard/backend/attack_launcher.py

INTENSITY_TO_PARAMS = {
    1: {"cpu_workers": 1, "cpu_load": 50, "memory_size": "128Mi"},
    2: {"cpu_workers": 1, "cpu_load": 70, "memory_size": "256Mi"},
    3: {"cpu_workers": 2, "cpu_load": 80, "memory_size": "384Mi"},
    4: {"cpu_workers": 2, "cpu_load": 90, "memory_size": "512Mi"},
    5: {"cpu_workers": 4, "cpu_load": 100, "memory_size": "768Mi"},
}
```

#### 10.2 k6 DDoS Attack Script

```javascript
// chaos/k6-scripts/http-flood.js
import http from 'k6/http';
import { sleep } from 'k6';

const TARGET_URL = __ENV.TARGET_URL || 'http://netflix-gateway.netflix.svc:8001';
const DURATION = __ENV.DURATION || '60s';

export let options = {
  vus: parseInt(__ENV.VUS || '50'),  // Virtual users (concurrent connections)
  duration: DURATION,
};

export default function () {
  // Flood all endpoints to simulate real DDoS
  http.get(`${TARGET_URL}/api/content/browse`);
  http.get(`${TARGET_URL}/api/search?q=action`);
  http.post(`${TARGET_URL}/api/stream/play`, JSON.stringify({content_id: "1"}));
  sleep(0.1);  // 10 requests/second per VU
}
```

The dashboard backend creates a Kubernetes Job running k6 for DDoS attacks:
```python
# Creates Job with k6 image, injects script as ConfigMap
async def launch_http_flood(target: str, vus: int, duration: int):
    batch_v1 = k8s_client.BatchV1Api()
    job = create_k6_job(target, vus, duration)  # Builds Job spec
    batch_v1.create_namespaced_job(namespace="chaos", body=job)
```

#### Phase 10 Chaos Checklist
- [ ] CPU Stress attack: slider set to 3, duration 60s, target search-service → Chaos Mesh creates StressChaos CRD → pod CPU spikes on Prometheus
- [ ] Pod Kill: target search-service → pod disappears from kubectl get pods, recreated within 15s
- [ ] HTTP Flood: target Netflix gateway, 50 VUs for 30s → Prometheus shows request spike, latency increases
- [ ] Emergency Stop: click "STOP ALL" → all active chaos experiments immediately terminated
- [ ] Safety check: try to attack sentinels-system namespace → button disabled/error returned
- [ ] 3D graph shows attack animation: red particles flowing to target node during attack
- [ ] Attack duration expires: attack automatically removed, 3D graph shows recovery
- [ ] All 10 attack types successfully launch without errors

---

### PHASE 11: Metrics, Scoring & Academic Validation
**Duration:** 2-3 days  
**Deliverable:** Metrics aggregator calculating and displaying F1, MTTD, MTTR, FPR, Recovery Rate, System Overhead

#### 11.1 Metrics Aggregator Service

All academic metrics are calculated and cached every 30 seconds. Results exposed via REST and Socket.IO.

The metrics aggregator queries:
1. **PostgreSQL** — healing_audit_log for MTTD, MTTR, Recovery Rate
2. **Prometheus** — chaos_mesh experiment timing for F1 calculation ground truth
3. **Prometheus** — healer process CPU/memory for System Overhead metric
4. **PostgreSQL** — false positive count (alert fired, but no chaos experiment was active)

#### 11.2 Metrics Display in Dashboard

The Metrics Scorecard panel shows all 6 academic metrics with:
- Current value (large number)
- Target value (goal from TRD)
- Traffic light indicator (green/yellow/red)
- Sparkline chart (last 20 data points trend)
- Confidence interval (for statistical validity)

For the academic paper, the dashboard can export a full metrics report as JSON:
```
GET /api/metrics/export?trials=30&fault_type=all
→ Returns: {
    trials: 30,
    fault_types: ["cpu_stress", "pod_kill", "memory_leak", ...],
    mttd: {mean: 91.2, std: 12.4, p95: 118, trials: 30},
    mttr: {mean: 14.1, std: 3.2, p95: 22, trials: 30},
    f1: {precision: 0.96, recall: 0.91, f1: 0.93, n_attacks: 47},
    false_positive_rate: 0.032,
    recovery_success_rate: 0.973,
    system_overhead_cpu_percent: 2.8,
    system_overhead_memory_mb: 187,
    wilcoxon_vs_baseline: {p_value: 0.0023, significant: true}
  }
```

#### Phase 11 Chaos Checklist
- [ ] Run 30 trials: `scripts/run-evaluation-suite.sh 30` (automates attack → wait → record cycle)
- [ ] Export metrics JSON: all 6 metrics populated with real data
- [ ] MTTD < 120s (demo environment; faster than required 60s is better)
- [ ] MTTR < 60s (target: <5 minutes)
- [ ] F1 Score > 0.85
- [ ] False Positive Rate < 10% (may be higher in fast-alert demo config)
- [ ] System Overhead: healer CPU < 200m, memory < 300Mi
- [ ] Wilcoxon test produces p < 0.05 for MTTR comparison with baseline

---

### PHASE 12: Chaos Engineering Validation Suite
**Duration:** 2-3 days  
**Deliverable:** Automated test suite running 8 fault scenarios, generating evaluation report

#### 12.1 Automated Evaluation Runner

```bash
# scripts/run-evaluation-suite.sh
#!/bin/bash
TRIALS=${1:-30}
echo "Running SENTINELS Evaluation Suite: $TRIALS trials"

FAULT_TYPES=("pod_kill" "cpu_stress" "memory_stress" "network_latency" 
             "http_flood" "crash_loop" "disk_io" "cascading")

for fault in "${FAULT_TYPES[@]}"; do
    echo "=== Fault Type: $fault ==="
    for i in $(seq 1 $((TRIALS/8))); do
        echo "  Trial $i/$((TRIALS/8)) for $fault"
        
        # Wait for baseline (30s with no active chaos)
        sleep 30
        
        # Record baseline metrics
        BASELINE=$(curl -s http://localhost:5050/api/metrics/snapshot)
        
        # Inject fault
        ATTACK_ID=$(curl -s -X POST http://localhost:3000/api/attacks/launch \
          -H "Content-Type: application/json" \
          -d "{\"type\": \"$fault\", \"target\": \"netflix\", \"intensity\": 3, \"duration\": 60}" \
          | jq -r '.attack_id')
        
        echo "  Attack $ATTACK_ID launched"
        
        # Wait for healing to complete (max 5 minutes)
        sleep 90
        
        # Record post-healing metrics
        curl -s "http://localhost:5050/api/metrics/trial?attack_id=$ATTACK_ID" \
          >> evaluation_results.jsonl
        
        echo "  Trial complete"
    done
done

echo "Evaluation complete. Generating report..."
python3 scripts/generate_evaluation_report.py evaluation_results.jsonl
```

#### Phase 12 Chaos Checklist
- [ ] Run full evaluation suite (8 fault types × ~4 trials = ~30 trials)
- [ ] All 8 fault types successfully injected and detected
- [ ] Evaluation report generated as PDF/Markdown
- [ ] SENTINELS performs better than baseline (K8s restart only) on all metrics
- [ ] Box plots generated for MTTD/MTTR distributions
- [ ] Statistical significance confirmed (p < 0.05)
- [ ] System runs stable for 24 hours with chaos experiments running every 30 minutes

---

# PART 7 — SECURITY ARCHITECTURE

## 7.1 RBAC Configuration

```yaml
# kubernetes/rbac/healer-rbac.yaml
# ServiceAccount for the healer — minimal permissions
apiVersion: v1
kind: ServiceAccount
metadata:
  name: healer-sa
  namespace: sentinels-system
---
# Role for Netflix namespace — only what healer needs
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: healer-role-netflix
  namespace: netflix
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch", "delete"]  # delete = restart action
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale"]
  verbs: ["get", "list", "watch", "patch"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["get", "list", "watch"]
# EXPLICITLY EXCLUDED (healer cannot touch):
# - secrets, configmaps (no data access)
# - serviceaccounts, roles, rolebindings (no privilege escalation)
# - nodes, persistentvolumes (no infrastructure access)
---
# Same Role for Prime namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: healer-role-prime
  namespace: prime
rules:  # identical to above
...
---
# RoleBindings — separate per namespace (NOT a ClusterRoleBinding)
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: healer-binding-netflix
  namespace: netflix
subjects:
- kind: ServiceAccount
  name: healer-sa
  namespace: sentinels-system
roleRef:
  kind: Role
  name: healer-role-netflix
  apiGroup: rbac.authorization.k8s.io
```

## 7.2 Network Policies (Zero Trust)

```yaml
# kubernetes/network-policies/sentinels-network-policy.yaml
# Default deny all in sentinels-system namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: sentinels-system
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
  # No ingress or egress rules = ALL traffic blocked
---
# Allow: AlertManager → Healer
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-alertmanager-to-healer
  namespace: sentinels-system
spec:
  podSelector:
    matchLabels:
      app: healer-agent
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: monitoring
    ports:
    - protocol: TCP
      port: 5000
---
# Allow: Healer → Kubernetes API server
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-healer-to-k8s-api
  namespace: sentinels-system
spec:
  podSelector:
    matchLabels:
      app: healer-agent
  policyTypes: [Egress]
  egress:
  - ports:
    - port: 443   # K8s API server
    - port: 6443  # Alternative K8s API port
---
# Allow: Dashboard → SENTINELS services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dashboard-to-sentinels
  namespace: sentinels-system
spec:
  podSelector:
    matchLabels:
      app: healer-agent
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: dashboard
```

## 7.3 Pod Security Standards

All SENTINELS pods enforce the Restricted Pod Security Standard:
```yaml
# Applied to every SENTINELS pod spec:
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault
```

## 7.4 Secrets Management

```yaml
# All secrets stored as Kubernetes Secrets (base64 encoded)
# In production: use External Secrets Operator + HashiCorp Vault
# For demo: Kubernetes Secrets are sufficient

apiVersion: v1
kind: Secret
metadata:
  name: sentinels-secrets
  namespace: sentinels-system
type: Opaque
stringData:
  postgres-url: "postgresql://sentinels:CHANGE_ME@postgres:5432/sentinels"
  redis-url: "redis://:CHANGE_ME@redis:6379"
  alertmanager-webhook-token: "sentinels-webhook-token-CHANGE_IN_PRODUCTION"
  opa-url: "http://opa-server.sentinels-system.svc:8181"
```

---

# PART 8 — EDGE CASES, FAILURE MODES & RISK MITIGATION

## 8.1 The Infinite Healing Loop Problem

**Scenario:** Healer restarts pod → pod starts, crashes → healer detects crash → restarts again → infinite loop

**Detection:** The `PodCrashLooping` alert triggers at 3 restarts in 5 minutes. After the healer restarts a pod once, it records the action with a cooldown timer (5 minutes minimum). If the pod continues crashing:
- Attempt 1: restart_pod action
- Attempt 2 (within 5min): BLOCKED by cooldown → escalated to alert_human
- After 3 failures: circuit breaker OPENS → all healing for this namespace paused 300s

**Mitigation Code:** `cooldown_mgr.record_action(pod)` — recorded in Redis with TTL=300

## 8.2 Healer Kills Too Many Pods (Thundering Herd)

**Scenario:** Multiple alerts fire simultaneously (5 services down) → healer restarts all 5 at once → service completely unavailable

**Detection:** Blast radius check: `healthy_pod_count < total_pod_count * 0.50`

**Mitigation:** Canary healing — if 5 pods need healing:
- Heal 1 first, wait 30s for verification
- If first pod recovers, heal next 2, wait 30s
- Then remaining 2
- Never leave fewer than 50% of pods available

## 8.3 SENTINELS Itself Goes Down

**Scenario:** Healer agent crashes → no healing happens → attackers can cause unlimited damage

**Mitigation:**
- Healer runs with `replicas: 2` (HA) — one replica death doesn't break healing
- Kubernetes native healing (liveness/readiness probes + ReplicaSet) handles healer recovery without SENTINELS intervention (self-healing at infrastructure level)
- AlertManager has fallback receiver: if webhook fails, emails admin (configurable)

## 8.4 OPA Server Unavailable

**Scenario:** OPA crashes → healer can't get policy decision → blocks all healing

**Mitigation:**
- Healer has embedded fallback policy table (Python dict) for critical rules
- OPA server runs with `replicas: 2`
- Fallback activates only if OPA fails 3 consecutive times

## 8.5 Prometheus Not Scraping

**Scenario:** ServiceMonitor misconfigured → metrics not collected → Isolation Forest has no data → alerts don't fire

**Detection:** Prometheus self-monitoring: `up{job="sentinels-services"} == 0` fires its own alert

**Mitigation:** Every service has `annotations: {prometheus.io/scrape: "true"}` as backup to ServiceMonitors

## 8.6 YouTube API Rate Limits

**Scenario:** Demo environment makes too many YouTube embed requests → YouTube blocks/throttles

**Mitigation:**
- YouTube IFrame API has no rate limits for embedding (it's free and unlimited)
- Use `youtube-nocookie.com` domain for embeds (privacy mode, no tracking, same reliability)
- Pre-load 5 specific video IDs that are known stable (official trailers from major studios)

## 8.7 Resource Exhaustion on Laptop

**Scenario:** Too many chaos experiments running + all services at high resource usage → laptop runs out of memory → k3d crashes

**Mitigation:**
- Maximum 2 concurrent chaos experiments (enforced by dashboard)
- All pods have hard memory limits (OOM-kill before node runs out)
- System alarm: if `node_memory_MemAvailable_bytes < 1GB`, dashboard shows RED warning and disables new attacks

## 8.8 Database Corruption During Demo

**Scenario:** PostgreSQL pod killed during write → data corruption → audit logs lost

**Mitigation:**
- PostgreSQL uses PersistentVolumeClaim (data survives pod restarts)
- PostgreSQL excluded from chaos experiment targets (protected namespace)
- Healing events also emitted via Socket.IO → frontend caches last 100 events in React state (survives brief DB outage)

---

# PART 9 — COMPLETE TECH STACK SUMMARY

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend - Dashboard** | React | 18.3 | Command Center SPA |
| **Frontend - Dashboard** | TypeScript | 5.4 | Type safety |
| **Frontend - Dashboard** | React Three Fiber | 8.16 | 3D topology graph |
| **Frontend - Dashboard** | Three.js | 0.166 | WebGL 3D engine |
| **Frontend - Dashboard** | Tailwind CSS | 3.4 | Styling |
| **Frontend - Dashboard** | Framer Motion | 11 | UI animations |
| **Frontend - Dashboard** | Socket.IO Client | 4.7 | Real-time events |
| **Frontend - Netflix** | React | 18.3 | Netflix UI |
| **Frontend - Prime** | React | 18.3 | Prime Video UI |
| **Backend - Healer** | Python | 3.12 | ML + operator |
| **Backend - Healer** | FastAPI | 0.111 | Async REST API |
| **Backend - Healer** | Socket.IO | 5.x | Real-time broadcast |
| **Backend - Healer** | Kopf | 1.x | K8s operator framework |
| **ML** | scikit-learn | 1.4+ | Isolation Forest |
| **ML** | NumPy | 1.26 | Feature computation |
| **ML** | Pandas | 2.2 | Data manipulation |
| **Backend - Netflix** | FastAPI | 0.111 | 8 microservices |
| **Backend - Prime** | Django | 5.0 | Monolith |
| **Policy Engine** | OPA | 0.65 | Rego policy evaluation |
| **Database** | PostgreSQL | 16 | Audit logs, user data |
| **Cache/PubSub** | Redis | 7.2 | Circuit breakers, events |
| **Time Series** | Prometheus TSDB | 2.52 | Metrics storage |
| **Monitoring** | kube-prometheus-stack | 82.x | Prometheus + Grafana |
| **Logging** | Loki | 3.x | Log aggregation |
| **Tracing** | Jaeger | 1.57 | Distributed traces |
| **Chaos** | Chaos Mesh | 2.7.3 | Fault injection |
| **Load Testing** | k6 | 0.51 | HTTP flood simulation |
| **Container** | Docker | 25.x | Image builds |
| **Kubernetes** | k3d (k3s) | 5.7 | Local K8s cluster |
| **Package Manager** | Helm | 4.1 | K8s app packaging |
| **CI/CD** | GitHub Actions | — | Build + push images |
| **Image Registry** | Docker Hub | — | Container images |
| **Cert Management** | cert-manager | 1.14 | TLS certificates |

---

# PART 10 — ACADEMIC PUBLICATION NOTES

Per the original TRD, target venues are SEAMS 2026 and IEEE CLOUD 2026.

## Key Claims This Implementation Supports:

1. **"Lightweight ML overhead"** → Isolation Forest inference in <0.1ms, entire healer using <200m CPU = demonstrably lightweight
2. **"Explainable remediation"** → Every healing action has a policy_id, policy_version, anomaly_score, reason string — full audit trail
3. **"Works on diverse architectures"** → Demonstrated on microservices (Netflix) AND monolith (Prime)
4. **"Faster than commercial alternatives"** → No 3-week training period (unlike Datadog Watchdog); operational in <5 minutes after install
5. **"Integrated chaos validation"** → Chaos Mesh experiments tied directly to evaluation metrics — this is the SEAMS paper's novelty

## Evaluation Baseline Comparison:

| Baseline | Description | Implementation |
|---|---|---|
| **B1: No Healing** | Only K8s restart policy active, no SENTINELS | Disable healer, run same fault suite |
| **B2: K8s Native** | HPA + liveness probes only | Tune HPA thresholds, disable healer |
| **B3: SENTINELS** | Full system active | Normal operation |

Compare MTTD and MTTR across all three baselines for the paper.

---
---

# PART 11 — ONE-COMMAND DEMO SETUP SCRIPT

```bash
# scripts/demo-setup.sh — Run this on the day of presentation
#!/bin/bash
set -e

echo "╔══════════════════════════════════════╗"
echo "║  SENTINELS v2.0 — Demo Setup Script  ║"
echo "╚══════════════════════════════════════╝"

# Step 1: Create k3d cluster
echo "[1/8] Creating Kubernetes cluster..."
k3d cluster create sentinels \
  --servers 1 --agents 2 \
  --port "3000:30000@loadbalancer" \
  --port "3001:30001@loadbalancer" \
  --port "3002:30002@loadbalancer" \
  --port "3003:30003@loadbalancer" \
  --port "9090:30090@loadbalancer" \
  --memory "10g" 2>/dev/null || \
  (echo "Cluster exists, reusing" && k3d cluster start sentinels)

# Step 2: Install monitoring stack
echo "[2/8] Installing Prometheus + Grafana + AlertManager..."
helm upgrade --install kube-prometheus-stack \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values monitoring/prometheus/values.yaml --wait

# Step 3: Install Loki
echo "[3/8] Installing Loki log aggregation..."
helm upgrade --install loki grafana/loki-stack \
  --namespace monitoring --set promtail.enabled=true --wait

# Step 4: Deploy NetflixOS
echo "[4/8] Deploying NetflixOS (microservices)..."
helm upgrade --install netflix kubernetes/helm-charts/netflix \
  --namespace netflix --create-namespace --wait

# Step 5: Deploy PrimeOS
echo "[5/8] Deploying PrimeOS (monolith)..."
helm upgrade --install prime kubernetes/helm-charts/prime \
  --namespace prime --create-namespace --wait

# Step 6: Deploy SENTINELS Core
echo "[6/8] Deploying SENTINELS healing engine..."
helm upgrade --install sentinels kubernetes/helm-charts/sentinels \
  --namespace sentinels-system --create-namespace --wait

# Step 7: Install Chaos Mesh
echo "[7/8] Installing Chaos Mesh v2.7.3..."
helm upgrade --install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos --create-namespace \
  --set controllerManager.enableFilterNamespace=false --wait

# Step 8: Deploy Command Center Dashboard
echo "[8/8] Deploying SENTINELS Command Center..."
helm upgrade --install dashboard kubernetes/helm-charts/dashboard \
  --namespace dashboard --create-namespace --wait

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  SENTINELS v2.0 is READY                     ║"
echo "║                                              ║"
echo "║  🎯 Command Center:  http://localhost:3000   ║"
echo "║  🎬 Netflix Clone:   http://localhost:3001   ║"
echo "║  📺 Prime Clone:     http://localhost:3002   ║"
echo "║  📊 Grafana:         http://localhost:3003   ║"
echo "║     (admin / sentinels2024)                  ║"
echo "║  🔍 Prometheus:      http://localhost:9090   ║"
echo "║                                              ║"
echo "║  SENTINELS is now monitoring both apps.      ║"
echo "║  Open Command Center and launch an attack!   ║"
echo "╚══════════════════════════════════════════════╝"
```

---

# APPENDIX A — QUICK REFERENCE: CRITICAL COMMANDS

```bash
# Create cluster
k3d cluster create sentinels --servers 1 --agents 2 --memory "10g"

# Install monitoring
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Check all pods
kubectl get pods -A

# Watch healer logs in real-time
kubectl logs -n sentinels-system -l app=healer-agent -f

# Forward Prometheus (if port mapping not working)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090

# Forward Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3003:80

# Test AlertManager webhook manually
curl -X POST http://localhost:5000/alerts \
  -H "Content-Type: application/json" \
  -d '{"version": "4", "alerts": [{"status": "firing", "labels": {"alertname": "HighCPUUsage", "pod": "search-service-xxx-yyy", "namespace": "netflix", "severity": "critical"}}]}'

# Check OPA policy
curl http://localhost:8181/v1/data/sentinels/healing/action \
  -d '{"input": {"anomaly_type": "high_cpu", "anomaly_score": -0.45, "cpu_percent": 92, "severity": "CRITICAL", "pod": "search-service-xxx", "namespace": "netflix"}}'

# Manually inject chaos (test without dashboard)
kubectl apply -f chaos/experiments/cpu-stress-search.yaml

# Emergency: delete all chaos
kubectl delete podchaos,stresschaos,networkchaos,dnschaos --all -n chaos
```

---

# APPENDIX B — GLOSSARY

| Term | Definition |
|---|---|
| **MAPE-K** | Monitor-Analyze-Plan-Execute-Knowledge — IBM's autonomic computing loop that SENTINELS implements |
| **Isolation Forest** | Unsupervised ML algorithm that detects anomalies by randomly partitioning data; anomalies are isolated with fewer splits |
| **Anomaly Score** | Continuous score from Isolation Forest; negative values = anomaly; more negative = more anomalous |
| **OPA/Rego** | Open Policy Agent / Rego language; evaluates JSON input against declarative policies in <1ms |
| **Kopf** | Kubernetes Operator Pythonic Framework; wraps Kubernetes API for operator development |
| **Circuit Breaker** | Safety mechanism that stops healing after consecutive failures; prevents healing-induced cascading failure |
| **Blast Radius** | The maximum impact of a healing action; SENTINELS limits blast radius to prevent healing from causing more harm |
| **MTTD** | Mean Time to Detect — how quickly SENTINELS notices a problem |
| **MTTR** | Mean Time to Recover — how quickly SENTINELS fixes a problem after detecting it |
| **F1 Score** | Harmonic mean of precision and recall; measures anomaly detection quality |
| **kube-prometheus-stack** | Helm chart that deploys the entire monitoring stack in one command |
| **k3d** | k3s (lightweight Kubernetes) running inside Docker containers for local development |
| **PDB** | Pod Disruption Budget — Kubernetes object that limits how many pods can be down simultaneously |
| **HPA** | Horizontal Pod Autoscaler — Kubernetes object that automatically scales pod replicas |
| **Liveness Probe** | Kubernetes health check; if fails, container is restarted |
| **Readiness Probe** | Kubernetes health check; if fails, pod is removed from service load balancer |
| **ServiceMonitor** | Custom Kubernetes resource that tells Prometheus which services to scrape |
| **PrometheusRule** | Custom Kubernetes resource that defines alerting rules in Prometheus |
| **Chaos Mesh** | CNCF project for fault injection in Kubernetes using CRDs |
| **RED Method** | Rate-Error-Duration; framework for monitoring microservices from user perspective |
| **USE Method** | Utilization-Saturation-Errors; framework for monitoring infrastructure resources |
| **Concept Drift** | When metric distributions shift over time, making old ML models less accurate |
| **Warm Start** | sklearn parameter that adds new estimators to an existing model (incremental training) |

---

# DOCUMENT METADATA

```
Document: SENTINELS v2.0 Master Blueprint & Development Bible
Version: 2.0.0
Created: 2026
Author: SENTINELS Architecture Team
Status: FINAL — Ready for Execution
Classification: Capstone Project Technical Specification

Files:
- Part 1: Vision, Architecture, Tech Stack (this document, Part 1)
- Part 2: Development Blocks, Phases, Implementation Guide (this document, Part 2)
- Part 3: Antigravity Prompt, Appendices (this document, Part 3)

Original TRD Reference:
- SENTINELS__Self-Healing_Kubernetes_Platform_Technical_Requirements_and_Execution_Blueprint.md
  (The original TRD remains valid for academic methodology and algorithm rationale)
  This v2.0 document EXTENDS it with the three-application architecture.

Change Log:
v1.0 → v2.0:
+ Added NetflixOS microservices application
+ Added PrimeOS monolith application  
+ Added SENTINELS Command Center with 3D visualization
+ Added Attack Launcher with 10 fault types
+ Added k6 HTTP flood simulation
+ Added Metrics Aggregator service
+ Added detailed React Three Fiber 3D graph specification
+ Added complete port assignment table
+ Added resource budget planning for laptop deployment
+ Added full Antigravity execution prompt
+ Added all edge cases and mitigation strategies
```
