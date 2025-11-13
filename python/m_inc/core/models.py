"""Core data models for M|inc economic system."""

from dataclasses import dataclass, field, fields, astuple
from enum import Enum
from typing import Optional, Dict, Any


class Role(Enum):
    """Agent roles in the M|inc economic system."""
    KING = "king"
    KNIGHT = "knight"
    MERCENARY = "mercenary"


class EventType(Enum):
    """Types of economic events that can occur."""
    TRAIT_DRIP = "trait_drip"
    TRADE = "trade"
    RETAINER = "retainer"
    BRIBE_ACCEPT = "bribe_accept"
    BRIBE_INSUFFICIENT = "bribe_insufficient_funds"
    DEFEND_WIN = "defend_win"
    DEFEND_LOSS = "defend_loss"
    UNOPPOSED_RAID = "unopposed_raid"


@dataclass
class WealthTraits:
    """Seven wealth traits representing agent capabilities.
    
    All traits are non-negative integers. Total wealth is the sum of all traits.
    """
    compute: int = 0
    copy: int = 0
    defend: int = 0
    raid: int = 0
    trade: int = 0
    sense: int = 0
    adapt: int = 0
    
    def __post_init__(self) -> None:
        """Validate that all traits are non-negative."""
        for trait_field in fields(self):
            value = getattr(self, trait_field.name)
            if value < 0:
                raise ValueError(f"Trait {trait_field.name} cannot be negative: {value}")
    
    def total(self) -> int:
        """Return the sum of all wealth traits."""
        return sum(astuple(self))
    
    def scale(self, factor: float) -> None:
        """Scale all traits by a factor (e.g., for wealth leakage).
        
        Args:
            factor: Scaling factor (0.0 to 1.0 for reduction)
        """
        for trait_field in fields(self):
            current = getattr(self, trait_field.name)
            new_value = int(current * factor)
            setattr(self, trait_field.name, max(0, new_value))
    
    def add(self, trait_name: str, amount: int) -> None:
        """Add (or subtract if negative) to a specific trait.
        
        Args:
            trait_name: Name of the trait to modify
            amount: Amount to add (can be negative)
        """
        if not hasattr(self, trait_name):
            raise ValueError(f"Unknown trait: {trait_name}")
        current = getattr(self, trait_name)
        setattr(self, trait_name, max(0, current + amount))
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary representation."""
        return {
            "compute": self.compute,
            "copy": self.copy,
            "defend": self.defend,
            "raid": self.raid,
            "trade": self.trade,
            "sense": self.sense,
            "adapt": self.adapt,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "WealthTraits":
        """Create WealthTraits from dictionary."""
        return cls(
            compute=data.get("compute", 0),
            copy=data.get("copy", 0),
            defend=data.get("defend", 0),
            raid=data.get("raid", 0),
            trade=data.get("trade", 0),
            sense=data.get("sense", 0),
            adapt=data.get("adapt", 0),
        )


@dataclass
class Agent:
    """An agent in the M|inc economic system.
    
    Agents have roles (King, Knight, Mercenary) and economic attributes
    (currency, wealth traits). They participate in economic interactions.
    """
    id: str
    tape_id: int
    role: Role
    currency: int
    wealth: WealthTraits
    employer: Optional[str] = None
    retainer_fee: int = 0
    bribe_threshold: int = 0
    alive: bool = True
    
    def __post_init__(self) -> None:
        """Validate agent state."""
        if self.currency < 0:
            raise ValueError(f"Currency cannot be negative: {self.currency}")
        if self.retainer_fee < 0:
            raise ValueError(f"Retainer fee cannot be negative: {self.retainer_fee}")
        if self.bribe_threshold < 0:
            raise ValueError(f"Bribe threshold cannot be negative: {self.bribe_threshold}")
    
    def wealth_total(self) -> int:
        """Return total wealth across all traits."""
        return self.wealth.total()
    
    def add_currency(self, amount: int) -> None:
        """Add currency (can be negative for deductions).
        
        Args:
            amount: Amount to add (negative for deduction)
        """
        self.currency = max(0, self.currency + amount)
    
    def add_wealth(self, trait_name: str, amount: int) -> None:
        """Add to a specific wealth trait.
        
        Args:
            trait_name: Name of the trait to modify
            amount: Amount to add (can be negative)
        """
        self.wealth.add(trait_name, amount)
    
    def scale_wealth(self, factor: float) -> None:
        """Scale all wealth traits by a factor.
        
        Args:
            factor: Scaling factor (0.0 to 1.0 for reduction)
        """
        self.wealth.scale(factor)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "tape_id": self.tape_id,
            "role": self.role.value,
            "currency": self.currency,
            "wealth": self.wealth.to_dict(),
            "employer": self.employer,
            "retainer_fee": self.retainer_fee,
            "bribe_threshold": self.bribe_threshold,
            "alive": self.alive,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        """Create Agent from dictionary."""
        return cls(
            id=data["id"],
            tape_id=data["tape_id"],
            role=Role(data["role"]),
            currency=data["currency"],
            wealth=WealthTraits.from_dict(data["wealth"]),
            employer=data.get("employer"),
            retainer_fee=data.get("retainer_fee", 0),
            bribe_threshold=data.get("bribe_threshold", 0),
            alive=data.get("alive", True),
        )


@dataclass
class Event:
    """An economic event that occurred during a tick.
    
    Events record interactions between agents (bribes, raids, defends, etc.)
    and system operations (trades, retainers, trait drips).
    """
    tick: int
    type: EventType
    king: Optional[str] = None
    knight: Optional[str] = None
    merc: Optional[str] = None
    amount: Optional[int] = None
    stake: Optional[int] = None
    p_knight: Optional[float] = None
    notes: Optional[str] = None
    # Additional fields for specific event types
    trait: Optional[str] = None  # for trait_drip
    delta: Optional[int] = None  # for trait_drip
    invest: Optional[int] = None  # for trade
    wealth_created: Optional[int] = None  # for trade
    rv: Optional[float] = None  # for bribe (raid value)
    threshold: Optional[int] = None  # for bribe_insufficient
    employer: Optional[str] = None  # for retainer
    agent: Optional[str] = None  # for trait_drip
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "tick": self.tick,
            "type": self.type.value,
        }
        
        # Add optional fields if present
        optional_fields = [
            "king", "knight", "merc", "amount", "stake", "p_knight", "notes",
            "trait", "delta", "invest", "wealth_created", "rv", "threshold",
            "employer", "agent"
        ]
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create Event from dictionary."""
        return cls(
            tick=data["tick"],
            type=EventType(data["type"]),
            king=data.get("king"),
            knight=data.get("knight"),
            merc=data.get("merc"),
            amount=data.get("amount"),
            stake=data.get("stake"),
            p_knight=data.get("p_knight"),
            notes=data.get("notes"),
            trait=data.get("trait"),
            delta=data.get("delta"),
            invest=data.get("invest"),
            wealth_created=data.get("wealth_created"),
            rv=data.get("rv"),
            threshold=data.get("threshold"),
            employer=data.get("employer"),
            agent=data.get("agent"),
        )


@dataclass
class TickMetrics:
    """Metrics computed for a single tick."""
    entropy: float
    compression_ratio: float
    copy_score_mean: float
    wealth_total: int
    currency_total: int
    bribes_paid: int = 0
    bribes_accepted: int = 0
    raids_attempted: int = 0
    raids_won_by_merc: int = 0
    raids_won_by_knight: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "entropy": round(self.entropy, 3),
            "compression_ratio": round(self.compression_ratio, 3),
            "copy_score_mean": round(self.copy_score_mean, 3),
            "wealth_total": self.wealth_total,
            "currency_total": self.currency_total,
            "bribes_paid": self.bribes_paid,
            "bribes_accepted": self.bribes_accepted,
            "raids_attempted": self.raids_attempted,
            "raids_won_by_merc": self.raids_won_by_merc,
            "raids_won_by_knight": self.raids_won_by_knight,
        }


@dataclass
class AgentSnapshot:
    """Snapshot of an agent's state at a specific tick."""
    id: str
    role: str
    currency: int
    wealth: Dict[str, int]
    
    @classmethod
    def from_agent(cls, agent: Agent) -> "AgentSnapshot":
        """Create snapshot from an Agent."""
        return cls(
            id=agent.id,
            role=agent.role.value,
            currency=agent.currency,
            wealth=agent.wealth.to_dict(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "role": self.role,
            "currency": self.currency,
            "wealth": self.wealth,
        }


@dataclass
class TickResult:
    """Result of processing a single tick."""
    tick_num: int
    events: list[Event]
    metrics: TickMetrics
    agent_snapshots: list[AgentSnapshot]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "tick": self.tick_num,
            "metrics": self.metrics.to_dict(),
            "agents": [snapshot.to_dict() for snapshot in self.agent_snapshots],
        }
