"""
Netflix Search Service — Port 8005
Full-text search using SQLite FTS5. Syncs content from content-service on startup.
Independent deployable — can die without affecting other services.
"""
import os
import sqlite3
import logging
import json
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, make_asgi_app
import httpx

SERVICE_NAME = "search-service"
SERVICE_PORT = 8005
CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://localhost:8003")
DB_PATH = "/tmp/search_index.db"

logging.basicConfig(level=logging.INFO, format=json.dumps({
    "timestamp": "%(asctime)s", "level": "%(levelname)s",
    "service": SERVICE_NAME, "message": "%(message)s"
}))
logger = logging.getLogger(SERVICE_NAME)

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency',
    ['method', 'endpoint', 'service'])
SEARCH_QUERIES = Counter('search_queries_total', 'Search queries executed', ['service'])

class SearchResult(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    youtube_id: str
    thumbnail_url: Optional[str] = None
    rating: float = 0.0
    rank: float = 0.0

def init_fts_db():
    """Initialize SQLite FTS5 database for full-text search."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS content_fts")
    conn.execute("""
        CREATE VIRTUAL TABLE content_fts USING fts5(
            id UNINDEXED, title, description, category,
            youtube_id UNINDEXED, thumbnail_url UNINDEXED,
            rating UNINDEXED, tokenize='porter unicode61'
        )
    """)
    conn.commit()
    return conn

async def sync_content_index():
    """Fetch all content from content-service and build the FTS5 index."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{CONTENT_SERVICE_URL}/content/browse")
            resp.raise_for_status()
            categories = resp.json()

        conn = init_fts_db()
        total = 0
        for cat_group in categories:
            for item in cat_group.get("items", []):
                conn.execute(
                    "INSERT INTO content_fts (id, title, description, category, youtube_id, thumbnail_url, rating) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (item["id"], item["title"], item.get("description", ""),
                     item["category"], item["youtube_id"],
                     item.get("thumbnail_url", ""), item.get("rating", 0))
                )
                total += 1
        conn.commit()
        conn.close()
        logger.info(f"FTS5 index built with {total} items")
        return total
    except Exception as e:
        logger.error(f"Failed to sync content index: {e}")
        # Create empty index so service still starts
        init_fts_db()
        return 0

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
    count = await sync_content_index()
    logger.info(f"Search index ready with {count} items")
    # Background re-sync every 5 minutes
    async def periodic_sync():
        while True:
            await asyncio.sleep(300)
            try:
                await sync_content_index()
            except Exception:
                pass
    task = asyncio.create_task(periodic_sync())
    yield
    task.cancel()

app = FastAPI(title="NetflixOS Search Service", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])
app.middleware("http")(metrics_middleware)
app.mount("/metrics", make_asgi_app())

@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.get("/search", response_model=List[SearchResult])
async def search(q: str = Query(..., min_length=1, description="Search query")):
    """Full-text search across movie titles and descriptions using FTS5 ranking."""
    SEARCH_QUERIES.labels(service=SERVICE_NAME).inc()
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        # FTS5 match with BM25 ranking
        rows = conn.execute("""
            SELECT id, title, description, category, youtube_id, thumbnail_url, rating,
                   rank AS rank_score
            FROM content_fts
            WHERE content_fts MATCH ?
            ORDER BY rank
            LIMIT 20
        """, (q,)).fetchall()
        conn.close()

        return [SearchResult(
            id=r["id"], title=r["title"], description=r["description"],
            category=r["category"], youtube_id=r["youtube_id"],
            thumbnail_url=r["thumbnail_url"], rating=r["rating"],
            rank=abs(r["rank_score"])
        ) for r in rows]
    except sqlite3.OperationalError:
        # Fallback: simple LIKE search if FTS fails
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT id, title, description, category, youtube_id, thumbnail_url, rating, 0.0 as rank_score
            FROM content_fts WHERE title LIKE ? OR description LIKE ?
            LIMIT 20
        """, (f"%{q}%", f"%{q}%")).fetchall()
        conn.close()
        return [SearchResult(
            id=r["id"], title=r["title"], description=r["description"],
            category=r["category"], youtube_id=r["youtube_id"],
            thumbnail_url=r["thumbnail_url"], rating=r["rating"], rank=0.0
        ) for r in rows]

@app.post("/search/reindex")
async def reindex():
    """Force re-sync of the FTS5 index from content-service."""
    count = await sync_content_index()
    return {"status": "reindexed", "items": count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
