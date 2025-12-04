#!/usr/bin/env python3
"""
Example: Visualize M|inc Outputs

This example demonstrates how to create visualizations from M|inc output files
to analyze economic dynamics, wealth distribution, currency flows, and event patterns.

Visualizations include:
- Wealth distribution over time
- Currency flows between roles
- Event frequency heatmaps
- Agent trajectories

Usage:
    python 05_visualize_outputs.py [--output-dir OUTPUT_DIR] [--save]

Requirements:
    pip install matplotlib seaborn
"""

import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.gridspec import GridSpec
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Error: matplotlib not available. Install with: pip install matplotlib")
    sys.exit(1)

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
    sns.set_style("whitegrid")
except ImportError:
    SEABORN_AVAILABLE = False
    print("Note: seaborn not available. Install with: pip install seaborn")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Note: pandas not available. Install with: pip install pandas")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Note: numpy not available. Install with: pip install numpy")


def load_tick_data(output_dir: Path) -> Optional[List[Dict[str, Any]]]:
    """Load tick JSON data."""
    tick_file = output_dir / "ticks.json"
    
    if not tick_file.exists():
        print(f"Error: Tick file not found: {tick_file}")
        return None
    
    with open(tick_file, 'r') as f:
        data = json.load(f)
        # Handle both single tick and list of ticks
        if isinstance(data, dict):
            return [data]
        return data


def load_event_data(output_dir: Path) -> Optional[Any]:
    """Load event CSV data."""
    event_file = output_dir / "events.csv"
    
    if not event_file.exists():
        print(f"Error: Event file not found: {event_file}")
        return None
    
    if PANDAS_AVAILABLE:
        return pd.read_csv(event_file)
    else:
        # Basic CSV parsing
        events = []
        with open(event_file, 'r') as f:
            header = f.readline().strip().split(',')
            for line in f:
                values = line.strip().split(',')
                events.append(dict(zip(header, values)))
        return events


def plot_wealth_distribution_over_time(tick_data: List[Dict[str, Any]], 
                                      save_path: Optional[Path] = None) -> None:
    """Plot wealth distribution over time by role.
    
    Shows how total wealth evolves for Kings, Knights, and Mercenaries.
    """
    if not tick_data:
        print("No tick data available for wealth distribution plot")
        return
    
    print("\nGenerating wealth distribution over time plot...")
    
    # Extract wealth by role over time
    ticks = []
    king_wealth = []
    knight_wealth = []
    merc_wealth = []
    
    for tick in tick_data:
        tick_num = tick.get('tick', 0)
        agents = tick.get('agents', [])
        
        role_wealth = {'king': 0, 'knight': 0, 'mercenary': 0}
        
        for agent in agents:
            role = agent.get('role', 'unknown')
            wealth = agent.get('wealth', {})
            wealth_total = sum(wealth.values()) if isinstance(wealth, dict) else 0
            
            if role in role_wealth:
                role_wealth[role] += wealth_total
        
        ticks.append(tick_num)
        king_wealth.append(role_wealth['king'])
        knight_wealth.append(role_wealth['knight'])
        merc_wealth.append(role_wealth['mercenary'])
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Absolute wealth
    ax1.plot(ticks, king_wealth, label='Kings', linewidth=2, marker='o', 
             markersize=4, color='gold')
    ax1.plot(ticks, knight_wealth, label='Knights', linewidth=2, marker='s', 
             markersize=4, color='steelblue')
    ax1.plot(ticks, merc_wealth, label='Mercenaries', linewidth=2, marker='^', 
             markersize=4, color='crimson')
    
    ax1.set_xlabel('Tick', fontsize=12)
    ax1.set_ylabel('Total Wealth', fontsize=12)
    ax1.set_title('Wealth Distribution Over Time by Role', fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Percentage distribution
    total_wealth = [k + n + m for k, n, m in zip(king_wealth, knight_wealth, merc_wealth)]
    
    king_pct = [k / t * 100 if t > 0 else 0 for k, t in zip(king_wealth, total_wealth)]
    knight_pct = [n / t * 100 if t > 0 else 0 for n, t in zip(knight_wealth, total_wealth)]
    merc_pct = [m / t * 100 if t > 0 else 0 for m, t in zip(merc_wealth, total_wealth)]
    
    ax2.stackplot(ticks, king_pct, knight_pct, merc_pct,
                  labels=['Kings', 'Knights', 'Mercenaries'],
                  colors=['gold', 'steelblue', 'crimson'],
                  alpha=0.7)
    
    ax2.set_xlabel('Tick', fontsize=12)
    ax2.set_ylabel('Wealth Share (%)', fontsize=12)
    ax2.set_title('Wealth Distribution (Percentage) Over Time', fontsize=14, fontweight='bold')
    ax2.legend(loc='best', fontsize=10)
    ax2.set_ylim(0, 100)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  Saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_currency_flows(tick_data: List[Dict[str, Any]], 
                       event_data: Any,
                       save_path: Optional[Path] = None) -> None:
    """Plot currency flows between roles.
    
    Shows net currency transfers between Kings, Knights, and Mercenaries.
    """
    if not tick_data or event_data is None:
        print("No data available for currency flows plot")
        return
    
    print("\nGenerating currency flows plot...")
    
    # Track currency over time
    ticks = []
    king_currency = []
    knight_currency = []
    merc_currency = []
    
    for tick in tick_data:
        tick_num = tick.get('tick', 0)
        agents = tick.get('agents', [])
        
        role_currency = {'king': 0, 'knight': 0, 'mercenary': 0}
        
        for agent in agents:
            role = agent.get('role', 'unknown')
            currency = agent.get('currency', 0)
            
            if role in role_currency:
                role_currency[role] += currency
        
        ticks.append(tick_num)
        king_currency.append(role_currency['king'])
        knight_currency.append(role_currency['knight'])
        merc_currency.append(role_currency['mercenary'])
    
    # Analyze flows from events
    if PANDAS_AVAILABLE and isinstance(event_data, pd.DataFrame):
        # Calculate net flows
        bribe_flows = event_data[event_data['type'] == 'bribe_accept']
        retainer_flows = event_data[event_data['type'] == 'retainer']
        defend_flows = event_data[event_data['type'].str.contains('defend', na=False)]
        
        total_bribes = bribe_flows['amount'].sum() if len(bribe_flows) > 0 else 0
        total_retainers = retainer_flows['amount'].sum() if len(retainer_flows) > 0 else 0
        total_stakes = defend_flows['stake'].sum() if len(defend_flows) > 0 else 0
    else:
        total_bribes = 0
        total_retainers = 0
        total_stakes = 0
    
    # Create plot
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(2, 2, figure=fig)
    
    # Plot 1: Currency over time
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(ticks, king_currency, label='Kings', linewidth=2, marker='o', 
             markersize=4, color='gold')
    ax1.plot(ticks, knight_currency, label='Knights', linewidth=2, marker='s', 
             markersize=4, color='steelblue')
    ax1.plot(ticks, merc_currency, label='Mercenaries', linewidth=2, marker='^', 
             markersize=4, color='crimson')
    
    ax1.set_xlabel('Tick', fontsize=12)
    ax1.set_ylabel('Total Currency', fontsize=12)
    ax1.set_title('Currency Holdings Over Time by Role', fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Flow diagram (simplified)
    ax2 = fig.add_subplot(gs[1, 0])
    
    flow_types = ['Bribes\n(K→M)', 'Retainers\n(K→N)', 'Stakes\n(N↔M)']
    flow_amounts = [total_bribes, total_retainers, total_stakes]
    colors = ['crimson', 'steelblue', 'purple']
    
    bars = ax2.bar(flow_types, flow_amounts, color=colors, alpha=0.7, edgecolor='black')
    ax2.set_ylabel('Total Currency Transferred', fontsize=12)
    ax2.set_title('Currency Flows by Type', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=10)
    
    # Plot 3: Currency distribution pie chart (final state)
    ax3 = fig.add_subplot(gs[1, 1])
    
    final_currencies = [king_currency[-1], knight_currency[-1], merc_currency[-1]]
    labels = ['Kings', 'Knights', 'Mercenaries']
    colors_pie = ['gold', 'steelblue', 'crimson']
    
    # Only plot non-zero values
    non_zero = [(l, c, col) for l, c, col in zip(labels, final_currencies, colors_pie) if c > 0]
    if non_zero:
        labels_nz, values_nz, colors_nz = zip(*non_zero)
        ax3.pie(values_nz, labels=labels_nz, colors=colors_nz, autopct='%1.1f%%',
                startangle=90, textprops={'fontsize': 10})
        ax3.set_title('Final Currency Distribution', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  Saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_event_frequency_heatmap(event_data: Any, 
                                 save_path: Optional[Path] = None) -> None:
    """Plot event frequency heatmap over time.
    
    Shows when different types of events occur throughout the simulation.
    """
    if event_data is None:
        print("No event data available for heatmap")
        return
    
    print("\nGenerating event frequency heatmap...")
    
    if PANDAS_AVAILABLE and isinstance(event_data, pd.DataFrame):
        # Create pivot table of event counts by tick and type
        event_counts = event_data.groupby(['tick', 'type']).size().reset_index(name='count')
        pivot = event_counts.pivot(index='type', columns='tick', values='count')
        pivot = pivot.fillna(0)
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(14, 8))
        
        if SEABORN_AVAILABLE:
            sns.heatmap(pivot, cmap='YlOrRd', annot=False, fmt='g', 
                       cbar_kws={'label': 'Event Count'}, ax=ax)
        else:
            im = ax.imshow(pivot.values, cmap='YlOrRd', aspect='auto')
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels(pivot.columns)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels(pivot.index)
            plt.colorbar(im, ax=ax, label='Event Count')
        
        ax.set_xlabel('Tick', fontsize=12)
        ax.set_ylabel('Event Type', fontsize=12)
        ax.set_title('Event Frequency Heatmap', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"  Saved to: {save_path}")
        else:
            plt.show()
        
        plt.close()
    else:
        # Basic implementation without pandas
        print("  Pandas required for heatmap visualization")


def plot_agent_trajectories(tick_data: List[Dict[str, Any]], 
                           num_agents: int = 10,
                           save_path: Optional[Path] = None) -> None:
    """Plot individual agent wealth trajectories.
    
    Shows how selected agents' wealth evolves over time.
    """
    if not tick_data:
        print("No tick data available for agent trajectories")
        return
    
    print(f"\nGenerating agent trajectories plot (showing {num_agents} agents)...")
    
    # Track individual agents over time
    agent_histories = defaultdict(lambda: {'ticks': [], 'wealth': [], 'role': None})
    
    for tick in tick_data:
        tick_num = tick.get('tick', 0)
        agents = tick.get('agents', [])
        
        for agent in agents:
            agent_id = agent.get('id', 'unknown')
            role = agent.get('role', 'unknown')
            wealth = agent.get('wealth', {})
            wealth_total = sum(wealth.values()) if isinstance(wealth, dict) else 0
            
            agent_histories[agent_id]['ticks'].append(tick_num)
            agent_histories[agent_id]['wealth'].append(wealth_total)
            if agent_histories[agent_id]['role'] is None:
                agent_histories[agent_id]['role'] = role
    
    # Select agents to plot (top N by final wealth)
    sorted_agents = sorted(agent_histories.items(), 
                          key=lambda x: x[1]['wealth'][-1] if x[1]['wealth'] else 0,
                          reverse=True)
    
    selected_agents = sorted_agents[:num_agents]
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Color map by role
    role_colors = {'king': 'gold', 'knight': 'steelblue', 'mercenary': 'crimson'}
    
    # Plot 1: All selected agents
    for agent_id, history in selected_agents:
        role = history['role']
        color = role_colors.get(role, 'gray')
        ax1.plot(history['ticks'], history['wealth'], 
                label=f"{agent_id} ({role})", 
                linewidth=1.5, alpha=0.7, color=color)
    
    ax1.set_xlabel('Tick', fontsize=12)
    ax1.set_ylabel('Wealth', fontsize=12)
    ax1.set_title(f'Top {num_agents} Agent Wealth Trajectories', fontsize=14, fontweight='bold')
    ax1.legend(loc='best', fontsize=8, ncol=2)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Wealth distribution statistics
    all_wealth_by_tick = defaultdict(list)
    for agent_id, history in agent_histories.items():
        for tick, wealth in zip(history['ticks'], history['wealth']):
            all_wealth_by_tick[tick].append(wealth)
    
    ticks_sorted = sorted(all_wealth_by_tick.keys())
    
    if NUMPY_AVAILABLE:
        means = [np.mean(all_wealth_by_tick[t]) for t in ticks_sorted]
        medians = [np.median(all_wealth_by_tick[t]) for t in ticks_sorted]
        p25 = [np.percentile(all_wealth_by_tick[t], 25) for t in ticks_sorted]
        p75 = [np.percentile(all_wealth_by_tick[t], 75) for t in ticks_sorted]
        
        ax2.plot(ticks_sorted, means, label='Mean', linewidth=2, color='blue')
        ax2.plot(ticks_sorted, medians, label='Median', linewidth=2, color='green')
        ax2.fill_between(ticks_sorted, p25, p75, alpha=0.3, color='gray', 
                        label='25th-75th percentile')
    else:
        # Simple mean without numpy
        means = [sum(all_wealth_by_tick[t]) / len(all_wealth_by_tick[t]) 
                for t in ticks_sorted]
        ax2.plot(ticks_sorted, means, label='Mean', linewidth=2, color='blue')
    
    ax2.set_xlabel('Tick', fontsize=12)
    ax2.set_ylabel('Wealth', fontsize=12)
    ax2.set_title('Wealth Distribution Statistics', fontsize=14, fontweight='bold')
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  Saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_wealth_traits_breakdown(tick_data: List[Dict[str, Any]], 
                                 save_path: Optional[Path] = None) -> None:
    """Plot breakdown of wealth traits over time.
    
    Shows how different wealth traits (compute, copy, defend, etc.) evolve.
    """
    if not tick_data:
        print("No tick data available for wealth traits breakdown")
        return
    
    print("\nGenerating wealth traits breakdown plot...")
    
    # Track traits over time
    ticks = []
    trait_totals = defaultdict(list)
    trait_names = ['compute', 'copy', 'defend', 'raid', 'trade', 'sense', 'adapt']
    
    for tick in tick_data:
        tick_num = tick.get('tick', 0)
        agents = tick.get('agents', [])
        
        tick_traits = {trait: 0 for trait in trait_names}
        
        for agent in agents:
            wealth = agent.get('wealth', {})
            for trait in trait_names:
                tick_traits[trait] += wealth.get(trait, 0)
        
        ticks.append(tick_num)
        for trait in trait_names:
            trait_totals[trait].append(tick_traits[trait])
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Stacked area chart
    trait_arrays = [trait_totals[trait] for trait in trait_names]
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE']
    
    ax1.stackplot(ticks, *trait_arrays, labels=trait_names, colors=colors, alpha=0.8)
    
    ax1.set_xlabel('Tick', fontsize=12)
    ax1.set_ylabel('Total Trait Value', fontsize=12)
    ax1.set_title('Wealth Traits Breakdown Over Time (Stacked)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left', fontsize=10, ncol=2)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Individual trait lines
    for trait, color in zip(trait_names, colors):
        ax2.plot(ticks, trait_totals[trait], label=trait.capitalize(), 
                linewidth=2, color=color, marker='o', markersize=3)
    
    ax2.set_xlabel('Tick', fontsize=12)
    ax2.set_ylabel('Total Trait Value', fontsize=12)
    ax2.set_title('Wealth Traits Over Time (Individual)', fontsize=14, fontweight='bold')
    ax2.legend(loc='best', fontsize=10, ncol=2)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  Saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def create_all_visualizations(output_dir: Path, save_dir: Optional[Path] = None) -> None:
    """Create all visualizations from M|inc outputs.
    
    Args:
        output_dir: Directory containing M|inc output files
        save_dir: Directory to save plots (if None, displays interactively)
    """
    print("=" * 60)
    print("M|inc Visualization Generator")
    print("=" * 60)
    print(f"\nLoading data from: {output_dir}")
    
    # Load data
    tick_data = load_tick_data(output_dir)
    event_data = load_event_data(output_dir)
    
    if tick_data is None:
        print("\nError: Could not load tick data")
        return
    
    print(f"Loaded {len(tick_data)} ticks")
    
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nSaving plots to: {save_dir}")
    
    # Generate visualizations
    plot_wealth_distribution_over_time(
        tick_data, 
        save_path=save_dir / "wealth_distribution.png" if save_dir else None
    )
    
    plot_currency_flows(
        tick_data, 
        event_data,
        save_path=save_dir / "currency_flows.png" if save_dir else None
    )
    
    plot_event_frequency_heatmap(
        event_data,
        save_path=save_dir / "event_heatmap.png" if save_dir else None
    )
    
    plot_agent_trajectories(
        tick_data,
        num_agents=10,
        save_path=save_dir / "agent_trajectories.png" if save_dir else None
    )
    
    plot_wealth_traits_breakdown(
        tick_data,
        save_path=save_dir / "wealth_traits.png" if save_dir else None
    )
    
    print("\n" + "=" * 60)
    print("Visualization complete!")
    print("=" * 60)
    
    if save_dir:
        print(f"\nPlots saved to: {save_dir}")
        print("\nGenerated files:")
        print("  - wealth_distribution.png")
        print("  - currency_flows.png")
        print("  - event_heatmap.png")
        print("  - agent_trajectories.png")
        print("  - wealth_traits.png")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Visualize M|inc simulation outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize outputs from default location
  python 05_visualize_outputs.py
  
  # Visualize outputs from custom location
  python 05_visualize_outputs.py --output-dir /path/to/output
  
  # Save plots to file instead of displaying
  python 05_visualize_outputs.py --save
  
  # Save plots to custom directory
  python 05_visualize_outputs.py --save --save-dir /path/to/plots
        """
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).parent / "output" / "historical",
        help='Directory containing M|inc output files (default: examples/output/historical)'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save plots to files instead of displaying'
    )
    
    parser.add_argument(
        '--save-dir',
        type=Path,
        default=None,
        help='Directory to save plots (default: output-dir/plots)'
    )
    
    args = parser.parse_args()
    
    # Check if matplotlib is available
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib is required for visualization")
        print("Install with: pip install matplotlib")
        return 1
    
    # Determine save directory
    save_dir = None
    if args.save:
        save_dir = args.save_dir if args.save_dir else args.output_dir / "plots"
    
    # Check if output directory exists
    if not args.output_dir.exists():
        print(f"Error: Output directory not found: {args.output_dir}")
        print("\nPlease run 01_process_historical_trace.py first to generate output files.")
        return 1
    
    # Create visualizations
    create_all_visualizations(args.output_dir, save_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
