# analysis/visualizer.py (Final Polished Version with new plots and annotations)
# Comments are in English

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

def create_visualizations(csv_path):
    """
    Reads the final, clean data and creates publication-quality plots.
    This version creates time-series plots for CPU and Memory with clean annotations.
    """
    try:
        data = pd.read_csv(csv_path, parse_dates=['timestamp'])
    except (FileNotFoundError, KeyError):
        print(f"Error reading '{csv_path}'. Please run the parser.py script first.")
        return

    sns.set_theme(style="darkgrid", palette="colorblind")

    # --- Data Extraction ---
    latency_data = data[data['metric'] == 'latency']
    failure_scenario_data = data[data['scenario'] == 'Resource-Aware (Failure)']
    cpu_data = failure_scenario_data[failure_scenario_data['metric'] == 'cpu']
    mem_data = failure_scenario_data[failure_scenario_data['metric'] == 'memory']
    event_data = failure_scenario_data[failure_scenario_data['metric'] == 'event']

    # --- Plot 1: Latency Distribution ---
    if not latency_data.empty:
        fig, ax = plt.subplots(figsize=(10, 7))
        sns.boxplot(x='scenario', y='value', data=latency_data, ax=ax)
        ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=10, integer=True))
        ax.set_title('Latency Distribution per Scenario', fontsize=16)
        ax.set_ylabel('Latency (ms)'); ax.set_xlabel('Scenario')
        plt.savefig('plot_latency_distribution.png', dpi=300, bbox_inches='tight')
        print("Saved: plot_latency_distribution.png")

    # --- Plot 2: CPU Usage Time-Series with Rolling Average ---
    if not cpu_data.empty:
        fig, ax = plt.subplots(figsize=(20, 8))
        cpu_data['cpu_smooth'] = cpu_data.groupby('node')['value'].transform(lambda s: s.rolling(5, min_periods=1).mean())
        sns.lineplot(x='timestamp', y='cpu_smooth', data=cpu_data, hue='node', style='node', ax=ax, linewidth=2.5)
        ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=8))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
        ax.set_title('Smoothed CPU Usage During Failure & Recovery Scenario', fontsize=18)
        ax.set_ylabel('CPU Usage (%) (Rolling Average)'); ax.set_xlabel('Time (Minute:Second)')
        ax.legend(title='Fog Node')
        plt.savefig('plot_cpu_timeseries.png', dpi=300, bbox_inches='tight')
        print("Saved: plot_cpu_timeseries.png")

    # --- Plot 3: Memory Usage with Clean Annotations ---
    if not mem_data.empty:
        fig, ax = plt.subplots(figsize=(20, 8))
        sns.lineplot(x='timestamp', y='value', data=mem_data, hue='node', style='node', markers=True, ax=ax, linewidth=2)

        # Add extra space at the bottom for the text annotations
        y_min, y_max = ax.get_ylim()
        ax.set_ylim(bottom=y_min - (y_max-y_min)*0.3, top=y_max + (y_max-y_min)*0.1)
        
        if not event_data.empty:
            for _, event in event_data.iterrows():
                color = 'red' if event['value'] == 'DOWN' else 'green'
                # Use annotate for advanced text placement with arrows
                ax.annotate(f"{event['node']} {event['value']}",
                            xy=(event['timestamp'], ax.get_ylim()[0] + (y_max-y_min)*0.1), # Arrow points here
                            xytext=(event['timestamp'], ax.get_ylim()[0]), # Text is here
                            arrowprops=dict(facecolor=color, shrink=0.05, width=1.5, headwidth=5),
                            ha='center', va='bottom', fontsize=10, color=color,
                            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%M:%S'))
        ax.set_title('Memory Usage During Failure & Recovery Scenario', fontsize=18)
        ax.set_ylabel('Memory Usage (MB)'); ax.set_xlabel('Time (Minute:Second)')
        ax.legend(title='Fog Node')
        plt.savefig('plot_memory_final.png', dpi=300, bbox_inches='tight')
        print("Saved: plot_memory_final.png")

    plt.show()

if __name__ == '__main__':
    create_visualizations('results.csv')