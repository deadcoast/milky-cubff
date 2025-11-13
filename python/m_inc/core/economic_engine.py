"""Economic engine for M|inc tick processing."""

from typing import List, Optional
from .models import Agent, Event, EventType, TickMetrics, TickResult, AgentSnapshot
from .agent_registry import AgentRegistry
from .config import EconomicConfig
from . import economics


class EconomicEngine:
    """Engine for processing M|inc economic ticks.
    
    Orchestrates the tick sequence:
    1. Soup drip (trait emergence)
    2. Trade operations
    3. Retainer payments
    4. Interactions (bribes, raids, defends)
    5. Metrics computation
    """
    
    def __init__(self, registry: AgentRegistry, config: EconomicConfig):
        """Initialize economic engine.
        
        Args:
            registry: Agent registry
            config: Economic configuration
        """
        self.registry = registry
        self.config = config
        self.current_tick = 0
    
    def process_tick(self, tick_num: int) -> TickResult:
        """Process a single economic tick.
        
        Args:
            tick_num: Tick number
            
        Returns:
            TickResult with events, metrics, and agent snapshots
        """
        self.current_tick = tick_num
        events: List[Event] = []
        
        # 1. Soup drip (trait emergence)
        events.extend(self._soup_drip())
        
        # 2. Trade operations
        events.extend(self._execute_trades())
        
        # 3. Retainer payments
        events.extend(self._pay_retainers())
        
        # 4. Interactions (bribes, raids, defends)
        events.extend(self._execute_interactions())
        
        # 5. Clamp non-negative values
        self._clamp_nonnegative()
        
        # 6. Compute metrics
        metrics = self._compute_metrics(events)
        
        # 7. Snapshot agents
        snapshots = self._snapshot_agents()
        
        return TickResult(
            tick_num=tick_num,
            events=events,
            metrics=metrics,
            agent_snapshots=snapshots
        )
    
    def _soup_drip(self) -> List[Event]:
        """Apply soup drip (trait emergence from BFF activity).
        
        Returns:
            List of trait_drip events
        """
        events = []
        
        for agent in self.registry.get_all_agents():
            # Rule: if copy >= 12 and tick % 2 == 0, add +1 copy
            if agent.wealth.copy >= 12 and self.current_tick % 2 == 0:
                agent.add_wealth("copy", 1)
                self.registry.update_agent(agent)
                
                events.append(Event(
                    tick=self.current_tick,
                    type=EventType.TRAIT_DRIP,
                    agent=agent.id,
                    trait="copy",
                    delta=1
                ))
        
        return events
    
    def _execute_trades(self) -> List[Event]:
        """Execute trade operations for all kings.
        
        Returns:
            List of trade events
        """
        events = []
        
        for king in self.registry.get_kings():
            wealth_created = economics.apply_trade(king, self.config)
            
            if wealth_created > 0:
                self.registry.update_agent(king)
                
                events.append(Event(
                    tick=self.current_tick,
                    type=EventType.TRADE,
                    king=king.id,
                    invest=self.config.trade["invest_per_tick"],
                    wealth_created=wealth_created
                ))
        
        return events
    
    def _pay_retainers(self) -> List[Event]:
        """Pay retainers from kings to employed knights.
        
        Returns:
            List of retainer events
        """
        events = []
        
        for knight in self.registry.get_knights():
            if not knight.employer:
                continue
            
            king = self.registry.get_agent(knight.employer)
            if not king:
                continue
            
            if king.currency >= knight.retainer_fee:
                # Transfer retainer
                king.add_currency(-knight.retainer_fee)
                knight.add_currency(knight.retainer_fee)
                
                self.registry.update_agent(king)
                self.registry.update_agent(knight)
                
                events.append(Event(
                    tick=self.current_tick,
                    type=EventType.RETAINER,
                    employer=king.id,
                    knight=knight.id,
                    amount=knight.retainer_fee
                ))
        
        return events
    
    def _execute_interactions(self) -> List[Event]:
        """Execute interactions between mercenaries and kings.
        
        Returns:
            List of interaction events (bribes, defends, raids)
        """
        events = []
        
        # Get all mercenaries in ID order (deterministic)
        mercenaries = sorted(self.registry.get_mercenaries(), key=lambda m: m.id)
        
        for merc in mercenaries:
            if not merc.alive:
                continue
            
            # Pick target king (highest exposed wealth)
            kings = [k for k in self.registry.get_kings() if k.alive]
            if not kings:
                break
            
            king = economics.pick_target_king(kings, self.config)
            
            # Get assigned knights (employer first, then strongest free)
            assigned_knights = self._get_assigned_knights(king)
            
            # Compute raid value
            rv = economics.raid_value(merc, king, assigned_knights, self.config)
            
            # Bribe check
            bribe_threshold = king.bribe_threshold
            
            if bribe_threshold >= rv and king.currency >= bribe_threshold:
                # Successful bribe
                king.add_currency(-bribe_threshold)
                merc.add_currency(bribe_threshold)
                economics.apply_bribe_leakage(king, self.config.bribe_leakage)
                
                self.registry.update_agent(king)
                self.registry.update_agent(merc)
                
                events.append(Event(
                    tick=self.current_tick,
                    type=EventType.BRIBE_ACCEPT,
                    king=king.id,
                    merc=merc.id,
                    amount=bribe_threshold,
                    rv=round(rv, 2),
                    notes="success"
                ))
                continue
            
            elif bribe_threshold >= rv:
                # Insufficient funds
                events.append(Event(
                    tick=self.current_tick,
                    type=EventType.BRIBE_INSUFFICIENT,
                    king=king.id,
                    merc=merc.id,
                    threshold=bribe_threshold
                ))
                # Fall through to contest
            
            # Contest (raid vs defend)
            if not assigned_knights:
                # Unopposed raid
                economics.apply_mirrored_losses(king, merc, self.config)
                
                self.registry.update_agent(king)
                self.registry.update_agent(merc)
                
                events.append(Event(
                    tick=self.current_tick,
                    type=EventType.UNOPPOSED_RAID,
                    king=king.id,
                    merc=merc.id
                ))
            else:
                # Defended raid
                knight = assigned_knights[0]  # One defender per attacker
                
                # Compute win probability
                p_knight = economics.p_knight_win(knight, merc, self.config)
                
                # Compute stake
                stake = economics.stake_amount(knight, merc, self.config)
                
                # Resolve outcome
                knight_wins = economics.resolve_knight_wins(p_knight, knight.id, merc.id)
                
                if knight_wins:
                    # Knight wins
                    knight.add_currency(stake)
                    merc.add_currency(-stake)
                    economics.apply_bounty(knight, merc, bounty_frac=0.07)
                    
                    self.registry.update_agent(knight)
                    self.registry.update_agent(merc)
                    
                    events.append(Event(
                        tick=self.current_tick,
                        type=EventType.DEFEND_WIN,
                        king=king.id,
                        knight=knight.id,
                        merc=merc.id,
                        stake=stake,
                        p_knight=round(p_knight, 3)
                    ))
                else:
                    # Mercenary wins
                    economics.apply_mirrored_losses(king, merc, self.config)
                    knight.add_currency(-stake)
                    if knight.wealth.defend > 0:
                        knight.add_wealth("defend", -1)
                    
                    self.registry.update_agent(king)
                    self.registry.update_agent(knight)
                    self.registry.update_agent(merc)
                    
                    events.append(Event(
                        tick=self.current_tick,
                        type=EventType.DEFEND_LOSS,
                        king=king.id,
                        knight=knight.id,
                        merc=merc.id,
                        stake=stake,
                        p_knight=round(p_knight, 3)
                    ))
        
        return events
    
    def _get_assigned_knights(self, king: Agent) -> List[Agent]:
        """Get knights assigned to defend a king.
        
        Priority: employer knights first, then strongest free knights.
        
        Args:
            king: King to get defenders for
            
        Returns:
            List of assigned knights (currently max 1)
        """
        # Get employed knights
        employed = self.registry.get_employed_knights(king.id)
        
        # Get free knights sorted by defend (descending)
        free = sorted(
            self.registry.get_free_knights(),
            key=lambda k: (-k.wealth.defend, k.id)
        )
        
        # Return employed first, then free (limit to 1 for now)
        all_knights = employed + free
        return all_knights[:1] if all_knights else []
    
    def _clamp_nonnegative(self) -> None:
        """Ensure all currency and wealth values are non-negative."""
        for agent in self.registry.get_all_agents():
            # Clamp currency
            if agent.currency < 0:
                agent.currency = 0
            
            # Clamp wealth traits
            for trait_name in ["compute", "copy", "defend", "raid", "trade", "sense", "adapt"]:
                trait_value = getattr(agent.wealth, trait_name)
                if trait_value < 0:
                    setattr(agent.wealth, trait_name, 0)
            
            self.registry.update_agent(agent)
    
    def _compute_metrics(self, events: List[Event]) -> TickMetrics:
        """Compute metrics for the current tick.
        
        Args:
            events: Events that occurred this tick
            
        Returns:
            TickMetrics with computed values
        """
        agents = self.registry.get_all_agents()
        
        # Compute totals
        wealth_total = sum(agent.wealth_total() for agent in agents)
        currency_total = sum(agent.currency for agent in agents)
        
        # Compute copy score mean
        copy_scores = [agent.wealth.copy for agent in agents]
        copy_score_mean = sum(copy_scores) / len(copy_scores) if copy_scores else 0.0
        
        # Normalize copy score (divide by 20 for 0-1 range approximation)
        copy_score_mean = copy_score_mean / 20.0
        
        # Compute entropy and compression (proxies for now)
        # These would ideally come from BFF soup analysis
        entropy = 6.2 - 0.24 * (self.current_tick * 0.05)
        compression_ratio = 2.5 + (self.current_tick * 0.05)
        
        # Count event types
        bribes_paid = sum(1 for e in events if e.type in [EventType.BRIBE_ACCEPT, EventType.BRIBE_INSUFFICIENT])
        bribes_accepted = sum(1 for e in events if e.type == EventType.BRIBE_ACCEPT)
        raids_attempted = sum(1 for e in events if e.type in [EventType.DEFEND_WIN, EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID])
        raids_won_by_merc = sum(1 for e in events if e.type in [EventType.DEFEND_LOSS, EventType.UNOPPOSED_RAID])
        raids_won_by_knight = sum(1 for e in events if e.type == EventType.DEFEND_WIN)
        
        return TickMetrics(
            entropy=max(0.0, entropy),
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
    
    def _snapshot_agents(self) -> List[AgentSnapshot]:
        """Create snapshots of all agents.
        
        Returns:
            List of agent snapshots
        """
        return [
            AgentSnapshot.from_agent(agent)
            for agent in self.registry.get_all_agents()
        ]
