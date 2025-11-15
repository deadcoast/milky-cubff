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
    TRAIT_DRIP = "trait_drip"


@dataclass
class Signal:
    """A signal representing a processed event with channel and priority.
    
    Signals are routed through channels that can have refractory periods
    to prevent immediate re-triggering.
    """
    channel: Channel
    priority: int
    payload: Dict[str, Any]
    timestamp: int  # tick number
    refractory_until: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
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
    channel_priorities: Dict[str, int] = field(default_factory=lambda: {
        "raid": 100,
        "defend": 100,
        "bribe": 90,
        "trade": 50,
        "retainer": 60,
        "trait_drip": 10
    })
    enable_queuing: bool = True
    enable_coalescing: bool = True


class SignalProcessor:
    """Process events and manage refractory periods for event channels.
    
    The SignalProcessor routes events to appropriate channels, enforces
    refractory periods to prevent oscillations, and manages event queuing
    during cooldown windows.
    """
    
    def __init__(self, config: SignalConfig):
        """Initialize the signal processor.
        
        Args:
            config: SignalConfig with refractory periods and priorities
        """
        self.config = config
        self._refractory_state: Dict[Channel, int] = {}  # channel -> tick when refractory expires
        self._event_queue: Dict[Channel, List[Event]] = {channel: [] for channel in Channel}
        self._current_tick: int = 0
    
    def process_events(self, events: List[Event]) -> List[Signal]:
        """Process events and route them to appropriate channels.
        
        Events that occur during refractory periods are queued if queuing
        is enabled, otherwise they are dropped.
        
        Args:
            events: List of events to process
            
        Returns:
            List of signals that were successfully routed
        """
        signals = []
        
        for event in events:
            channel = self._event_to_channel(event)
            
            # Update current tick from event if not set
            if self._current_tick == 0 and event.tick > 0:
                self._current_tick = event.tick
            
            if self.is_channel_active(channel):
                # Channel is active, create signal
                signal = self._create_signal(event, channel)
                signals.append(signal)
                
                # Set refractory period for this channel based on current tick
                refractory_ticks = self._get_refractory_period(channel)
                if refractory_ticks > 0:
                    # Use event tick if current tick is 0, otherwise use current tick
                    base_tick = event.tick if self._current_tick == 0 else self._current_tick
                    self._refractory_state[channel] = base_tick + refractory_ticks
                    signal.refractory_until = self._refractory_state[channel]
            else:
                # Channel is in refractory period
                if self.config.enable_queuing:
                    self._event_queue[channel].append(event)
        
        # Sort signals by priority (highest first)
        signals.sort(key=lambda s: s.priority, reverse=True)
        
        return signals
    
    def update_refractory(self, tick_num: int) -> List[Signal]:
        """Update refractory state and process queued events.
        
        This should be called at the start of each tick to:
        1. Update the current tick number
        2. Clear expired refractory periods
        3. Process queued events for channels that are now active
        
        Args:
            tick_num: Current tick number
            
        Returns:
            List of signals from queued events that can now be processed
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
            
            # Process queued events for this channel
            if self._event_queue[channel]:
                queued_events = self._event_queue[channel]
                self._event_queue[channel] = []
                
                # Coalesce if enabled
                if self.config.enable_coalescing:
                    queued_events = self._coalesce_events(queued_events)
                
                # Process the queued events
                for event in queued_events:
                    signal = self._create_signal(event, channel)
                    signals.append(signal)
                    
                    # Set new refractory period
                    refractory_ticks = self._get_refractory_period(channel)
                    if refractory_ticks > 0:
                        self._refractory_state[channel] = tick_num + refractory_ticks
                        signal.refractory_until = self._refractory_state[channel]
        
        # Sort signals by priority
        signals.sort(key=lambda s: s.priority, reverse=True)
        
        return signals
    
    def is_channel_active(self, channel: Channel) -> bool:
        """Check if a channel is currently active (not in refractory period).
        
        Args:
            channel: Channel to check
            
        Returns:
            True if channel is active, False if in refractory period
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
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get the number of queued events for each channel.
        
        Returns:
            Dictionary mapping channel names to queue length
        """
        return {channel.value: len(self._event_queue[channel]) for channel in Channel}
    
    def clear_queues(self) -> None:
        """Clear all queued events."""
        for channel in Channel:
            self._event_queue[channel] = []
    
    def _event_to_channel(self, event: Event) -> Channel:
        """Map an event to its appropriate channel.
        
        Args:
            event: Event to map
            
        Returns:
            Channel for this event type
        """
        event_type_to_channel = {
            EventType.TRAIT_DRIP: Channel.TRAIT_DRIP,
            EventType.TRADE: Channel.TRADE,
            EventType.RETAINER: Channel.RETAINER,
            EventType.BRIBE_ACCEPT: Channel.BRIBE,
            EventType.BRIBE_INSUFFICIENT: Channel.BRIBE,
            EventType.DEFEND_WIN: Channel.DEFEND,
            EventType.DEFEND_LOSS: Channel.DEFEND,
            EventType.UNOPPOSED_RAID: Channel.RAID,
        }
        
        return event_type_to_channel.get(event.type, Channel.RAID)
    
    def _create_signal(self, event: Event, channel: Channel) -> Signal:
        """Create a signal from an event.
        
        Args:
            event: Event to convert
            channel: Channel for the signal
            
        Returns:
            Signal instance
        """
        priority = self.config.channel_priorities.get(channel.value, 50)
        
        payload = {
            "event_type": event.type.value,
            "tick": event.tick,
        }
        
        # Add event-specific fields to payload
        if event.king:
            payload["king"] = event.king
        if event.knight:
            payload["knight"] = event.knight
        if event.merc:
            payload["merc"] = event.merc
        if event.amount is not None:
            payload["amount"] = event.amount
        if event.stake is not None:
            payload["stake"] = event.stake
        if event.notes:
            payload["notes"] = event.notes
        
        return Signal(
            channel=channel,
            priority=priority,
            payload=payload,
            timestamp=event.tick
        )
    
    def _get_refractory_period(self, channel: Channel) -> int:
        """Get the refractory period for a channel.
        
        Args:
            channel: Channel to query
            
        Returns:
            Refractory period in ticks
        """
        channel_to_config = {
            Channel.RAID: self.config.refractory.raid,
            Channel.DEFEND: self.config.refractory.defend,
            Channel.BRIBE: self.config.refractory.bribe,
            Channel.TRADE: self.config.refractory.trade,
            Channel.RETAINER: 0,  # No refractory for retainers
            Channel.TRAIT_DRIP: 0,  # No refractory for trait drips
        }
        
        return channel_to_config.get(channel, 0)
    
    def _coalesce_events(self, events: List[Event]) -> List[Event]:
        """Coalesce multiple queued events into a smaller set.
        
        This reduces redundant events by combining similar events.
        For now, we use a simple strategy: keep only the most recent
        event of each type for each agent combination.
        
        Args:
            events: List of events to coalesce
            
        Returns:
            Coalesced list of events
        """
        if not events:
            return []
        
        # Group events by (type, king, knight, merc) tuple
        event_map: Dict[tuple, Event] = {}
        
        for event in events:
            key = (event.type, event.king, event.knight, event.merc)
            # Keep the most recent event (last one in the list)
            event_map[key] = event
        
        return list(event_map.values())
