"""Event aggregator for M|inc tick summaries and metrics."""

from typing import List, Dict, Optional
from collections import defaultdict
import math
from .models import Event, EventType, Agent, Role, TickMetrics


class EventAggregator:
    """Aggregates events and computes tick-level summaries.
    
    Collects events from a tick and generates:
    - Event counts by type
    - Currency flows by role
    - Wealth changes by role and trait
    - Tick-level metrics (entropy, compression, wealth distribution)
    """
    
    def __init__(self):
        """Initialize event aggregator with empty state."""
        self.events: List[Event] = []
        self.agents: Optional[List[Agent]] = None
    
    def add_event(self, event: Event) -> None:
        """Add an event to the aggregator.
        
        Args:
            event: Event to add
        """
        self.events.append(event)
    
    def set_agents(self, agents: List[Agent]) -> None:
        """Set the current agent list for metrics computation.
        
        Args:
            agents: List of all agents in current state
        """
        self.agents = agents
    
    def get_tick_summary(self, tick_num: int) -> Dict:
        """Generate a summary for the specified tick.
        
        Args:
            tick_num: Tick number to summarize
            
        Returns:
            Dictionary with event counts, currency flows, and wealth changes
        """
        tick_events = [e for e in self.events if e.tick == tick_num]
        
        # Compute event counts by type
        event_counts = self._compute_event_counts(tick_events)
        
        # Compute currency flows by role
        currency_flows = self._compute_currency_flows(tick_events)
        
        # Compute wealth changes by role and trait
        wealth_changes = self._compute_wealth_changes(tick_events)
        
        return {
            "tick": tick_num,
            "event_counts": event_counts,
            "currency_flows": currency_flows,
            "wealth_changes": wealth_changes,
        }
    
    def compute_metrics(self, agents: List[Agent], 
                       entropy: float = 0.0,
                       compression_ratio: float = 0.0) -> TickMetrics:
        """Compute tick-level metrics from agents and events.
        
        Args:
            agents: List of all agents
            entropy: Entropy value (from BFF trace, default 0.0)
            compression_ratio: Compression ratio (from BFF trace, default 0.0)
            
        Returns:
            TickMetrics with all computed values
        """
        # Compute basic totals
        wealth_total = sum(agent.wealth_total() for agent in agents)
        currency_total = sum(agent.currency for agent in agents)
        
        # Compute mean copy score
        copy_scores = [agent.wealth.copy for agent in agents]
        copy_score_mean = sum(copy_scores) / len(copy_scores) if copy_scores else 0.0
        
        # Compute entropy from agent wealth distribution
        if not entropy:
            entropy = self._compute_wealth_entropy(agents)
        
        # Compute compression ratio proxy (if not provided)
        if not compression_ratio:
            compression_ratio = self._compute_compression_proxy(agents)
        
        # Count event types
        bribes_paid = sum(1 for e in self.events 
                         if e.type in [EventType.BRIBE_ACCEPT, EventType.BRIBE_INSUFFICIENT])
        bribes_accepted = sum(1 for e in self.events if e.type == EventType.BRIBE_ACCEPT)
        raids_attempted = sum(1 for e in self.events 
                             if e.type in [EventType.DEFEND_WIN, EventType.DEFEND_LOSS, 
                                          EventType.UNOPPOSED_RAID])
        raids_won_by_merc = sum(1 for e in self.events 
                               if e.type in [EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID])
        raids_won_by_knight = sum(1 for e in self.events if e.type == EventType.DEFEND_WIN)
        
        return TickMetrics(
            entropy=entropy,
            compression_ratio=compression_ratio,
            copy_score_mean=copy_score_mean,
            wealth_total=wealth_total,
            currency_total=currency_total,
            bribes_paid=bribes_paid,
            bribes_accepted=bribes_accepted,
            raids_attempted=raids_attempted,
            raids_won_by_merc=raids_won_by_merc,
            raids_won_by_knight=raids_won_by_knight,
        )
    
    def compute_gini_coefficient(self, agents: List[Agent]) -> float:
        """Compute Gini coefficient for wealth inequality.
        
        The Gini coefficient measures inequality in wealth distribution.
        0 = perfect equality, 1 = perfect inequality.
        
        Args:
            agents: List of all agents
            
        Returns:
            Gini coefficient (0.0 to 1.0)
        """
        if not agents:
            return 0.0
        
        # Get wealth values sorted
        wealth_values = sorted([agent.wealth_total() for agent in agents])
        n = len(wealth_values)
        
        if n == 0 or sum(wealth_values) == 0:
            return 0.0
        
        # Compute Gini coefficient using the formula:
        # G = (2 * sum(i * w_i)) / (n * sum(w_i)) - (n + 1) / n
        cumsum = 0.0
        for i, wealth in enumerate(wealth_values, start=1):
            cumsum += i * wealth
        
        total_wealth = sum(wealth_values)
        gini = (2.0 * cumsum) / (n * total_wealth) - (n + 1.0) / n
        
        return max(0.0, min(1.0, gini))  # Clamp to [0, 1]
    
    def _compute_wealth_entropy(self, agents: List[Agent]) -> float:
        """Compute Shannon entropy from agent wealth distribution.
        
        Entropy measures the diversity/uncertainty in wealth distribution.
        Higher entropy = more diverse distribution.
        
        Args:
            agents: List of all agents
            
        Returns:
            Shannon entropy in bits
        """
        if not agents:
            return 0.0
        
        # Get wealth values
        wealth_values = [agent.wealth_total() for agent in agents]
        total_wealth = sum(wealth_values)
        
        if total_wealth == 0:
            return 0.0
        
        # Compute probabilities
        probabilities = [w / total_wealth for w in wealth_values if w > 0]
        
        # Compute Shannon entropy: H = -sum(p * log2(p))
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
        
        return entropy
    
    def _compute_compression_proxy(self, agents: List[Agent]) -> float:
        """Compute compression ratio proxy from agent diversity.
        
        This is a proxy metric based on the diversity of agent states.
        Higher values indicate more compressible (less diverse) states.
        
        Args:
            agents: List of all agents
            
        Returns:
            Compression ratio proxy
        """
        if not agents:
            return 0.0
        
        # Use role distribution as a simple proxy
        role_counts = defaultdict(int)
        for agent in agents:
            role_counts[agent.role.value] += 1
        
        n = len(agents)
        if n == 0:
            return 0.0
        
        # Compute diversity score (inverse of concentration)
        # Higher concentration = higher compression ratio
        max_count = max(role_counts.values()) if role_counts else 0
        concentration = max_count / n if n > 0 else 0
        
        # Scale to reasonable range (1.0 to 3.0)
        compression_ratio = 1.0 + (concentration * 2.0)
        
        return compression_ratio
    
    def clear(self) -> None:
        """Clear all accumulated events."""
        self.events.clear()
    
    def _compute_event_counts(self, events: List[Event]) -> Dict[str, int]:
        """Compute event counts by type.
        
        Args:
            events: List of events to count
            
        Returns:
            Dictionary mapping event type to count
        """
        counts: Dict[str, int] = defaultdict(int)
        for event in events:
            counts[event.type.value] += 1
        return dict(counts)
    
    def _compute_currency_flows(self, events: List[Event]) -> Dict[str, Dict[str, int]]:
        """Compute currency flows by role.
        
        Tracks currency gained/lost by each role from events.
        
        Args:
            events: List of events to analyze
            
        Returns:
            Dictionary mapping role to {gained, lost} amounts
        """
        flows: Dict[str, Dict[str, int]] = {
            "king": {"gained": 0, "lost": 0},
            "knight": {"gained": 0, "lost": 0},
            "mercenary": {"gained": 0, "lost": 0},
        }
        
        for event in events:
            # Bribe accept: king loses, merc gains
            if event.type == EventType.BRIBE_ACCEPT and event.amount:
                flows["king"]["lost"] += event.amount
                flows["mercenary"]["gained"] += event.amount
            
            # Trade: king loses currency
            elif event.type == EventType.TRADE and event.invest:
                flows["king"]["lost"] += event.invest
            
            # Retainer: king loses, knight gains
            elif event.type == EventType.RETAINER and event.amount:
                flows["king"]["lost"] += event.amount
                flows["knight"]["gained"] += event.amount
            
            # Defend win: merc loses stake, knight gains
            elif event.type == EventType.DEFEND_WIN and event.stake:
                flows["mercenary"]["lost"] += event.stake
                flows["knight"]["gained"] += event.stake
            
            # Defend loss: knight loses stake, merc gains
            elif event.type == EventType.DEFEND_LOSS and event.stake:
                flows["knight"]["lost"] += event.stake
                flows["mercenary"]["gained"] += event.stake
        
        return flows
    
    def _compute_wealth_changes(self, events: List[Event]) -> Dict[str, Dict[str, int]]:
        """Compute wealth changes by role and trait.
        
        Tracks wealth gained/lost by each role from events.
        
        Args:
            events: List of events to analyze
            
        Returns:
            Dictionary mapping role to trait changes
        """
        changes: Dict[str, Dict[str, int]] = {
            "king": defaultdict(int),
            "knight": defaultdict(int),
            "mercenary": defaultdict(int),
        }
        
        for event in events:
            # Trait drip: track by agent role (would need agent lookup)
            if event.type == EventType.TRAIT_DRIP and event.trait and event.delta:
                # Note: We'd need agent role info to properly categorize
                # For now, just track the trait name
                pass
            
            # Trade: king gains wealth (defend +3, trade +2)
            elif event.type == EventType.TRADE and event.wealth_created:
                changes["king"]["defend"] += 3
                changes["king"]["trade"] += 2
        
        # Convert defaultdicts to regular dicts
        return {
            role: dict(trait_changes) 
            for role, trait_changes in changes.items()
        }

