
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates # Import for date formatting
import seaborn as sns

def create_visualizations(csv_path):
    """
    Reads the parsed data and creates final, publication-quality plots.
    This version includes improved text annotation placement and x-axis formatting.
    """
    try:
        data = pd.read_csv(csv_path, parse_dates=['timestamp'])
    except (FileNotFoundError, KeyError):
        print(f"Error reading '{csv_path}'. Please run the parser.py script first.")
        return

    sns.set_theme(style="whitegrid", palette="viridis")

    # --- Data Extraction ---
    latency_data = data[data['metric'] == 'latency']
    cpu_data = data[data['metric'] == 'cpu']
    failure_scenario_data = data[data['scenario'] == 'Resource-Aware (Failure)']
    mem_data = failure_scenario_data[failure_scenario_data['metric'] == 'memory']
    event_data = failure_scenario_data[failure_scenario_data['metric'] == 'event']

    # --- Plot 1 & 2 (Latency and CPU) remain the same ---
    if not latency_data.empty:
        plt.figure(figsize=(10, 7))
        sns.boxplot(x='scenario', y='value', data=latency_data)
        plt.title('Distribution of End-to-End Latency per Scenario', fontsize=16)
        plt.ylabel('Latency (ms)'); plt.xlabel('Experiment Scenario')
        plt.savefig('plot_latency_distribution.png', dpi=300, bbox_inches='tight')
        print("Saved plot: plot_latency_distribution.png")

    if not cpu_data.empty:
        # ... (CPU plot code is unchanged) ...
        plt.savefig('plot_cpu_usage.png', dpi=300, bbox_inches='tight')
        print("Saved plot: plot_cpu_usage.png")

    # --- Plot 3: Memory Usage with Final Polished Annotations ---
    if not mem_data.empty:
        fig, ax = plt.subplots(figsize=(20, 8)) # Make the figure even wider
        sns.lineplot(x='timestamp', y='value', data=mem_data, hue='node', style='node', markers=True, ax=ax, linewidth=2)

        y_min, y_max = ax.get_ylim()
        if y_max <= y_min: y_max = y_min + 1
        
        # --- IMPROVEMENT: Increased vertical separation for text ---
        text_y_positions = [
            y_min,                      # Position 1: At the very bottom
            y_max - (y_max - y_min) * 0.1 # Position 2: At the very top
        ]
        pos_idx = 0

        for _, event in event_data.iterrows():
            color = 'red' if event['value'] == 'DOWN' else 'green'
            ax.axvline(x=event['timestamp'], color=color, linestyle='--', linewidth=1.5, alpha=0.9)
            
            # Alternate the y-position of the text
            current_y_pos = text_y_positions[pos_idx % 2]
            vertical_alignment = 'bottom' if (pos_idx % 2 == 0) else 'top'
            pos_idx += 1
            
            ax.text(event['timestamp'], current_y_pos, f" {event['node']} {event['value']} ", 
                    rotation=90, color=color, verticalalignment=vertical_alignment, fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7))
        
        # --- IMPROVEMENT: Better x-axis date formatting ---
        # Display time in Minute:Second format
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
        # Set ticks at reasonable intervals (e.g., every 30 seconds)
        ax.xaxis.set_major_locator(plt.MaxNLocator(20)) 
        plt.xticks(rotation=45) # Rotate for better readability

        ax.set_title('Memory Usage During Failure & Recovery Scenario', fontsize=18)
        ax.set_ylabel('Memory Usage (MB)', fontsize=14); ax.set_xlabel('Time (Minute:Second)', fontsize=14)
        ax.legend(title='Fog Node', fontsize=12)
        plt.savefig('plot_memory_with_events_final.png', dpi=300, bbox_inches='tight')
        print("Saved final plot: plot_memory_with_events_final.png")

    plt.show()

if __name__ == '__main__':
    create_visualizations('results.csv')