Here’s a concise, agent-optimized migration plan to bring 0.1.1 fully up to date.

### Scope
- Target directory: `docs/0.1.1/`
- Edit targets: `architecture/interaction-logic.md`, `architecture/integration-plan.md`, `architecture/modules.md`, `architecture/incentives.md`
- Database targets: `database/agents.csv`, `database/events_log.csv`, `database/events.csv`, `database/run_ticks.json`, `database/ticks.json`, `database/nameTypes.yaml`
- Context sources (read-only while editing each target):
    - `docs/0.1.0/` legacy files (with `_LEGACY` pointers in MOCs)
    - `docs/0.1.1/api/` (schemas/specs)
    - `python/` analysis and interpreter scripts

### Working rule
- Edit exactly ONE target file at a time.
- While editing, consult MULTIPLE context files (0.1.1 siblings, 0.1.0 LEGACY, `python/`).
- Keep content terse and operational, link out for details.

## Phase 1 — Architecture Docs

1) Update `architecture/interaction-logic.md`
- Context: `architecture/incentives.md`, `architecture/integration-plan.md`, `database/*.json|*.csv`, `python/*`
- Tasks:
    - Align equations/weights/ordering with 0.1.1c values already enumerated (EXPOSURE, RAID_VALUE_WEIGHTS, defend tie-break, bribe leakage, mirrored losses).
    - Ensure tick ordering matches emitted event streams in `events*.csv` and fields in `run_ticks.json`.
    - Add a compact “Determinism and tie-breakers” checkpoint.
- Acceptance:
    - All formulas present, pinned constants match 0.1.1c.
    - Event names/fields align with database files.

2) Update `architecture/integration-plan.md`
- Context: `python/` scripts, `api/*`, `database/*`, `OVERVIEW.md`
- Tasks:
    - Reference concrete adapters and outputs that exist in 0.1.1 (CSV/JSON schemas, caching, refractory notes).
    - Replace generic future tense with present-tense deliverables wired to current files.
    - Add “Integration points” list binding to `python/save_bff_trace.py`, `analyse_soup.py`, `bff_interpreter.py`.
- Acceptance:
    - All bullet deliverables map to real files/paths.
    - Output schema links point to 0.1.1 API docs.

3) Update `architecture/modules.md`
- Context: `python/*`, `api/*`, `architecture/interaction-logic.md`
- Tasks:
    - Map module list to actual Python modules (e.g., VM, soup, analytics, detectors, snapshot, assay, CLI) and adapter layer; ensure “Quick start” matches runnable CLI.
    - Ensure “Why these modules” reflects 0.1.1 goals (determinism, adapters, logs).
    - Keep examples brief, link out to `python/` paths.
- Acceptance:
    - All listed modules exist or are clearly adapter contracts; commands run as documented.

4) Update `architecture/incentives.md`
- Context: `architecture/interaction-logic.md`, `database/*.csv|*.json`
- Tasks:
    - Freeze priority lists and cross-check with contest/bribe/trade rules in interaction logic.
    - Keep equations short; link to interaction-logic for math.
- Acceptance:
    - No contradictions with interaction logic; terms match event naming.

## Phase 2 — Database Updates

5) Normalize `database/agents.csv`
- Context: `architecture/*`, `ticks.json`, `run_ticks.json`
- Tasks:
    - Ensure columns match current model (roles, currency, seven traits, employer, retainer_fee, bribe_policy_mode, bribe_threshold).
    - Fix placeholders like `nan`/empty to canonical blanks or zeros (deterministic).
- Acceptance:
    - Clean CSV with consistent types; aligns with snapshot fields.

6) Validate `database/events_log.csv` and `database/events.csv`
- Context: `architecture/interaction-logic.md` event types, `api` schemas
- Tasks:
    - Ensure event types/fields: `trade`, `trait_drip`, `retainer`, `bribe_accept`, `bribe_insufficient_funds`, `defend_win`, `defend_loss`, `unopposed_raid`.
    - Fix numeric consistency (ints where expected), remove spurious `0.0` if integer.
- Acceptance:
    - Headers align with documented event schema; sample rows valid.

7) Validate `database/run_ticks.json` and `database/ticks.json`
- Context: `architecture/interaction-logic.md` tick ordering, metrics names
- Tasks:
    - Ensure `metrics` keys consistent across files (entropy, compression_ratio, copy_score_mean, wealth_total, currency_total; plus per-tick counts in `ticks.json`).
    - Confirm agent snapshots mirror `agents.csv` columns/trait names.
- Acceptance:
    - JSON validates; keys stable; values consistent across ticks.

8) Maintain `database/nameTypes.yaml`
- Context: repo naming practice; `docs/0.1.1` needs
- Tasks:
    - Adopt a compact schema with:
        - `nameType` definition (type, description, examples)
        - Branch naming conventions with variables and ticket IDs
        - Doc naming patterns for 0.1.1 (e.g., `m.inc-<topic>-0.1.1.md` if needed)
    - Keep to minimal lists and examples; remove verbose prose.
- Acceptance:
    - One-screen YAML, actionable examples, versioned comment header.

## Phase 3 — Consistency and Cross-Refs

9) Cross-link pass
- Ensure `docs/0.1.1/MOC.md` retains minimal links but now points to updated anchors/sections where applicable (no bloat).
- Verify `docs/MOC.md` and `docs/0.1.0/MOC.md` remain consistent (0.1.0 marked as LEGACY where appropriate).

10) Sanity validation
- Check that all file links resolve; relative paths correct.
- Spot-check equations/weights vs prose across files.

## Execution cadence (per NOTE)
- For each target (1 file at a time):
    - Open target for edit.
    - Open ≥3 context sources (one 0.1.1 doc, one 0.1.0 LEGACY, one `python/` or `api/`).
    - Make concise updates; keep sections short; link out for depth.
    - Validate against database files if the target mentions events/metrics.

## Acceptance criteria (overall)
- All 0.1.1 docs reflect the pinned 0.1.1c logic and current modules/adapters.
- Database files’ schemas/values match the documented events, metrics, and traits.
- `nameTypes.yaml` is compact, useful, and tailored to this repo.
- MOCs remain minimal and navigational with brief “Agent checkpoints”.

If you approve, I’ll execute Phase 1 step 1 (edit `architecture/interaction-logic.md`) using `incentives.md`, `integration-plan.md`, and `python/*` as context.
