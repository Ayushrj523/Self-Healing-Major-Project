"""
SENTINELS v2.0 — Integration Test Suite
Tests the full attack -> detect -> heal -> metrics pipeline.

Usage:
    cd E:\\Projects\\SENTINAL
    python -m pytest tests/integration/test_full_cycle.py -v
"""
import time
import pytest
import requests

HEALER_URL = "http://127.0.0.1:5000"
METRICS_URL = "http://127.0.0.1:5050"
TIMEOUT = 15


class TestFullHealingCycle:
    """End-to-end integration tests for the SENTINELS healing pipeline."""

    def test_healer_health(self):
        """Verify the healer agent is running and healthy."""
        resp = requests.get(f"{HEALER_URL}/health", timeout=TIMEOUT)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "operational"

    def test_metrics_health(self):
        """Verify the metrics aggregator is running and healthy."""
        resp = requests.get(f"{METRICS_URL}/health", timeout=TIMEOUT)
        assert resp.status_code == 200

    def test_simulate_cpu_attack(self):
        """Launch a CPU stress attack and verify healing."""
        resp = requests.post(f"{HEALER_URL}/api/simulate", json={
            "anomaly_type": "high_cpu",
            "namespace": "netflix",
            "pod": "api-gateway",
        }, timeout=TIMEOUT)
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == "healing_complete"
        assert data["result"] == "SUCCESS"
        assert data["recovery_time_ms"] > 0
        assert data["namespace"] == "netflix"

    def test_simulate_memory_attack(self):
        """Launch a memory pressure attack and verify healing."""
        resp = requests.post(f"{HEALER_URL}/api/simulate", json={
            "anomaly_type": "high_memory",
            "namespace": "netflix",
            "pod": "content-service",
        }, timeout=TIMEOUT)
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == "SUCCESS"
        assert "recovery_time_ms" in data

    def test_simulate_crash_loop(self):
        """Launch a crash loop attack on prime and verify healing."""
        resp = requests.post(f"{HEALER_URL}/api/simulate", json={
            "anomaly_type": "crash_loop",
            "namespace": "prime",
            "pod": "primeos-monolith",
        }, timeout=TIMEOUT)
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"] == "SUCCESS"

    def test_healing_log_populated(self):
        """Verify the healing log contains events after attacks."""
        resp = requests.get(f"{HEALER_URL}/api/healing-log", timeout=TIMEOUT)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_metrics_update_after_attacks(self):
        """Verify metrics aggregator reflects healing events."""
        # Wait for metrics aggregator to poll
        time.sleep(5)

        resp = requests.get(f"{METRICS_URL}/api/scores", timeout=TIMEOUT)
        assert resp.status_code == 200
        scores = resp.json()
        assert scores["total_healing_actions"] >= 1
        assert scores["f1_score"] > 0
        assert scores["recovery_rate"] > 0

    def test_full_cycle_detection_to_recovery(self):
        """Full cycle: attack, detect anomaly, execute policy, recover."""
        # Record initial state
        initial = requests.get(f"{METRICS_URL}/api/scores", timeout=TIMEOUT).json()
        initial_heals = initial.get("total_healing_actions", 0)

        # Launch attack
        attack = requests.post(f"{HEALER_URL}/api/simulate", json={
            "anomaly_type": "high_error_rate",
            "namespace": "netflix",
            "pod": "search-service",
        }, timeout=TIMEOUT)
        assert attack.status_code == 200
        event = attack.json()

        # Verify event structure
        assert "id" in event
        assert "timestamp" in event
        assert event["type"] == "healing_complete"
        assert event["policy_action"] in ["restart_pod", "scale_up", "cordon_node", "rollback_deployment"]
        assert event["anomaly_score"] is not None

        # Wait for metrics to update
        time.sleep(5)

        # Verify metrics incremented
        updated = requests.get(f"{METRICS_URL}/api/scores", timeout=TIMEOUT).json()
        assert updated["total_healing_actions"] >= initial_heals

    def test_multiple_namespace_attacks(self):
        """Verify attacks work across both netflix and prime namespaces."""
        for ns, pod in [("netflix", "user-service"), ("prime", "primeos-monolith")]:
            resp = requests.post(f"{HEALER_URL}/api/simulate", json={
                "anomaly_type": "high_cpu",
                "namespace": ns,
                "pod": pod,
            }, timeout=TIMEOUT)
            assert resp.status_code == 200
            assert resp.json()["namespace"] == ns


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
