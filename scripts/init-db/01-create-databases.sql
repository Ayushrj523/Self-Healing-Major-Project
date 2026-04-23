-- ═══════════════════════════════════════════════════════════════
-- SENTINELS v2.0 — Database Initialization
-- Creates all 3 databases used by the platform
-- ═══════════════════════════════════════════════════════════════

-- Netflix database (used by Netflix microservices)
CREATE DATABASE netflix_db OWNER sentinels;

-- Prime database (used by PrimeOS monolith)
CREATE DATABASE prime_db OWNER sentinels;

-- Sentinels database (used by healer agent + metrics aggregator)
CREATE DATABASE sentinels_db OWNER sentinels;
