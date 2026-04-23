# SENTINELS v2.0 — OPA Rego Policy
# Deterministic healing decisions based on anomaly context.
# Endpoint: /v1/data/sentinels/healing

package sentinels.healing

import rego.v1

# ─── Default Values ──────────────────────────────────────────
default action := "observe"
default cooldown_seconds := 120
default reason := "No matching policy — defaulting to observe"

# ─── HIGH CPU ────────────────────────────────────────────────
action := "restart_pod" if {
    input.anomaly_type == "high_cpu"
    input.severity == "critical"
    input.anomaly_score < -0.30
}

action := "observe" if {
    input.anomaly_type == "high_cpu"
    input.severity == "warning"
}

cooldown_seconds := 120 if {
    input.anomaly_type == "high_cpu"
    input.severity == "critical"
}

# ─── HIGH MEMORY ─────────────────────────────────────────────
action := "restart_pod" if {
    input.anomaly_type == "high_memory"
    input.severity == "critical"
    input.anomaly_score < -0.30
}

action := "observe" if {
    input.anomaly_type == "high_memory"
    input.severity == "warning"
}

cooldown_seconds := 120 if {
    input.anomaly_type == "high_memory"
}

# ─── CRASH LOOP ──────────────────────────────────────────────
action := "rollback" if {
    input.anomaly_type == "crash_loop"
    input.severity == "critical"
    input.restart_count > 5
}

action := "restart_pod" if {
    input.anomaly_type == "crash_loop"
    input.severity == "critical"
    input.restart_count <= 5
}

action := "restart_pod" if {
    input.anomaly_type == "crash_loop"
    input.severity == "warning"
}

cooldown_seconds := 300 if {
    input.anomaly_type == "crash_loop"
}

# ─── HIGH ERROR RATE ─────────────────────────────────────────
action := "restart_pod" if {
    input.anomaly_type == "high_error_rate"
    input.severity == "critical"
}

action := "observe" if {
    input.anomaly_type == "high_error_rate"
    input.severity == "warning"
}

cooldown_seconds := 90 if {
    input.anomaly_type == "high_error_rate"
}

# ─── TRAFFIC SPIKE ───────────────────────────────────────────
action := "scale_up" if {
    input.anomaly_type == "traffic_spike"
    input.severity == "critical"
}

action := "scale_up" if {
    input.anomaly_type == "traffic_spike"
    input.severity == "warning"
}

cooldown_seconds := 60 if {
    input.anomaly_type == "traffic_spike"
}

# ─── HIGH LATENCY ────────────────────────────────────────────
action := "scale_up" if {
    input.anomaly_type == "high_latency"
    input.severity == "critical"
}

action := "observe" if {
    input.anomaly_type == "high_latency"
    input.severity == "warning"
}

cooldown_seconds := 180 if {
    input.anomaly_type == "high_latency"
}

# ─── BLAST RADIUS SAFETY OVERRIDE ────────────────────────────
# If too many pods are unhealthy, force observation mode
action := "observe" if {
    input.healthy_ratio < 0.50
}

cooldown_seconds := 300 if {
    input.healthy_ratio < 0.50
}

# ─── MONOLITH PROTECTION ─────────────────────────────────────
# PrimeOS monolith gets extended cooldowns
cooldown_seconds := 300 if {
    input.namespace == "prime"
    action == "restart_pod"
}

# ─── EXPLAINABLE REASON ──────────────────────────────────────
reason := concat(" | ", [
    concat("", ["Policy: ", input.anomaly_type, "/", input.severity]),
    concat("", ["Action: ", action]),
    concat("", ["Score: ", format_int(input.anomaly_score * 10000, 10), "/10000"]),
    concat("", ["Cooldown: ", format_int(cooldown_seconds, 10), "s"]),
])
