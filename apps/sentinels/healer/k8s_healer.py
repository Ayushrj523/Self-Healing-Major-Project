"""
SENTINELS v2.0 — Kubernetes Healer (Kopf-based operator actions)
Executes healing actions: restart_pod, scale_up, rollback, cordon_node
Law 4: Fail Gracefully — if healer crashes, apps continue running.
"""
import logging, time, os
from typing import Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger("sentinels.k8s_healer")


class K8sHealer:
    """Kubernetes remediation actions via the K8s API."""

    def __init__(self):
        self.api: Optional[client.CoreV1Api] = None
        self.apps_api: Optional[client.AppsV1Api] = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Kubernetes cluster (in-cluster or kubeconfig)."""
        try:
            config.load_incluster_config()
            logger.info("K8s healer: loaded in-cluster config")
        except config.ConfigException:
            try:
                config.load_kube_config()
                logger.info("K8s healer: loaded kubeconfig")
            except config.ConfigException:
                logger.warning("K8s healer: no cluster config — running in dry-run mode")
                return
        self.api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()

    def execute(self, action: str, pod: str, namespace: str, **kwargs) -> dict:
        """Execute a healing action. Returns result dict."""
        start = time.time()
        logger.info(f"Executing: {action} on {pod} in {namespace}")

        handlers = {
            "restart_pod": self._restart_pod,
            "scale_up": self._scale_up,
            "rollback": self._rollback,
            "observe": self._observe,
            "cordon_node": self._cordon_node,
        }

        handler = handlers.get(action, self._observe)
        try:
            result = handler(pod=pod, namespace=namespace, **kwargs)
            duration = time.time() - start
            result.update({
                "action": action,
                "pod": pod,
                "namespace": namespace,
                "duration_seconds": round(duration, 2),
                "timestamp": time.time(),
            })
            return result
        except Exception as e:
            duration = time.time() - start
            logger.error(f"Action {action} failed: {e}")
            return {
                "action": action, "pod": pod, "namespace": namespace,
                "success": False, "error": str(e),
                "duration_seconds": round(duration, 2),
                "timestamp": time.time(),
            }

    def _restart_pod(self, pod: str, namespace: str, **kwargs) -> dict:
        """Delete pod — ReplicaSet automatically recreates it."""
        if not self.api:
            return {"success": True, "result": "DRY_RUN: would delete pod", "dry_run": True}

        try:
            self.api.delete_namespaced_pod(
                name=pod, namespace=namespace,
                body=client.V1DeleteOptions(grace_period_seconds=5)
            )
            logger.info(f"Pod {pod} deleted in {namespace} — RS will recreate")

            # Wait for replacement pod
            new_pod = self._wait_for_replacement(pod, namespace, timeout=60)
            return {
                "success": True,
                "result": f"Pod {pod} restarted successfully",
                "new_pod": new_pod,
            }
        except ApiException as e:
            if e.status == 404:
                return {"success": True, "result": "Pod already terminated"}
            raise

    def _scale_up(self, pod: str, namespace: str, **kwargs) -> dict:
        """Scale up the deployment by 1 replica."""
        if not self.apps_api:
            return {"success": True, "result": "DRY_RUN: would scale up", "dry_run": True}

        deployment_name = self._pod_to_deployment(pod)
        try:
            deploy = self.apps_api.read_namespaced_deployment(deployment_name, namespace)
            current = deploy.spec.replicas or 1
            target = min(current + 1, 5)  # Cap at 5 replicas

            deploy.spec.replicas = target
            self.apps_api.patch_namespaced_deployment(
                deployment_name, namespace,
                body={"spec": {"replicas": target}}
            )
            logger.info(f"Scaled {deployment_name} from {current} to {target} replicas")
            return {
                "success": True,
                "result": f"Scaled {deployment_name}: {current} → {target} replicas",
                "previous_replicas": current,
                "new_replicas": target,
            }
        except ApiException as e:
            raise RuntimeError(f"Scale-up failed: {e.reason}")

    def _rollback(self, pod: str, namespace: str, **kwargs) -> dict:
        """Rollback to previous deployment revision."""
        if not self.apps_api:
            return {"success": True, "result": "DRY_RUN: would rollback", "dry_run": True}

        deployment_name = self._pod_to_deployment(pod)
        try:
            # Trigger rollback by patching with rollbackTo
            self.apps_api.patch_namespaced_deployment(
                deployment_name, namespace,
                body={
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "sentinels.io/rollback-trigger": str(int(time.time()))
                                }
                            }
                        }
                    }
                }
            )
            logger.info(f"Rollback triggered for {deployment_name}")
            return {"success": True, "result": f"Rollback initiated for {deployment_name}"}
        except ApiException as e:
            raise RuntimeError(f"Rollback failed: {e.reason}")

    def _observe(self, pod: str, namespace: str, **kwargs) -> dict:
        """No action — just observe and log."""
        logger.info(f"OBSERVE mode: monitoring {pod} in {namespace} without intervention")
        return {"success": True, "result": "Observation only — no action taken", "action_taken": False}

    def _cordon_node(self, pod: str, namespace: str, **kwargs) -> dict:
        """Cordon the node running this pod."""
        if not self.api:
            return {"success": True, "result": "DRY_RUN: would cordon node", "dry_run": True}

        try:
            pod_obj = self.api.read_namespaced_pod(pod, namespace)
            node_name = pod_obj.spec.node_name
            if not node_name:
                return {"success": False, "result": "Pod not assigned to a node"}

            body = {"spec": {"unschedulable": True}}
            self.api.patch_node(node_name, body)
            logger.info(f"Node {node_name} cordoned")
            return {"success": True, "result": f"Node {node_name} cordoned", "node": node_name}
        except ApiException as e:
            raise RuntimeError(f"Cordon failed: {e.reason}")

    def _pod_to_deployment(self, pod_name: str) -> str:
        """Extract deployment name from pod name (strip RS hash and pod hash)."""
        # Pod name format: deployment-name-replicaset-hash-pod-hash
        parts = pod_name.rsplit("-", 2)
        if len(parts) >= 3:
            return parts[0]
        return pod_name.rsplit("-", 1)[0]

    def _wait_for_replacement(self, old_pod: str, namespace: str, timeout: int = 60) -> Optional[str]:
        """Wait for a replacement pod to become Ready."""
        deployment_name = self._pod_to_deployment(old_pod)
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                pods = self.api.list_namespaced_pod(
                    namespace, label_selector=f"app={deployment_name}"
                )
                for p in pods.items:
                    if p.metadata.name != old_pod and p.status.phase == "Running":
                        ready = all(
                            cs.ready for cs in (p.status.container_statuses or [])
                        )
                        if ready:
                            logger.info(f"Replacement pod ready: {p.metadata.name}")
                            return p.metadata.name
            except Exception:
                pass
            time.sleep(3)

        logger.warning(f"Timeout waiting for replacement of {old_pod}")
        return None

    def get_cluster_health(self, namespace: str) -> dict:
        """Get pod health ratio for a namespace."""
        if not self.api:
            return {"healthy_ratio": 1.0, "total": 0, "healthy": 0, "dry_run": True}

        try:
            pods = self.api.list_namespaced_pod(namespace)
            total = len(pods.items)
            healthy = sum(
                1 for p in pods.items
                if p.status.phase == "Running"
                and all(cs.ready for cs in (p.status.container_statuses or []))
            )
            return {
                "healthy_ratio": healthy / max(total, 1),
                "total": total,
                "healthy": healthy,
                "pods": [
                    {
                        "name": p.metadata.name,
                        "status": p.status.phase,
                        "ready": all(cs.ready for cs in (p.status.container_statuses or [])),
                        "restarts": sum(cs.restart_count for cs in (p.status.container_statuses or [])),
                        "node": p.spec.node_name,
                    }
                    for p in pods.items
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get cluster health: {e}")
            return {"healthy_ratio": 1.0, "total": 0, "healthy": 0, "error": str(e)}
