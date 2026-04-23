.PHONY: help dev dev-up dev-down dev-logs build-all test-all clean cluster-create cluster-delete deploy undeploy

# ═══════════════════════════════════════════════════════════════
# SENTINELS v2.0 — Makefile
# ═══════════════════════════════════════════════════════════════

help: ## Show this help
	@echo "SENTINELS v2.0 — Available Commands"
	@echo "═══════════════════════════════════════════"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Local Development ──────────────────────────────────────────
dev-up: ## Start all services locally via Docker Compose
	docker-compose -f docker-compose.dev.yml up -d --build

dev-down: ## Stop all local services
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## Follow logs from all services
	docker-compose -f docker-compose.dev.yml logs -f

dev-ps: ## Show status of all local services
	docker-compose -f docker-compose.dev.yml ps

# ── Building ───────────────────────────────────────────────────
build-netflix: ## Build all Netflix Docker images
	docker build -t sentinels/netflix-user-service:latest apps/netflix/user-service/
	docker build -t sentinels/netflix-content-service:latest apps/netflix/content-service/
	docker build -t sentinels/netflix-search-service:latest apps/netflix/search-service/
	docker build -t sentinels/netflix-streaming-service:latest apps/netflix/streaming-service/
	docker build -t sentinels/netflix-recommendation-service:latest apps/netflix/recommendation-service/
	docker build -t sentinels/netflix-payment-service:latest apps/netflix/payment-service/
	docker build -t sentinels/netflix-notification-service:latest apps/netflix/notification-service/
	docker build -t sentinels/netflix-api-gateway:latest apps/netflix/api-gateway/
	docker build -t sentinels/netflix-frontend:latest apps/netflix/frontend/

build-prime: ## Build PrimeOS Docker images
	docker build -t sentinels/prime-backend:latest apps/prime/backend/
	docker build -t sentinels/prime-frontend:latest apps/prime/frontend/

build-sentinels: ## Build SENTINELS engine images
	docker build -t sentinels/healer-agent:latest sentinels/healer-agent/
	docker build -t sentinels/metrics-aggregator:latest sentinels/metrics-aggregator/

build-dashboard: ## Build Dashboard images
	docker build -t sentinels/dashboard-backend:latest dashboard/backend/
	docker build -t sentinels/dashboard-frontend:latest dashboard/frontend/

build-all: build-netflix build-prime build-sentinels build-dashboard ## Build ALL Docker images

# ── Kubernetes ─────────────────────────────────────────────────
cluster-create: ## Create k3d Kubernetes cluster
	powershell -ExecutionPolicy Bypass -File scripts/create-cluster.ps1

cluster-delete: ## Delete k3d cluster
	k3d cluster delete sentinels

deploy: ## Deploy all services to Kubernetes
	powershell -ExecutionPolicy Bypass -File scripts/setup.ps1

undeploy: ## Remove all deployments from Kubernetes
	kubectl delete namespace netflix prime monitoring sentinels-system chaos dashboard --ignore-not-found

# ── Testing ────────────────────────────────────────────────────
test-all: ## Run all tests
	@echo "Testing Netflix services..."
	cd apps/netflix/user-service && python -m pytest tests/ -v
	@echo "Testing SENTINELS ML..."
	cd sentinels/healer-agent && python -m pytest tests/ -v

# ── Cleanup ────────────────────────────────────────────────────
clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
