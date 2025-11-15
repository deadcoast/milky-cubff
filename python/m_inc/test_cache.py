"""Tests for cache layer."""

import pytest
from core.cache import (
    CacheLayer,
    CanonicalState,
    compute_canonical_state,
    CacheStats,
    WitnessSample,
)
from core.config import CacheConfig
from core.models import Agent, Role, WealthTraits


def test_canonical_state_computation():
    """Test canonical state computation from agents."""
    # Create test agents
    agents = [
        Agent(
            id="M-01",
            tape_id=1,
            role=Role.MERCENARY,
            currency=50,
            wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=6, adapt=5)
        ),
        Agent(
            id="K-01",
            tape_id=2,
            role=Role.KING,
            currency=6000,
            wealth=WealthTraits(compute=12, copy=15, defend=20, raid=3, trade=18, sense=7, adapt=9)
        ),
    ]
    
    config_hash = "test_hash_123"
    
    # Compute canonical state
    state = compute_canonical_state(agents, config_hash)
    
    # Verify agents are sorted by ID
    assert state.agents[0]["id"] == "K-01"
    assert state.agents[1]["id"] == "M-01"
    
    # Verify config hash is included
    assert state.config_hash == config_hash
    
    # Verify hash is computed
    state_hash = state.compute_hash()
    assert len(state_hash) == 16
    assert isinstance(state_hash, str)


def test_canonical_state_determinism():
    """Test that canonical state produces same hash for same inputs."""
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=18, raid=2, trade=15, sense=5, adapt=7)
        ),
    ]
    
    config_hash = "abc123"
    
    # Compute state twice
    state1 = compute_canonical_state(agents, config_hash)
    state2 = compute_canonical_state(agents, config_hash)
    
    # Hashes should match
    assert state1.compute_hash() == state2.compute_hash()


def test_cache_layer_basic():
    """Test basic cache operations."""
    config = CacheConfig(enabled=True, max_size=100, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    # Create a simple state
    state = CanonicalState(
        agents=[{"id": "K-01", "role": "king", "currency": 5000, "wealth": {}}],
        config_hash="test"
    )
    
    # Define a compute function
    call_count = 0
    def compute_fn(s: CanonicalState) -> int:
        nonlocal call_count
        call_count += 1
        return 42
    
    # First call should compute
    result1 = cache.get_or_compute(state, compute_fn)
    assert result1 == 42
    assert call_count == 1
    assert cache.stats.misses == 1
    assert cache.stats.hits == 0
    
    # Second call should hit cache
    result2 = cache.get_or_compute(state, compute_fn)
    assert result2 == 42
    assert call_count == 1  # Not called again
    assert cache.stats.hits == 1


def test_cache_layer_lru_eviction():
    """Test LRU eviction policy."""
    config = CacheConfig(enabled=True, max_size=2, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    # Create three different states
    state1 = CanonicalState(agents=[{"id": "K-01"}], config_hash="h1")
    state2 = CanonicalState(agents=[{"id": "K-02"}], config_hash="h2")
    state3 = CanonicalState(agents=[{"id": "K-03"}], config_hash="h3")
    
    def compute_fn(s: CanonicalState) -> str:
        return s.agents[0]["id"]
    
    # Fill cache
    cache.get_or_compute(state1, compute_fn)
    cache.get_or_compute(state2, compute_fn)
    assert len(cache) == 2
    
    # Add third item - should evict first (state1)
    cache.get_or_compute(state3, compute_fn)
    assert len(cache) == 2
    assert cache.stats.evictions == 1
    
    # state2 and state3 should still be cached
    initial_hits = cache.stats.hits
    cache.get_or_compute(state2, compute_fn)
    assert cache.stats.hits == initial_hits + 1  # Hit
    
    cache.get_or_compute(state3, compute_fn)
    assert cache.stats.hits == initial_hits + 2  # Hit


def test_cache_invalidation():
    """Test cache invalidation."""
    config = CacheConfig(enabled=True, max_size=100, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    state = CanonicalState(agents=[{"id": "K-01"}], config_hash="test")
    
    # Add entry
    cache.get_or_compute(state, lambda s: 42)
    assert len(cache) == 1
    
    # Invalidate
    cache.invalidate("test reason")
    assert len(cache) == 0


def test_cache_disabled():
    """Test that cache can be disabled."""
    config = CacheConfig(enabled=False, max_size=100, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    state = CanonicalState(agents=[{"id": "K-01"}], config_hash="test")
    
    call_count = 0
    def compute_fn(s: CanonicalState) -> int:
        nonlocal call_count
        call_count += 1
        return 42
    
    # Both calls should compute (no caching)
    cache.get_or_compute(state, compute_fn)
    cache.get_or_compute(state, compute_fn)
    
    assert call_count == 2
    assert len(cache) == 0


def test_witness_sampling():
    """Test witness sampling for cache validation."""
    config = CacheConfig(enabled=True, max_size=100, witness_sample_rate=1.0)
    cache = CacheLayer(config)
    
    state = CanonicalState(agents=[{"id": "K-01"}], config_hash="test")
    
    def compute_fn(s: CanonicalState) -> int:
        return 42
    
    # Add entry - should create witness
    cache.get_or_compute(state, compute_fn)
    assert len(cache.witnesses) == 1
    
    # Validate witnesses
    failures = cache.validate_witnesses(compute_fn)
    assert failures == 0
    assert cache.stats.witness_validations == 1
    assert cache.stats.witness_failures == 0


def test_cache_stats():
    """Test cache statistics."""
    config = CacheConfig(enabled=True, max_size=100, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    state = CanonicalState(agents=[{"id": "K-01"}], config_hash="test")
    
    # Initial stats
    stats = cache.get_stats()
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.hit_rate() == 0.0
    
    # Add some operations
    cache.get_or_compute(state, lambda s: 42)  # Miss
    cache.get_or_compute(state, lambda s: 42)  # Hit
    cache.get_or_compute(state, lambda s: 42)  # Hit
    
    stats = cache.get_stats()
    assert stats.hits == 2
    assert stats.misses == 1
    assert stats.hit_rate() == 2/3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
