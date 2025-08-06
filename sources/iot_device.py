
import socket
import time
import json
import random
import requests

# --- Configuration ---
SCHEDULER_URL = "http://scheduler:5000/get_fog_node"
FOG_PORT = 9999
DEVICE_ID = "iot-device-1"

print(f"[{DEVICE_ID}] Starting up. Will ask scheduler at {SCHEDULER_URL} for placement.")

def get_target_fog_node():
    """Gets the target fog node from the scheduler."""
    try:
        response = requests.get(SCHEDULER_URL)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return data.get("fog_node_host")
    except requests.exceptions.RequestException as e:
        print(f"[{DEVICE_ID}] Could not connect to scheduler: {e}")
        return None

while True:
    target_host = get_target_fog_node()
    if not target_host:
        print(f"[{DEVICE_ID}] Could not get a fog node. Retrying in 5s.")
        time.sleep(5)
        continue

    print(f"[{DEVICE_ID}] Scheduler assigned: '{target_host}'. Sending data...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((target_host, FOG_PORT))
            
            # Record the start time before sending 
            start_time = time.time()

            payload = {
                "device_id": DEVICE_ID,
                "temperature": round(random.uniform(20.0, 30.0), 2),
                "timestamp": start_time # Use the recorded start_time
            }
            
            message = json.dumps(payload).encode('utf-8')
            s.sendall(message)
            print(f"[{DEVICE_ID}] Successfully sent data to {target_host}")

    except Exception as e:
        print(f"[{DEVICE_ID}] An error occurred sending data to {target_host}: {e}")
    
    time.sleep(5)