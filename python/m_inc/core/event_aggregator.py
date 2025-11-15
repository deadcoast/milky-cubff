"""Event aggregator for collecting and summarizing M|inc events."""

from typing import Dict, List, Optional
from collections import defaultdict
import math
from .models import Event, EventType, Agent, Role, TickMetrics


class TickSummary:
    """Summary of events and state changes for a single tick."""
    
    def __init__(self, tick: int):
        """Initialize tick summary.
        
        Args:
            tick: Tick number
        """
        self.tick = tick
        self.event_counts: Dict[str, int] = defaultdict(int)
        self.currency_flows: Dict[str, int] = defaultdict(int)
        self.wealth_changes: Dict[str, Dict[str, int]] = {
            "king": defaultdict(int),
            "knight": defaultdict(int),
            "mercenary": defaultdict(int)
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "tick": self.tick,
            "event_counts": dict(self.event_counts),
            "currency_flows": dict(self.currency_flows),
            "wealth_changes": {
                role: dict(traits) for role, traits in self.wealth_changes.items()
            }
        }


class EventAggregator:
    """Aggregates events and computes tick-level summaries.
    
    Collects micro-events (bribes, raids, trades) and produces:
    - Event counts by type
    - Currency flows by role
    - Wealth changes by role and trait
    - Tick-level metrics
    """
    
    def __init__(self):
        """Initialize event aggregator."""
        self.events: List[Event] = []
        self.tick_summaries: Dict[int, TickSummary] = {}
    
    def add_event(self, event: Event) -> None:
        """Add an event to the aggregator.
        
        Args:
            event: Event to add
        """
        self.events.append(event)
        
        # Update tick summary
        if event.tick not in self.tick_summaries:
            self.tick_summaries[event.tick] = TickSummary(event.tick)
        
        summary = self.tick_summaries[event.tick]
        
        # Count event type
        summary.event_counts[event.type.value] += 1
        
        # Track currency flows
        if event.type == EventType.BRIBE_ACCEPT:
            # King pays merc
            summary.currency_flows["king"] -= event.amount or 0
            summary.currency_flows["mercenary"] += event.amount or 0
        
        elif event.type == EventType.RETAINER:
            # King pays knight
            summary.currency_flows["king"] -= event.amount or 0
            summary.currency_flows["knight"] += event.amount or 0
        
        elif event.type == EventType.TRADE:
            # King invests currency, creates wealth
            summary.currency_flows["king"] -= event.invest or 0
            summary.wealth_changes["king"]["defend"] += 3
            summary.wealth_changes["king"]["trade"] += 2
        
        elif event.type == EventType.DEFEND_WIN:
            # Knight gains stake from merc
            summary.currency_flows["knight"] += event.stake or 0
            summary.currency_flows["mercenary"] -= event.stake or 0
        
        elif event.type == EventType.DEFEND_LOSS:
            # Merc gains from king, knight loses stake
            summary.currency_flows["knight"] -= event.stake or 0
        
        elif event.type == EventType.TRAIT_DRIP:
            # Trait emergence
            if event.trait and event.delta:
                # Determine role from agent ID prefix
                if event.agent:
                    role_map = {"K": "king", "N": "knight", "M": "mercenary"}
                    role = role_map.get(event.agent[0], "mercenary")
                    summary.wealth_changes[role][event.trait] += event.delta
    
    def get_tick_summary(self, tick_num: int) -> Optional[TickSummary]:
        """Get summary for a specific tick.
        
        Args:
            tick_num: Tick number
            
        Returns:
            TickSummary or None if tick not found
        """
        return self.tick_summaries.get(tick_num)
    
    def get_all_events(self) -> List[Event]:
        """Get all collected events.
        
        Returns:
            List of all events
        """
        return self.events
    
    def get_events_by_tick(self, tick_num: int) -> List[Event]:
        """Get all events for a specific tick.
        
        Args:
            tick_num: Tick number
            
        Returns:
            List of events for the tick
        """
        return [e for e in self.events if e.tick == tick_num]
    
    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """Get all events of a specific type.
        
        Args:
            event_type: Event type to filter by
            
        Returns:
            List of events of the specified type
        """
        return [e for e in self.events if e.type == event_type]
    
    def compute_metrics(self, agents: List[Agent]) -> TickMetrics:
        """Compute metrics from current agent state.
        
        Args:
            agents: List of all agents
            
        Returns:
            TickMetrics with computed values
        """
        if not agents:
            return TickMetrics(
                entropy=0.0,
                compression_ratio=0.0,
                copy_score_mean=0.0,
                wealth_total=0,
                currency_total=0
            )
        
        # Compute totals
        wealth_total = sum(agent.wealth_total() for agent in agents)
        currency_total = sum(agent.currency for agent in agents)
        
        # Compute copy score mean (normalized to 0-1 range)
        copy_scores = [agent.wealth.copy for agent in agents]
        copy_score_mean = sum(copy_scores) / len(copy_scores) if copy_scores else 0.0
        copy_score_mean = copy_score_mean / 20.0  # Normalize
        
        # Compute entropy from wealth distribution
        entropy = self._compute_entropy(agents)
        
        # Compute compression ratio proxy
        compression_ratio = self._compute_compression_ratio(agents)
        
        # Count event types from recent events
        recent_events = self.events[-100:] if len(self.events) > 100 else self.events
        
        bribes_paid = sum(1 for e in recent_events if e.type in [EventType.BRIBE_ACCEPT, EventType.BRIBE_INSUFFICIENT])
        bribes_accepted = sum(1 for e in recent_events if e.type == EventType.BRIBE_ACCEPT)
        raids_attempted = sum(1 for e in recent_events if e.type in [EventType.DEFEND_WIN, EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID])
        raids_won_by_merc = sum(1 for e in recent_events if e.type in [EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID])
        raids_won_by_knight = sum(1 for e in recent_events if e.type == EventType.DEFEND_WIN)
        
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
            raids_won_by_knight=raids_won_by_knight
        )
    
    def _compute_entropy(self, agents: List[Agent]) -> float:
        """Compute entropy from agent wealth distribution.
        
        Uses Shannon entropy: H = -Σ(p_i * log2(p_i))
        where p_i is the proportion of total wealth held by agent i.
        
        Args:
            agents: List of all agents
            
        Returns:
            Entropy value (higher = more uniform distribution)
        """
        total_wealth = sum(agent.wealth_total() for agent in agents)
        
        if total_wealth == 0:
            return 0.0
        
        entropy = 0.0
        for agent in agents:
            wealth = agent.wealth_total()
            if wealth > 0:
                p = wealth / total_wealth
                entropy -= p * math.log2(p)
        
        return entropy
    
    def _compute_compression_ratio(self, agents: List[Agent]) -> float:
        """Compute compression ratio proxy from agent diversity.
        
        Higher compression ratio indicates more diverse/complex agent states.
        Uses the ratio of unique wealth configurations to total agents.
        
        Args:
            agents: List of all agents
            
        Returns:
            Compression ratio proxy
        """
        if not agents:
            return 0.0
        
        # Count unique wealth configurations
        wealth_configs = set()
        for agent in agents:
            config = tuple(agent.wealth.to_dict().values())
            wealth_configs.add(config)
        
        # Ratio of unique configs to total agents
        diversity = len(wealth_configs) / len(agents)
        
        # Scale to approximate compression ratio (1.0 to 3.0 range)
        compression_ratio = 1.0 + (diversity * 2.0)
        
        return compression_ratio
    
    def compute_gini_coefficient(self, agents: List[Agent]) -> float:
        """Compute Gini coefficient for wealth inequality.
        
        Gini coefficient ranges from 0 (perfect equality) to 1 (perfect inequality).
        
        Args:
            agents: List of all agents
            
        Returns:
            Gini coefficient
        """
        if not agents:
            return 0.0
        
        # Get sorted wealth values
        wealth_values = sorted([agent.wealth_total() for agent in agents])
        n = len(wealth_values)
        
        if sum(wealth_values) == 0:
            return 0.0
        
        # Compute Gini coefficient
        cumsum = 0.0
        for i, wealth in enumerate(wealth_values):
            cumsum += (i + 1) * wealth
        
        total_wealth = sum(wealth_values)
        gini = (2 * cumsum) / (n * total_wealth) - (n + 1) / n
        
        return gini
    
    def get_wealth_distribution_by_role(self, agents: List[Agent]) -> Dict[str, Dict[str, float]]:
        """Get wealth distribution statistics by role.
        
        Args:
            agents: List of all agents
            
        Returns:
            Dict mapping role to {mean, median, total}
        """
        distribution = {}
        
        for role in [Role.KING, Role.KNIGHT, Role.MERCENARY]:
            role_agents = [a for a in agents if a.role == role]
            
            if not role_agents:
                distribution[role.value] = {"mean": 0.0, "median": 0.0, "total": 0}
                continue
            
            wealth_values = sorted([a.wealth_total() for a in role_agents])
            total = sum(wealth_values)
            mean = total / len(wealth_values)
            median = wealth_values[len(wealth_values) // 2]
            
            distribution[role.value] = {
                "mean": mean,
                "median": median,
                "total": total
            }
        
        return distribution
    
    def clear(self) -> None:
        """Clear all collected events and summaries."""
        self.events.clear()
        self.tick_summaries.clear()
    
    def to_dict(self) -> Dict:
        """Convert aggregator state to dictionary.
        
        Returns:
            Dict with events and summaries
        """
        return {
            "events": [e.to_dict() for e in self.events],
            "tick_summaries": {
                tick: summary.to_dict() 
                for tick, summary in self.tick_summaries.items()
            }
        }
