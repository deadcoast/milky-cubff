"""Tests for event aggregator."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.event_aggregator import EventAggregator
from core.models import Event, EventType, Agent, Role, WealthTraits


def test_event_aggregator_initialization():
    """Test that EventAggregator can be initialized."""
    aggregator = EventAggregator()
    
    assert aggregator.events == []
    assert aggregator.agents is None


def test_add_event():
    """Test adding events to the aggregator."""
    aggregator = EventAggregator()
    
    event1 = Event(tick=1, type=EventType.TRADE, king="K-01", invest=100)
    event2 = Event(tick=1, type=EventType.RETAINER, king="K-01", knight="N-01", amount=50)
    
    aggregator.add_event(event1)
    aggregator.add_event(event2)
    
    assert len(aggregator.events) == 2
    assert aggregator.events[0] == event1
    assert aggregator.events[1] == event2


def test_get_tick_summary():
    """Test generating tick summary."""
    aggregator = EventAggregator()
    
    # Add events for tick 1
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-01", invest=100))
    aggregator.add_event(Event(tick=1, type=EventType.RETAINER, king="K-01", knight="N-01", amount=50))
    aggregator.add_event(Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=200))
    
    # Add events for tick 2
    aggregator.add_event(Event(tick=2, type=EventType.TRADE, king="K-02", invest=100))
    
    # Get summary for tick 1
    summary = aggregator.get_tick_summary(tick_num=1)
    
    assert summary["tick"] == 1
    assert "event_counts" in summary
    assert "currency_flows" in summary
    assert "wealth_changes" in summary
    
    # Check event counts
    assert summary["event_counts"]["trade"] == 1
    assert summary["event_counts"]["retainer"] == 1
    assert summary["event_counts"]["bribe_accept"] == 1


def test_compute_event_counts():
    """Test event count computation."""
    aggregator = EventAggregator()
    
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-01"))
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-02"))
    aggregator.add_event(Event(tick=1, type=EventType.RETAINER, king="K-01", knight="N-01"))
    aggregator.add_event(Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01"))
    
    summary = aggregator.get_tick_summary(tick_num=1)
    counts = summary["event_counts"]
    
    assert counts["trade"] == 2
    assert counts["retainer"] == 1
    assert counts["bribe_accept"] == 1


def test_compute_currency_flows():
    """Test currency flow computation."""
    aggregator = EventAggregator()
    
    # Bribe: king loses 200, merc gains 200
    aggregator.add_event(Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=200))
    
    # Trade: king loses 100
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-01", invest=100))
    
    # Retainer: king loses 50, knight gains 50
    aggregator.add_event(Event(tick=1, type=EventType.RETAINER, king="K-01", knight="N-01", amount=50))
    
    # Defend win: merc loses 30, knight gains 30
    aggregator.add_event(Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-01", stake=30))
    
    summary = aggregator.get_tick_summary(tick_num=1)
    flows = summary["currency_flows"]
    
    # King: lost 200 (bribe) + 100 (trade) + 50 (retainer) = 350
    assert flows["king"]["lost"] == 350
    assert flows["king"]["gained"] == 0
    
    # Knight: gained 50 (retainer) + 30 (defend win) = 80
    assert flows["knight"]["gained"] == 80
    assert flows["knight"]["lost"] == 0
    
    # Mercenary: gained 200 (bribe), lost 30 (defend loss)
    assert flows["mercenary"]["gained"] == 200
    assert flows["mercenary"]["lost"] == 30


def test_compute_wealth_changes():
    """Test wealth change computation."""
    aggregator = EventAggregator()
    
    # Trade creates wealth: +3 defend, +2 trade
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-01", invest=100, wealth_created=5))
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-02", invest=100, wealth_created=5))
    
    summary = aggregator.get_tick_summary(tick_num=1)
    changes = summary["wealth_changes"]
    
    # Kings should have gained wealth from trades
    assert changes["king"]["defend"] == 6  # 2 trades * 3 defend each
    assert changes["king"]["trade"] == 4   # 2 trades * 2 trade each


def test_compute_metrics():
    """Test metrics computation."""
    aggregator = EventAggregator()
    
    # Create test agents
    agents = [
        Agent(id="K-01", tape_id=0, role=Role.KING, currency=1000, 
              wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=10, sense=8, adapt=7)),
        Agent(id="N-01", tape_id=1, role=Role.KNIGHT, currency=500,
              wealth=WealthTraits(compute=8, copy=12, defend=18, raid=3, trade=6, sense=5, adapt=4)),
        Agent(id="M-01", tape_id=2, role=Role.MERCENARY, currency=100,
              wealth=WealthTraits(compute=5, copy=8, defend=10, raid=15, trade=3, sense=6, adapt=8)),
    ]
    
    # Add some events
    aggregator.add_event(Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01"))
    aggregator.add_event(Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-01"))
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-01"))
    
    metrics = aggregator.compute_metrics(agents)
    
    # Check basic metrics
    assert metrics.wealth_total == sum(a.wealth_total() for a in agents)
    assert metrics.currency_total == sum(a.currency for a in agents)
    assert metrics.copy_score_mean > 0
    
    # Check event counts
    assert metrics.bribes_accepted == 1
    assert metrics.raids_won_by_knight == 1


def test_compute_metrics_event_counts():
    """Test that metrics correctly count different event types."""
    aggregator = EventAggregator()
    
    agents = [
        Agent(id="K-01", tape_id=0, role=Role.KING, currency=1000, 
              wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=10, sense=8, adapt=7)),
    ]
    
    # Add various events
    aggregator.add_event(Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01"))
    aggregator.add_event(Event(tick=1, type=EventType.BRIBE_INSUFFICIENT, king="K-01", merc="M-02"))
    aggregator.add_event(Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-03"))
    aggregator.add_event(Event(tick=1, type=EventType.DEFEND_LOSS, king="K-01", knight="N-01", merc="M-04"))
    aggregator.add_event(Event(tick=1, type=EventType.UNOPPOSED_RAID, king="K-01", merc="M-05"))
    
    metrics = aggregator.compute_metrics(agents)
    
    # Bribes paid = bribe_accept + bribe_insufficient
    assert metrics.bribes_paid == 2
    assert metrics.bribes_accepted == 1
    
    # Raids attempted = defend_win + defend_loss + unopposed_raid
    assert metrics.raids_attempted == 3
    assert metrics.raids_won_by_knight == 1
    assert metrics.raids_won_by_merc == 2  # defend_loss + unopposed_raid


def test_compute_gini_coefficient():
    """Test Gini coefficient computation."""
    aggregator = EventAggregator()
    
    # Perfect equality: all agents have same wealth
    equal_agents = [
        Agent(id="A-01", tape_id=0, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10)),
        Agent(id="A-02", tape_id=1, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10)),
        Agent(id="A-03", tape_id=2, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10)),
    ]
    
    gini_equal = aggregator.compute_gini_coefficient(equal_agents)
    assert gini_equal < 0.1, f"Expected Gini near 0 for equal distribution, got {gini_equal}"
    
    # High inequality: one agent has most wealth
    unequal_agents = [
        Agent(id="A-01", tape_id=0, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=1, sense=1, adapt=1)),
        Agent(id="A-02", tape_id=1, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=1, sense=1, adapt=1)),
        Agent(id="A-03", tape_id=2, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=100, copy=100, defend=100, raid=100, trade=100, sense=100, adapt=100)),
    ]
    
    gini_unequal = aggregator.compute_gini_coefficient(unequal_agents)
    assert gini_unequal > 0.5, f"Expected high Gini for unequal distribution, got {gini_unequal}"


def test_compute_gini_coefficient_edge_cases():
    """Test Gini coefficient edge cases."""
    aggregator = EventAggregator()
    
    # Empty list
    gini_empty = aggregator.compute_gini_coefficient([])
    assert gini_empty == 0.0
    
    # Single agent
    single_agent = [
        Agent(id="A-01", tape_id=0, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10)),
    ]
    gini_single = aggregator.compute_gini_coefficient(single_agent)
    assert gini_single == 0.0
    
    # All zero wealth
    zero_agents = [
        Agent(id="A-01", tape_id=0, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=0, copy=0, defend=0, raid=0, trade=0, sense=0, adapt=0)),
        Agent(id="A-02", tape_id=1, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=0, copy=0, defend=0, raid=0, trade=0, sense=0, adapt=0)),
    ]
    gini_zero = aggregator.compute_gini_coefficient(zero_agents)
    assert gini_zero == 0.0


def test_compute_wealth_entropy():
    """Test wealth entropy computation."""
    aggregator = EventAggregator()
    
    # Equal distribution should have high entropy
    equal_agents = [
        Agent(id="A-01", tape_id=0, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10)),
        Agent(id="A-02", tape_id=1, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10)),
        Agent(id="A-03", tape_id=2, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10)),
    ]
    
    entropy_equal = aggregator._compute_wealth_entropy(equal_agents)
    assert entropy_equal > 0, f"Expected positive entropy, got {entropy_equal}"
    
    # Unequal distribution should have lower entropy
    unequal_agents = [
        Agent(id="A-01", tape_id=0, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=1, sense=1, adapt=1)),
        Agent(id="A-02", tape_id=1, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=1, sense=1, adapt=1)),
        Agent(id="A-03", tape_id=2, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=100, copy=100, defend=100, raid=100, trade=100, sense=100, adapt=100)),
    ]
    
    entropy_unequal = aggregator._compute_wealth_entropy(unequal_agents)
    assert entropy_unequal > 0
    assert entropy_unequal < entropy_equal, "Unequal distribution should have lower entropy"


def test_compute_wealth_entropy_edge_cases():
    """Test wealth entropy edge cases."""
    aggregator = EventAggregator()
    
    # Empty list
    entropy_empty = aggregator._compute_wealth_entropy([])
    assert entropy_empty == 0.0
    
    # All zero wealth
    zero_agents = [
        Agent(id="A-01", tape_id=0, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=0, copy=0, defend=0, raid=0, trade=0, sense=0, adapt=0)),
    ]
    entropy_zero = aggregator._compute_wealth_entropy(zero_agents)
    assert entropy_zero == 0.0


def test_clear():
    """Test clearing accumulated events."""
    aggregator = EventAggregator()
    
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-01"))
    aggregator.add_event(Event(tick=1, type=EventType.RETAINER, king="K-01", knight="N-01"))
    
    assert len(aggregator.events) == 2
    
    aggregator.clear()
    
    assert len(aggregator.events) == 0


def test_set_agents():
    """Test setting agent list."""
    aggregator = EventAggregator()
    
    agents = [
        Agent(id="K-01", tape_id=0, role=Role.KING, currency=1000,
              wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=10, sense=8, adapt=7)),
    ]
    
    aggregator.set_agents(agents)
    
    assert aggregator.agents == agents


if __name__ == "__main__":
    # Run all tests
    print("Running event aggregator tests...")
    
    tests = [
        ("test_event_aggregator_initialization", test_event_aggregator_initialization),
        ("test_add_event", test_add_event),
        ("test_get_tick_summary", test_get_tick_summary),
        ("test_compute_event_counts", test_compute_event_counts),
        ("test_compute_currency_flows", test_compute_currency_flows),
        ("test_compute_wealth_changes", test_compute_wealth_changes),
        ("test_compute_metrics", test_compute_metrics),
        ("test_compute_metrics_event_counts", test_compute_metrics_event_counts),
        ("test_compute_gini_coefficient", test_compute_gini_coefficient),
        ("test_compute_gini_coefficient_edge_cases", test_compute_gini_coefficient_edge_cases),
        ("test_compute_wealth_entropy", test_compute_wealth_entropy),
        ("test_compute_wealth_entropy_edge_cases", test_compute_wealth_entropy_edge_cases),
        ("test_clear", test_clear),
        ("test_set_agents", test_set_agents),
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
