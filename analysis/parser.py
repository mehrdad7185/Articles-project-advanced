

import re
import pandas as pd
import os

def parse_log_file(log_file_path, scenario_name):
    """
    Parses a log file for all metrics, correctly handling log inconsistencies.
    This version correctly looks for the 'memory' key.
    """
    # Regex to split a log line into its source (container) and message.
    log_line_regex = re.compile(r"^(.*?)\s*\|\s*(.*)")
    
    records = []
    time_step = 0 # A simple counter to simulate the passage of time.
    
    print(f"Parsing {log_file_path} for scenario '{scenario_name}'...")

    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = log_line_regex.match(line)
            if not match: continue

            container_name = match.group(1).strip()
            message = match.group(2).strip()
            
            # Increment time step for each line to create a sequence.
            time_step += 1
            current_timestamp = pd.to_datetime('2025-01-01') + pd.to_timedelta(time_step, unit='s')

            # --- 1. Extract Latency ---
            if ">> Calculated E2E Latency:" in message:
                try:
                    latency = float(message.split(':')[-1].strip().split(' ')[0])
                    records.append({
                        "scenario": scenario_name, "metric": "latency",
                        "node": container_name, "value": latency, "timestamp": current_timestamp
                    })
                except (ValueError, IndexError): continue

            # --- 2. Extract Health Events ---
            if "[HEALTH CHECK]" in message:
                event_match = re.search(r"Node '(\w+-\w+-\d)' (.*)", message)
                if event_match:
                    node_name = event_match.group(1)
                    event_type = "DOWN" if "SUSPECTED" in event_match.group(2) else "UP"
                    records.append({
                        "scenario": scenario_name, "metric": "event",
                        "node": node_name, "value": event_type, "timestamp": current_timestamp
                    })

            # --- 3. Extract CPU and Memory ---
            if container_name.startswith('scheduler') and "Status: {" in message:
                status_dict_match = re.search(r"(\{.*\})", message)
                if status_dict_match:
                    status_dict_str = status_dict_match.group(1)
                    node_info_regex = re.compile(r"'(\w+-\w+-\d)':\s*\{.*?\}")
                    for node_match in node_info_regex.finditer(status_dict_str):
                        node_name = node_match.group(1)
                        node_info_str = node_match.group(0)
                        try:
                            cpu_val = re.search(r"'cpu':\s*([\d\.]+)", node_info_str)
                            # --- BUG FIX: Changed 'mem' to 'memory' to match the log output ---
                            mem_val = re.search(r"'memory':\s*([\d\.]+)", node_info_str)
                            
                            cpu = float(cpu_val.group(1)) if cpu_val else 0.0
                            mem = float(mem_val.group(1)) if mem_val else 0.0
                            
                            records.append({"scenario": scenario_name, "metric": "cpu", "node": node_name, "value": cpu, "timestamp": current_timestamp})
                            records.append({"scenario": scenario_name, "metric": "memory", "node": node_name, "value": mem, "timestamp": current_timestamp})
                        except (AttributeError, ValueError): continue
    return records

if __name__ == '__main__':
    log_files = {
        '../log_resource_aware_normal.txt': 'Resource-Aware (Normal)',
        '../log_resource_aware_failure.txt': 'Resource-Aware (Failure)',
        '../log_random.txt': 'Random'
    }
    all_records = []
    for file_path, name in log_files.items():
        if os.path.exists(file_path):
            all_records.extend(parse_log_file(file_path, name))
        else:
            print(f"Warning: Log file not found at '{file_path}'. Skipping.")
    if not all_records:
        print("\nError: No data was successfully parsed.")
    else:
        df = pd.DataFrame(all_records)
        df.to_csv('results.csv', index=False)
        print(f"\nParsing complete. {len(df)} records saved to 'results.csv'")
        print("Sample of the data:")
        print(df.head())