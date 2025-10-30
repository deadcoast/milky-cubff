Got it — here’s a tight, complete rules + data spec you can drop in as v0.1.1 – Mercenaries Inc.. It keeps things general (not code-heavy), but precise enough that you can implement directly when you’re ready.

# Mercenaries Inc. — Rule & Data Spec (v0.1.1)

## 0) Glossary

* Tape: 64-byte genome (self-modifying BF variant). Two tapes temporarily concatenate to 128 bytes during execution.
* Trait: An atomic capability or property encoded/held by a tape; aggregated as wealth.
* Wealth: Multiset/vector of traits owned by an agent (king/knight/mercenary).
* Currency: Fungible unit used only by kings and knights; mercenaries cannot trade, only receive bribes or loot.
* Incentive: Priority function that ranks agent choices.

---

## 1) Tunables (global constants)

```yaml
version: "m.inc/0.1.1"

# Tape soup
TAPE_BYTES: 64
PAIR_BYTES: 128
NOOP_FRACTION: 31/32
POOL_SIZE: 1_000_000           # conceptual scale, not prescriptive
MUTATION_RATE: 0.001           # per-byte per run, configurable
SELF_MOD_WINDOW: true          # permit writes to the active 128B window

# Economy
CURRENCY_TO_WEALTH_RATIO: 100:5  # 100 currency -> 5 wealth (traits) via trade between kings only
BRIBE_MIN_UNIT: 1
BRIBE_OFFER_MODE: "threshold"    # king pre-commits a % threshold to match/beat raid value
BRIBE_LEAKAGE: 0.05              # king loses this fraction of wealth even on a successful bribe (friction)

# Conflict outcomes
ON_FAILED_BRIBE:
  KING_CURRENCY_LOSS: 0.50       # 50% currency
  KING_WEALTH_LOSS:   0.25       # 25% wealth
  MERC_CURRENCY_GAIN: "mirror"   # gains the king’s lost currency
  MERC_WEALTH_GAIN:   "mirror"   # gains the king’s lost wealth

ON_SUCCESSFUL_BRIBE:
  KING_CURRENCY_LOSS: "bribe_amount"
  KING_WEALTH_LEAK:   0.02..0.08 # sample in [0.02, 0.08] around BRIBE_LEAKAGE
  MERC_CURRENCY_GAIN: "bribe_amount"
  MERC_WEALTH_GAIN:   0

# Knight–Mercenary defend/raid contest
DEFEND_RESOLUTION:
  BASE_WINRATE_KNIGHT: 0.50      # symmetric default before modifiers
  TRAIT_ADVANTAGE_WEIGHT: 0.30   # how strongly trait deltas tilt odds
  CURRENCY_STAKE_FACTOR: 0.10    # currency wager scaling from participants

# Reproduction & fitness
REPRODUCTION_THRESHOLD:
  ENTROPY_DROP: "significant"    # detectable compression drop
  COPY_SCORE_MIN: 0.8            # 0..1 heuristic for “is copying itself”
FITNESS_WEIGHTS:
  SURVIVAL: 0.25
  REPRODUCTION: 0.35
  WEALTH_ACCUMULATION: 0.25
  CURRENCY_BALANCE: 0.15
```

---

## 2) Core Sets & Types

```yaml
Roles: [king, knight, mercenary]

TraitTypes:
  # Keep abstract; implementations can map to BF motifs, I/O skill, memory ops, etc.
  - compute
  - copy
  - defend
  - raid
  - trade
  - sense
  - adapt

WealthVector:
  # Map TraitType -> nonnegative integer
  compute: int
  copy: int
  defend: int
  raid: int
  trade: int
  sense: int
  adapt: int

Currency: int >= 0

IncentiveProfile:
  # Role priorities (normalized weights, but you may keep ordinal semantics)
  king:     [survive, defend_wealth, maintain_currency, grow_wealth]
  knight:   [win_defends, earn_fees, enhance_defend_traits, survive]
  mercenary:[gain_wealth, gain_currency, raid_frequency, survive]

Agent:
  id: UUID
  role: Role
  tape_ids: [UUID, ...]         # 1..N tapes attributed to the agent
  wealth: WealthVector
  currency: Currency
  incentive: IncentiveProfile
  bindings:
    # Optional stable relationships
    employer: king_id|null       # for knights
    retainer_fee: int            # periodic king->knight currency
```

---

## 3) Initialization

```yaml
Init:
  # Kings start strong, Knights modest, Mercenaries hungry
  kings:
    count: K
    wealth: ~High (e.g., sum(wealth)=80..120)
    currency: ~High (e.g., 2_000..10_000)
    incentive: king default
  knights:
    count: N
    wealth: ~Medium (sum=20..40, defend>=raid)
    currency: ~Low/Medium (100..500)
    incentive: knight default
    employer: optional king_id
    retainer_fee: optional (10..50 per cycle)
  mercenaries:
    count: M
    wealth: ~Low (sum=5..15, raid>=defend)
    currency: 0
    incentive: mercenary default

  tapes:
    per_agent: 1..3
    bytes: random with NOOP_FRACTION
    mutation_rate: MUTATION_RATE
```

---

## 4) Economy Rules

[R-E1] Currency↔Wealth conversion (kings only).

* Only king–king trades permitted.
* Fixed global ratio: 100 currency → 5 wealth.
* Wealth created via trade is modeled as augmenting existing TraitTypes, typically favoring `trade`, `defend`, or `copy` based on king preference.
* Mercenaries cannot trade. Knights do not trade; they earn via fees/outcomes.

[R-E2] Bribe semantics (king → mercenary).

* A king can post a bribe policy: “pay ≥ X currency if targeted.”
* When a mercenary selects a king to raid, compare bribe_amount vs raid_value (derived from merc’s `raid` strength vs king’s exposed wealth, see [R-C3]).
* If `bribe_amount ≥ raid_value`: successful bribe → merc takes bribe, does not raid. King suffers wealth leakage (systemic friction).
* Else: failed bribe → normal raid resolution; losses per `ON_FAILED_BRIBE`.

[R-E3] Retainers (king → knight).

* Optional periodic fee `retainer_fee` deducted from king → knight.
* Knight gives priority defend to that king when scheduling conflicts arise.

---

## 5) Interaction Rules (Conflict & Choice)

[R-C1] Target selection (mercenary).

* A mercenary evaluates candidate kings using incentive (wealth gain > currency gain > raid frequency > survival).
* Expected raid value is estimated from:
  `E[raid_value] = f(merc.raid, king.defend, king.wealth_visible, historic_outcomes)`
* If a posted bribe exists and `bribe_amount ≥ E[raid_value]`, the mercenary accepts bribe (no raid). Otherwise, attempt raid.

[R-C2] Knight scheduling.

* Knights prioritize defends for their employer; otherwise market-match (auction/queue) to kings under attack.

[R-C3] Raid vs Defend resolution.

* If no knight defends: apply ON_FAILED_BRIBE losses directly (mercenary succeeds by default), unless bribe succeeded.
* If a knight defends, compute win odds for the knight:

  ```
  base = DEFEND_RESOLUTION.BASE_WINRATE_KNIGHT
  trait_delta = (knight.defend + knight.sense + knight.adapt) 
                - (merc.raid + merc.sense + merc.adapt)
  modifier = sigmoid(trait_delta * DEFEND_RESOLUTION.TRAIT_ADVANTAGE_WEIGHT)
  P_knight_win = clamp(base + modifier - 0.5, 0.05, 0.95)
  ```

    * Draw outcome ~ Bernoulli(P_knight_win).
    * Currency stakes: each side auto-stakes

    ```
    stake = floor( CURRENCY_STAKE_FACTOR * (knight.currency + merc.currency) )
    ```
    * If knight wins:

        * knight.currency += stake
        * merc.currency -= stake (not below 0)
        * knight may loot a small wealth slice (e.g., 5–10%) from merc’s `raid` or `adapt` as “bounty.”
        * king loses nothing further this tick.
    * If mercenary wins:

        * apply ON_FAILED_BRIBE to king
        * mercenary receives the mirrored gains
        * knight loses stake and may suffer minor wealth loss in `defend` (equipment degradation).

[R-C4] Multi-mercenary collisions.

* If multiple mercenaries target same king in the same tick:

    * Bribe is first-come or split per posted policy.
    * Defend matches one knight per merc if available.
    * If insufficient knights, unresolved raids succeed unless bribed off.

---

## 6) Incentives (per role)

[R-I1] Mercenary incentive (lexicographic):

1. Maximize expected wealth gain (via raids)
2. Then currency gain (via bribes/loot)
3. Then raid frequency (keep hunting)
4. Then survival

[R-I2] Knight incentive:

1. Maximize successful defends (win rate and count)
2. Earn currency (retainers, stakes, bounties)
3. Improve defend/sense/adapt traits
4. Survival

[R-I3] King incentive:

1. Survive (minimize catastrophic losses)
2. Defend wealth (traits)
3. Maintain currency buffer
4. Grow wealth via king↔king trade

---

## 7) Workflow / Tick Cycle

Each tick consists of:

1. Soup step (BFF core)

   * Randomly pluck two tapes from the pool.
   * Concatenate → 128B pair, run (self-mod allowed), split, return to pool.
   * Apply stochastic mutation.
   * Track compression/entropy and copy-score; when programs emerge (REPRODUCTION_THRESHOLD), attribute replicated/beneficial motifs to the agents that own those tapes.

2. Attribution & Earnings

   * If a tape demonstrably copies or improves motifs relevant to `copy`, `trade`, `defend`, `raid`, or `adapt`, increment the owning agent’s corresponding wealth traits (small deltas).
   * This is the bridge from BF emergence → trait economy.

3. Declarations

   * Kings post/update bribe policy and (optional) retainer fees.
   * Knights may change employer if unpaid or better offers exist.
   * Kings execute trade with other kings (currency→wealth).

4. Targeting

   * Mercenaries pick kings (see [R-C1]).
   * Kings auto-seek available knights if threatened.

5. Resolution

   * Bribe checks → either accept or contest.
   * Knight–Merc conflicts resolved via [R-C3].
   * Apply losses/gains.

6. Upkeep

   * Apply retainer fees.
   * Apply wealth leakage where relevant.
   * Non-negative clamps for currency/traits.

7. Metrics

   * Record per-tick: entropy, compression ratio, copy-score distribution, role survival counts, total wealth/currency, conflict outcomes, bribes paid/accepted.

---

## 8) Derived Quantities & Heuristics

```yaml
Derived:
  raid_value(merc, king):
    # Not an absolute formula; use as a general heuristic
    = α*(merc.wealth.raid) 
    + β*(merc.wealth.sense + merc.wealth.adapt)
    - γ*(king_defend_projection)
    + δ*(king.wealth_total_exposed)

  king_defend_projection(king, assigned_knights):
    = sum over knights [ k.defend + 0.5*k.sense + 0.5*k.adapt ]
      * min(1, assigned_knights / attackers)

  wealth_total_exposed(agent):
    = sum(agent.wealth.values) * exposure_factor(agent.role)
    # Kings typically have higher exposure_factor than mercs/knights.

  fitness(agent):
    = w1*survival_norm
    + w2*reproduction_norm
    + w3*wealth_norm
    + w4*currency_norm
    # weights from FITNESS_WEIGHTS
```

*(α..δ, exposure_factor) are implementation knobs; keep them simple at first.)*

---

## 9) Edge Conditions

* Zero-defend kings are soft targets; expect higher raid frequency until they adopt bribes, hire knights, or trade into `defend`.
* Mercenary starvation (no bribes, strong knight coverage) naturally drives them to gang up on the weakest king or evolve higher `raid`.
* Knight market failure (kings refuse retainers) → kings must rely on bribes; expect rising wealth leakage even when bribes succeed.
* Compression plateau: if entropy stops dropping, temporarily boost mutation rate or allow role drift (agents can retune trait goals).

---

## 10) Data Blocks (canonical “all variables and data” scaffold)

You can keep one state file per tick like:

```yaml
state:
  tick: 000123
  metrics:
    entropy: 5.91
    compression_ratio: 2.7
    copy_score_mean: 0.64
    bribes_paid: 3
    bribes_accepted: 2
    raids_attempted: 5
    raids_won_by_merc: 2
    raids_won_by_knight: 3

  agents:
    - id: K-01
      role: king
      currency: 5400
      wealth:
        compute: 14
        copy: 16
        defend: 22
        raid: 3
        trade: 18
        sense: 7
        adapt: 9
      bribe_policy:
        mode: threshold
        threshold: 350     # currency offered if targeted
      retainers:
        - knight_id: N-07
          fee: 25

    - id: N-07
      role: knight
      employer: K-01
      currency: 210
      wealth:
        compute: 5
        copy: 3
        defend: 17
        raid: 2
        trade: 0
        sense: 9
        adapt: 6

    - id: M-12
      role: mercenary
      currency: 40
      wealth:
        compute: 2
        copy: 4
        defend: 1
        raid: 11
        trade: 0
        sense: 5
        adapt: 4
      last_targets: [K-01, K-03]
```

---

## 11) Rule IDs (quick reference)

* Economy: R-E1 (king trade), R-E2 (bribes), R-E3 (retainers)
* Conflict/Choice: R-C1 (merc targeting), R-C2 (knight scheduling), R-C3 (raid/defend resolution), R-C4 (multi-merc collisions)
* Incentives: R-I1/2/3 (role priorities)

---

## 12) Minimal References (conceptual anchors)

* BFF “byte soup” → entropy drop & emergent copying (use as the reproduction signal and trait drip).
* Conway/Hashlife/Wireworld → intuition for emergence and locality; we borrow only the idea of macro-metrics (e.g., compressibility), not their mechanics.
* Market games / bribery → use threshold bribes as stabilizing force against raids.

---
