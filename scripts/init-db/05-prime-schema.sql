-- ═══════════════════════════════════════════════════════════════
-- PrimeOS Schema — Monolith database (all-in-one)
-- ═══════════════════════════════════════════════════════════════
\connect prime_db;

CREATE TABLE IF NOT EXISTS prime_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    is_prime_member BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prime_content (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    youtube_id VARCHAR(20) NOT NULL,
    thumbnail_url VARCHAR(500),
    release_year INTEGER,
    rating FLOAT DEFAULT 0.0,
    is_prime_exclusive BOOLEAN DEFAULT FALSE,
    duration_minutes INTEGER DEFAULT 120,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prime_watch_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES prime_users(id) ON DELETE CASCADE,
    content_id INTEGER REFERENCES prime_content(id) ON DELETE CASCADE,
    progress_percent FLOAT DEFAULT 0.0,
    watched_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prime_content_category ON prime_content(category);
CREATE INDEX IF NOT EXISTS idx_prime_watch_user ON prime_watch_history(user_id);
