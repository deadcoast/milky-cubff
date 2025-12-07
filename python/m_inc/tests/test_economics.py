"""Tests for economics calculation functions."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.economics import (
    sigmoid, clamp, wealth_total, wealth_exposed,
    king_defend_projection, raid_value, p_knight_win,
    resolve_bribe, resolve_defend, apply_bribe_outcome,
    apply_bribe_leakage, apply_mirrored_losses, apply_bounty,
    BribeOutcome, DefendOutcome
)
from core.models import Agent, WealthTraits, Role
from core.config import EconomicConfig


def test_sigmoid():
    """Test sigmoid function."""
    assert sigmoid(0) == 0.5
    assert abs(sigmoid(100) - 1.0) < 0.001
    assert abs(sigmoid(-100) - 0.0) < 0.001
    assert 0 < sigmoid(1) < 1


def test_clamp():
    """Test clamp function."""
    assert clamp(0.5, 0.0, 1.0) == 0.5
    assert clamp(-1.0, 0.0, 1.0) == 0.0
    assert clamp(2.0, 0.0, 1.0) == 1.0
    assert clamp(0.3, 0.1, 0.9) == 0.3


def test_wealth_total():
    """Test wealth_total function."""
    agent = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    )
    assert wealth_total(agent) == 76


def test_wealth_exposed():
    """Test wealth_exposed function."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    )
    
    # King exposure factor is 1.0
    assert wealth_exposed(king, config) == 76.0


def test_king_defend_projection():
    """Test king_defend_projection function."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    )
    
    knight1 = Agent(
        id="N-01",
        tape_id=2,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=5, copy=3, defend=15, raid=2, trade=0, sense=8, adapt=5)
    )
    
    knight2 = Agent(
        id="N-02",
        tape_id=3,
        role=Role.KNIGHT,
        currency=150,
        wealth=WealthTraits(compute=4, copy=2, defend=12, raid=1, trade=0, sense=7, adapt=4)
    )
    
    # Test with no knights
    assert king_defend_projection(king, [], 1, config) == 0.0
    
    # Test with one knight
    projection1 = king_defend_projection(king, [knight1], 1, config)
    assert projection1 > 0
    
    # Test with two knights
    projection2 = king_defend_projection(king, [knight1, knight2], 1, config)
    assert projection2 > projection1


def test_raid_value():
    """Test raid_value function."""
    config = EconomicConfig()
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    )
    
    knight = Agent(
        id="N-01",
        tape_id=2,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=5, copy=3, defend=15, raid=2, trade=0, sense=8, adapt=5)
    )
    
    # Test raid value calculation
    rv = raid_value(merc, king, [knight], config)
    assert rv >= 0.0
    assert isinstance(rv, float)


def test_p_knight_win():
    """Test p_knight_win function."""
    config = EconomicConfig()
    
    knight = Agent(
        id="N-01",
        tape_id=2,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=5, copy=3, defend=15, raid=2, trade=0, sense=8, adapt=5),
        employer="K-01"
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    # Test probability calculation
    p = p_knight_win(knight, merc, config)
    assert 0.05 <= p <= 0.95
    assert isinstance(p, float)


def test_resolve_bribe_success():
    """Test successful bribe resolution."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6),
        bribe_threshold=500
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    # Test successful bribe
    outcome = resolve_bribe(king, merc, [], config)
    assert outcome.accepted == True
    assert outcome.amount == 500
    assert outcome.king_currency_delta == -500
    assert outcome.merc_currency_delta == 500


def test_resolve_bribe_insufficient_funds():
    """Test bribe with insufficient funds."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=100,  # Not enough
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6),
        bribe_threshold=500
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    # Test insufficient funds
    outcome = resolve_bribe(king, merc, [], config)
    assert outcome.accepted == False
    assert outcome.reason == "insufficient_funds"


def test_resolve_bribe_threshold_too_low():
    """Test bribe with threshold too low."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6),
        bribe_threshold=10  # Too low
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    # Test threshold too low
    outcome = resolve_bribe(king, merc, [], config)
    assert outcome.accepted == False
    assert outcome.reason == "threshold_too_low"


def test_resolve_defend():
    """Test defend resolution."""
    config = EconomicConfig()
    
    knight = Agent(
        id="N-01",
        tape_id=2,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=5, copy=3, defend=15, raid=2, trade=0, sense=8, adapt=5)
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    # Test defend resolution
    outcome = resolve_defend(knight, merc, config)
    assert isinstance(outcome.knight_wins, bool)
    assert outcome.stake >= 0
    assert 0.05 <= outcome.p_knight <= 0.95
    assert outcome.knight_id == "N-01"
    assert outcome.merc_id == "M-01"


def test_apply_bribe_outcome():
    """Test applying bribe outcome."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    outcome = BribeOutcome(
        accepted=True,
        amount=500,
        king_currency_delta=-500,
        merc_currency_delta=500,
        king_wealth_leakage=0.05
    )
    
    initial_king_currency = king.currency
    initial_merc_currency = merc.currency
    initial_king_wealth = king.wealth_total()
    
    apply_bribe_outcome(king, merc, outcome)
    
    assert king.currency == initial_king_currency - 500
    assert merc.currency == initial_merc_currency + 500
    assert king.wealth_total() < initial_king_wealth  # Leakage applied


def test_apply_bribe_leakage():
    """Test applying bribe leakage."""
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    )
    
    initial_wealth = king.wealth_total()
    
    apply_bribe_leakage(king, 0.05)
    
    # Wealth should be reduced by approximately 5%
    # Note: Due to integer rounding per trait, the total may not be exactly 95%
    assert king.wealth_total() < initial_wealth
    assert king.wealth_total() <= int(initial_wealth * 0.95)


def test_apply_mirrored_losses():
    """Test applying mirrored losses."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    initial_king_currency = king.currency
    initial_merc_currency = merc.currency
    
    apply_mirrored_losses(king, merc, config)
    
    # King should lose currency and wealth
    assert king.currency < initial_king_currency
    # Merc should gain currency and wealth
    assert merc.currency > initial_merc_currency


def test_apply_bounty():
    """Test applying bounty."""
    knight = Agent(
        id="N-01",
        tape_id=2,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=5, copy=3, defend=15, raid=2, trade=0, sense=8, adapt=5)
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    initial_merc_raid = merc.wealth.raid
    initial_merc_adapt = merc.wealth.adapt
    initial_knight_raid = knight.wealth.raid
    initial_knight_adapt = knight.wealth.adapt
    
    apply_bounty(knight, merc, 0.07)
    
    # Merc should lose raid and adapt (7% of 15 = 1, 7% of 5 = 0)
    assert merc.wealth.raid <= initial_merc_raid
    # Knight should gain raid (at least)
    assert knight.wealth.raid >= initial_knight_raid


def test_raid_value_edge_cases():
    """Test raid_value with edge cases."""
    config = EconomicConfig()
    
    # Test with zero wealth merc
    merc_zero = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=0,
        wealth=WealthTraits(compute=0, copy=0, defend=0, raid=0, trade=0, sense=0, adapt=0)
    )
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    )
    
    rv = raid_value(merc_zero, king, [], config)
    assert rv >= 0.0  # Should not be negative
    
    # Test with very high defend king
    king_high_defend = Agent(
        id="K-02",
        tape_id=2,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=100, copy=100, defend=200, raid=50, trade=120, sense=80, adapt=60)
    )
    
    merc = Agent(
        id="M-02",
        tape_id=5,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    rv_high = raid_value(merc, king_high_defend, [], config)
    assert rv_high >= 0.0


def test_p_knight_win_edge_cases():
    """Test p_knight_win with edge cases."""
    config = EconomicConfig()
    
    # Test with very strong knight
    knight_strong = Agent(
        id="N-01",
        tape_id=2,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=50, copy=30, defend=150, raid=20, trade=0, sense=80, adapt=50)
    )
    
    merc_weak = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=5, trade=0, sense=2, adapt=1)
    )
    
    p = p_knight_win(knight_strong, merc_weak, config)
    assert p == 0.95  # Should be clamped to max
    
    # Test with very weak knight
    knight_weak = Agent(
        id="N-02",
        tape_id=3,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=0, sense=1, adapt=1)
    )
    
    merc_strong = Agent(
        id="M-02",
        tape_id=5,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=20, copy=40, defend=10, raid=150, trade=0, sense=70, adapt=50)
    )
    
    p = p_knight_win(knight_weak, merc_strong, config)
    assert p == 0.05  # Should be clamped to min


def test_resolve_defend_deterministic_tiebreak():
    """Test that resolve_defend uses deterministic tiebreaking."""
    config = EconomicConfig()
    
    # Create knight and merc with traits that result in exactly p=0.5
    # Knight: defend=10, sense=5, adapt=5 = 20
    # Merc: raid=10, sense=5, adapt=5 = 20
    # trait_delta = 0, so p should be 0.5
    knight = Agent(
        id="N-01",
        tape_id=2,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=5, copy=3, defend=10, raid=2, trade=0, sense=5, adapt=5)
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=200,
        wealth=WealthTraits(compute=5, copy=3, defend=1, raid=10, trade=0, sense=5, adapt=5)
    )
    
    # With equal relevant traits, p_knight_win should be 0.5
    outcome = resolve_defend(knight, merc, config)
    
    # Verify probability is 0.5
    assert outcome.p_knight == 0.5
    # Tiebreak should use knight.id < merc.id
    # Since "N-01" > "M-01" lexicographically, merc should win
    assert outcome.knight_wins == False


def test_wealth_transfer_non_negative():
    """Test that wealth transfers never result in negative values."""
    config = EconomicConfig()
    
    # Test with very small wealth
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=10,
        wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=1, sense=1, adapt=1)
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=5,
        wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=0, sense=1, adapt=1)
    )
    
    # Apply large losses
    apply_mirrored_losses(king, merc, config)
    
    # Verify non-negative
    assert king.currency >= 0
    assert king.wealth_total() >= 0
    assert merc.currency >= 0
    assert merc.wealth_total() >= 0


def test_currency_transfer_conservation():
    """Test that currency transfers conserve total currency (except trades)."""
    config = EconomicConfig()
    
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6),
        bribe_threshold=500
    )
    
    merc = Agent(
        id="M-01",
        tape_id=4,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=7, adapt=5)
    )
    
    total_before = king.currency + merc.currency
    
    # Apply bribe
    outcome = resolve_bribe(king, merc, [], config)
    apply_bribe_outcome(king, merc, outcome)
    
    total_after = king.currency + merc.currency
    
    # Currency should be conserved in bribe (no creation/destruction)
    assert total_after == total_before


if __name__ == "__main__":
    # Run all tests
    print("Running economics tests...")
    
    tests = [
        ("test_sigmoid", test_sigmoid),
        ("test_clamp", test_clamp),
        ("test_wealth_total", test_wealth_total),
        ("test_wealth_exposed", test_wealth_exposed),
        ("test_king_defend_projection", test_king_defend_projection),
        ("test_raid_value", test_raid_value),
        ("test_p_knight_win", test_p_knight_win),
        ("test_resolve_bribe_success", test_resolve_bribe_success),
        ("test_resolve_bribe_insufficient_funds", test_resolve_bribe_insufficient_funds),
        ("test_resolve_bribe_threshold_too_low", test_resolve_bribe_threshold_too_low),
        ("test_resolve_defend", test_resolve_defend),
        ("test_apply_bribe_outcome", test_apply_bribe_outcome),
        ("test_apply_bribe_leakage", test_apply_bribe_leakage),
        ("test_apply_mirrored_losses", test_apply_mirrored_losses),
        ("test_apply_bounty", test_apply_bounty),
        ("test_raid_value_edge_cases", test_raid_value_edge_cases),
        ("test_p_knight_win_edge_cases", test_p_knight_win_edge_cases),
        ("test_resolve_defend_deterministic_tiebreak", test_resolve_defend_deterministic_tiebreak),
        ("test_wealth_transfer_non_negative", test_wealth_transfer_non_negative),
        ("test_currency_transfer_conservation", test_currency_transfer_conservation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name} passed")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{passed} tests passed, {failed} tests failed")
