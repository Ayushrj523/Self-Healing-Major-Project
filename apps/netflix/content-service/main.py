"""
Netflix Content Service — Port 8003
Movie catalog management: browse by category, get details, seed data.
"""
import os
import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import asyncpg

SERVICE_NAME = "content-service"
SERVICE_PORT = 8003
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
CONTENT_SERVED = Counter('content_items_served_total', 'Content items served', ['service'])

db_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return db_pool

# ─── Models ───────────────────────────────────────────────────
class ContentItem(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    youtube_id: str
    thumbnail_url: Optional[str] = None
    release_year: Optional[int] = None
    rating: float = 0.0
    duration_minutes: int = 120
    maturity_rating: str = "PG-13"
    tags: List[str] = []

class ContentBrowseResponse(BaseModel):
    category: str
    items: List[ContentItem]
    total: int

# ─── Middleware ───────────────────────────────────────────────
async def metrics_middleware(request: Request, call_next):
    method, path = request.method, request.url.path
    with REQUEST_LATENCY.labels(method=method, endpoint=path, service=SERVICE_NAME).time():
        response = await call_next(request)
    REQUEST_COUNT.labels(method=method, endpoint=path,
        status_code=response.status_code, service=SERVICE_NAME).inc()
    return response

# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{SERVICE_NAME} starting on port {SERVICE_PORT}")
    pool = await get_pool()
    # Ensure table exists (in case init scripts didn't run)
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS netflix_content (
                id SERIAL PRIMARY KEY, title VARCHAR(255) NOT NULL,
                description TEXT, category VARCHAR(50) NOT NULL,
                youtube_id VARCHAR(20) NOT NULL, thumbnail_url VARCHAR(500),
                release_year INTEGER, rating FLOAT DEFAULT 0.0,
                duration_minutes INTEGER DEFAULT 120,
                maturity_rating VARCHAR(10) DEFAULT 'PG-13',
                tags TEXT[] DEFAULT '{}', created_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        count = await conn.fetchval("SELECT COUNT(*) FROM netflix_content")
        logger.info(f"Content catalog loaded: {count} movies")
    yield
    if db_pool:
        await db_pool.close()

app = FastAPI(title="NetflixOS Content Service", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])
app.middleware("http")(metrics_middleware)
app.mount("/metrics", make_asgi_app())

def row_to_content(r) -> ContentItem:
    return ContentItem(
        id=r["id"], title=r["title"], description=r["description"],
        category=r["category"], youtube_id=r["youtube_id"],
        thumbnail_url=r["thumbnail_url"], release_year=r["release_year"],
        rating=r["rating"], duration_minutes=r["duration_minutes"],
        maturity_rating=r["maturity_rating"],
        tags=list(r["tags"]) if r["tags"] else []
    )

@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def ready():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM netflix_content")
        return {"status": "ready", "content_count": count}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/content/browse")
async def browse_content(category: Optional[str] = None):
    """Browse content, optionally filtered by category. Returns grouped by category."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        if category:
            rows = await conn.fetch(
                "SELECT * FROM netflix_content WHERE LOWER(category) = LOWER($1) ORDER BY rating DESC", category)
            items = [row_to_content(r) for r in rows]
            CONTENT_SERVED.labels(service=SERVICE_NAME).inc(len(items))
            return [ContentBrowseResponse(category=category, items=items, total=len(items))]
        else:
            rows = await conn.fetch("SELECT * FROM netflix_content ORDER BY category, rating DESC")
            grouped = {}
            for r in rows:
                cat = r["category"]
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(row_to_content(r))
            CONTENT_SERVED.labels(service=SERVICE_NAME).inc(len(rows))
            return [ContentBrowseResponse(category=cat, items=items, total=len(items))
                    for cat, items in grouped.items()]

@app.get("/content/{content_id}", response_model=ContentItem)
async def get_content(content_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        r = await conn.fetchrow("SELECT * FROM netflix_content WHERE id = $1", content_id)
    if not r:
        raise HTTPException(status_code=404, detail="Content not found")
    CONTENT_SERVED.labels(service=SERVICE_NAME).inc()
    return row_to_content(r)

@app.get("/content/search/internal")
async def search_content(q: str = Query(..., min_length=1)):
    """Internal search endpoint (used by search-service for data sync)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT * FROM netflix_content
               WHERE LOWER(title) LIKE $1 OR LOWER(description) LIKE $1
               ORDER BY rating DESC LIMIT 20""",
            f"%{q.lower()}%"
        )
    return [row_to_content(r) for r in rows]

@app.get("/content/categories")
async def list_categories():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT category, COUNT(*) as count FROM netflix_content GROUP BY category ORDER BY category")
    return [{"category": r["category"], "count": r["count"]} for r in rows]

@app.get("/content/featured")
async def featured_content():
    """Returns top 10 highest-rated movies for the hero section."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM netflix_content ORDER BY rating DESC LIMIT 10")
    return [row_to_content(r) for r in rows]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
