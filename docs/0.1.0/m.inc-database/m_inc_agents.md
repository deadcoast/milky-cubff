# agents

## code

```python
# Create starter CSV/JSON datasets for Mercenaries Inc.
import json
import pandas as pd

# --- Agents seed (tick 0 / initial) ---
agents = [
    # Kings
    {
        "id": "K-01", "role": "king", "currency": 5400,
        "compute": 14, "copy": 16, "defend": 22, "raid": 3, "trade": 18, "sense": 7, "adapt": 9,
        "employer": "", "retainer_fee": "", "bribe_policy_mode": "threshold", "bribe_threshold": 350
    },
    {
        "id": "K-02", "role": "king", "currency": 7200,
        "compute": 10, "copy": 12, "defend": 18, "raid": 2, "trade": 22, "sense": 6, "adapt": 8,
        "employer": "", "retainer_fee": "", "bribe_policy_mode": "threshold", "bribe_threshold": 400
    },
    # Knights
    {
        "id": "N-07", "role": "knight", "currency": 210,
        "compute": 5, "copy": 3, "defend": 17, "raid": 2, "trade": 0, "sense": 9, "adapt": 6,
        "employer": "K-01", "retainer_fee": 25, "bribe_policy_mode": "", "bribe_threshold": ""
    },
    {
        "id": "N-11", "role": "knight", "currency": 160,
        "compute": 4, "copy": 2, "defend": 14, "raid": 1, "trade": 0, "sense": 8, "adapt": 5,
        "employer": "K-02", "retainer_fee": 20, "bribe_policy_mode": "", "bribe_threshold": ""
    },
    # Mercenaries
    {
        "id": "M-12", "role": "mercenary", "currency": 40,
        "compute": 2, "copy": 4, "defend": 1, "raid": 11, "trade": 0, "sense": 5, "adapt": 4,
        "employer": "", "retainer_fee": "", "bribe_policy_mode": "", "bribe_threshold": ""
    },
    {
        "id": "M-19", "role": "mercenary", "currency": 15,
        "compute": 1, "copy": 3, "defend": 0, "raid": 8, "trade": 0, "sense": 4, "adapt": 3,
        "employer": "", "retainer_fee": "", "bribe_policy_mode": "", "bribe_threshold": ""
    },
]

agents_df = pd.DataFrame(agents)
agents_csv_path = "/mnt/data/m_inc_agents.csv"
agents_df.to_csv(agents_csv_path, index=False)

# --- Three ticks of state snapshots ---
ticks = [
    # Tick 1: M-12 targets K-01. Bribe 350 < estimated raid_value (say ~380) -> bribe fails.
    # N-07 defends and wins  (knight win). Stakes transfer to N-07 from M-12.
    {
        "tick": 1,
        "metrics": {
            "entropy": 5.91, "compression_ratio": 2.70, "copy_score_mean": 0.64,
            "bribes_paid": 1, "bribes_accepted": 0,
            "raids_attempted": 2, "raids_won_by_merc": 0, "raids_won_by_knight": 1
        },
        "notes": [
            "K-01 offers 350 bribe to M-12; estimated raid_value≈380 → bribe rejected.",
            "N-07 defends K-01 and wins; stake gained.",
            "K-02 trades 200 currency→ +10 wealth (favoring defend/trade)."
        ],
        "agents": [
            {"id": "K-01", "currency": 5400, "wealth": {"compute":14,"copy":16,"defend":22,"raid":3,"trade":18,"sense":7,"adapt":9}},
            {"id": "K-02", "currency": 7000, "wealth": {"compute":10,"copy":12,"defend":19,"raid":2,"trade":26,"sense":6,"adapt":9}},
            {"id": "N-07", "currency": 230, "wealth": {"compute":5,"copy":3,"defend":17,"raid":2,"trade":0,"sense":9,"adapt":6}},
            {"id": "N-11", "currency": 180, "wealth": {"compute":4,"copy":2,"defend":14,"raid":1,"trade":0,"sense":8,"adapt":5}},
            {"id": "M-12", "currency": 30, "wealth": {"compute":2,"copy":4,"defend":1,"raid":11,"trade":0,"sense":5,"adapt":4}},
            {"id": "M-19", "currency": 15, "wealth": {"compute":1,"copy":3,"defend":0,"raid":8,"trade":0,"sense":4,"adapt":3}}
        ]
    },
    # Tick 2: M-19 targets K-02. Bribe 400 >= estimated raid_value (~320) -> bribe accepted.
    # Wealth leakage on king; bribe paid to M-19. K-01 performs small king↔king trade with K-02.
    {
        "tick": 2,
        "metrics": {
            "entropy": 5.76, "compression_ratio": 2.86, "copy_score_mean": 0.67,
            "bribes_paid": 1, "bribes_accepted": 1,
            "raids_attempted": 1, "raids_won_by_merc": 0, "raids_won_by_knight": 0
        },
        "notes": [
            "K-02 bribe threshold 400 ≥ estimated raid_value→ bribe accepted by M-19.",
            "K-02 wealth leakage ~3% applied; M-19 receives 400 currency.",
            "K-01 and K-02 trade: each invests 100 currency; each gains +5 wealth to defend/trade split."
        ],
        "agents": [
            {"id": "K-01", "currency": 5300, "wealth": {"compute":14,"copy":16,"defend":24,"raid":3,"trade":20,"sense":7,"adapt":9}},
            {"id": "K-02", "currency": 6500, "wealth": {"compute":10,"copy":12,"defend":20,"raid":2,"trade":27,"sense":6,"adapt":9}},
            {"id": "N-07", "currency": 255, "wealth": {"compute":5,"copy":3,"defend":17,"raid":2,"trade":0,"sense":9,"adapt":6}},
            {"id": "N-11", "currency": 200, "wealth": {"compute":4,"copy":2,"defend":14,"raid":1,"trade":0,"sense":8,"adapt":5}},
            {"id": "M-12", "currency": 35, "wealth": {"compute":2,"copy":5,"defend":1,"raid":11,"trade":0,"sense":5,"adapt":4}},
            {"id": "M-19", "currency": 415, "wealth": {"compute":1,"copy":3,"defend":0,"raid":8,"trade":0,"sense":4,"adapt":3}}
        ]
    },
    # Tick 3: M-12 and M-19 both target K-01. K-01 bribe 350; M-19 rejects (raid_value high), M-12 accepts.
    # Two defends: N-07 defends employer K-01 vs M-19 but loses; apply ON_FAILED_BRIBE losses to K-01.
    {
        "tick": 3
        "metrics": {
            "entropy": 5.48, "compression_ratio": 3.11, "copy_score_mean": 0.71,
            "bribes_paid": 1, "bribes_accepted": 1,
            "raids_attempted": 2, "raids_won_by_merc": 1, "raids_won_by_knight": 0
        },
        "notes": [
            "M-12 accepts bribe 350 from K-01; no raid from M-12 (no wealth loss, small leakage).",
            "M-19 rejects bribe; N-07 defends and loses → K-01 loses 50% currency and 25% wealth, mirrored to M-19.",
            "Minor bounty loss on N-07 from failed defend; equipment degradation."
        ],
        "agents": [
            {"id": "K-01", "currency": int(5300*0.5 - 350),  # 50% loss from failed defend vs M-19, and 350 paid to M-12
             "wealth": {"compute":11,"copy":12,"defend":18,"raid":2,"trade":15,"sense":5,"adapt":7}},
            {"id": "K-02", "currency": 6400, "wealth": {"compute":10,"copy":12,"defend":20,"raid":2,"trade":27,"sense":6,"adapt":9}},
            {"id": "N-07", "currency": 240, "wealth": {"compute":5,"copy":3,"defend":16,"raid":2,"trade":0,"sense":9,"adapt":6}},
            {"id": "N-11", "currency": 205, "wealth": {"compute":4,"copy":2,"defend":14,"raid":1,"trade":0,"sense":8,"adapt":5}},
            {"id": "M-12", "currency": 385, "wealth": {"compute":2,"copy":5,"defend":1,"raid":11,"trade":0,"sense":5,"adapt":4}},
            {"id": "M-19", "currency":  int(415 + (5300*0.5)),  # gains mirrored currency from K-01
             "wealth": {"compute":2,"copy":4,"defend":0,"raid":10,"trade":0,"sense":5,"adapt":4}}
        ]
    }
]

# Fix computed ints
for t in ticks:
    for a in t["agents"]:
        if isinstance(a["currency"], float):
            a["currency"] = int(a["currency"])

ticks_path = "/mnt/data/m_inc_ticks.json"
with open(ticks_path, "w", encoding="utf-8") as f:
    json.dump(ticks, f, indent=2)

agents_df
```

### Result

| g | id    | role   | currency | compute | copy | defend | raid | trade | sense |
|---|-------|--------|----------|---------|------|--------|------|-------|-------|
| 0 | K-01  | king   | 5400     | 14      | 16   | 22     | 3    | 18    | 7     |
| 1 | K-02  | king   | 7200     | 10      | 12   | 18     | 2    | 22    | 6     |
| 2 | N-07  | knight | 210      | 5       | 3    | 17     | 2    | 0     | 9     |
| 3 | N-11  | knight | 160      | 4       | 2    | 14     | 1    | 0     | 8     |
| 4 | M-12  | merc   | 40       | 2       | 4    | 1      | 11   | 0     | 5     |
| 5 | M-19  | merc   | 15       | 1       | 3    | 0      | 8    | 0     | 4     |

| g | adapt | employer | retainer_fee | bribe_policy_mode | bribe_threshold |
|---|-------|----------|--------------|-------------------|-----------------|
| 0 | 9     |          |              | threshold         | 350             |
| 1 | 8     |          |              | threshold         | 400             |
| 2 | 6     |    K-01  |    25        |                   |                 |
| 3 | 5     |    K-02  |    30        |                   |                 |
| 4 | 4     |          |              |                   |                 |
| 5 | 3     |          |              |                   |                 |
