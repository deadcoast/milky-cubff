---
title: "M|inc JSON and CSV Schemas"
description: "Schemas for per-tick snapshots and event logs (0.1.1)"
version: "0.1.1"
last_updated: "2025-10-30"
---

## JSON: Per-Tick Snapshot

```json
{
  "macro_tick": 1,
  "tick": 10,
  "metrics": {
    "entropy": 6.08,
    "compression_ratio": 3.00,
    "copy_score_mean": 0.417,
    "wealth_total": 399,
    "currency_total": 12187
  },
  "meta": {
    "config_version": "0.1.1",
    "config_hash": "<sha256>",
    "adapter_version": "0.1.1"
  },
  "agents": [
    {
      "id": "K-01",
      "role": "king",
      "currency": 4400,
      "wealth": {"compute":14, "copy":17, "defend":25, "raid":3, "trade":20, "sense":7, "adapt":9}
    }
  ],
  "cache": {"hits": 42, "misses": 7},
  "micro_events": [
    {"idx":0, "channel":"raid", "priority":2, "ref":"M-12->K-01"}
  ]
}
```

- roles: enum [king, knight, mercenary]
- wealth: object with seven integer fields

## CSV: Event Log

Columns:

- tick:int, macro_tick:int, micro_idx:int, channel:str, priority:int, type:str, king:str, knight:str, merc:str, amount:int, stake:int, p_knight:float, notes:str

Example rows:

```
tick,macro_tick,micro_idx,channel,priority,type,king,knight,merc,amount,stake,p_knight,notes
3,1,0,bribe,1,bribe_accept,K-01,,M-12,350,,, 
3,1,1,defend,2,defend_loss,K-01,N-07,M-19,,250,0.48,mirrored loss
4,1,2,trade,0,trade,K-02,,,,100,,, 
```

## Deterministic Functions (Reference)

- raid_value(merc, king, knights)
- p_knight_win(knight, merc)
- bribe_outcome(king, merc, threshold)
- trade_action(king, amount)

These functions are pure and must be reproducible given the same inputs.
