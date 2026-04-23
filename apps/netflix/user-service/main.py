"""
Netflix User Service — Port 8002
Handles user registration, login (JWT), profile management, and watch history.
"""
import os
import uuid
import logging
import json
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app

import asyncpg

# ─── Configuration ────────────────────────────────────────────
SERVICE_NAME = "user-service"
SERVICE_PORT = 8002
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentinels:sentinels123@localhost:5432/netflix_db")
JWT_SECRET = os.getenv("JWT_SECRET", "sentinels-jwt-secret-change-in-production-2024")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

# ─── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format=json.dumps({
        "timestamp": "%(asctime)s",
        "level": "%(levelname)s",
        "service": SERVICE_NAME,
        "message": "%(message)s"
    })
)
logger = logging.getLogger(SERVICE_NAME)

# ─── Prometheus Metrics ───────────────────────────────────────
REQUEST_COUNT = Counter(
    'http_requests_total', 'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 'HTTP request latency',
    ['method', 'endpoint', 'service']
)
ACTIVE_REQUESTS = Gauge(
    'http_requests_active', 'Active HTTP requests',
    ['service']
)

# ─── Password Hashing ────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Database Pool ────────────────────────────────────────────
db_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return db_pool

# ─── Pydantic Models ─────────────────────────────────────────
class UserRegister(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 chars)")
    display_name: str = Field(..., min_length=1, description="Display name")

class UserLogin(BaseModel):
    email: str
    password: str

class UserProfile(BaseModel):
    id: int
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class WatchHistoryEntry(BaseModel):
    content_id: int
    title: str
    watched_at: str
    progress_percent: float

# ─── JWT Utilities ────────────────────────────────────────────
def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"user_id": int(payload["sub"]), "email": payload["email"]}
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# ─── Middleware ───────────────────────────────────────────────
async def metrics_middleware(request: Request, call_next):
    ACTIVE_REQUESTS.labels(service=SERVICE_NAME).inc()
    method = request.method
    path = request.url.path
    
    with REQUEST_LATENCY.labels(method=method, endpoint=path, service=SERVICE_NAME).time():
        response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=method, endpoint=path,
        status_code=response.status_code, service=SERVICE_NAME
    ).inc()
    ACTIVE_REQUESTS.labels(service=SERVICE_NAME).dec()
    return response

# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"{SERVICE_NAME} starting on port {SERVICE_PORT}")
    pool = await get_pool()
    # Create tables if not exist
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS netflix_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                avatar_url VARCHAR(500),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS watch_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES netflix_users(id),
                content_id INTEGER NOT NULL,
                title VARCHAR(255),
                progress_percent FLOAT DEFAULT 0.0,
                watched_at TIMESTAMP DEFAULT NOW()
            )
        ''')
        # Seed demo users if they don't exist
        existing = await conn.fetchval("SELECT COUNT(*) FROM netflix_users")
        if existing == 0:
            demo_users = [
                ("user1@netflix.com", "sentinels123", "Ayush Demo"),
                ("user2@netflix.com", "sentinels123", "Demo User 2"),
                ("user3@netflix.com", "sentinels123", "Demo User 3"),
                ("user4@netflix.com", "sentinels123", "Demo User 4"),
                ("user5@netflix.com", "sentinels123", "Demo User 5"),
            ]
            for email, pwd, name in demo_users:
                hashed = pwd_context.hash(pwd)
                await conn.execute(
                    "INSERT INTO netflix_users (email, password_hash, display_name) VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                    email, hashed, name
                )
            logger.info(f"Seeded {len(demo_users)} demo users")
    
    yield
    
    if db_pool:
        await db_pool.close()
    logger.info(f"{SERVICE_NAME} shutting down")

# ─── FastAPI App ──────────────────────────────────────────────
app = FastAPI(
    title="NetflixOS User Service",
    version="2.0.0",
    description="User authentication, profile management, and watch history",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(metrics_middleware)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ─── Health Endpoints ─────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def ready():
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ready", "service": SERVICE_NAME}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not ready: {str(e)}")

# ─── Auth Endpoints ───────────────────────────────────────────
@app.post("/auth/register", response_model=TokenResponse)
async def register(user: UserRegister):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchval("SELECT id FROM netflix_users WHERE email = $1", user.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed = pwd_context.hash(user.password)
        row = await conn.fetchrow(
            """INSERT INTO netflix_users (email, password_hash, display_name) 
               VALUES ($1, $2, $3) RETURNING id, email, display_name, avatar_url, created_at""",
            user.email, hashed, user.display_name
        )
    
    token = create_access_token(row["id"], row["email"])
    return TokenResponse(
        access_token=token,
        user=UserProfile(
            id=row["id"],
            email=row["email"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            created_at=row["created_at"].isoformat()
        )
    )

@app.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, password_hash, display_name, avatar_url, created_at FROM netflix_users WHERE email = $1",
            credentials.email
        )
    
    if not row or not pwd_context.verify(credentials.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token(row["id"], row["email"])
    return TokenResponse(
        access_token=token,
        user=UserProfile(
            id=row["id"],
            email=row["email"],
            display_name=row["display_name"],
            avatar_url=row["avatar_url"],
            created_at=row["created_at"].isoformat()
        )
    )

# ─── Profile Endpoints ───────────────────────────────────────
@app.get("/profile", response_model=UserProfile)
async def get_profile(user: dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, display_name, avatar_url, created_at FROM netflix_users WHERE id = $1",
            user["user_id"]
        )
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(
        id=row["id"],
        email=row["email"],
        display_name=row["display_name"],
        avatar_url=row["avatar_url"],
        created_at=row["created_at"].isoformat()
    )

@app.put("/profile")
async def update_profile(display_name: str = None, avatar_url: str = None, user: dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if display_name:
            await conn.execute(
                "UPDATE netflix_users SET display_name = $1, updated_at = NOW() WHERE id = $2",
                display_name, user["user_id"]
            )
        if avatar_url:
            await conn.execute(
                "UPDATE netflix_users SET avatar_url = $1, updated_at = NOW() WHERE id = $2",
                avatar_url, user["user_id"]
            )
    return {"status": "updated"}

# ─── Watch History ────────────────────────────────────────────
@app.get("/watch-history", response_model=List[WatchHistoryEntry])
async def get_watch_history(user: dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT content_id, title, progress_percent, watched_at 
               FROM watch_history WHERE user_id = $1 
               ORDER BY watched_at DESC LIMIT 50""",
            user["user_id"]
        )
    return [
        WatchHistoryEntry(
            content_id=r["content_id"],
            title=r["title"] or "",
            watched_at=r["watched_at"].isoformat(),
            progress_percent=r["progress_percent"]
        ) for r in rows
    ]

@app.post("/watch-history")
async def add_watch_history(content_id: int, title: str = "", progress_percent: float = 0.0, user: dict = Depends(get_current_user)):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO watch_history (user_id, content_id, title, progress_percent)
               VALUES ($1, $2, $3, $4)""",
            user["user_id"], content_id, title, progress_percent
        )
    return {"status": "recorded"}

# ─── User validation endpoint (for other services) ───────────
@app.get("/validate-token")
async def validate_token(user: dict = Depends(get_current_user)):
    return {"valid": True, "user_id": user["user_id"], "email": user["email"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT)
