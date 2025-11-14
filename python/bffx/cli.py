"""
Command-line interface for BFF soup experiments.

This module provides a CLI for running digital abiogenesis experiments
without writing code. It supports parameter exploration and streams
real-time metrics to stdout.
"""

import argparse
import random
import sys
from typing import Optional

from . import (
    Soup,
    shannon_entropy_bits,
    compress_ratio,
    opcode_histogram,
    top_programs,
    DEFAULT_STEP_LIMIT,
)
from .scheduler import random_disjoint_pairs


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for the CLI.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Run BFF digital abiogenesis experiments",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--pop",
        type=int,
        default=1024,
        help="Population size (must be even)"
    )
    
    parser.add_argument(
        "--epochs",
        type=int,
        default=10000,
        help="Number of epochs to run"
    )
    
    parser.add_argument(
        "--step-limit",
        type=int,
        default=DEFAULT_STEP_LIMIT,
        help="Maximum instructions per VM execution"
    )
    
    parser.add_argument(
        "--mutate",
        type=float,
        default=0.0,
        help="Per-byte mutation probability (0.0 to 1.0)"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (optional)"
    )
    
    parser.add_argument(
        "--report-every",
        type=int,
        default=100,
        help="Reporting interval in epochs"
    )
    
    parser.add_argument(
        "--log-events",
        action="store_true",
        help="Track and report replication events (slower)"
    )
    
    return parser


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv)
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_argument_parser()
    args = parser.parse_args(argv)
    
    # Validate arguments
    if args.pop < 2:
        print(f"Error: Population size must be at least 2, got {args.pop}", file=sys.stderr)
        return 1
    
    if args.pop % 2 != 0:
        print(f"Error: Population size must be even, got {args.pop}", file=sys.stderr)
        return 1
    
    if args.epochs < 1:
        print(f"Error: Epoch count must be at least 1, got {args.epochs}", file=sys.stderr)
        return 1
    
    if args.step_limit < 1:
        print(f"Error: Step limit must be at least 1, got {args.step_limit}", file=sys.stderr)
        return 1
    
    if not (0.0 <= args.mutate <= 1.0):
        print(f"Error: Mutation probability must be between 0.0 and 1.0, got {args.mutate}", file=sys.stderr)
        return 1
    
    if args.report_every < 1:
        print(f"Error: Reporting interval must be at least 1, got {args.report_every}", file=sys.stderr)
        return 1
    
    # Create seeded RNG
    rng = random.Random(args.seed)
    
    # Print configuration
    print(f"# BFF Digital Abiogenesis Experiment")
    print(f"# Population: {args.pop}")
    print(f"# Epochs: {args.epochs}")
    print(f"# Step limit: {args.step_limit}")
    print(f"# Mutation rate: {args.mutate}")
    print(f"# Seed: {args.seed if args.seed is not None else 'unseeded'}")
    print(f"# Report every: {args.report_every} epochs")
    print(f"# Log events: {args.log_events}")
    print()
    
    # Initialize Soup with specified size
    soup = Soup(size=args.pop, rng=rng)
    
    # Run epochs with scheduler
    for epoch in range(1, args.epochs + 1):
        # Execute one epoch
        outcomes = soup.epoch(
            scheduler=random_disjoint_pairs,
            step_limit=args.step_limit,
            mutation_p=args.mutate,
            record_outcomes=args.log_events
        )
        
        # Report metrics at specified intervals
        if epoch % args.report_every == 0:
            # Compute metrics
            entropy = shannon_entropy_bits(soup.pool)
            compression = compress_ratio(soup.pool)
            top_progs = top_programs(soup.pool, k=1)
            top_count = top_progs[0][1] if top_progs else 0
            
            # Output basic metrics
            print(f"epoch {epoch:6d} | top_count {top_count:4d}/{args.pop:4d} | "
                  f"compress_ratio {compression:.3f} | shannon_bits {entropy:.3f}")
            
            # Output opcode histogram
            opcodes = opcode_histogram(soup.pool)
            opcode_str = " ".join(f"{op}:{opcodes.get(op, 0)}" 
                                 for op in ['>', '<', '+', '-', '{', '}', '.', ',', '[', ']'])
            print(f"opcode_counts: {opcode_str}")
            
            # Optionally output replication event counts
            if args.log_events and outcomes:
                replication_counts = {
                    "A_exact": sum(1 for o in outcomes if o.replication_event.kind == "A_exact_replicator"),
                    "B_exact": sum(1 for o in outcomes if o.replication_event.kind == "B_exact_replicator"),
                    "none": sum(1 for o in outcomes if o.replication_event.kind == "none")
                }
                total_replications = replication_counts["A_exact"] + replication_counts["B_exact"]
                print(f"exact_replication_events_this_epoch: {total_replications} "
                      f"(A:{replication_counts['A_exact']} B:{replication_counts['B_exact']})")
            
            # Flush output for real-time monitoring
            sys.stdout.flush()
    
    print()
    print("# Experiment complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
