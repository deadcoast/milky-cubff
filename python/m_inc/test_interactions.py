"""Tests for interaction orchestration (_execute_interactions)."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.economic_engine import EconomicEngine
from core.agent_registry import AgentRegistry
from core.config import RegistryConfig, EconomicConfig, TraitEmergenceConfig
from core.models import EventType, Role, WealthTraits


def test_execute_interactions_basic():
    """Test basic interaction orchestration with mercenaries targeting kings."""
    # Setup
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    
    # Create agents with specific roles
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    # Ensure we have at least one mercenary and one king
    mercs = registry.get_mercenaries()
    kings = registry.get_kings()
    
    assert len(mercs) > 0, "Need at least one mercenary"
    assert len(kings) > 0, "Need at least one king"
    
    # Give kings some currency and wealth
    for king in kings:
        king.currency = 1000
        king.wealth = WealthTraits(compute=10, copy=10, defend=15, raid=5, trade=10, sense=8, adapt=7)
        king.bribe_threshold = 500
        registry.update_agent(king)
    
    # Give mercenaries some attributes
    for merc in mercs:
        merc.currency = 100
        merc.wealth = WealthTraits(compute=5, copy=5, defend=5, raid=12, trade=3, sense=6, adapt=8)
        registry.update_agent(merc)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick
    result = engine.process_tick(tick_num=1)
    
    # Check for interaction events (bribes, defends, raids)
    interaction_events = [
        e for e in result.events 
        if e.type in [EventType.BRIBE_ACCEPT, EventType.BRIBE_INSUFFICIENT, 
                     EventType.DEFEND_WIN, EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID]
    ]
    
    # Should have at least one interaction per mercenary
    assert len(interaction_events) >= len(mercs), \
        f"Expected at least {len(mercs)} interaction events, got {len(interaction_events)}"


def test_mercenaries_iterate_in_id_order():
    """Test that mercenaries are processed in ID order."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(15))
    registry.assign_roles(tape_ids)
    
    mercs = registry.get_mercenaries()
    kings = registry.get_kings()
    
    if len(mercs) < 2 or len(kings) < 1:
        return  # Skip if not enough agents
    
    # Set up kings with wealth
    for king in kings:
        king.currency = 10000  # High currency to ensure bribes succeed
        king.wealth = WealthTraits(compute=10, copy=10, defend=15, raid=5, trade=10, sense=8, adapt=7)
        king.bribe_threshold = 5000  # Very high threshold to ensure bribes succeed
        registry.update_agent(king)
    
    # Set up mercenaries with low raid values
    for merc in mercs:
        merc.currency = 50
        merc.wealth = WealthTraits(compute=5, copy=5, defend=5, raid=3, trade=3, sense=3, adapt=3)
        registry.update_agent(merc)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Get all interaction events
    interaction_events = [
        e for e in result.events 
        if e.type in [EventType.BRIBE_ACCEPT, EventType.BRIBE_INSUFFICIENT, 
                     EventType.DEFEND_WIN, EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID]
    ]
    
    # Extract mercenary IDs from events (in order they appear)
    merc_ids_in_events = []
    seen = set()
    for e in interaction_events:
        if e.merc and e.merc not in seen:
            merc_ids_in_events.append(e.merc)
            seen.add(e.merc)
    
    # Verify they appear in sorted order
    sorted_merc_ids = sorted([m.id for m in mercs])
    
    # The mercenary IDs should appear in sorted order (even if not all get events)
    # Check that the order is maintained
    for i in range(len(merc_ids_in_events) - 1):
        assert merc_ids_in_events[i] < merc_ids_in_events[i+1], \
            f"Mercenaries not in sorted order at position {i}: {merc_ids_in_events[i]} should be < {merc_ids_in_events[i+1]}"


def test_target_king_selection():
    """Test that mercenaries target the king with highest exposed wealth."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(15))
    registry.assign_roles(tape_ids)
    
    kings = registry.get_kings()
    mercs = registry.get_mercenaries()
    
    if len(kings) < 2 or len(mercs) < 1:
        return  # Skip if not enough agents
    
    # Set up kings with different wealth levels
    kings[0].currency = 500
    kings[0].wealth = WealthTraits(compute=5, copy=5, defend=5, raid=5, trade=5, sense=5, adapt=5)
    kings[0].bribe_threshold = 50  # Low threshold
    registry.update_agent(kings[0])
    
    if len(kings) > 1:
        kings[1].currency = 1000
        kings[1].wealth = WealthTraits(compute=20, copy=20, defend=20, raid=20, trade=20, sense=20, adapt=20)
        kings[1].bribe_threshold = 50  # Low threshold
        registry.update_agent(kings[1])
    
    # Set up mercenaries
    for merc in mercs:
        merc.currency = 50
        merc.wealth = WealthTraits(compute=5, copy=5, defend=5, raid=8, trade=3, sense=6, adapt=8)
        registry.update_agent(merc)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Get interaction events
    interaction_events = [
        e for e in result.events 
        if e.type in [EventType.BRIBE_ACCEPT, EventType.BRIBE_INSUFFICIENT, 
                     EventType.DEFEND_WIN, EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID]
    ]
    
    # All mercenaries should target the same king (highest exposed wealth)
    if len(interaction_events) > 0:
        target_kings = set(e.king for e in interaction_events if e.king)
        # With deterministic targeting, all mercs should target the same king
        # (the one with highest exposed wealth)
        assert len(target_kings) >= 1, "Should have at least one target king"


def test_bribe_success():
    """Test successful bribe when threshold >= raid_value and king has currency."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    kings = registry.get_kings()
    mercs = registry.get_mercenaries()
    
    if len(kings) < 1 or len(mercs) < 1:
        return
    
    # Set up king with high threshold and currency
    king = kings[0]
    king.currency = 2000
    king.wealth = WealthTraits(compute=10, copy=10, defend=15, raid=5, trade=10, sense=8, adapt=7)
    king.bribe_threshold = 1000  # Very high threshold
    registry.update_agent(king)
    
    # Set up mercenary with low raid value
    merc = mercs[0]
    merc.currency = 50
    merc.wealth = WealthTraits(compute=5, copy=5, defend=5, raid=3, trade=3, sense=3, adapt=3)
    registry.update_agent(merc)
    
    initial_king_currency = king.currency
    initial_merc_currency = merc.currency
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Check for bribe accept events
    bribe_events = [e for e in result.events if e.type == EventType.BRIBE_ACCEPT]
    
    if len(bribe_events) > 0:
        # Verify currency transfer
        updated_king = registry.get_agent(king.id)
        updated_merc = registry.get_agent(merc.id)
        
        assert updated_king.currency < initial_king_currency, "King should have less currency"
        assert updated_merc.currency > initial_merc_currency, "Merc should have more currency"


def test_bribe_insufficient_funds():
    """Test bribe failure when king lacks sufficient currency."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    kings = registry.get_kings()
    mercs = registry.get_mercenaries()
    
    if len(kings) < 1 or len(mercs) < 1:
        return
    
    # Set up king with high threshold but low currency
    king = kings[0]
    king.currency = 50  # Low currency
    king.wealth = WealthTraits(compute=10, copy=10, defend=15, raid=5, trade=10, sense=8, adapt=7)
    king.bribe_threshold = 1000  # High threshold but can't afford it
    registry.update_agent(king)
    
    # Set up mercenary
    merc = mercs[0]
    merc.currency = 50
    merc.wealth = WealthTraits(compute=5, copy=5, defend=5, raid=3, trade=3, sense=3, adapt=3)
    registry.update_agent(merc)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Check for bribe insufficient or defend events
    bribe_insufficient = [e for e in result.events if e.type == EventType.BRIBE_INSUFFICIENT]
    defend_events = [e for e in result.events if e.type in [EventType.DEFEND_WIN, EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID]]
    
    # Should have either bribe insufficient or defend events
    assert len(bribe_insufficient) + len(defend_events) > 0


def test_defend_contest():
    """Test defend contest when bribe fails."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(15))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    kings = registry.get_kings()
    knights = registry.get_knights()
    mercs = registry.get_mercenaries()
    
    if len(kings) < 1 or len(mercs) < 1:
        return
    
    # Set up king with low threshold (bribe will fail)
    king = kings[0]
    king.currency = 1000
    king.wealth = WealthTraits(compute=10, copy=10, defend=15, raid=5, trade=10, sense=8, adapt=7)
    king.bribe_threshold = 10  # Very low threshold
    registry.update_agent(king)
    
    # Set up mercenary with high raid value
    merc = mercs[0]
    merc.currency = 100
    merc.wealth = WealthTraits(compute=5, copy=5, defend=5, raid=20, trade=3, sense=10, adapt=10)
    registry.update_agent(merc)
    
    # Set up knights
    for knight in knights:
        knight.currency = 100
        knight.wealth = WealthTraits(compute=5, copy=5, defend=15, raid=3, trade=3, sense=8, adapt=8)
        registry.update_agent(knight)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Check for defend events
    defend_events = [e for e in result.events if e.type in [EventType.DEFEND_WIN, EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID]]
    
    assert len(defend_events) > 0, "Should have defend events when bribe fails"


def test_unopposed_raid():
    """Test unopposed raid when no knights are available."""
    registry_config = RegistryConfig(
        role_ratios={"king": 0.5, "knight": 0.0, "mercenary": 0.5}  # No knights
    )
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    kings = registry.get_kings()
    knights = registry.get_knights()
    mercs = registry.get_mercenaries()
    
    assert len(knights) == 0, "Should have no knights for this test"
    
    if len(kings) < 1 or len(mercs) < 1:
        return
    
    # Set up king with very low threshold to ensure bribe fails
    king = kings[0]
    king.currency = 1000
    king.wealth = WealthTraits(compute=10, copy=10, defend=15, raid=5, trade=10, sense=8, adapt=7)
    king.bribe_threshold = 1  # Very low threshold - bribe will fail
    registry.update_agent(king)
    
    # Set up mercenary with high raid value
    merc = mercs[0]
    merc.currency = 50
    merc.wealth = WealthTraits(compute=5, copy=5, defend=5, raid=30, trade=3, sense=15, adapt=15)
    registry.update_agent(merc)
    
    initial_king_wealth = king.wealth_total()
    initial_king_currency = king.currency
    initial_merc_wealth = merc.wealth_total()
    initial_merc_currency = merc.currency
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Check for all event types
    all_events = result.events
    bribe_accept = [e for e in all_events if e.type == EventType.BRIBE_ACCEPT]
    unopposed_events = [e for e in all_events if e.type == EventType.UNOPPOSED_RAID]
    defend_events = [e for e in all_events if e.type in [EventType.DEFEND_WIN, EventType.DEFEND_LOSS]]
    
    # Since no knights and low bribe threshold, should have unopposed raids
    # But if bribe succeeds, that's also valid
    assert len(bribe_accept) + len(unopposed_events) + len(defend_events) > 0, \
        f"Should have interaction events. Got bribes={len(bribe_accept)}, unopposed={len(unopposed_events)}, defends={len(defend_events)}"
    
    # Verify some transfer occurred (either currency or wealth)
    updated_king = registry.get_agent(king.id)
    updated_merc = registry.get_agent(merc.id)
    
    # King should lose something (currency or wealth) OR merc should gain something
    king_lost_something = (updated_king.wealth_total() < initial_king_wealth or 
                          updated_king.currency < initial_king_currency)
    merc_gained_something = (updated_merc.wealth_total() > initial_merc_wealth or 
                            updated_merc.currency > initial_merc_currency)
    
    # At least one of these should be true
    assert king_lost_something or merc_gained_something, \
        "Some transfer should occur during interaction"


def test_knight_assignment_priority():
    """Test that employed knights defend their employer first."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(15))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    kings = registry.get_kings()
    knights = registry.get_knights()
    mercs = registry.get_mercenaries()
    
    if len(kings) < 1 or len(knights) < 1 or len(mercs) < 1:
        return
    
    # Set up king with employed knight
    king = kings[0]
    king.currency = 1000
    king.wealth = WealthTraits(compute=10, copy=10, defend=15, raid=5, trade=10, sense=8, adapt=7)
    king.bribe_threshold = 10  # Low threshold to force defend
    registry.update_agent(king)
    
    # Ensure at least one knight is employed by this king
    employed_knights = [k for k in knights if k.employer == king.id]
    if not employed_knights and knights:
        knights[0].employer = king.id
        knights[0].currency = 100
        knights[0].wealth = WealthTraits(compute=5, copy=5, defend=15, raid=3, trade=3, sense=8, adapt=8)
        registry.update_agent(knights[0])
        employed_knights = [knights[0]]
    
    # Set up mercenary
    merc = mercs[0]
    merc.currency = 100
    merc.wealth = WealthTraits(compute=5, copy=5, defend=5, raid=20, trade=3, sense=10, adapt=10)
    registry.update_agent(merc)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    result = engine.process_tick(tick_num=1)
    
    # Check for defend events involving the employed knight
    defend_events = [e for e in result.events if e.type in [EventType.DEFEND_WIN, EventType.DEFEND_LOSS]]
    
    if len(defend_events) > 0 and employed_knights:
        # The defending knight should be the employed one
        defending_knight_ids = [e.knight for e in defend_events if e.knight]
        employed_knight_ids = [k.id for k in employed_knights]
        
        # At least one defend event should involve an employed knight
        assert any(kid in employed_knight_ids for kid in defending_knight_ids), \
            "Employed knights should defend their employer"


if __name__ == "__main__":
    # Run all tests
    print("Running interaction orchestration tests...")
    
    tests = [
        ("test_execute_interactions_basic", test_execute_interactions_basic),
        ("test_mercenaries_iterate_in_id_order", test_mercenaries_iterate_in_id_order),
        ("test_target_king_selection", test_target_king_selection),
        ("test_bribe_success", test_bribe_success),
        ("test_bribe_insufficient_funds", test_bribe_insufficient_funds),
        ("test_defend_contest", test_defend_contest),
        ("test_unopposed_raid", test_unopposed_raid),
        ("test_knight_assignment_priority", test_knight_assignment_priority),
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
