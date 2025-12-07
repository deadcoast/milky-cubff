"""Unit tests for core data models."""

from core.models import Agent, WealthTraits, Role, Event, EventType, TickMetrics, TickResult, AgentSnapshot
from core.schemas import validate_agent, validate_event, validate_tick_result, validate_config
from core.config import ConfigLoader, MIncConfig


def test_wealth_traits_creation():
    """Test WealthTraits creation and validation."""
    wealth = WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    assert wealth.total() == 76
    assert wealth.compute == 10
    assert wealth.copy == 15


def test_wealth_traits_non_negative():
    """Test that WealthTraits enforces non-negative values."""
    try:
        WealthTraits(compute=-5, copy=10, defend=20, raid=5, trade=12, sense=8, adapt=6)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_wealth_traits_scale():
    """Test WealthTraits scaling."""
    wealth = WealthTraits(compute=10, copy=20, defend=30, raid=40, trade=50, sense=60, adapt=70)
    wealth.scale(0.5)
    assert wealth.compute == 5
    assert wealth.copy == 10
    assert wealth.defend == 15


def test_wealth_traits_add():
    """Test WealthTraits add method."""
    wealth = WealthTraits(compute=10, copy=20, defend=30, raid=40, trade=50, sense=60, adapt=70)
    wealth.add("compute", 5)
    assert wealth.compute == 15
    
    # Test clamping to zero
    wealth.add("compute", -100)
    assert wealth.compute == 0


def test_agent_creation():
    """Test Agent creation and validation."""
    wealth = WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    agent = Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=wealth,
        bribe_threshold=350
    )
    assert agent.id == "K-01"
    assert agent.role == Role.KING
    assert agent.currency == 5000
    assert agent.wealth_total() == 76


def test_agent_non_negative_currency():
    """Test that Agent enforces non-negative currency."""
    wealth = WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    try:
        Agent(
            id="K-01",
            tape_id=0,
            role=Role.KING,
            currency=-100,
            wealth=wealth
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_agent_add_currency():
    """Test Agent add_currency method."""
    wealth = WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    agent = Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=wealth
    )
    
    agent.add_currency(100)
    assert agent.currency == 5100
    
    # Test clamping to zero
    agent.add_currency(-10000)
    assert agent.currency == 0


def test_event_creation():
    """Test Event creation."""
    event = Event(
        tick=1,
        type=EventType.BRIBE_ACCEPT,
        king="K-01",
        merc="M-12",
        amount=350,
        notes="success"
    )
    assert event.tick == 1
    assert event.type == EventType.BRIBE_ACCEPT
    assert event.king == "K-01"
    assert event.merc == "M-12"
    assert event.amount == 350


def test_tick_metrics_creation():
    """Test TickMetrics creation."""
    metrics = TickMetrics(
        entropy=5.91,
        compression_ratio=2.70,
        copy_score_mean=0.64,
        wealth_total=399,
        currency_total=12187,
        bribes_paid=1,
        bribes_accepted=0,
        raids_attempted=2
    )
    assert metrics.entropy == 5.91
    assert metrics.wealth_total == 399
    assert metrics.bribes_paid == 1


def test_agent_to_dict_from_dict():
    """Test Agent serialization."""
    wealth = WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    agent = Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=wealth,
        bribe_threshold=350
    )
    
    agent_dict = agent.to_dict()
    agent_restored = Agent.from_dict(agent_dict)
    
    assert agent_restored.id == agent.id
    assert agent_restored.role == agent.role
    assert agent_restored.currency == agent.currency
    assert agent_restored.wealth.total() == agent.wealth.total()


def test_config_loader_default():
    """Test ConfigLoader default configuration."""
    config = ConfigLoader.get_default()
    assert config.version == "0.1.1"
    assert config.seed == 1337
    assert config.registry.role_ratios["king"] == 0.10
    assert config.registry.role_ratios["knight"] == 0.20
    assert config.registry.role_ratios["mercenary"] == 0.70


def test_config_hash():
    """Test configuration hash computation."""
    config = ConfigLoader.get_default()
    hash1 = config.compute_hash()
    
    # Same config should produce same hash
    config2 = ConfigLoader.get_default()
    hash2 = config2.compute_hash()
    assert hash1 == hash2
    
    # Different config should produce different hash
    config3 = ConfigLoader.get_default()
    config3.seed = 9999
    hash3 = config3.compute_hash()
    assert hash1 != hash3


def test_config_validation():
    """Test configuration validation."""
    config = ConfigLoader.get_default()
    errors = ConfigLoader.validate(config)
    assert len(errors) == 0
    
    # Test invalid config
    config.registry.role_ratios = {"king": 0.5, "knight": 0.3, "mercenary": 0.1}
    errors = ConfigLoader.validate(config)
    assert len(errors) > 0


def test_schema_validation():
    """Test Pydantic schema validation."""
    agent_data = {
        "id": "K-01",
        "tape_id": 0,
        "role": "king",
        "currency": 5000,
        "wealth": {
            "compute": 10,
            "copy": 15,
            "defend": 20,
            "raid": 5,
            "trade": 12,
            "sense": 8,
            "adapt": 6
        },
        "bribe_threshold": 350,
        "alive": True
    }
    
    # Should validate successfully
    schema = validate_agent(agent_data)
    assert schema.id == "K-01"
    assert schema.currency == 5000


def test_schema_validation_negative_currency():
    """Test that schema validation rejects negative currency."""
    agent_data = {
        "id": "K-01",
        "tape_id": 0,
        "role": "king",
        "currency": -100,  # Invalid
        "wealth": {
            "compute": 10,
            "copy": 15,
            "defend": 20,
            "raid": 5,
            "trade": 12,
            "sense": 8,
            "adapt": 6
        }
    }
    
    try:
        validate_agent(agent_data)
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected


def test_event_serialization():
    """Test Event to_dict and from_dict."""
    event = Event(
        tick=5,
        type=EventType.TRADE,
        king="K-01",
        amount=100,
        notes="trade executed"
    )
    
    event_dict = event.to_dict()
    assert event_dict["tick"] == 5
    assert event_dict["type"] == "trade"
    assert event_dict["king"] == "K-01"
    assert event_dict["amount"] == 100
    
    # Reconstruct from dict
    event_restored = Event.from_dict(event_dict)
    assert event_restored.tick == event.tick
    assert event_restored.type == event.type
    assert event_restored.king == event.king
    assert event_restored.amount == event.amount


def test_wealth_traits_boundary_values():
    """Test WealthTraits with boundary values."""
    # Test with zero values
    wealth_zero = WealthTraits(compute=0, copy=0, defend=0, raid=0, trade=0, sense=0, adapt=0)
    assert wealth_zero.total() == 0
    
    # Test with large values
    wealth_large = WealthTraits(compute=1000, copy=2000, defend=3000, raid=4000, trade=5000, sense=6000, adapt=7000)
    assert wealth_large.total() == 28000
    
    # Test scaling to zero
    wealth_large.scale(0.0)
    assert wealth_large.total() == 0


def test_agent_wealth_total_method():
    """Test Agent.wealth_total() method."""
    wealth = WealthTraits(compute=10, copy=20, defend=30, raid=40, trade=50, sense=60, adapt=70)
    agent = Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=wealth
    )
    
    assert agent.wealth_total() == 280
    
    # Modify wealth and verify
    agent.wealth.add("compute", 10)
    assert agent.wealth_total() == 290


def test_tick_result_creation():
    """Test TickResult creation and structure."""
    metrics = TickMetrics(
        entropy=5.5,
        compression_ratio=2.5,
        copy_score_mean=0.5,
        wealth_total=1000,
        currency_total=50000,
        bribes_paid=5,
        bribes_accepted=3,
        raids_attempted=10
    )
    
    agent_snapshot = AgentSnapshot(
        id="K-01",
        role="king",
        currency=5000,
        wealth={"compute": 10, "copy": 15, "defend": 20, "raid": 5, "trade": 12, "sense": 8, "adapt": 6}
    )
    
    events = [
        Event(tick=1, type=EventType.TRADE, king="K-01", amount=100)
    ]
    
    result = TickResult(
        tick_num=1,
        events=events,
        metrics=metrics,
        agent_snapshots=[agent_snapshot]
    )
    
    assert result.tick_num == 1
    assert len(result.events) == 1
    assert result.metrics.wealth_total == 1000
    assert len(result.agent_snapshots) == 1


def test_agent_snapshot_from_agent():
    """Test creating AgentSnapshot from Agent."""
    wealth = WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=12, sense=8, adapt=6)
    agent = Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=wealth
    )
    
    snapshot = AgentSnapshot.from_agent(agent)
    
    assert snapshot.id == "K-01"
    assert snapshot.role == "king"
    assert snapshot.currency == 5000
    assert snapshot.wealth["compute"] == 10


def test_role_enum():
    """Test Role enum values."""
    assert Role.KING.value == "king"
    assert Role.KNIGHT.value == "knight"
    assert Role.MERCENARY.value == "mercenary"


def test_event_type_enum():
    """Test EventType enum values."""
    assert EventType.TRADE.value == "trade"
    assert EventType.BRIBE_ACCEPT.value == "bribe_accept"
    assert EventType.DEFEND_WIN.value == "defend_win"
    assert EventType.DEFEND_LOSS.value == "defend_loss"


if __name__ == "__main__":
    # Run all tests
    tests = [
        test_wealth_traits_creation,
        test_wealth_traits_non_negative,
        test_wealth_traits_scale,
        test_wealth_traits_add,
        test_agent_creation,
        test_agent_non_negative_currency,
        test_agent_add_currency,
        test_event_creation,
        test_tick_metrics_creation,
        test_agent_to_dict_from_dict,
        test_config_loader_default,
        test_config_hash,
        test_config_validation,
        test_schema_validation,
        test_schema_validation_negative_currency,
        test_event_serialization,
        test_wealth_traits_boundary_values,
        test_agent_wealth_total_method,
        test_tick_result_creation,
        test_agent_snapshot_from_agent,
        test_role_enum,
        test_event_type_enum,
    ]
    
    print("Running core models tests...")
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✓ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
