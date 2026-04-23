-- ═══════════════════════════════════════════════════════════════
-- SENTINELS Schema — Healing Audit Log, Anomaly Records
-- ═══════════════════════════════════════════════════════════════
\connect sentinels_db;

CREATE TABLE IF NOT EXISTS healing_audit_log (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(100) UNIQUE NOT NULL,
    alert_name VARCHAR(100) NOT NULL,
    pod_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(100) NOT NULL,
    anomaly_type VARCHAR(50),
    anomaly_score FLOAT,
    severity VARCHAR(20),
    action_taken VARCHAR(50),
    action_detail JSONB DEFAULT '{}',
    policy_id VARCHAR(100),
    policy_version VARCHAR(20),
    safety_checks_passed BOOLEAN DEFAULT TRUE,
    execution_success BOOLEAN,
    recovery_verified BOOLEAN,
    mttd_seconds FLOAT,
    mttr_seconds FLOAT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS anomaly_records (
    id SERIAL PRIMARY KEY,
    pod_name VARCHAR(255) NOT NULL,
    namespace VARCHAR(100) NOT NULL,
    anomaly_score FLOAT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    features JSONB DEFAULT '{}',
    is_true_positive BOOLEAN,
    chaos_experiment_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_healing_audit_created ON healing_audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_healing_audit_namespace ON healing_audit_log(namespace);
CREATE INDEX IF NOT EXISTS idx_anomaly_records_pod ON anomaly_records(pod_name);
CREATE INDEX IF NOT EXISTS idx_anomaly_records_created ON anomaly_records(created_at DESC);
