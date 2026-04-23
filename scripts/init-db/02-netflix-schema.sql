-- ═══════════════════════════════════════════════════════════════
-- Netflix Schema — Users, Content, Watch History, Payments
-- ═══════════════════════════════════════════════════════════════
\connect netflix_db;

CREATE TABLE IF NOT EXISTS netflix_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    subscription_plan VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS netflix_content (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    youtube_id VARCHAR(20) NOT NULL,
    thumbnail_url VARCHAR(500),
    release_year INTEGER,
    rating FLOAT DEFAULT 0.0,
    duration_minutes INTEGER DEFAULT 120,
    maturity_rating VARCHAR(10) DEFAULT 'PG-13',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS watch_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES netflix_users(id) ON DELETE CASCADE,
    content_id INTEGER REFERENCES netflix_content(id) ON DELETE CASCADE,
    title VARCHAR(255),
    progress_percent FLOAT DEFAULT 0.0,
    watched_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES netflix_users(id) ON DELETE CASCADE,
    plan VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'completed',
    transaction_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES netflix_users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_content_category ON netflix_content(category);
CREATE INDEX IF NOT EXISTS idx_watch_history_user ON watch_history(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
