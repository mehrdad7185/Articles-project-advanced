# src/scheduler.py (Final, Synchronized Version)
# Comments are in English

from flask import Flask, jsonify, request
import time
import docker

app = Flask(__name__)

# --- Configuration ---
FOG_NODES = ['fog-node-1', 'fog-node-2']
RECOVERY_TIME_SECONDS = 30

# --- State Management ---
node_status = {
    node: {"status": "UP", "last_failure": 0, "cpu": 0.0, "memory": 0.0}
    for node in FOG_NODES
}

# --- Docker Client Initialization ---
try:
    client = docker.from_env()
    client.ping()
    DOCKER_AVAILABLE = True
    print("[INFO] Successfully connected to Docker daemon.")
except Exception as e:
    DOCKER_AVAILABLE = False
    print(f"[CRITICAL_ERROR] Could not connect to Docker daemon: {e}")

def update_all_node_statuses():
    """Updates the status and resource usage of all nodes."""
    if not DOCKER_AVAILABLE: return

    for node_name in FOG_NODES:
        try:
            is_in_recovery = (node_status[node_name]["status"] == "SUSPECTED" and
                              time.time() - node_status[node_name]["last_failure"] > RECOVERY_TIME_SECONDS)

            if node_status[node_name]["status"] == "UP" or is_in_recovery:
                container = client.containers.get(node_name)
                stats = container.stats(stream=False)
                
                # --- Robust CPU Calculation ---
                cpu_percent = 0.0
                cpu_stats = stats.get("cpu_stats", {})
                precpu_stats = stats.get("precpu_stats", {})
                cpu_usage = cpu_stats.get("cpu_usage", {})
                precpu_usage = precpu_stats.get("cpu_usage", {})
                cpu_delta = cpu_usage.get("total_usage", 0) - precpu_usage.get("total_usage", 0)
                system_cpu_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)
                online_cpus = cpu_stats.get("online_cpus", 1)

                if system_cpu_delta > 0 and cpu_delta > 0:
                    cpu_percent = (cpu_delta / system_cpu_delta) * online_cpus * 100.0
                
                # --- Memory Calculation ---
                memory_usage = stats.get("memory_stats", {}).get("usage", 0) / (1024 * 1024)
                
                if node_status[node_name]["status"] != "UP":
                    print(f"[HEALTH CHECK] Node '{node_name}' has recovered and is now UP.")
                
                node_status[node_name].update({
                    "status": "UP", "cpu": round(cpu_percent, 2), "memory": round(memory_usage, 2)
                })
        
        except (docker.errors.NotFound, KeyError):
            _mark_node_as_suspected(node_name)
        except Exception as e:
            print(f"[ERROR] Unexpected error for {node_name}: {e}")
            _mark_node_as_suspected(node_name)

@app.route('/get_fog_node', methods=['GET'])
def get_fog_node():
    update_all_node_statuses()
    active_nodes = {node: info for node, info in node_status.items() if info["status"] == "UP"}

    if not active_nodes:
        return jsonify({"error": "No active nodes"}), 503

    chosen_node = min(active_nodes, key=lambda node: active_nodes[node]['cpu'])
    # --- Standardized log format for easy parsing ---
    print(f"STATUS_UPDATE::{node_status}")
    return jsonify({"fog_node_host": chosen_node})

def _mark_node_as_suspected(node_name):
    if node_name in node_status and node_status[node_name]['status'] == 'UP':
        node_status[node_name]['status'] = 'SUSPECTED'
        node_status[node_name]['last_failure'] = time.time()
        print(f"[HEALTH CHECK] Node '{node_name}' is now SUSPECTED.")

@app.route('/report_failure', methods=['POST'])
def report_failure():
    failed_node = request.get_json().get('node')
    if failed_node: _mark_node_as_suspected(failed_node)
    return jsonify({"status": "acknowledged"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)