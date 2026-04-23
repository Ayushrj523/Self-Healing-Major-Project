-- ═══════════════════════════════════════════════════════════════
-- Demo Users — Seeded for all platforms
-- ═══════════════════════════════════════════════════════════════

-- Netflix demo users (password: sentinels123, bcrypt hash)
\connect netflix_db;
INSERT INTO netflix_users (email, password_hash, display_name, subscription_plan) VALUES
('user1@netflix.com', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOm3cYDu7TLgJDqI6W.w8vfY.qxGq8Kau', 'Ayush Demo', 'premium'),
('user2@netflix.com', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOm3cYDu7TLgJDqI6W.w8vfY.qxGq8Kau', 'Demo User 2', 'standard'),
('user3@netflix.com', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOm3cYDu7TLgJDqI6W.w8vfY.qxGq8Kau', 'Demo User 3', 'basic'),
('user4@netflix.com', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOm3cYDu7TLgJDqI6W.w8vfY.qxGq8Kau', 'Demo User 4', 'premium'),
('user5@netflix.com', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOm3cYDu7TLgJDqI6W.w8vfY.qxGq8Kau', 'Demo User 5', 'free')
ON CONFLICT (email) DO NOTHING;

-- Prime demo users
\connect prime_db;
INSERT INTO prime_users (email, password_hash, display_name, is_prime_member) VALUES
('user1@prime.com', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOm3cYDu7TLgJDqI6W.w8vfY.qxGq8Kau', 'Ayush Prime', TRUE),
('user2@prime.com', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOm3cYDu7TLgJDqI6W.w8vfY.qxGq8Kau', 'Prime User 2', TRUE),
('user3@prime.com', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOm3cYDu7TLgJDqI6W.w8vfY.qxGq8Kau', 'Prime User 3', FALSE)
ON CONFLICT (email) DO NOTHING;
