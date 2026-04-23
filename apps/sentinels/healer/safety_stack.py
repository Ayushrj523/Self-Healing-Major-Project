"""
SENTINELS v2.0 — Safety Stack
Circuit breakers, cooldown timers, blast radius controls, PDB checks.
Law 2: Safety Over Speed — these ALWAYS execute before any remediation action.
"""
import logging, time, json, os
from typing import Optional
import redis

logger = logging.getLogger("sentinels.safety")


class SafetyStack:
    """Circuit breaker + cooldown + blast radius controller using Redis state."""

    def __init__(self, redis_url: str = "redis://localhost:6379/3"):
        self.redis_url = os.getenv("REDIS_URL", redis_url)
        self.redis: Optional[redis.Redis] = None
        self._connect_redis()

        # Configuration
        self.circuit_breaker_threshold = 5  # failures before opening circuit
        self.circuit_breaker_reset_time = 300  # 5 min reset
        self.blast_radius_threshold = 0.75  # minimum healthy pod ratio
        self.max_concurrent_actions = 3
        self.default_cooldown = 120  # 2 min default

    def _connect_redis(self) -> None:
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            self.redis.ping()
            logger.info("Safety stack Redis connected")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e} — using in-memory fallback")
            self.redis = None
            self._memory_store: dict = {}

    def _get(self, key: str) -> Optional[str]:
        if self.redis:
            return self.redis.get(key)
        return self._memory_store.get(key)

    def _set(self, key: str, value: str, ex: int = 0) -> None:
        if self.redis:
            if ex > 0:
                self.redis.setex(key, ex, value)
            else:
                self.redis.set(key, value)
        else:
            self._memory_store[key] = value

    def _incr(self, key: str) -> int:
        if self.redis:
            return self.redis.incr(key)
        val = int(self._memory_store.get(key, 0)) + 1
        self._memory_store[key] = str(val)
        return val

    def check_all(self, pod: str, namespace: str, action: str,
                  healthy_ratio: float = 1.0, cooldown_seconds: int = 120) -> dict:
        """
        Run ALL safety checks. Returns pass/fail with detailed reasons.
        ALL checks must pass for action to proceed.
        """
        checks = {}

        # 1. Circuit breaker
        cb = self._check_circuit_breaker(namespace)
        checks["circuit_breaker"] = cb

        # 2. Cooldown timer
        cd = self._check_cooldown(pod, cooldown_seconds)
        checks["cooldown"] = cd

        # 3. Blast radius
        br = self._check_blast_radius(namespace, healthy_ratio)
        checks["blast_radius"] = br

        # 4. Concurrent actions limit
        ca = self._check_concurrent_actions()
        checks["concurrent_actions"] = ca

        all_passed = all(c["passed"] for c in checks.values())
        blocked_by = [name for name, c in checks.items() if not c["passed"]]

        result = {
            "all_passed": all_passed,
            "checks": checks,
            "blocked_by": blocked_by,
            "action": action,
            "pod": pod,
            "namespace": namespace,
        }

        if all_passed:
            logger.info(f"Safety checks PASSED for {action} on {pod} in {namespace}")
        else:
            logger.warning(f"Safety checks BLOCKED: {blocked_by} — action {action} on {pod}")

        return result

    def record_action(self, pod: str, namespace: str, success: bool) -> None:
        """Record action outcome for circuit breaker and cooldown state."""
        now = str(int(time.time()))

        # Set cooldown
        cooldown_key = f"sentinels:cooldown:{pod}"
        self._set(cooldown_key, now, ex=300)

        # Update circuit breaker
        if not success:
            fail_key = f"sentinels:cb_failures:{namespace}"
            count = self._incr(fail_key)
            if self.redis:
                self.redis.expire(fail_key, self.circuit_breaker_reset_time)
            if count >= self.circuit_breaker_threshold:
                cb_key = f"sentinels:cb_open:{namespace}"
                self._set(cb_key, now, ex=self.circuit_breaker_reset_time)
                logger.warning(f"Circuit breaker OPENED for namespace {namespace} "
                               f"after {count} failures")
        else:
            # Success resets failure count
            fail_key = f"sentinels:cb_failures:{namespace}"
            self._set(fail_key, "0")

        # Track concurrent actions
        active_key = "sentinels:active_actions"
        if self.redis:
            self.redis.decr(active_key)

    def _check_circuit_breaker(self, namespace: str) -> dict:
        cb_key = f"sentinels:cb_open:{namespace}"
        is_open = self._get(cb_key) is not None
        return {
            "passed": not is_open,
            "state": "OPEN" if is_open else "CLOSED",
            "reason": f"Circuit breaker {'OPEN — too many recent failures' if is_open else 'CLOSED — operating normally'}"
        }

    def _check_cooldown(self, pod: str, cooldown_seconds: int) -> dict:
        cooldown_key = f"sentinels:cooldown:{pod}"
        last_action = self._get(cooldown_key)
        if last_action:
            elapsed = time.time() - int(last_action)
            if elapsed < cooldown_seconds:
                remaining = cooldown_seconds - elapsed
                return {
                    "passed": False,
                    "reason": f"Cooldown active — {remaining:.0f}s remaining (last action {elapsed:.0f}s ago)",
                    "remaining_seconds": remaining,
                }
        return {"passed": True, "reason": "No active cooldown", "remaining_seconds": 0}

    def _check_blast_radius(self, namespace: str, healthy_ratio: float) -> dict:
        passed = healthy_ratio >= self.blast_radius_threshold
        return {
            "passed": passed,
            "healthy_ratio": healthy_ratio,
            "threshold": self.blast_radius_threshold,
            "reason": f"Healthy ratio {healthy_ratio:.0%} {'≥' if passed else '<'} "
                      f"threshold {self.blast_radius_threshold:.0%}"
        }

    def _check_concurrent_actions(self) -> dict:
        active_key = "sentinels:active_actions"
        current = int(self._get(active_key) or "0")
        passed = current < self.max_concurrent_actions
        return {
            "passed": passed,
            "current": current,
            "max": self.max_concurrent_actions,
            "reason": f"{current}/{self.max_concurrent_actions} concurrent actions"
        }

    def get_status(self) -> dict:
        return {
            "redis_connected": self.redis is not None,
            "circuit_breaker_threshold": self.circuit_breaker_threshold,
            "blast_radius_threshold": self.blast_radius_threshold,
            "max_concurrent_actions": self.max_concurrent_actions,
        }
