"""
Reproducibility test for BFF VM Foundation.

This test verifies that the BFF VM and soup evolution are fully deterministic.
Running the same experiment with the same seed should produce byte-for-byte
identical results at every epoch.

Requirements tested: 9.3
"""

import random
from .soup import Soup
from .scheduler import random_disjoint_pairs
from .analytics import shannon_entropy_bits, compress_ratio, top_programs


def test_reproducibility():
    """
    Run same experiment with same seed twice.
    
    Verifies:
    - Populations are byte-for-byte identical at each epoch
    - Metrics (entropy, compression ratio) are identical
    - Top programs are identical
    """
    # Configuration
    population_size = 64
    num_epochs = 100  # Shorter run for faster testing
    step_limit = 8192
    mutation_rate = 0.0001
    seed = 12345  # Fixed seed for reproducibility
    
    # Run 1: First execution
    rng1 = random.Random(seed)
    soup1 = Soup(size=population_size, rng=rng1)
    
    # Track metrics for run 1
    metrics1 = []
    populations1 = []
    
    # Capture initial state
    populations1.append([bytearray(prog) for prog in soup1.pool])
    metrics1.append({
        'entropy': shannon_entropy_bits(soup1.pool),
        'compress': compress_ratio(soup1.pool),
        'top_programs': top_programs(soup1.pool, k=3)
    })
    
    # Run evolution for run 1
    for epoch in range(num_epochs):
        soup1.epoch(
            scheduler=random_disjoint_pairs,
            step_limit=step_limit,
            mutation_p=mutation_rate,
            record_outcomes=False
        )
        
        # Capture state after each epoch
        populations1.append([bytearray(prog) for prog in soup1.pool])
        metrics1.append({
            'entropy': shannon_entropy_bits(soup1.pool),
            'compress': compress_ratio(soup1.pool),
            'top_programs': top_programs(soup1.pool, k=3)
        })
    
    # Run 2: Second execution with same seed
    rng2 = random.Random(seed)
    soup2 = Soup(size=population_size, rng=rng2)
    
    # Track metrics for run 2
    metrics2 = []
    populations2 = []
    
    # Capture initial state
    populations2.append([bytearray(prog) for prog in soup2.pool])
    metrics2.append({
        'entropy': shannon_entropy_bits(soup2.pool),
        'compress': compress_ratio(soup2.pool),
        'top_programs': top_programs(soup2.pool, k=3)
    })
    
    # Run evolution for run 2
    for epoch in range(num_epochs):
        soup2.epoch(
            scheduler=random_disjoint_pairs,
            step_limit=step_limit,
            mutation_p=mutation_rate,
            record_outcomes=False
        )
        
        # Capture state after each epoch
        populations2.append([bytearray(prog) for prog in soup2.pool])
        metrics2.append({
            'entropy': shannon_entropy_bits(soup2.pool),
            'compress': compress_ratio(soup2.pool),
            'top_programs': top_programs(soup2.pool, k=3)
        })
    
    # Verification 1: Populations are byte-for-byte identical at each epoch
    print(f"\n=== Reproducibility Test Results ===")
    print(f"Population: {population_size} programs")
    print(f"Epochs: {num_epochs}")
    print(f"Seed: {seed}")
    print(f"\nVerifying byte-for-byte identity at each epoch...")
    
    for epoch_idx in range(len(populations1)):
        pop1 = populations1[epoch_idx]
        pop2 = populations2[epoch_idx]
        
        assert len(pop1) == len(pop2), \
            f"Population sizes differ at epoch {epoch_idx}: {len(pop1)} vs {len(pop2)}"
        
        for prog_idx in range(len(pop1)):
            prog1 = pop1[prog_idx]
            prog2 = pop2[prog_idx]
            
            assert prog1 == prog2, \
                f"Program {prog_idx} differs at epoch {epoch_idx}:\n" \
                f"  Run 1: {prog1.hex()}\n" \
                f"  Run 2: {prog2.hex()}"
    
    print(f"✓ All {len(populations1)} population snapshots are byte-for-byte identical")
    
    # Verification 2: Metrics are identical
    print(f"\nVerifying metrics identity at each epoch...")
    
    for epoch_idx in range(len(metrics1)):
        m1 = metrics1[epoch_idx]
        m2 = metrics2[epoch_idx]
        
        # Check entropy (should be exactly equal for deterministic computation)
        assert m1['entropy'] == m2['entropy'], \
            f"Entropy differs at epoch {epoch_idx}: {m1['entropy']} vs {m2['entropy']}"
        
        # Check compression ratio (should be exactly equal)
        assert m1['compress'] == m2['compress'], \
            f"Compression ratio differs at epoch {epoch_idx}: {m1['compress']} vs {m2['compress']}"
        
        # Check top programs (should be identical)
        top1 = m1['top_programs']
        top2 = m2['top_programs']
        
        assert len(top1) == len(top2), \
            f"Top programs list length differs at epoch {epoch_idx}: {len(top1)} vs {len(top2)}"
        
        for i in range(len(top1)):
            prog1, count1 = top1[i]
            prog2, count2 = top2[i]
            
            assert prog1 == prog2, \
                f"Top program {i} differs at epoch {epoch_idx}:\n" \
                f"  Run 1: {prog1.hex()}\n" \
                f"  Run 2: {prog2.hex()}"
            
            assert count1 == count2, \
                f"Top program {i} count differs at epoch {epoch_idx}: {count1} vs {count2}"
    
    print(f"✓ All {len(metrics1)} metric snapshots are identical")
    
    # Print sample metrics to show evolution
    print(f"\n=== Sample Evolution Metrics ===")
    sample_epochs = [0, num_epochs // 4, num_epochs // 2, 3 * num_epochs // 4, num_epochs]
    
    for epoch_idx in sample_epochs:
        m = metrics1[epoch_idx]
        print(f"\nEpoch {epoch_idx}:")
        print(f"  Entropy: {m['entropy']:.6f} bits")
        print(f"  Compression ratio: {m['compress']:.6f}")
        print(f"  Top program count: {m['top_programs'][0][1] if m['top_programs'] else 0}/{population_size}")
    
    print(f"\n✓ Reproducibility verified: Same seed produces identical results")
    print(f"  - {len(populations1)} population snapshots are byte-for-byte identical")
    print(f"  - {len(metrics1)} metric snapshots are identical")
    print(f"  - Deterministic execution confirmed")


if __name__ == "__main__":
    test_reproducibility()
    print("\n✓ Reproducibility test passed!")
