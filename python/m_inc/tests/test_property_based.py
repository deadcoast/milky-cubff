"""Property-based tests for M|inc system.

These tests use Hypothesis to verify invariants and properties that should hold
across all valid inputs.

**Feature: minc-integration**
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
import copy

from core.economics import (
    sigmoid, clamp, wealth_total, wealth_exposed,
    king_defend_projection, raid_value, p_knight_win,
    resolve_bribe, resolve_defend, apply_bribe_outcome,
    apply_bribe_leakage, apply_mirrored_losses, apply_bounty
)
from core.models import Agent, WealthTraits, Role
from core.config import EconomicConfig
from core.cache import CacheLayer, CanonicalState, CacheConfig


# Strategy for generating wealth traits
@st.composite
def wealth_traits_strategy(draw):
    """Generate valid WealthTraits."""
    return WealthTraits(
        compute=draw(st.integers(min_value=0, max_value=200)),
        copy=draw(st.integers(min_value=0, max_value=200)),
        defend=draw(st.integers(min_value=0, max_value=200)),
        raid=draw(st.integers(min_value=0, max_value=200)),
        trade=draw(st.integers(min_value=0, max_value=200)),
        sense=draw(st.integers(min_value=0, max_value=200)),
        adapt=draw(st.integers(min_value=0, max_value=200))
    )


# Strategy for generating agents
@st.composite
def agent_strategy(draw, role=None):
    """Generate valid Agent."""
    if role is None:
        role = draw(st.sampled_from([Role.KING, Role.KNIGHT, Role.MERCENARY]))
    
    agent_id = draw(st.text(min_size=1, max_size=10, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"))
    tape_id = draw(st.integers(min_value=0, max_value=10000))
    currency = draw(st.integers(min_value=0, max_value=100000))
    wealth = draw(wealth_traits_strategy())
    
    agent = Agent(
        id=agent_id,
        tape_id=tape_id,
        role=role,
        currency=currency,
        wealth=wealth
    )
    
    if role == Role.KING:
        agent.bribe_threshold = draw(st.integers(min_value=0, max_value=10000))
    elif role == Role.KNIGHT:
        agent.employer = draw(st.one_of(st.none(), st.text(min_size=1, max_size=10)))
        agent.retainer_fee = draw(st.integers(min_value=0, max_value=1000))
    
    return agent


# ============================================================================
# Property 1: Currency/Wealth Non-Negativity Invariant
# **Feature: minc-integration, Property 1: Non-negativity invariant**
# **Validates: Requirements 3.5**
# ============================================================================

@given(
    king=agent_strategy(role=Role.KING),
    merc=agent_strategy(role=Role.MERCENARY)
)
@settings(max_examples=100)
def test_bribe_non_negativity(king, merc):
    """
    Property: For any king and mercenary, after a bribe transaction,
    both agents must have non-negative currency and wealth.
    
    **Feature: minc-integration, Property 1: Non-negativity invariant**
    **Validates: Requirements 3.5**
    """
    config = EconomicConfig()
    
    # Make a copy to preserve original state
    king_copy = copy.deepcopy(king)
    merc_copy = copy.deepcopy(merc)
    
    # Resolve and apply bribe
    outcome = resolve_bribe(king_copy, merc_copy, [], config)
    if outcome.accepted:
        apply_bribe_outcome(king_copy, merc_copy, outcome)
    
    # Verify non-negativity
    assert king_copy.currency >= 0, f"King currency became negative: {king_copy.currency}"
    assert merc_copy.currency >= 0, f"Merc currency became negative: {merc_copy.currency}"
    assert king_copy.wealth_total() >= 0, f"King wealth became negative: {king_copy.wealth_total()}"
    assert merc_copy.wealth_total() >= 0, f"Merc wealth became negative: {merc_copy.wealth_total()}"


@given(
    knight=agent_strategy(role=Role.KNIGHT),
    merc=agent_strategy(role=Role.MERCENARY),
    king=agent_strategy(role=Role.KING)
)
@settings(max_examples=100)
def test_defend_non_negativity(knight, merc, king):
    """
    Property: For any knight, mercenary, and king, after a defend contest,
    all agents must have non-negative currency and wealth.
    
    **Feature: minc-integration, Property 1: Non-negativity invariant**
    **Validates: Requirements 3.5**
    """
    config = EconomicConfig()
    
    # Make copies
    knight_copy = copy.deepcopy(knight)
    merc_copy = copy.deepcopy(merc)
    king_copy = copy.deepcopy(king)
    
    # Resolve defend
    outcome = resolve_defend(knight_copy, merc_copy, config)
    
    # Apply outcomes based on winner
    if outcome.knight_wins:
        # Knight wins: transfer stake from merc to knight, apply bounty
        transfer = min(outcome.stake, merc_copy.currency)
        merc_copy.currency -= transfer
        knight_copy.currency += transfer
        apply_bounty(knight_copy, merc_copy, 0.07)
    else:
        # Merc wins: apply mirrored losses, deduct stake from knight
        apply_mirrored_losses(king_copy, merc_copy, config)
        stake_deduction = min(outcome.stake, knight_copy.currency)
        knight_copy.currency -= stake_deduction
    
    # Verify non-negativity
    assert knight_copy.currency >= 0, f"Knight currency became negative: {knight_copy.currency}"
    assert merc_copy.currency >= 0, f"Merc currency became negative: {merc_copy.currency}"
    assert king_copy.currency >= 0, f"King currency became negative: {king_copy.currency}"
    assert knight_copy.wealth_total() >= 0, f"Knight wealth became negative"
    assert merc_copy.wealth_total() >= 0, f"Merc wealth became negative"
    assert king_copy.wealth_total() >= 0, f"King wealth became negative"


@given(
    agent=agent_strategy(),
    leakage_frac=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100)
def test_leakage_non_negativity(agent, leakage_frac):
    """
    Property: For any agent and leakage fraction, applying leakage
    must not result in negative wealth.
    
    **Feature: minc-integration, Property 1: Non-negativity invariant**
    **Validates: Requirements 3.5**
    """
    agent_copy = copy.deepcopy(agent)
    apply_bribe_leakage(agent_copy, leakage_frac)
    
    assert agent_copy.wealth_total() >= 0, f"Wealth became negative after leakage"
    assert agent_copy.wealth.compute >= 0
    assert agent_copy.wealth.copy >= 0
    assert agent_copy.wealth.defend >= 0
    assert agent_copy.wealth.raid >= 0
    assert agent_copy.wealth.trade >= 0
    assert agent_copy.wealth.sense >= 0
    assert agent_copy.wealth.adapt >= 0


# ============================================================================
# Property 2: Currency Conservation in Bribes
# **Feature: minc-integration, Property 2: Currency conservation**
# **Validates: Requirements 3.5, 8.1**
# ============================================================================

@given(
    king=agent_strategy(role=Role.KING),
    merc=agent_strategy(role=Role.MERCENARY)
)
@settings(max_examples=100)
def test_bribe_currency_conservation(king, merc):
    """
    Property: For any successful bribe, the total currency between
    king and mercenary is conserved (no creation or destruction).
    
    **Feature: minc-integration, Property 2: Currency conservation**
    **Validates: Requirements 3.5, 8.1**
    """
    config = EconomicConfig()
    
    # Make copies
    king_copy = copy.deepcopy(king)
    merc_copy = copy.deepcopy(merc)
    
    total_before = king_copy.currency + merc_copy.currency
    
    # Resolve and apply bribe
    outcome = resolve_bribe(king_copy, merc_copy, [], config)
    if outcome.accepted:
        apply_bribe_outcome(king_copy, merc_copy, outcome)
        
        total_after = king_copy.currency + merc_copy.currency
        
        # Currency should be conserved (no creation/destruction)
        assert total_after == total_before, \
            f"Currency not conserved: {total_before} -> {total_after}"


# ============================================================================
# Property 3: Deterministic Resolution
# **Feature: minc-integration, Property 3: Deterministic resolution**
# **Validates: Requirements 8.1, 8.2**
# ============================================================================

@given(
    knight=agent_strategy(role=Role.KNIGHT),
    merc=agent_strategy(role=Role.MERCENARY)
)
@settings(max_examples=100)
def test_defend_deterministic(knight, merc):
    """
    Property: For any knight and mercenary, resolve_defend produces
    the same outcome when called multiple times with the same inputs.
    
    **Feature: minc-integration, Property 3: Deterministic resolution**
    **Validates: Requirements 8.1, 8.2**
    """
    config = EconomicConfig()
    
    # Resolve twice
    outcome1 = resolve_defend(knight, merc, config)
    outcome2 = resolve_defend(knight, merc, config)
    
    # Should be identical
    assert outcome1.knight_wins == outcome2.knight_wins
    assert outcome1.p_knight == outcome2.p_knight
    assert outcome1.stake == outcome2.stake
    assert outcome1.knight_id == outcome2.knight_id
    assert outcome1.merc_id == outcome2.merc_id


@given(
    king=agent_strategy(role=Role.KING),
    merc=agent_strategy(role=Role.MERCENARY),
    knights=st.lists(agent_strategy(role=Role.KNIGHT), min_size=0, max_size=5)
)
@settings(max_examples=100)
def test_bribe_deterministic(king, merc, knights):
    """
    Property: For any king, mercenary, and knights, resolve_bribe produces
    the same outcome when called multiple times with the same inputs.
    
    **Feature: minc-integration, Property 3: Deterministic resolution**
    **Validates: Requirements 8.1, 8.2**
    """
    config = EconomicConfig()
    
    # Resolve twice
    outcome1 = resolve_bribe(king, merc, knights, config)
    outcome2 = resolve_bribe(king, merc, knights, config)
    
    # Should be identical
    assert outcome1.accepted == outcome2.accepted
    if outcome1.accepted:
        assert outcome1.amount == outcome2.amount
        assert outcome1.king_currency_delta == outcome2.king_currency_delta
        assert outcome1.merc_currency_delta == outcome2.merc_currency_delta
        assert outcome1.king_wealth_leakage == outcome2.king_wealth_leakage
    else:
        assert outcome1.reason == outcome2.reason


@given(
    merc=agent_strategy(role=Role.MERCENARY),
    king=agent_strategy(role=Role.KING),
    knights=st.lists(agent_strategy(role=Role.KNIGHT), min_size=0, max_size=5)
)
@settings(max_examples=100)
def test_raid_value_deterministic(merc, king, knights):
    """
    Property: For any mercenary, king, and knights, raid_value produces
    the same result when called multiple times with the same inputs.
    
    **Feature: minc-integration, Property 3: Deterministic resolution**
    **Validates: Requirements 8.1, 8.2**
    """
    config = EconomicConfig()
    
    # Compute twice
    rv1 = raid_value(merc, king, knights, config)
    rv2 = raid_value(merc, king, knights, config)
    
    # Should be identical
    assert rv1 == rv2


# ============================================================================
# Property 4: Probability Bounds
# **Feature: minc-integration, Property 4: Probability bounds**
# **Validates: Requirements 8.2**
# ============================================================================

@given(
    knight=agent_strategy(role=Role.KNIGHT),
    merc=agent_strategy(role=Role.MERCENARY)
)
@settings(max_examples=100)
def test_p_knight_win_bounds(knight, merc):
    """
    Property: For any knight and mercenary, p_knight_win must be
    clamped between 0.05 and 0.95.
    
    **Feature: minc-integration, Property 4: Probability bounds**
    **Validates: Requirements 8.2**
    """
    config = EconomicConfig()
    
    p = p_knight_win(knight, merc, config)
    
    assert 0.05 <= p <= 0.95, f"Probability out of bounds: {p}"
    assert isinstance(p, float)


# ============================================================================
# Property 5: Sigmoid Properties
# **Feature: minc-integration, Property 5: Sigmoid properties**
# **Validates: Requirements 8.1**
# ============================================================================

@given(x=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_sigmoid_bounds(x):
    """
    Property: For any finite input, sigmoid output is between 0 and 1.
    
    **Feature: minc-integration, Property 5: Sigmoid properties**
    **Validates: Requirements 8.1**
    """
    result = sigmoid(x)
    assert 0.0 <= result <= 1.0, f"Sigmoid out of bounds: {result}"


@given(x=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_sigmoid_symmetry(x):
    """
    Property: Sigmoid is symmetric around 0.5, i.e., sigmoid(-x) = 1 - sigmoid(x).
    
    **Feature: minc-integration, Property 5: Sigmoid properties**
    **Validates: Requirements 8.1**
    """
    pos = sigmoid(x)
    neg = sigmoid(-x)
    
    # Allow small floating point error
    assert abs(pos + neg - 1.0) < 1e-10, f"Sigmoid not symmetric: sigmoid({x})={pos}, sigmoid({-x})={neg}"


# ============================================================================
# Property 6: Clamp Properties
# **Feature: minc-integration, Property 6: Clamp properties**
# **Validates: Requirements 8.1**
# ============================================================================

@given(
    value=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    min_val=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_clamp_bounds(value, min_val, max_val):
    """
    Property: For any value and bounds, clamp returns a value within [min, max].
    
    **Feature: minc-integration, Property 6: Clamp properties**
    **Validates: Requirements 8.1**
    """
    assume(min_val <= max_val)  # Only test valid bounds
    
    result = clamp(value, min_val, max_val)
    
    assert min_val <= result <= max_val, f"Clamp out of bounds: {result} not in [{min_val}, {max_val}]"


@given(
    value=st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False),
    min_val=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
    max_val=st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_clamp_idempotent(value, min_val, max_val):
    """
    Property: Clamping twice is the same as clamping once (idempotent).
    
    **Feature: minc-integration, Property 6: Clamp properties**
    **Validates: Requirements 8.1**
    """
    assume(min_val <= max_val)
    
    once = clamp(value, min_val, max_val)
    twice = clamp(once, min_val, max_val)
    
    assert once == twice, f"Clamp not idempotent: {once} != {twice}"


# ============================================================================
# Property 7: Cache Correctness
# **Feature: minc-integration, Property 7: Cache correctness**
# **Validates: Requirements 12.3**
# ============================================================================

@given(
    agents=st.lists(agent_strategy(), min_size=1, max_size=10),
    config_hash=st.text(min_size=1, max_size=20, alphabet="abcdef0123456789")
)
@settings(max_examples=100)
def test_cache_correctness(agents, config_hash):
    """
    Property: For any set of agents and config hash, cached results
    must match computed results.
    
    **Feature: minc-integration, Property 7: Cache correctness**
    **Validates: Requirements 12.3**
    """
    cache_config = CacheConfig(enabled=True, max_size=1000, witness_sample_rate=0.0)
    cache = CacheLayer(cache_config)
    
    state = CanonicalState.from_agents(agents, config_hash)
    
    # Compute result
    call_count = 0
    def compute_fn():
        nonlocal call_count
        call_count += 1
        return sum(a.currency for a in agents)
    
    # First call computes
    result1 = cache.get_or_compute(state, compute_fn)
    assert call_count == 1
    
    # Second call uses cache
    result2 = cache.get_or_compute(state, compute_fn)
    assert call_count == 1  # Not called again
    
    # Results must match
    assert result1 == result2, f"Cached result {result2} != computed result {result1}"


@given(
    agents=st.lists(agent_strategy(), min_size=1, max_size=10),
    config_hash=st.text(min_size=1, max_size=20, alphabet="abcdef0123456789")
)
@settings(max_examples=100)
def test_canonical_state_ordering_invariant(agents, config_hash):
    """
    Property: For any set of agents with unique IDs, the canonical state hash is
    independent of agent ordering.
    
    **Feature: minc-integration, Property 7: Cache correctness**
    **Validates: Requirements 12.3**
    """
    # Ensure unique IDs by assigning sequential IDs
    for i, agent in enumerate(agents):
        agent.id = f"A-{i:03d}"
    
    # Create two states with different orderings
    state1 = CanonicalState.from_agents(agents, config_hash)
    state2 = CanonicalState.from_agents(list(reversed(agents)), config_hash)
    
    # Hashes should be identical
    assert state1.hash() == state2.hash(), \
        f"Canonical state hash depends on ordering"


# ============================================================================
# Property 8: Wealth Total Consistency
# **Feature: minc-integration, Property 8: Wealth total consistency**
# **Validates: Requirements 3.1, 3.2**
# ============================================================================

@given(agent=agent_strategy())
@settings(max_examples=100)
def test_wealth_total_consistency(agent):
    """
    Property: For any agent, wealth_total equals the sum of all traits.
    
    **Feature: minc-integration, Property 8: Wealth total consistency**
    **Validates: Requirements 3.1, 3.2**
    """
    total = wealth_total(agent)
    expected = (agent.wealth.compute + agent.wealth.copy + agent.wealth.defend +
                agent.wealth.raid + agent.wealth.trade + agent.wealth.sense +
                agent.wealth.adapt)
    
    assert total == expected, f"Wealth total mismatch: {total} != {expected}"


# ============================================================================
# Property 9: Raid Value Non-Negative
# **Feature: minc-integration, Property 9: Raid value non-negative**
# **Validates: Requirements 8.1**
# ============================================================================

@given(
    merc=agent_strategy(role=Role.MERCENARY),
    king=agent_strategy(role=Role.KING),
    knights=st.lists(agent_strategy(role=Role.KNIGHT), min_size=0, max_size=5)
)
@settings(max_examples=100)
def test_raid_value_non_negative(merc, king, knights):
    """
    Property: For any mercenary, king, and knights, raid_value is non-negative.
    
    **Feature: minc-integration, Property 9: Raid value non-negative**
    **Validates: Requirements 8.1**
    """
    config = EconomicConfig()
    
    rv = raid_value(merc, king, knights, config)
    
    assert rv >= 0.0, f"Raid value is negative: {rv}"


# ============================================================================
# Property 10: Defend Stake Calculation
# **Feature: minc-integration, Property 10: Defend stake calculation**
# **Validates: Requirements 5.4**
# ============================================================================

@given(
    knight=agent_strategy(role=Role.KNIGHT),
    merc=agent_strategy(role=Role.MERCENARY)
)
@settings(max_examples=100)
def test_defend_stake_bounds(knight, merc):
    """
    Property: For any knight and mercenary, the defend stake is bounded
    by the available currency.
    
    **Feature: minc-integration, Property 10: Defend stake calculation**
    **Validates: Requirements 5.4**
    """
    config = EconomicConfig()
    
    outcome = resolve_defend(knight, merc, config)
    
    # Stake should not exceed combined currency
    max_stake = knight.currency + merc.currency
    assert outcome.stake <= max_stake, \
        f"Stake {outcome.stake} exceeds available currency {max_stake}"
    assert outcome.stake >= 0, f"Stake is negative: {outcome.stake}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
