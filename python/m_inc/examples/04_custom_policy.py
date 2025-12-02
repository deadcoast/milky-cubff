#!/usr/bin/env python3
"""
Example: Custom Policy Configuration

This example demonstrates how to create and use custom economic policies
with M|inc by modifying YAML configuration files.

Usage:
    python 04_custom_policy.py
"""

import sys
import yaml
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from m_inc.core.agent_registry import AgentRegistry, RegistryConfig
from m_inc.core.economic_engine import EconomicEngine, EconomicConfig
from m_inc.adapters.trace_reader import TraceReader
from m_inc.core.config import ConfigLoader


def create_custom_config():
    """Create a custom configuration with modified economic parameters."""
    
    # Load default config as base
    default_config_path = Path(__file__).parent.parent / "config" / "minc_default.yaml"
    
    with open(default_config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Modify economic parameters for more aggressive gameplay
    print("Creating custom configuration with aggressive parameters...")
    print()
    
    # Increase raid rewards
    config['economic']['raid_value_weights']['alpha_raid'] = 1.5  # Increased from 1.0
    config['economic']['raid_value_weights']['beta_sense_adapt'] = 0.35  # Increased from 0.25
    print("✓ Increased raid value weights (more aggressive raids)")
    
    # Reduce king defense advantage
    config['economic']['raid_value_weights']['gamma_king_defend'] = 0.40  # Reduced from 0.60
    print("✓ Reduced king defense projection weight (weaker defenses)")
    
    # Increase bribe leakage
    config['economic']['bribe_leakage'] = 0.10  # Increased from 0.05
    print("✓ Increased bribe leakage (10% vs 5%)")
    
    # Increase trade rewards
    config['economic']['trade']['created_wealth_units'] = 7  # Increased from 5
    config['economic']['trade']['distribution']['defend'] = 4  # Increased from 3
    config['economic']['trade']['distribution']['trade'] = 3  # Increased from 2
    print("✓ Increased trade rewards (7 wealth units vs 5)")
    
    # Adjust knight advantage
    config['economic']['defend_resolution']['base_knight_winrate'] = 0.55  # Increased from 0.50
    config['economic']['defend_resolution']['trait_advantage_weight'] = 0.40  # Increased from 0.30
    print("✓ Increased knight advantage in contests")
    
    # Reduce refractory periods for faster action
    config['refractory']['raid'] = 1  # Reduced from 2
    config['refractory']['defend'] = 0  # Reduced from 1
    print("✓ Reduced refractory periods (faster action)")
    
    print()
    
    # Save custom config
    custom_config_path = Path(__file__).parent / "custom_aggressive.yaml"
    with open(custom_config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Custom configuration saved to: {custom_config_path}")
    print()
    
    return custom_config_path


def compare_configurations():
    """Compare default vs custom configuration outcomes."""
    
    print("=" * 60)
    print("M|inc Example: Custom Policy Configuration")
    print("=" * 60)
    print()
    
    # Create custom config
    custom_config_path = create_custom_config()
    
    # Load trace
    trace_file = Path(__file__).parent.parent / "testdata" / "bff_trace_small.json"
    
    if not trace_file.exists():
        print(f"Error: Trace file not found: {trace_file}")
        return 1
    
    # Run with default config
    print("Running simulation with DEFAULT configuration...")
    print("-" * 60)
    default_config_path = Path(__file__).parent.parent / "config" / "minc_default.yaml"
    default_results = run_simulation(trace_file, default_config_path, num_ticks=10)
    print()
    
    # Run with custom config
    print("Running simulation with CUSTOM configuration...")
    print("-" * 60)
    custom_results = run_simulation(trace_file, custom_config_path, num_ticks=10)
    print()
    
    # Compare results
    print("=" * 60)
    print("Configuration Comparison")
    print("=" * 60)
    print()
    
    print(f"{'Metric':<30} {'Default':>15} {'Custom':>15} {'Change':>15}")
    print("-" * 75)
    
    metrics = [
        ('Final Wealth', 'wealth_total'),
        ('Final Currency', 'currency_total'),
        ('Total Events', 'event_count'),
        ('Bribes Accepted', 'bribes_accepted'),
        ('Raids Attempted', 'raids_attempted'),
        ('Knight Wins', 'raids_won_by_knight'),
        ('Merc Wins', 'raids_won_by_merc'),
    ]
    
    for label, key in metrics:
        default_val = default_results.get(key, 0)
        custom_val = custom_results.get(key, 0)
        
        if default_val > 0:
            change_pct = ((custom_val - default_val) / default_val) * 100
            change_str = f"{change_pct:+.1f}%"
        else:
            change_str = "N/A"
        
        print(f"{label:<30} {default_val:>15,} {custom_val:>15,} {change_str:>15}")
    
    print()
    print("Key Observations:")
    
    if custom_results['raids_attempted'] > default_results['raids_attempted']:
        print("  • More raids occurred with aggressive parameters")
    
    if custom_results['bribes_accepted'] < default_results['bribes_accepted']:
        print("  • Fewer bribes accepted (higher leakage cost)")
    
    if custom_results['wealth_total'] > default_results['wealth_total']:
        print("  • More wealth created (increased trade rewards)")
    
    print()
    print("Try experimenting with different parameter combinations!")
    print(f"Edit: {custom_config_path}")
    print()
    
    return 0


def run_simulation(trace_file, config_file, num_ticks):
    """Run a simulation and return summary metrics."""
    
    # Load configuration
    config = ConfigLoader.load(config_file)
    
    # Initialize components
    trace_reader = TraceReader(trace_file)
    
    registry_config = RegistryConfig(
        role_ratios=config.roles.ratios,
        seed=config.seed
    )
    registry = AgentRegistry(registry_config)
    
    economic_config = EconomicConfig.from_dict(config.economic)
    engine = EconomicEngine(registry, economic_config)
    
    # Assign roles
    epoch = trace_reader.read_epoch()
    tape_ids = list(epoch.tapes.keys())
    registry.assign_roles(tape_ids)
    
    # Process ticks
    total_events = 0
    final_metrics = None
    
    for tick in range(1, num_ticks + 1):
        result = engine.process_tick(tick)
        total_events += len(result.events)
        final_metrics = result.metrics
        
        print(f"Tick {tick:3d}: "
              f"Wealth={result.metrics.wealth_total:6d}, "
              f"Events={len(result.events):3d}")
    
    # Return summary
    return {
        'wealth_total': final_metrics.wealth_total,
        'currency_total': final_metrics.currency_total,
        'event_count': total_events,
        'bribes_accepted': final_metrics.bribes_accepted,
        'raids_attempted': final_metrics.raids_attempted,
        'raids_won_by_knight': final_metrics.raids_won_by_knight,
        'raids_won_by_merc': final_metrics.raids_won_by_merc,
    }


def show_policy_customization_guide():
    """Show guide for customizing policies."""
    
    print("\n" + "=" * 60)
    print("Policy Customization Guide")
    print("=" * 60)
    print()
    print("Key parameters to experiment with:")
    print()
    print("1. Raid Value Weights (economic.raid_value_weights):")
    print("   - alpha_raid: Weight for mercenary raid trait")
    print("   - beta_sense_adapt: Weight for mercenary sense+adapt")
    print("   - gamma_king_defend: Weight for king defense")
    print("   - delta_king_exposed: Weight for king exposed wealth")
    print()
    print("2. Defend Resolution (economic.defend_resolution):")
    print("   - base_knight_winrate: Base probability (0.0-1.0)")
    print("   - trait_advantage_weight: Sigmoid scaling factor")
    print("   - clamp_min/max: Probability bounds")
    print()
    print("3. Trade Parameters (economic.trade):")
    print("   - invest_per_tick: Currency cost")
    print("   - created_wealth_units: Total wealth created")
    print("   - distribution: How wealth is allocated")
    print()
    print("4. Refractory Periods (refractory):")
    print("   - raid/defend/bribe/trade: Cooldown in ticks")
    print()
    print("5. Role Ratios (roles.ratios):")
    print("   - king/knight/mercenary: Population proportions")
    print()


if __name__ == "__main__":
    exit_code = compare_configurations()
    
    if exit_code == 0:
        show_policy_customization_guide()
    
    sys.exit(exit_code)
