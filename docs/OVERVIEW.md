# Mercenaries Incorporated (M|inc)  
## A Brainfuck-Derived Experiment on Emergent Economics and Digital Incentive Systems

---

## I. ORIGIN AND CONCEPTUAL BASIS

### 1. Lineage: Blaise Agüera y Arcas and the BFF Experiment
The BFF Experiment—designed by Blaise Agüera y Arcas—used the Brainfuck (BF) language to simulate *life emerging from entropy*.  
- It began with millions of random 64-byte tapes, most of which contained meaningless instructions.  
- Over millions of iterations, entropy dropped, compression increased, and self-replicating code emerged.  
- This marked the emergence of *purpose* from randomness: bytes evolved to copy themselves.

This experiment demonstrated that organization and function can emerge from chaos when replication, mutation, and selection exist—even in a minimalist computational substrate.

---

### 2. Expansion: From Reproduction to Incentive
`Mercenaries Incorporated` (abbreviated M|inc) extends Blaise’s concept from biological emergence to *economic emergence*.  
Instead of life forming from entropy, purposeful systems form from incentive and exchange.

#### Conceptual Evolution

| Layer | BFF Concept | Mercenaries Inc. Analogue |
|:------|:-------------|:---------------------------|
| Byte | Genetic atom | Trait (Wealth unit) |
| Reproduction | Copying tape | Accumulating Wealth |
| Entropy Drop | Compression of randomness | Economic order emerging |
| Purpose | Replication instinct | Incentive (Wealth, Survival) |

---

### 3. The Why — Why M|inc is Special
Unlike BFF, which focuses on *replication*, M|inc focuses on *strategic interaction*.  
Where the BFF tapes evolve to self-replicate, the M|inc agents evolve to survive through asymmetric incentive loops:  
- Kings generate order and wealth.  
- Knights defend that order.  
- Mercenaries exploit its weaknesses.

This transforms a digital entropy field into a living micro-economy, where evolution selects for strategic intelligence rather than biological persistence.

---

### 4. The Result
M|inc will produce:
- Emergent *economic ecosystems* rather than biological ones.  
- Self-stabilizing behaviors: corruption, defense, parasitism, and cooperation.  
- Simulated analogues of trust, wealth concentration, and collapse cycles.  
- Observable entropy–order transitions expressed through currency–wealth ratios.

```json
"unique_results": {
  "emergent_markets": "Self-organizing exchange systems between autonomous agents.",
  "strategic_ecosystems": "Reinforcement of defensive or predatory incentives through stable equilibria.",
  "economic_entropy_dynamics": "Observable transitions between chaos and stable trade loops.",
  "applied_use_cases": [
    "Economic modeling for AI swarms or distributed agent systems",
    "AI ethics simulations (resource-driven behaviors)",
    "Synthetic market equilibrium testing",
    "Autonomous systems behavior research"
  ]
}
```

---

## II. HOW IT OPERATES

### 1. The Digital World

Like BFF, the base environment is a soup of tapes:

- Each tape = 64 bytes.
- Each agent owns 1–3 tapes.
- 31/32 of bytes are no-ops (entropy background).
- Self-modification and mutation are allowed.

Over time, the system evolves toward lower entropy and higher organization—but here, that organization takes the form of economic behavior.

---

### 2. The Economic Species

#### Roles

- King – Generates wealth, manages currency, can trade or bribe.
- Knight – Defends kings for retainer currency, earns through success in conflict.
- Mercenary – Predatory raider seeking to accumulate wealth and currency.

Each role follows a distinct incentive hierarchy:

| Role      | Incentive Priority (Descending)                                        |
| --------- | ---------------------------------------------------------------------- |
| King      | Survive → Defend Wealth → Maintain Currency → Grow via Trade           |
| Knight    | Win Defends → Earn Currency → Grow Defend/Sense/Adapt Traits → Survive |
| Mercenary | Gain Wealth → Gain Currency → Raid Frequency → Survive                 |

---

### 3. The Core Logic

#### 3.1 Incentive

Acts as the motivational vector for each agent type.

- Mercenary: `incentive = wealth++ + currency++ + raid++ + survive--`
- Knight: `incentive = defend_success++ + wealth++ + employment++`
- King: `incentive = survive++ + defend++ + trade++`

---

#### 3.2 Wealth (Traits)

Represents quantifiable *capabilities*.
Each agent tracks seven wealth traits:

```yaml
wealth = {
  compute, copy, defend, raid, trade, sense, adapt
}
```

- Total wealth = sum of all seven traits.
- Wealth can be *created* (via trade), *transferred* (via raids, bribes), or *leaked* (via corruption and entropy).

---

#### 3.3 Currency

Fungible resource connecting all roles.

- Kings can trade 100 currency → +5 wealth (3 defend, 2 trade).
- Knights earn currency from kings (retainers) or from stakes in successful defends.
- Mercenaries gain currency from raids, bribes, or mirrored king losses.

Conversion Ratio

```
100 currency = 5 wealth units
```

---

#### 3.4 Bribes (King → Mercenary)

Bribe Check:

```
if (bribe_threshold >= raid_value) and (currency >= threshold)
  -> success
else
  -> contest (defend/raid)
```

Outcomes:

- Success: merc accepts, no raid.
  `king.currency -= bribe; merc.currency += bribe; king.wealth *= 0.95`
- Fail: insufficient or smaller bribe — merc raids king.
  `king loses 50% currency, 25% wealth (mirrored to merc).`

---

#### 3.5 Defend (Knight ↔ Mercenary)

When contesting a raid:

```
p_knight_win = clamp(0.05, 0.95,
  0.5 + (sigmoid(0.3 * ((knight.defend+knight.sense+knight.adapt)
                       - (merc.raid+merc.sense+merc.adapt))) - 0.5))
)
```

Outcome:

- If `p_knight_win > 0.5`: knight wins, earns stake (10% of combined currency), gains bounty (7% of merc raid/adapt).
- If `p_knight_win < 0.5`: merc wins, king loses mirrored wealth and currency, knight loses stake and -1 defend.

---

#### 3.6 Raid Value (Deterministic)

```
raid_value = 1.0*merc.raid + 0.25*(merc.sense+merc.adapt)
            - 0.60*(king_defend_projection)
            + 0.40*(king_wealth_exposed)
```

Where:

```
king_defend_projection = Σ(knight.defend + 0.5*sense + 0.5*adapt)
king_wealth_exposed = total_wealth * exposure_factor(king=1.0)
```

---

#### 3.7 Entropy Mechanics

Every tick simulates one evolutionary step:

1. Combine two tapes → run → split → reinsert.
2. Apply small mutations (`0.1%` rate).
3. Agents gain trait bonuses from emergent tape activity (`copy >= 12 → +1 copy every 2 ticks`).

Over time:

- Entropy ↓
- Compression ↑
- Order Emerges

---

## III. DATA REQUIREMENTS AND OUTPUT STRUCTURE

### JSON File — Per-Tick Snapshots

Contains all agent states and metrics.

Example:

```json
[
  {
    "tick": 10,
    "metrics": {
      "entropy": 6.08,
      "compression_ratio": 3.00,
      "copy_score_mean": 0.417,
      "wealth_total": 399,
      "currency_total": 12187
    },
    "agents": [
      {"id":"K-01","role":"king","currency":4400,"wealth":{"compute":14,"copy":17,"defend":25,"raid":3,"trade":20,"sense":7,"adapt":9}},
      {"id":"M-12","role":"mercenary","currency":0,"wealth":{"compute":2,"copy":5,"defend":1,"raid":11,"trade":0,"sense":5,"adapt":4}}
    ]
  }
]
```

---

### CSV File — Event Log

Each row records a significant system interaction.

| tick | type         | king | knight | merc | amount | stake | p_knight | notes                |
| ---- | ------------ | ---- | ------ | ---- | ------ | ----- | -------- | -------------------- |
| 3    | bribe_accept | K-01 |        | M-12 | 350    |       |          | success, wealth leak |
| 3    | defend_loss  | K-01 | N-07   | M-19 |        | 250   | 0.48     | mirrored loss        |
| 4    | trade        | K-02 |        |      | 100    |       |          | +5 wealth            |

---

### CSV File — Final Agent Table

Snapshot after 10 ticks, representing evolved state.

| id   | role      | currency | compute | copy | defend | raid | trade | sense | adapt | wealth_total |
| ---- | --------- | -------- | ------- | ---- | ------ | ---- | ----- | ----- | ----- | ------------ |
| K-01 | king      | 4400     | 14      | 17   | 25     | 3    | 20    | 7     | 9     | 95           |
| K-02 | king      | 6200     | 10      | 13   | 22     | 2    | 26    | 6     | 9     | 88           |
| N-07 | knight    | 1427     | 5       | 3    | 19     | 2    | 0     | 9     | 6     | 44           |
| M-12 | mercenary | 0        | 2       | 5    | 1      | 11   | 0     | 5     | 4     | 28           |

---

## IV. UNIQUENESS AND APPLICATION

### Unique Operations

- Deterministic economic evolution: agents adapt not biologically, but economically.
- Every transaction modifies entropy → compression → emergent order.
- Traits evolve as if through economic natural selection.

### Why It’s Unique

Where typical simulations model *agent intelligence* through reinforcement learning,
M|inc models intelligence through incentive structure.

### Unique Results

```json
{
  "unique_results": {
    "emergent_markets": "Agents spontaneously form trade and defense economies.",
    "strategic_ecosystems": "Stable alliances and parasitic cycles emerge naturally.",
    "economic_entropy_dynamics": "Entropy–order transitions measurable through wealth and compression ratios.",
    "applied_use_cases": [
      "Autonomous economic AI testing",
      "Synthetic behavior evolution in resource systems",
      "Entropy-based equilibrium modeling",
      "Experimental incentive systems for AI ecosystems"
    ]
  }
}
```

---

## V. TARGETS

### Human Consumption

- Designed as a readable project overview + data dictionary.
- Enables straightforward continuation and implementation.
- Maintains consistent logic across economy, incentive, and emergence.

### AI Agent Consumption

- Structured for direct ingestion:

    - Deterministic formulas.
    - Defined invariants.
    - JSON/CSV schemas ready for automation.

Purpose:
To form a bridge between *emergent computation* and *economic simulation*—
demonstrating that in the same way replication can emerge from entropy, economy can emerge from incentive.

---
