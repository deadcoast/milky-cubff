"""Command-line interface for M|inc."""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from .core.config import ConfigLoader, MIncConfig
from .core.agent_registry import AgentRegistry
from .core.economic_engine import EconomicEngine
from .adapters.trace_reader import TraceReader
from .adapters.output_writer import create_output_writer, generate_metadata


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for M|inc CLI.
    
    Args:
        argv: Command-line arguments (uses sys.argv if None)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="M|inc - Mercenaries Incorporated economic layer for CuBFF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a BFF trace file
  minc --trace testdata/bff_trace.json --config config/minc_default.yaml --output output/ --ticks 100
  
  # Run with live BFF simulation (streaming)
  ./bin/main --lang bff_noheads | minc --stream --config config.yaml --output output/
  
  # Use default configuration
  minc --trace testdata/bff_trace.json --output output/ --ticks 50
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--trace',
        type=Path,
        help='Path to BFF trace file (JSON or gzipped JSON)'
    )
    input_group.add_argument(
        '--stream',
        action='store_true',
        help='Read from stdin (streaming mode)'
    )
    
    # Configuration
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to YAML configuration file (uses defaults if not specified)'
    )
    
    # Output options
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output directory for results'
    )
    
    # Simulation options
    parser.add_argument(
        '--ticks',
        type=int,
        default=100,
        help='Number of ticks to process (default: 100)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed (overrides config)'
    )
    
    # Logging options
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    try:
        # Load configuration
        if args.config:
            logger.info(f"Loading configuration from {args.config}")
            config = ConfigLoader.load(args.config)
        else:
            logger.info("Using default configuration")
            config = ConfigLoader.get_default()
        
        # Override seed if specified
        if args.seed is not None:
            config.seed = args.seed
        
        # Validate configuration
        errors = ConfigLoader.validate(config)
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return 1
        
        # Initialize trace reader
        if args.stream:
            logger.info("Reading from stdin (streaming mode)")
            trace_reader = TraceReader(source=None)
        else:
            logger.info(f"Reading trace from {args.trace}")
            if not args.trace.exists():
                logger.error(f"Trace file not found: {args.trace}")
                return 1
            trace_reader = TraceReader(source=args.trace)
        
        # Initialize output writer
        logger.info(f"Writing output to {args.output}")
        metadata = generate_metadata(
            version=config.version,
            seed=config.seed,
            config_hash=config.compute_hash(),
            additional={"ticks": args.ticks}
        )
        output_writer = create_output_writer(
            output_dir=args.output,
            config=config.output,
            metadata=metadata,
            streaming=args.stream
        )
        
        # Read first epoch to get tape IDs
        logger.info("Reading initial epoch...")
        first_epoch = trace_reader.read_epoch()
        if not first_epoch:
            logger.error("Failed to read initial epoch from trace")
            return 1
        
        tape_ids = list(first_epoch.tapes.keys())
        logger.info(f"Found {len(tape_ids)} tapes in trace")
        
        # Initialize agent registry
        logger.info("Initializing agent registry...")
        registry = AgentRegistry(config.registry, seed=config.seed)
        registry.assign_roles(tape_ids)
        registry.assign_knight_employers()
        
        stats = registry.get_stats()
        logger.info(f"Assigned roles: {stats['kings']} kings, {stats['knights']} knights, {stats['mercenaries']} mercenaries")
        
        # Initialize economic engine
        logger.info("Initializing economic engine...")
        engine = EconomicEngine(registry, config.economic)
        
        # Process ticks
        logger.info(f"Processing {args.ticks} ticks...")
        for tick in range(1, args.ticks + 1):
            # Process tick
            result = engine.process_tick(tick)
            
            # Write outputs
            output_writer.write_tick_json(result)
            output_writer.write_event_csv(result.events)
            
            # Log progress
            if tick % 10 == 0 or args.verbose:
                logger.info(
                    f"Tick {tick}/{args.ticks}: "
                    f"wealth={result.metrics.wealth_total}, "
                    f"currency={result.metrics.currency_total}, "
                    f"events={len(result.events)}"
                )
        
        # Write final agent state
        logger.info("Writing final agent state...")
        output_writer.write_final_agents_csv(registry.get_all_agents())
        
        # Flush and close
        output_writer.close()
        trace_reader.close()
        
        # Print summary
        final_stats = registry.get_stats()
        logger.info("=" * 60)
        logger.info("Simulation complete!")
        logger.info(f"  Ticks processed: {args.ticks}")
        logger.info(f"  Total agents: {final_stats['total_agents']}")
        logger.info(f"  Total wealth: {final_stats['total_wealth']}")
        logger.info(f"  Total currency: {final_stats['total_currency']}")
        logger.info(f"  Output directory: {args.output}")
        logger.info("=" * 60)
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
