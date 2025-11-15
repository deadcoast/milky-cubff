"""Cache layer for M|inc economic outcomes."""

import hashlib
import json
import logging
import random
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .models import Agent
from .config import CacheConfig

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CanonicalState:
    """Canonical representation of agent states for caching.
    
    Agents are sorted by ID for deterministic ordering.
    Only relevant fields (role, currency, wealth) are included.
    """
    agents: List[Dict[str, Any]]
    config_hash: str
    
    def compute_hash(self) -> str:
        """Compute hash of the canonical state.
        
        Returns:
            16-character hex hash
        """
        state_str = json.dumps({
            "agents": self.agents,
            "config_hash": self.config_hash
        }, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]


def compute_canonical_state(agents: List[Agent], config_hash: str) -> CanonicalState:
    """Compute canonical state representation from agents.
    
    Args:
        agents: List of agents
        config_hash: Hash of the configuration
        
    Returns:
        CanonicalState with sorted agents and config hash
    """
    # Sort agents by ID for deterministic ordering
    sorted_agents = sorted(agents, key=lambda a: a.id)
    
    # Extract relevant fields only
    agent_dicts = []
    for agent in sorted_agents:
        agent_dicts.append({
            "id": agent.id,
            "role": agent.role.value,
            "currency": agent.currency,
            "wealth": {
                "compute": agent.wealth.compute,
                "copy": agent.wealth.copy,
                "defend": agent.wealth.defend,
                "raid": agent.wealth.raid,
                "trade": agent.wealth.trade,
                "sense": agent.wealth.sense,
                "adapt": agent.wealth.adapt,
            }
        })
    
    return CanonicalState(
        agents=agent_dicts,
        config_hash=config_hash
    )


@dataclass
class CacheStats:
    """Statistics for cache performance."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    witness_validations: int = 0
    witness_failures: int = 0
    
    def hit_rate(self) -> float:
        """Compute cache hit rate.
        
        Returns:
            Hit rate as a fraction (0.0 to 1.0)
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(self.hit_rate(), 3),
            "witness_validations": self.witness_validations,
            "witness_failures": self.witness_failures,
        }


@dataclass
class WitnessSample:
    """A witness sample for cache validation.
    
    Stores input state and output for validation.
    """
    state_hash: str
    input_state: CanonicalState
    output: Any
    
    def validate(self, compute_fn: Callable[[CanonicalState], Any]) -> bool:
        """Validate cached output against recomputation.
        
        Args:
            compute_fn: Function to recompute output
            
        Returns:
            True if cached output matches recomputed output
        """
        try:
            recomputed = compute_fn(self.input_state)
            return self.output == recomputed
        except Exception as e:
            logger.error(f"Witness validation failed with exception: {e}")
            return False


class CacheLayer:
    """Cache layer for memoizing deterministic economic outcomes.
    
    Uses LRU eviction policy with configurable max size.
    Stores witness samples for validation.
    """
    
    def __init__(self, config: CacheConfig):
        """Initialize cache layer.
        
        Args:
            config: Cache configuration
        """
        self.config = config
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.witnesses: List[WitnessSample] = []
        self.stats = CacheStats()
        self.enabled = config.enabled
    
    def get_or_compute(
        self,
        state: CanonicalState,
        compute_fn: Callable[[CanonicalState], T]
    ) -> T:
        """Get cached result or compute and cache it.
        
        Args:
            state: Canonical state to use as cache key
            compute_fn: Function to compute result if not cached
            
        Returns:
            Cached or computed result
        """
        if not self.enabled:
            return compute_fn(state)
        
        # Compute cache key
        cache_key = state.compute_hash()
        
        # Check cache
        if cache_key in self.cache:
            # Cache hit - move to end (LRU)
            self.cache.move_to_end(cache_key)
            self.stats.hits += 1
            return self.cache[cache_key]
        
        # Cache miss - compute result
        self.stats.misses += 1
        result = compute_fn(state)
        
        # Store in cache
        self.cache[cache_key] = result
        
        # Evict oldest if over max size
        if len(self.cache) > self.config.max_size:
            self.cache.popitem(last=False)
            self.stats.evictions += 1
        
        # Store witness sample
        if random.random() < self.config.witness_sample_rate:
            self.witnesses.append(WitnessSample(
                state_hash=cache_key,
                input_state=state,
                output=result
            ))
        
        return result
    
    def invalidate(self, reason: str = "manual") -> None:
        """Clear cache and reset statistics.
        
        Args:
            reason: Reason for invalidation (for logging)
        """
        cache_size = len(self.cache)
        self.cache.clear()
        self.witnesses.clear()
        logger.info(f"Cache invalidated ({reason}): cleared {cache_size} entries")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics.
        
        Returns:
            CacheStats with current metrics
        """
        return self.stats
    
    def validate_witnesses(
        self,
        compute_fn: Callable[[CanonicalState], Any]
    ) -> int:
        """Validate witness samples against recomputation.
        
        Args:
            compute_fn: Function to recompute outputs
            
        Returns:
            Number of validation failures
        """
        failures = 0
        
        for witness in self.witnesses:
            self.stats.witness_validations += 1
            
            if not witness.validate(compute_fn):
                failures += 1
                self.stats.witness_failures += 1
                logger.warning(
                    f"Witness validation failed for state {witness.state_hash}"
                )
        
        if failures > 0:
            logger.error(
                f"Cache validation failed: {failures}/{len(self.witnesses)} witnesses"
            )
        
        return failures
    
    def __len__(self) -> int:
        """Return number of cached entries."""
        return len(self.cache)
