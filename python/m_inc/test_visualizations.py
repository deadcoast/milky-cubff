#!/usr/bin/env python3
"""
Test script for visualization functions.

Tests that visualization code can load data and prepare plots
without requiring matplotlib to be installed.
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_load_tick_data():
    """Test loading tick data."""
    print("Testing tick data loading...")
    
    output_dir = Path(__file__).parent / "examples" / "output" / "historical"
    tick_file = output_dir / "ticks.json"
    
    if not tick_file.exists():
        print(f"  SKIP: Tick file not found: {tick_file}")
        return False
    
    with open(tick_file, 'r') as f:
        data = json.load(f)
        if isinstance(data, dict):
            data = [data]
    
    print(f"  OK: Loaded {len(data)} ticks")
    
    # Verify structure
    if data:
        first_tick = data[0]
        assert 'tick' in first_tick, "Missing 'tick' field"
        assert 'metrics' in first_tick, "Missing 'metrics' field"
        assert 'agents' in first_tick, "Missing 'agents' field"
        print(f"  OK: Tick structure valid")
    
    return True


def test_load_event_data():
    """Test loading event data."""
    print("\nTesting event data loading...")
    
    output_dir = Path(__file__).parent / "examples" / "output" / "historical"
    event_file = output_dir / "events.csv"
    
    if not event_file.exists():
        print(f"  SKIP: Event file not found: {event_file}")
        return False
    
    events = []
    with open(event_file, 'r') as f:
        header = f.readline().strip().split(',')
        for line in f:
            values = line.strip().split(',')
            events.append(dict(zip(header, values)))
    
    print(f"  OK: Loaded {len(events)} events")
    
    # Verify structure
    if events:
        first_event = events[0]
        assert 'tick' in first_event, "Missing 'tick' field"
        assert 'type' in first_event, "Missing 'type' field"
        print(f"  OK: Event structure valid")
    
    return True


def test_wealth_distribution_data():
    """Test extracting wealth distribution data."""
    print("\nTesting wealth distribution data extraction...")
    
    output_dir = Path(__file__).parent / "examples" / "output" / "historical"
    tick_file = output_dir / "ticks.json"
    
    if not tick_file.exists():
        print(f"  SKIP: Tick file not found")
        return False
    
    with open(tick_file, 'r') as f:
        tick_data = json.load(f)
        if isinstance(tick_data, dict):
            tick_data = [tick_data]
    
    # Extract wealth by role
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
    
    print(f"  OK: Extracted wealth data for {len(ticks)} ticks")
    print(f"  OK: Kings wealth range: {min(king_wealth)} - {max(king_wealth)}")
    print(f"  OK: Knights wealth range: {min(knight_wealth)} - {max(knight_wealth)}")
    print(f"  OK: Mercs wealth range: {min(merc_wealth)} - {max(merc_wealth)}")
    
    return True


def test_agent_trajectories_data():
    """Test extracting agent trajectory data."""
    print("\nTesting agent trajectories data extraction...")
    
    output_dir = Path(__file__).parent / "examples" / "output" / "historical"
    tick_file = output_dir / "ticks.json"
    
    if not tick_file.exists():
        print(f"  SKIP: Tick file not found")
        return False
    
    with open(tick_file, 'r') as f:
        tick_data = json.load(f)
        if isinstance(tick_data, dict):
            tick_data = [tick_data]
    
    # Track individual agents
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
    
    print(f"  OK: Tracked {len(agent_histories)} agents")
    
    # Find top agents
    sorted_agents = sorted(agent_histories.items(), 
                          key=lambda x: x[1]['wealth'][-1] if x[1]['wealth'] else 0,
                          reverse=True)
    
    if sorted_agents:
        top_agent_id, top_history = sorted_agents[0]
        print(f"  OK: Top agent: {top_agent_id} ({top_history['role']}) with final wealth {top_history['wealth'][-1]}")
    
    return True


def test_event_patterns():
    """Test extracting event pattern data."""
    print("\nTesting event pattern data extraction...")
    
    output_dir = Path(__file__).parent / "examples" / "output" / "historical"
    event_file = output_dir / "events.csv"
    
    if not event_file.exists():
        print(f"  SKIP: Event file not found")
        return False
    
    events = []
    with open(event_file, 'r') as f:
        header = f.readline().strip().split(',')
        for line in f:
            values = line.strip().split(',')
            events.append(dict(zip(header, values)))
    
    # Count event types
    event_counts = defaultdict(int)
    for event in events:
        event_type = event.get('type', 'unknown')
        event_counts[event_type] += 1
    
    print(f"  OK: Found {len(event_counts)} event types")
    for event_type, count in sorted(event_counts.items()):
        print(f"    - {event_type}: {count}")
    
    return True


def test_wealth_traits_data():
    """Test extracting wealth traits data."""
    print("\nTesting wealth traits data extraction...")
    
    output_dir = Path(__file__).parent / "examples" / "output" / "historical"
    tick_file = output_dir / "ticks.json"
    
    if not tick_file.exists():
        print(f"  SKIP: Tick file not found")
        return False
    
    with open(tick_file, 'r') as f:
        tick_data = json.load(f)
        if isinstance(tick_data, dict):
            tick_data = [tick_data]
    
    # Track traits over time
    trait_names = ['compute', 'copy', 'defend', 'raid', 'trade', 'sense', 'adapt']
    trait_totals = defaultdict(list)
    
    for tick in tick_data:
        agents = tick.get('agents', [])
        tick_traits = {trait: 0 for trait in trait_names}
        
        for agent in agents:
            wealth = agent.get('wealth', {})
            for trait in trait_names:
                tick_traits[trait] += wealth.get(trait, 0)
        
        for trait in trait_names:
            trait_totals[trait].append(tick_traits[trait])
    
    print(f"  OK: Extracted trait data for {len(tick_data)} ticks")
    for trait in trait_names:
        values = trait_totals[trait]
        if values:
            print(f"    - {trait}: {min(values)} - {max(values)}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("M|inc Visualization Data Tests")
    print("=" * 60)
    
    tests = [
        test_load_tick_data,
        test_load_event_data,
        test_wealth_distribution_data,
        test_agent_trajectories_data,
        test_event_patterns,
        test_wealth_traits_data,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Tests: {passed}/{total} passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✓ All visualization data extraction tests passed!")
        print("\nNote: Actual plot generation requires matplotlib:")
        print("  pip install matplotlib seaborn")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
