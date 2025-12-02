"""Signal processing with refractory periods for M|inc events.

This module implements the SignalProcessor class which manages event channels
with priorities and refractory periods to prevent oscillatory loops.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from .models import Event, EventType
from .config import RefractoryConfig


class Channel(Enum):
    """Event channels for signal processing."""
    RAID = "raid"
    DEFEND = "defend"
    BRIBE = "bribe"
    TRADE = "trade"
    RETAINER = "retainer"


@dataclass
class Signal:
    """A signal representing a processed event with channel and priority.
    
    Signals are routed through channels that can have refractory periods
    to prevent immediate re-triggering.
    """
    channel: Channel
    priority: int
    payload: Dict[str, Any]
    timestamp: int
    refractory_until: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary representation."""
        return {
            "channel": self.channel.value,
            "priority": self.priority,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "refractory_until": self.refractory_until,
        }


@dataclass
class SignalConfig:
    """Configuration for signal processing."""
    refractory: RefractoryConfig = field(default_factory=RefractoryConfig)
    priorities: Dict[str, int] = field(default_factory=lambda: {
        "raid": 3,
        "defend": 3,
        "bribe": 2,
        "trade": 1,
        "retainer": 1,
    })


class SignalProcessor:
    """Process events through channels with refractory periods.
    
    The SignalProcessor routes events to appropriate channels, enforces
    refractory periods to prevent oscillations, and manages event queuing
    during cooldown windows.
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
    """
    
    def __init__(self, config: SignalConfig):
        """Initialize the signal processor.
        
        Args:
            config: SignalConfig with refractory periods and priorities
        """
        self.config = config
        self._refractory_state: Dict[Channel, int] = {}  # channel -> tick when refractory expires
        self._queued_events: Dict[Channel, List[Event]] = {channel: [] for channel in Channel}
        self._current_tick: int = 0
    
    def process_events(self, events: List[Event]) -> List[Signal]:
        """Route events to channels and create signals.
        
        Events that occur during refractory periods are queued for later
        processing. Active events are converted to signals with priorities.
        
        Args:
            events: List of events to process
            
        Returns:
            List of signals sorted by priority (highest first)
            
        Requirements: 13.1, 13.2, 13.3
        """
        signals = []
        
        for event in events:
            channel = self._event_to_channel(event)
            
            if self.is_channel_active(channel):
                # Channel is active, create signal
                signal = self._create_signal(event, channel)
                signals.append(signal)
                
                # Set refractory period for this channel
                refractory_ticks = self._get_refractory_period(channel)
                if refractory_ticks > 0:
                    self._refractory_state[channel] = self._current_tick + refractory_ticks
                    signal.refractory_until = self._refractory_state[channel]
            else:
                # Channel is in refractory, queue the event
                self._queued_events[channel].append(event)
        
        # Sort signals by priority (highest first)
        signals.sort(key=lambda s: s.priority, reverse=True)
        
        return signals
    
    def update_refractory(self, tick_num: int) -> List[Signal]:
        """Update refractory state and process queued events.
        
        This method should be called at the start of each tick to:
        1. Update the current tick number
        2. Check which channels have expired refractory periods
        3. Process queued events for expired channels
        
        Args:
            tick_num: Current tick number
            
        Returns:
            List of signals from coalesced queued events
            
        Requirements: 13.2, 13.4
        """
        self._current_tick = tick_num
        signals = []
        
        # Check each channel for expired refractory periods
        expired_channels = []
        for channel, expiry_tick in list(self._refractory_state.items()):
            if tick_num >= expiry_tick:
                expired_channels.append(channel)
        
        # Remove expired refractory states
        for channel in expired_channels:
            del self._refractory_state[channel]
        
        # Process queued events for expired channels
        for channel in expired_channels:
            if self._queued_events[channel]:
                # Coalesce queued events
                coalesced_events = self._coalesce_events(self._queued_events[channel])
                
                # Create signals from coalesced events
                for event in coalesced_events:
                    signal = self._create_signal(event, channel)
                    signals.append(signal)
                    
                    # Set new refractory period
                    refractory_ticks = self._get_refractory_period(channel)
                    if refractory_ticks > 0:
                        self._refractory_state[channel] = tick_num + refractory_ticks
                        signal.refractory_until = self._refractory_state[channel]
                
                # Clear the queue
                self._queued_events[channel] = []
        
        # Sort signals by priority
        signals.sort(key=lambda s: s.priority, reverse=True)
        
        return signals
    
    def is_channel_active(self, channel: Channel) -> bool:
        """Check if a channel is active (not in refractory period).
        
        Args:
            channel: Channel to check
            
        Returns:
            True if channel is active, False if in refractory period
            
        Requirements: 13.2
        """
        if channel not in self._refractory_state:
            return True
        
        return self._current_tick >= self._refractory_state[channel]
    
    def get_refractory_status(self) -> Dict[str, Optional[int]]:
        """Get the refractory status for all channels.
        
        Returns:
            Dictionary mapping channel names to expiry tick (None if active)
        """
        status = {}
        for channel in Channel:
            if channel in self._refractory_state:
                status[channel.value] = self._refractory_state[channel]
            else:
                status[channel.value] = None
        return status
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """Get the number of queued events for each channel.
        
        Returns:
            Dictionary mapping channel names to queue sizes
        """
        return {channel.value: len(events) for channel, events in self._queued_events.items()}
    
    def _event_to_channel(self, event: Event) -> Channel:
        """Map an event type to its corresponding channel.
        
        Args:
            event: Event to map
            
        Returns:
            Channel for the event
        """
        # Map event types to channels
        event_channel_map = {
            EventType.BRIBE_ACCEPT: Channel.BRIBE,
            EventType.BRIBE_INSUFFICIENT: Channel.BRIBE,
            EventType.DEFEND_WIN: Channel.DEFEND,
            EventType.DEFEND_LOSS: Channel.DEFEND,
            EventType.UNOPPOSED_RAID: Channel.RAID,
            EventType.TRADE: Channel.TRADE,
            EventType.RETAINER: Channel.RETAINER,
            EventType.TRAIT_DRIP: Channel.TRADE,  # Trait drips use trade channel (no refractory)
        }
        
        return event_channel_map.get(event.type, Channel.TRADE)
    
    def _create_signal(self, event: Event, channel: Channel) -> Signal:
        """Create a signal from an event.
        
        Args:
            event: Event to convert
            channel: Channel for the signal
            
        Returns:
            Signal with appropriate priority and payload
        """
        priority = self.config.priorities.get(channel.value, 1)
        
        # Create payload from event data
        payload = event.to_dict()
        
        return Signal(
            channel=channel,
            priority=priority,
            payload=payload,
            timestamp=event.tick,
        )
    
    def _get_refractory_period(self, channel: Channel) -> int:
        """Get the refractory period for a channel.
        
        Args:
            channel: Channel to query
            
        Returns:
            Refractory period in ticks
        """
        channel_name = channel.value
        return getattr(self.config.refractory, channel_name, 0)
    
    def _coalesce_events(self, events: List[Event]) -> List[Event]:
        """Coalesce queued events when refractory period expires.
        
        This method processes queued events and applies coalescing logic:
        - Deduplicates identical events (same type and participants)
        - Merges events with the same participants, keeping the most recent
        - Sorts by tick number to maintain temporal ordering
        
        Args:
            events: List of queued events
            
        Returns:
            List of coalesced events sorted by tick and priority
            
        Requirements: 13.4
        """
        if not events:
            return []
        
        # Coalescing strategy:
        # 1. Group events by a unique key (type + participants)
        # 2. For each group, keep only the most recent event (highest tick)
        # 3. Sort final list by tick number to maintain temporal ordering
        
        # Create a dictionary to track the most recent event for each unique interaction
        coalesced: Dict[str, Event] = {}
        
        for event in events:
            # Create a unique key based on event type and participants
            key_parts = [event.type.value]
            if event.king:
                key_parts.append(f"K:{event.king}")
            if event.knight:
                key_parts.append(f"N:{event.knight}")
            if event.merc:
                key_parts.append(f"M:{event.merc}")
            
            key = "|".join(key_parts)
            
            # Keep the most recent event for this key
            if key not in coalesced or event.tick > coalesced[key].tick:
                coalesced[key] = event
        
        # Return coalesced events sorted by tick number
        return sorted(coalesced.values(), key=lambda e: e.tick)
