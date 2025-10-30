---
title: "M|inc Incentive System"
description: "Deterministic economic incentive model layered atop CuBFF (0.1.1)"
version: "0.1.1"
last_updated: "2025-10-30"
dependencies:
  - "../../OVERVIEW.md"
  - "../api/m.inc-json-schemas.md"
---

# M|inc Incentive System

Incentives are the main driver of the M|inc ecosystem, combined with survival it provides a more realistic model of natural selection.

## Roles and Incentive Priorities

- King: survive → defend wealth → maintain currency → grow via trade
- Knight: win defends → earn currency → grow defend/sense/adapt → survive
- Mercenary: gain wealth → gain currency → raid frequency → survive

## Wealth Traits

Seven additive traits, integer-valued per agent:

- compute, copy, defend, raid, trade, sense, adapt

Total wealth = sum of all seven traits.

## Currency–Wealth Conversion

- 100 currency = 5 wealth units
- King trade action: -100 currency → +3 defend, +2 trade

## Bribes (king → mercenary)

Bribe threshold check:

```
if (bribe_threshold >= raid_value) and (king.currency >= bribe_threshold):
  success
else:
  contest (defend/raid)
```

Outcomes:

- Success: king.currency -= bribe; merc.currency += bribe; king.wealth *= 0.95
- Fail: king loses 50% currency, 25% wealth; merc mirrors gains proportionally

## Defend Contest (knight vs mercenary)

Probability knight wins:

```
p_knight_win = clamp(0.05, 0.95,
  0.5 + (sigmoid(0.3 * ((knight.defend + knight.sense + knight.adapt)
                       - (merc.raid + merc.sense + merc.adapt))) - 0.5)
)
```

- Knight win: earns stake (10% of combined currency), bounty (7% of merc raid/adapt)
- Knight loss: loses stake; -1 defend; king mirrored loss of currency/wealth

## Raid Value (deterministic)

```
raid_value = 1.0*merc.raid + 0.25*(merc.sense+merc.adapt)
            - 0.60*(king_defend_projection)
            + 0.40*(king_wealth_exposed)

king_defend_projection = Σ(knight.defend + 0.5*sense + 0.5*adapt)
king_wealth_exposed = total_wealth * exposure_factor(king=1.0)
```

## Entropy Mechanics (compatibility with current framework)

- Tick loop remains: pair → run → split → reinsert
- Mutation rate remains at ~0.1%
- Emergent tape activity confers trait bonuses (e.g., copy ≥ 12 → +1 copy every 2 ticks)

## Event Types (for external loggers)

- trade, bribe_accept, bribe_fail, defend_win, defend_loss, raid_win, raid_loss

## Determinism and Reproducibility

- All formulas pure functions of current state
- Randomness isolated to existing mutation and pairing; seedable
- Event sequencing is recorded to CSV for replay
