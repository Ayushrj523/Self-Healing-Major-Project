"""
Netflix Recommendation Service — Port 8006
Pre-computed recommendations stored in Redis. Uses content similarity (tags + category overlap).
"""
import os, logging, json, random
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, make_asgi_app
import httpx
import redis.asyncio as aioredis

SERVICE_NAME = "recommendation-service"
SERVICE_PORT = 8006
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/2")
CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://localhost:8003")

logging.basicConfig(level=logging.INFO, format=json.dumps({
    "timestamp": "%(asctime)s", "level": "%(levelname)s",
    "service": SERVICE_NAME, "message": "%(message)s"
}))
logger = logging.getLogger(SERVICE_NAME)

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency',
    ['method', 'endpoint', 'service'])

redis_client: Optional[aioredis.Redis] = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

class RecommendedItem(BaseModel):
    id: int
    title: str
    category: str
    youtube_id: str
    thumbnail_url: Optional[str] = None
    rating: float = 0.0
    score: float = 0.0

def compute_similarity(item_a_tags: list, item_b_tags: list, same_category: bool) -> float:
    """Jaccard similarity on tags, boosted by same-category match."""
    if not item_a_tags and not item_b_tags:
        return 0.3 if same_category else 0.0
    set_a, set_b = set(item_a_tags), set(item_b_tags)
    intersection = len(set_a & set_b)
    union = len(set_a | set_b) or 1
    jaccard = intersection / union
    return jaccard + (0.3 if same_category else 0.0)

async def build_recommendations_cache():
    """Fetch all content and pre-compute recommendations for each item."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{CONTENT_SERVICE_URL}/content/browse")
            resp.raise_for_status()
            categories = resp.json()
        
        all_items = []
        for cat_group in categories:
            all_items.extend(cat_group.get("items", []))
        
        if not all_items:
            logger.warning("No content available for recommendations")
            return 0

        r = await get_redis()
        count = 0
        for item in all_items:
            scores = []
            for other in all_items:
                if other["id"] == item["id"]:
                    continue
                sim = compute_similarity(
                    item.get("tags", []), other.get("tags", []),
                    item["category"] == other["category"]
                )
                scores.append((other, sim))
            # Sort by similarity desc, take top 10
            scores.sort(key=lambda x: (-x[1], -x[0].get("rating", 0)))
            top_recs = scores[:10]
            
            rec_data = json.dumps([{
                "id": r[0]["id"], "title": r[0]["title"],
                "category": r[0]["category"], "youtube_id": r[0]["youtube_id"],
                "thumbnail_url": r[0].get("thumbnail_url", ""),
                "rating": r[0].get("rating", 0), "score": round(r[1], 3)
            } for r in top_recs])
            
            await r.set(f"rec:item:{item['id']}", rec_data, ex=3600)
            count += 1
        
        # Also build "trending" (top-rated overall)
        trending = sorted(all_items, key=lambda x: x.get("rating", 0), reverse=True)[:10]
        await r.set("rec:trending", json.dumps(trending), ex=3600)
        
        logger.info(f"Built recommendations for {count} items")
        return count
    except Exception as e:
        logger.error(f"Failed to build recommendations: {e}")
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
    await build_recommendations_cache()
    yield
    if redis_client:
        await redis_client.close()

app = FastAPI(title="NetflixOS Recommendation Service", version="2.0.0", lifespan=lifespan)
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

@app.get("/recommend/item/{content_id}", response_model=List[RecommendedItem])
async def recommend_for_item(content_id: int):
    """Get recommendations similar to a specific content item."""
    r = await get_redis()
    cached = await r.get(f"rec:item:{content_id}")
    if cached:
        return json.loads(cached)
    # Fallback: return trending
    trending = await r.get("rec:trending")
    if trending:
        items = json.loads(trending)
        return [RecommendedItem(id=i["id"], title=i["title"], category=i["category"],
            youtube_id=i["youtube_id"], thumbnail_url=i.get("thumbnail_url",""),
            rating=i.get("rating",0), score=0.5) for i in items[:10]]
    return []

@app.get("/recommend/user/{user_id}", response_model=List[RecommendedItem])
async def recommend_for_user(user_id: int):
    """Get personalized recommendations (based on trending for now, watch-history based in K8s)."""
    r = await get_redis()
    trending = await r.get("rec:trending")
    if trending:
        items = json.loads(trending)
        random.shuffle(items)
        return [RecommendedItem(id=i["id"], title=i["title"], category=i["category"],
            youtube_id=i["youtube_id"], thumbnail_url=i.get("thumbnail_url",""),
            rating=i.get("rating",0), score=0.8) for i in items[:10]]
    return []

@app.get("/recommend/trending")
async def trending():
    r = await get_redis()
    cached = await r.get("rec:trending")
    return json.loads(cached) if cached else []

@app.post("/recommend/rebuild")
async def rebuild():
    count = await build_recommendations_cache()
    return {"status": "rebuilt", "items": count}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
