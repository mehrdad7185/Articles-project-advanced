
import socket
import json
import os
import time
# --- Configuration ---
# Listen on all available network interfaces
HOST = '0.0.0.0'  
PORT = 9999
# Get the container's hostname to identify which fog node is running this code
NODE_ID = os.uname().nodename 

# Create a TCP/IP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allow reusing the address, which is helpful for quick restarts
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind the socket to the port
server_socket.bind((HOST, PORT))

# Listen for incoming connections
server_socket.listen()

print(f"[{NODE_ID}] Fog node is running and listening on {HOST}:{PORT}")

while True:
                    # Wait for a connection
    conn, addr = server_socket.accept()
    with conn:
        # Record the end time as soon as a message is received ---
        end_time = time.time()
          # Receive the data from the client
        print(f"[{NODE_ID}] Connected by {addr}")
        data = conn.recv(1024) # 1024 is the buffer size
        
        if data:
            try:          # Decode the bytes to a string and parse the JSON
                message = json.loads(data.decode('utf-8'))
                print(f"[{NODE_ID}] Received data: {message}")

                # Calculate and print the latency
                start_time = message.get("timestamp", 0)
                if start_time > 0:
                    latency = (end_time - start_time) * 1000 # in milliseconds
                    print(f"[{NODE_ID}] >> Calculated E2E Latency: {latency:.2f} ms")

            except json.JSONDecodeError:
                print(f"[{NODE_ID}] Received non-JSON data: {data.decode('utf-8')}")

