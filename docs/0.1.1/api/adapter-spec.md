---
title: "M|inc Adapter Spec"
description: "Interfaces for incentive adapter, cache, signals, and policy DSL (0.1.1)"
version: "0.1.1"
last_updated: "2025-10-30"
dependencies:
  - "../architecture/m.inc-incentives.md"
  - "m.inc-json-schemas.md"
---

## Modules and Contracts

### python/m_inc/adapter.py
- Purpose: Orchestrate per-tick processing from soup traces to JSON/CSV outputs.
- Key functions:
    - `process_tick(raw_tick, config) -> (tick_json, event_rows)`
    - `aggregate_micro_events(events) -> TickSummary`
    - `emit_outputs(tick_json, event_rows, sink)`

### python/m_inc/cache.py
- Purpose: Canonicalize state and memoize deterministic outcomes.
- Key functions:
    - `compute_canonical_state(agent_set) -> CanonicalState`
    - `hash_state(canonical_state, params_hash) -> str`
    - `memoized_encounter(canonical_state, params) -> EncounterOutcome`

### python/m_inc/signals.py
- Purpose: Event channels with priority and refractory periods.
- Key types: `Signal`, `Channel`, `Priority`.
- Key functions:
    - `update_signals(events_in, refractory_cfg) -> list[Signal]`
    - `schedule(events, priorities) -> list[Signal]`

### python/m_inc/policy_dsl.py
## Function Signatures (Reference)

```python
class CanonicalState(TypedDict):
    agents: list[dict]
    roles: dict[str, str]
    params_hash: str

def compute_canonical_state(agent_set: dict) -> CanonicalState: ...
def hash_state(canonical_state: CanonicalState, params_hash: str) -> str: ...

class EncounterOutcome(TypedDict):
    events: list[dict]
    cache_key: str

def memoized_encounter(state: CanonicalState, params: dict) -> EncounterOutcome: ...

def bribe_outcome(king: dict, merc: dict, threshold: int) -> dict: ...
def raid_value(merc: dict, king: dict, knights: list[dict]) -> float: ...
def p_knight_win(knight: dict, merc: dict) -> float: ...
def trade_action(king: dict, amount: int) -> dict: ...

def update_signals(events_in: list[dict], refractory_cfg: dict) -> list[dict]: ...
def aggregate_micro_events(events: list[dict]) -> dict: ...
```

- Purpose: Compile YAML policy into pure callables.
- Key functions:
    - `compile_policies(yaml_cfg) -> Policies`
    - `policies.bribe_outcome(king, merc, threshold) -> BribeOutcome`
    - `policies.raid_value(merc, king, knights) -> float`
    - `policies.p_knight_win(knight, merc) -> float`
    - `policies.trade_action(king, amount) -> TradeOutcome`

## Processing Pipeline (Pure Functions)
1. Parse raw tick → `AgentSet`
2. Canonicalize → `CanonicalState`
3. Hash + lookup cache → outcome or compute
4. Compute incentives (bribe/raid/defend/trade) via `Policies`
5. Update `Signals` with priorities and refractory windows
6. Aggregate micro-events → `TickSummary`
7. Emit JSON/CSV per schemas

## Determinism
All policy functions are pure given inputs. Seeded randomness remains confined to the BFF layer.

### Caching Safeguards
- Cache key = `hash(canonical_state) + params_hash + adapter_version`.
- Periodic witness sampling: store input/output pairs for N% of cache writes.
- Config changes invalidate cache via `params_hash`.

### Refractory Safeguards
- Each channel has `refractory_ms` (or ticks) preventing immediate re-fire.
- Events within the window are queued and coalesced.
- Prevents oscillatory raid/defend loops.

## Configuration
- YAML: role ratios, thresholds, exposure, refractory, schedules.
- Config hash used in cache key and JSON `meta`.
