"""Unit test for soup drip functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from m_inc.core.models import Agent, Role, WealthTraits, EventType
from m_inc.core.agent_registry import AgentRegistry
from m_inc.core.economic_engine import EconomicEngine
from m_inc.core.config import ConfigLoader


def test_soup_drip_basic():
    """Test that soup drip applies +1 copy when copy >= 12 and tick % 2 == 0."""
    print("\n" + "=" * 60)
    print("Test: Soup Drip Basic Functionality")
    print("=" * 60)
    
    # Load config
    config_path = Path(__file__).parent / "config" / "minc_default.yaml"
    config = ConfigLoader.load(config_path)
    
    # Create registry
    registry = AgentRegistry(config.registry, seed=1337)
    
    # Manually create agents with high copy values
    agent1 = Agent(
        id="M-00",
        tape_id=0,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(compute=5, copy=12, defend=3, raid=4, trade=2, sense=3, adapt=2)
    )
    
    agent2 = Agent(
        id="M-01",
        tape_id=1,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(compute=5, copy=15, defend=3, raid=4, trade=2, sense=3, adapt=2)
    )
    
    agent3 = Agent(
        id="M-02",
        tape_id=2,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(compute=5, copy=11, defend=3, raid=4, trade=2, sense=3, adapt=2)
    )
    
    # Add agents to registry
    registry.agents = {
        "M-00": agent1,
        "M-01": agent2,
        "M-02": agent3,
    }
    
    print(f"\nInitial state:")
    print(f"  M-00: copy={agent1.wealth.copy}")
    print(f"  M-01: copy={agent2.wealth.copy}")
    print(f"  M-02: copy={agent3.wealth.copy} (below threshold)")
    
    # Create engine
    engine = EconomicEngine(registry, config.economic)
    
    # Process tick 1 (odd tick, no drip should occur)
    print(f"\nProcessing tick 1 (odd tick)...")
    result1 = engine.process_tick(1)
    drip_events1 = [e for e in result1.events if e.type == EventType.TRAIT_DRIP]
    print(f"  Trait drip events: {len(drip_events1)}")
    assert len(drip_events1) == 0, "No drip should occur on odd ticks"
    
    # Check copy values unchanged
    agent1_after_tick1 = registry.get_agent("M-00")
    agent2_after_tick1 = registry.get_agent("M-01")
    agent3_after_tick1 = registry.get_agent("M-02")
    print(f"  M-00: copy={agent1_after_tick1.wealth.copy} (unchanged)")
    print(f"  M-01: copy={agent2_after_tick1.wealth.copy} (unchanged)")
    print(f"  M-02: copy={agent3_after_tick1.wealth.copy} (unchanged)")
    
    # Process tick 2 (even tick, drip should occur for agents with copy >= 12)
    print(f"\nProcessing tick 2 (even tick)...")
    result2 = engine.process_tick(2)
    drip_events2 = [e for e in result2.events if e.type == EventType.TRAIT_DRIP]
    print(f"  Trait drip events: {len(drip_events2)}")
    
    # Should have 2 drip events (M-00 and M-01, but not M-02)
    assert len(drip_events2) == 2, f"Expected 2 drip events, got {len(drip_events2)}"
    
    # Check the events
    for event in drip_events2:
        print(f"  Event: agent={event.agent}, trait={event.trait}, delta={event.delta}")
        assert event.trait == "copy", f"Expected trait='copy', got '{event.trait}'"
        assert event.delta == 1, f"Expected delta=1, got {event.delta}"
        assert event.agent in ["M-00", "M-01"], f"Unexpected agent: {event.agent}"
    
    # Check copy values increased
    agent1_after_tick2 = registry.get_agent("M-00")
    agent2_after_tick2 = registry.get_agent("M-01")
    agent3_after_tick2 = registry.get_agent("M-02")
    print(f"  M-00: copy={agent1_after_tick2.wealth.copy} (+1)")
    print(f"  M-01: copy={agent2_after_tick2.wealth.copy} (+1)")
    print(f"  M-02: copy={agent3_after_tick2.wealth.copy} (unchanged, below threshold)")
    
    assert agent1_after_tick2.wealth.copy == 13, f"Expected M-00 copy=13, got {agent1_after_tick2.wealth.copy}"
    assert agent2_after_tick2.wealth.copy == 16, f"Expected M-01 copy=16, got {agent2_after_tick2.wealth.copy}"
    assert agent3_after_tick2.wealth.copy == 11, f"Expected M-02 copy=11, got {agent3_after_tick2.wealth.copy}"
    
    # Process tick 3 (odd tick, no drip)
    print(f"\nProcessing tick 3 (odd tick)...")
    result3 = engine.process_tick(3)
    drip_events3 = [e for e in result3.events if e.type == EventType.TRAIT_DRIP]
    print(f"  Trait drip events: {len(drip_events3)}")
    assert len(drip_events3) == 0, "No drip should occur on odd ticks"
    
    # Process tick 4 (even tick, drip should occur again)
    print(f"\nProcessing tick 4 (even tick)...")
    result4 = engine.process_tick(4)
    drip_events4 = [e for e in result4.events if e.type == EventType.TRAIT_DRIP]
    print(f"  Trait drip events: {len(drip_events4)}")
    assert len(drip_events4) == 2, f"Expected 2 drip events, got {len(drip_events4)}"
    
    # Check final copy values
    agent1_final = registry.get_agent("M-00")
    agent2_final = registry.get_agent("M-01")
    agent3_final = registry.get_agent("M-02")
    print(f"  M-00: copy={agent1_final.wealth.copy} (13 -> 14)")
    print(f"  M-01: copy={agent2_final.wealth.copy} (16 -> 17)")
    print(f"  M-02: copy={agent3_final.wealth.copy} (still below threshold)")
    
    assert agent1_final.wealth.copy == 14, f"Expected M-00 copy=14, got {agent1_final.wealth.copy}"
    assert agent2_final.wealth.copy == 17, f"Expected M-01 copy=17, got {agent2_final.wealth.copy}"
    assert agent3_final.wealth.copy == 11, f"Expected M-02 copy=11, got {agent3_final.wealth.copy}"
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)


def test_soup_drip_threshold_boundary():
    """Test that soup drip only applies when copy >= 12 (not copy > 12)."""
    print("\n" + "=" * 60)
    print("Test: Soup Drip Threshold Boundary")
    print("=" * 60)
    
    # Load config
    config_path = Path(__file__).parent / "config" / "minc_default.yaml"
    config = ConfigLoader.load(config_path)
    
    # Create registry
    registry = AgentRegistry(config.registry, seed=1337)
    
    # Create agents at boundary values
    agent_at_threshold = Agent(
        id="M-00",
        tape_id=0,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(compute=5, copy=12, defend=3, raid=4, trade=2, sense=3, adapt=2)
    )
    
    agent_below_threshold = Agent(
        id="M-01",
        tape_id=1,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(compute=5, copy=11, defend=3, raid=4, trade=2, sense=3, adapt=2)
    )
    
    registry.agents = {
        "M-00": agent_at_threshold,
        "M-01": agent_below_threshold,
    }
    
    print(f"\nInitial state:")
    print(f"  M-00: copy=12 (at threshold)")
    print(f"  M-01: copy=11 (below threshold)")
    
    # Create engine
    engine = EconomicEngine(registry, config.economic)
    
    # Process tick 2 (even tick)
    print(f"\nProcessing tick 2 (even tick)...")
    result = engine.process_tick(2)
    drip_events = [e for e in result.events if e.type == EventType.TRAIT_DRIP]
    print(f"  Trait drip events: {len(drip_events)}")
    
    # Should have exactly 1 drip event (only M-00)
    assert len(drip_events) == 1, f"Expected 1 drip event, got {len(drip_events)}"
    assert drip_events[0].agent == "M-00", f"Expected agent M-00, got {drip_events[0].agent}"
    
    # Check final values
    agent_at_threshold_after = registry.get_agent("M-00")
    agent_below_threshold_after = registry.get_agent("M-01")
    print(f"  M-00: copy={agent_at_threshold_after.wealth.copy} (12 -> 13)")
    print(f"  M-01: copy={agent_below_threshold_after.wealth.copy} (unchanged)")
    
    assert agent_at_threshold_after.wealth.copy == 13
    assert agent_below_threshold_after.wealth.copy == 11
    
    print("\n" + "=" * 60)
    print("✓ Boundary test passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_soup_drip_basic()
    test_soup_drip_threshold_boundary()
    print("\n✓ All soup drip tests passed!")
