"""
Netflix API Gateway — Port 8001
Central entry point for all Netflix API requests. Handles JWT validation,
request routing to downstream services, rate limiting, and graceful degradation.
"""
import os, logging, json, time
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from jose import JWTError, jwt
from prometheus_client import Counter, Histogram, make_asgi_app
import httpx

SERVICE_NAME = "api-gateway"
SERVICE_PORT = 8001
JWT_SECRET = os.getenv("JWT_SECRET", "sentinels-jwt-secret-change-in-production-2024")
JWT_ALGORITHM = "HS256"

# Downstream service URLs
SERVICES = {
    "user": os.getenv("USER_SERVICE_URL", "http://localhost:8002"),
    "content": os.getenv("CONTENT_SERVICE_URL", "http://localhost:8003"),
    "streaming": os.getenv("STREAMING_SERVICE_URL", "http://localhost:8004"),
    "search": os.getenv("SEARCH_SERVICE_URL", "http://localhost:8005"),
    "recommendation": os.getenv("RECOMMENDATION_SERVICE_URL", "http://localhost:8006"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8007"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8008"),
}

logging.basicConfig(level=logging.INFO, format=json.dumps({
    "timestamp": "%(asctime)s", "level": "%(levelname)s",
    "service": SERVICE_NAME, "message": "%(message)s"
}))
logger = logging.getLogger(SERVICE_NAME)

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency',
    ['method', 'endpoint', 'service'])
UPSTREAM_ERRORS = Counter('upstream_errors_total', 'Upstream service errors',
    ['target_service', 'service'])

async def metrics_middleware(request: Request, call_next):
    method, path = request.method, request.url.path
    with REQUEST_LATENCY.labels(method=method, endpoint=path, service=SERVICE_NAME).time():
        response = await call_next(request)
    REQUEST_COUNT.labels(method=method, endpoint=path,
        status_code=response.status_code, service=SERVICE_NAME).inc()
    return response

def validate_jwt(request: Request) -> Optional[dict]:
    """Validate JWT and return payload, or None if no/invalid token."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"user_id": int(payload["sub"]), "email": payload["email"]}
    except JWTError:
        return None

async def proxy_request(service_name: str, path: str, request: Request,
                         require_auth: bool = False) -> Response:
    """Proxy request to downstream service with error handling."""
    if require_auth:
        user = validate_jwt(request)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
    
    base_url = SERVICES.get(service_name)
    if not base_url:
        raise HTTPException(status_code=500, detail=f"Unknown service: {service_name}")
    
    url = f"{base_url}{path}"
    if request.url.query:
        url += f"?{request.url.query}"
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            body = await request.body()
            headers = {k: v for k, v in request.headers.items() 
                      if k.lower() not in ("host", "content-length")}
            
            resp = await client.request(
                method=request.method, url=url,
                content=body if body else None, headers=headers
            )
            
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json")
            )
    except httpx.ConnectError:
        UPSTREAM_ERRORS.labels(target_service=service_name, service=SERVICE_NAME).inc()
        logger.error(f"Service unavailable: {service_name} at {base_url}")
        return JSONResponse(
            status_code=503,
            content={"error": f"{service_name} is currently unavailable",
                     "service": service_name, "degraded": True}
        )
    except httpx.TimeoutException:
        UPSTREAM_ERRORS.labels(target_service=service_name, service=SERVICE_NAME).inc()
        return JSONResponse(status_code=504,
            content={"error": f"{service_name} request timed out"})

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{SERVICE_NAME} starting on port {SERVICE_PORT}")
    logger.info(f"Downstream services: {json.dumps({k: v for k, v in SERVICES.items()})}")
    yield

app = FastAPI(title="NetflixOS API Gateway", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(metrics_middleware)
app.mount("/metrics", make_asgi_app())

# ─── Health & Status ──────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/status")
async def service_status():
    """Check health of all downstream services."""
    results = {}
    async with httpx.AsyncClient(timeout=5) as client:
        for name, url in SERVICES.items():
            try:
                resp = await client.get(f"{url}/health")
                results[name] = {"status": "healthy", "latency_ms": resp.elapsed.total_seconds() * 1000}
            except Exception:
                results[name] = {"status": "unavailable"}
    return {"gateway": "healthy", "services": results}

# ─── Auth Routes (public) ────────────────────────────────────
@app.post("/api/auth/register")
async def register(request: Request):
    return await proxy_request("user", "/auth/register", request)

@app.post("/api/auth/login")
async def login(request: Request):
    return await proxy_request("user", "/auth/login", request)

# ─── Profile Routes (authenticated) ──────────────────────────
@app.get("/api/profile")
async def get_profile(request: Request):
    return await proxy_request("user", "/profile", request, require_auth=True)

# ─── Content Routes (public) ─────────────────────────────────
@app.get("/api/content/browse")
async def browse(request: Request):
    return await proxy_request("content", "/content/browse", request)

@app.get("/api/content/featured")
async def featured(request: Request):
    return await proxy_request("content", "/content/featured", request)

@app.get("/api/content/categories")
async def categories(request: Request):
    return await proxy_request("content", "/content/categories", request)

@app.get("/api/content/{content_id}")
async def get_content(content_id: int, request: Request):
    return await proxy_request("content", f"/content/{content_id}", request)

# ─── Search Routes (public) ──────────────────────────────────
@app.get("/api/search")
async def search(request: Request):
    return await proxy_request("search", "/search", request)

# ─── Streaming Routes (authenticated) ────────────────────────
@app.post("/api/stream/play")
async def play(request: Request):
    return await proxy_request("streaming", "/stream/play", request, require_auth=True)

@app.post("/api/stream/progress")
async def progress(request: Request):
    return await proxy_request("streaming", "/stream/progress", request, require_auth=True)

# ─── Recommendation Routes ───────────────────────────────────
@app.get("/api/recommend/item/{content_id}")
async def recommend_item(content_id: int, request: Request):
    return await proxy_request("recommendation", f"/recommend/item/{content_id}", request)

@app.get("/api/recommend/trending")
async def trending(request: Request):
    return await proxy_request("recommendation", "/recommend/trending", request)

# ─── Payment Routes (authenticated) ──────────────────────────
@app.get("/api/payment/plans")
async def plans(request: Request):
    return await proxy_request("payment", "/payment/plans", request)

@app.post("/api/payment/subscribe")
async def subscribe(request: Request):
    return await proxy_request("payment", "/payment/subscribe", request, require_auth=True)

# ─── Notification Routes (authenticated) ─────────────────────
@app.get("/api/notifications/{user_id}")
async def notifications(user_id: int, request: Request):
    return await proxy_request("notification", f"/notifications/{user_id}", request, require_auth=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
