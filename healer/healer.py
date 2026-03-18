import time
import requests
import docker
import numpy as np
import subprocess
from sklearn.ensemble import IsolationForest

DOCKER_CONTAINER_NAME = "patient_netflix"
TARGET_APP_URL = "http://patient:5000/"
DASHBOARD_API_URL = "http://dashboard:8080/api/telemetry"
NGINX_CONTAINER_NAME = "sentinel_nginx"
NGINX_CONF_PATH = "/etc/sentinel_nginx/nginx_dynamic.conf"

# Smart Scaling Config
MAX_REPLICAS = 3
MIN_REPLICAS = 1
CPU_SCALE_UP = 80.0
CPU_SCALE_DOWN = 30.0
active_replicas = {}

# Rollback Config
STABLE_IMAGE_TAG = "sentinels_patient_stable"
FAILURE_THRESHOLD = 5
consecutive_failures = 0
rollback_in_progress = False

# Traffic Rerouting Config
rerouting_active = False

print("[SYSTEM] Booting Sentinel Watchdog...", flush=True)

try:
    client = docker.from_env()
    print("[SYSTEM] Successfully connected to Docker Daemon.", flush=True)
except Exception as e:
    print(f"[SYSTEM ERROR] Could not connect to Docker: {e}", flush=True)
    exit(1)

X_train = np.array([[1.0, 10.0], [2.0, 15.0], [1.5, 12.0], [3.0, 20.0], [0.5, 8.0]])
model = IsolationForest(contamination=0.1, random_state=42)
model.fit(X_train)

def push_telemetry(cpu, mem, lat, status, c_state, msg=None):
    payload = {
        "cpu": cpu or 0,
        "memory": mem or 0,
        "latency": lat or 0,
        "status": status,
        "container_state": c_state,
        "log_msg": msg
    }
    try:
        requests.post(DASHBOARD_API_URL, json=payload, timeout=2)
    except requests.exceptions.RequestException:
        pass

def getContainerMetrics():
    try:
        container = client.containers.get(DOCKER_CONTAINER_NAME)
        stats = container.stats(stream=False)
        c_state = container.status
        cpu_percent = 0.0
        try:
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            sys_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            if 'online_cpus' in stats['cpu_stats']:
                cpus = stats['cpu_stats']['online_cpus']
            elif 'percpu_usage' in stats['cpu_stats']['cpu_usage']:
                cpus = len(stats['cpu_stats']['cpu_usage']['percpu_usage'])
            else:
                cpus = 1
            if sys_delta > 0.0 and cpu_delta > 0.0:
                cpu_percent = (cpu_delta / sys_delta) * cpus * 100.0
        except KeyError:
            pass
        try:
            mem_mb = stats['memory_stats']['usage'] / (1024 * 1024)
        except KeyError:
            mem_mb = 0.0
        return cpu_percent, mem_mb, c_state, container
    except docker.errors.NotFound:
        return None, None, "dead", None
    except Exception:
        return None, None, "error", None

def getHttpMetrics():
    start_time = time.time()
    try:
        response = requests.get(TARGET_APP_URL + "health_check", timeout=5)
        latency = (time.time() - start_time) * 1000
        return response.status_code, latency
    except requests.exceptions.RequestException:
        return 500, (time.time() - start_time) * 1000

# ─────────────────────────────────────────────
#  SMART SCALING
# ─────────────────────────────────────────────
def get_replica_count():
    return len(active_replicas)

def scale_up():
    current = get_replica_count()
    if current >= (MAX_REPLICAS - 1):
        msg = f"[SCALER] Already at max replicas ({MAX_REPLICAS}). Cannot scale further."
        print(msg, flush=True)
        push_telemetry(None, None, None, 200, "running", msg)
        return
    replica_name = f"patient_netflix_replica_{current + 1}"
    msg = f"[SCALER] CPU overload detected! Spinning up new replica: {replica_name}"
    print(msg, flush=True)
    push_telemetry(None, None, None, 200, "scaling", msg)
    try:
        original = client.containers.get(DOCKER_CONTAINER_NAME)
        image = original.image
        replica = client.containers.run(
            image=image,
            name=replica_name,
            detach=True,
            network="self-healing-major-project_sentinel_net",
            environment={"FLASK_ENV": "production"},
            labels={"role": "replica", "managed_by": "sentinel_healer"}
        )
        active_replicas[replica_name] = replica
        msg2 = f"[SCALER] ✅ Replica '{replica_name}' is UP. Total instances: {1 + get_replica_count()}"
        print(msg2, flush=True)
        push_telemetry(None, None, None, 200, "running", msg2)
        # Add replica to nginx routing
        reroute_to_replica(replica_name)
    except Exception as e:
        err = f"[SCALER ERROR] Failed to spin up replica: {e}"
        print(err, flush=True)
        push_telemetry(None, None, None, 500, "error", err)

def scale_down():
    if not active_replicas:
        return
    replica_name, replica = list(active_replicas.items())[-1]
    msg = f"[SCALER] Load normalized. Scaling down — removing '{replica_name}'"
    print(msg, flush=True)
    push_telemetry(None, None, None, 200, "running", msg)
    try:
        replica.stop()
        replica.remove()
        del active_replicas[replica_name]
        msg2 = f"[SCALER] ✅ Replica removed. Total instances: {1 + get_replica_count()}"
        print(msg2, flush=True)
        push_telemetry(None, None, None, 200, "running", msg2)
        # Update nginx after scale down
        restore_primary_routing()
    except Exception as e:
        err = f"[SCALER ERROR] Failed to remove replica: {e}"
        print(err, flush=True)
        push_telemetry(None, None, None, 500, "error", err)

# ─────────────────────────────────────────────
#  ROLLBACK
# ─────────────────────────────────────────────
def snapshot_stable_image():
    try:
        container = client.containers.get(DOCKER_CONTAINER_NAME)
        image = container.image
        image.tag(STABLE_IMAGE_TAG, tag="latest")
        msg = f"[ROLLBACK] ✅ Stable image snapshot saved as '{STABLE_IMAGE_TAG}'"
        print(msg, flush=True)
        push_telemetry(None, None, None, 200, "running", msg)
    except Exception as e:
        print(f"[ROLLBACK] Warning: Could not snapshot stable image: {e}", flush=True)

def rollback():
    global rollback_in_progress, consecutive_failures
    if rollback_in_progress:
        return
    rollback_in_progress = True
    msg1 = f"[ROLLBACK] 🚨 Bad deployment detected! {FAILURE_THRESHOLD} consecutive failures. Initiating rollback..."
    print(msg1, flush=True)
    push_telemetry(None, None, None, 500, "rolling_back", msg1)
    time.sleep(15)
    try:
        try:
            stable_image = client.images.get(f"{STABLE_IMAGE_TAG}:latest")
        except docker.errors.ImageNotFound:
            msg_err = "[ROLLBACK] ❌ No stable image found! Falling back to restart."
            print(msg_err, flush=True)
            push_telemetry(None, None, None, 500, "error", msg_err)
            container = client.containers.get(DOCKER_CONTAINER_NAME)
            container.restart()
            rollback_in_progress = False
            consecutive_failures = 0
            return
        msg2 = "[ROLLBACK] Stopping bad deployment..."
        print(msg2, flush=True)
        push_telemetry(None, None, None, 500, "rolling_back", msg2)
        try:
            bad_container = client.containers.get(DOCKER_CONTAINER_NAME)
            bad_container.stop()
            bad_container.remove()
        except Exception:
            pass
        msg3 = f"[ROLLBACK] Redeploying from stable image '{STABLE_IMAGE_TAG}'..."
        print(msg3, flush=True)
        push_telemetry(None, None, None, 500, "rolling_back", msg3)
        client.containers.run(
            image=stable_image,
            name=DOCKER_CONTAINER_NAME,
            detach=True,
            ports={"5000/tcp": 5000},
            network="self-healing-major-project_sentinel_net",
            restart_policy={"Name": "unless-stopped"},
            labels={"managed_by": "sentinel_healer", "role": "primary"}
        )
        msg4 = "[ROLLBACK] ✅ Rollback complete! System restored to last stable version."
        print(msg4, flush=True)
        push_telemetry(None, None, None, 200, "running", msg4)
        consecutive_failures = 0
        restore_primary_routing()
    except Exception as e:
        err = f"[ROLLBACK ERROR] Rollback failed: {e}"
        print(err, flush=True)
        push_telemetry(None, None, None, 500, "error", err)
    finally:
        rollback_in_progress = False

# ─────────────────────────────────────────────
#  TRAFFIC REROUTING — NEW ADDITION
# ─────────────────────────────────────────────
def reload_nginx():
    """Sends reload signal to Nginx container to apply new config."""
    try:
        nginx = client.containers.get(NGINX_CONTAINER_NAME)
        nginx.exec_run("nginx -s reload")
        print("[ROUTER] Nginx reloaded with new routing config.", flush=True)
    except Exception as e:
        print(f"[ROUTER ERROR] Could not reload Nginx: {e}", flush=True)

def reroute_to_replica(replica_name):
    """
    When primary is sick or under load, adds replica to Nginx upstream.
    Traffic gets distributed between primary and replica.
    """
    global rerouting_active
    try:
        # Get replica container IP
        replica = client.containers.get(replica_name)
        networks = replica.attrs['NetworkSettings']['Networks']
        replica_ip = list(networks.values())[0]['IPAddress']

        # Write dynamic nginx config to include replica
        config = f"""
# Auto-generated by Sentinel Healer — Traffic Rerouting Active
upstream sentinels_backend {{
    server patient:5000;
    server {replica_ip}:5000;
}}
"""
        with open(NGINX_CONF_PATH, 'w') as f:
            f.write(config)

        reload_nginx()
        rerouting_active = True

        msg = f"[ROUTER] 🔀 Traffic rerouting ACTIVE — distributing load to '{replica_name}' ({replica_ip})"
        print(msg, flush=True)
        push_telemetry(None, None, None, 200, "rerouting", msg)

    except Exception as e:
        err = f"[ROUTER ERROR] Failed to reroute traffic: {e}"
        print(err, flush=True)
        push_telemetry(None, None, None, 500, "error", err)

def reroute_away_from_primary():
    """
    When primary is completely sick (crash/high latency),
    routes ALL traffic to healthy replicas only.
    """
    global rerouting_active

    if not active_replicas:
        msg = "[ROUTER] ⚠️ No healthy replicas available for rerouting!"
        print(msg, flush=True)
        push_telemetry(None, None, None, 500, "error", msg)
        return

    try:
        # Build upstream with only healthy replicas
        upstream_servers = ""
        for replica_name in active_replicas:
            replica = client.containers.get(replica_name)
            networks = replica.attrs['NetworkSettings']['Networks']
            replica_ip = list(networks.values())[0]['IPAddress']
            upstream_servers += f"    server {replica_ip}:5000;\n"

        config = f"""
# Auto-generated by Sentinel Healer — PRIMARY DOWN, rerouting to replicas
upstream sentinels_backend {{
{upstream_servers}}}
"""
        with open(NGINX_CONF_PATH, 'w') as f:
            f.write(config)

        reload_nginx()
        rerouting_active = True

        msg = f"[ROUTER] 🚨 Primary DOWN! Rerouting ALL traffic to {len(active_replicas)} healthy replica(s)."
        print(msg, flush=True)
        push_telemetry(None, None, None, 200, "rerouting", msg)

    except Exception as e:
        err = f"[ROUTER ERROR] Rerouting failed: {e}"
        print(err, flush=True)
        push_telemetry(None, None, None, 500, "error", err)

def restore_primary_routing():
    """Restores normal routing back to primary when it's healthy again."""
    global rerouting_active
    try:
        config = """
# Auto-generated by Sentinel Healer — Normal routing restored
upstream sentinels_backend {
    server patient:5000;
}
"""
        with open(NGINX_CONF_PATH, 'w') as f:
            f.write(config)

        reload_nginx()
        rerouting_active = False

        msg = "[ROUTER] ✅ Primary healthy — normal routing restored."
        print(msg, flush=True)
        push_telemetry(None, None, None, 200, "running", msg)

    except Exception as e:
        err = f"[ROUTER ERROR] Could not restore routing: {e}"
        print(err, flush=True)

# ─────────────────────────────────────────────
#  HEAL FUNCTION
# ─────────────────────────────────────────────
def heal(container, issue):
    msg1 = f"[CRITICAL] Neural Net detected {issue}. Pending Analysis..."
    print(msg1, flush=True)
    push_telemetry(None, None, None, 500, "healing_wait", msg1)

    # Reroute traffic away from sick primary immediately
    if active_replicas:
        reroute_away_from_primary()

    time.sleep(15)
    try:
        if issue in ["Crash", "High Latency"]:
            msg2 = f"[HEALER] Action Execution: Restarting '{DOCKER_CONTAINER_NAME}'"
            print(msg2, flush=True)
            push_telemetry(None, None, None, 500, "restarting", msg2)
            container.restart()
        else:
            msg2 = f"[HEALER] Action Execution: Target Redeploy (Stop/Start)"
            print(msg2, flush=True)
            push_telemetry(None, None, None, 500, "redeploying", msg2)
            container.stop()
            container.start()
        msg3 = "[SYSTEM] Remediation Applied. Calibrating internal sensors (5s delay)."
        print(msg3, flush=True)
        push_telemetry(None, None, None, 200, "running", msg3)
        time.sleep(5)
        # Restore normal routing after healing
        restore_primary_routing()
    except Exception as e:
        msgErr = f"[ERROR] Healing failed: {e}"
        print(msgErr, flush=True)
        push_telemetry(None, None, None, 500, "dead", msgErr)

# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def run():
    global consecutive_failures
    print("[SYSTEM] Monitoring Active.", flush=True)
    push_telemetry(0, 0, 0, 200, "waiting", "[SYSTEM] Healer Agent online and bound to Netflix Target.")
    time.sleep(20)
    snapshot_stable_image()
    scale_up_cooldown = 0

    while True:
        cpu, mem, c_state, container = getContainerMetrics()
        if not container:
            time.sleep(1)
            continue
        status_code, latency = getHttpMetrics()
        push_telemetry(cpu, mem, latency, status_code, c_state, None)
        issue_detected = None

        # Smart Scaling
        if cpu is not None:
            if cpu > CPU_SCALE_UP and scale_up_cooldown <= 0:
                scale_up()
                scale_up_cooldown = 30
            elif cpu < CPU_SCALE_DOWN and active_replicas:
                scale_down()
        if scale_up_cooldown > 0:
            scale_up_cooldown -= 1

        # Rollback check
        if status_code != 200:
            consecutive_failures += 1
            msg = f"[ROLLBACK MONITOR] Consecutive failures: {consecutive_failures}/{FAILURE_THRESHOLD}"
            print(msg, flush=True)
            if consecutive_failures >= FAILURE_THRESHOLD:
                rollback()
                time.sleep(10)
                continue
        else:
            consecutive_failures = 0

        # Crash / latency detection
        if latency > 5000 or status_code != 200:
            if status_code == 500 or status_code == 0:
                issue_detected = "Crash"
            else:
                issue_detected = "High Latency"

        if not issue_detected and cpu is not None and mem is not None:
            pred = model.predict([[cpu, mem]])
            if pred[0] == -1:
                if cpu > 80.0 or mem > 40.0:
                    issue_detected = "Resource Exhaustion"

        if issue_detected:
            heal(container, issue_detected)

        time.sleep(1)

if __name__ == "__main__":
    run()
