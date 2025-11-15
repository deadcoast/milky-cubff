"""Tests for signal processing with refractory periods."""

import pytest
from core.signals import SignalProcessor, SignalConfig, Channel
from core.models import Event, EventType
from core.config import RefractoryConfig


def test_signal_processor_initialization():
    """Test that SignalProcessor initializes correctly."""
    config = SignalConfig()
    processor = SignalProcessor(config)
    
    assert processor.config == config
    assert processor._current_tick == 0
    assert len(processor._refractory_state) == 0


def test_process_events_routes_to_channels():
    """Test that events are routed to appropriate channels."""
    config = SignalConfig()
    processor = SignalProcessor(config)
    
    events = [
        Event(tick=1, type=EventType.TRADE, king="K-01", amount=100),
        Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=500),
        Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-02"),
    ]
    
    signals = processor.process_events(events)
    
    assert len(signals) == 3
    assert signals[0].channel in [Channel.TRADE, Channel.BRIBE, Channel.DEFEND]


def test_refractory_period_blocks_events():
    """Test that refractory periods block immediate re-triggering."""
    refractory = RefractoryConfig(raid=2, defend=1, bribe=1, trade=0)
    config = SignalConfig(refractory=refractory, enable_queuing=True)
    processor = SignalProcessor(config)
    
    # First event should go through
    event1 = Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01")
    signals1 = processor.process_events([event1])
    
    assert len(signals1) == 1
    assert not processor.is_channel_active(Channel.BRIBE)
    
    # Second event should be queued
    event2 = Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-02")
    signals2 = processor.process_events([event2])
    
    assert len(signals2) == 0  # Queued, not processed
    assert processor.get_queue_status()["bribe"] == 1


def test_update_refractory_clears_expired():
    """Test that update_refractory clears expired periods."""
    refractory = RefractoryConfig(bribe=2)
    config = SignalConfig(refractory=refractory)
    processor = SignalProcessor(config)
    
    # Trigger refractory at tick 1
    event = Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01")
    processor.process_events([event])
    
    assert not processor.is_channel_active(Channel.BRIBE)
    
    # Update to tick 2 (still in refractory)
    processor.update_refractory(2)
    assert not processor.is_channel_active(Channel.BRIBE)
    
    # Update to tick 3 (refractory expired)
    processor.update_refractory(3)
    assert processor.is_channel_active(Channel.BRIBE)


def test_queued_events_processed_after_refractory():
    """Test that queued events are processed when refractory expires."""
    refractory = RefractoryConfig(defend=2)
    config = SignalConfig(refractory=refractory, enable_queuing=True)
    processor = SignalProcessor(config)
    
    # First event triggers refractory
    event1 = Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-01")
    signals1 = processor.process_events([event1])
    assert len(signals1) == 1
    
    # Second event gets queued
    event2 = Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-02")
    signals2 = processor.process_events([event2])
    assert len(signals2) == 0
    assert processor.get_queue_status()["defend"] == 1
    
    # Update to tick 3 (refractory expires)
    signals3 = processor.update_refractory(3)
    assert len(signals3) == 1  # Queued event processed
    assert processor.get_queue_status()["defend"] == 0


def test_is_channel_active():
    """Test channel active status checking."""
    refractory = RefractoryConfig(raid=3)
    config = SignalConfig(refractory=refractory)
    processor = SignalProcessor(config)
    
    # Initially all channels are active
    assert processor.is_channel_active(Channel.RAID)
    
    # Trigger refractory
    event = Event(tick=1, type=EventType.UNOPPOSED_RAID, king="K-01", merc="M-01")
    processor.process_events([event])
    
    # Channel should be inactive
    assert not processor.is_channel_active(Channel.RAID)
    
    # Update to expiry tick
    processor.update_refractory(4)
    assert processor.is_channel_active(Channel.RAID)


def test_event_coalescing():
    """Test that queued events are coalesced."""
    refractory = RefractoryConfig(bribe=2)
    config = SignalConfig(refractory=refractory, enable_queuing=True, enable_coalescing=True)
    processor = SignalProcessor(config)
    
    # Trigger refractory
    event1 = Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=100)
    processor.process_events([event1])
    
    # Queue multiple similar events
    event2 = Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=200)
    event3 = Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=300)
    processor.process_events([event2, event3])
    
    assert processor.get_queue_status()["bribe"] == 2
    
    # Update refractory - should coalesce to 1 event
    signals = processor.update_refractory(3)
    assert len(signals) == 1
    assert signals[0].payload["amount"] == 300  # Most recent


def test_signal_priority_ordering():
    """Test that signals are ordered by priority."""
    config = SignalConfig()
    processor = SignalProcessor(config)
    
    events = [
        Event(tick=1, type=EventType.TRAIT_DRIP, agent="K-01"),  # Low priority
        Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-01"),  # High priority
        Event(tick=1, type=EventType.TRADE, king="K-01"),  # Medium priority
    ]
    
    signals = processor.process_events(events)
    
    # Should be sorted by priority (highest first)
    assert len(signals) == 3
    assert signals[0].priority >= signals[1].priority >= signals[2].priority


def test_get_refractory_status():
    """Test getting refractory status for all channels."""
    refractory = RefractoryConfig(raid=2, bribe=1)
    config = SignalConfig(refractory=refractory)
    processor = SignalProcessor(config)
    
    # Trigger some refractory periods
    events = [
        Event(tick=1, type=EventType.UNOPPOSED_RAID, king="K-01", merc="M-01"),
        Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-02", merc="M-02"),
    ]
    processor.process_events(events)
    
    status = processor.get_refractory_status()
    
    assert status["raid"] == 3  # tick 1 + 2
    assert status["bribe"] == 2  # tick 1 + 1
    assert status["defend"] is None  # Not triggered
    assert status["trade"] is None


def test_clear_queues():
    """Test clearing all event queues."""
    refractory = RefractoryConfig(defend=2)
    config = SignalConfig(refractory=refractory, enable_queuing=True)
    processor = SignalProcessor(config)
    
    # Trigger refractory and queue events
    event1 = Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-01")
    processor.process_events([event1])
    
    event2 = Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-02")
    processor.process_events([event2])
    
    assert processor.get_queue_status()["defend"] == 1
    
    processor.clear_queues()
    assert processor.get_queue_status()["defend"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
