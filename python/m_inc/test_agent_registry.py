"""Tests for agent registry functionality."""

import pytest
from core.agent_registry import AgentRegistry
from core.models import Role, Agent, WealthTraits
from core.config import RegistryConfig


def test_agent_registry_initialization():
    """Test that AgentRegistry initializes correctly."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    assert registry.config == config
    assert len(registry.agents) == 0
    assert registry.rng is not None


def test_assign_roles_with_ratios():
    """Test role assignment based on configured ratios."""
    config = RegistryConfig(
        role_ratios={"king": 0.10, "knight": 0.20, "mercenary": 0.70}
    )
    registry = AgentRegistry(config, seed=42)
    
    # Create 100 tape IDs
    tape_ids = list(range(100))
    registry.assign_roles(tape_ids)
    
    # Check total agents
    assert len(registry.agents) == 100
    
    # Check role distribution
    kings = registry.get_agents_by_role(Role.KING)
    knights = registry.get_agents_by_role(Role.KNIGHT)
    mercs = registry.get_agents_by_role(Role.MERCENARY)
    
    assert len(kings) == 10
    assert len(knights) == 20
    assert len(mercs) == 70


def test_agent_initialization_currency():
    """Test that agents are initialized with correct currency ranges."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(30))
    registry.assign_roles(tape_ids)
    
    # Check kings have currency in range 5000-7000
    for king in registry.get_kings():
        assert 5000 <= king.currency <= 7000
    
    # Check knights have currency in range 100-300
    for knight in registry.get_knights():
        assert 100 <= knight.currency <= 300
    
    # Check mercenaries have currency in range 0-50
    for merc in registry.get_mercenaries():
        assert 0 <= merc.currency <= 50


def test_agent_initialization_wealth_traits():
    """Test that agents are initialized with wealth traits."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    for agent in registry.get_all_agents():
        # Check all traits are non-negative
        assert agent.wealth.compute >= 0
        assert agent.wealth.copy >= 0
        assert agent.wealth.defend >= 0
        assert agent.wealth.raid >= 0
        assert agent.wealth.trade >= 0
        assert agent.wealth.sense >= 0
        assert agent.wealth.adapt >= 0


def test_king_bribe_threshold_initialization():
    """Test that kings are initialized with bribe thresholds."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    for king in registry.get_kings():
        assert 300 <= king.bribe_threshold <= 500


def test_knight_retainer_fee_initialization():
    """Test that knights are initialized with retainer fees."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(20))
    registry.assign_roles(tape_ids)
    
    for knight in registry.get_knights():
        assert 20 <= knight.retainer_fee <= 30


def test_get_agent_by_id():
    """Test agent lookup by ID."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    # Get first king
    kings = registry.get_kings()
    if kings:
        king = kings[0]
        retrieved = registry.get_agent(king.id)
        assert retrieved is not None
        assert retrieved.id == king.id


def test_get_agent_by_tape():
    """Test agent lookup by tape ID."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    # Get agent by tape ID
    agent = registry.get_agent_by_tape(tape_ids[0])
    assert agent is not None
    assert agent.tape_id == tape_ids[0]


def test_get_agents_by_role():
    """Test filtering agents by role."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(30))
    registry.assign_roles(tape_ids)
    
    kings = registry.get_agents_by_role(Role.KING)
    knights = registry.get_agents_by_role(Role.KNIGHT)
    mercs = registry.get_agents_by_role(Role.MERCENARY)
    
    # Check all returned agents have correct role
    for king in kings:
        assert king.role == Role.KING
    
    for knight in knights:
        assert knight.role == Role.KNIGHT
    
    for merc in mercs:
        assert merc.role == Role.MERCENARY


def test_update_agent():
    """Test updating agent state."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(10))
    registry.assign_roles(tape_ids)
    
    # Get an agent and modify it
    agent = registry.get_all_agents()[0]
    original_currency = agent.currency
    agent.currency = original_currency + 100
    
    # Update in registry
    registry.update_agent(agent)
    
    # Retrieve and verify
    updated = registry.get_agent(agent.id)
    assert updated.currency == original_currency + 100


def test_assign_knight_employers():
    """Test assigning knights to king employers."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(30))
    registry.assign_roles(tape_ids)
    
    # Assign employers
    registry.assign_knight_employers()
    
    kings = registry.get_kings()
    knights = registry.get_knights()
    
    # Check that knights have employers
    employed_knights = [k for k in knights if k.employer is not None]
    assert len(employed_knights) > 0
    
    # Check that employers are valid king IDs
    king_ids = {k.id for k in kings}
    for knight in employed_knights:
        assert knight.employer in king_ids


def test_get_employed_knights():
    """Test getting knights employed by a specific king."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(30))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    kings = registry.get_kings()
    if kings:
        king = kings[0]
        employed = registry.get_employed_knights(king.id)
        
        # All returned knights should have this king as employer
        for knight in employed:
            assert knight.employer == king.id


def test_get_free_knights():
    """Test getting knights without employers."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(30))
    registry.assign_roles(tape_ids)
    
    # Before assignment, all knights should be free
    free_knights = registry.get_free_knights()
    all_knights = registry.get_knights()
    assert len(free_knights) == len(all_knights)
    
    # After assignment, some may still be free
    registry.assign_knight_employers()
    free_knights_after = registry.get_free_knights()
    
    for knight in free_knights_after:
        assert knight.employer is None


def test_role_mutation():
    """Test role mutation functionality."""
    config = RegistryConfig(mutation_rate=0.5)
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(20))
    registry.assign_roles(tape_ids)
    
    # Store original roles
    original_roles = {agent.id: agent.role for agent in registry.get_all_agents()}
    
    # Mutate roles
    mutations = registry.mutate_roles()
    
    # Check that some mutations occurred (with 50% rate and 20 agents, expect some)
    assert len(mutations) > 0
    
    # Check mutation format
    for agent_id, old_role, new_role in mutations:
        assert old_role != new_role
        assert original_roles[agent_id] == old_role
        
        # Check agent was actually updated
        agent = registry.get_agent(agent_id)
        assert agent.role == new_role


def test_role_mutation_updates_attributes():
    """Test that role mutation updates role-specific attributes."""
    config = RegistryConfig(mutation_rate=1.0)  # Force all to mutate
    registry = AgentRegistry(config, seed=42)
    
    # Create a single king
    tape_ids = [0]
    registry.assign_roles(tape_ids)
    
    agent = registry.get_all_agents()[0]
    
    # Force mutation by calling multiple times until role changes
    for _ in range(10):
        mutations = registry.mutate_roles(mutation_rate=1.0)
        if mutations:
            break
    
    # Check that attributes were updated based on new role
    if agent.role == Role.KNIGHT:
        assert agent.retainer_fee > 0
        assert agent.bribe_threshold == 0
    elif agent.role == Role.KING:
        assert agent.bribe_threshold > 0
        assert agent.employer is None
    elif agent.role == Role.MERCENARY:
        assert agent.employer is None
        assert agent.retainer_fee == 0
        assert agent.bribe_threshold == 0


def test_get_stats():
    """Test registry statistics."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(100))
    registry.assign_roles(tape_ids)
    
    stats = registry.get_stats()
    
    assert stats["total_agents"] == 100
    assert stats["kings"] == 10
    assert stats["knights"] == 20
    assert stats["mercenaries"] == 70
    assert stats["total_currency"] > 0
    assert stats["total_wealth"] > 0
    assert stats["avg_currency"] > 0
    assert stats["avg_wealth"] > 0


def test_to_dict_and_from_dict():
    """Test serialization and deserialization."""
    config = RegistryConfig()
    registry = AgentRegistry(config, seed=42)
    
    tape_ids = list(range(20))
    registry.assign_roles(tape_ids)
    
    # Serialize
    data = registry.to_dict()
    
    assert "agents" in data
    assert "stats" in data
    assert len(data["agents"]) == 20
    
    # Create new registry and deserialize
    registry2 = AgentRegistry(config, seed=42)
    registry2.from_dict(data)
    
    # Check agents match
    assert len(registry2.agents) == len(registry.agents)
    
    for agent_id in registry.agents:
        agent1 = registry.get_agent(agent_id)
        agent2 = registry2.get_agent(agent_id)
        assert agent1.id == agent2.id
        assert agent1.role == agent2.role
        assert agent1.currency == agent2.currency


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
