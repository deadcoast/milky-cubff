"""
M|inc - Mercenaries Incorporated Economic Layer for CuBFF

This package provides an economic incentive system layered on top of the BFF
(Brainfuck Forth) self-replicating soup experiment. It tracks agents with roles
(Kings, Knights, Mercenaries) and simulates economic interactions including
bribes, raids, defends, trades, and retainers.

Version: 0.1.1
"""

__version__ = "0.1.1"
__author__ = "CuBFF M|inc Team"

from .core.models import Agent, WealthTraits, Role, Event, EventType
from .core.agent_registry import AgentRegistry
from .core.economic_engine import EconomicEngine

__all__ = [
    "Agent",
    "WealthTraits",
    "Role",
    "Event",
    "EventType",
    "AgentRegistry",
    "EconomicEngine",
]
