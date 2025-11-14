"""
Soup management for BFF population evolution.

This module implements the canonical workflow for digital abiogenesis:
random pairing → concatenation → execution → splitting → population update.
Repeated for millions of epochs until self-replicating programs emerge.
"""

import random
from dataclasses import dataclass
from typing import List, Optional

from .vm import BFFVM, RunResult
from .scheduler import PairScheduler
from .detectors import detect_exact_replication, ReplicationEvent


@dataclass
class PairOutcome:
    """Records the outcome of a single program pair interaction.
    
    Attributes:
        i: Index of first program in population
        j: Index of second program in population
        order: Concatenation order ("AB" or "BA")
        result: VM execution result
        replication_event: Replication detection result
    """
    i: int
    j: int
    order: str
    result: RunResult
    replication_event: ReplicationEvent


class Soup:
    """Manages a population of BFF programs and their evolution.
    
    The Soup class implements the primordial soup workflow where programs
    interact through random pairing, potentially evolving into self-replicators
    through millions of epochs.
    """
    
    def __init__(self, size: int, rng: Optional[random.Random] = None):
        """Initialize a soup with random programs.
        
        Args:
            size: Population size (must be even and >= 2)
            rng: Optional seeded random number generator for reproducibility.
                 If None, creates a new unseeded RNG.
        
        Raises:
            ValueError: If size is odd or less than 2
        """
        if size < 2:
            raise ValueError(f"Population size must be at least 2, got {size}")
        
        if size % 2 != 0:
            raise ValueError(f"Population size must be even, got {size}")
        
        self.rng = rng if rng is not None else random.Random()
        self.epoch_index = 0
        
        # Generate random initial programs (64 bytes each)
        self.pool: List[bytearray] = []
        for _ in range(size):
            program = bytearray(self.rng.getrandbits(8) for _ in range(64))
            self.pool.append(program)

    def epoch(
        self,
        scheduler: PairScheduler,
        step_limit: int = 8192,
        mutation_p: float = 0.0,
        record_outcomes: bool = False
    ) -> List[PairOutcome]:
        """Execute one epoch of the soup evolution.
        
        The canonical workflow:
        1. Scheduler generates disjoint pairs
        2. For each pair (A, B):
           - Randomly choose AB or BA concatenation order
           - Concatenate into 128-byte tape
           - Execute with BFF VM
           - Split at byte 64 back into A', B'
           - Optionally apply mutation
           - Replace A→A', B→B' in population
        3. Increment epoch counter
        4. Optionally record outcomes with replication events
        
        Args:
            scheduler: Function that generates program pairs
            step_limit: Maximum instructions per VM execution
            mutation_p: Per-byte mutation probability (0.0 = no mutation)
            record_outcomes: If True, record detailed outcomes for analysis
        
        Returns:
            List of PairOutcome if record_outcomes=True, empty list otherwise
        """
        n = len(self.pool)
        pairs = scheduler(n, self.rng)
        
        # Pre-allocate next generation array
        next_gen = [bytearray(64) for _ in range(n)]
        
        # Track outcomes if requested
        outcomes = [] if record_outcomes else []
        
        for i, j in pairs:
            # Get programs A and B
            A_before = bytes(self.pool[i])
            B_before = bytes(self.pool[j])
            
            # Randomly choose AB or BA order
            if self.rng.random() < 0.5:
                order = "AB"
                tape = bytearray(A_before + B_before)
            else:
                order = "BA"
                tape = bytearray(B_before + A_before)
            
            # Execute VM
            vm = BFFVM(tape, step_limit=step_limit)
            result = vm.run()
            
            # Split tape back into two programs
            if order == "AB":
                A_after = bytes(result.tape[0:64])
                B_after = bytes(result.tape[64:128])
            else:
                # BA order: first 64 bytes go to B, second 64 bytes go to A
                B_after = bytes(result.tape[0:64])
                A_after = bytes(result.tape[64:128])
            
            # Apply mutation if enabled
            if mutation_p > 0.0:
                A_after = self._mutate_program(A_after, mutation_p)
                B_after = self._mutate_program(B_after, mutation_p)
            
            # Replace programs in next generation
            next_gen[i] = bytearray(A_after)
            next_gen[j] = bytearray(B_after)
            
            # Record outcome if requested
            if record_outcomes:
                replication_event = detect_exact_replication(
                    A_before, B_before, A_after, B_after
                )
                outcomes.append(PairOutcome(
                    i=i,
                    j=j,
                    order=order,
                    result=result,
                    replication_event=replication_event
                ))
        
        # Replace population with next generation
        self.pool = next_gen
        
        # Increment epoch counter
        self.epoch_index += 1
        
        return outcomes
    
    def _mutate_program(self, program: bytes, per_byte_p: float) -> bytes:
        """Apply per-byte mutation to a program.
        
        Args:
            program: 64-byte program
            per_byte_p: Probability of mutation per byte
        
        Returns:
            Mutated program (may be unchanged if no mutations occurred)
        """
        mutated = bytearray(program)
        for i in range(len(mutated)):
            if self.rng.random() < per_byte_p:
                mutated[i] = self.rng.getrandbits(8)
        return bytes(mutated)
    
    def inject_mutation(self, per_byte_p: float) -> None:
        """Apply mutation to all programs in the population.
        
        This method allows injecting genetic diversity into the population
        at any point during evolution.
        
        Args:
            per_byte_p: Probability of mutation per byte
        """
        for i in range(len(self.pool)):
            for j in range(len(self.pool[i])):
                if self.rng.random() < per_byte_p:
                    self.pool[i][j] = self.rng.getrandbits(8)
