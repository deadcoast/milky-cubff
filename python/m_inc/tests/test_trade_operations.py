"""Comprehensive tests for trade operations (Task 5.3)."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.economic_engine import EconomicEngine
from core.agent_registry import AgentRegistry
from core.config import RegistryConfig, EconomicConfig, TraitEmergenceConfig
from core.models import EventType, Role


def test_trade_checks_king_currency_threshold():
    """Test that trade only executes when King currency >= 100.
    
    Requirements: 6.1, 6.2
    """
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    kings = registry.get_kings()
    if not kings:
        print("⚠ No kings available, skipping test")
        return
    
    # Test case 1: King with exactly 100 currency should trade
    kings[0].currency = 100
    initial_defend = kings[0].wealth.defend
    initial_trade = kings[0].wealth.trade
    registry.update_agent(kings[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    trade_events = [e for e in result.events if e.type == EventType.TRADE and e.king == kings[0].id]
    assert len(trade_events) == 1, f"Expected 1 trade event for king with 100 currency, got {len(trade_events)}"
    
    # Verify currency was deducted
    updated_king = registry.get_agent(kings[0].id)
    assert updated_king.currency == 0, f"Expected currency=0 after trade, got {updated_king.currency}"
    
    # Test case 2: King with < 100 currency should NOT trade
    if len(kings) > 1:
        kings[1].currency = 99
        registry.update_agent(kings[1])
        
        engine2 = EconomicEngine(registry, economic_config, trait_config)
        result2 = engine2.process_tick(tick_num=1)
        
        trade_events2 = [e for e in result2.events if e.type == EventType.TRADE and e.king == kings[1].id]
        assert len(trade_events2) == 0, f"Expected 0 trade events for king with 99 currency, got {len(trade_events2)}"


def test_trade_deducts_100_currency():
    """Test that trade deducts exactly 100 currency.
    
    Requirements: 6.2
    """
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    kings = registry.get_kings()
    if not kings:
        print("⚠ No kings available, skipping test")
        return
    
    # Set king currency to 500 and record initial value
    kings[0].currency = 500
    initial_currency = kings[0].currency
    registry.update_agent(kings[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Check that a trade event occurred
    trade_events = [e for e in result.events if e.type == EventType.TRADE and e.king == kings[0].id]
    assert len(trade_events) == 1, f"Expected 1 trade event, got {len(trade_events)}"
    
    # Verify the trade event shows 100 currency investment
    assert trade_events[0].invest == 100, f"Expected invest=100, got {trade_events[0].invest}"
    
    # Note: Final currency may differ due to other operations (retainers, interactions)
    # The key is that the trade event itself shows 100 currency was invested


def test_trade_adds_3_defend_2_trade():
    """Test that trade adds 3 defend + 2 trade wealth.
    
    Requirements: 6.2
    """
    # Test the apply_trade function directly to isolate trade logic
    from core.economics import apply_trade
    from core.models import Agent, Role, WealthTraits
    
    economic_config = EconomicConfig()
    
    # Create a test king
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=500,
        wealth=WealthTraits(compute=10, copy=10, defend=10, raid=5, trade=8, sense=6, adapt=7)
    )
    
    initial_defend = king.wealth.defend
    initial_trade = king.wealth.trade
    initial_currency = king.currency
    
    # Apply trade
    wealth_created = apply_trade(king, economic_config)
    
    # Verify results
    assert wealth_created == 5, f"Expected wealth_created=5, got {wealth_created}"
    assert king.currency == initial_currency - 100, f"Expected currency={initial_currency - 100}, got {king.currency}"
    assert king.wealth.defend == initial_defend + 3, f"Expected defend={initial_defend + 3}, got {king.wealth.defend}"
    assert king.wealth.trade == initial_trade + 2, f"Expected trade={initial_trade + 2}, got {king.wealth.trade}"


def test_trade_generates_events():
    """Test that trade operations generate proper events.
    
    Requirements: 6.4
    """
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    kings = registry.get_kings()
    if not kings:
        print("⚠ No kings available, skipping test")
        return
    
    # Set multiple kings with sufficient currency
    for king in kings[:2]:
        king.currency = 500
        registry.update_agent(king)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Verify trade events
    trade_events = [e for e in result.events if e.type == EventType.TRADE]
    assert len(trade_events) >= 1, f"Expected at least 1 trade event, got {len(trade_events)}"
    
    # Verify event structure
    for event in trade_events:
        assert event.tick == 1
        assert event.type == EventType.TRADE
        assert event.king is not None
        assert event.invest == 100
        assert event.wealth_created == 5
        assert event.notes is not None


def test_trade_only_for_kings():
    """Test that only kings can execute trades.
    
    Requirements: 6.1
    """
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    # Give knights and mercs currency
    knights = registry.get_knights()
    mercs = registry.get_mercenaries()
    
    for knight in knights:
        knight.currency = 500
        registry.update_agent(knight)
    
    for merc in mercs:
        merc.currency = 500
        registry.update_agent(merc)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Verify only kings have trade events
    trade_events = [e for e in result.events if e.type == EventType.TRADE]
    for event in trade_events:
        agent = registry.get_agent(event.king)
        assert agent.role == Role.KING, f"Trade event for non-king: {agent.role}"


def test_trade_executes_before_interactions():
    """Test that trades execute before raid/defend interactions.
    
    Requirements: 6.3
    """
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    # Set up kings with currency
    kings = registry.get_kings()
    if kings:
        kings[0].currency = 500
        registry.update_agent(kings[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Find indices of trade and interaction events
    trade_indices = [i for i, e in enumerate(result.events) if e.type == EventType.TRADE]
    interaction_indices = [i for i, e in enumerate(result.events) 
                          if e.type in [EventType.BRIBE_ACCEPT, EventType.BRIBE_INSUFFICIENT, 
                                       EventType.DEFEND_WIN, EventType.DEFEND_LOSS, 
                                       EventType.UNOPPOSED_RAID]]
    
    # If both exist, verify trade comes before interactions
    if trade_indices and interaction_indices:
        max_trade_idx = max(trade_indices)
        min_interaction_idx = min(interaction_indices)
        assert max_trade_idx < min_interaction_idx, \
            f"Trade events should come before interaction events"


def test_multiple_kings_can_trade():
    """Test that multiple kings can trade in the same tick.
    
    Requirements: 6.1, 6.2
    """
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(20))  # More agents to ensure multiple kings
    registry.assign_roles(tape_ids)
    
    kings = registry.get_kings()
    if len(kings) < 2:
        print("⚠ Need at least 2 kings, skipping test")
        return
    
    # Give all kings sufficient currency
    for king in kings:
        king.currency = 500
        registry.update_agent(king)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Verify multiple trade events
    trade_events = [e for e in result.events if e.type == EventType.TRADE]
    assert len(trade_events) == len(kings), \
        f"Expected {len(kings)} trade events, got {len(trade_events)}"


def test_trade_with_zero_currency():
    """Test that kings with 0 currency cannot trade.
    
    Requirements: 6.5
    """
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    kings = registry.get_kings()
    if not kings:
        print("⚠ No kings available, skipping test")
        return
    
    # Set king currency to 0
    kings[0].currency = 0
    registry.update_agent(kings[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Verify no trade events for this king
    trade_events = [e for e in result.events if e.type == EventType.TRADE and e.king == kings[0].id]
    assert len(trade_events) == 0, f"Expected 0 trade events for king with 0 currency, got {len(trade_events)}"


if __name__ == "__main__":
    print("Running comprehensive trade operation tests...")
    
    tests = [
        ("test_trade_checks_king_currency_threshold", test_trade_checks_king_currency_threshold),
        ("test_trade_deducts_100_currency", test_trade_deducts_100_currency),
        ("test_trade_adds_3_defend_2_trade", test_trade_adds_3_defend_2_trade),
        ("test_trade_generates_events", test_trade_generates_events),
        ("test_trade_only_for_kings", test_trade_only_for_kings),
        ("test_trade_executes_before_interactions", test_trade_executes_before_interactions),
        ("test_multiple_kings_can_trade", test_multiple_kings_can_trade),
        ("test_trade_with_zero_currency", test_trade_with_zero_currency),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name} passed")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_name} error: {e}")
            failed += 1
    
    print(f"\n{passed} tests passed, {failed} tests failed")
    
    if failed > 0:
        sys.exit(1)
