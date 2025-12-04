#!/usr/bin/env python3
"""
Example: Analyze M|inc Outputs

This example demonstrates how to load and analyze M|inc output files
to extract insights about economic dynamics.

Usage:
    python 03_analyze_outputs.py
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Note: pandas not available, using basic analysis")


def load_tick_data(output_dir):
    """Load tick JSON data."""
    tick_file = output_dir / "ticks.json"
    
    if not tick_file.exists():
        print(f"Error: Tick file not found: {tick_file}")
        return None
    
    with open(tick_file, 'r') as f:
        return json.load(f)


def load_event_data(output_dir):
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


def analyze_wealth_dynamics(tick_data):
    """Analyze wealth accumulation over time."""
    print("\n" + "=" * 60)
    print("Wealth Dynamics Analysis")
    print("=" * 60)
    
    if not tick_data:
        return
    
    ticks = tick_data if isinstance(tick_data, list) else [tick_data]
    
    print(f"\nTotal ticks: {len(ticks)}")
    print()
    
    # Track metrics over time
    wealth_history = []
    currency_history = []
    
    for tick in ticks:
        metrics = tick.get('metrics', {})
        wealth_history.append(metrics.get('wealth_total', 0))
        currency_history.append(metrics.get('currency_total', 0))
    
    # Calculate statistics
    if wealth_history:
        print("Wealth Statistics:")
        print(f"  Initial: {wealth_history[0]:,}")
        print(f"  Final: {wealth_history[-1]:,}")
        print(f"  Change: {wealth_history[-1] - wealth_history[0]:+,}")
        print(f"  Growth rate: {((wealth_history[-1] / wealth_history[0]) - 1) * 100:+.2f}%")
        print()
    
    if currency_history:
        print("Currency Statistics:")
        print(f"  Initial: {currency_history[0]:,}")
        print(f"  Final: {currency_history[-1]:,}")
        print(f"  Change: {currency_history[-1] - currency_history[0]:+,}")
        print()
    
    # Analyze by role
    if ticks:
        last_tick = ticks[-1]
        agents = last_tick.get('agents', [])
        
        role_stats = defaultdict(lambda: {'count': 0, 'wealth': 0, 'currency': 0})
        
        for agent in agents:
            role = agent.get('role', 'unknown')
            wealth = agent.get('wealth', {})
            wealth_total = sum(wealth.values()) if isinstance(wealth, dict) else 0
            
            role_stats[role]['count'] += 1
            role_stats[role]['wealth'] += wealth_total
            role_stats[role]['currency'] += agent.get('currency', 0)
        
        print("Final State by Role:")
        for role in ['king', 'knight', 'mercenary']:
            if role in role_stats:
                stats = role_stats[role]
                print(f"  {role.capitalize()}s:")
                print(f"    Count: {stats['count']}")
                print(f"    Total wealth: {stats['wealth']:,}")
                print(f"    Total currency: {stats['currency']:,}")
                print(f"    Avg wealth: {stats['wealth'] / stats['count']:.1f}")
                print(f"    Avg currency: {stats['currency'] / stats['count']:.1f}")


def analyze_event_patterns(event_data):
    """Analyze event patterns and frequencies."""
    print("\n" + "=" * 60)
    print("Event Pattern Analysis")
    print("=" * 60)
    
    if event_data is None:
        return
    
    if PANDAS_AVAILABLE and isinstance(event_data, pd.DataFrame):
        print(f"\nTotal events: {len(event_data)}")
        print()
        
        # Event type distribution
        print("Event Type Distribution:")
        event_counts = event_data['type'].value_counts()
        for event_type, count in event_counts.items():
            pct = (count / len(event_data)) * 100
            print(f"  {event_type}: {count} ({pct:.1f}%)")
        print()
        
        # Bribe analysis
        bribes = event_data[event_data['type'].str.contains('bribe', case=False, na=False)]
        if len(bribes) > 0:
            print("Bribe Analysis:")
            print(f"  Total bribes: {len(bribes)}")
            accepted = len(bribes[bribes['type'] == 'bribe_accept'])
            print(f"  Accepted: {accepted} ({(accepted/len(bribes))*100:.1f}%)")
            print()
        
        # Defend analysis
        defends = event_data[event_data['type'].str.contains('defend', case=False, na=False)]
        if len(defends) > 0:
            print("Defend Contest Analysis:")
            print(f"  Total contests: {len(defends)}")
            knight_wins = len(defends[defends['type'] == 'defend_win'])
            print(f"  Knight wins: {knight_wins} ({(knight_wins/len(defends))*100:.1f}%)")
            print()
    
    else:
        # Basic analysis without pandas
        print(f"\nTotal events: {len(event_data)}")
        print()
        
        event_counts = defaultdict(int)
        for event in event_data:
            event_type = event.get('type', 'unknown')
            event_counts[event_type] += 1
        
        print("Event Type Distribution:")
        total = len(event_data)
        for event_type, count in sorted(event_counts.items()):
            pct = (count / total) * 100
            print(f"  {event_type}: {count} ({pct:.1f}%)")


def analyze_economic_efficiency(tick_data, event_data):
    """Analyze economic efficiency metrics."""
    print("\n" + "=" * 60)
    print("Economic Efficiency Analysis")
    print("=" * 60)
    
    if not tick_data:
        return
    
    ticks = tick_data if isinstance(tick_data, list) else [tick_data]
    
    # Calculate trade efficiency
    if event_data is not None:
        if PANDAS_AVAILABLE and isinstance(event_data, pd.DataFrame):
            trades = event_data[event_data['type'] == 'trade']
            trade_count = len(trades)
        else:
            trade_count = sum(1 for e in event_data if e.get('type') == 'trade')
        
        print(f"\nTrade Operations: {trade_count}")
        print(f"  Investment: {trade_count * 100:,} currency")
        print(f"  Wealth created: {trade_count * 5:,} units")
        print()
    
    # Calculate wealth concentration
    if ticks:
        last_tick = ticks[-1]
        agents = last_tick.get('agents', [])
        
        if agents:
            wealth_values = []
            for agent in agents:
                wealth = agent.get('wealth', {})
                wealth_total = sum(wealth.values()) if isinstance(wealth, dict) else 0
                wealth_values.append(wealth_total)
            
            wealth_values.sort(reverse=True)
            total_wealth = sum(wealth_values)
            
            if total_wealth > 0:
                print("Wealth Concentration:")
                top_10_pct = max(1, len(wealth_values) // 10)
                top_10_wealth = sum(wealth_values[:top_10_pct])
                print(f"  Top 10% hold: {(top_10_wealth/total_wealth)*100:.1f}% of wealth")
                
                top_1_pct = max(1, len(wealth_values) // 100)
                top_1_wealth = sum(wealth_values[:top_1_pct])
                print(f"  Top 1% hold: {(top_1_wealth/total_wealth)*100:.1f}% of wealth")


def main():
    """Analyze M|inc outputs."""
    
    print("=" * 60)
    print("M|inc Example: Analyze Outputs")
    print("=" * 60)
    
    # Use output from previous example
    output_dir = Path(__file__).parent / "output" / "historical"
    
    if not output_dir.exists():
        print(f"\nError: Output directory not found: {output_dir}")
        print("\nPlease run 01_process_historical_trace.py first to generate output files.")
        return 1
    
    print(f"\nAnalyzing outputs from: {output_dir}")
    
    # Load data
    print("\nLoading data...")
    tick_data = load_tick_data(output_dir)
    event_data = load_event_data(output_dir)
    
    # Run analyses
    analyze_wealth_dynamics(tick_data)
    analyze_event_patterns(event_data)
    analyze_economic_efficiency(tick_data, event_data)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
