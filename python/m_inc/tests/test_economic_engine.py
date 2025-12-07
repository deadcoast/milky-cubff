"""Tests for economic engine."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.economic_engine import EconomicEngine
from core.agent_registry import AgentRegistry
from core.config import RegistryConfig, EconomicConfig, TraitEmergenceConfig
from core.models import EventType


def test_economic_engine_initialization():
    """Test that EconomicEngine can be initialized."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig()
    
    registry = AgentRegistry(registry_config, seed=42)
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    assert engine.registry == registry
    assert engine.config == economic_config
    assert engine.trait_config == trait_config


def test_process_tick_basic():
    """Test basic tick processing with minimal agents."""
    # Setup
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig()
    
    registry = AgentRegistry(registry_config, seed=42)
    
    # Create some agents
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process a tick
    result = engine.process_tick(tick_num=1)
    
    # Verify result structure
    assert result.tick_num == 1
    assert isinstance(result.events, list)
    assert result.metrics is not None
    assert isinstance(result.agent_snapshots, list)
    assert len(result.agent_snapshots) == 10


def test_soup_drip():
    """Test trait emergence (soup drip) functionality."""
    # Setup with trait emergence enabled
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(
        enabled=True,
        rules=[
            {
                "condition": "copy >= 12 and tick % 2 == 0",  # Use lowercase 'and'
                "delta": {"copy": 1}
            }
        ]
    )
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(5))
    registry.assign_roles(tape_ids)
    
    # Set one agent's copy trait to 12
    agents = registry.get_all_agents()
    if not agents:
        return  # Skip test if no agents
    
    agents[0].wealth.copy = 12
    registry.update_agent(agents[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick 2 (even tick)
    result = engine.process_tick(tick_num=2)
    
    # Check for trait drip events
    drip_events = [e for e in result.events if e.type == EventType.TRAIT_DRIP]
    assert len(drip_events) > 0, f"Expected trait drip events, got {len(drip_events)}"
    
    # Verify the agent's copy trait increased
    updated_agent = registry.get_agent(agents[0].id)
    assert updated_agent.wealth.copy == 13, f"Expected copy=13, got {updated_agent.wealth.copy}"


def test_soup_drip_odd_tick():
    """Test that soup drip does NOT occur on odd ticks."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(
        enabled=True,
        rules=[
            {
                "condition": "copy >= 12 and tick % 2 == 0",
                "delta": {"copy": 1}
            }
        ]
    )
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(5))
    registry.assign_roles(tape_ids)
    
    agents = registry.get_all_agents()
    if not agents:
        return
    
    agents[0].wealth.copy = 12
    registry.update_agent(agents[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick 1 (odd tick)
    result = engine.process_tick(tick_num=1)
    
    # Should NOT have trait drip events
    drip_events = [e for e in result.events if e.type == EventType.TRAIT_DRIP]
    assert len(drip_events) == 0, f"Expected no trait drip events on odd tick, got {len(drip_events)}"
    
    # Verify the agent's copy trait did NOT increase
    updated_agent = registry.get_agent(agents[0].id)
    assert updated_agent.wealth.copy == 12, f"Expected copy=12, got {updated_agent.wealth.copy}"


def test_soup_drip_below_threshold():
    """Test that soup drip does NOT occur when copy < 12."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(
        enabled=True,
        rules=[
            {
                "condition": "copy >= 12 and tick % 2 == 0",
                "delta": {"copy": 1}
            }
        ]
    )
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(5))
    registry.assign_roles(tape_ids)
    
    agents = registry.get_all_agents()
    if not agents:
        return
    
    agents[0].wealth.copy = 11  # Below threshold
    registry.update_agent(agents[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick 2 (even tick)
    result = engine.process_tick(tick_num=2)
    
    # Should NOT have trait drip events
    drip_events = [e for e in result.events if e.type == EventType.TRAIT_DRIP]
    assert len(drip_events) == 0, f"Expected no trait drip events below threshold, got {len(drip_events)}"
    
    # Verify the agent's copy trait did NOT increase
    updated_agent = registry.get_agent(agents[0].id)
    assert updated_agent.wealth.copy == 11, f"Expected copy=11, got {updated_agent.wealth.copy}"


def test_soup_drip_disabled():
    """Test that soup drip does NOT occur when disabled."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(
        enabled=False,  # Disabled
        rules=[
            {
                "condition": "copy >= 12 and tick % 2 == 0",
                "delta": {"copy": 1}
            }
        ]
    )
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(5))
    registry.assign_roles(tape_ids)
    
    agents = registry.get_all_agents()
    if not agents:
        return
    
    agents[0].wealth.copy = 12
    registry.update_agent(agents[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick 2 (even tick)
    result = engine.process_tick(tick_num=2)
    
    # Should NOT have trait drip events when disabled
    drip_events = [e for e in result.events if e.type == EventType.TRAIT_DRIP]
    assert len(drip_events) == 0, f"Expected no trait drip events when disabled, got {len(drip_events)}"
    
    # Verify the agent's copy trait did NOT increase
    updated_agent = registry.get_agent(agents[0].id)
    assert updated_agent.wealth.copy == 12, f"Expected copy=12, got {updated_agent.wealth.copy}"


def test_soup_drip_multiple_agents():
    """Test that soup drip applies to multiple agents."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(
        enabled=True,
        rules=[
            {
                "condition": "copy >= 12 and tick % 2 == 0",
                "delta": {"copy": 1}
            }
        ]
    )
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(5))
    registry.assign_roles(tape_ids)
    
    agents = registry.get_all_agents()
    if len(agents) < 3:
        return
    
    # Set multiple agents' copy trait to 12
    agents[0].wealth.copy = 12
    agents[1].wealth.copy = 15
    agents[2].wealth.copy = 11  # Below threshold
    registry.update_agent(agents[0])
    registry.update_agent(agents[1])
    registry.update_agent(agents[2])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick 2 (even tick)
    result = engine.process_tick(tick_num=2)
    
    # Should have 2 trait drip events (agents 0 and 1)
    drip_events = [e for e in result.events if e.type == EventType.TRAIT_DRIP]
    assert len(drip_events) == 2, f"Expected 2 trait drip events, got {len(drip_events)}"
    
    # Verify agents' copy traits
    updated_agent0 = registry.get_agent(agents[0].id)
    updated_agent1 = registry.get_agent(agents[1].id)
    updated_agent2 = registry.get_agent(agents[2].id)
    assert updated_agent0.wealth.copy == 13
    assert updated_agent1.wealth.copy == 16
    assert updated_agent2.wealth.copy == 11  # Unchanged


def test_execute_trades():
    """Test trade execution for kings."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    # Ensure at least one king has enough currency
    kings = registry.get_kings()
    if kings:
        kings[0].currency = 500
        registry.update_agent(kings[0])
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick
    result = engine.process_tick(tick_num=1)
    
    # Check for trade events
    trade_events = [e for e in result.events if e.type == EventType.TRADE]
    assert len(trade_events) > 0


def test_pay_retainers():
    """Test retainer payment from kings to knights."""
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
    
    # Check for retainer events
    retainer_events = [e for e in result.events if e.type == EventType.RETAINER]
    
    # Should have retainer events if there are employed knights
    employed_knights = [k for k in registry.get_knights() if k.employer]
    assert len(retainer_events) == len(employed_knights)


def test_compute_metrics():
    """Test metrics computation."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick
    result = engine.process_tick(tick_num=1)
    
    # Verify metrics
    metrics = result.metrics
    assert metrics.wealth_total >= 0
    assert metrics.currency_total >= 0
    assert metrics.copy_score_mean >= 0.0


def test_snapshot_agents():
    """Test agent snapshot creation."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(5))
    registry.assign_roles(tape_ids)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick
    result = engine.process_tick(tick_num=1)
    
    # Verify snapshots
    assert len(result.agent_snapshots) == 5
    for snapshot in result.agent_snapshots:
        assert snapshot.id is not None
        assert snapshot.role is not None
        assert snapshot.currency >= 0
        assert snapshot.wealth is not None


def test_tick_result_serialization():
    """Test that TickResult can be serialized to dict."""
    registry_config = RegistryConfig()
    economic_config = EconomicConfig()
    trait_config = TraitEmergenceConfig(enabled=False)
    
    registry = AgentRegistry(registry_config, seed=42)
    tape_ids = list(range(5))
    registry.assign_roles(tape_ids)
    
    engine = EconomicEngine(registry, economic_config, trait_config)
    
    # Process tick
    result = engine.process_tick(tick_num=1)
    
    # Convert to dict
    result_dict = result.to_dict()
    
    assert result_dict["tick"] == 1
    assert "metrics" in result_dict
    assert "agents" in result_dict
    assert isinstance(result_dict["agents"], list)


if __name__ == "__main__":
    # Run all tests
    print("Running economic engine tests...")
    
    tests = [
        ("test_economic_engine_initialization", test_economic_engine_initialization),
        ("test_process_tick_basic", test_process_tick_basic),
        ("test_soup_drip", test_soup_drip),
        ("test_soup_drip_odd_tick", test_soup_drip_odd_tick),
        ("test_soup_drip_below_threshold", test_soup_drip_below_threshold),
        ("test_soup_drip_disabled", test_soup_drip_disabled),
        ("test_soup_drip_multiple_agents", test_soup_drip_multiple_agents),
        ("test_execute_trades", test_execute_trades),
        ("test_pay_retainers", test_pay_retainers),
        ("test_compute_metrics", test_compute_metrics),
        ("test_snapshot_agents", test_snapshot_agents),
        ("test_tick_result_serialization", test_tick_result_serialization),
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
            failed += 1
    
    print(f"\n{passed} tests passed, {failed} tests failed")
