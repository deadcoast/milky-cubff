"""Test retainer payment functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from m_inc.core.models import Agent, WealthTraits, Role, EventType
from m_inc.core.agent_registry import AgentRegistry
from m_inc.core.economic_engine import EconomicEngine
from m_inc.core.config import ConfigLoader


def test_retainer_payment_success():
    """Test successful retainer payment when king has sufficient funds."""
    print("\n" + "=" * 60)
    print("Test: Retainer Payment - Success Case")
    print("=" * 60)
    
    # Load config
    config_path = Path(__file__).parent / "config" / "minc_default.yaml"
    config = ConfigLoader.load(config_path)
    
    # Create registry
    registry = AgentRegistry(config.registry, seed=42)
    
    # Create a king with sufficient currency
    king = Agent(
        id="K-00",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(defend=10, trade=5),
        bribe_threshold=400
    )
    registry.agents[king.id] = king
    registry._tape_to_agent[king.tape_id] = king.id
    
    # Create a knight employed by the king
    knight = Agent(
        id="N-00",
        tape_id=2,
        role=Role.KNIGHT,
        currency=50,
        wealth=WealthTraits(defend=15, sense=8),
        employer=king.id,
        retainer_fee=100
    )
    registry.agents[knight.id] = knight
    registry._tape_to_agent[knight.tape_id] = knight.id
    
    print(f"\nInitial state:")
    print(f"  King {king.id}: currency={king.currency}")
    print(f"  Knight {knight.id}: currency={knight.currency}, employer={knight.employer}, retainer_fee={knight.retainer_fee}")
    
    # Create engine and process tick
    engine = EconomicEngine(registry, config.economic)
    result = engine.process_tick(1)
    
    # Check results
    king_after = registry.get_agent(king.id)
    knight_after = registry.get_agent(knight.id)
    
    # Note: King also executes trade (costs 100) before retainer payment
    expected_king_currency = 1000 - 100 - 100  # Initial - trade - retainer = 800
    expected_knight_currency = 50 + 100  # Initial + retainer = 150
    
    print(f"\nAfter tick 1:")
    print(f"  King {king_after.id}: currency={king_after.currency} (expected: {expected_king_currency})")
    print(f"  Knight {knight_after.id}: currency={knight_after.currency} (expected: {expected_knight_currency})")
    
    # Find retainer event
    retainer_events = [e for e in result.events if e.type == EventType.RETAINER]
    print(f"\nRetainer events: {len(retainer_events)}")
    
    if retainer_events:
        event = retainer_events[0]
        print(f"  Event: employer={event.employer}, knight={event.knight}, amount={event.amount}")
        
        # Verify event details
        assert event.employer == king.id, f"Expected employer {king.id}, got {event.employer}"
        assert event.knight == knight.id, f"Expected knight {knight.id}, got {event.knight}"
        assert event.amount == knight.retainer_fee, f"Expected amount {knight.retainer_fee}, got {event.amount}"
        print("  ✓ Event details correct")
    
    # Verify currency transfer (accounting for trade operation)
    assert king_after.currency == expected_king_currency, f"Expected king currency {expected_king_currency}, got {king_after.currency}"
    assert knight_after.currency == expected_knight_currency, f"Expected knight currency {expected_knight_currency}, got {knight_after.currency}"
    print("  ✓ Currency transfer correct")
    
    print("\n✓ Test passed!")


def test_retainer_payment_insufficient_funds():
    """Test retainer payment skipped when king has insufficient funds."""
    print("\n" + "=" * 60)
    print("Test: Retainer Payment - Insufficient Funds")
    print("=" * 60)
    
    # Load config
    config_path = Path(__file__).parent / "config" / "minc_default.yaml"
    config = ConfigLoader.load(config_path)
    
    # Create registry
    registry = AgentRegistry(config.registry, seed=42)
    
    # Create a king with insufficient currency
    king = Agent(
        id="K-00",
        tape_id=1,
        role=Role.KING,
        currency=50,  # Less than retainer fee
        wealth=WealthTraits(defend=10, trade=5),
        bribe_threshold=400
    )
    registry.agents[king.id] = king
    registry._tape_to_agent[king.tape_id] = king.id
    
    # Create a knight employed by the king
    knight = Agent(
        id="N-00",
        tape_id=2,
        role=Role.KNIGHT,
        currency=50,
        wealth=WealthTraits(defend=15, sense=8),
        employer=king.id,
        retainer_fee=100  # More than king's currency
    )
    registry.agents[knight.id] = knight
    registry._tape_to_agent[knight.tape_id] = knight.id
    
    print(f"\nInitial state:")
    print(f"  King {king.id}: currency={king.currency} (insufficient for retainer_fee={knight.retainer_fee})")
    print(f"  Knight {knight.id}: currency={knight.currency}, employer={knight.employer}")
    
    # Create engine and process tick
    engine = EconomicEngine(registry, config.economic)
    result = engine.process_tick(1)
    
    # Check results
    king_after = registry.get_agent(king.id)
    knight_after = registry.get_agent(knight.id)
    
    print(f"\nAfter tick 1:")
    print(f"  King {king_after.id}: currency={king_after.currency} (expected: unchanged at 50)")
    print(f"  Knight {knight_after.id}: currency={knight_after.currency} (expected: unchanged at 50)")
    
    # Find retainer events
    retainer_events = [e for e in result.events if e.type == EventType.RETAINER]
    print(f"\nRetainer events: {len(retainer_events)} (expected: 0)")
    
    # Verify no payment occurred
    assert king_after.currency == 50, f"Expected king currency unchanged at 50, got {king_after.currency}"
    assert knight_after.currency == 50, f"Expected knight currency unchanged at 50, got {knight_after.currency}"
    assert len(retainer_events) == 0, f"Expected no retainer events, got {len(retainer_events)}"
    print("  ✓ Payment correctly skipped")
    
    print("\n✓ Test passed!")


def test_retainer_payment_no_employer():
    """Test that knights without employers don't receive retainer payments."""
    print("\n" + "=" * 60)
    print("Test: Retainer Payment - No Employer")
    print("=" * 60)
    
    # Load config
    config_path = Path(__file__).parent / "config" / "minc_default.yaml"
    config = ConfigLoader.load(config_path)
    
    # Create registry
    registry = AgentRegistry(config.registry, seed=42)
    
    # Create a knight without an employer
    knight = Agent(
        id="N-00",
        tape_id=2,
        role=Role.KNIGHT,
        currency=50,
        wealth=WealthTraits(defend=15, sense=8),
        employer=None,  # No employer
        retainer_fee=100
    )
    registry.agents[knight.id] = knight
    registry._tape_to_agent[knight.tape_id] = knight.id
    
    print(f"\nInitial state:")
    print(f"  Knight {knight.id}: currency={knight.currency}, employer={knight.employer} (no employer)")
    
    # Create engine and process tick
    engine = EconomicEngine(registry, config.economic)
    result = engine.process_tick(1)
    
    # Check results
    knight_after = registry.get_agent(knight.id)
    
    print(f"\nAfter tick 1:")
    print(f"  Knight {knight_after.id}: currency={knight_after.currency} (expected: unchanged at 50)")
    
    # Find retainer events
    retainer_events = [e for e in result.events if e.type == EventType.RETAINER]
    print(f"\nRetainer events: {len(retainer_events)} (expected: 0)")
    
    # Verify no payment occurred
    assert knight_after.currency == 50, f"Expected knight currency unchanged at 50, got {knight_after.currency}"
    assert len(retainer_events) == 0, f"Expected no retainer events, got {len(retainer_events)}"
    print("  ✓ No payment for unemployed knight")
    
    print("\n✓ Test passed!")


def main():
    """Run all retainer payment tests."""
    print("\n" + "=" * 60)
    print("RETAINER PAYMENT TESTS")
    print("=" * 60)
    
    try:
        test_retainer_payment_success()
        test_retainer_payment_insufficient_funds()
        test_retainer_payment_no_employer()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
