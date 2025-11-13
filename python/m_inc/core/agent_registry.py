"""Agent registry for managing M|inc agents and their roles."""

import random
from typing import Dict, List, Optional
from .models import Agent, WealthTraits, Role
from .config import RegistryConfig


class AgentRegistry:
    """Registry for managing agents and their economic state.
    
    Handles:
    - Role assignment based on configured ratios
    - Agent initialization with role-specific attributes
    - Agent lookup and filtering
    - State persistence and updates
    """
    
    def __init__(self, config: RegistryConfig, seed: Optional[int] = None):
        """Initialize agent registry.
        
        Args:
            config: Registry configuration
            seed: Random seed for deterministic role assignment
        """
        self.config = config
        self.agents: Dict[str, Agent] = {}
        self._tape_to_agent: Dict[int, str] = {}
        self._role_counters = {"K": 0, "N": 0, "M": 0}
        self.rng = random.Random(seed)
    
    def assign_roles(self, tape_ids: List[int]) -> None:
        """Assign roles to tape IDs based on configured ratios.
        
        Args:
            tape_ids: List of BFF tape IDs to assign roles to
        """
        num_tapes = len(tape_ids)
        
        # Calculate number of each role
        num_kings = int(num_tapes * self.config.role_ratios["king"])
        num_knights = int(num_tapes * self.config.role_ratios["knight"])
        num_mercs = num_tapes - num_kings - num_knights  # Remainder are mercenaries
        
        # Create role assignments
        roles = (
            [Role.KING] * num_kings +
            [Role.KNIGHT] * num_knights +
            [Role.MERCENARY] * num_mercs
        )
        
        # Shuffle for random assignment
        self.rng.shuffle(roles)
        
        # Assign roles to tapes
        for tape_id, role in zip(tape_ids, roles):
            self._create_agent(tape_id, role)
    
    def _create_agent(self, tape_id: int, role: Role) -> Agent:
        """Create a new agent with the given role.
        
        Args:
            tape_id: BFF tape ID
            role: Agent role
            
        Returns:
            Created Agent instance
        """
        # Generate agent ID
        role_prefix = {
            Role.KING: "K",
            Role.KNIGHT: "N",
            Role.MERCENARY: "M"
        }[role]
        
        agent_num = self._role_counters[role_prefix]
        self._role_counters[role_prefix] += 1
        agent_id = f"{role_prefix}-{agent_num:02d}"
        
        # Initialize currency
        currency_range = self.config.initial_currency.get(role.value, (0, 100))
        currency = self.rng.randint(currency_range[0], currency_range[1])
        
        # Initialize wealth traits
        wealth = self._initialize_wealth(role)
        
        # Initialize role-specific attributes
        employer = None
        retainer_fee = 0
        bribe_threshold = 0
        
        if role == Role.KNIGHT:
            # Knights will be assigned employers later
            retainer_fee = self.rng.randint(20, 30)
        elif role == Role.KING:
            # Kings have bribe thresholds
            bribe_threshold = self.rng.randint(300, 500)
        
        # Create agent
        agent = Agent(
            id=agent_id,
            tape_id=tape_id,
            role=role,
            currency=currency,
            wealth=wealth,
            employer=employer,
            retainer_fee=retainer_fee,
            bribe_threshold=bribe_threshold,
            alive=True
        )
        
        # Register agent
        self.agents[agent_id] = agent
        self._tape_to_agent[tape_id] = agent_id
        
        return agent
    
    def _initialize_wealth(self, role: Role) -> WealthTraits:
        """Initialize wealth traits for a role.
        
        Args:
            role: Agent role
            
        Returns:
            WealthTraits with role-appropriate values
        """
        wealth_ranges = self.config.initial_wealth.get(role.value, {})
        
        traits = {}
        for trait_name in ["compute", "copy", "defend", "raid", "trade", "sense", "adapt"]:
            trait_range = wealth_ranges.get(trait_name, (0, 5))
            traits[trait_name] = self.rng.randint(trait_range[0], trait_range[1])
        
        return WealthTraits(**traits)
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID.
        
        Args:
            agent_id: Agent identifier (e.g., "K-01")
            
        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_agent_by_tape(self, tape_id: int) -> Optional[Agent]:
        """Get an agent by their tape ID.
        
        Args:
            tape_id: BFF tape ID
            
        Returns:
            Agent instance or None if not found
        """
        agent_id = self._tape_to_agent.get(tape_id)
        if agent_id:
            return self.agents.get(agent_id)
        return None
    
    def get_agents_by_role(self, role: Role) -> List[Agent]:
        """Get all agents with a specific role.
        
        Args:
            role: Role to filter by
            
        Returns:
            List of agents with the specified role
        """
        return [agent for agent in self.agents.values() if agent.role == role]
    
    def get_all_agents(self) -> List[Agent]:
        """Get all agents.
        
        Returns:
            List of all agents
        """
        return list(self.agents.values())
    
    def update_agent(self, agent: Agent) -> None:
        """Update an agent's state in the registry.
        
        Args:
            agent: Agent with updated state
        """
        if agent.id in self.agents:
            self.agents[agent.id] = agent
    
    def assign_knight_employers(self) -> None:
        """Assign knights to king employers.
        
        Distributes knights evenly among kings. Knights without employers
        remain available as free agents.
        """
        kings = self.get_agents_by_role(Role.KING)
        knights = self.get_agents_by_role(Role.KNIGHT)
        
        if not kings:
            return
        
        # Shuffle knights for random assignment
        knights_copy = knights.copy()
        self.rng.shuffle(knights_copy)
        
        # Assign knights to kings in round-robin fashion
        for i, knight in enumerate(knights_copy):
            king = kings[i % len(kings)]
            knight.employer = king.id
            self.update_agent(knight)
    
    def mutate_roles(self, mutation_rate: Optional[float] = None) -> List[tuple[str, Role, Role]]:
        """Randomly mutate agent roles.
        
        Args:
            mutation_rate: Probability of role mutation (uses config if None)
            
        Returns:
            List of (agent_id, old_role, new_role) tuples for mutated agents
        """
        if mutation_rate is None:
            mutation_rate = self.config.mutation_rate
        
        if mutation_rate <= 0:
            return []
        
        mutations = []
        all_roles = [Role.KING, Role.KNIGHT, Role.MERCENARY]
        
        for agent in self.agents.values():
            if self.rng.random() < mutation_rate:
                old_role = agent.role
                # Choose a different role
                new_role = self.rng.choice([r for r in all_roles if r != old_role])
                
                # Update role
                agent.role = new_role
                
                # Reset role-specific attributes
                if new_role == Role.KNIGHT:
                    agent.retainer_fee = self.rng.randint(20, 30)
                    agent.bribe_threshold = 0
                elif new_role == Role.KING:
                    agent.bribe_threshold = self.rng.randint(300, 500)
                    agent.employer = None
                    agent.retainer_fee = 0
                else:  # Mercenary
                    agent.employer = None
                    agent.retainer_fee = 0
                    agent.bribe_threshold = 0
                
                self.update_agent(agent)
                mutations.append((agent.id, old_role, new_role))
        
        return mutations
    
    def get_kings(self) -> List[Agent]:
        """Get all king agents."""
        return self.get_agents_by_role(Role.KING)
    
    def get_knights(self) -> List[Agent]:
        """Get all knight agents."""
        return self.get_agents_by_role(Role.KNIGHT)
    
    def get_mercenaries(self) -> List[Agent]:
        """Get all mercenary agents."""
        return self.get_agents_by_role(Role.MERCENARY)
    
    def get_employed_knights(self, king_id: str) -> List[Agent]:
        """Get all knights employed by a specific king.
        
        Args:
            king_id: King agent ID
            
        Returns:
            List of knights employed by the king
        """
        return [
            knight for knight in self.get_knights()
            if knight.employer == king_id
        ]
    
    def get_free_knights(self) -> List[Agent]:
        """Get all knights without an employer.
        
        Returns:
            List of unemployed knights
        """
        return [
            knight for knight in self.get_knights()
            if not knight.employer
        ]
    
    def get_stats(self) -> Dict[str, any]:
        """Get registry statistics.
        
        Returns:
            Dict with counts and distributions
        """
        total = len(self.agents)
        kings = len(self.get_kings())
        knights = len(self.get_knights())
        mercs = len(self.get_mercenaries())
        
        total_currency = sum(agent.currency for agent in self.agents.values())
        total_wealth = sum(agent.wealth_total() for agent in self.agents.values())
        
        return {
            "total_agents": total,
            "kings": kings,
            "knights": knights,
            "mercenaries": mercs,
            "total_currency": total_currency,
            "total_wealth": total_wealth,
            "avg_currency": total_currency / total if total > 0 else 0,
            "avg_wealth": total_wealth / total if total > 0 else 0
        }
    
    def to_dict(self) -> Dict[str, any]:
        """Convert registry to dictionary representation.
        
        Returns:
            Dict with all agents and metadata
        """
        return {
            "agents": [agent.to_dict() for agent in self.agents.values()],
            "stats": self.get_stats()
        }
    
    def from_dict(self, data: Dict[str, any]) -> None:
        """Load registry from dictionary representation.
        
        Args:
            data: Dict with agents data
        """
        self.agents.clear()
        self._tape_to_agent.clear()
        
        for agent_data in data.get("agents", []):
            agent = Agent.from_dict(agent_data)
            self.agents[agent.id] = agent
            self._tape_to_agent[agent.tape_id] = agent.id
            
            # Update role counters
            role_prefix = agent.id[0]
            if role_prefix in self._role_counters:
                agent_num = int(agent.id.split("-")[1])
                self._role_counters[role_prefix] = max(
                    self._role_counters[role_prefix],
                    agent_num + 1
                )
