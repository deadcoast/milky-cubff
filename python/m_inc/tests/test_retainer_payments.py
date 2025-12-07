"""Comprehensive tests for retainer payment functionality.

Tests verify Requirements 7.1-7.5:
- 7.1: Knights with employers receive retainer payments each tick
- 7.2: Transfer occurs only if king has sufficient currency
- 7.3: Retainer payments occur after trades but before interactions
- 7.4: Retainer events are recorded with proper fields
- 7.5: Insufficient funds skip payment without error
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.economic_engine import EconomicEngine
from core.agent_registry import AgentRegistry
from core.config import RegistryConfig, EconomicConfig, TraitEmergenceConfig
from core.models import EventType, Role


def test_retainer_payment_with_sufficient_funds():
    """Test Requirement 7.1 & 7.2: Knights with employers receive retainer when king has funds."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    # Get a knight with an employer
    employed_knights = [k for k in registry.get_knights() if k.employer]
    if not employed_knights:
        print("⚠ No employed knights, skipping test")
        return
    
    knight = employed_knights[0]
    king = registry.get_agent(knight.employer)
    
    # Ensure king has sufficient currency but not enough to trade (< 100)
    retainer_fee = knight.retainer_fee
    initial_king_currency = retainer_fee + 10  # Enough for retainer but not trade
    initial_knight_currency = knight.currency
    
    king.currency = initial_king_currency
    registry.update_agent(king)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Call _pay_retainers directly to isolate retainer logic
    retainer_events = engine._pay_retainers(tick_num=1)
    
    # Verify retainer event was created
    assert len(retainer_events) > 0, "Expected at least one retainer event"
    
    # Find the specific retainer event for this knight
    knight_event = next((e for e in retainer_events if e.knight == knight.id), None)
    assert knight_event is not None, f"Expected retainer event for knight {knight.id}"
    
    # Verify currency transfer occurred
    updated_king = registry.get_agent(king.id)
    updated_knight = registry.get_agent(knight.id)
    
    assert updated_king.currency == initial_king_currency - retainer_fee, \
        f"King currency should be {initial_king_currency - retainer_fee}, got {updated_king.currency}"
    assert updated_knight.currency == initial_knight_currency + retainer_fee, \
        f"Knight currency should be {initial_knight_currency + retainer_fee}, got {updated_knight.currency}"
    
    print("✓ Retainer payment with sufficient funds works correctly")


def test_retainer_payment_insufficient_funds():
    """Test Requirement 7.5: Payment skipped without error when king lacks funds."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    # Get a knight with an employer
    employed_knights = [k for k in registry.get_knights() if k.employer]
    if not employed_knights:
        print("⚠ No employed knights, skipping test")
        return
    
    knight = employed_knights[0]
    king = registry.get_agent(knight.employer)
    
    # Set king currency below retainer fee
    initial_king_currency = knight.retainer_fee - 10
    initial_knight_currency = knight.currency
    
    king.currency = initial_king_currency
    registry.update_agent(king)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Call _pay_retainers directly to isolate retainer logic
    retainer_events = engine._pay_retainers(tick_num=1)
    
    # Verify NO retainer event was created for this knight
    knight_events = [e for e in retainer_events if e.knight == knight.id]
    assert len(knight_events) == 0, "Expected no retainer event when king lacks funds"
    
    # Verify currency unchanged
    updated_king = registry.get_agent(king.id)
    updated_knight = registry.get_agent(knight.id)
    
    assert updated_king.currency == initial_king_currency, \
        f"King currency should remain {initial_king_currency}, got {updated_king.currency}"
    assert updated_knight.currency == initial_knight_currency, \
        f"Knight currency should remain {initial_knight_currency}, got {updated_knight.currency}"
    
    print("✓ Retainer payment correctly skipped when king lacks funds")


def test_retainer_payment_order():
    """Test Requirement 7.3: Retainer payments occur after trades but before interactions."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    # Ensure at least one king can trade
    kings = registry.get_kings()
    if kings:
        kings[0].currency = 500
        registry.update_agent(kings[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick
    result = engine.process_tick(tick_num=1)
    
    # Find event indices
    trade_indices = [i for i, e in enumerate(result.events) if e.type == EventType.TRADE]
    retainer_indices = [i for i, e in enumerate(result.events) if e.type == EventType.RETAINER]
    interaction_indices = [i for i, e in enumerate(result.events) if e.type in [
        EventType.BRIBE_ACCEPT, EventType.BRIBE_INSUFFICIENT,
        EventType.DEFEND_WIN, EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID
    ]]
    
    # Verify order: trades < retainers < interactions
    if trade_indices and retainer_indices:
        assert max(trade_indices) < min(retainer_indices), \
            "Trade events should occur before retainer events"
    
    if retainer_indices and interaction_indices:
        assert max(retainer_indices) < min(interaction_indices), \
            "Retainer events should occur before interaction events"
    
    print("✓ Retainer payments occur in correct order")


def test_retainer_event_fields():
    """Test Requirement 7.4: Retainer events contain all required fields."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    # Ensure kings have enough currency
    kings = registry.get_kings()
    for king in kings:
        king.currency = 1000
        registry.update_agent(king)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick
    result = engine.process_tick(tick_num=1)
    
    # Get retainer events
    retainer_events = [e for e in result.events if e.type == EventType.RETAINER]
    
    if not retainer_events:
        print("⚠ No retainer events, skipping field validation")
        return
    
    # Verify each retainer event has required fields
    for event in retainer_events:
        assert event.tick == 1, f"Event should have tick=1, got {event.tick}"
        assert event.type == EventType.RETAINER, f"Event type should be RETAINER"
        assert event.king is not None, "Event should have king field"
        assert event.knight is not None, "Event should have knight field"
        assert event.employer is not None, "Event should have employer field"
        assert event.amount is not None, "Event should have amount field"
        assert event.amount > 0, f"Retainer amount should be positive, got {event.amount}"
        
        # Verify employer matches king
        assert event.employer == event.king, \
            f"Employer {event.employer} should match king {event.king}"
    
    print("✓ Retainer events contain all required fields")


def test_retainer_payment_multiple_knights():
    """Test that multiple employed knights all receive retainer payments."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(20))  # More agents for more knights
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    # Ensure all kings have enough currency
    kings = registry.get_kings()
    for king in kings:
        king.currency = 5000
        registry.update_agent(king)
    
    # Count employed knights
    employed_knights = [k for k in registry.get_knights() if k.employer]
    num_employed = len(employed_knights)
    
    if num_employed == 0:
        print("⚠ No employed knights, skipping test")
        return
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick
    result = engine.process_tick(tick_num=1)
    
    # Count retainer events
    retainer_events = [e for e in result.events if e.type == EventType.RETAINER]
    
    assert len(retainer_events) == num_employed, \
        f"Expected {num_employed} retainer events, got {len(retainer_events)}"
    
    # Verify each employed knight received payment
    for knight in employed_knights:
        knight_event = next((e for e in retainer_events if e.knight == knight.id), None)
        assert knight_event is not None, \
            f"Expected retainer event for employed knight {knight.id}"
    
    print(f"✓ All {num_employed} employed knights received retainer payments")


def test_retainer_payment_no_employer():
    """Test that knights without employers do not receive retainer payments."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    # Don't assign employers - all knights are free
    
    # Ensure kings have currency
    kings = registry.get_kings()
    for king in kings:
        king.currency = 1000
        registry.update_agent(king)
    
    # Verify no knights have employers
    free_knights = [k for k in registry.get_knights() if not k.employer]
    all_knights = registry.get_knights()
    
    assert len(free_knights) == len(all_knights), "All knights should be free"
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick
    result = engine.process_tick(tick_num=1)
    
    # Should have NO retainer events
    retainer_events = [e for e in result.events if e.type == EventType.RETAINER]
    assert len(retainer_events) == 0, \
        f"Expected no retainer events for free knights, got {len(retainer_events)}"
    
    print("✓ Free knights correctly do not receive retainer payments")


def test_retainer_currency_conservation():
    """Test that retainer payments conserve total currency."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    # Ensure kings have enough currency
    kings = registry.get_kings()
    for king in kings:
        king.currency = 1000
        registry.update_agent(king)
    
    # Calculate total currency before
    total_before = sum(agent.currency for agent in registry.get_all_agents())
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick (disable trait drip and trades to isolate retainer effects)
    trait_config.enabled = False
    
    # Manually call just retainer payments
    retainer_events = engine._pay_retainers(tick_num=1)
    
    # Calculate total currency after
    total_after = sum(agent.currency for agent in registry.get_all_agents())
    
    # Currency should be conserved (no creation or destruction)
    assert total_after == total_before, \
        f"Currency not conserved: before={total_before}, after={total_after}"
    
    print("✓ Retainer payments conserve total currency")


if __name__ == "__main__":
    print("Running comprehensive retainer payment tests...\n")
    
    tests = [
        test_retainer_payment_with_sufficient_funds,
        test_retainer_payment_insufficient_funds,
        test_retainer_payment_order,
        test_retainer_event_fields,
        test_retainer_payment_multiple_knights,
        test_retainer_payment_no_employer,
        test_retainer_currency_conservation,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    
    if failed == 0:
        print("\n✓ All retainer payment requirements verified!")
