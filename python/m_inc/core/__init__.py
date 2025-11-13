"""Core M|inc components: models, engine, registry, and configuration."""

from .models import Agent, WealthTraits, Role, Event, EventType, TickMetrics, TickResult, AgentSnapshot
from .agent_registry import AgentRegistry
from .economic_engine import EconomicEngine
from .config import ConfigLoader, EconomicConfig, MIncConfig
from . import economics

__all__ = [
    "Agent",
    "WealthTraits",
    "Role",
    "Event",
    "EventType",
    "TickMetrics",
    "TickResult",
    "AgentSnapshot",
    "AgentRegistry",
    "EconomicEngine",
    "ConfigLoader",
    "EconomicConfig",
    "MIncConfig",
    "economics",
]
