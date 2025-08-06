
from flask import Flask, jsonify

app = Flask(__name__)

# --- Configuration ---
FOG_NODES = ['fog-node-1', 'fog-node-2']

# A simple in-memory dictionary to track the load (number of connections)
# This dictionary acts as the "state" of our scheduler.
node_load = {node: 0 for node in FOG_NODES}

@app.route('/get_fog_node', methods=['GET'])
def get_fog_node():
    """
    Placement endpoint implementing the "Least Connections" algorithm.
    """
    global node_load

    # --- Placement Algorithm ---
    # Find the node with the minimum number of connections.
    # The min() function with a key is a clean way to find the dictionary key
    # corresponding to the minimum value.
    chosen_node = min(node_load, key=node_load.get)
    
    # Increment the load count for the chosen node
    node_load[chosen_node] += 1
    
    print(f"Current loads: {node_load}. Chosen node: '{chosen_node}'")
    
    return jsonify({
        "fog_node_host": chosen_node
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)