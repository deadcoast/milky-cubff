"""Pure economic calculation functions for M|inc."""

import math
from typing import List
from .models import Agent
from .config import EconomicConfig


def sigmoid(x: float) -> float:
    """Compute sigmoid function.
    
    Args:
        x: Input value
        
    Returns:
        Sigmoid of x (between 0 and 1)
    """
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        # Handle extreme values
        return 0.0 if x < 0 else 1.0


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def wealth_total(agent: Agent) -> int:
    """Compute total wealth for an agent.
    
    Args:
        agent: Agent to compute wealth for
        
    Returns:
        Sum of all wealth traits
    """
    return agent.wealth_total()


def wealth_exposed(agent: Agent, config: EconomicConfig) -> float:
    """Compute exposed wealth for an agent.
    
    Args:
        agent: Agent to compute exposed wealth for
        config: Economic configuration
        
    Returns:
        Exposed wealth (total wealth * exposure factor)
    """
    exposure_factor = config.exposure_factors.get(agent.role.value, 1.0)
    return agent.wealth_total() * exposure_factor


def king_defend_projection(king: Agent, knights: List[Agent], 
                           attackers: int, config: EconomicConfig) -> float:
    """Compute king's defensive projection from assigned knights.
    
    Args:
        king: King agent
        knights: List of defending knights
        attackers: Number of attackers
        config: Economic configuration
        
    Returns:
        Defensive projection score
    """
    if attackers <= 0:
        attackers = 1
    
    # Sum defensive capabilities of knights
    score = sum(
        k.wealth.defend + 0.5 * k.wealth.sense + 0.5 * k.wealth.adapt
        for k in knights
    )
    
    # Normalize by number of attackers
    return score * min(1.0, len(knights) / attackers)


def raid_value(merc: Agent, king: Agent, knights: List[Agent], 
               config: EconomicConfig) -> float:
    """Compute raid value for bribe evaluation.
    
    Formula:
    raid_value = alpha*merc.raid + beta*(merc.sense+merc.adapt)
                - gamma*king_defend_projection + delta*king_wealth_exposed
    
    Args:
        merc: Mercenary agent
        king: King agent
        knights: List of defending knights
        config: Economic configuration
        
    Returns:
        Raid value (non-negative)
    """
    weights = config.raid_value_weights
    
    kd = king_defend_projection(king, knights, attackers=1, config=config)
    exposed = wealth_exposed(king, config)
    
    value = (
        weights["alpha_raid"] * merc.wealth.raid +
        weights["beta_sense_adapt"] * (merc.wealth.sense + merc.wealth.adapt) -
        weights["gamma_king_defend"] * kd +
        weights["delta_king_exposed"] * exposed
    )
    
    return max(0.0, value)


def p_knight_win(knight: Agent, merc: Agent, config: EconomicConfig) -> float:
    """Compute probability of knight winning a defend contest.
    
    Formula:
    p = clamp(0.05, 0.95,
        0.5 + (sigmoid(0.3 * trait_delta) - 0.5) + employment_bonus)
    
    where trait_delta = (knight.defend + knight.sense + knight.adapt)
                       - (merc.raid + merc.sense + merc.adapt)
    
    Employment bonus: Knights hired by a king receive a significant defensive buff
    
    Args:
        knight: Knight agent
        merc: Mercenary agent
        config: Economic configuration
        
    Returns:
        Probability of knight winning (between 0.05 and 0.95)
    """
    defend_res = config.defend_resolution
    
    base = defend_res["base_knight_winrate"]
    weight = defend_res["trait_advantage_weight"]
    
    # Compute trait delta
    knight_traits = knight.wealth.defend + knight.wealth.sense + knight.wealth.adapt
    merc_traits = merc.wealth.raid + merc.wealth.sense + merc.wealth.adapt
    trait_delta = knight_traits - merc_traits
    
    # Apply sigmoid transformation
    raw = base + (sigmoid(weight * trait_delta) - 0.5)
    
    # Employment bonus: Hired knights get a significant buff
    employment_bonus = 0.0
    if knight.employer:
        # Employed knights get a +0.25 bonus (25% better chance)
        employment_bonus = defend_res.get("employment_bonus", 0.25)
    
    # Add employment bonus
    raw += employment_bonus
    
    # Clamp to valid range
    return clamp(raw, defend_res["clamp_min"], defend_res["clamp_max"])


def stake_amount(knight: Agent, merc: Agent, config: EconomicConfig) -> int:
    """Compute stake amount for a defend contest.
    
    Args:
        knight: Knight agent
        merc: Mercenary agent
        config: Economic configuration
        
    Returns:
        Stake amount (10% of combined currency)
    """
    stake_frac = config.defend_resolution["stake_currency_frac"]
    combined = knight.currency + merc.currency
    return int(stake_frac * combined)


def resolve_knight_wins(p_knight: float, knight_id: str, merc_id: str) -> bool:
    """Deterministically resolve whether knight wins.
    
    Uses probability and lexicographic tie-breaking.
    
    Args:
        p_knight: Probability of knight winning
        knight_id: Knight agent ID
        merc_id: Mercenary agent ID
        
    Returns:
        True if knight wins, False if mercenary wins
    """
    if p_knight > 0.5:
        return True
    elif p_knight < 0.5:
        return False
    else:
        # Exact tie: use lexicographic comparison
        return knight_id < merc_id


def apply_bribe_leakage(king: Agent, leakage_frac: float) -> None:
    """Apply wealth leakage to a king after successful bribe.
    
    Args:
        king: King agent
        leakage_frac: Fraction of wealth to leak (e.g., 0.05 for 5%)
    """
    king.scale_wealth(1.0 - leakage_frac)


def apply_mirrored_losses(king: Agent, merc: Agent, config: EconomicConfig) -> None:
    """Apply mirrored losses from king to mercenary.
    
    Used when bribe fails or mercenary wins defend contest.
    
    Args:
        king: King agent (loses currency and wealth)
        merc: Mercenary agent (gains mirrored amounts)
        config: Economic configuration
    """
    failed_bribe = config.on_failed_bribe
    
    # Currency loss
    currency_loss = int(king.currency * failed_bribe["king_currency_loss_frac"])
    king.add_currency(-currency_loss)
    merc.add_currency(currency_loss)
    
    # Wealth loss (per trait)
    wealth_loss_frac = failed_bribe["king_wealth_loss_frac"]
    for trait_name in ["compute", "copy", "defend", "raid", "trade", "sense", "adapt"]:
        trait_value = getattr(king.wealth, trait_name)
        loss = int(trait_value * wealth_loss_frac)
        if loss > 0:
            king.add_wealth(trait_name, -loss)
            merc.add_wealth(trait_name, loss)


def apply_bounty(knight: Agent, merc: Agent, bounty_frac: float = 0.07) -> None:
    """Apply bounty transfer from mercenary to knight.
    
    Knight takes a percentage of mercenary's raid and adapt traits.
    
    Args:
        knight: Knight agent (gains bounty)
        merc: Mercenary agent (loses bounty)
        bounty_frac: Fraction of traits to transfer (default 7%)
    """
    for trait_name in ["raid", "adapt"]:
        trait_value = getattr(merc.wealth, trait_name)
        bounty = int(trait_value * bounty_frac)
        if bounty > 0:
            merc.add_wealth(trait_name, -bounty)
            knight.add_wealth(trait_name, bounty)


def apply_trade(king: Agent, config: EconomicConfig) -> int:
    """Apply trade operation for a king.
    
    Deducts currency and adds wealth according to configured distribution.
    
    Args:
        king: King agent
        config: Economic configuration
        
    Returns:
        Amount of wealth created (0 if trade didn't happen)
    """
    trade_config = config.trade
    invest = trade_config["invest_per_tick"]
    
    if king.currency < invest:
        return 0
    
    # Deduct currency
    king.add_currency(-invest)
    
    # Add wealth according to distribution
    created = trade_config["created_wealth_units"]
    distribution = trade_config["distribution"]
    
    for trait_name, amount in distribution.items():
        king.add_wealth(trait_name, amount)
    
    return created


def pick_target_king(kings: List[Agent], config: EconomicConfig) -> Agent:
    """Deterministically pick target king with highest exposed wealth.
    
    Args:
        kings: List of king agents
        config: Economic configuration
        
    Returns:
        King with highest exposed wealth (tie-broken by ID)
    """
    if not kings:
        raise ValueError("No kings available to target")
    
    # Sort by exposed wealth (descending), then by ID (ascending)
    sorted_kings = sorted(
        kings,
        key=lambda k: (-wealth_exposed(k, config), k.id)
    )
    
    return sorted_kings[0]
