"""Configuration management for M|inc."""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml


@dataclass
class RegistryConfig:
    """Configuration for agent registry."""
    role_ratios: Dict[str, float] = field(default_factory=lambda: {
        "king": 0.10,
        "knight": 0.20,
        "mercenary": 0.70
    })
    mutation_rate: float = 0.0
    initial_currency: Dict[str, tuple[int, int]] = field(default_factory=lambda: {
        "king": (5000, 7000),
        "knight": (100, 300),
        "mercenary": (0, 50)
    })
    initial_wealth: Dict[str, Dict[str, tuple[int, int]]] = field(default_factory=lambda: {
        "king": {
            "compute": (10, 15),
            "copy": (12, 18),
            "defend": (18, 25),
            "raid": (2, 4),
            "trade": (15, 22),
            "sense": (5, 9),
            "adapt": (7, 11)
        },
        "knight": {
            "compute": (3, 6),
            "copy": (2, 4),
            "defend": (12, 20),
            "raid": (1, 3),
            "trade": (0, 0),
            "sense": (7, 10),
            "adapt": (4, 7)
        },
        "mercenary": {
            "compute": (1, 3),
            "copy": (3, 6),
            "defend": (0, 2),
            "raid": (12, 18),  # Increased from (8, 12)
            "trade": (0, 0),
            "sense": (5, 9),   # Increased from (3, 6)
            "adapt": (4, 7)    # Increased from (2, 5)
        }
    })


@dataclass
class EconomicConfig:
    """Configuration for economic parameters."""
    currency_to_wealth_ratio: tuple[int, int] = (100, 5)
    bribe_leakage: float = 0.05
    exposure_factors: Dict[str, float] = field(default_factory=lambda: {
        "king": 1.0,
        "knight": 0.5,
        "mercenary": 0.4
    })
    raid_value_weights: Dict[str, float] = field(default_factory=lambda: {
        "alpha_raid": 1.0,
        "beta_sense_adapt": 0.25,
        "gamma_king_defend": 0.60,
        "delta_king_exposed": 0.40
    })
    defend_resolution: Dict[str, float] = field(default_factory=lambda: {
        "base_knight_winrate": 0.50,
        "trait_advantage_weight": 0.30,
        "employment_bonus": 0.08,
        "clamp_min": 0.05,
        "clamp_max": 0.95,
        "stake_currency_frac": 0.10
    })
    trade: Dict[str, Any] = field(default_factory=lambda: {
        "invest_per_tick": 100,
        "created_wealth_units": 5,
        "distribution": {"defend": 3, "trade": 2}
    })
    on_failed_bribe: Dict[str, float] = field(default_factory=lambda: {
        "king_currency_loss_frac": 0.50,
        "king_wealth_loss_frac": 0.25
    })


@dataclass
class RefractoryConfig:
    """Configuration for refractory periods."""
    raid: int = 2
    defend: int = 1
    bribe: int = 1
    trade: int = 0


@dataclass
class CacheConfig:
    """Configuration for caching."""
    enabled: bool = True
    max_size: int = 10000
    witness_sample_rate: float = 0.05


@dataclass
class OutputConfig:
    """Configuration for output formats."""
    json_ticks: bool = True
    csv_events: bool = True
    csv_final_agents: bool = True
    compress: bool = False


@dataclass
class TraitEmergenceConfig:
    """Configuration for trait emergence rules."""
    enabled: bool = True
    rules: List[Dict[str, Any]] = field(default_factory=lambda: [
        {
            "condition": "copy >= 12 AND tick % 2 == 0",
            "delta": {"copy": 1}
        }
    ])


@dataclass
class MIncConfig:
    """Complete M|inc configuration."""
    version: str = "0.1.1"
    seed: int = 1337
    registry: RegistryConfig = field(default_factory=RegistryConfig)
    economic: EconomicConfig = field(default_factory=EconomicConfig)
    refractory: RefractoryConfig = field(default_factory=RefractoryConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    trait_emergence: TraitEmergenceConfig = field(default_factory=TraitEmergenceConfig)
    
    def compute_hash(self) -> str:
        """Compute a hash of the configuration for cache invalidation."""
        # Convert config to dict and compute hash
        config_dict = self.to_dict()
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "version": self.version,
            "seed": self.seed,
            "roles": {
                "ratios": self.registry.role_ratios,
                "mutation_rate": self.registry.mutation_rate
            },
            "economic": {
                "currency_to_wealth_ratio": list(self.economic.currency_to_wealth_ratio),
                "bribe_leakage": self.economic.bribe_leakage,
                "exposure_factors": self.economic.exposure_factors,
                "raid_value_weights": self.economic.raid_value_weights,
                "defend_resolution": self.economic.defend_resolution,
                "trade": self.economic.trade,
                "on_failed_bribe": self.economic.on_failed_bribe
            },
            "refractory": {
                "raid": self.refractory.raid,
                "defend": self.refractory.defend,
                "bribe": self.refractory.bribe,
                "trade": self.refractory.trade
            },
            "cache": {
                "enabled": self.cache.enabled,
                "max_size": self.cache.max_size,
                "witness_sample_rate": self.cache.witness_sample_rate
            },
            "output": {
                "json_ticks": self.output.json_ticks,
                "csv_events": self.output.csv_events,
                "csv_final_agents": self.output.csv_final_agents,
                "compress": self.output.compress
            },
            "trait_emergence": {
                "enabled": self.trait_emergence.enabled,
                "rules": self.trait_emergence.rules
            }
        }


class ConfigLoader:
    """Loader for M|inc configuration files."""
    
    @staticmethod
    def load(path: Path | str) -> MIncConfig:
        """Load configuration from YAML file.
        
        Args:
            path: Path to YAML configuration file
            
        Returns:
            MIncConfig instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        return ConfigLoader.from_dict(data)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> MIncConfig:
        """Create configuration from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            MIncConfig instance
        """
        # Extract sections
        version = data.get("version", "0.1.1")
        seed = data.get("seed", 1337)
        
        # Registry config
        roles_data = data.get("roles", {})
        registry = RegistryConfig(
            role_ratios=roles_data.get("ratios", RegistryConfig().role_ratios),
            mutation_rate=roles_data.get("mutation_rate", 0.0)
        )
        
        # Economic config
        econ_data = data.get("economic", {})
        economic = EconomicConfig(
            currency_to_wealth_ratio=tuple(econ_data.get("currency_to_wealth_ratio", [100, 5])),
            bribe_leakage=econ_data.get("bribe_leakage", 0.05),
            exposure_factors=econ_data.get("exposure_factors", EconomicConfig().exposure_factors),
            raid_value_weights=econ_data.get("raid_value_weights", EconomicConfig().raid_value_weights),
            defend_resolution=econ_data.get("defend_resolution", EconomicConfig().defend_resolution),
            trade=econ_data.get("trade", EconomicConfig().trade),
            on_failed_bribe=econ_data.get("on_failed_bribe", EconomicConfig().on_failed_bribe)
        )
        
        # Refractory config
        refr_data = data.get("refractory", {})
        refractory = RefractoryConfig(
            raid=refr_data.get("raid", 2),
            defend=refr_data.get("defend", 1),
            bribe=refr_data.get("bribe", 1),
            trade=refr_data.get("trade", 0)
        )
        
        # Cache config
        cache_data = data.get("cache", {})
        cache = CacheConfig(
            enabled=cache_data.get("enabled", True),
            max_size=cache_data.get("max_size", 10000),
            witness_sample_rate=cache_data.get("witness_sample_rate", 0.05)
        )
        
        # Output config
        output_data = data.get("output", {})
        output = OutputConfig(
            json_ticks=output_data.get("json_ticks", True),
            csv_events=output_data.get("csv_events", True),
            csv_final_agents=output_data.get("csv_final_agents", True),
            compress=output_data.get("compress", False)
        )
        
        # Trait emergence config
        trait_data = data.get("trait_emergence", {})
        trait_emergence = TraitEmergenceConfig(
            enabled=trait_data.get("enabled", True),
            rules=trait_data.get("rules", TraitEmergenceConfig().rules)
        )
        
        return MIncConfig(
            version=version,
            seed=seed,
            registry=registry,
            economic=economic,
            refractory=refractory,
            cache=cache,
            output=output,
            trait_emergence=trait_emergence
        )
    
    @staticmethod
    def save(config: MIncConfig, path: Path | str) -> None:
        """Save configuration to YAML file.
        
        Args:
            config: MIncConfig instance
            path: Path to save YAML file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)
    
    @staticmethod
    def get_default() -> MIncConfig:
        """Get default configuration.
        
        Returns:
            MIncConfig with default values
        """
        return MIncConfig()
    
    @staticmethod
    def validate(config: MIncConfig) -> List[str]:
        """Validate configuration.
        
        Args:
            config: MIncConfig to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate role ratios sum to 1.0
        ratio_sum = sum(config.registry.role_ratios.values())
        if abs(ratio_sum - 1.0) > 0.01:
            errors.append(f"Role ratios must sum to 1.0, got {ratio_sum}")
        
        # Validate non-negative values
        if config.seed < 0:
            errors.append("Seed must be non-negative")
        
        if config.economic.bribe_leakage < 0 or config.economic.bribe_leakage > 1:
            errors.append("Bribe leakage must be between 0 and 1")
        
        # Validate refractory periods
        if config.refractory.raid < 0:
            errors.append("Raid refractory period must be non-negative")
        
        # Validate cache config
        if config.cache.max_size < 0:
            errors.append("Cache max size must be non-negative")
        
        if config.cache.witness_sample_rate < 0 or config.cache.witness_sample_rate > 1:
            errors.append("Witness sample rate must be between 0 and 1")
        
        return errors
