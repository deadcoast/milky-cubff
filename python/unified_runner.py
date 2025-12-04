#!/usr/bin/env python3
"""Unified Runner for CuBFF + BFFx + M|inc Integration.

This script provides a single entry point for running BFF simulations
with M|inc economic analysis across all supported modes:

1. BFFx Mode: Pure Python BFF simulation → M|inc
2. Binary Trace Mode: Existing trace file → M|inc
3. JSON Trace Mode: Existing JSON trace → M|inc

Usage:
    # Run BFFx simulation with M|inc
    python unified_runner.py bffx --population 100 --epochs 1000 --ticks 100 --output output/

    # Process binary trace with M|inc
    python unified_runner.py trace --input trace.bin --config config.yaml --output output/

    # Process JSON trace with M|inc
    python unified_runner.py json --input trace.json --config config.yaml --output output/

    # Convert binary trace to JSON (no M|inc)
    python unified_runner.py convert --input trace.bin --output trace.json
"""

import argparse
import sys
import logging
import random
from pathlib import Path
from typing import Optional, Iterator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def run_bffx_mode(
    population_size: int,
    num_epochs: int,
    num_ticks: int,
    seed: Optional[int],
    step_limit: int,
    mutation_p: float,
    config_path: Optional[Path],
    output_dir: Path,
    verbose: bool
) -> int:
    """Run BFFx simulation with M|inc processing.

    Args:
        population_size: Number of programs in soup
        num_epochs: Number of BFF epochs to run
        num_ticks: Number of M|inc ticks to process
        seed: Random seed
        step_limit: Max VM steps per interaction
        mutation_p: Mutation probability
        config_path: Path to M|inc config (or None for defaults)
        output_dir: Output directory
        verbose: Verbose logging

    Returns:
        Exit code (0 for success)
    """
    from bffx import Soup
    from bffx.scheduler import random_disjoint_pairs

    from m_inc.adapters.bffx_bridge import BFFxBridge
    from m_inc.core.config import ConfigLoader
    from m_inc.core.agent_registry import AgentRegistry
    from m_inc.core.economic_engine import EconomicEngine
    from m_inc.adapters.output_writer import create_output_writer, generate_metadata

    logger.info("=" * 60)
    logger.info("UNIFIED RUNNER: BFFx Mode")
    logger.info("=" * 60)

    # Load config
    if config_path:
        config = ConfigLoader.load(config_path)
    else:
        config = ConfigLoader.get_default()

    if seed is not None:
        config.seed = seed

    # Initialize BFFx
    logger.info(f"Initializing BFFx soup (population={population_size}, seed={config.seed})")
    rng = random.Random(config.seed)
    soup = Soup(size=population_size, rng=rng)
    bridge = BFFxBridge(soup, compute_metrics=True)

    # Get initial population snapshot for agent registration
    initial_epoch = bridge.snapshot_to_epoch()
    tape_ids = list(initial_epoch.tapes.keys())

    # Initialize M|inc
    logger.info(f"Initializing M|inc registry with {len(tape_ids)} agents")
    registry = AgentRegistry(config.registry, seed=config.seed)
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()

    stats = registry.get_stats()
    logger.info(f"Roles: {stats['kings']} kings, {stats['knights']} knights, {stats['mercenaries']} mercenaries")

    # Initialize engine
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)

    # Initialize output
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = generate_metadata(
        version=config.version,
        seed=config.seed,
        config_hash=config.compute_hash(),
        additional={
            "mode": "bffx",
            "population_size": population_size,
            "num_epochs": num_epochs,
            "num_ticks": num_ticks
        }
    )
    output_writer = create_output_writer(
        output_dir=output_dir,
        config=config.output,
        metadata=metadata,
        streaming=False
    )

    # Run simulation
    logger.info(f"Running {num_epochs} BFFx epochs with {num_ticks} M|inc ticks...")
    epochs_per_tick = max(1, num_epochs // num_ticks)

    for tick in range(1, num_ticks + 1):
        # Run BFFx epochs
        for _ in range(epochs_per_tick):
            outcomes = soup.epoch(
                scheduler=random_disjoint_pairs,
                step_limit=step_limit,
                mutation_p=mutation_p,
                record_outcomes=True
            )

        # Get epoch data with metrics
        epoch_data = bridge.convert_outcomes_to_epoch(outcomes)

        # Update engine with BFF metrics (for future use)
        # This allows trait emergence rules to access BFF analytics

        # Process M|inc tick
        result = engine.process_tick(tick)

        # Inject BFF metrics into result
        if epoch_data.metrics:
            result.metrics.entropy = epoch_data.metrics.get("entropy", 0.0)
            result.metrics.compression_ratio = epoch_data.metrics.get("compression_ratio", 0.0)

        # Write outputs
        output_writer.write_tick_json(result)
        output_writer.write_event_csv(result.events)

        if tick % 10 == 0 or verbose:
            logger.info(
                f"Tick {tick}/{num_ticks}: "
                f"epoch={soup.epoch_index}, "
                f"entropy={result.metrics.entropy:.2f}, "
                f"wealth={result.metrics.wealth_total}"
            )

    # Write final state
    output_writer.write_final_agents_csv(registry.get_all_agents())
    output_writer.close()

    # Summary
    final_stats = registry.get_stats()
    logger.info("=" * 60)
    logger.info("Simulation Complete!")
    logger.info(f"  BFFx epochs: {soup.epoch_index}")
    logger.info(f"  M|inc ticks: {num_ticks}")
    logger.info(f"  Total wealth: {final_stats['total_wealth']}")
    logger.info(f"  Total currency: {final_stats['total_currency']}")
    logger.info(f"  Output: {output_dir}")
    logger.info("=" * 60)

    return 0


def run_trace_mode(
    input_path: Path,
    config_path: Optional[Path],
    output_dir: Path,
    num_ticks: int,
    verbose: bool
) -> int:
    """Run M|inc on binary BFF trace file.

    Args:
        input_path: Path to binary trace
        config_path: Path to config file
        output_dir: Output directory
        num_ticks: Number of ticks
        verbose: Verbose logging

    Returns:
        Exit code
    """
    from m_inc.adapters.bff_bridge import BFFBridge
    from m_inc.core.config import ConfigLoader
    from m_inc.core.agent_registry import AgentRegistry
    from m_inc.core.economic_engine import EconomicEngine
    from m_inc.adapters.output_writer import create_output_writer, generate_metadata

    logger.info("=" * 60)
    logger.info("UNIFIED RUNNER: Binary Trace Mode")
    logger.info("=" * 60)

    # Load config
    if config_path:
        config = ConfigLoader.load(config_path)
    else:
        config = ConfigLoader.get_default()

    # Open bridge
    logger.info(f"Reading binary trace: {input_path}")
    bridge = BFFBridge(input_path)

    # Read first epoch
    first_epoch = bridge.read_state_as_epoch()
    if not first_epoch:
        logger.error("Failed to read initial epoch from trace")
        return 1

    tape_ids = list(first_epoch.tapes.keys())
    logger.info(f"Found {len(tape_ids)} tapes in trace")

    # Initialize M|inc
    registry = AgentRegistry(config.registry, seed=config.seed)
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()

    engine = EconomicEngine(registry, config.economic, config.trait_emergence)

    # Initialize output
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = generate_metadata(
        version=config.version,
        seed=config.seed,
        config_hash=config.compute_hash(),
        additional={"mode": "binary_trace", "trace": str(input_path)}
    )
    output_writer = create_output_writer(
        output_dir=output_dir,
        config=config.output,
        metadata=metadata,
        streaming=False
    )

    # Process ticks
    logger.info(f"Processing {num_ticks} ticks...")
    for tick in range(1, num_ticks + 1):
        result = engine.process_tick(tick)
        output_writer.write_tick_json(result)
        output_writer.write_event_csv(result.events)

        if tick % 10 == 0 or verbose:
            logger.info(f"Tick {tick}/{num_ticks}: wealth={result.metrics.wealth_total}")

    output_writer.write_final_agents_csv(registry.get_all_agents())
    output_writer.close()
    bridge.close()

    logger.info(f"Output written to: {output_dir}")
    return 0


def run_json_mode(
    input_path: Path,
    config_path: Optional[Path],
    output_dir: Path,
    num_ticks: int,
    verbose: bool
) -> int:
    """Run M|inc on JSON trace file.

    Args:
        input_path: Path to JSON trace
        config_path: Path to config file
        output_dir: Output directory
        num_ticks: Number of ticks
        verbose: Verbose logging

    Returns:
        Exit code
    """
    from m_inc.adapters.trace_reader import TraceReader
    from m_inc.core.config import ConfigLoader
    from m_inc.core.agent_registry import AgentRegistry
    from m_inc.core.economic_engine import EconomicEngine
    from m_inc.adapters.output_writer import create_output_writer, generate_metadata

    logger.info("=" * 60)
    logger.info("UNIFIED RUNNER: JSON Trace Mode")
    logger.info("=" * 60)

    # Load config
    if config_path:
        config = ConfigLoader.load(config_path)
    else:
        config = ConfigLoader.get_default()

    # Open reader
    logger.info(f"Reading JSON trace: {input_path}")
    reader = TraceReader(input_path)

    # Read first epoch
    first_epoch = reader.read_epoch()
    if not first_epoch:
        logger.error("Failed to read initial epoch from trace")
        return 1

    tape_ids = list(first_epoch.tapes.keys())
    logger.info(f"Found {len(tape_ids)} tapes in trace")

    # Initialize M|inc
    registry = AgentRegistry(config.registry, seed=config.seed)
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()

    engine = EconomicEngine(registry, config.economic, config.trait_emergence)

    # Initialize output
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = generate_metadata(
        version=config.version,
        seed=config.seed,
        config_hash=config.compute_hash(),
        additional={"mode": "json_trace", "trace": str(input_path)}
    )
    output_writer = create_output_writer(
        output_dir=output_dir,
        config=config.output,
        metadata=metadata,
        streaming=False
    )

    # Process ticks
    logger.info(f"Processing {num_ticks} ticks...")
    for tick in range(1, num_ticks + 1):
        # Read next epoch for metrics if available
        epoch = reader.read_epoch()

        result = engine.process_tick(tick)

        # Inject trace metrics if available
        if epoch and epoch.metrics:
            result.metrics.entropy = epoch.metrics.get("entropy", 0.0)
            result.metrics.compression_ratio = epoch.metrics.get("compression_ratio", 0.0)

        output_writer.write_tick_json(result)
        output_writer.write_event_csv(result.events)

        if tick % 10 == 0 or verbose:
            logger.info(f"Tick {tick}/{num_ticks}: wealth={result.metrics.wealth_total}")

    output_writer.write_final_agents_csv(registry.get_all_agents())
    output_writer.close()
    reader.close()

    logger.info(f"Output written to: {output_dir}")
    return 0


def run_convert_mode(input_path: Path, output_path: Path, num_states: Optional[int]) -> int:
    """Convert binary trace to JSON format.

    Args:
        input_path: Path to binary trace
        output_path: Path to output JSON
        num_states: Number of states to convert (None for all)

    Returns:
        Exit code
    """
    from m_inc.adapters.bff_bridge import convert_bff_trace_to_json

    logger.info("=" * 60)
    logger.info("UNIFIED RUNNER: Convert Mode")
    logger.info("=" * 60)

    logger.info(f"Converting {input_path} → {output_path}")
    convert_bff_trace_to_json(input_path, output_path, num_states)
    logger.info("Conversion complete!")

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Runner for CuBFF + BFFx + M|inc Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  bffx      Run pure Python BFFx simulation with M|inc economic layer
  trace     Process existing binary BFF trace file with M|inc
  json      Process existing JSON trace file with M|inc
  convert   Convert binary trace to JSON format (no M|inc processing)

Examples:
  # Run 1000 BFFx epochs with 100 M|inc economic ticks
  %(prog)s bffx --population 100 --epochs 1000 --ticks 100 --output results/

  # Process existing binary trace
  %(prog)s trace --input simulation.bin --config config.yaml --output results/

  # Convert binary to JSON for analysis
  %(prog)s convert --input trace.bin --output trace.json
        """
    )

    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")

    # BFFx mode
    bffx_parser = subparsers.add_parser("bffx", help="Run BFFx simulation with M|inc")
    bffx_parser.add_argument("--population", type=int, default=100,
                            help="Soup population size (default: 100)")
    bffx_parser.add_argument("--epochs", type=int, default=1000,
                            help="Number of BFFx epochs (default: 1000)")
    bffx_parser.add_argument("--ticks", type=int, default=100,
                            help="Number of M|inc ticks (default: 100)")
    bffx_parser.add_argument("--seed", type=int, help="Random seed")
    bffx_parser.add_argument("--step-limit", type=int, default=8192,
                            help="Max VM steps per interaction (default: 8192)")
    bffx_parser.add_argument("--mutation", type=float, default=0.0,
                            help="Per-byte mutation probability (default: 0.0)")
    bffx_parser.add_argument("--config", type=Path, help="M|inc config file")
    bffx_parser.add_argument("--output", type=Path, required=True,
                            help="Output directory")
    bffx_parser.add_argument("-v", "--verbose", action="store_true",
                            help="Verbose output")

    # Binary trace mode
    trace_parser = subparsers.add_parser("trace", help="Process binary trace with M|inc")
    trace_parser.add_argument("--input", type=Path, required=True,
                             help="Input binary trace file")
    trace_parser.add_argument("--config", type=Path, help="M|inc config file")
    trace_parser.add_argument("--output", type=Path, required=True,
                             help="Output directory")
    trace_parser.add_argument("--ticks", type=int, default=100,
                             help="Number of M|inc ticks (default: 100)")
    trace_parser.add_argument("-v", "--verbose", action="store_true",
                             help="Verbose output")

    # JSON trace mode
    json_parser = subparsers.add_parser("json", help="Process JSON trace with M|inc")
    json_parser.add_argument("--input", type=Path, required=True,
                            help="Input JSON trace file")
    json_parser.add_argument("--config", type=Path, help="M|inc config file")
    json_parser.add_argument("--output", type=Path, required=True,
                            help="Output directory")
    json_parser.add_argument("--ticks", type=int, default=100,
                            help="Number of M|inc ticks (default: 100)")
    json_parser.add_argument("-v", "--verbose", action="store_true",
                            help="Verbose output")

    # Convert mode
    convert_parser = subparsers.add_parser("convert", help="Convert binary trace to JSON")
    convert_parser.add_argument("--input", type=Path, required=True,
                               help="Input binary trace file")
    convert_parser.add_argument("--output", type=Path, required=True,
                               help="Output JSON file")
    convert_parser.add_argument("--num-states", type=int,
                               help="Number of states to convert (default: all)")

    args = parser.parse_args()

    if args.mode is None:
        parser.print_help()
        return 1

    try:
        if args.mode == "bffx":
            return run_bffx_mode(
                population_size=args.population,
                num_epochs=args.epochs,
                num_ticks=args.ticks,
                seed=args.seed,
                step_limit=args.step_limit,
                mutation_p=args.mutation,
                config_path=args.config,
                output_dir=args.output,
                verbose=args.verbose
            )
        elif args.mode == "trace":
            return run_trace_mode(
                input_path=args.input,
                config_path=args.config,
                output_dir=args.output,
                num_ticks=args.ticks,
                verbose=args.verbose
            )
        elif args.mode == "json":
            return run_json_mode(
                input_path=args.input,
                config_path=args.config,
                output_dir=args.output,
                num_ticks=args.ticks,
                verbose=args.verbose
            )
        elif args.mode == "convert":
            return run_convert_mode(
                input_path=args.input,
                output_path=args.output,
                num_states=args.num_states
            )
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
