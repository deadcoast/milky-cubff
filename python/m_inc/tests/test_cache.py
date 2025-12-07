"""Tests for cache layer."""

import pytest
from core.cache import (
    CacheLayer,
    CanonicalState,
    WitnessSample,
    compute_canonical_state
)
from core.config import CacheConfig
from core.models import Agent, WealthTraits, Role


def test_canonical_state_hash():
    """Test that canonical state produces consistent hashes."""
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
        ),
        Agent(
            id="M-01",
            tape_id=2,
            role=Role.MERCENARY,
            currency=50,
            wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=6, adapt=5)
        )
    ]
    
    config_hash = "abc123"
    
    # Create canonical state
    state1 = CanonicalState.from_agents(agents, config_hash)
    state2 = CanonicalState.from_agents(agents, config_hash)
    
    # Hashes should be identical
    assert state1.hash() == state2.hash()


def test_canonical_state_ordering():
    """Test that agent ordering doesn't affect canonical state hash."""
    agent1 = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
    )
    agent2 = Agent(
        id="M-01",
        tape_id=2,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=6, adapt=5)
    )
    
    config_hash = "abc123"
    
    # Create states with different orderings
    state1 = CanonicalState.from_agents([agent1, agent2], config_hash)
    state2 = CanonicalState.from_agents([agent2, agent1], config_hash)
    
    # Hashes should be identical (agents sorted by ID)
    assert state1.hash() == state2.hash()


def test_canonical_state_different_config():
    """Test that different config hashes produce different state hashes."""
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
        )
    ]
    
    state1 = CanonicalState.from_agents(agents, "config1")
    state2 = CanonicalState.from_agents(agents, "config2")
    
    # Different config hashes should produce different state hashes
    assert state1.hash() != state2.hash()


def test_cache_layer_basic():
    """Test basic cache operations."""
    config = CacheConfig(enabled=True, max_size=100, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
        )
    ]
    
    state = CanonicalState.from_agents(agents, "config_hash")
    
    # First call should compute
    call_count = 0
    def compute_fn():
        nonlocal call_count
        call_count += 1
        return 42
    
    result1 = cache.get_or_compute(state, compute_fn)
    assert result1 == 42
    assert call_count == 1
    assert cache.stats.misses == 1
    assert cache.stats.hits == 0
    
    # Second call should use cache
    result2 = cache.get_or_compute(state, compute_fn)
    assert result2 == 42
    assert call_count == 1  # Not called again
    assert cache.stats.hits == 1


def test_cache_layer_disabled():
    """Test that cache can be disabled."""
    config = CacheConfig(enabled=False, max_size=100, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
        )
    ]
    
    state = CanonicalState.from_agents(agents, "config_hash")
    
    call_count = 0
    def compute_fn():
        nonlocal call_count
        call_count += 1
        return 42
    
    # Both calls should compute (cache disabled)
    result1 = cache.get_or_compute(state, compute_fn)
    result2 = cache.get_or_compute(state, compute_fn)
    
    assert result1 == 42
    assert result2 == 42
    assert call_count == 2  # Called twice


def test_cache_layer_lru_eviction():
    """Test LRU eviction when cache is full."""
    config = CacheConfig(enabled=True, max_size=2, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    # Create three different states
    agents1 = [Agent(id="K-01", tape_id=1, role=Role.KING, currency=1000,
                     wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7))]
    agents2 = [Agent(id="K-02", tape_id=2, role=Role.KING, currency=2000,
                     wealth=WealthTraits(compute=11, copy=13, defend=21, raid=4, trade=16, sense=6, adapt=8))]
    agents3 = [Agent(id="K-03", tape_id=3, role=Role.KING, currency=3000,
                     wealth=WealthTraits(compute=12, copy=14, defend=22, raid=5, trade=17, sense=7, adapt=9))]
    
    state1 = CanonicalState.from_agents(agents1, "config")
    state2 = CanonicalState.from_agents(agents2, "config")
    state3 = CanonicalState.from_agents(agents3, "config")
    
    # Fill cache
    cache.get_or_compute(state1, lambda: "result1")
    cache.get_or_compute(state2, lambda: "result2")
    
    assert cache.get_size() == 2
    assert cache.stats.evictions == 0
    
    # Add third entry - should evict first
    cache.get_or_compute(state3, lambda: "result3")
    
    assert cache.get_size() == 2
    assert cache.stats.evictions == 1
    
    # State1 should be evicted, state2 and state3 should be cached
    call_count = 0
    def recompute():
        nonlocal call_count
        call_count += 1
        return "recomputed"
    
    cache.get_or_compute(state1, recompute)
    assert call_count == 1  # Had to recompute
    
    # After adding state1 back, state2 was evicted (it was oldest)
    # So state1 and state3 should be cached now
    call_count = 0
    cache.get_or_compute(state3, recompute)
    assert call_count == 0  # Still cached


def test_cache_invalidation():
    """Test cache invalidation."""
    config = CacheConfig(enabled=True, max_size=100, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
        )
    ]
    
    state = CanonicalState.from_agents(agents, "config_hash")
    
    # Cache a result
    cache.get_or_compute(state, lambda: 42)
    assert cache.get_size() == 1
    assert cache.stats.hits == 0
    
    # Verify it's cached
    cache.get_or_compute(state, lambda: 42)
    assert cache.stats.hits == 1
    
    # Invalidate cache
    cache.invalidate("test invalidation")
    assert cache.get_size() == 0
    assert cache.stats.invalidations == 1
    
    # Should need to recompute
    cache.get_or_compute(state, lambda: 42)
    assert cache.stats.misses == 2  # Original miss + miss after invalidation


def test_witness_sampling():
    """Test witness sample storage."""
    config = CacheConfig(enabled=True, max_size=100, witness_sample_rate=1.0)  # Always sample
    cache = CacheLayer(config)
    
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
        )
    ]
    
    state = CanonicalState.from_agents(agents, "config_hash")
    
    # Cache a result
    cache.get_or_compute(state, lambda: 42)
    
    # Should have a witness sample
    assert cache.get_witness_count() == 1


def test_witness_validation():
    """Test witness validation."""
    config = CacheConfig(enabled=True, max_size=100, witness_sample_rate=1.0)
    cache = CacheLayer(config)
    
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
        )
    ]
    
    state = CanonicalState.from_agents(agents, "config_hash")
    
    # Cache a result
    cache.get_or_compute(state, lambda: 42)
    
    # Validate witnesses
    failures = cache.validate_witnesses()
    assert len(failures) == 0
    assert cache.stats.witness_validations == 1
    assert cache.stats.witness_failures == 0


def test_cache_stats():
    """Test cache statistics."""
    config = CacheConfig(enabled=True, max_size=100, witness_sample_rate=0.0)
    cache = CacheLayer(config)
    
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
        )
    ]
    
    state = CanonicalState.from_agents(agents, "config_hash")
    
    # Initial stats
    stats = cache.get_stats()
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.hit_rate() == 0.0
    
    # Cache miss
    cache.get_or_compute(state, lambda: 42)
    stats = cache.get_stats()
    assert stats.misses == 1
    assert stats.hit_rate() == 0.0
    
    # Cache hit
    cache.get_or_compute(state, lambda: 42)
    stats = cache.get_stats()
    assert stats.hits == 1
    assert stats.hit_rate() == 0.5
    
    # Another hit
    cache.get_or_compute(state, lambda: 42)
    stats = cache.get_stats()
    assert stats.hits == 2
    assert stats.hit_rate() == pytest.approx(0.667, rel=0.01)


def test_compute_canonical_state_function():
    """Test the convenience function for computing canonical state."""
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=5, adapt=7)
        )
    ]
    
    state = compute_canonical_state(agents, "config_hash")
    
    assert isinstance(state, CanonicalState)
    assert len(state.agents) == 1
    assert state.config_hash == "config_hash"
    assert state.agents[0]["id"] == "K-01"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
