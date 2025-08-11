
import re
import pandas as pd
import os
import ast

def parse_log_file(log_file_path, scenario_name):
    """
    Parses a log file for all metrics. This version is synchronized
    with the 'STATUS_UPDATE::' format from the final scheduler.py.
    """
    log_line_regex = re.compile(r"^(.*?)\s*\|\s*(.*)")
    records = []
    time_step = 0
    
    print(f"Parsing {log_file_path} for scenario '{scenario_name}'...")

    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = log_line_regex.match(line)
            if not match: continue

            container_name = match.group(1).strip()
            message = match.group(2).strip()
            
            time_step += 1
            current_timestamp = pd.to_datetime('2025-01-01') + pd.to_timedelta(time_step, unit='s')

            # --- KEY CHANGE: Corrected the string to look for ---
            if ">> Calculated E2E Latency:" in message:
                try:
                    # The rest of the logic for parsing latency is correct
                    latency = float(message.split(':')[-1].strip().split(' ')[0])
                    records.append({
                        "scenario": scenario_name, "metric": "latency",
                        "node": container_name, "value": latency, "timestamp": current_timestamp
                    })
                except (ValueError, IndexError): continue

            # --- Extract Health Events (no changes here) ---
            if "[HEALTH CHECK]" in message:
                event_match = re.search(r"Node '(\w+-\w+-\d)' (.*)", message)
                if event_match:
                    node_name, desc = event_match.groups()
                    event_type = "DOWN" if "SUSPECTED" in desc else "UP"
                    records.append({
                        "scenario": scenario_name, "metric": "event",
                        "node": node_name, "value": event_type, "timestamp": current_timestamp
                    })

            # --- Extract CPU and Memory (no changes here) ---
            if message.startswith("STATUS_UPDATE::"):
                try:
                    dict_str = message.replace("STATUS_UPDATE::", "")
                    status_dict = ast.literal_eval(dict_str)
                    
                    for node_name, stats in status_dict.items():
                        records.append({
                            "scenario": scenario_name, "metric": "cpu", "node": node_name,
                            "value": stats.get('cpu', 0.0), "timestamp": current_timestamp
                        })
                        records.append({
                            "scenario": scenario_name, "metric": "memory", "node": node_name,
                            "value": stats.get('memory', 0.0), "timestamp": current_timestamp
                        })
                except (ValueError, SyntaxError): continue
    return records

# The main block remains unchanged
if __name__ == '__main__':
    log_files = {
        '../log_resource_aware_normal.txt': 'Resource-Aware (Normal)',
        '../log_resource_aware_failure.txt': 'Resource-Aware (Failure)',
        '../log_random.txt': 'Random'
    }
    all_records = []
    for file_path, name in log_files.items():
        if os.path.exists(file_path): all_records.extend(parse_log_file(file_path, name))
        else: print(f"Warning: Log file not found at '{file_path}'. Skipping.")
    if not all_records:
        print("\nError: No data was parsed.")
    else:
        df = pd.DataFrame(all_records)
        df.to_csv('results.csv', index=False)
        print(f"\nParsing complete. {len(df)} records saved to 'results.csv'")
        print("Sample of the data:"); print(df.head())