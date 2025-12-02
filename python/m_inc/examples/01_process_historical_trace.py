#!/usr/bin/env python3
"""
Example: Process Historical BFF Trace

This example demonstrates how to process an existing BFF trace file
with M|inc to analyze economic dynamics.

Usage:
    python 01_process_historical_trace.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from m_inc.core.agent_registry import AgentRegistry, RegistryConfig
from m_inc.core.economic_engine import EconomicEngine, EconomicConfig
from m_inc.adapters.trace_reader import TraceReader
from m_inc.adapters.output_writer import OutputWriter, OutputConfig
from m_inc.core.config import ConfigLoader


def main():
    """Process a historical BFF trace with M|inc."""
    
    # Configuration
    trace_file = Path(__file__).parent.parent / "testdata" / "bff_trace_small.json"
    config_file = Path(__file__).parent.parent / "config" / "minc_default.yaml"
    output_dir = Path(__file__).parent / "output" / "historical"
    num_ticks = 10
    
    print("=" * 60)
    print("M|inc Example: Process Historical BFF Trace")
    print("=" * 60)
    print(f"Trace file: {trace_file}")
    print(f"Config: {config_file}")
    print(f"Output: {output_dir}")
    print(f"Ticks: {num_ticks}")
    print()
    
    # Load configuration
    print("Loading configuration...")
    config = ConfigLoader.load(config_file)
    print(f"  Role ratios: {config.registry.role_ratios}")
    print(f"  Cache enabled: {config.cache.enabled}")
    print()
    
    # Initialize components
    print("Initializing components...")
    trace_reader = TraceReader(trace_file)
    
    registry = AgentRegistry(config.registry)
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)
    
    output_config = OutputConfig(
        json_ticks=True,
        csv_events=True,
        csv_final_agents=True,
        compress=False
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    writer = OutputWriter(output_dir, output_config)
    print("  Components initialized")
    print()
    
    # Read initial epoch and assign roles
    print("Reading initial epoch and assigning roles...")
    epoch = trace_reader.read_epoch()
    tape_ids = list(epoch.tapes.keys())
    registry.assign_roles(tape_ids)
    
    kings = registry.get_agents_by_role("king")
    knights = registry.get_agents_by_role("knight")
    mercs = registry.get_agents_by_role("mercenary")
    print(f"  Assigned roles: {len(kings)} Kings, {len(knights)} Knights, {len(mercs)} Mercenaries")
    print()
    
    # Process ticks
    print("Processing ticks...")
    print("-" * 60)
    
    all_events = []
    
    for tick in range(1, num_ticks + 1):
        # Process tick
        result = engine.process_tick(tick)
        
        # Collect events
        all_events.extend(result.events)
        
        # Write tick snapshot
        writer.write_tick_json(result)
        
        # Display summary
        print(f"Tick {tick:3d}: "
              f"Wealth={result.metrics.wealth_total:6d}, "
              f"Currency={result.metrics.currency_total:7d}, "
              f"Events={len(result.events):3d}, "
              f"Bribes={result.metrics.bribes_accepted:2d}, "
              f"Raids={result.metrics.raids_attempted:2d}")
    
    print("-" * 60)
    print()
    
    # Write final outputs
    print("Writing final outputs...")
    writer.flush_ticks()  # Write accumulated tick snapshots
    writer.write_event_csv(all_events)
    
    all_agents = []
    for role in ["king", "knight", "mercenary"]:
        all_agents.extend(registry.get_agents_by_role(role))
    writer.write_final_agents_csv(all_agents)
    
    print(f"  Wrote {len(all_events)} events to CSV")
    print(f"  Wrote {len(all_agents)} final agent states to CSV")
    print()
    
    # Summary statistics
    print("Summary Statistics:")
    print(f"  Total events: {len(all_events)}")
    
    event_counts = {}
    for event in all_events:
        event_counts[event.type.value] = event_counts.get(event.type.value, 0) + 1
    
    for event_type, count in sorted(event_counts.items()):
        print(f"    {event_type}: {count}")
    
    print()
    print(f"Output files written to: {output_dir}")
    print("  - ticks.json (per-tick snapshots)")
    print("  - events.csv (event log)")
    print("  - agents_final.csv (final agent states)")
    print()
    print("Done!")


if __name__ == "__main__":
    main()
