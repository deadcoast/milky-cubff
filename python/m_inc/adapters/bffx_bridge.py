"""Bridge adapter for BFFx Soup integration with M|inc.

This module provides functionality to convert BFFx Soup simulation data
to M|inc EpochData format, enabling direct integration between BFFx's
pure Python BFF VM and M|inc's economic layer.

Key conversions:
- BFFx Soup.pool (population) → EpochData.tapes
- BFFx PairOutcome[] → EpochData.interactions
- BFFx analytics → EpochData.metrics
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Iterator, Tuple, TYPE_CHECKING

# Add bffx to path if needed
_bffx_path = Path(__file__).parent.parent.parent / "bffx"
if str(_bffx_path.parent) not in sys.path:
    sys.path.insert(0, str(_bffx_path.parent))

from .trace_reader import EpochData

# Conditional import for type checking to avoid circular dependencies
if TYPE_CHECKING:
    from bffx import Soup, PairOutcome


class BFFxBridge:
    """Bridge between BFFx Soup and M|inc EpochData.

    This adapter converts live BFFx simulation data to the EpochData format
    that M|inc's economic engine can process.

    Usage:
        from bffx import Soup
        from bffx.scheduler import random_disjoint_pairs
        from m_inc.adapters.bffx_bridge import BFFxBridge

        # Create and run soup simulation
        soup = Soup(size=100, rng=random.Random(42))
        bridge = BFFxBridge(soup)

        # Run epochs and convert to EpochData
        for _ in range(100):
            outcomes = soup.epoch(random_disjoint_pairs, record_outcomes=True)
            epoch_data = bridge.convert_outcomes_to_epoch(outcomes)
            # Pass epoch_data to M|inc engine
    """

    def __init__(self, soup: Optional["Soup"] = None, compute_metrics: bool = True):
        """Initialize BFFx bridge.

        Args:
            soup: BFFx Soup instance to bridge (can be set later)
            compute_metrics: Whether to compute analytics metrics (entropy, etc.)
        """
        self._soup = soup
        self._compute_metrics = compute_metrics
        self._epoch_count = 0

    @property
    def soup(self) -> Optional["Soup"]:
        """Get the current soup instance."""
        return self._soup

    @soup.setter
    def soup(self, value: "Soup") -> None:
        """Set the soup instance."""
        self._soup = value

    def get_population_as_tapes(self) -> Dict[int, bytearray]:
        """Convert soup population to tapes dictionary.

        Returns:
            Dict mapping tape_id to 64-byte program
        """
        if self._soup is None:
            raise ValueError("Soup not set. Initialize bridge with a Soup instance.")

        tapes = {}
        for i, program in enumerate(self._soup.pool):
            tapes[i] = bytearray(program)
        return tapes

    def get_interactions_from_outcomes(
        self,
        outcomes: List["PairOutcome"]
    ) -> List[Tuple[int, int]]:
        """Extract interaction pairs from PairOutcome list.

        Args:
            outcomes: List of PairOutcome from soup.epoch()

        Returns:
            List of (tape_a_id, tape_b_id) tuples
        """
        interactions = []
        for outcome in outcomes:
            interactions.append((outcome.i, outcome.j))
        return interactions

    def compute_population_metrics(self) -> Dict[str, float]:
        """Compute analytics metrics from current population.

        Uses BFFx analytics functions to compute:
        - entropy: Shannon entropy in bits
        - compression_ratio: Lempel-Ziv compression ratio
        - unique_programs: Number of unique programs
        - mean_opcode_density: Average density of opcodes

        Returns:
            Dict of metric name to value
        """
        if self._soup is None:
            return {}

        if not self._compute_metrics:
            return {}

        try:
            from bffx import shannon_entropy_bits, compress_ratio

            # Pass population directly to analytics functions (they expect List[bytearray])
            population = self._soup.pool

            # Compute entropy (expects list of programs)
            entropy = shannon_entropy_bits(population)

            # Compute compression ratio (expects list of programs)
            compression = compress_ratio(population)

            # Count unique programs
            unique = len(set(bytes(p) for p in population))

            # Compute opcode density (fraction of bytes that are valid opcodes)
            all_bytes = b''.join(bytes(p) for p in population)
            opcode_chars = set(b'[]+-.,<>{}')
            opcode_count = sum(1 for b in all_bytes if b in opcode_chars)
            opcode_density = opcode_count / len(all_bytes) if all_bytes else 0.0

            return {
                "entropy": entropy,
                "compression_ratio": compression,
                "unique_programs": float(unique),
                "opcode_density": opcode_density,
                "population_size": float(len(self._soup.pool))
            }

        except ImportError:
            # BFFx analytics not available
            return {}

    def compute_outcome_metrics(
        self,
        outcomes: List["PairOutcome"]
    ) -> Dict[str, float]:
        """Compute metrics from epoch outcomes.

        Args:
            outcomes: List of PairOutcome from soup.epoch()

        Returns:
            Dict of outcome-related metrics
        """
        if not outcomes:
            return {}

        # Count replication events
        exact_replications = 0
        partial_replications = 0
        total_steps = 0

        for outcome in outcomes:
            total_steps += outcome.result.steps
            if outcome.replication_event:
                # Check if it's an exact replication based on kind
                if outcome.replication_event.kind in ("A_exact_replicator", "B_exact_replicator"):
                    exact_replications += 1
                elif outcome.replication_event.kind != "none":
                    partial_replications += 1

        return {
            "exact_replications": float(exact_replications),
            "partial_replications": float(partial_replications),
            "total_steps": float(total_steps),
            "mean_steps": total_steps / len(outcomes) if outcomes else 0.0
        }

    def convert_outcomes_to_epoch(
        self,
        outcomes: List["PairOutcome"],
        include_population_metrics: bool = True
    ) -> EpochData:
        """Convert BFFx epoch outcomes to M|inc EpochData.

        This is the main conversion function that creates an EpochData
        object from BFFx simulation results.

        Args:
            outcomes: List of PairOutcome from soup.epoch()
            include_population_metrics: Whether to compute population-level metrics

        Returns:
            EpochData ready for M|inc processing
        """
        if self._soup is None:
            raise ValueError("Soup not set. Initialize bridge with a Soup instance.")

        # Get current population as tapes
        tapes = self.get_population_as_tapes()

        # Extract interactions
        interactions = self.get_interactions_from_outcomes(outcomes)

        # Compute metrics
        metrics = {}
        if include_population_metrics:
            metrics.update(self.compute_population_metrics())
        metrics.update(self.compute_outcome_metrics(outcomes))
        metrics["epoch_num"] = float(self._soup.epoch_index)

        epoch_data = EpochData(
            epoch_num=self._soup.epoch_index,
            tapes=tapes,
            interactions=interactions,
            metrics=metrics
        )

        self._epoch_count += 1
        return epoch_data

    def snapshot_to_epoch(self) -> EpochData:
        """Create EpochData from current soup state without outcomes.

        Useful for capturing initial state or intermediate snapshots
        without running an epoch.

        Returns:
            EpochData with current population and metrics (no interactions)
        """
        if self._soup is None:
            raise ValueError("Soup not set. Initialize bridge with a Soup instance.")

        tapes = self.get_population_as_tapes()
        metrics = self.compute_population_metrics()
        metrics["epoch_num"] = float(self._soup.epoch_index)

        return EpochData(
            epoch_num=self._soup.epoch_index,
            tapes=tapes,
            interactions=[],
            metrics=metrics
        )


def stream_bffx_to_minc(
    soup: "Soup",
    scheduler,
    num_epochs: int,
    step_limit: int = 8192,
    mutation_p: float = 0.0,
    compute_metrics: bool = True
) -> Iterator[EpochData]:
    """Stream BFFx simulation epochs as EpochData for M|inc.

    This is the main integration function that runs a BFFx simulation
    and yields EpochData objects for M|inc processing.

    Args:
        soup: BFFx Soup instance
        scheduler: Pairing scheduler function
        num_epochs: Number of epochs to run
        step_limit: Max steps per VM execution
        mutation_p: Per-byte mutation probability
        compute_metrics: Whether to compute analytics metrics

    Yields:
        EpochData for each epoch

    Example:
        from bffx import Soup
        from bffx.scheduler import random_disjoint_pairs
        from m_inc.adapters.bffx_bridge import stream_bffx_to_minc
        from m_inc.core.economic_engine import EconomicEngine

        soup = Soup(size=100, rng=random.Random(42))

        for epoch_data in stream_bffx_to_minc(soup, random_disjoint_pairs, 100):
            # Process with M|inc
            result = engine.process_tick(epoch_data.epoch_num)
            print(f"Tick {result.tick_num}: wealth={result.metrics.wealth_total}")
    """
    bridge = BFFxBridge(soup, compute_metrics=compute_metrics)

    # Yield initial snapshot
    yield bridge.snapshot_to_epoch()

    # Run epochs
    for _ in range(num_epochs):
        outcomes = soup.epoch(
            scheduler=scheduler,
            step_limit=step_limit,
            mutation_p=mutation_p,
            record_outcomes=True
        )
        yield bridge.convert_outcomes_to_epoch(outcomes)


def create_bffx_to_minc_runner(
    population_size: int = 100,
    seed: Optional[int] = None,
    step_limit: int = 8192,
    mutation_p: float = 0.0
):
    """Create a configured BFFx→M|inc runner.

    Returns a callable that runs BFFx simulation and yields EpochData.

    Args:
        population_size: Number of programs in soup
        seed: Random seed for reproducibility
        step_limit: Max steps per VM execution
        mutation_p: Per-byte mutation probability

    Returns:
        Callable that takes num_epochs and yields EpochData
    """
    import random
    from bffx import Soup
    from bffx.scheduler import random_disjoint_pairs

    rng = random.Random(seed) if seed is not None else random.Random()
    soup = Soup(size=population_size, rng=rng)

    def runner(num_epochs: int) -> Iterator[EpochData]:
        return stream_bffx_to_minc(
            soup=soup,
            scheduler=random_disjoint_pairs,
            num_epochs=num_epochs,
            step_limit=step_limit,
            mutation_p=mutation_p
        )

    return runner
