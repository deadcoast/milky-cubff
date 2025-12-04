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


def process_single_trace(trace_path: Path, config: MIncConfig, output_dir: Path, 
                        num_ticks: int, verbose: bool = False) -> dict:
    """Process a single trace file.
    
    Args:
        trace_path: Path to trace file
        config: M|inc configuration
        output_dir: Output directory
        num_ticks: Number of ticks to process
        verbose: Enable verbose logging
        
    Returns:
        Dict with summary statistics
    """
    try:
        # Initialize trace reader
        trace_reader = TraceReader(source=trace_path)
        
        # Initialize output writer
        metadata = generate_metadata(
            version=config.version,
            seed=config.seed,
            config_hash=config.compute_hash(),
            additional={"ticks": num_ticks, "trace": str(trace_path)}
        )
        output_writer = create_output_writer(
            output_dir=output_dir,
            config=config.output,
            metadata=metadata,
            streaming=False
        )
        
        # Read first epoch to get tape IDs
        first_epoch = trace_reader.read_epoch()
        if not first_epoch:
            logger.error(f"Failed to read initial epoch from {trace_path}")
            return {"success": False, "error": "Failed to read initial epoch"}
        
        tape_ids = list(first_epoch.tapes.keys())
        
        # Initialize agent registry
        registry = AgentRegistry(config.registry, seed=config.seed)
        registry.assign_roles(tape_ids)
        registry.assign_knight_employers()
        
        # Initialize economic engine
        engine = EconomicEngine(registry, config.economic, config.trait_emergence)
        
        # Process ticks
        for tick in range(1, num_ticks + 1):
            result = engine.process_tick(tick)
            output_writer.write_tick_json(result)
            output_writer.write_event_csv(result.events)
        
        # Write final agent state
        output_writer.write_final_agents_csv(registry.get_all_agents())
        output_writer.close()
        trace_reader.close()
        
        # Return summary
        final_stats = registry.get_stats()
        return {
            "success": True,
            "trace": str(trace_path),
            "ticks": num_ticks,
            "agents": final_stats['total_agents'],
            "wealth": final_stats['total_wealth'],
            "currency": final_stats['total_currency']
        }
    
    except Exception as e:
        logger.error(f"Error processing {trace_path}: {e}")
        return {"success": False, "trace": str(trace_path), "error": str(e)}


def process_batch(trace_paths: list[Path], config: MIncConfig, output_base: Path,
                 num_ticks: int, num_workers: int = 1, verbose: bool = False) -> list[dict]:
    """Process multiple trace files in batch mode.
    
    Args:
        trace_paths: List of trace file paths
        config: M|inc configuration
        output_base: Base output directory
        num_ticks: Number of ticks to process per trace
        num_workers: Number of parallel workers
        verbose: Enable verbose logging
        
    Returns:
        List of summary dicts for each trace
    """
    import concurrent.futures
    import time
    
    logger.info(f"Processing {len(trace_paths)} traces with {num_workers} workers")
    
    results = []
    start_time = time.time()
    
    if num_workers == 1:
        # Sequential processing
        for i, trace_path in enumerate(trace_paths, 1):
            logger.info(f"Processing trace {i}/{len(trace_paths)}: {trace_path.name}")
            output_dir = output_base / trace_path.stem
            result = process_single_trace(trace_path, config, output_dir, num_ticks, verbose)
            results.append(result)
    else:
        # Parallel processing
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {}
            for trace_path in trace_paths:
                output_dir = output_base / trace_path.stem
                future = executor.submit(
                    process_single_trace, trace_path, config, output_dir, num_ticks, verbose
                )
                futures[future] = trace_path
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                trace_path = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result["success"]:
                        logger.info(f"Completed: {trace_path.name}")
                    else:
                        logger.error(f"Failed: {trace_path.name}")
                except Exception as e:
                    logger.error(f"Exception processing {trace_path.name}: {e}")
                    results.append({
                        "success": False,
                        "trace": str(trace_path),
                        "error": str(e)
                    })
    
    elapsed = time.time() - start_time
    logger.info(f"Batch processing complete in {elapsed:.2f}s")
    
    return results


def generate_batch_summary(results: list[dict], output_path: Path) -> None:
    """Generate a summary report for batch processing.
    
    Args:
        results: List of result dicts from batch processing
        output_path: Path to write summary report
    """
    import json
    
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]
    
    summary = {
        "total_traces": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "results": results
    }
    
    # Add aggregate statistics
    if successful:
        summary["aggregate"] = {
            "total_agents": sum(r.get("agents", 0) for r in successful),
            "total_wealth": sum(r.get("wealth", 0) for r in successful),
            "total_currency": sum(r.get("currency", 0) for r in successful),
            "avg_agents": sum(r.get("agents", 0) for r in successful) / len(successful),
            "avg_wealth": sum(r.get("wealth", 0) for r in successful) / len(successful),
            "avg_currency": sum(r.get("currency", 0) for r in successful) / len(successful)
        }
    
    # Write summary
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Batch summary written to {output_path}")


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
  
  # Process multiple traces in batch mode
  minc --batch trace1.json trace2.json trace3.json --output batch_output/ --ticks 50
  
  # Process batch with parallel workers
  minc --batch traces/*.json --output batch_output/ --parallel 4 --ticks 100
  
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
    input_group.add_argument(
        '--batch',
        type=Path,
        nargs='+',
        help='Process multiple trace files in batch mode'
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
        '--parallel',
        type=int,
        default=1,
        help='Number of parallel workers for batch mode (default: 1)'
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
        
        # Handle batch mode
        if args.batch:
            logger.info(f"Running in batch mode with {len(args.batch)} traces")
            
            # Validate all trace files exist
            missing = [p for p in args.batch if not p.exists()]
            if missing:
                logger.error("Some trace files not found:")
                for p in missing:
                    logger.error(f"  - {p}")
                return 1
            
            # Process batch
            results = process_batch(
                trace_paths=args.batch,
                config=config,
                output_base=args.output,
                num_ticks=args.ticks,
                num_workers=args.parallel,
                verbose=args.verbose
            )
            
            # Generate summary report
            summary_path = args.output / "batch_summary.json"
            generate_batch_summary(results, summary_path)
            
            # Print summary
            successful = sum(1 for r in results if r.get("success", False))
            failed = len(results) - successful
            logger.info("=" * 60)
            logger.info("Batch processing complete!")
            logger.info(f"  Total traces: {len(results)}")
            logger.info(f"  Successful: {successful}")
            logger.info(f"  Failed: {failed}")
            logger.info(f"  Summary: {summary_path}")
            logger.info("=" * 60)
            
            return 0 if failed == 0 else 1
        
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
        engine = EconomicEngine(registry, config.economic, config.trait_emergence)
        
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
