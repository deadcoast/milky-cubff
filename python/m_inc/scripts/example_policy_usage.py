"""Example demonstrating Policy DSL usage in M|inc.

This example shows how to:
1. Load a policy configuration from YAML
2. Compile policies into callable functions
3. Use compiled policies in economic calculations
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from m_inc.policies import PolicyCompiler
from m_inc.core.models import Agent, Role, WealthTraits
from m_inc.core.config import EconomicConfig


def main():
    """Demonstrate Policy DSL usage."""
    
    # Define a policy configuration
    policy_config = {
        'policies': {
            'raid_value': {
                'formula': 'alpha*merc.wealth.raid + beta*(merc.wealth.sense+merc.wealth.adapt) - gamma*king_defend + delta*king_exposed',
                'params': {
                    'alpha': 1.0,
                    'beta': 0.25,
                    'gamma': 0.60,
                    'delta': 0.40
                }
            },
            'bribe_outcome': {
                'condition': 'threshold >= raid_value and king.currency >= threshold',
                'on_success': {
                    'king_currency': '-threshold',
                    'merc_currency': '+threshold',
                    'king_wealth_leakage': 0.05
                }
            },
            'p_knight_win': {
                'formula': 'clamp(base + (sigmoid(weight * trait_delta) - 0.5), clamp_min, clamp_max)',
                'params': {
                    'base': 0.5,
                    'weight': 0.3,
                    'employment_bonus': 0.25,
                    'clamp_min': 0.05,
                    'clamp_max': 0.95
                }
            },
            'trade_action': {
                'params': {
                    'invest_per_tick': 100,
                    'created_wealth_units': 5,
                    'distribution': {'defend': 3, 'trade': 2}
                }
            }
        }
    }
    
    # Create sample agents
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(compute=10, copy=12, defend=20, raid=2, trade=15, sense=5, adapt=7),
        bribe_threshold=300
    )
    
    knight = Agent(
        id="N-01",
        tape_id=2,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=3, copy=2, defend=15, raid=1, trade=0, sense=8, adapt=5),
        employer="K-01"
    )
    
    merc = Agent(
        id="M-01",
        tape_id=3,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=1, copy=3, defend=0, raid=12, trade=0, sense=6, adapt=4)
    )
    
    # Create economic config
    config = EconomicConfig()
    
    # Compile policies
    print("Compiling policies...")
    compiler = PolicyCompiler(policy_config)
    
    # Validate first
    errors = compiler.validate()
    if errors:
        print(f"Validation errors: {errors}")
        return
    
    compiled = compiler.compile()
    print("✓ Policies compiled successfully\n")
    
    # Use compiled policies
    print("=== Economic Calculations ===\n")
    
    # 1. Compute raid value
    raid_val = compiled.raid_value(merc, king, [knight], config)
    print(f"Raid Value: {raid_val:.2f}")
    print(f"  - Mercenary raid trait: {merc.wealth.raid}")
    print(f"  - King's bribe threshold: {king.bribe_threshold}")
    
    # 2. Evaluate bribe outcome
    bribe_result = compiled.bribe_outcome(king, merc, [knight], config, raid_val)
    print(f"\nBribe Outcome: {'ACCEPTED' if bribe_result.accepted else 'REJECTED'}")
    if bribe_result.accepted:
        print(f"  - Amount: {bribe_result.amount}")
        print(f"  - King currency delta: {bribe_result.king_currency_delta}")
        print(f"  - Merc currency delta: {bribe_result.merc_currency_delta}")
        print(f"  - King wealth leakage: {bribe_result.king_wealth_leakage * 100}%")
    else:
        print(f"  - Reason: {bribe_result.reason}")
    
    # 3. Compute knight win probability
    p_win = compiled.p_knight_win(knight, merc, config)
    print(f"\nKnight Win Probability: {p_win:.2%}")
    print(f"  - Knight defend: {knight.wealth.defend}")
    print(f"  - Mercenary raid: {merc.wealth.raid}")
    print(f"  - Knight employed: {knight.employer is not None}")
    
    # 4. Execute trade action
    print(f"\nTrade Action:")
    print(f"  - King currency before: {king.currency}")
    print(f"  - King defend before: {king.wealth.defend}")
    
    wealth_created = compiled.trade_action(king, config)
    
    print(f"  - Wealth created: {wealth_created}")
    print(f"  - King currency after: {king.currency}")
    print(f"  - King defend after: {king.wealth.defend}")
    
    print("\n=== Policy DSL Demo Complete ===")


if __name__ == '__main__':
    main()
