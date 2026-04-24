"""
Netflix Notification Service — Port 8008
Simulated email/push notification dispatch, logged to PostgreSQL.
"""
import os, logging, json, uuid
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, make_asgi_app
import asyncpg

SERVICE_NAME = "notification-service"
SERVICE_PORT = 8008
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
NOTIFICATIONS_SENT = Counter('notifications_sent_total', 'Notifications sent', ['type', 'service'])

db_pool: Optional[asyncpg.Pool] = None
async def get_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return db_pool

class NotifyRequest(BaseModel):
    user_id: int
    type: str = "info"  # info, welcome, payment, recommendation, alert
    title: str
    message: str

class NotificationItem(BaseModel):
    id: int
    type: str
    title: str
    message: str
    read: bool
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
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL,
                type VARCHAR(50) NOT NULL, title VARCHAR(255) NOT NULL,
                message TEXT, read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
    yield
    if db_pool: await db_pool.close()

app = FastAPI(title="NetflixOS Notification Service", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(metrics_middleware)
app.mount("/metrics", make_asgi_app())

@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.post("/notify")
async def send_notification(req: NotifyRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO notifications (user_id, type, title, message)
               VALUES ($1, $2, $3, $4) RETURNING id, created_at""",
            req.user_id, req.type, req.title, req.message
        )
    NOTIFICATIONS_SENT.labels(type=req.type, service=SERVICE_NAME).inc()
    logger.info(f"[SIMULATED] Notification sent: user={req.user_id} type={req.type} title={req.title}")
    return {"status": "sent", "notification_id": row["id"],
            "message": "[SIMULATED] Notification delivered"}

@app.get("/notifications/{user_id}", response_model=List[NotificationItem])
async def get_notifications(user_id: int, unread_only: bool = False):
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = "SELECT id, type, title, message, read, created_at FROM notifications WHERE user_id = $1"
        if unread_only:
            query += " AND read = FALSE"
        query += " ORDER BY created_at DESC LIMIT 50"
        rows = await conn.fetch(query, user_id)
    return [NotificationItem(id=r["id"], type=r["type"], title=r["title"],
        message=r["message"], read=r["read"], created_at=r["created_at"].isoformat()) for r in rows]

@app.put("/notifications/{notification_id}/read")
async def mark_read(notification_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE notifications SET read = TRUE WHERE id = $1", notification_id)
    return {"status": "marked_read"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
