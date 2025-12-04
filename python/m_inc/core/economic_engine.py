"""Economic engine for M|inc tick processing."""

import ast
import operator
from typing import List, Dict, Any
from .models import Agent, Event, EventType, TickMetrics, TickResult, AgentSnapshot, Role
from .agent_registry import AgentRegistry
from .config import EconomicConfig, TraitEmergenceConfig
from . import economics


class SafeExpressionEvaluator:
    """Safe expression evaluator using AST parsing.

    Only allows:
    - Numeric literals
    - Variable lookups from a whitelist
    - Arithmetic operators (+, -, *, /, //, %, **)
    - Comparison operators (==, !=, <, <=, >, >=)
    - Boolean operators (and, or, not)

    Does NOT allow:
    - Function calls
    - Attribute access
    - Subscript access
    - Lambda expressions
    - List/dict comprehensions
    """

    SAFE_BINARY_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    SAFE_UNARY_OPS = {
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        ast.Not: operator.not_,
    }

    SAFE_COMPARE_OPS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
    }

    def __init__(self, allowed_vars: set):
        """Initialize evaluator with allowed variable names.

        Args:
            allowed_vars: Set of variable names that can be referenced
        """
        self.allowed_vars = allowed_vars

    def evaluate(self, expression: str, context: Dict[str, Any]) -> Any:
        """Safely evaluate an expression.

        Args:
            expression: Expression string to evaluate
            context: Dictionary of variable values

        Returns:
            Evaluated result

        Raises:
            ValueError: If expression contains unsafe operations
            NameError: If expression references undefined variables
        """
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")

        return self._eval_node(tree.body, context)

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """Recursively evaluate an AST node.

        Args:
            node: AST node to evaluate
            context: Variable context

        Returns:
            Evaluated result
        """
        if isinstance(node, ast.Constant):
            # Allow numeric and boolean constants only
            if isinstance(node.value, (int, float, bool, type(None))):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")

        elif isinstance(node, ast.Name):
            if node.id not in self.allowed_vars:
                raise ValueError(f"Variable not allowed: {node.id}")
            if node.id not in context:
                raise NameError(f"Undefined variable: {node.id}")
            return context[node.id]

        elif isinstance(node, ast.BinOp):
            if type(node.op) not in self.SAFE_BINARY_OPS:
                raise ValueError(f"Operator not allowed: {type(node.op).__name__}")
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            return self.SAFE_BINARY_OPS[type(node.op)](left, right)

        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in self.SAFE_UNARY_OPS:
                raise ValueError(f"Unary operator not allowed: {type(node.op).__name__}")
            operand = self._eval_node(node.operand, context)
            return self.SAFE_UNARY_OPS[type(node.op)](operand)

        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                if type(op) not in self.SAFE_COMPARE_OPS:
                    raise ValueError(f"Comparison not allowed: {type(op).__name__}")
                right = self._eval_node(comparator, context)
                if not self.SAFE_COMPARE_OPS[type(op)](left, right):
                    return False
                left = right
            return True

        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for value in node.values:
                    if not self._eval_node(value, context):
                        return False
                return True
            elif isinstance(node.op, ast.Or):
                for value in node.values:
                    if self._eval_node(value, context):
                        return True
                return False
            else:
                raise ValueError(f"Boolean operator not allowed: {type(node.op).__name__}")

        else:
            # Reject all other node types (Call, Attribute, Subscript, Lambda, etc.)
            raise ValueError(f"Expression type not allowed: {type(node).__name__}")


class EconomicEngine:
    """Engine for processing M|inc economic ticks.
    
    Orchestrates the tick sequence:
    1. Soup drip (trait emergence)
    2. Trade operations
    3. Retainer payments
    4. Raid/defend interactions
    
    All operations are deterministic given the same initial state.
    """
    
    def __init__(self, registry: AgentRegistry, config: EconomicConfig,
                 trait_config: TraitEmergenceConfig):
        """Initialize economic engine.
        
        Args:
            registry: Agent registry managing all agents
            config: Economic configuration parameters
            trait_config: Trait emergence configuration
        """
        self.registry = registry
        self.config = config
        self.trait_config = trait_config
    
    def process_tick(self, tick_num: int) -> TickResult:
        """Process a complete economic tick.
        
        Executes the tick sequence:
        1. Soup drip (trait emergence)
        2. Trade operations
        3. Retainer payments
        4. Raid/defend interactions
        
        Args:
            tick_num: Current tick number (1-indexed)
            
        Returns:
            TickResult with events, metrics, and agent snapshots
        """
        events: List[Event] = []
        
        # Execute tick sequence
        events.extend(self._soup_drip(tick_num))
        events.extend(self._execute_trades(tick_num))
        events.extend(self._pay_retainers(tick_num))
        events.extend(self._execute_interactions(tick_num))
        
        # Compute metrics and snapshots
        metrics = self._compute_metrics()
        snapshots = self._snapshot_agents()
        
        return TickResult(
            tick_num=tick_num,
            events=events,
            metrics=metrics,
            agent_snapshots=snapshots
        )
    
    def _soup_drip(self, tick_num: int) -> List[Event]:
        """Apply trait emergence (soup drip) rules.

        Checks trait emergence conditions and applies deltas.
        Default rule: if copy >= 12 and tick is even, increment copy by 1.

        Args:
            tick_num: Current tick number

        Returns:
            List of trait_drip events
        """
        events: List[Event] = []

        if not self.trait_config.enabled:
            return events

        # Define allowed variables for condition evaluation
        allowed_vars = {
            "copy", "compute", "defend", "raid", "trade",
            "sense", "adapt", "tick", "currency"
        }
        evaluator = SafeExpressionEvaluator(allowed_vars)

        for rule in self.trait_config.rules:
            condition = rule.get("condition", "")
            delta = rule.get("delta", {})

            if not condition:
                continue

            # Parse and evaluate condition for each agent
            for agent in self.registry.get_all_agents():
                # Build evaluation context
                context = {
                    "copy": agent.wealth.copy,
                    "compute": agent.wealth.compute,
                    "defend": agent.wealth.defend,
                    "raid": agent.wealth.raid,
                    "trade": agent.wealth.trade,
                    "sense": agent.wealth.sense,
                    "adapt": agent.wealth.adapt,
                    "tick": tick_num,
                    "currency": agent.currency
                }

                # Evaluate condition safely using AST-based evaluator
                try:
                    if evaluator.evaluate(condition, context):
                        # Apply delta
                        for trait_name, amount in delta.items():
                            agent.add_wealth(trait_name, amount)

                            # Record event
                            events.append(Event(
                                tick=tick_num,
                                type=EventType.TRAIT_DRIP,
                                agent=agent.id,
                                trait=trait_name,
                                delta=amount,
                                notes=f"drip: {trait_name}+{amount}"
                            ))

                        # Update agent in registry
                        self.registry.update_agent(agent)
                except (ValueError, NameError) as e:
                    # Log and skip invalid/unsafe conditions
                    import logging
                    logging.warning(f"Invalid trait emergence condition '{condition}': {e}")

        return events
    
    def _execute_trades(self, tick_num: int) -> List[Event]:
        """Execute trade operations for kings.
        
        Each king can invest 100 currency to create 5 wealth units
        (3 defend, 2 trade) if they have sufficient funds.
        
        Args:
            tick_num: Current tick number
            
        Returns:
            List of trade events
        """
        events: List[Event] = []
        
        kings = self.registry.get_kings()
        invest_amount = self.config.trade["invest_per_tick"]
        
        for king in kings:
            if king.currency >= invest_amount:
                # Apply trade
                wealth_created = economics.apply_trade(king, self.config)
                
                if wealth_created > 0:
                    # Record event
                    events.append(Event(
                        tick=tick_num,
                        type=EventType.TRADE,
                        king=king.id,
                        invest=invest_amount,
                        wealth_created=wealth_created,
                        notes=f"invested {invest_amount}, created {wealth_created} wealth"
                    ))
                    
                    # Update agent in registry
                    self.registry.update_agent(king)
        
        return events
    
    def _pay_retainers(self, tick_num: int) -> List[Event]:
        """Pay retainer fees from kings to employed knights.
        
        For each knight with an employer, attempt to transfer the
        retainer fee from the employer king to the knight.
        
        Args:
            tick_num: Current tick number
            
        Returns:
            List of retainer events
        """
        events: List[Event] = []
        
        knights = self.registry.get_knights()
        
        for knight in knights:
            if knight.employer:
                king = self.registry.get_agent(knight.employer)
                
                if king and king.currency >= knight.retainer_fee:
                    # Transfer retainer
                    king.add_currency(-knight.retainer_fee)
                    knight.add_currency(knight.retainer_fee)
                    
                    # Record event
                    events.append(Event(
                        tick=tick_num,
                        type=EventType.RETAINER,
                        king=king.id,
                        knight=knight.id,
                        employer=king.id,
                        amount=knight.retainer_fee,
                        notes=f"retainer payment: {knight.retainer_fee}"
                    ))
                    
                    # Update agents in registry
                    self.registry.update_agent(king)
                    self.registry.update_agent(knight)
        
        return events
    
    def _execute_interactions(self, tick_num: int) -> List[Event]:
        """Execute raid/defend interactions.
        
        For each mercenary (in ID order):
        1. Select target king (highest exposed wealth)
        2. Assign defending knights (employer first, then strongest free)
        3. Evaluate bribe
        4. If bribe fails, resolve defend contest
        
        Args:
            tick_num: Current tick number
            
        Returns:
            List of interaction events (bribe, defend, raid)
        """
        events: List[Event] = []
        
        mercenaries = sorted(self.registry.get_mercenaries(), key=lambda m: m.id)
        kings = self.registry.get_kings()
        
        if not kings:
            return events
        
        for merc in mercenaries:
            # Select target king (highest exposed wealth)
            target_king = economics.pick_target_king(kings, self.config)
            
            # Get defending knights
            defending_knights = self._assign_defending_knights(target_king)
            
            # Compute raid value
            rv = economics.raid_value(merc, target_king, defending_knights, self.config)
            
            # Evaluate bribe
            threshold = target_king.bribe_threshold
            
            if threshold >= rv and target_king.currency >= threshold:
                # Bribe succeeds
                target_king.add_currency(-threshold)
                merc.add_currency(threshold)
                
                # Apply wealth leakage to king
                economics.apply_bribe_leakage(target_king, self.config.bribe_leakage)
                
                # Record event
                events.append(Event(
                    tick=tick_num,
                    type=EventType.BRIBE_ACCEPT,
                    king=target_king.id,
                    merc=merc.id,
                    amount=threshold,
                    rv=rv,
                    notes="success"
                ))
                
                # Update agents
                self.registry.update_agent(target_king)
                self.registry.update_agent(merc)
                
            elif threshold >= rv:
                # Bribe would work but king lacks funds
                events.append(Event(
                    tick=tick_num,
                    type=EventType.BRIBE_INSUFFICIENT,
                    king=target_king.id,
                    merc=merc.id,
                    threshold=threshold,
                    rv=rv,
                    notes="insufficient funds"
                ))
                
                # Proceed to raid/defend
                events.extend(self._resolve_defend(tick_num, target_king, merc, defending_knights))
                
            else:
                # Bribe threshold too low, proceed to raid/defend
                events.extend(self._resolve_defend(tick_num, target_king, merc, defending_knights))
        
        return events
    
    def _assign_defending_knights(self, king: Agent) -> List[Agent]:
        """Assign knights to defend a king.
        
        Priority:
        1. Employed knights (knights with this king as employer)
        2. Free knights (strongest by defend + sense + adapt)
        
        Args:
            king: King being defended
            
        Returns:
            List of defending knights (may be empty)
        """
        defending = []
        
        # Get employed knights
        employed = self.registry.get_employed_knights(king.id)
        defending.extend(employed)
        
        # Get free knights (not employed by anyone)
        free_knights = self.registry.get_free_knights()
        
        # Sort free knights by defensive strength
        free_knights_sorted = sorted(
            free_knights,
            key=lambda k: -(k.wealth.defend + k.wealth.sense + k.wealth.adapt)
        )
        
        # Add strongest free knight if available
        if free_knights_sorted:
            defending.append(free_knights_sorted[0])
        
        return defending
    
    def _resolve_defend(self, tick_num: int, king: Agent, merc: Agent,
                       knights: List[Agent]) -> List[Event]:
        """Resolve a defend contest between knight(s) and mercenary.
        
        If no knights available, mercenary wins unopposed.
        Otherwise, strongest knight defends and outcome is determined
        by p_knight_win probability with deterministic tie-breaking.
        
        Args:
            tick_num: Current tick number
            king: King being raided
            merc: Mercenary raiding
            knights: List of defending knights
            
        Returns:
            List of defend events
        """
        events: List[Event] = []
        
        if not knights:
            # Unopposed raid - mercenary wins
            economics.apply_mirrored_losses(king, merc, self.config)
            
            events.append(Event(
                tick=tick_num,
                type=EventType.UNOPPOSED_RAID,
                king=king.id,
                merc=merc.id,
                notes="no defenders"
            ))
            
            # Update agents
            self.registry.update_agent(king)
            self.registry.update_agent(merc)
            
            return events
        
        # Select defending knight (first in list, which is employer or strongest free)
        knight = knights[0]
        
        # Compute win probability
        p_knight = economics.p_knight_win(knight, merc, self.config)
        
        # Compute stake
        stake = economics.stake_amount(knight, merc, self.config)
        
        # Resolve deterministically
        knight_wins = economics.resolve_knight_wins(p_knight, knight.id, merc.id)
        
        if knight_wins:
            # Knight wins
            # Transfer stake from merc to knight
            merc.add_currency(-stake)
            knight.add_currency(stake)
            
            # Apply bounty (7% of merc's raid and adapt)
            economics.apply_bounty(knight, merc, bounty_frac=0.07)
            
            events.append(Event(
                tick=tick_num,
                type=EventType.DEFEND_WIN,
                king=king.id,
                knight=knight.id,
                merc=merc.id,
                stake=stake,
                p_knight=p_knight,
                notes=f"knight wins (p={p_knight:.3f})"
            ))
            
            # Update agents
            self.registry.update_agent(knight)
            self.registry.update_agent(merc)
            
        else:
            # Mercenary wins
            # Transfer stake from knight to merc
            knight.add_currency(-stake)
            merc.add_currency(stake)
            
            # Apply mirrored losses from king to merc
            economics.apply_mirrored_losses(king, merc, self.config)
            
            events.append(Event(
                tick=tick_num,
                type=EventType.DEFEND_LOSS,
                king=king.id,
                knight=knight.id,
                merc=merc.id,
                stake=stake,
                p_knight=p_knight,
                notes=f"merc wins (p={p_knight:.3f})"
            ))
            
            # Update agents
            self.registry.update_agent(king)
            self.registry.update_agent(knight)
            self.registry.update_agent(merc)
        
        return events
    
    def _compute_metrics(self) -> TickMetrics:
        """Compute tick-level metrics.
        
        Computes:
        - Total wealth and currency
        - Mean copy score
        - Entropy (placeholder - requires BFF trace data)
        - Compression ratio (placeholder - requires BFF trace data)
        - Event counts (computed from events in process_tick)
        
        Returns:
            TickMetrics with computed values
        """
        agents = self.registry.get_all_agents()
        
        # Compute totals
        wealth_total = sum(agent.wealth_total() for agent in agents)
        currency_total = sum(agent.currency for agent in agents)
        
        # Compute mean copy score
        copy_scores = [agent.wealth.copy for agent in agents]
        copy_score_mean = sum(copy_scores) / len(copy_scores) if copy_scores else 0.0
        
        # Placeholder values for BFF-specific metrics
        # These would be computed from BFF trace data in full integration
        entropy = 0.0
        compression_ratio = 0.0
        
        return TickMetrics(
            entropy=entropy,
            compression_ratio=compression_ratio,
            copy_score_mean=copy_score_mean,
            wealth_total=wealth_total,
            currency_total=currency_total,
            bribes_paid=0,  # Will be updated by caller
            bribes_accepted=0,  # Will be updated by caller
            raids_attempted=0,  # Will be updated by caller
            raids_won_by_merc=0,  # Will be updated by caller
            raids_won_by_knight=0  # Will be updated by caller
        )
    
    def _snapshot_agents(self) -> List[AgentSnapshot]:
        """Capture current state of all agents.
        
        Returns:
            List of AgentSnapshot objects
        """
        agents = self.registry.get_all_agents()
        return [AgentSnapshot.from_agent(agent) for agent in agents]
