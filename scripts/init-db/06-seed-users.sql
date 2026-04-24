-- ═══════════════════════════════════════════════════════════════
-- Demo Users — Seeded for PrimeOS only
-- Netflix users are seeded by the Python user-service on startup (bcrypt)
-- Prime users use SHA-256 hash to match the Django backend's hashlib.sha256()
-- 
-- Password: sentinels123
-- SHA-256:  8ef68686335429bf8090cb65f94da2abb5560e6b8100019582be47a88d086c37
-- Computed: python -c "import hashlib; print(hashlib.sha256(b'sentinels123').hexdigest())"
-- ═══════════════════════════════════════════════════════════════

-- ── DO NOT seed Netflix users here ──
-- The Python user-service seeds them on startup using bcrypt (passlib).
-- If we seed bcrypt hashes here, they might not match what passlib expects.
-- Let the service handle its own seeding — it's the source of truth.

-- ── Prime Users (SHA-256 hashed) ─────────────────────────────
\connect prime_db;

INSERT INTO prime_users (email, password_hash, display_name, is_prime_member) VALUES
('user1@prime.com', '8ef68686335429bf8090cb65f94da2abb5560e6b8100019582be47a88d086c37', 'Ayush Prime', TRUE),
('user2@prime.com', '8ef68686335429bf8090cb65f94da2abb5560e6b8100019582be47a88d086c37', 'Prime User 2', TRUE),
('user3@prime.com', '8ef68686335429bf8090cb65f94da2abb5560e6b8100019582be47a88d086c37', 'Prime User 3', TRUE),
('user4@prime.com', '8ef68686335429bf8090cb65f94da2abb5560e6b8100019582be47a88d086c37', 'Prime User 4', TRUE),
('user5@prime.com', '8ef68686335429bf8090cb65f94da2abb5560e6b8100019582be47a88d086c37', 'Prime User 5', FALSE)
ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash;
