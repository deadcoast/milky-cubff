"""Pydantic schemas for validation of M|inc data structures."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class RoleSchema(str, Enum):
    """Agent role schema."""
    KING = "king"
    KNIGHT = "knight"
    MERCENARY = "mercenary"


class EventTypeSchema(str, Enum):
    """Event type schema."""
    TRAIT_DRIP = "trait_drip"
    TRADE = "trade"
    RETAINER = "retainer"
    BRIBE_ACCEPT = "bribe_accept"
    BRIBE_INSUFFICIENT = "bribe_insufficient_funds"
    DEFEND_WIN = "defend_win"
    DEFEND_LOSS = "defend_loss"
    UNOPPOSED_RAID = "unopposed_raid"


class WealthTraitsSchema(BaseModel):
    """Schema for wealth traits validation."""
    compute: int = Field(ge=0, description="Compute trait (non-negative)")
    copy: int = Field(ge=0, description="Copy trait (non-negative)")
    defend: int = Field(ge=0, description="Defend trait (non-negative)")
    raid: int = Field(ge=0, description="Raid trait (non-negative)")
    trade: int = Field(ge=0, description="Trade trait (non-negative)")
    sense: int = Field(ge=0, description="Sense trait (non-negative)")
    adapt: int = Field(ge=0, description="Adapt trait (non-negative)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "compute": 14,
                "copy": 16,
                "defend": 22,
                "raid": 3,
                "trade": 18,
                "sense": 7,
                "adapt": 9
            }
        }


class AgentSchema(BaseModel):
    """Schema for agent validation."""
    id: str = Field(description="Agent ID (e.g., K-01, N-07, M-12)")
    tape_id: int = Field(ge=0, description="BFF tape ID")
    role: RoleSchema = Field(description="Agent role")
    currency: int = Field(ge=0, description="Currency balance (non-negative)")
    wealth: WealthTraitsSchema = Field(description="Wealth traits")
    employer: Optional[str] = Field(None, description="Employer ID (for Knights)")
    retainer_fee: int = Field(0, ge=0, description="Retainer fee (for Knights)")
    bribe_threshold: int = Field(0, ge=0, description="Bribe threshold (for Kings)")
    alive: bool = Field(True, description="Whether agent is alive")
    
    @field_validator('id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate agent ID format (K-XX, N-XX, M-XX)."""
        if not v or len(v) < 3:
            raise ValueError("Agent ID must be at least 3 characters")
        prefix = v[0]
        if prefix not in ['K', 'N', 'M']:
            raise ValueError("Agent ID must start with K, N, or M")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "K-01",
                "tape_id": 0,
                "role": "king",
                "currency": 5400,
                "wealth": {
                    "compute": 14,
                    "copy": 16,
                    "defend": 22,
                    "raid": 3,
                    "trade": 18,
                    "sense": 7,
                    "adapt": 9
                },
                "employer": None,
                "retainer_fee": 0,
                "bribe_threshold": 350,
                "alive": True
            }
        }


class EventSchema(BaseModel):
    """Schema for event validation."""
    tick: int = Field(ge=1, description="Tick number")
    type: EventTypeSchema = Field(description="Event type")
    king: Optional[str] = Field(None, description="King agent ID")
    knight: Optional[str] = Field(None, description="Knight agent ID")
    merc: Optional[str] = Field(None, description="Mercenary agent ID")
    amount: Optional[int] = Field(None, ge=0, description="Currency amount")
    stake: Optional[int] = Field(None, ge=0, description="Stake amount")
    p_knight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Knight win probability")
    notes: Optional[str] = Field(None, description="Additional notes")
    trait: Optional[str] = Field(None, description="Trait name (for trait_drip)")
    delta: Optional[int] = Field(None, description="Trait delta (for trait_drip)")
    invest: Optional[int] = Field(None, ge=0, description="Investment amount (for trade)")
    wealth_created: Optional[int] = Field(None, ge=0, description="Wealth created (for trade)")
    rv: Optional[float] = Field(None, ge=0.0, description="Raid value (for bribe)")
    threshold: Optional[int] = Field(None, ge=0, description="Bribe threshold")
    employer: Optional[str] = Field(None, description="Employer ID (for retainer)")
    agent: Optional[str] = Field(None, description="Agent ID (for trait_drip)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tick": 1,
                "type": "bribe_accept",
                "king": "K-01",
                "merc": "M-12",
                "amount": 350,
                "rv": 320.5,
                "notes": "success"
            }
        }


class TickMetricsSchema(BaseModel):
    """Schema for tick metrics validation."""
    entropy: float = Field(ge=0.0, description="Shannon entropy")
    compression_ratio: float = Field(ge=0.0, description="Compression ratio")
    copy_score_mean: float = Field(ge=0.0, description="Mean copy score")
    wealth_total: int = Field(ge=0, description="Total wealth across all agents")
    currency_total: int = Field(ge=0, description="Total currency across all agents")
    bribes_paid: int = Field(0, ge=0, description="Number of bribes paid")
    bribes_accepted: int = Field(0, ge=0, description="Number of bribes accepted")
    raids_attempted: int = Field(0, ge=0, description="Number of raids attempted")
    raids_won_by_merc: int = Field(0, ge=0, description="Number of raids won by mercenaries")
    raids_won_by_knight: int = Field(0, ge=0, description="Number of raids won by knights")
    
    class Config:
        json_schema_extra = {
            "example": {
                "entropy": 5.91,
                "compression_ratio": 2.70,
                "copy_score_mean": 0.64,
                "wealth_total": 399,
                "currency_total": 12187,
                "bribes_paid": 1,
                "bribes_accepted": 0,
                "raids_attempted": 2,
                "raids_won_by_merc": 0,
                "raids_won_by_knight": 1
            }
        }


class AgentSnapshotSchema(BaseModel):
    """Schema for agent snapshot validation."""
    id: str = Field(description="Agent ID")
    role: RoleSchema = Field(description="Agent role")
    currency: int = Field(ge=0, description="Currency balance")
    wealth: WealthTraitsSchema = Field(description="Wealth traits")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "K-01",
                "role": "king",
                "currency": 5400,
                "wealth": {
                    "compute": 14,
                    "copy": 16,
                    "defend": 22,
                    "raid": 3,
                    "trade": 18,
                    "sense": 7,
                    "adapt": 9
                }
            }
        }


class TickResultSchema(BaseModel):
    """Schema for tick result validation."""
    tick: int = Field(ge=1, description="Tick number")
    metrics: TickMetricsSchema = Field(description="Tick metrics")
    agents: List[AgentSnapshotSchema] = Field(description="Agent snapshots")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tick": 1,
                "metrics": {
                    "entropy": 5.91,
                    "compression_ratio": 2.70,
                    "copy_score_mean": 0.64,
                    "wealth_total": 399,
                    "currency_total": 12187
                },
                "agents": [
                    {
                        "id": "K-01",
                        "role": "king",
                        "currency": 5400,
                        "wealth": {
                            "compute": 14,
                            "copy": 16,
                            "defend": 22,
                            "raid": 3,
                            "trade": 18,
                            "sense": 7,
                            "adapt": 9
                        }
                    }
                ],
                "meta": {
                    "version": "0.1.1",
                    "seed": 1337,
                    "config_hash": "a3f2b9c1"
                }
            }
        }


class ConfigSchema(BaseModel):
    """Schema for M|inc configuration validation."""
    version: str = Field(description="Configuration version")
    seed: int = Field(ge=0, description="Random seed")
    roles: Dict[str, Any] = Field(description="Role configuration")
    economic: Dict[str, Any] = Field(description="Economic parameters")
    refractory: Optional[Dict[str, int]] = Field(None, description="Refractory periods")
    cache: Optional[Dict[str, Any]] = Field(None, description="Cache configuration")
    output: Optional[Dict[str, bool]] = Field(None, description="Output options")
    trait_emergence: Optional[Dict[str, Any]] = Field(None, description="Trait emergence rules")
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate version format."""
        if not v or '.' not in v:
            raise ValueError("Version must be in format X.Y.Z")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "0.1.1",
                "seed": 1337,
                "roles": {
                    "ratios": {
                        "king": 0.10,
                        "knight": 0.20,
                        "mercenary": 0.70
                    }
                },
                "economic": {
                    "currency_to_wealth_ratio": [100, 5],
                    "bribe_leakage": 0.05
                },
                "refractory": {
                    "raid": 2,
                    "defend": 1
                },
                "cache": {
                    "enabled": True,
                    "max_size": 10000
                },
                "output": {
                    "json_ticks": True,
                    "csv_events": True
                }
            }
        }


def validate_agent(data: Dict[str, Any]) -> AgentSchema:
    """Validate agent data against schema."""
    return AgentSchema(**data)


def validate_event(data: Dict[str, Any]) -> EventSchema:
    """Validate event data against schema."""
    return EventSchema(**data)


def validate_tick_result(data: Dict[str, Any]) -> TickResultSchema:
    """Validate tick result data against schema."""
    return TickResultSchema(**data)


def validate_config(data: Dict[str, Any]) -> ConfigSchema:
    """Validate configuration data against schema."""
    return ConfigSchema(**data)
