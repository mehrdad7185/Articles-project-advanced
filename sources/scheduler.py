

from flask import Flask, jsonify, request
import time
import docker

app = Flask(__name__)

# --- Configuration ---
FOG_NODES = ['fog-node-1', 'fog-node-2']
RECOVERY_TIME_SECONDS = 30
PLACEMENT_STRATEGY = 'LEAST_CPU'

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
    """
    The core logic for updating the status of all nodes.
    It tries to get stats for each node. Success means it's UP, failure means it's DOWN.
    """
    if not DOCKER_AVAILABLE:
        return

    for node_name in FOG_NODES:
        try:
            # Check if the node was previously suspected and its recovery time is over
            is_in_recovery = (node_status[node_name]["status"] == "SUSPECTED" and
                              time.time() - node_status[node_name]["last_failure"] > RECOVERY_TIME_SECONDS)

            # We only try to get stats for nodes that are UP or in recovery
            if node_status[node_name]["status"] == "UP" or is_in_recovery:
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
                
                # If we successfully get stats, the node is definitely UP
                if node_status[node_name]["status"] != "UP":
                    print(f"[HEALTH CHECK] Node '{node_name}' has recovered and is now UP.")
                
                node_status[node_name].update({
                    "status": "UP", "cpu": round(cpu_percent, 2), "memory": round(memory_usage, 2)
                })
        
        except docker.errors.NotFound:
            # If container is not found, it is definitely down.
            _mark_node_as_suspected(node_name)
        except Exception as e:
            # Also mark as down on other unexpected errors
            print(f"[ERROR] Could not get stats for {node_name}: {e}")
            _mark_node_as_suspected(node_name)

@app.route('/get_fog_node', methods=['GET'])
def get_fog_node():
    """ The main placement endpoint. """
    # 1. Update the status of all nodes based on their current state
    update_all_node_statuses()
    
    # 2. Filter for nodes that are currently marked as "UP"
    active_nodes = {node: info for node, info in node_status.items() if info["status"] == "UP"}

    if not active_nodes:
        return jsonify({"error": "No active fog nodes available"}), 503

    # 3. Choose placement based on the selected strategy
    chosen_node = min(active_nodes, key=lambda node: active_nodes[node]['cpu'])
    
    print(f"Status: {node_status}. Chosen: '{chosen_node}'")
    return jsonify({"fog_node_host": chosen_node})

def _mark_node_as_suspected(node_name):
    """ Helper function to mark a node as suspected if it's not already. """
    if node_name in node_status and node_status[node_name]['status'] == 'UP':
        node_status[node_name]['status'] = 'SUSPECTED'
        node_status[node_name]['last_failure'] = time.time()
        print(f"[HEALTH CHECK] Node '{node_name}' is now SUSPECTED.")

@app.route('/report_failure', methods=['POST'])
def report_failure():
    """ Endpoint for devices to report a connection failure. """
    failed_node = request.get_json().get('node')
    if failed_node:
        _mark_node_as_suspected(failed_node)
    return jsonify({"status": "acknowledged"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)