"""Tests for signal processing with refractory periods."""

import pytest
from m_inc.core.signals import SignalProcessor, SignalConfig, Channel, Signal
from m_inc.core.models import Event, EventType
from m_inc.core.config import RefractoryConfig


def test_signal_processor_initialization():
    """Test that SignalProcessor initializes correctly."""
    config = SignalConfig()
    processor = SignalProcessor(config)
    
    assert processor.config == config
    assert processor._current_tick == 0
    assert len(processor._refractory_state) == 0
    assert len(processor._queued_events) == len(Channel)


def test_process_events_creates_signals():
    """Test that process_events converts events to signals."""
    config = SignalConfig(refractory=RefractoryConfig(raid=0, defend=0, bribe=0, trade=0))
    processor = SignalProcessor(config)
    
    events = [
        Event(tick=1, type=EventType.TRADE, king="K-01", amount=100),
        Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=200),
    ]
    
    signals = processor.process_events(events)
    
    assert len(signals) == 2
    assert all(isinstance(s, Signal) for s in signals)


def test_process_events_sorts_by_priority():
    """Test that signals are sorted by priority (highest first)."""
    config = SignalConfig(
        refractory=RefractoryConfig(raid=0, defend=0, bribe=0, trade=0),
        priorities={"trade": 1, "bribe": 2, "defend": 3}
    )
    processor = SignalProcessor(config)
    
    events = [
        Event(tick=1, type=EventType.TRADE, king="K-01"),
        Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01"),
        Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-01"),
    ]
    
    signals = processor.process_events(events)
    
    # Should be sorted: defend (3), bribe (2), trade (1)
    assert signals[0].channel == Channel.DEFEND
    assert signals[1].channel == Channel.BRIBE
    assert signals[2].channel == Channel.TRADE


def test_is_channel_active_when_no_refractory():
    """Test that channels are active when not in refractory period."""
    config = SignalConfig()
    processor = SignalProcessor(config)
    
    assert processor.is_channel_active(Channel.RAID)
    assert processor.is_channel_active(Channel.DEFEND)
    assert processor.is_channel_active(Channel.BRIBE)


def test_is_channel_active_during_refractory():
    """Test that channels are inactive during refractory period."""
    config = SignalConfig(refractory=RefractoryConfig(raid=2))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # Process an event to trigger refractory
    events = [Event(tick=1, type=EventType.UNOPPOSED_RAID, merc="M-01", king="K-01")]
    processor.process_events(events)
    
    # Channel should be inactive until tick 3 (1 + 2)
    assert not processor.is_channel_active(Channel.RAID)
    
    # Move to tick 3
    processor._current_tick = 3
    assert processor.is_channel_active(Channel.RAID)


def test_events_queued_during_refractory():
    """Test that events are queued when channel is in refractory period."""
    config = SignalConfig(refractory=RefractoryConfig(bribe=2))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # First event triggers refractory
    events1 = [Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01")]
    signals1 = processor.process_events(events1)
    assert len(signals1) == 1
    
    # Second event should be queued
    events2 = [Event(tick=2, type=EventType.BRIBE_ACCEPT, king="K-02", merc="M-02")]
    processor._current_tick = 2
    signals2 = processor.process_events(events2)
    assert len(signals2) == 0  # No signals because channel is in refractory
    
    # Check queue
    queue_sizes = processor.get_queue_sizes()
    assert queue_sizes["bribe"] == 1


def test_update_refractory_processes_queued_events():
    """Test that update_refractory processes queued events when refractory expires."""
    config = SignalConfig(refractory=RefractoryConfig(defend=2))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # First event triggers refractory
    events1 = [Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-01")]
    processor.process_events(events1)
    
    # Queue events during refractory
    processor._current_tick = 2
    events2 = [Event(tick=2, type=EventType.DEFEND_WIN, king="K-02", knight="N-02", merc="M-02")]
    processor.process_events(events2)
    
    # Update to tick 3 (refractory expires)
    signals = processor.update_refractory(3)
    
    # Should process the queued event
    assert len(signals) == 1
    assert signals[0].channel == Channel.DEFEND
    
    # Queue should be empty
    queue_sizes = processor.get_queue_sizes()
    assert queue_sizes["defend"] == 0


def test_refractory_period_set_correctly():
    """Test that refractory periods are set correctly from config."""
    config = SignalConfig(refractory=RefractoryConfig(raid=3, defend=2, bribe=1))
    processor = SignalProcessor(config)
    processor._current_tick = 5
    
    # Process events for different channels
    events = [
        Event(tick=5, type=EventType.UNOPPOSED_RAID, merc="M-01", king="K-01"),
        Event(tick=5, type=EventType.DEFEND_WIN, king="K-02", knight="N-01", merc="M-02"),
        Event(tick=5, type=EventType.BRIBE_ACCEPT, king="K-03", merc="M-03"),
    ]
    
    signals = processor.process_events(events)
    
    # Check refractory_until values
    raid_signal = next(s for s in signals if s.channel == Channel.RAID)
    defend_signal = next(s for s in signals if s.channel == Channel.DEFEND)
    bribe_signal = next(s for s in signals if s.channel == Channel.BRIBE)
    
    assert raid_signal.refractory_until == 8  # 5 + 3
    assert defend_signal.refractory_until == 7  # 5 + 2
    assert bribe_signal.refractory_until == 6  # 5 + 1


def test_get_refractory_status():
    """Test that get_refractory_status returns correct state."""
    config = SignalConfig(refractory=RefractoryConfig(raid=2))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # Initially all channels should be active (None)
    status = processor.get_refractory_status()
    assert all(v is None for v in status.values())
    
    # Trigger refractory on raid channel
    events = [Event(tick=1, type=EventType.UNOPPOSED_RAID, merc="M-01", king="K-01")]
    processor.process_events(events)
    
    status = processor.get_refractory_status()
    assert status["raid"] == 3  # 1 + 2
    assert status["defend"] is None
    assert status["bribe"] is None


def test_zero_refractory_period():
    """Test that channels with zero refractory period don't block."""
    config = SignalConfig(refractory=RefractoryConfig(trade=0))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # Process multiple trade events
    events1 = [Event(tick=1, type=EventType.TRADE, king="K-01")]
    signals1 = processor.process_events(events1)
    assert len(signals1) == 1
    
    # Should be able to process another immediately
    events2 = [Event(tick=1, type=EventType.TRADE, king="K-02")]
    signals2 = processor.process_events(events2)
    assert len(signals2) == 1


def test_event_to_channel_mapping():
    """Test that events are mapped to correct channels."""
    config = SignalConfig()
    processor = SignalProcessor(config)
    
    test_cases = [
        (EventType.BRIBE_ACCEPT, Channel.BRIBE),
        (EventType.BRIBE_INSUFFICIENT, Channel.BRIBE),
        (EventType.DEFEND_WIN, Channel.DEFEND),
        (EventType.DEFEND_LOSS, Channel.DEFEND),
        (EventType.UNOPPOSED_RAID, Channel.RAID),
        (EventType.TRADE, Channel.TRADE),
        (EventType.RETAINER, Channel.RETAINER),
        (EventType.TRAIT_DRIP, Channel.TRADE),
    ]
    
    for event_type, expected_channel in test_cases:
        event = Event(tick=1, type=event_type)
        channel = processor._event_to_channel(event)
        assert channel == expected_channel, f"Event {event_type} should map to {expected_channel}"


def test_multiple_queued_events_coalesced():
    """Test that multiple queued events are processed when refractory expires."""
    config = SignalConfig(refractory=RefractoryConfig(bribe=2))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # Trigger refractory
    events1 = [Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01")]
    processor.process_events(events1)
    
    # Queue multiple events
    processor._current_tick = 2
    events2 = [
        Event(tick=2, type=EventType.BRIBE_ACCEPT, king="K-02", merc="M-02"),
        Event(tick=2, type=EventType.BRIBE_INSUFFICIENT, king="K-03", merc="M-03"),
    ]
    processor.process_events(events2)
    
    # Update to expire refractory
    signals = processor.update_refractory(3)
    
    # Should process both queued events
    assert len(signals) == 2
    assert all(s.channel == Channel.BRIBE for s in signals)


def test_coalesced_events_maintain_temporal_order():
    """Test that coalesced events are processed in temporal order."""
    config = SignalConfig(refractory=RefractoryConfig(defend=3))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # Trigger refractory
    events1 = [Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-01")]
    processor.process_events(events1)
    
    # Queue events at different ticks (out of order)
    processor._current_tick = 2
    events2 = [Event(tick=3, type=EventType.DEFEND_WIN, king="K-03", knight="N-03", merc="M-03")]
    processor.process_events(events2)
    
    processor._current_tick = 3
    events3 = [Event(tick=2, type=EventType.DEFEND_LOSS, king="K-02", knight="N-02", merc="M-02")]
    processor.process_events(events3)
    
    # Update to expire refractory at tick 4
    signals = processor.update_refractory(4)
    
    # Should process both events in temporal order (tick 2 before tick 3)
    assert len(signals) == 2
    assert signals[0].payload["tick"] == 2
    assert signals[1].payload["tick"] == 3


def test_queued_events_across_multiple_channels():
    """Test that queued events in different channels are handled independently."""
    config = SignalConfig(refractory=RefractoryConfig(bribe=2, defend=2))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # Trigger refractory on both channels
    events1 = [
        Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01"),
        Event(tick=1, type=EventType.DEFEND_WIN, king="K-02", knight="N-01", merc="M-02"),
    ]
    processor.process_events(events1)
    
    # Queue events on both channels
    processor._current_tick = 2
    events2 = [
        Event(tick=2, type=EventType.BRIBE_ACCEPT, king="K-03", merc="M-03"),
        Event(tick=2, type=EventType.DEFEND_LOSS, king="K-04", knight="N-02", merc="M-04"),
    ]
    processor.process_events(events2)
    
    # Check both channels have queued events
    queue_sizes = processor.get_queue_sizes()
    assert queue_sizes["bribe"] == 1
    assert queue_sizes["defend"] == 1
    
    # Update to expire refractory
    signals = processor.update_refractory(3)
    
    # Should process queued events from both channels
    assert len(signals) == 2
    channels = {s.channel for s in signals}
    assert Channel.BRIBE in channels
    assert Channel.DEFEND in channels
    
    # Queues should be empty
    queue_sizes = processor.get_queue_sizes()
    assert queue_sizes["bribe"] == 0
    assert queue_sizes["defend"] == 0


def test_priority_scheduling_with_coalesced_events():
    """Test that coalesced events are sorted by priority."""
    config = SignalConfig(
        refractory=RefractoryConfig(bribe=2, defend=2, trade=2),
        priorities={"trade": 1, "bribe": 2, "defend": 3}
    )
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # Trigger refractory on multiple channels
    events1 = [
        Event(tick=1, type=EventType.TRADE, king="K-01"),
        Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-02", merc="M-01"),
        Event(tick=1, type=EventType.DEFEND_WIN, king="K-03", knight="N-01", merc="M-02"),
    ]
    processor.process_events(events1)
    
    # Queue events on all channels
    processor._current_tick = 2
    events2 = [
        Event(tick=2, type=EventType.TRADE, king="K-04"),
        Event(tick=2, type=EventType.BRIBE_ACCEPT, king="K-05", merc="M-03"),
        Event(tick=2, type=EventType.DEFEND_LOSS, king="K-06", knight="N-02", merc="M-04"),
    ]
    processor.process_events(events2)
    
    # Update to expire refractory
    signals = processor.update_refractory(3)
    
    # Should be sorted by priority: defend (3), bribe (2), trade (1)
    assert len(signals) == 3
    assert signals[0].channel == Channel.DEFEND
    assert signals[0].priority == 3
    assert signals[1].channel == Channel.BRIBE
    assert signals[1].priority == 2
    assert signals[2].channel == Channel.TRADE
    assert signals[2].priority == 1


def test_coalescing_deduplicates_identical_events():
    """Test that coalescing deduplicates identical events, keeping the most recent."""
    config = SignalConfig(refractory=RefractoryConfig(bribe=3))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # Trigger refractory
    events1 = [Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=100)]
    processor.process_events(events1)
    
    # Queue multiple events with same participants at different ticks
    processor._current_tick = 2
    events2 = [Event(tick=2, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=150)]
    processor.process_events(events2)
    
    processor._current_tick = 3
    events3 = [Event(tick=3, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-01", amount=200)]
    processor.process_events(events3)
    
    # Update to expire refractory at tick 4
    signals = processor.update_refractory(4)
    
    # Should only have 1 signal (the most recent one from tick 3)
    assert len(signals) == 1
    assert signals[0].payload["tick"] == 3
    assert signals[0].payload["amount"] == 200


def test_coalescing_preserves_different_participants():
    """Test that coalescing preserves events with different participants."""
    config = SignalConfig(refractory=RefractoryConfig(defend=3))
    processor = SignalProcessor(config)
    processor._current_tick = 1
    
    # Trigger refractory
    events1 = [Event(tick=1, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-01")]
    processor.process_events(events1)
    
    # Queue events with different participants
    processor._current_tick = 2
    events2 = [
        Event(tick=2, type=EventType.DEFEND_WIN, king="K-01", knight="N-01", merc="M-02"),  # Different merc
        Event(tick=2, type=EventType.DEFEND_WIN, king="K-02", knight="N-01", merc="M-01"),  # Different king
        Event(tick=2, type=EventType.DEFEND_WIN, king="K-01", knight="N-02", merc="M-01"),  # Different knight
    ]
    processor.process_events(events2)
    
    # Update to expire refractory
    signals = processor.update_refractory(4)
    
    # Should have 3 signals (all different participants)
    assert len(signals) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
