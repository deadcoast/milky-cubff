#!/usr/bin/env python3
"""
Generate example BFF trace files for M|inc testing.

This script creates synthetic BFF trace data with the correct format
for testing M|inc integration without requiring actual BFF simulation runs.
"""

import json
import random
from pathlib import Path


def generate_tape_hex(seed: int) -> str:
    """Generate a 128-character hex string representing a 64-byte tape."""
    random.seed(seed)
    return ''.join(random.choice('0123456789abcdef') for _ in range(128))


def generate_epoch(epoch_num: int, num_tapes: int = 20, num_interactions: int = 10):
    """Generate a single epoch of BFF trace data."""
    # Generate tapes
    tapes = {
        str(i): generate_tape_hex(epoch_num * 1000 + i)
        for i in range(num_tapes)
    }
    
    # Generate random interactions (pairs of tape IDs)
    interactions = []
    tape_ids = list(range(num_tapes))
    random.seed(epoch_num * 2000)
    for _ in range(num_interactions):
        pair = random.sample(tape_ids, 2)
        interactions.append(pair)
    
    # Generate metrics with slight variation
    base_entropy = 6.0
    base_compression = 2.5
    base_copy_score = 0.5
    
    metrics = {
        "entropy": round(base_entropy - epoch_num * 0.02, 2),
        "compression_ratio": round(base_compression + epoch_num * 0.02, 2),
        "copy_score_mean": round(base_copy_score + epoch_num * 0.01, 2)
    }
    
    return {
        "epoch": epoch_num,
        "tapes": tapes,
        "interactions": interactions,
        "metrics": metrics
    }


def generate_trace(num_epochs: int, output_file: Path):
    """Generate a complete BFF trace file."""
    trace = [generate_epoch(i) for i in range(num_epochs)]
    
    with open(output_file, 'w') as f:
        json.dump(trace, f, indent=2)
    
    print(f"Generated {num_epochs}-epoch trace: {output_file}")


if __name__ == "__main__":
    # Generate 10-tick trace for quick testing
    generate_trace(10, Path(__file__).parent / "trace_10tick.json")
    
    # Generate 100-tick trace for validation
    generate_trace(100, Path(__file__).parent / "trace_100tick.json")
