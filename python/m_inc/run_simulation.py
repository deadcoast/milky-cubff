"""Run a full M|inc simulation with detailed output."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from m_inc.core.config import ConfigLoader
from m_inc.core.agent_registry import AgentRegistry
from m_inc.core.economic_engine import EconomicEngine
from m_inc.adapters.trace_reader import TraceReader
from m_inc.adapters.output_writer import create_output_writer, generate_metadata


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_tick_summary(tick, result):
    """Print a summary of a tick's results."""
    m = result.metrics
    print(f"Tick {tick:3d} | "
          f"Wealth: {m.wealth_total:5d} | "
          f"Currency: {m.currency_total:10d} | "
          f"Events: {len(result.events):3d} | "
          f"Bribes: {m.bribes_accepted}/{m.bribes_paid} | "
          f"Raids: {m.raids_won_by_knight}/{m.raids_attempted}")


def main():
    print_header("M|inc Economic Simulation")
    
    # Configuration
    config_path = Path(__file__).parent / "config" / "minc_default.yaml"
    trace_path = Path(__file__).parent / "testdata" / "bff_trace_medium.json"
    output_dir = Path(__file__).parent / "simulation_output"
    num_ticks = 50
    
    print(f"\nConfiguration:")
    print(f"  Config: {config_path.name}")
    print(f"  Trace: {trace_path.name}")
    print(f"  Output: {output_dir}")
    print(f"  Ticks: {num_ticks}")
    
    # Load configuration
    print("\n[1/6] Loading configuration...")
    config = ConfigLoader.load(config_path)
    print(f"      ✓ Seed: {config.seed}")
    print(f"      ✓ King ratio: {config.registry.role_ratios['king']:.0%}")
    print(f"      ✓ Knight ratio: {config.registry.role_ratios['knight']:.0%}")
    print(f"      ✓ Mercenary ratio: {config.registry.role_ratios['mercenary']:.0%}")
    
    # Load trace
    print("\n[2/6] Loading BFF trace...")
    trace_reader = TraceReader(trace_path)
    first_epoch = trace_reader.read_epoch()
    tape_ids = list(first_epoch.tapes.keys())
    print(f"      ✓ Loaded {len(tape_ids)} tapes")
    
    # Initialize registry
    print("\n[3/6] Initializing agent registry...")
    registry = AgentRegistry(config.registry, seed=config.seed)
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    stats = registry.get_stats()
    print(f"      ✓ Kings: {stats['kings']}")
    print(f"      ✓ Knights: {stats['knights']}")
    print(f"      ✓ Mercenaries: {stats['mercenaries']}")
    print(f"      ✓ Initial wealth: {stats['total_wealth']}")
    print(f"      ✓ Initial currency: {stats['total_currency']}")
    
    # Initialize engine
    print("\n[4/6] Initializing economic engine...")
    engine = EconomicEngine(registry, config.economic)
    print(f"      ✓ Engine ready")
    
    # Initialize output writer
    print("\n[5/6] Initializing output writer...")
    metadata = generate_metadata(
        version=config.version,
        seed=config.seed,
        config_hash=config.compute_hash(),
        additional={"ticks": num_ticks, "trace": trace_path.name}
    )
    output_writer = create_output_writer(
        output_dir=output_dir,
        config=config.output,
        metadata=metadata
    )
    print(f"      ✓ Output directory created")
    
    # Process ticks
    print_header(f"Processing {num_ticks} Ticks")
    print("\nTick    | Wealth | Currency   | Events | Bribes | Raids")
    print("-" * 70)
    
    for tick in range(1, num_ticks + 1):
        result = engine.process_tick(tick)
        output_writer.write_tick_json(result)
        output_writer.write_event_csv(result.events)
        
        # Print every 5 ticks
        if tick % 5 == 0 or tick == 1:
            print_tick_summary(tick, result)
    
    # Write final state
    print("\n[6/6] Writing final agent state...")
    output_writer.write_final_agents_csv(registry.get_all_agents())
    output_writer.close()
    trace_reader.close()
    print(f"      ✓ Final state written")
    
    # Final summary
    final_stats = registry.get_stats()
    print_header("Simulation Complete")
    
    print(f"\nFinal Statistics:")
    print(f"  Total agents: {final_stats['total_agents']}")
    print(f"  Total wealth: {final_stats['total_wealth']} (Δ {final_stats['total_wealth'] - stats['total_wealth']:+d})")
    print(f"  Total currency: {final_stats['total_currency']:,} (Δ {final_stats['total_currency'] - stats['total_currency']:+,})")
    print(f"  Avg wealth per agent: {final_stats['avg_wealth']:.1f}")
    print(f"  Avg currency per agent: {final_stats['avg_currency']:,.1f}")
    
    print(f"\nRole Distribution:")
    kings = registry.get_kings()
    knights = registry.get_knights()
    mercs = registry.get_mercenaries()
    
    king_wealth = sum(k.wealth_total() for k in kings)
    knight_wealth = sum(k.wealth_total() for k in knights)
    merc_wealth = sum(m.wealth_total() for m in mercs)
    
    king_currency = sum(k.currency for k in kings)
    knight_currency = sum(k.currency for k in knights)
    merc_currency = sum(m.currency for m in mercs)
    
    print(f"  Kings: {len(kings)} agents")
    print(f"    - Total wealth: {king_wealth} ({king_wealth/final_stats['total_wealth']*100:.1f}%)")
    print(f"    - Total currency: {king_currency:,} ({king_currency/final_stats['total_currency']*100:.1f}%)")
    print(f"  Knights: {len(knights)} agents")
    print(f"    - Total wealth: {knight_wealth} ({knight_wealth/final_stats['total_wealth']*100:.1f}%)")
    print(f"    - Total currency: {knight_currency:,} ({knight_currency/final_stats['total_currency']*100:.1f}%)")
    print(f"  Mercenaries: {len(mercs)} agents")
    print(f"    - Total wealth: {merc_wealth} ({merc_wealth/final_stats['total_wealth']*100:.1f}%)")
    print(f"    - Total currency: {merc_currency:,} ({merc_currency/final_stats['total_currency']*100:.1f}%)")
    
    print(f"\nOutput Files:")
    paths = output_writer.get_output_paths()
    for name, path in paths.items():
        if path.exists():
            size = path.stat().st_size / 1024
            print(f"  ✓ {name}: {path.name} ({size:.1f} KB)")
    
    print("\n" + "=" * 70)
    print("  Simulation data saved to:", output_dir)
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
