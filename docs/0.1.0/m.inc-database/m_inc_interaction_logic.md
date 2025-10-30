# Mercenaries Inc. — Interaction Logic Completion (v0.1.1c)

This extends the previous **v0.1.1** spec with finalized equations, tie-breakers, and ordering for the variables already in play.

## A) Fixed Parameters (pin existing knobs)

```yaml
version: "m.inc/0.1.1c"

# Exposure factor used in raid valuation
EXPOSURE_FACTOR:
  king: 1.00
  knight: 0.50
  mercenary: 0.40

# Raid value weights (used in bribe check)
RAID_VALUE_WEIGHTS:
  alpha_raid: 1.00          # merc.raid
  beta_sense_adapt: 0.25    # merc.(sense+adapt)
  gamma_king_defend: 0.60   # subtract king's projected defend
  delta_king_exposed: 0.40  # add exposed king wealth

# Bribe leakage (successful bribe only)
BRIBE_LEAKAGE_FRAC: 0.05     # fixed 5% across all wealth traits

# Failed-bribe loss mirrors (king -> merc)
ON_FAILED_BRIBE:
  king_currency_loss_frac: 0.50
  king_wealth_loss_frac:   0.25
  merc_currency_gain: "mirror"
  merc_wealth_gain:   "mirror"

# Defend resolution (deterministic)
DEFEND_RESOLUTION:
  base_knight_winrate: 0.50
  trait_advantage_weight: 0.30   # sigmoid input multiplier
  clamp_min: 0.05
  clamp_max: 0.95
  stake_currency_frac: 0.10      # of (knight.currency + merc.currency)

# Trade (kings only; existing rule)
TRADE:
  invest_per_tick_currency: 100
  created_wealth_units: 5
  distribution:
    - [defend, 3]
    - [trade, 2]
  remainder_to: defend

# Retainer (existing)
RETAINER:
  pay_each_tick: true

# Soup drip (existing minimal signal)
SOUP_DRIP:
  condition: "agent.copy >= 12 AND tick % 2 == 0"
  delta: {copy: +1}
```

---

## B) Primitive Functions (exact math; no new features)

```yaml
wealth_total(agent) = sum(agent.wealth[compute,copy,defend,raid,trade,sense,adapt])

wealth_exposed(agent) = wealth_total(agent) * EXPOSURE_FACTOR[agent.role]

king_defend_projection(king, assigned_knights, attackers):
  attackers'count := max(1, attackers)
  score := Σ_{k in assigned_knights} (k.defend + 0.5*k.sense + 0.5*k.adapt)
  return score * min(1.0, len(assigned_knights) / attackers'count)

raid_value(merc, king, assigned_knights):
  α,β,γ,δ := RAID_VALUE_WEIGHTS
  KD := king_defend_projection(king, assigned_knights, attackers=1)
  return max(0,
    α*merc.raid + β*(merc.sense + merc.adapt) - γ*KD + δ*wealth_exposed(king)
  )

sigmoid(x) = 1 / (1 + e^{-x})

p_knight_win(knight, merc):
  base := DEFEND_RESOLUTION.base_knight_winrate
  w := DEFEND_RESOLUTION.trait_advantage_weight
  raw := base + (sigmoid(w * ((knight.defend + knight.sense + knight.adapt)
                              - (merc.raid + merc.sense + merc.adapt))) - 0.5)
  return clamp(raw, DEFEND_RESOLUTION.clamp_min, DEFEND_RESOLUTION.clamp_max)

stake(knight, merc) = floor(DEFEND_RESOLUTION.stake_currency_frac * (knight.currency + merc.currency))
```

**Tie-breaker** (deterministic outcome selection):

* If `p_knight_win > 0.5` → knight wins.
* If `p_knight_win < 0.5` → merc wins.
* If exactly `0.5` → knight wins iff `knight.id < merc.id` (lexicographic), else merc.

---

## C) Bribe Evaluation (no new behavior, just pinned)

```yaml
bribe_check(king, merc, assigned_knights):
  rv := raid_value(merc, king, assigned_knights)
  offered := king.bribe_threshold (0 if unset)
  if offered >= rv and king.currency >= offered:
    # Successful bribe
    king.currency -= offered
    merc.currency += offered
    apply_wealth_leakage(king, BRIBE_LEAKAGE_FRAC)
    result: "accepted"
  else if offered >= rv and king.currency < offered:
    result: "insufficient_funds" # no transfer
  else:
    result: "rejected"
```

**Wealth leakage (successful bribe only):**

```
apply_wealth_leakage(king, f):
  for each trait T in wealth:
    king.wealth[T] := floor(king.wealth[T] * (1 - f))
```

---

## D) Raid/Defend Resolution (existing outcomes, fully specified)

```yaml
contest(king, merc, assigned_knights):
  if len(assigned_knights) == 0:
    # Unopposed success for merc (as per prior rule)
    apply_failed_bribe_losses(king, merc)
    return "unopposed_raid"

  knight := assigned_knights[0] # one defender per attacker in current model
  p := p_knight_win(knight, merc)
  s := stake(knight, merc)

  if knight_wins(p, knight.id, merc.id):   # uses the tie-break rule above
    knight.currency += s
    merc.currency := max(0, merc.currency - s)
    bounty(knight, merc, frac=0.07)        # knight loots small % of merc's raid/adapt
    return "defend_win"
  else:
    apply_failed_bribe_losses(king, merc)  # king→merc mirrored losses
    knight.currency := max(0, knight.currency - s)
    if knight.defend > 0: knight.defend -= 1  # equipment wear
    return "defend_loss"
```

**Mirrored losses (failed bribe/raid success only):**

```
apply_failed_bribe_losses(king, merc):
  c_loss := floor(king.currency * ON_FAILED_BRIBE.king_currency_loss_frac)
  king.currency -= c_loss
  merc.currency += c_loss

  for trait T in wealth:
    w_loss := floor(king.wealth[T] * ON_FAILED_BRIBE.king_wealth_loss_frac)
    king.wealth[T] := king.wealth[T] - w_loss
    merc.wealth[T] := merc.wealth[T] + w_loss
```

**Knight bounty (only on defend win):**

```
bounty(knight, merc, frac):
  for T in [raid, adapt]:
    amt := floor(merc.wealth[T] * frac)
    merc.wealth[T] := merc.wealth[T] - amt
    knight.wealth[T] := knight.wealth[T] + amt
```

---

## E) Targeting & Assignment (no new logic, just frozen ordering)

```yaml
# Deterministic target selection for current model:
pick_target_king(agents):
  return argmax_k (wealth_exposed(k), tie-break by k.id asc)

assigned_knights_for(king):
  # Employer priority, then strongest free (if any exist)
  ordered := [knight where knight.employer == king.id] + sort_desc_by_defend([free_knights])
  return ordered[:1]   # exactly one currently
```

---

## F) Tick Ordering (same flow, made precise)

```yaml
tick(t):
  1) soup_drip()               # apply SOUP_DRIP to all agents
  2) trades()                  # each king invests 100 currency → +5 wealth (3 defend, 2 trade)
  3) pay_retainers()           # employer king → knight retainer_fee, if funds available
  4) for each mercenary in id order:
       king := pick_target_king()
       defenders := assigned_knights_for(king)
       # bribe gate
       case bribe_check(king, merc, defenders):
         - "accepted": record bribe event; continue
         - "insufficient_funds": proceed to contest()
         - "rejected": proceed to contest()
       # contest path (may be unopposed)
       contest(king, merc, defenders)
  5) clamp_nonnegative()       # currency, wealth never below zero
  6) snapshot_metrics()        # entropy, compression proxy, copy_score_mean, aggregates
```

**clamp_nonnegative():**
For each agent and each trait T: `wealth[T] := max(0, wealth[T])`; `currency := max(0, currency)`.

---

## G) Role Incentives (frozen, explicit priority lists)

```yaml
incentives:
  mercenary: [max_wealth_gain, then_currency_gain, then_raid_frequency, then_survival]
  knight:    [max_defend_success, then_currency, then_improve_defend/sense/adapt, then_survival]
  king:      [survive, then_defend_wealth, then_currency_buffer, then_wealth_growth_via_trade]
```

*(These are decision priorities already reflected in the target/bribe/contest ordering above; no new behavior.)*

---

## H) Data Validations & Invariants

```yaml
invariants:
  - currency >= 0
  - all wealth traits >= 0
  - no wealth or currency created/destroyed in contests except:
      * BRIBE transfer (king→merc) and BRIBE_LEAKAGE (reduces king wealth)
      * MIRRORED TRANSFER (king→merc) on defend_loss/unopposed_raid
      * BOUNTY transfer (merc→knight) on defend_win
      * TRADE wealth creation strictly per TRADE.created_wealth_units per king per tick
  - exactly one defending knight per attacking merc in current model
  - bribe_threshold is a posted scalar per king; unchanged during a tick
  - tie-breaks deterministic by lexicographic id where applicable
```

---

## I) Minimal Event Schema (for current variables only)

```yaml
event_types:
  - trait_drip {tick, agent, trait="copy", delta:int}
  - trade {tick, king, invest:int, wealth_created:int}
  - retainer {tick, employer, knight, amount:int}
  - bribe_accept {tick, king, merc, amount:int, rv:float}
  - bribe_insufficient_funds {tick, king, merc, threshold:int}
  - defend_win {tick, king, knight, merc, stake:int, p_knight:float}
  - defend_loss {tick, king, knight, merc, stake:int, p_knight:float}
  - unopposed_raid {tick, king, merc}
```

---

## J) One-Screen Pseudocode (deterministic, exactly what you have)

```text
for t in 1..T:
  # soup drip
  for a in Agents:
    if a.copy >= 12 and t % 2 == 0: a.copy += 1

  # trades
  for k in Kings:
    if k.currency >= 100:
      k.currency -= 100
      k.defend += 3
      k.trade  += 2

  # retainers
  for n in Knights with employer != "":
    k = Kings[n.employer]
    if k.currency >= n.retainer_fee:
      k.currency -= n.retainer_fee
      n.currency += n.retainer_fee

  # interactions
  for m in Mercenaries (id asc):
    k = argmax_k wealth_exposed(k); tie by id
    assigned = [employer knight if any else strongest free][:1]
    rv = raid_value(m, k, assigned)

    if k.bribe_threshold >= rv and k.currency >= k.bribe_threshold:
      k.currency -= k.bribe_threshold
      m.currency += k.bribe_threshold
      for T in wealth: k[T] = floor(k[T] * 0.95)
      log bribe_accept
      continue

    if assigned == []:
      # unopposed
      mirror (50% currency, 25% wealth) king → merc
      log unopposed_raid
      continue

    n = assigned[0]
    p = clamp(0.5 + sigmoid(0.3*((n.defend+n.sense+n.adapt)-(m.raid+m.sense+m.adapt))) - 0.5, 0.05, 0.95)
    s = floor(0.1 * (n.currency + m.currency))

    if (p > 0.5) or (p == 0.5 and n.id < m.id):
      n.currency += s; m.currency = max(0, m.currency - s)
      # bounty
      for T in [raid, adapt]: t_amt = floor(m[T]*0.07); m[T]-=t_amt; n[T]+=t_amt
      log defend_win
    else:
      mirror (50% currency, 25% wealth) king → merc
      n.currency = max(0, n.currency - s)
      if n.defend > 0: n.defend -= 1
      log defend_loss

  # clamps & metrics...
```
