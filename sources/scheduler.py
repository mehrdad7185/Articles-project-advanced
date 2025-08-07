
from flask import Flask, jsonify
import os

# --- Attempt to import the docker library ---
DOCKER_AVAILABLE = False
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    print("[WARNING] Docker SDK not found. Will use 'Least Connections' algorithm as a fallback.")

app = Flask(__name__)

# --- Configuration ---
FOG_NODES = ['fog-node-1', 'fog-node-2']
PLACEMENT_STRATEGY = os.getenv("PLACEMENT_STRATEGY", "LEAST_CPU") # Default to advanced strategy

# --- State Dictionaries ---
# For Least Connections algorithm
node_connections = {node: 0 for node in FOG_NODES}
# For Least CPU algorithm
node_stats = {node: {"cpu": 0.0, "memory": 0.0} for node in FOG_NODES}

# --- Docker Client Initialization ---
client = None
if DOCKER_AVAILABLE:
    try:
        # Initialize client only if docker is available and running
        client = docker.from_env()
        # Ping the server to check for a valid connection
        client.ping()
        print("[INFO] Successfully connected to Docker daemon. Using 'Least CPU' strategy.")
    except Exception as e:
        print(f"[ERROR] Could not connect to Docker daemon: {e}")
        print("[INFO] Switching to 'Least Connections' strategy as a fallback.")
        DOCKER_AVAILABLE = False

def get_least_cpu_node():
    """Calculates and returns the node with the least CPU usage."""
    for node_name in FOG_NODES:
        try:
            container = client.containers.get(node_name)
            stats = container.stats(stream=False)
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_cpu_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = (cpu_delta / system_cpu_delta) * stats["cpu_stats"]["online_cpus"] * 100.0 if system_cpu_delta > 0 else 0
            node_stats[node_name] = {"cpu": round(cpu_percent, 2)}
        except docker.errors.NotFound:
            print(f"[CRITICAL] Node '{node_name}' not found. Marking as unavailable.")
            node_stats[node_name] = {"cpu": 999.0} # Mark as unavailable
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred while fetching stats for {node_name}: {e}")
            node_stats[node_name] = {"cpu": 999.0} # Mark as unavailable on error
    
    active_nodes = {n: s for n, s in node_stats.items() if s['cpu'] < 999.0}
    if not active_nodes: return None
    
    chosen_node = min(active_nodes, key=lambda n: active_nodes[n]['cpu'])
    print(f"Stats: {active_nodes}. Chosen (CPU): '{chosen_node}'")
    return chosen_node

def get_least_connections_node():
    """Returns the node with the least active connections."""
    global node_connections
    chosen_node = min(node_connections, key=node_connections.get)
    node_connections[chosen_node] += 1
    print(f"Connections: {node_connections}. Chosen (Connections): '{chosen_node}'")
    return chosen_node

@app.route('/get_fog_node', methods=['GET'])
def get_fog_node():
    """Main placement endpoint that decides which algorithm to use."""
    chosen_node = None
    if PLACEMENT_STRATEGY == "LEAST_CPU" and DOCKER_AVAILABLE:
        chosen_node = get_least_cpu_node()
        # If the primary algorithm fails (e.g., all nodes down), fall back
        if not chosen_node:
            chosen_node = get_least_connections_node()
    else:
        chosen_node = get_least_connections_node()
        
    if not chosen_node:
        return jsonify({"error": "No available fog nodes to handle the request."}), 503
        
    return jsonify({"fog_node_host": chosen_node})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)