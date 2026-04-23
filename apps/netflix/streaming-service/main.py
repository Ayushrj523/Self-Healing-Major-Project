"""
Netflix Streaming Service — Port 8004
Handles video playback via YouTube iframe delegation and Redis-based watch tracking.
"""
import os
import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, make_asgi_app
import httpx
import redis.asyncio as aioredis

SERVICE_NAME = "streaming-service"
SERVICE_PORT = 8004
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://localhost:8003")
YOUTUBE_EMBED_BASE = "https://www.youtube-nocookie.com/embed"

logging.basicConfig(level=logging.INFO, format=json.dumps({
    "timestamp": "%(asctime)s", "level": "%(levelname)s",
    "service": SERVICE_NAME, "message": "%(message)s"
}))
logger = logging.getLogger(SERVICE_NAME)

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency',
    ['method', 'endpoint', 'service'])
STREAMS_STARTED = Counter('streams_started_total', 'Total streams started', ['service'])
ACTIVE_STREAMS = Counter('active_streams_current', 'Currently active streams', ['service'])

redis_client: Optional[aioredis.Redis] = None

async def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

class PlayRequest(BaseModel):
    content_id: int
    user_id: Optional[int] = None

class PlayResponse(BaseModel):
    content_id: int
    title: str
    youtube_id: str
    embed_url: str
    session_id: str

class StreamProgress(BaseModel):
    content_id: int
    user_id: int
    progress_percent: float

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
    yield
    if redis_client:
        await redis_client.close()

app = FastAPI(title="NetflixOS Streaming Service", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])
app.middleware("http")(metrics_middleware)
app.mount("/metrics", make_asgi_app())

@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.post("/stream/play", response_model=PlayResponse)
async def play(req: PlayRequest):
    """Start a streaming session — fetches content metadata, returns YouTube embed URL."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{CONTENT_SERVICE_URL}/content/{req.content_id}")
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Content not found")
            resp.raise_for_status()
            content = resp.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Content service unavailable")

    import uuid
    session_id = str(uuid.uuid4())[:12]
    youtube_id = content["youtube_id"]
    embed_url = f"{YOUTUBE_EMBED_BASE}/{youtube_id}?autoplay=1&rel=0&modestbranding=1"

    # Track session in Redis
    try:
        r = await get_redis()
        await r.hset(f"stream:session:{session_id}", mapping={
            "content_id": str(req.content_id),
            "user_id": str(req.user_id or 0),
            "youtube_id": youtube_id,
            "started_at": datetime.utcnow().isoformat(),
            "progress": "0"
        })
        await r.expire(f"stream:session:{session_id}", 7200)  # 2hr TTL
        # Track concurrent viewers
        await r.incr(f"stream:viewers:{req.content_id}")
        await r.expire(f"stream:viewers:{req.content_id}", 7200)
    except Exception as e:
        logger.warning(f"Redis tracking failed (non-fatal): {e}")

    STREAMS_STARTED.labels(service=SERVICE_NAME).inc()
    return PlayResponse(
        content_id=req.content_id,
        title=content["title"],
        youtube_id=youtube_id,
        embed_url=embed_url,
        session_id=session_id
    )

@app.post("/stream/progress")
async def update_progress(progress: StreamProgress):
    """Update watch progress for a user."""
    try:
        r = await get_redis()
        await r.hset(f"stream:progress:{progress.user_id}:{progress.content_id}",
            mapping={"progress": str(progress.progress_percent),
                      "updated_at": datetime.utcnow().isoformat()})
        await r.expire(f"stream:progress:{progress.user_id}:{progress.content_id}", 86400)
    except Exception as e:
        logger.warning(f"Progress tracking failed: {e}")
    return {"status": "updated"}

@app.get("/stream/viewers/{content_id}")
async def get_viewers(content_id: int):
    """Get current viewer count for a content item."""
    try:
        r = await get_redis()
        count = await r.get(f"stream:viewers:{content_id}")
        return {"content_id": content_id, "viewers": int(count or 0)}
    except Exception:
        return {"content_id": content_id, "viewers": 0}

@app.post("/stream/stop")
async def stop_stream(session_id: str):
    """End a streaming session."""
    try:
        r = await get_redis()
        session = await r.hgetall(f"stream:session:{session_id}")
        if session:
            content_id = session.get("content_id", "0")
            await r.decr(f"stream:viewers:{content_id}")
            await r.delete(f"stream:session:{session_id}")
    except Exception as e:
        logger.warning(f"Stop stream failed: {e}")
    return {"status": "stopped"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
