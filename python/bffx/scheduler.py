"""
Scheduler module for BFF soup experiments.

Provides pairing algorithms that determine which programs interact each epoch.
The default scheduler uses random disjoint pairing where every program
interacts exactly once per epoch.
"""

import random
from typing import List, Tuple, Callable


# Type alias for scheduler functions
PairScheduler = Callable[[int, random.Random], List[Tuple[int, int]]]


def random_disjoint_pairs(n: int, rng: random.Random) -> List[Tuple[int, int]]:
    """
    Generate random disjoint pairs for program interactions.
    
    This is the canonical pairing strategy for BFF soup experiments where
    every program interacts exactly once per epoch. The population is
    shuffled and then paired sequentially: (0,1), (2,3), (4,5), etc.
    
    Args:
        n: Population size (must be even)
        rng: Seeded random number generator for reproducibility
        
    Returns:
        List of (i, j) tuples representing program index pairs
        
    Raises:
        ValueError: If n is odd or less than 2
        
    Example:
        >>> rng = random.Random(42)
        >>> pairs = random_disjoint_pairs(6, rng)
        >>> len(pairs)
        3
        >>> # Each program appears exactly once
        >>> all_indices = set()
        >>> for i, j in pairs:
        ...     all_indices.add(i)
        ...     all_indices.add(j)
        >>> len(all_indices)
        6
    """
    if n < 2:
        raise ValueError(f"Population size must be at least 2, got {n}")
    
    if n % 2 != 0:
        raise ValueError(f"Population size must be even, got {n}")
    
    # Create shuffled indices
    indices = list(range(n))
    rng.shuffle(indices)
    
    # Create disjoint pairs by pairing consecutive elements
    pairs = []
    for i in range(0, n, 2):
        pairs.append((indices[i], indices[i + 1]))
    
    return pairs
