"""Tests for economic calculation functions."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.models import Agent, Role, WealthTraits
from core.config import EconomicConfig
from core.economics import (
    sigmoid, clamp, wealth_total, wealth_exposed,
    king_defend_projection, raid_value, p_knight_win,
    resolve_bribe, resolve_defend, apply_bribe_outcome,
    apply_defend_outcome, BribeOutcome, DefendOutcome
)


def test_sigmoid():
    """Test sigmoid function."""
    assert 0.0 < sigmoid(0) < 1.0
    assert sigmoid(0) == 0.5
    assert sigmoid(10) > 0.9
    assert sigmoid(-10) < 0.1
    print("✓ sigmoid tests passed")


def test_clamp():
    """Test clamp function."""
    assert clamp(0.5, 0.0, 1.0) == 0.5
    assert clamp(-1.0, 0.0, 1.0) == 0.0
    assert clamp(2.0, 0.0, 1.0) == 1.0
    print("✓ clamp tests passed")


def test_wealth_functions():
    """Test wealth calculation functions."""
    config = EconomicConfig()
    
    agent = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=5, defend=15, raid=3, trade=8, sense=6, adapt=4)
    )
    
    total = wealth_total(agent)
    assert total == 51
    
    exposed = wealth_exposed(agent, config)
    assert exposed > 0
    
    print("✓ wealth function tests passed")


def test_raid_value():
    """Test raid value calculation."""
    config = EconomicConfig()
    
    merc = Agent(
        id="M-01",
        tape_id=1,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(raid=20, sense=10, adapt=8)
    )
    
    king = Agent(
        id="K-01",
        tape_id=2,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(defend=15, trade=20)
    )
    
    knights = []
    
    rv = raid_value(merc, king, knights, config)
    assert rv >= 0
    assert isinstance(rv, float)
    
    print("✓ raid_value tests passed")


def test_p_knight_win():
    """Test knight win probability calculation."""
    config = EconomicConfig()
    
    knight = Agent(
        id="N-01",
        tape_id=1,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(defend=15, sense=8, adapt=6),
        employer="K-01"
    )
    
    merc = Agent(
        id="M-01",
        tape_id=2,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(raid=12, sense=5, adapt=4)
    )
    
    p = p_knight_win(knight, merc, config)
    assert 0.05 <= p <= 0.95
    
    print("✓ p_knight_win tests passed")


def test_resolve_bribe():
    """Test bribe resolution."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(defend=15, trade=20),
        bribe_threshold=500
    )
    
    merc = Agent(
        id="M-01",
        tape_id=2,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(raid=10, sense=5, adapt=4)
    )
    
    knights = []
    
    outcome = resolve_bribe(king, merc, knights, config)
    assert isinstance(outcome, BribeOutcome)
    
    # Test insufficient funds
    king_poor = Agent(
        id="K-02",
        tape_id=3,
        role=Role.KING,
        currency=10,
        wealth=WealthTraits(defend=15),
        bribe_threshold=500
    )
    
    outcome2 = resolve_bribe(king_poor, merc, knights, config)
    assert not outcome2.accepted
    assert outcome2.reason == "insufficient_funds"
    
    print("✓ resolve_bribe tests passed")


def test_resolve_defend():
    """Test defend resolution."""
    config = EconomicConfig()
    
    knight = Agent(
        id="N-01",
        tape_id=1,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(defend=15, sense=8, adapt=6),
        employer="K-01"
    )
    
    merc = Agent(
        id="M-01",
        tape_id=2,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(raid=12, sense=5, adapt=4)
    )
    
    outcome = resolve_defend(knight, merc, config)
    assert isinstance(outcome, DefendOutcome)
    assert 0.05 <= outcome.p_knight <= 0.95
    assert outcome.stake >= 0
    
    print("✓ resolve_defend tests passed")


def test_apply_bribe_outcome():
    """Test applying bribe outcome."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(defend=15, trade=20)
    )
    
    merc = Agent(
        id="M-01",
        tape_id=2,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(raid=10)
    )
    
    initial_king_currency = king.currency
    initial_merc_currency = merc.currency
    initial_king_wealth = king.wealth_total()
    
    outcome = BribeOutcome(
        accepted=True,
        amount=500,
        king_currency_delta=-500,
        merc_currency_delta=500,
        king_wealth_leakage=0.05
    )
    
    apply_bribe_outcome(king, merc, outcome)
    
    assert king.currency == initial_king_currency - 500
    assert merc.currency == initial_merc_currency + 500
    assert king.wealth_total() < initial_king_wealth  # Leakage applied
    
    print("✓ apply_bribe_outcome tests passed")


def test_apply_defend_outcome():
    """Test applying defend outcome."""
    config = EconomicConfig()
    
    knight = Agent(
        id="N-01",
        tape_id=1,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(defend=15, sense=8, adapt=6),
        employer="K-01"
    )
    
    merc = Agent(
        id="M-01",
        tape_id=2,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(raid=12, sense=5, adapt=4)
    )
    
    king = Agent(
        id="K-01",
        tape_id=3,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(defend=15, trade=20)
    )
    
    # Test knight wins
    outcome_win = DefendOutcome(
        knight_wins=True,
        stake=30,
        p_knight=0.6,
        bounty_frac=0.07
    )
    
    initial_knight_currency = knight.currency
    initial_merc_currency = merc.currency
    
    apply_defend_outcome(knight, merc, king, outcome_win, config)
    
    assert knight.currency > initial_knight_currency  # Gained stake
    assert merc.currency < initial_merc_currency  # Lost stake
    
    print("✓ apply_defend_outcome tests passed")


if __name__ == "__main__":
    test_sigmoid()
    test_clamp()
    test_wealth_functions()
    test_raid_value()
    test_p_knight_win()
    test_resolve_bribe()
    test_resolve_defend()
    test_apply_bribe_outcome()
    test_apply_defend_outcome()
    
    print("\n✅ All economics tests passed!")
