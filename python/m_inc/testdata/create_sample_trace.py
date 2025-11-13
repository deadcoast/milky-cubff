"""Script to create sample BFF trace files for testing M|inc."""

import json
import random
from pathlib import Path


def create_sample_trace(output_path: Path, num_epochs: int = 10, num_tapes: int = 100):
    """Create a sample BFF trace file.
    
    Args:
        output_path: Path to write sample trace
        num_epochs: Number of epochs to generate
        num_tapes: Number of tapes per epoch
    """
    random.seed(42)  # For reproducibility
    
    epochs = []
    for epoch_num in range(num_epochs):
        # Generate random tapes (64 bytes each)
        tapes = {}
        for tape_id in range(num_tapes):
            tape = bytearray(random.randint(0, 255) for _ in range(64))
            tapes[str(tape_id)] = tape.hex()
        
        # Generate random interactions
        interactions = []
        for _ in range(num_tapes // 2):
            a = random.randint(0, num_tapes - 1)
            b = random.randint(0, num_tapes - 1)
            if a != b:
                interactions.append([a, b])
        
        # Generate sample metrics (simulating entropy decrease over time)
        metrics = {
            "entropy": max(3.0, 6.0 - (epoch_num * 0.3)),
            "compression_ratio": 2.5 + (epoch_num * 0.06),
            "copy_score_mean": min(1.0, 0.3 + (epoch_num * 0.07))
        }
        
        epochs.append({
            "epoch": epoch_num,
            "tapes": tapes,
            "interactions": interactions,
            "metrics": metrics
        })
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(epochs, f, indent=2)
    
    print(f"Created sample trace: {output_path}")
    print(f"  Epochs: {num_epochs}")
    print(f"  Tapes per epoch: {num_tapes}")
    print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    # Create small trace for quick testing
    create_sample_trace(
        Path(__file__).parent / "bff_trace_small.json",
        num_epochs=10,
        num_tapes=50
    )
    
    # Create medium trace for validation
    create_sample_trace(
        Path(__file__).parent / "bff_trace_medium.json",
        num_epochs=100,
        num_tapes=100
    )
    
    print("\nSample traces created successfully!")
