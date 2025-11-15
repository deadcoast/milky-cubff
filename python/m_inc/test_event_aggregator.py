"""Tests for EventAggregator."""

from core.event_aggregator import EventAggregator, TickSummary
from core.models import Event, EventType, Agent, Role, WealthTraits


def test_add_event():
    """Test adding events to aggregator."""
    aggregator = EventAggregator()
    
    event = Event(
        tick=1,
        type=EventType.TRADE,
        king="K-01",
        invest=100,
        wealth_created=5
    )
    
    aggregator.add_event(event)
    
    assert len(aggregator.events) == 1
    assert aggregator.events[0] == event
    assert 1 in aggregator.tick_summaries


def test_get_tick_summary():
    """Test getting tick summary."""
    aggregator = EventAggregator()
    
    # Add multiple events for tick 1
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-01"))
    aggregator.add_event(Event(tick=1, type=EventType.RETAINER, knight="N-01", amount=25))
    aggregator.add_event(Event(tick=2, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=350))
    
    summary1 = aggregator.get_tick_summary(1)
    assert summary1 is not None
    assert summary1.tick == 1
    assert summary1.event_counts["trade"] == 1
    assert summary1.event_counts["retainer"] == 1
    
    summary2 = aggregator.get_tick_summary(2)
    assert summary2 is not None
    assert summary2.event_counts["bribe_accept"] == 1


def test_currency_flows():
    """Test currency flow tracking."""
    aggregator = EventAggregator()
    
    # Bribe: King pays merc
    aggregator.add_event(Event(
        tick=1,
        type=EventType.BRIBE_ACCEPT,
        king="K-01",
        merc="M-01",
        amount=350
    ))
    
    summary = aggregator.get_tick_summary(1)
    assert summary.currency_flows["king"] == -350
    assert summary.currency_flows["mercenary"] == 350


def test_wealth_changes():
    """Test wealth change tracking."""
    aggregator = EventAggregator()
    
    # Trade creates wealth
    aggregator.add_event(Event(
        tick=1,
        type=EventType.TRADE,
        king="K-01",
        invest=100,
        wealth_created=5
    ))
    
    summary = aggregator.get_tick_summary(1)
    assert summary.wealth_changes["king"]["defend"] == 3
    assert summary.wealth_changes["king"]["trade"] == 2


def test_compute_metrics():
    """Test metrics computation."""
    aggregator = EventAggregator()
    
    # Create test agents
    agents = [
        Agent(
            id="K-01",
            tape_id=1,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=15, defend=20, raid=5, trade=18, sense=7, adapt=9)
        ),
        Agent(
            id="N-01",
            tape_id=2,
            role=Role.KNIGHT,
            currency=200,
            wealth=WealthTraits(compute=8, copy=12, defend=18, raid=3, trade=10, sense=6, adapt=7)
        ),
        Agent(
            id="M-01",
            tape_id=3,
            role=Role.MERCENARY,
            currency=50,
            wealth=WealthTraits(compute=5, copy=8, defend=10, raid=15, trade=5, sense=8, adapt=10)
        )
    ]
    
    metrics = aggregator.compute_metrics(agents)
    
    assert metrics.wealth_total == 84 + 64 + 61  # Sum of all wealth
    assert metrics.currency_total == 5250
    assert metrics.copy_score_mean > 0
    assert metrics.entropy > 0
    assert metrics.compression_ratio > 0


def test_compute_entropy():
    """Test entropy computation."""
    aggregator = EventAggregator()
    
    # Equal wealth distribution should have high entropy
    equal_agents = [
        Agent(id=f"A-{i}", tape_id=i, role=Role.MERCENARY, currency=100,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10))
        for i in range(5)
    ]
    
    entropy_equal = aggregator._compute_entropy(equal_agents)
    
    # Unequal wealth distribution should have lower entropy
    unequal_agents = [
        Agent(id="A-0", tape_id=0, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=50, copy=50, defend=50, raid=50, trade=50, sense=50, adapt=50)),
        Agent(id="A-1", tape_id=1, role=Role.MERCENARY, currency=100,
              wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=1, sense=1, adapt=1)),
        Agent(id="A-2", tape_id=2, role=Role.MERCENARY, currency=100,
              wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=1, sense=1, adapt=1)),
    ]
    
    entropy_unequal = aggregator._compute_entropy(unequal_agents)
    
    assert entropy_equal > entropy_unequal


def test_compute_gini_coefficient():
    """Test Gini coefficient computation."""
    aggregator = EventAggregator()
    
    # Perfect equality (Gini = 0)
    equal_agents = [
        Agent(id=f"A-{i}", tape_id=i, role=Role.MERCENARY, currency=100,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10))
        for i in range(5)
    ]
    
    gini_equal = aggregator.compute_gini_coefficient(equal_agents)
    assert gini_equal < 0.1  # Close to 0
    
    # High inequality
    unequal_agents = [
        Agent(id="A-0", tape_id=0, role=Role.KING, currency=100,
              wealth=WealthTraits(compute=100, copy=100, defend=100, raid=100, trade=100, sense=100, adapt=100)),
        Agent(id="A-1", tape_id=1, role=Role.MERCENARY, currency=100,
              wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=1, sense=1, adapt=1)),
        Agent(id="A-2", tape_id=2, role=Role.MERCENARY, currency=100,
              wealth=WealthTraits(compute=1, copy=1, defend=1, raid=1, trade=1, sense=1, adapt=1)),
    ]
    
    gini_unequal = aggregator.compute_gini_coefficient(unequal_agents)
    assert gini_unequal > 0.3  # Higher inequality


def test_get_wealth_distribution_by_role():
    """Test wealth distribution by role."""
    aggregator = EventAggregator()
    
    agents = [
        Agent(id="K-01", tape_id=1, role=Role.KING, currency=5000,
              wealth=WealthTraits(compute=20, copy=20, defend=20, raid=20, trade=20, sense=20, adapt=20)),
        Agent(id="K-02", tape_id=2, role=Role.KING, currency=6000,
              wealth=WealthTraits(compute=30, copy=30, defend=30, raid=30, trade=30, sense=30, adapt=30)),
        Agent(id="N-01", tape_id=3, role=Role.KNIGHT, currency=200,
              wealth=WealthTraits(compute=10, copy=10, defend=10, raid=10, trade=10, sense=10, adapt=10)),
    ]
    
    distribution = aggregator.get_wealth_distribution_by_role(agents)
    
    assert "king" in distribution
    assert "knight" in distribution
    assert "mercenary" in distribution
    
    assert distribution["king"]["total"] == 140 + 210  # Sum of king wealth
    assert distribution["knight"]["total"] == 70


def test_get_events_by_type():
    """Test filtering events by type."""
    aggregator = EventAggregator()
    
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-01"))
    aggregator.add_event(Event(tick=1, type=EventType.TRADE, king="K-02"))
    aggregator.add_event(Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01"))
    
    trade_events = aggregator.get_events_by_type(EventType.TRADE)
    assert len(trade_events) == 2
    
    bribe_events = aggregator.get_events_by_type(EventType.BRIBE_ACCEPT)
    assert len(bribe_events) == 1


if __name__ == "__main__":
    print("Running EventAggregator tests...")
    
    test_add_event()
    print("✓ test_add_event")
    
    test_get_tick_summary()
    print("✓ test_get_tick_summary")
    
    test_currency_flows()
    print("✓ test_currency_flows")
    
    test_wealth_changes()
    print("✓ test_wealth_changes")
    
    test_compute_metrics()
    print("✓ test_compute_metrics")
    
    test_compute_entropy()
    print("✓ test_compute_entropy")
    
    test_compute_gini_coefficient()
    print("✓ test_compute_gini_coefficient")
    
    test_get_wealth_distribution_by_role()
    print("✓ test_get_wealth_distribution_by_role")
    
    test_get_events_by_type()
    print("✓ test_get_events_by_type")
    
    print("\nAll tests passed!")
