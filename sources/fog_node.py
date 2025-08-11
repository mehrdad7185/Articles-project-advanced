# sources/fog_node.py (Final Version with CPU-intensive task)
# Comments are in English

import socket
import json
import os
import time

# --- Configuration ---
HOST = '0.0.0.0'
PORT = 9999
NODE_ID = os.uname().nodename

# --- NEW: CPU-Intensive function ---
def cpu_intensive_task(n=30):
    """
    A simple function to simulate a CPU-heavy workload.
    Calculating Fibonacci numbers recursively is a classic example.
    The number 'n' can be adjusted to make the task lighter or heavier.
    """
    if n <= 1:
        return n
    else:
        return cpu_intensive_task(n-1) + cpu_intensive_task(n-2)

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"[{NODE_ID}] Fog node is running and listening on {HOST}:{PORT}")

while True:
    conn, addr = server_socket.accept()
    with conn:
        end_time = time.time()
        print(f"[{NODE_ID}] Connected by {addr}")
        data = conn.recv(1024)
        
        if data:
            try:
                message = json.loads(data.decode('utf-8'))
                print(f"[{NODE_ID}] Received data: {message}")

                # --- NEW: Execute the heavy task upon receiving data ---
                print(f"[{NODE_ID}] Starting CPU-intensive task...")
                start_cpu_task = time.time()
                # We don't care about the result, just the computation
                cpu_intensive_task(n=32) 
                end_cpu_task = time.time()
                print(f"[{NODE_ID}] Finished CPU task in {end_cpu_task - start_cpu_task:.2f} seconds.")

                # Calculate and print the end-to-end latency
                start_time = message.get("timestamp", 0)
                if start_time > 0:
                    latency = (end_time - start_time) * 1000
                    print(f"[{NODE_ID}] >> Calculated E2E Latency: {latency:.2f} ms")

            except json.JSONDecodeError:
                print(f"[{NODE_ID}] Received non-JSON data: {data.decode('utf-8')}")