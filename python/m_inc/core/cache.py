"""Cache layer for memoizing deterministic economic outcomes."""

import hashlib
import json
import logging
import random
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .config import CacheConfig
from .models import Agent

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CanonicalState:
    """Normalized representation of agent states for caching.
    
    Canonical states are deterministic representations that can be hashed
    for cache key generation. Agents are sorted by ID to ensure consistency.
    """
    agents: List[Dict[str, Any]]
    config_hash: str
    
    def hash(self) -> str:
        """Compute hash of canonical state.
        
        Returns:
            16-character hex hash string
        """
        state_str = json.dumps({
            "agents": self.agents,
            "config_hash": self.config_hash
        }, sort_keys=True)
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]
    
    @classmethod
    def from_agents(cls, agents: List[Agent], config_hash: str) -> "CanonicalState":
        """Create canonical state from list of agents.
        
        Args:
            agents: List of agents to canonicalize
            config_hash: Hash of current configuration
            
        Returns:
            CanonicalState instance
        """
        # Sort agents by ID for deterministic ordering
        sorted_agents = sorted(agents, key=lambda a: a.id)
        
        # Extract relevant fields (role, currency, wealth)
        agent_dicts = []
        for agent in sorted_agents:
            agent_dicts.append({
                "id": agent.id,
                "role": agent.role.value,
                "currency": agent.currency,
                "wealth": agent.wealth.to_dict()
            })
        
        return cls(agents=agent_dicts, config_hash=config_hash)


@dataclass
class WitnessSample:
    """Sample of input/output pair for cache validation.
    
    Witness samples are stored to validate that cached outcomes
    remain correct over time.
    """
    state_hash: str
    input_state: CanonicalState
    output: Any
    timestamp: float
    
    def validate(self, compute_fn: Callable) -> bool:
        """Validate that recomputation produces same output.
        
        Args:
            compute_fn: Function to recompute output
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            recomputed = compute_fn()
            return recomputed == self.output
        except Exception as e:
            logger.error(f"Witness validation failed with exception: {e}")
            return False


@dataclass
class CacheStats:
    """Statistics about cache performance."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    witness_validations: int = 0
    witness_failures: int = 0
    
    def hit_rate(self) -> float:
        """Calculate cache hit rate.
        
        Returns:
            Hit rate as fraction (0.0 to 1.0)
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "invalidations": self.invalidations,
            "hit_rate": round(self.hit_rate(), 3),
            "witness_validations": self.witness_validations,
            "witness_failures": self.witness_failures
        }


class CacheLayer:
    """Cache layer for memoizing deterministic economic outcomes.
    
    Uses LRU eviction policy and stores witness samples for validation.
    Cache keys are computed from canonical state + config hash.
    """
    
    def __init__(self, config: CacheConfig):
        """Initialize cache layer.
        
        Args:
            config: Cache configuration
        """
        self.config = config
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.witnesses: Dict[str, WitnessSample] = {}
        self.stats = CacheStats()
        self.rng = random.Random()
    
    def get_or_compute(
        self,
        state: CanonicalState,
        compute_fn: Callable[[], T]
    ) -> T:
        """Get cached result or compute and cache it.
        
        Args:
            state: Canonical state for cache key
            compute_fn: Function to compute result if not cached
            
        Returns:
            Cached or computed result
        """
        if not self.config.enabled:
            return compute_fn()
        
        # Compute cache key
        cache_key = state.hash()
        
        # Check cache
        if cache_key in self.cache:
            self.stats.hits += 1
            # Move to end (LRU)
            self.cache.move_to_end(cache_key)
            return self.cache[cache_key]
        
        # Cache miss - compute result
        self.stats.misses += 1
        result = compute_fn()
        
        # Store in cache
        self._store(cache_key, result, state)
        
        return result
    
    def _store(self, cache_key: str, result: Any, state: CanonicalState) -> None:
        """Store result in cache with LRU eviction.
        
        Args:
            cache_key: Cache key
            result: Result to cache
            state: Canonical state for witness sampling
        """
        # Check if we need to evict
        if len(self.cache) >= self.config.max_size:
            # Evict oldest entry (LRU)
            evicted_key, _ = self.cache.popitem(last=False)
            self.stats.evictions += 1
            
            # Remove witness if exists
            if evicted_key in self.witnesses:
                del self.witnesses[evicted_key]
        
        # Store result
        self.cache[cache_key] = result
        
        # Store witness sample with configured probability
        if self.rng.random() < self.config.witness_sample_rate:
            import time
            self.witnesses[cache_key] = WitnessSample(
                state_hash=cache_key,
                input_state=state,
                output=result,
                timestamp=time.time()
            )
    
    def invalidate(self, reason: str = "") -> None:
        """Clear all cached entries.
        
        Args:
            reason: Reason for invalidation (for logging)
        """
        num_entries = len(self.cache)
        self.cache.clear()
        self.witnesses.clear()
        self.stats.invalidations += 1
        
        if reason:
            logger.info(f"Cache invalidated ({num_entries} entries): {reason}")
        else:
            logger.info(f"Cache invalidated ({num_entries} entries)")
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics.
        
        Returns:
            CacheStats instance
        """
        return self.stats
    
    def validate_witnesses(self) -> List[str]:
        """Validate all witness samples.
        
        Returns:
            List of cache keys that failed validation
        """
        failures = []
        
        for cache_key, witness in self.witnesses.items():
            self.stats.witness_validations += 1
            
            # Check if cached value still exists
            if cache_key not in self.cache:
                continue
            
            # Validate cached value matches witness
            cached_value = self.cache[cache_key]
            if cached_value != witness.output:
                self.stats.witness_failures += 1
                failures.append(cache_key)
                logger.warning(f"Witness validation failed for cache key: {cache_key}")
        
        return failures
    
    def get_size(self) -> int:
        """Get current cache size.
        
        Returns:
            Number of cached entries
        """
        return len(self.cache)
    
    def get_witness_count(self) -> int:
        """Get number of witness samples.
        
        Returns:
            Number of witness samples
        """
        return len(self.witnesses)


def compute_canonical_state(agents: List[Agent], config_hash: str) -> CanonicalState:
    """Compute canonical state from list of agents.
    
    This is a convenience function that wraps CanonicalState.from_agents.
    
    Args:
        agents: List of agents
        config_hash: Hash of current configuration
        
    Returns:
        CanonicalState instance
    """
    return CanonicalState.from_agents(agents, config_hash)
