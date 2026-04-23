"""
SENTINELS v2.0 — OPA Policy Engine Client
Queries OPA server for healing action decisions based on anomaly context.
Falls back to local policy evaluation if OPA server is unavailable.
"""
import logging, json, os
from typing import Optional
import httpx

logger = logging.getLogger("sentinels.policy")

# ─── Local Fallback Policies (when OPA server unavailable) ────
LOCAL_POLICIES = {
    "high_cpu": {
        "critical": {"action": "restart_pod", "escalation": "scale_up", "cooldown_seconds": 120},
        "warning": {"action": "observe", "escalation": "restart_pod", "cooldown_seconds": 60},
    },
    "high_memory": {
        "critical": {"action": "restart_pod", "escalation": "scale_up", "cooldown_seconds": 120},
        "warning": {"action": "observe", "escalation": "restart_pod", "cooldown_seconds": 60},
    },
    "crash_loop": {
        "critical": {"action": "rollback", "escalation": "cordon_node", "cooldown_seconds": 300},
        "warning": {"action": "restart_pod", "escalation": "rollback", "cooldown_seconds": 180},
    },
    "high_error_rate": {
        "critical": {"action": "restart_pod", "escalation": "scale_up", "cooldown_seconds": 90},
        "warning": {"action": "observe", "escalation": "restart_pod", "cooldown_seconds": 60},
    },
    "high_latency": {
        "critical": {"action": "scale_up", "escalation": "restart_pod", "cooldown_seconds": 180},
        "warning": {"action": "observe", "escalation": "scale_up", "cooldown_seconds": 120},
    },
    "traffic_spike": {
        "critical": {"action": "scale_up", "escalation": "rate_limit", "cooldown_seconds": 60},
        "warning": {"action": "scale_up", "escalation": None, "cooldown_seconds": 60},
    },
    "unknown_anomaly": {
        "critical": {"action": "restart_pod", "escalation": "observe", "cooldown_seconds": 180},
        "warning": {"action": "observe", "escalation": "restart_pod", "cooldown_seconds": 120},
    },
}


class PolicyEngine:
    """OPA-backed policy engine with local fallback."""

    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = os.getenv("OPA_URL", opa_url)
        self.opa_available = False
        self.policy_path = "/v1/data/sentinels/healing"
        self._check_opa()

    def _check_opa(self) -> None:
        """Check if OPA server is reachable."""
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self.opa_url}/health")
                self.opa_available = resp.status_code == 200
        except Exception:
            self.opa_available = False
        logger.info(f"OPA server {'available' if self.opa_available else 'unavailable — using local policies'}")

    def evaluate(self, context: dict) -> dict:
        """
        Evaluate policy for a given anomaly context.
        
        context: {
            anomaly_type: str, severity: str, anomaly_score: float,
            namespace: str, pod: str, duration_minutes: float,
            restart_count: int, healthy_ratio: float
        }
        """
        # Try OPA first
        if self.opa_available:
            result = self._query_opa(context)
            if result:
                return result

        # Fallback to local policies
        return self._evaluate_local(context)

    def _query_opa(self, context: dict) -> Optional[dict]:
        """Query OPA server for policy decision."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(
                    f"{self.opa_url}{self.policy_path}",
                    json={"input": context}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("result", {})
                    if result:
                        logger.info(f"OPA decision: {result.get('action', 'unknown')} | "
                                     f"reason: {result.get('reason', 'N/A')}")
                        return result
        except Exception as e:
            logger.warning(f"OPA query failed: {e} — falling back to local policies")
            self.opa_available = False
        return None

    def _evaluate_local(self, context: dict) -> dict:
        """Local policy evaluation — deterministic rule matching."""
        anomaly_type = context.get("anomaly_type", "unknown_anomaly")
        severity = context.get("severity", "warning")
        score = context.get("anomaly_score", 0.0)
        namespace = context.get("namespace", "unknown")
        healthy_ratio = context.get("healthy_ratio", 1.0)
        restart_count = context.get("restart_count", 0)

        # Get base policy
        type_policies = LOCAL_POLICIES.get(anomaly_type, LOCAL_POLICIES["unknown_anomaly"])
        policy = type_policies.get(severity, type_policies["warning"])

        action = policy["action"]
        escalation = policy.get("escalation")
        cooldown = policy["cooldown_seconds"]

        # Apply blast radius safety: if healthy ratio < 50%, reduce aggression
        if healthy_ratio < 0.50:
            logger.warning(f"Blast radius check: only {healthy_ratio*100:.0f}% pods healthy — "
                           f"reducing aggression from {action} to observe")
            action = "observe"
            cooldown = 300  # Long cooldown to prevent cascade

        # Monolith special handling: PrimeOS only has 1 pod, be more careful
        if namespace == "prime":
            if action == "restart_pod":
                cooldown = max(cooldown, 300)  # 5 min minimum for monolith
            logger.info(f"Monolith detected ({namespace}) — extended cooldown to {cooldown}s")

        # Build explainable reason
        reason = (
            f"Policy decision for {anomaly_type} ({severity}): "
            f"action={action} | "
            f"anomaly_score={score:.4f} | "
            f"namespace={namespace} | "
            f"healthy_ratio={healthy_ratio:.0%} | "
            f"restart_count={restart_count} | "
            f"cooldown={cooldown}s"
        )

        result = {
            "action": action,
            "escalation": escalation,
            "cooldown_seconds": cooldown,
            "reason": reason,
            "policy_source": "opa" if self.opa_available else "local_fallback",
            "policy_id": f"{anomaly_type}_{severity}",
            "severity": severity,
        }

        logger.info(f"Policy: {action} for {anomaly_type}/{severity} in {namespace} "
                     f"(cooldown={cooldown}s, escalation={escalation})")
        return result

    def get_policies(self) -> dict:
        """Return all current policies for dashboard display."""
        return {
            "source": "opa" if self.opa_available else "local_fallback",
            "opa_url": self.opa_url,
            "opa_available": self.opa_available,
            "policies": LOCAL_POLICIES
        }
