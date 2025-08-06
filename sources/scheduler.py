
from flask import Flask, jsonify
import random

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration ---
# A list of available fog nodes. In a real system, this could be dynamic.
FOG_NODES = ['fog-node-1', 'fog-node-2']

@app.route('/get_fog_node', methods=['GET'])
def get_fog_node():
    """
    This is the main placement endpoint.
    It implements a simple random choice algorithm.
    """
    # --- Placement Algorithm ---
    # For now, we just select a node randomly.
    # This is our baseline "Random" algorithm for the paper.
    chosen_node = random.choice(FOG_NODES)
    
    print(f"Placement decision: Assigning request to '{chosen_node}'")
    
    # Return the chosen node's hostname as a JSON response
    return jsonify({
        "fog_node_host": chosen_node
    })

if __name__ == '__main__':
    # Run the Flask app. 
    # host='0.0.0.0' makes it accessible from other containers.
    app.run(host='0.0.0.0', port=5000)