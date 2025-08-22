
import socket
import json
import os
import time
import math
import random

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 9999
NODE_ID = os.uname().nodename

# --- More Stable and Controllable CPU-Intensive function ---
def cpu_intensive_task(duration_seconds=0.5):
    """
    Simulates a stable CPU workload for a given duration.
    This is better for generating smooth, realistic data for our ML model,
    as opposed to the spiky load from a recursive Fibonacci function.
    It performs a series of mathematical calculations in a loop.
    """
    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        # Perform some math operations to keep the CPU busy
        _ = math.sqrt(random.random()) * math.sin(random.random()) * math.cos(random.random())


# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"[{NODE_ID}] Fog node is running and listening on {HOST}:{PORT}")

while True:
    conn, addr = server_socket.accept()
    with conn:
        # We no longer capture the initial time here.
        data = conn.recv(1024)
        
        if data:
            try:
                message = json.loads(data.decode('utf-8'))

                # --- Step 1: Execute the stable workload task ---
                # This simulates the actual processing of the request.
                cpu_intensive_task(duration_seconds=0.7) 
                
                # --- KEY FIX: Capture the end time AFTER the processing is complete ---
                end_time = time.time()

                # --- Step 2: Calculate and print the true end-to-end response time ---
                start_time = message.get("timestamp", 0)
                if start_time > 0:
                    # This value now correctly includes both network latency and service processing time.
                    response_time = (end_time - start_time) * 1000
                    # Changed the log message to be more accurate.
                    print(f"[{NODE_ID}] >> Calculated E2E Response Time: {response_time:.2f} ms")

            except json.JSONDecodeError:
                print(f"[{NODE_ID}] Received non-JSON data: {data.decode('utf-8')}")