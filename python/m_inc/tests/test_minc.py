"""Quick test script for M|inc."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from m_inc.core.config import ConfigLoader
from m_inc.core.agent_registry import AgentRegistry
from m_inc.core.economic_engine import EconomicEngine
from m_inc.adapters.trace_reader import TraceReader
from m_inc.adapters.output_writer import create_output_writer, generate_metadata


def main():
    print("=" * 60)
    print("M|inc Test Run")
    print("=" * 60)
    
    # Load configuration
    config_path = Path(__file__).parent / "config" / "minc_default.yaml"
    print(f"\n1. Loading configuration from {config_path.name}...")
    config = ConfigLoader.load(config_path)
    print(f"   ✓ Configuration loaded (seed={config.seed})")
    
    # Load trace
    trace_path = Path(__file__).parent / "testdata" / "bff_trace_small.json"
    print(f"\n2. Loading trace from {trace_path.name}...")
    trace_reader = TraceReader(trace_path)
    
    # Read first epoch
    first_epoch = trace_reader.read_epoch()
    tape_ids = list(first_epoch.tapes.keys())
    print(f"   ✓ Loaded {len(tape_ids)} tapes")
    
    # Initialize registry
    print(f"\n3. Initializing agent registry...")
    registry = AgentRegistry(config.registry, seed=config.seed)
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    stats = registry.get_stats()
    print(f"   ✓ Assigned roles:")
    print(f"     - Kings: {stats['kings']}")
    print(f"     - Knights: {stats['knights']}")
    print(f"     - Mercenaries: {stats['mercenaries']}")
    print(f"     - Total wealth: {stats['total_wealth']}")
    print(f"     - Total currency: {stats['total_currency']}")
    
    # Initialize engine
    print(f"\n4. Initializing economic engine...")
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)
    print(f"   ✓ Engine ready")
    
    # Initialize output writer
    output_dir = Path(__file__).parent / "test_output"
    print(f"\n5. Initializing output writer...")
    metadata = generate_metadata(
        version=config.version,
        seed=config.seed,
        config_hash=config.compute_hash()
    )
    output_writer = create_output_writer(
        output_dir=output_dir,
        config=config.output,
        metadata=metadata
    )
    print(f"   ✓ Output directory: {output_dir}")
    
    # Process ticks
    num_ticks = 10
    print(f"\n6. Processing {num_ticks} ticks...")
    for tick in range(1, num_ticks + 1):
        result = engine.process_tick(tick)
        output_writer.write_tick_json(result)
        output_writer.write_event_csv(result.events)
        
        print(f"   Tick {tick:2d}: "
              f"wealth={result.metrics.wealth_total:5d}, "
              f"currency={result.metrics.currency_total:6d}, "
              f"events={len(result.events):2d}")
    
    # Write final state
    print(f"\n7. Writing final agent state...")
    output_writer.write_final_agents_csv(registry.get_all_agents())
    output_writer.close()
    print(f"   ✓ Final state written")
    
    # Summary
    final_stats = registry.get_stats()
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print(f"Final Statistics:")
    print(f"  Total agents: {final_stats['total_agents']}")
    print(f"  Total wealth: {final_stats['total_wealth']}")
    print(f"  Total currency: {final_stats['total_currency']}")
    print(f"  Avg wealth: {final_stats['avg_wealth']:.1f}")
    print(f"  Avg currency: {final_stats['avg_currency']:.1f}")
    print(f"\nOutput files:")
    paths = output_writer.get_output_paths()
    for name, path in paths.items():
        if path.exists():
            print(f"  ✓ {name}: {path.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
