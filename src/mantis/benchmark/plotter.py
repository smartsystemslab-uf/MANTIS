import matplotlib.pyplot as plt
import pandas as pd
import json
from pathlib import Path

def plot_observability_overhead(results_file: str, output_image: str):
    """
    Expects a JSON file with a list of benchmark reports.
    Example: 
    [
        {"mode": "off", "avg_latency_s": 2.5, "concurrency": 1},
        {"mode": "full", "avg_latency_s": 3.1, "concurrency": 1}
    ]
    """
    with open(results_file, "r") as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    
    # We use a standard academic style
    plt.style.use('seaborn-v0_8-whitegrid')
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    modes = df['mode'].unique()
    avg_latencies = [df[df['mode'] == m]['avg_latency_s'].mean() for m in modes]
    
    colors = ['#4C72B0', '#DD8452', '#55A868']
    
    bars = ax.bar(modes, avg_latencies, color=colors[:len(modes)], width=0.5)
    
    ax.set_title('Observability Overhead: Latency Impact', fontsize=14, pad=15)
    ax.set_xlabel('Observability Mode', fontsize=12)
    ax.set_ylabel('Average Latency (seconds)', fontsize=12)
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{height:.2f}s',
                ha='center', va='bottom', fontsize=11)
                
    # Add a percentage increase annotation if both "off" and "full" exist
    if "off" in modes and "full" in modes:
        off_lat = df[df['mode'] == "off"]['avg_latency_s'].mean()
        full_lat = df[df['mode'] == "full"]['avg_latency_s'].mean()
        if off_lat > 0:
            overhead = ((full_lat - off_lat) / off_lat) * 100
            ax.annotate(f"Overhead: +{overhead:.1f}%", 
                        xy=(0.5, 0.9), xycoords='axes fraction',
                        ha='center', fontsize=12,
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    print(f"Plot saved to {output_image}")
