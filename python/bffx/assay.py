"""Replicator assay protocol for testing candidate self-replicating programs.

This module provides systematic testing of candidate replicators against
random food programs to verify replication capability.
"""

import random
from typing import List, Tuple, Optional

from .vm import BFFVM
from .detectors import detect_exact_replication


def assay_candidate(
    candidate: bytes,
    foods: List[bytes],
    trials: int = 100,
    step_limit: int = 8192,
    rng: Optional[random.Random] = None
) -> Tuple[int, int]:
    """Test a candidate replicator against random food programs.
    
    This function implements a rigorous assay protocol:
    1. For each trial, pick a random food program
    2. Test BOTH AB and BA orientations (candidate+food and food+candidate)
    3. Count success only if BOTH orientations show exact replication
    4. Return (successes, total_trials)
    
    The requirement for both orientations to succeed ensures the candidate
    is a robust replicator, not just lucky in one orientation.
    
    Args:
        candidate: The program to test (must be exactly 64 bytes)
        foods: List of food programs to test against (must not be empty)
        trials: Number of trials to run (default: 100)
        step_limit: Maximum instructions per VM execution (default: 8192)
        rng: Random number generator for reproducibility (default: new unseeded RNG)
    
    Returns:
        Tuple of (successes, total_trials) where success means BOTH
        AB and BA orientations produced exact replication.
    
    Raises:
        ValueError: If candidate is not exactly 64 bytes
        ValueError: If foods list is empty
        ValueError: If any food program is not exactly 64 bytes
    
    Examples:
        >>> # Test a known replicator
        >>> replicator = bytes([...])  # 64-byte replicator
        >>> foods = [bytes(random.getrandbits(8) for _ in range(64)) for _ in range(100)]
        >>> successes, total = assay_candidate(replicator, foods, trials=50)
        >>> print(f"Success rate: {successes}/{total}")
    """
    # Validate candidate is exactly 64 bytes
    if len(candidate) != 64:
        raise ValueError(f"Candidate must be exactly 64 bytes, got {len(candidate)}")
    
    # Validate foods list is not empty
    if not foods:
        raise ValueError("Foods list must not be empty")
    
    # Validate all food programs are exactly 64 bytes
    for i, food in enumerate(foods):
        if len(food) != 64:
            raise ValueError(f"Food program at index {i} must be exactly 64 bytes, got {len(food)}")
    
    # Create RNG if not provided
    if rng is None:
        rng = random.Random()
    
    successes = 0
    
    for _ in range(trials):
        # Pick a random food program
        food = rng.choice(foods)
        
        # Test AB orientation: candidate + food
        tape_ab = bytearray(candidate + food)
        vm_ab = BFFVM(tape_ab, step_limit=step_limit)
        result_ab = vm_ab.run()
        
        # Split the result back into two programs
        A_after_ab = bytes(result_ab.tape[:64])
        B_after_ab = bytes(result_ab.tape[64:])
        
        # Detect replication in AB orientation
        event_ab = detect_exact_replication(
            A_before=candidate,
            B_before=food,
            A_after=A_after_ab,
            B_after=B_after_ab
        )
        
        # Test BA orientation: food + candidate
        tape_ba = bytearray(food + candidate)
        vm_ba = BFFVM(tape_ba, step_limit=step_limit)
        result_ba = vm_ba.run()
        
        # Split the result back into two programs
        A_after_ba = bytes(result_ba.tape[:64])
        B_after_ba = bytes(result_ba.tape[64:])
        
        # Detect replication in BA orientation
        event_ba = detect_exact_replication(
            A_before=food,
            B_before=candidate,
            A_after=A_after_ba,
            B_after=B_after_ba
        )
        
        # Count success only if BOTH orientations show exact replication
        # In AB: candidate is A, so we look for A_exact_replicator
        # In BA: candidate is B, so we look for B_exact_replicator
        ab_success = (event_ab.kind == "A_exact_replicator")
        ba_success = (event_ba.kind == "B_exact_replicator")
        
        if ab_success and ba_success:
            successes += 1
    
    return (successes, trials)
