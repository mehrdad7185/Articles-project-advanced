
from flask import Flask, jsonify, request
import time
import docker

app = Flask(__name__)

# --- Configuration ---
FOG_NODES = ['fog-node-1', 'fog-node-2']
# Time in seconds before we try a 'SUSPECTED' node again
RECOVERY_TIME_SECONDS = 10
# The placement strategy. For the paper, you can test 'LEAST_CPU' or 'LEAST_RAM'
PLACEMENT_STRATEGY = 'LEAST_CPU' 

# --- State Management ---
# A single, comprehensive dictionary to track node status
node_status = {
    node: {"status": "UP", "last_failure": 0, "cpu": 0.0, "memory": 0.0}
    for node in FOG_NODES
}

# --- Docker Client Initialization ---
try:
    client = docker.from_env()
    client.ping() # Check connection
    DOCKER_AVAILABLE = True
    print("[INFO] Successfully connected to Docker daemon.")
except Exception as e:
    DOCKER_AVAILABLE = False
    print(f"[CRITICAL_ERROR] Could not connect to Docker daemon: {e}")
    print("[INFO] Docker not available. Health checks will be limited to failure reporting only.")


def update_node_stats():
   
    if not DOCKER_AVAILABLE:
        return

    for node_name in FOG_NODES:
        # We only need to get stats for nodes that are considered UP
        if node_status[node_name]["status"] == "UP":
            try:
                container = client.containers.get(node_name)
                stats = container.stats(stream=False)
                
                # --- CPU Calculation ---
                cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                cpu_percent = 0.0
                if system_cpu_delta > 0 and cpu_delta > 0:
                    cpu_percent = (cpu_delta / system_cpu_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100.0
                
                # --- Memory Calculation ---
                memory_usage = stats["memory_stats"]["usage"] / (1024 * 1024) # in MB

                node_status[node_name].update({"cpu": round(cpu_percent, 2), "memory": round(memory_usage, 2)})

            except docker.errors.NotFound:
                # If a container is not found, it has failed. Report it.
                print(f"[HEALTH CHECK] Node '{node_name}' not found during stat update. Marking as SUSPECTED.")
                _mark_node_as_suspected(node_name)
            except Exception as e:
                print(f"[ERROR] Could not get stats for {node_name}: {e}")
                _mark_node_as_suspected(node_name)

@app.route('/get_fog_node', methods=['GET'])
def get_fog_node():
    """
    The main placement endpoint. It combines health checks and resource-based placement.
    """
    # 1. Check if any suspected nodes are ready for recovery
    for node, info in node_status.items():
        if info["status"] == "SUSPECTED" and time.time() - info["last_failure"] > RECOVERY_TIME_SECONDS:
            info["status"] = "UP"
            print(f"[HEALTH CHECK] Node '{node}' recovery period is over. Marking as UP.")

    # 2. Get the latest resource stats from Docker
    update_node_stats()

    # 3. Filter for nodes that are currently marked as "UP"
    active_nodes = {node: info for node, info in node_status.items() if info["status"] == "UP"}

    if not active_nodes:
        return jsonify({"error": "No active fog nodes available"}), 503

    # 4. Choose placement based on the selected strategy
    if PLACEMENT_STRATEGY == 'LEAST_CPU':
        chosen_node = min(active_nodes, key=lambda node: active_nodes[node]['cpu'])
    elif PLACEMENT_STRATEGY == 'LEAST_RAM':
        chosen_node = min(active_nodes, key=lambda node: active_nodes[node]['memory'])
    else: # Fallback to a simple round-robin style if strategy is unknown
        chosen_node = min(active_nodes.items(), key=lambda item: item[1].get('connections', 0))[0]

    status_str = ", ".join([
        f"'{n}': {{'cpu': {s['cpu']}%, 'mem': {s['memory']}MB, 'status': '{s['status']}'}}"
        for n, s in node_status.items()
    ])
    print(f"Status: {{{status_str}}}. Strategy: {PLACEMENT_STRATEGY}. Chosen: '{chosen_node}'")
    
    return jsonify({"fog_node_host": chosen_node})

def _mark_node_as_suspected(node_name):
    """A helper function to mark a node as suspected."""
    if node_name in node_status and node_status[node_name]['status'] == 'UP':
        node_status[node_name]['status'] = 'SUSPECTED'
        node_status[node_name]['last_failure'] = time.time()

@app.route('/report_failure', methods=['POST'])
def report_failure():
    """Endpoint for devices to report a connection failure."""
    data = request.get_json()
    failed_node = data.get('node')
    if failed_node:
        print(f"[HEALTH CHECK] Received failure report for node '{failed_node}'.")
        _mark_node_as_suspected(failed_node)
    return jsonify({"status": "acknowledged"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)