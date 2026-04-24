#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# SENTINELS v2.0 — Database Creation Script
# Runs BEFORE SQL scripts (Docker sorts .sh before .sql)
# sentinels_db is created by POSTGRES_DB env var already
# ═══════════════════════════════════════════════════════════════
set -e

echo "╔══════════════════════════════════════════╗"
echo "║  SENTINELS v2.0 — Creating databases...  ║"
echo "╚══════════════════════════════════════════╝"

# IMPORTANT: Must connect to a known database. The POSTGRES_DB
# (sentinels_db) is guaranteed to exist. Without -d, psql tries
# to connect to a database named after POSTGRES_USER ("sentinels")
# which does NOT exist, causing FATAL errors.
PGDB="${POSTGRES_DB:-sentinels_db}"

# Create netflix_db if it doesn't exist
if ! psql -U "$POSTGRES_USER" -d "$PGDB" -tc "SELECT 1 FROM pg_database WHERE datname = 'netflix_db'" | grep -q 1; then
    echo "Creating netflix_db..."
    psql -U "$POSTGRES_USER" -d "$PGDB" -c "CREATE DATABASE netflix_db OWNER $POSTGRES_USER;"
    echo "  ✓ netflix_db created"
else
    echo "  • netflix_db already exists"
fi

# Create prime_db if it doesn't exist
if ! psql -U "$POSTGRES_USER" -d "$PGDB" -tc "SELECT 1 FROM pg_database WHERE datname = 'prime_db'" | grep -q 1; then
    echo "Creating prime_db..."
    psql -U "$POSTGRES_USER" -d "$PGDB" -c "CREATE DATABASE prime_db OWNER $POSTGRES_USER;"
    echo "  ✓ prime_db created"
else
    echo "  • prime_db already exists"
fi

# Grant privileges
psql -U "$POSTGRES_USER" -d "$PGDB" -c "GRANT ALL PRIVILEGES ON DATABASE netflix_db TO $POSTGRES_USER;"
psql -U "$POSTGRES_USER" -d "$PGDB" -c "GRANT ALL PRIVILEGES ON DATABASE prime_db TO $POSTGRES_USER;"
psql -U "$POSTGRES_USER" -d "$PGDB" -c "GRANT ALL PRIVILEGES ON DATABASE sentinels_db TO $POSTGRES_USER;"

echo ""
echo "All databases ready:"
psql -U "$POSTGRES_USER" -d "$PGDB" -c "\l" | grep -E "netflix_db|prime_db|sentinels_db"
echo ""
