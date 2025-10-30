# Deterministic loop

```python
# Deterministic simulation loop for Mercenaries Inc.
# - Loads agents from CSV created earlier if available; otherwise seeds defaults.
# - Runs a deterministic tick loop with fixed parameters and writes results to JSON/CSV.
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from math import exp
import pandas as pd
from pathlib import Path
import random

DATA_DIR = Path("/mnt/data")

AGENTS_CSV = DATA_DIR / "m_inc_agents.csv"
TICKS_JSON = DATA_DIR / "m_inc_run_ticks.json"
EVENTS_CSV = DATA_DIR / "m_inc_events.csv"
FINAL_AGENTS_CSV = DATA_DIR / "m_inc_agents_final.csv"

WEALTH_KEYS = ["compute","copy","defend","raid","trade","sense","adapt"]

# --- Deterministic knobs (no randomness except seed for tie-breaks) ---
SEED = 1337
rng = random.Random(SEED)

CURRENCY_TO_WEALTH_RATIO = (100,5)  # 100 currency -> +5 total wealth units
BRIBE_LEAKAGE_RANGE = (0.02, 0.08)  # we will pick deterministic mid (0.05)
BRIBE_LEAKAGE = sum(BRIBE_LEAKAGE_RANGE)/2.0

ON_FAILED_BRIBE = {
    "KING_CURRENCY_LOSS": 0.50,
    "KING_WEALTH_LOSS":   0.25,
    "MERC_CURRENCY_GAIN": "mirror",
    "MERC_WEALTH_GAIN":   "mirror",
}

DEFEND = {
    "BASE_WINRATE_KNIGHT": 0.50,
    "TRAIT_ADVANTAGE_WEIGHT": 0.30,
    "CURRENCY_STAKE_FACTOR": 0.10,
}

# Raid value weights (deterministic)
ALPHA_RAID = 1.0   # merc.raid
BETA_SENSE_ADAPT = 0.25
GAMMA_KING_DEFEND = 0.60
DELTA_KING_EXPOSE = 0.40

EXPOSURE_FACTOR = {"king": 1.0, "knight": 0.5, "mercenary": 0.4}

# Trade policy: each king invests TRADE_INVEST per tick if currency allows
TRADE_INVEST = 100  # currency
# Distribution of +5 wealth units when trade fires: favor defend/trade
TRADE_DISTRIBUTION = [("defend", 3), ("trade", 2)]  # totals to 5

# Retainer fee collected every tick if present
# Already encoded in agents: retainer_fee

@dataclass
class Agent:
    id: str
    role: str
    currency: int
    compute: int
    copy: int
    defend: int
    raid: int
    trade: int
    sense: int
    adapt: int
    employer: str = ""
    retainer_fee: int | str = ""
    bribe_policy_mode: str = ""
    bribe_threshold: int | str = ""
    # runtime fields
    alive: bool = True

    def wealth_total(self) -> int:
        return sum(getattr(self, k) for k in WEALTH_KEYS)

    def to_wealth_dict(self) -> Dict[str, int]:
        return {k: getattr(self, k) for k in WEALTH_KEYS}

    def add_wealth(self, key: str, amt: int):
        setattr(self, key, max(0, getattr(self, key) + amt))

    def scale_wealth(self, frac: float):
        # scale each trait by (1 - frac) rounding down deterministically
        for k in WEALTH_KEYS:
            new_val = int(getattr(self, k) * (1.0 - frac))
            setattr(self, k, new_val)

def load_agents() -> Dict[str, Agent]:
    if AGENTS_CSV.exists():
        df = pd.read_csv(AGENTS_CSV)
    else:
        # seed defaults (same as earlier CSV)
        df = pd.DataFrame([
            {"id":"K-01","role":"king","currency":5400,"compute":14,"copy":16,"defend":22,"raid":3,"trade":18,"sense":7,"adapt":9,"employer":"","retainer_fee":"","bribe_policy_mode":"threshold","bribe_threshold":350},
            {"id":"K-02","role":"king","currency":7200,"compute":10,"copy":12,"defend":18,"raid":2,"trade":22,"sense":6,"adapt":8,"employer":"","retainer_fee":"","bribe_policy_mode":"threshold","bribe_threshold":400},
            {"id":"N-07","role":"knight","currency":210,"compute":5,"copy":3,"defend":17,"raid":2,"trade":0,"sense":9,"adapt":6,"employer":"K-01","retainer_fee":25,"bribe_policy_mode":"","bribe_threshold":""},
            {"id":"N-11","role":"knight","currency":160,"compute":4,"copy":2,"defend":14,"raid":1,"trade":0,"sense":8,"adapt":5,"employer":"K-02","retainer_fee":20,"bribe_policy_mode":"","bribe_threshold":""},
            {"id":"M-12","role":"mercenary","currency":40,"compute":2,"copy":4,"defend":1,"raid":11,"trade":0,"sense":5,"adapt":4,"employer":"","retainer_fee":"","bribe_policy_mode":"","bribe_threshold":""},
            {"id":"M-19","role":"mercenary","currency":15,"compute":1,"copy":3,"defend":0,"raid":8,"trade":0,"sense":4,"adapt":3,"employer":"","retainer_fee":"","bribe_policy_mode":"","bribe_threshold":""},
        ])
    agents = {}
    for rec in df.to_dict(orient="records"):
        # normalize blanks
        rt = int(rec["retainer_fee"]) if str(rec.get("retainer_fee","")).strip().isdigit() else 0
        bt = int(rec["bribe_threshold"]) if str(rec.get("bribe_threshold","")).strip().isdigit() else 0
        a = Agent(
            id=rec["id"], role=rec["role"], currency=int(rec["currency"]),
            compute=int(rec["compute"]), copy=int(rec["copy"]), defend=int(rec["defend"]),
            raid=int(rec["raid"]), trade=int(rec["trade"]), sense=int(rec["sense"]), adapt=int(rec["adapt"]),
            employer=str(rec.get("employer","")) or "",
            retainer_fee=rt, bribe_policy_mode=str(rec.get("bribe_policy_mode","")) or "",
            bribe_threshold=bt
        )
        agents[a.id] = a
    return agents

def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + exp(-x))

def king_defend_projection(king: Agent, knights: List[Agent], attackers: int) -> float:
    if attackers <= 0: attackers = 1
    score = sum(k.defend + 0.5*k.sense + 0.5*k.adapt for k in knights)
    # normalize by attackers
    return score * min(1.0, len(knights)/attackers)

def wealth_exposed(agent: Agent) -> float:
    return agent.wealth_total() * EXPOSURE_FACTOR.get(agent.role, 1.0)

def raid_value(merc: Agent, king: Agent, assigned_knights: List[Agent]) -> float:
    kd = king_defend_projection(king, assigned_knights, attackers=1)
    val = (
        ALPHA_RAID * merc.raid +
        BETA_SENSE_ADAPT * (merc.sense + merc.adapt) -
        GAMMA_KING_DEFEND * kd +
        DELTA_KING_EXPOSE * wealth_exposed(king)
    )
    return max(0.0, val)

def stake_amount(knight: Agent, merc: Agent) -> int:
    return int(DEFEND["CURRENCY_STAKE_FACTOR"] * (knight.currency + merc.currency))

def resolve_defend(knight: Agent, merc: Agent) -> Tuple[str, float]:
    base = DEFEND["BASE_WINRATE_KNIGHT"]
    trait_delta = (knight.defend + knight.sense + knight.adapt) - (merc.raid + merc.sense + merc.adapt)
    modifier = (sigmoid(trait_delta * DEFEND["TRAIT_ADVANTAGE_WEIGHT"]) - 0.5)  # roughly -0.5..+0.5
    p_knight = max(0.05, min(0.95, base + modifier))
    # Deterministic outcome: knight wins iff p_knight >= 0.5; on exact tie use id lexical order as tiebreaker
    outcome = "knight" if (p_knight > 0.5 or (abs(p_knight - 0.5) < 1e-9 and knight.id < merc.id)) else "merc"
    return outcome, p_knight

def apply_trade(king: Agent, invest: int = TRADE_INVEST):
    if king.currency < invest: return 0
    king.currency -= invest
    # +5 total wealth per 100 invested
    created = (CURRENCY_TO_WEALTH_RATIO[1])
    # Distribute deterministically per TRADE_DISTRIBUTION
    used = 0
    for k, amt in TRADE_DISTRIBUTION:
        give = min(amt, created - used)
        if give > 0:
            king.add_wealth(k, give)
            used += give
    # Any remainder (shouldn't happen with 3+2) go to defend
    if used < created:
        king.add_wealth("defend", created - used)
    return created

def wealth_leakage(king: Agent, leak_frac: float = BRIBE_LEAKAGE):
    # leak across all traits
    king.scale_wealth(leak_frac)

def mirror_transfer_from_king_to_merc(king: Agent, merc: Agent):
    # Currency mirror
    lose_c = int(king.currency * ON_FAILED_BRIBE["KING_CURRENCY_LOSS"])
    king.currency -= lose_c
    merc.currency += lose_c
    # Wealth mirror
    for k in WEALTH_KEYS:
        lose_w = int(getattr(king, k) * ON_FAILED_BRIBE["KING_WEALTH_LOSS"])
        if lose_w > 0:
            king.add_wealth(k, -lose_w)
            merc.add_wealth(k, lose_w)

def bounty_to_knight(knight: Agent, merc: Agent, frac: float = 0.07):
    # Knight takes small bounty from merc raid/adapt
    for k in ("raid", "adapt"):
        amt = int(getattr(merc, k) * frac)
        if amt > 0:
            merc.add_wealth(k, -amt)
            knight.add_wealth(k, amt)

def pay_retainers(agents: Dict[str, Agent], events: List[Dict], tick: int):
    for a in agents.values():
        if a.role == "knight" and a.employer:
            k = agents.get(a.employer)
            if k and k.currency >= int(a.retainer_fee):
                k.currency -= int(a.retainer_fee)
                a.currency += int(a.retainer_fee)
                events.append({"tick": tick, "type": "retainer", "employer": k.id, "knight": a.id, "amount": int(a.retainer_fee)})

def available_knights_for_king(agents: Dict[str, Agent], king_id: str) -> List[Agent]:
    # Employer first; else strongest available knight by defend
    owned = [a for a in agents.values() if a.role=="knight" and a.employer==king_id]
    free = [a for a in agents.values() if a.role=="knight" and a.employer=="" ]  # none in seed, but logic stands
    # Sort free by defend desc
    free.sort(key=lambda x: (-x.defend, x.id))
    return owned + free

def pick_target_king(agents: Dict[str, Agent]) -> Optional[Agent]:
    # Deterministic selection: pick king with highest wealth_exposed, tie by id
    kings = [a for a in agents.values() if a.role=="king" and a.alive]
    if not kings: return None
    kings.sort(key=lambda k: (-wealth_exposed(k), k.id))
    return kings[0]

def soup_step_and_trait_drip(agents: Dict[str, Agent], events: List[Dict], tick: int):
    # Deterministic "emergence" drip: if an agent's copy >= 12, add +1 copy to that agent every other tick
    for a in agents.values():
        if a.copy >= 12 and tick % 2 == 0:
            a.copy += 1
            events.append({"tick": tick, "type": "trait_drip", "agent": a.id, "trait": "copy", "delta": 1})

def snapshot_metrics(agents: Dict[str, Agent], tick: int) -> Dict[str, float]:
    # Deterministic proxy metrics
    total_wealth = sum(a.wealth_total() for a in agents.values())
    total_currency = sum(a.currency for a in agents.values())
    # simple compression proxy increases slowly
    compression_ratio = 2.5 + 0.05 * tick
    entropy = 6.2 - 0.24 * (compression_ratio - 2.5)  # descending with compression
    copy_mean = sum(a.copy for a in agents.values())/max(1,len(agents))
    return {
        "entropy": round(entropy, 3),
        "compression_ratio": round(compression_ratio, 3),
        "copy_score_mean": round(copy_mean/20.0, 3),  # normalize-ish
        "wealth_total": int(total_wealth),
        "currency_total": int(total_currency),
    }

def run_sim(ticks: int = 10) -> Tuple[List[Dict], Dict[str, Agent], pd.DataFrame]:
    agents = load_agents()
    events: List[Dict] = []
    tick_snapshots: List[Dict] = []

    for t in range(1, ticks+1):
        # 1) Soup step (deterministic drip)
        soup_step_and_trait_drip(agents, events, t)

        # 2) Trades: each king invests TRADE_INVEST if possible
        for a in [x for x in agents.values() if x.role=="king"]:
            created = 0
            if a.currency >= TRADE_INVEST:
                created = apply_trade(a, TRADE_INVEST)
            if created:
                events.append({"tick": t, "type": "trade", "king": a.id, "invest": TRADE_INVEST, "wealth_created": created})

        # 3) Retainers
        pay_retainers(agents, events, t)

        # 4) Targeting: each mercenary attempts an action against the top-exposed king deterministically
        kings_list = [x for x in agents.values() if x.role=="king" and x.alive]
        if kings_list:
            for merc in [x for x in agents.values() if x.role=="mercenary" and x.alive]:
                king = pick_target_king(agents)
                if not king: break

                # Knights assigned (employer first)
                knights = available_knights_for_king(agents, king.id)
                assigned = knights[:1]  # one defender per attacker for now

                # Bribe check
                bribe = int(getattr(king, "bribe_threshold", 0) or 0)
                rv = raid_value(merc, king, assigned)
                if bribe > 0 and bribe >= rv:
                    # Successful bribe
                    if king.currency >= bribe:
                        king.currency -= bribe
                        merc.currency += bribe
                        wealth_leakage(king, BRIBE_LEAKAGE)
                        events.append({"tick": t, "type": "bribe_accept", "king": king.id, "merc": merc.id, "amount": bribe, "rv": round(rv,2)})
                    else:
                        events.append({"tick": t, "type": "bribe_insufficient_funds", "king": king.id, "merc": merc.id, "threshold": bribe})
                else:
                    # Contest (raid vs defend)
                    if assigned:
                        knight = assigned[0]
                        outcome, p_knight = resolve_defend(knight, merc)
                        st = stake_amount(knight, merc)
                        if outcome == "knight":
                            knight.currency += st
                            merc.currency = max(0, merc.currency - st)
                            bounty_to_knight(knight, merc, frac=0.07)
                            events.append({"tick": t, "type": "defend_win", "king": king.id, "knight": knight.id, "merc": merc.id, "stake": st, "p_knight": round(p_knight,3)})
                        else:
                            # Merc wins: apply mirrored losses to king
                            mirror_transfer_from_king_to_merc(king, merc)
                            # Knight loses stake and 1 defend (equipment wear) deterministically if enough defend
                            knight.currency = max(0, knight.currency - st)
                            if knight.defend > 0:
                                knight.defend -= 1
                            events.append({"tick": t, "type": "defend_loss", "king": king.id, "knight": knight.id, "merc": merc.id, "stake": st, "p_knight": round(p_knight,3)})
                    else:
                        # No knight; auto success for merc
                        mirror_transfer_from_king_to_merc(king, merc)
                        events.append({"tick": t, "type": "unopposed_raid", "king": king.id, "merc": merc.id})

        # 5) Snapshot
        metrics = snapshot_metrics(agents, t)
        snapshot_agents = []
        for a in agents.values():
            snapshot_agents.append({
                "id": a.id, "role": a.role, "currency": a.currency, "wealth": a.to_wealth_dict()
            })
        tick_snapshots.append({"tick": t, "metrics": metrics, "agents": snapshot_agents})

    # Write outputs
    with open(TICKS_JSON, "w", encoding="utf-8") as f:
        json.dump(tick_snapshots, f, indent=2)

    events_df = pd.DataFrame(events)
    if not events_df.empty:
        events_df.to_csv(EVENTS_CSV, index=False)
    # final agent table
    agents_df = pd.DataFrame([{
        "id": a.id, "role": a.role, "currency": a.currency, **a.to_wealth_dict(),
        "employer": a.employer, "retainer_fee": int(a.retainer_fee) if str(a.retainer_fee).isdigit() else 0,
        "bribe_policy_mode": a.bribe_policy_mode, "bribe_threshold": int(a.bribe_threshold) if str(a.bribe_threshold).isdigit() else 0
    } for a in agents.values()])
    agents_df.to_csv(FINAL_AGENTS_CSV, index=False)

    return tick_snapshots, agents, events_df

# Run a small deterministic simulation (10 ticks)
ticks, agents_final, events_df = run_sim(ticks=10)

# Show brief previews
import caas_jupyter_tools as cj
if not events_df.empty:
    cj.display_dataframe_to_user("Mercenaries Inc. - Events Log (first 100 rows)", events_df.head(100))
# Return minimal prints to stdout for context
print("Wrote:", TICKS_JSON, EVENTS_CSV if EVENTS_CSV.exists() else "(no events)", FINAL_AGENTS_CSV)

# Prepare a tiny summary for the user
summary = {
    "ticks_written": len(ticks),
    "first_tick_metrics": ticks[0]["metrics"],
    "last_tick_metrics": ticks[-1]["metrics"],
    "final_agents": {aid: {"currency": a.currency, "wealth_total": a.wealth_total()} for aid,a in agents_final.items()}
}
summary
```

* [m_inc_run_ticks.json](sandbox:/mnt/data/m_inc_run_ticks.json) — per-tick snapshots with metrics and all agent states
* [m_inc_events.csv](sandbox:/mnt/data/m_inc_events.csv) — event log (bribes, trades, defends, raids, retainers)
* [m_inc_agents_final.csv](sandbox:/mnt/data/m_inc_agents_final.csv) — final agent table after tick 10

Notes:

* No randomness except a fixed seed for tie-breaks; defend outcomes are deterministic via a score function.
* Kings auto-trade 100 currency/tick into +5 wealth (3 to `defend`, 2 to `trade`).
* Bribe success is a threshold vs computed `raid_value`; successful bribes apply a fixed 5% wealth leakage.
* When contested, we compute a deterministic win probability; outcome resolves by threshold, not sampling.

Want me to tweak weights (α,β,γ,δ), trade amounts, or enable multi-knight assignments per attack?
