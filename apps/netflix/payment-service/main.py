"""
Netflix Payment Service — Port 8007
Simulated subscription management and payment processing.
"""
import os, logging, json, uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, make_asgi_app
import asyncpg

SERVICE_NAME = "payment-service"
SERVICE_PORT = 8007
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentinels:sentinels123@localhost:5432/netflix_db")

logging.basicConfig(level=logging.INFO, format=json.dumps({
    "timestamp": "%(asctime)s", "level": "%(levelname)s",
    "service": SERVICE_NAME, "message": "%(message)s"
}))
logger = logging.getLogger(SERVICE_NAME)

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency',
    ['method', 'endpoint', 'service'])
PAYMENTS_PROCESSED = Counter('payments_processed_total', 'Total payments', ['plan', 'service'])

PLANS = {
    "basic": {"name": "Basic", "price": 8.99, "screens": 1, "quality": "720p"},
    "standard": {"name": "Standard", "price": 13.99, "screens": 2, "quality": "1080p"},
    "premium": {"name": "Premium", "price": 17.99, "screens": 4, "quality": "4K"},
}

db_pool: Optional[asyncpg.Pool] = None
async def get_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return db_pool

class SubscribeRequest(BaseModel):
    user_id: int
    plan: str

class PaymentRecord(BaseModel):
    id: int
    user_id: int
    plan: str
    amount: float
    status: str
    transaction_id: str
    created_at: str

async def metrics_middleware(request: Request, call_next):
    method, path = request.method, request.url.path
    with REQUEST_LATENCY.labels(method=method, endpoint=path, service=SERVICE_NAME).time():
        response = await call_next(request)
    REQUEST_COUNT.labels(method=method, endpoint=path,
        status_code=response.status_code, service=SERVICE_NAME).inc()
    return response

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{SERVICE_NAME} starting on port {SERVICE_PORT}")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
                plan VARCHAR(20) NOT NULL, amount DECIMAL(10,2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'USD', status VARCHAR(20) DEFAULT 'completed',
                transaction_id VARCHAR(100), created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
    yield
    if db_pool: await db_pool.close()

app = FastAPI(title="NetflixOS Payment Service", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])
app.middleware("http")(metrics_middleware)
app.mount("/metrics", make_asgi_app())

@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.get("/payment/plans")
async def list_plans():
    return PLANS

@app.post("/payment/subscribe")
async def subscribe(req: SubscribeRequest):
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Choose from: {list(PLANS.keys())}")
    
    plan_info = PLANS[req.plan]
    txn_id = f"SIM-{uuid.uuid4().hex[:12].upper()}"
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO payments (user_id, plan, amount, transaction_id, status)
               VALUES ($1, $2, $3, $4, 'completed') RETURNING id, created_at""",
            req.user_id, req.plan, plan_info["price"], txn_id
        )
        # Update user's subscription plan
        await conn.execute(
            "UPDATE netflix_users SET subscription_plan = $1, updated_at = NOW() WHERE id = $2",
            req.plan, req.user_id
        )
    
    PAYMENTS_PROCESSED.labels(plan=req.plan, service=SERVICE_NAME).inc()
    logger.info(f"Payment processed: user={req.user_id} plan={req.plan} txn={txn_id}")
    
    return {
        "status": "success",
        "transaction_id": txn_id,
        "plan": plan_info,
        "message": f"[SIMULATED] Successfully subscribed to {plan_info['name']} plan"
    }

@app.get("/payment/history/{user_id}", response_model=List[PaymentRecord])
async def payment_history(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, user_id, plan, amount, status, transaction_id, created_at FROM payments WHERE user_id = $1 ORDER BY created_at DESC LIMIT 20",
            user_id
        )
    return [PaymentRecord(id=r["id"], user_id=r["user_id"], plan=r["plan"],
        amount=float(r["amount"]), status=r["status"], transaction_id=r["transaction_id"],
        created_at=r["created_at"].isoformat()) for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
