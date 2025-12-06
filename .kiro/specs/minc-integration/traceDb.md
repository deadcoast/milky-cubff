# TRACEABILITY DB

## COVERAGE ANALYSIS

Total requirements: 75
Coverage: 73.33

The following properties are missing tasks:
- Property 1: Non-negativity invariant
- Property 2: Deterministic execution
- Property 3: Role assignment distribution
- Property 4: Agent initialization
- Property 5: Registry lookup consistency
- Property 6: Role mutation rate
- Property 7: Currency-wealth conversion ratio
- Property 8: Bribe evaluation
- Property 9: Bribe success conditions
- Property 10: Bribe failure leads to contest
- Property 11: Knight win probability calculation
- Property 12: Deterministic contest resolution
- Property 13: Mercenary victory transfers
- Property 14: Trade currency requirement
- Property 15: Trade event recording
- Property 16: Retainer payment conditions
- Property 17: Retainer event recording
- Property 18: Canonical state determinism
- Property 19: Cache correctness
- Property 20: Cache invalidation on config change
- Property 21: Witness sample storage
- Property 22: Refractory period enforcement
- Property 23: Event coalescing
- Property 24: Copy trait drip rule
- Property 25: Trait emergence disable
- Property 26: Metrics completeness
- Property 27: Output schema compliance
- Property 28: Configuration hash consistency
- Property 29: Configuration validation

## TRACEABILITY

### Property 1: Non-negativity invariant

For any agent at any point in time, currency and all wealth traits
    must be non-negative.

    **Feature: minc-integration, Property 1: Non-negativity invariant**

**Validates**
- Criteria 3.1: THE System SHALL maintain per-agent currency balances as non-negative integers
- Criteria 3.2: THE System SHALL maintain per-agent wealth traits as seven non-negative integers
- Criteria 3.5: THE System SHALL prevent currency or wealth from becoming negative through clamping operations
- Criteria 3.1: THE System SHALL maintain per-agent currency balances as non-negative integers
- Criteria 3.2: THE System SHALL maintain per-agent wealth traits as seven non-negative integers
- Criteria 3.5: THE System SHALL prevent currency or wealth from becoming negative through clamping operations

**Implementation tasks**

**Implemented PBTs**
- [Non-negativity invariant**](./../../../python/m_inc/test_property_based.py#L76)
- [Non-negativity invariant**](./../../../python/m_inc/test_property_based.py#L90)
- [Non-negativity invariant**](./../../../python/m_inc/test_property_based.py#L122)
- [Non-negativity invariant**](./../../../python/m_inc/test_property_based.py#L167)

### Property 2: Deterministic execution

*For any* initial state and random seed, executing the same sequence of ticks must produce identical event sequences, agent states, and metrics.

**Validates**
- Criteria 3.4: THE System SHALL apply deterministic wealth and currency updates based on economic events
- Criteria 8.2: THE System SHALL resolve ties deterministically using lexicographic ID comparison
- Criteria 8.3: THE System SHALL apply sigmoid and clamp functions with fixed parameters
- Criteria 8.4: THE System SHALL NOT introduce randomness in economic event resolution (randomness remains in BFF pairing only)
- Criteria 8.5: WHEN given the same initial state and seed, THE System SHALL produce identical event sequences and final states

**Implementation tasks**

**Implemented PBTs**
- [Currency conservation**](./../../../python/m_inc/test_property_based.py#L185)
- [Currency conservation**](./../../../python/m_inc/test_property_based.py#L199)

### Property 3: Role assignment distribution

*For any* set of tape IDs and configured role ratios, the assigned roles must match the configured distribution within rounding error (±1 agent per role).

**Validates**
- Criteria 2.2: THE System SHALL support configurable role ratios (e.g., 10% Kings, 20% Knights, 70% Mercenaries)

**Implementation tasks**

**Implemented PBTs**
- [Deterministic resolution**](./../../../python/m_inc/test_property_based.py#L224)
- [Deterministic resolution**](./../../../python/m_inc/test_property_based.py#L238)
- [Deterministic resolution**](./../../../python/m_inc/test_property_based.py#L266)
- [Deterministic resolution**](./../../../python/m_inc/test_property_based.py#L297)

### Property 4: Agent initialization

*For any* agent created with a specific role, the initial currency and wealth traits must fall within the configured ranges for that role, and all seven wealth traits must be initialized.

**Validates**
- Criteria 2.3: THE System SHALL initialize agents with role-specific starting currency and wealth traits
- Criteria 2.4: WHEN an agent is created, THE System SHALL assign seven wealth traits (compute, copy, defend, raid, trade, sense, adapt) with initial values

**Implementation tasks**

**Implemented PBTs**
- [Probability bounds**](./../../../python/m_inc/test_property_based.py#L312)
- [Probability bounds**](./../../../python/m_inc/test_property_based.py#L326)

### Property 5: Registry lookup consistency

*For any* tape ID assigned to an agent, retrieving the agent by tape ID must return the same agent as retrieving by agent ID.

**Validates**
- Criteria 2.1: THE System SHALL maintain an agent registry mapping tape IDs to roles and economic attributes

**Implementation tasks**

**Implemented PBTs**
- [Sigmoid properties**](./../../../python/m_inc/test_property_based.py#L339)
- [Sigmoid properties**](./../../../python/m_inc/test_property_based.py#L349)
- [Sigmoid properties**](./../../../python/m_inc/test_property_based.py#L362)

### Property 6: Role mutation rate

*For any* configured mutation rate and population of agents, over a sufficient number of ticks, the observed mutation frequency should approximate the configured rate within statistical bounds.

**Validates**
- Criteria 2.5: THE System SHALL support optional role mutation at a configurable low rate (default 0%)

**Implementation tasks**

**Implemented PBTs**
- [Clamp properties**](./../../../python/m_inc/test_property_based.py#L374)
- [Clamp properties**](./../../../python/m_inc/test_property_based.py#L388)
- [Clamp properties**](./../../../python/m_inc/test_property_based.py#L408)

### Property 7: Currency-wealth conversion ratio

*For any* trade operation that converts currency to wealth, the ratio must be exactly 100 currency = 5 wealth units.

**Validates**
- Criteria 3.3: THE System SHALL enforce the conversion ratio of 100 currency = 5 wealth units

**Implementation tasks**

**Implemented PBTs**
- [Cache correctness**](./../../../python/m_inc/test_property_based.py#L421)
- [Cache correctness**](./../../../python/m_inc/test_property_based.py#L435)
- [Cache correctness**](./../../../python/m_inc/test_property_based.py#L472)

### Property 8: Bribe evaluation

*For any* mercenary targeting a king, the system must evaluate the king's bribe threshold against the computed raid value using the exact formula: raid_value = 1.0×merc.raid + 0.25×(merc.sense+merc.adapt) - 0.60×king_defend_projection + 0.40×king_wealth_exposed.

**Validates**
- Criteria 4.1: WHEN a Mercenary targets a King, THE System SHALL evaluate the King's bribe threshold against the computed raid value
- Criteria 4.5: THE System SHALL compute raid value using the formula: raid_value = 1.0×merc.raid + 0.25×(merc.sense+merc.adapt) - 0.60×king_defend_projection + 0.40×king_wealth_exposed

**Implementation tasks**

**Implemented PBTs**
- [Wealth total consistency**](./../../../python/m_inc/test_property_based.py#L490)
- [Wealth total consistency**](./../../../python/m_inc/test_property_based.py#L500)

### Property 9: Bribe success conditions

*For any* king and mercenary interaction, IF bribe_threshold >= raid_value AND king.currency >= bribe_threshold, THEN the bribe must succeed with exact currency transfer and 5% wealth leakage applied to the king.

**Validates**
- Criteria 4.2: IF the bribe threshold is greater than or equal to the raid value AND the King has sufficient currency, THEN THE System SHALL execute a successful bribe
- Criteria 4.3: WHEN a bribe succeeds, THE System SHALL transfer currency from King to Mercenary and apply 5% wealth leakage to the King

**Implementation tasks**

**Implemented PBTs**
- [Raid value non-negative**](./../../../python/m_inc/test_property_based.py#L513)
- [Raid value non-negative**](./../../../python/m_inc/test_property_based.py#L527)

### Property 10: Bribe failure leads to contest

*For any* king and mercenary interaction, IF bribe_threshold < raid_value OR king.currency < bribe_threshold, THEN a raid/defend contest must be initiated.

**Validates**
- Criteria 4.4: IF the bribe threshold is insufficient OR the King lacks currency, THEN THE System SHALL proceed to raid/defend contest
- Criteria 5.1: WHEN a bribe fails or is rejected, THE System SHALL initiate a raid/defend contest

**Implementation tasks**

**Implemented PBTs**
- [Defend stake calculation**](./../../../python/m_inc/test_property_based.py#L539)
- [Defend stake calculation**](./../../../python/m_inc/test_property_based.py#L553)

### Property 11: Knight win probability calculation

*For any* knight and mercenary in a defend contest, the win probability must be computed using the exact formula: p_knight_win = clamp(0.05, 0.95, 0.5 + sigmoid(0.3×trait_delta) - 0.5).

**Validates**
- Criteria 5.2: THE System SHALL compute knight win probability using: p_knight_win = clamp(0.05, 0.95, 0.5 + sigmoid(0.3×trait_delta) - 0.5)

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 12: Deterministic contest resolution

*For any* knight and mercenary in a defend contest, IF p_knight_win > 0.5 OR (p_knight_win == 0.5 AND knight.id < merc.id), THEN the contest must resolve as a knight victory with exact stake and bounty transfers.

**Validates**
- Criteria 5.3: IF p_knight_win > 0.5 OR (p_knight_win == 0.5 AND knight.id < merc.id), THEN THE System SHALL resolve as knight victory
- Criteria 5.4: WHEN a knight wins, THE System SHALL transfer stake (10% of combined currency) from Mercenary to Knight and apply 7% bounty from Mercenary's raid/adapt traits

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 13: Mercenary victory transfers

*For any* mercenary victory in a defend contest, mirrored losses (50% currency, 25% wealth) must be transferred from king to mercenary, and stake must be deducted from knight.

**Validates**
- Criteria 5.5: WHEN a mercenary wins, THE System SHALL apply mirrored losses (50% currency, 25% wealth) from King to Mercenary and deduct stake from Knight

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 14: Trade currency requirement

*For any* king agent, a trade operation is possible IF AND ONLY IF the king's currency >= 100. When a trade occurs, exactly 100 currency is deducted and exactly 5 wealth units are added (3 to defend, 2 to trade).

**Validates**
- Criteria 6.1: WHEN a tick begins, THE System SHALL allow each King to invest 100 currency in trade if sufficient funds are available
- Criteria 6.2: WHEN a King trades, THE System SHALL deduct 100 currency and add 5 wealth units distributed as: 3 to defend, 2 to trade
- Criteria 6.5: THE System SHALL NOT allow trades if the King's currency balance is below 100

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 15: Trade event recording

*For any* trade operation, an event must be recorded containing: tick number, king ID, investment amount (100), and wealth created (5 units with distribution).

**Validates**
- Criteria 6.4: THE System SHALL record trade events with timestamp, King ID, investment amount, and wealth created

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 16: Retainer payment conditions

*For any* knight with an employer king, IF the king has sufficient currency, THEN the retainer fee must be transferred from king to knight. IF the king lacks sufficient currency, THEN no payment occurs and no error is raised.

**Validates**
- Criteria 7.1: WHEN a Knight has an employer King, THE System SHALL attempt to pay the retainer fee each tick
- Criteria 7.2: IF the employer King has sufficient currency, THEN THE System SHALL transfer the retainer amount from King to Knight
- Criteria 7.5: IF the employer King lacks sufficient currency, THEN THE System SHALL skip the retainer payment without error

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 17: Retainer event recording

*For any* retainer payment (successful or skipped), an event must be recorded containing: tick number, employer ID, knight ID, and amount (or 0 if skipped).

**Validates**
- Criteria 7.4: THE System SHALL record retainer events with timestamp, employer ID, Knight ID, and amount

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 18: Canonical state determinism

*For any* set of agents with unique IDs, the canonical state hash must be invariant under agent ordering (i.e., shuffling the agent list produces the same hash).

**Validates**
- Criteria 12.1: THE System SHALL compute canonical state representations for agent sets
- Criteria 12.2: THE System SHALL hash canonical states combined with config hash for cache keys

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 19: Cache correctness

*For any* canonical state and config hash, IF a cached outcome exists, THEN using the cached result must produce identical outcomes to recomputing from scratch.

**Validates**
- Criteria 12.3: WHEN a cached outcome exists for a state, THE System SHALL reuse it instead of recomputing

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 20: Cache invalidation on config change

*For any* configuration change, all cached results must be invalidated and subsequent computations must use the new configuration.

**Validates**
- Criteria 11.3: WHEN configuration changes, THE System SHALL invalidate cached results
- Criteria 12.5: THE System SHALL invalidate cache entries when configuration or adapter version changes

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 21: Witness sample storage

*For any* cache write operation, witness samples (input/output pairs) must be stored at the configured sample rate for validation purposes.

**Validates**
- Criteria 12.4: THE System SHALL store witness samples (input/output pairs) for cache validation

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 22: Refractory period enforcement

*For any* event that fires on a channel, that channel must be blocked for exactly the configured refractory period (in ticks), and any events on that channel during the refractory period must be queued.

**Validates**
- Criteria 13.1: THE System SHALL maintain refractory windows for event channels (raid, defend, bribe, trade)
- Criteria 13.2: WHEN an event fires, THE System SHALL block the same channel for the configured refractory period
- Criteria 13.3: THE System SHALL queue events that occur during refractory periods

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 23: Event coalescing

*For any* queued events on a channel, when the refractory period expires, the events must be coalesced according to priority rules before being processed.

**Validates**
- Criteria 13.4: THE System SHALL coalesce queued events when the refractory period expires

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 24: Copy trait drip rule

*For any* agent with copy trait >= 12, on every even tick (tick % 2 == 0), the copy trait must be incremented by exactly 1, and a trait_drip event must be recorded.

**Validates**
- Criteria 14.1: WHEN an agent's copy trait reaches 12 or higher, THE System SHALL increment copy by 1 every 2 ticks
- Criteria 14.4: THE System SHALL record trait_drip events in the event log

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 25: Trait emergence disable

*For any* configuration with trait_emergence.enabled = false, no trait drip operations must occur regardless of agent trait values.

**Validates**
- Criteria 14.5: THE System SHALL support disabling trait emergence via configuration flag

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 26: Metrics completeness

*For any* tick, the computed metrics must include all required fields: entropy, compression_ratio, copy_score_mean, wealth_total, currency_total, bribes_paid, bribes_accepted, raids_attempted, raids_won_by_merc, raids_won_by_knight, and wealth distribution statistics per role.

**Validates**
- Criteria 9.1: THE System SHALL compute per-tick metrics including: entropy, compression_ratio, copy_score_mean, wealth_total, currency_total
- Criteria 9.2: THE System SHALL track event counts: bribes_paid, bribes_accepted, raids_attempted, raids_won_by_merc, raids_won_by_knight
- Criteria 9.3: THE System SHALL calculate wealth distribution statistics (mean, median, Gini coefficient) per role

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 27: Output schema compliance

*For any* output (JSON tick snapshot, CSV event log, or final agent CSV), the data must validate against the documented schema and include all required fields and metadata (version, seed, config_hash, timestamp).

**Validates**
- Criteria 10.1: THE System SHALL output per-tick JSON snapshots containing: tick number, metrics object, and agents array with full state
- Criteria 10.2: THE System SHALL output CSV event logs with columns: tick, type, king, knight, merc, amount, stake, p_knight, notes
- Criteria 10.3: THE System SHALL output final agent CSV with columns: id, role, currency, compute, copy, defend, raid, trade, sense, adapt, wealth_total
- Criteria 10.4: THE System SHALL include metadata in JSON outputs: version, seed, config_hash, timestamp
- Criteria 10.5: THE System SHALL validate all outputs against documented schemas before writing

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 28: Configuration hash consistency

*For any* configuration, the computed config hash must be deterministic (same config always produces same hash) and must be included in all output metadata.

**Validates**
- Criteria 11.2: THE System SHALL compute a config hash and include it in all output metadata

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

### Property 29: Configuration validation

*For any* invalid configuration (e.g., role ratios not summing to 1.0, negative values, out-of-range parameters), the system must reject the configuration and report specific validation errors.

**Validates**
- Criteria 11.5: THE System SHALL validate configuration on load and report errors for invalid values

**Implementation tasks**

**Implemented PBTs**
- No implemented PBTs found

## DATA

### ACCEPTANCE CRITERIA (75 total)
- 1.1: THE System SHALL preserve all existing BFF simulation functionality without modification to core C++ files (main.cc, common.h, common.cc, *.cu) (not covered)
- 1.2: THE System SHALL implement M|inc as a separate Python module under python/m_inc/ directory (not covered)
- 1.3: THE System SHALL consume BFF soup traces as read-only inputs (not covered)
- 1.4: THE System SHALL NOT require changes to existing Python analysis tools (bff_interpreter.py, analyse_soup.py) (not covered)
- 1.5: THE System SHALL provide optional CLI flags to enable/disable M|inc processing (not covered)
- 2.1: THE System SHALL maintain an agent registry mapping tape IDs to roles and economic attributes (covered)
- 2.2: THE System SHALL support configurable role ratios (e.g., 10% Kings, 20% Knights, 70% Mercenaries) (covered)
- 2.3: THE System SHALL initialize agents with role-specific starting currency and wealth traits (covered)
- 2.4: WHEN an agent is created, THE System SHALL assign seven wealth traits (compute, copy, defend, raid, trade, sense, adapt) with initial values (covered)
- 2.5: THE System SHALL support optional role mutation at a configurable low rate (default 0%) (covered)
- 3.1: THE System SHALL maintain per-agent currency balances as non-negative integers (covered)
- 3.2: THE System SHALL maintain per-agent wealth traits as seven non-negative integers (covered)
- 3.3: THE System SHALL enforce the conversion ratio of 100 currency = 5 wealth units (covered)
- 3.4: THE System SHALL apply deterministic wealth and currency updates based on economic events (covered)
- 3.5: THE System SHALL prevent currency or wealth from becoming negative through clamping operations (covered)
- 4.1: WHEN a Mercenary targets a King, THE System SHALL evaluate the King's bribe threshold against the computed raid value (covered)
- 4.2: IF the bribe threshold is greater than or equal to the raid value AND the King has sufficient currency, THEN THE System SHALL execute a successful bribe (covered)
- 4.3: WHEN a bribe succeeds, THE System SHALL transfer currency from King to Mercenary and apply 5% wealth leakage to the King (covered)
- 4.4: IF the bribe threshold is insufficient OR the King lacks currency, THEN THE System SHALL proceed to raid/defend contest (covered)
- 4.5: THE System SHALL compute raid value using the formula: raid_value = 1.0×merc.raid + 0.25×(merc.sense+merc.adapt) - 0.60×king_defend_projection + 0.40×king_wealth_exposed (covered)
- 5.1: WHEN a bribe fails or is rejected, THE System SHALL initiate a raid/defend contest (covered)
- 5.2: THE System SHALL compute knight win probability using: p_knight_win = clamp(0.05, 0.95, 0.5 + sigmoid(0.3×trait_delta) - 0.5) (covered)
- 5.3: IF p_knight_win > 0.5 OR (p_knight_win == 0.5 AND knight.id < merc.id), THEN THE System SHALL resolve as knight victory (covered)
- 5.4: WHEN a knight wins, THE System SHALL transfer stake (10% of combined currency) from Mercenary to Knight and apply 7% bounty from Mercenary's raid/adapt traits (covered)
- 5.5: WHEN a mercenary wins, THE System SHALL apply mirrored losses (50% currency, 25% wealth) from King to Mercenary and deduct stake from Knight (covered)
- 6.1: WHEN a tick begins, THE System SHALL allow each King to invest 100 currency in trade if sufficient funds are available (covered)
- 6.2: WHEN a King trades, THE System SHALL deduct 100 currency and add 5 wealth units distributed as: 3 to defend, 2 to trade (covered)
- 6.3: THE System SHALL execute trade operations before raid/defend interactions in each tick (not covered)
- 6.4: THE System SHALL record trade events with timestamp, King ID, investment amount, and wealth created (covered)
- 6.5: THE System SHALL NOT allow trades if the King's currency balance is below 100 (covered)
- 7.1: WHEN a Knight has an employer King, THE System SHALL attempt to pay the retainer fee each tick (covered)
- 7.2: IF the employer King has sufficient currency, THEN THE System SHALL transfer the retainer amount from King to Knight (covered)
- 7.3: THE System SHALL execute retainer payments after trades but before raid/defend interactions (not covered)
- 7.4: THE System SHALL record retainer events with timestamp, employer ID, Knight ID, and amount (covered)
- 7.5: IF the employer King lacks sufficient currency, THEN THE System SHALL skip the retainer payment without error (covered)
- 8.1: THE System SHALL use pure functions for all economic calculations (bribe, raid_value, p_knight_win, trade) (not covered)
- 8.2: THE System SHALL resolve ties deterministically using lexicographic ID comparison (covered)
- 8.3: THE System SHALL apply sigmoid and clamp functions with fixed parameters (covered)
- 8.4: THE System SHALL NOT introduce randomness in economic event resolution (randomness remains in BFF pairing only) (covered)
- 8.5: WHEN given the same initial state and seed, THE System SHALL produce identical event sequences and final states (covered)
- 9.1: THE System SHALL compute per-tick metrics including: entropy, compression_ratio, copy_score_mean, wealth_total, currency_total (covered)
- 9.2: THE System SHALL track event counts: bribes_paid, bribes_accepted, raids_attempted, raids_won_by_merc, raids_won_by_knight (covered)
- 9.3: THE System SHALL calculate wealth distribution statistics (mean, median, Gini coefficient) per role (covered)
- 9.4: THE System SHALL provide opcode histogram tracking for BFF instruction usage (not covered)
- 9.5: THE System SHALL output metrics in JSON format with tick number, timestamp, and all computed values (not covered)
- 10.1: THE System SHALL output per-tick JSON snapshots containing: tick number, metrics object, and agents array with full state (covered)
- 10.2: THE System SHALL output CSV event logs with columns: tick, type, king, knight, merc, amount, stake, p_knight, notes (covered)
- 10.3: THE System SHALL output final agent CSV with columns: id, role, currency, compute, copy, defend, raid, trade, sense, adapt, wealth_total (covered)
- 10.4: THE System SHALL include metadata in JSON outputs: version, seed, config_hash, timestamp (covered)
- 10.5: THE System SHALL validate all outputs against documented schemas before writing (covered)
- 11.1: THE System SHALL load configuration from YAML files specifying: role ratios, thresholds, exposure factors, refractory periods (not covered)
- 11.2: THE System SHALL compute a config hash and include it in all output metadata (covered)
- 11.3: WHEN configuration changes, THE System SHALL invalidate cached results (covered)
- 11.4: THE System SHALL provide default configuration values for all parameters (not covered)
- 11.5: THE System SHALL validate configuration on load and report errors for invalid values (covered)
- 12.1: THE System SHALL compute canonical state representations for agent sets (covered)
- 12.2: THE System SHALL hash canonical states combined with config hash for cache keys (covered)
- 12.3: WHEN a cached outcome exists for a state, THE System SHALL reuse it instead of recomputing (covered)
- 12.4: THE System SHALL store witness samples (input/output pairs) for cache validation (covered)
- 12.5: THE System SHALL invalidate cache entries when configuration or adapter version changes (covered)
- 13.1: THE System SHALL maintain refractory windows for event channels (raid, defend, bribe, trade) (covered)
- 13.2: WHEN an event fires, THE System SHALL block the same channel for the configured refractory period (covered)
- 13.3: THE System SHALL queue events that occur during refractory periods (covered)
- 13.4: THE System SHALL coalesce queued events when the refractory period expires (covered)
- 13.5: THE System SHALL configure refractory periods in ticks or milliseconds via YAML (not covered)
- 14.1: WHEN an agent's copy trait reaches 12 or higher, THE System SHALL increment copy by 1 every 2 ticks (covered)
- 14.2: THE System SHALL define configurable thresholds for other trait emergence rules (not covered)
- 14.3: THE System SHALL apply trait drip operations at the start of each tick before other interactions (not covered)
- 14.4: THE System SHALL record trait_drip events in the event log (covered)
- 14.5: THE System SHALL support disabling trait emergence via configuration flag (covered)
- 15.1: THE System SHALL consume output from save_bff_trace.py without modification (not covered)
- 15.2: THE System SHALL provide a CLI wrapper that pipes BFF soup data to M|inc adapter (not covered)
- 15.3: THE System SHALL support running M|inc analysis on historical BFF trace files (not covered)
- 15.4: THE System SHALL NOT break existing Python tool imports or CLI commands (not covered)
- 15.5: THE System SHALL document integration points with existing tools in README (not covered)

### IMPORTANT ACCEPTANCE CRITERIA (0 total)

### CORRECTNESS PROPERTIES (29 total)
- Property 1: Non-negativity invariant
- Property 2: Deterministic execution
- Property 3: Role assignment distribution
- Property 4: Agent initialization
- Property 5: Registry lookup consistency
- Property 6: Role mutation rate
- Property 7: Currency-wealth conversion ratio
- Property 8: Bribe evaluation
- Property 9: Bribe success conditions
- Property 10: Bribe failure leads to contest
- Property 11: Knight win probability calculation
- Property 12: Deterministic contest resolution
- Property 13: Mercenary victory transfers
- Property 14: Trade currency requirement
- Property 15: Trade event recording
- Property 16: Retainer payment conditions
- Property 17: Retainer event recording
- Property 18: Canonical state determinism
- Property 19: Cache correctness
- Property 20: Cache invalidation on config change
- Property 21: Witness sample storage
- Property 22: Refractory period enforcement
- Property 23: Event coalescing
- Property 24: Copy trait drip rule
- Property 25: Trait emergence disable
- Property 26: Metrics completeness
- Property 27: Output schema compliance
- Property 28: Configuration hash consistency
- Property 29: Configuration validation

### IMPLEMENTATION TASKS (74 total)
1. Set up M|inc project structure and core infrastructure
2. Implement core data models and type definitions
2.1 Create `core/models.py` with Agent, WealthTraits, Role, Event, EventType dataclasses
2.2 Create `core/schemas.py` with Pydantic schemas for validation
2.3 Create `core/config.py` for configuration management
3. Implement Trace Reader component
3.1 Create `adapters/trace_reader.py` with TraceReader class
3.2 Add trace format detection and normalization
4. Implement Agent Registry component
4.1 Create `core/agent_registry.py` with AgentRegistry class
4.2 Add agent initialization logic
4.3 Add role mutation support (optional)
5. Implement Economic Engine core
5.1 Create `core/economic_engine.py` with EconomicEngine class
5.2 Implement soup drip logic
5.3 Implement trade operations
5.4 Implement retainer payments
5.5 Implement interaction orchestration
6. Implement economic calculation functions
6.1 Create `core/economics.py` with pure calculation functions
6.2 Implement bribe resolution logic
6.3 Implement defend resolution logic
6.4 Implement wealth and currency transfer functions
7. Implement Policy DSL Compiler
7.1 Create `policies/policy_dsl.py` with PolicyCompiler class
7.2 Add policy function generators
7.3 Add policy validation and testing
8. Implement Cache Layer
8.1 Create `core/cache.py` with CacheLayer class
8.2 Implement canonical state computation
8.3 Add witness sampling for cache validation
9. Implement Signal Processor
9.1 Create `core/signals.py` with SignalProcessor class
9.2 Add event queuing and coalescing
10. Implement Event Aggregator
10.1 Create `core/event_aggregator.py` with EventAggregator class
10.2 Add metrics computation
11. Implement Output Writer
11.1 Create `adapters/output_writer.py` with OutputWriter class
11.2 Add JSON serialization
11.3 Add CSV serialization
12. Implement CLI interface
12.1 Create `cli.py` with main entry point
12.2 Add streaming mode support
12.3 Add batch processing mode
13. Create configuration files and examples
13.1 Create `config/minc_default.yaml` with default parameters
13.2 Create `config/minc_fast.yaml` for quick experiments
13.3 Create example trace files in `testdata/`
14. Implement integration with existing BFF tools
14.1 Create `adapters/bff_bridge.py` for BFF integration
14.2 Create wrapper script `run_minc_on_bff.py`
14.3 Update existing tool documentation
15. Write comprehensive tests
15.1 Create unit tests for economic functions
15.2 Create unit tests for data models
15.3 Create integration tests for components
15.4 Create end-to-end tests
15.5 Create property-based tests
16. Create documentation and examples
16.1 Write `python/m_inc/README.md`
16.2 Create usage examples
16.3 Create API reference documentation
16.4 Create visualization examples
17. Perform integration validation
17.1 Run M|inc on existing BFF traces
17.2 Validate determinism
17.3 Validate performance
17.4 Validate against 0.1.1 spec outputs
18. Add Correctness Properties section to design document
18.1 Review requirements document for all acceptance criteria
18.2 Perform property reflection to eliminate redundancy
18.3 Write Correctness Properties section in design.md
18.4 Verify property coverage

### IMPLEMENTED PBTS (27 total)
**Property 1:**
- [Non-negativity invariant**](./../../../python/m_inc/test_property_based.py#L76)
- [Non-negativity invariant**](./../../../python/m_inc/test_property_based.py#L90)
- [Non-negativity invariant**](./../../../python/m_inc/test_property_based.py#L122)
- [Non-negativity invariant**](./../../../python/m_inc/test_property_based.py#L167)
**Property 2:**
- [Currency conservation**](./../../../python/m_inc/test_property_based.py#L185)
- [Currency conservation**](./../../../python/m_inc/test_property_based.py#L199)
**Property 3:**
- [Deterministic resolution**](./../../../python/m_inc/test_property_based.py#L224)
- [Deterministic resolution**](./../../../python/m_inc/test_property_based.py#L238)
- [Deterministic resolution**](./../../../python/m_inc/test_property_based.py#L266)
- [Deterministic resolution**](./../../../python/m_inc/test_property_based.py#L297)
**Property 4:**
- [Probability bounds**](./../../../python/m_inc/test_property_based.py#L312)
- [Probability bounds**](./../../../python/m_inc/test_property_based.py#L326)
**Property 5:**
- [Sigmoid properties**](./../../../python/m_inc/test_property_based.py#L339)
- [Sigmoid properties**](./../../../python/m_inc/test_property_based.py#L349)
- [Sigmoid properties**](./../../../python/m_inc/test_property_based.py#L362)
**Property 6:**
- [Clamp properties**](./../../../python/m_inc/test_property_based.py#L374)
- [Clamp properties**](./../../../python/m_inc/test_property_based.py#L388)
- [Clamp properties**](./../../../python/m_inc/test_property_based.py#L408)
**Property 7:**
- [Cache correctness**](./../../../python/m_inc/test_property_based.py#L421)
- [Cache correctness**](./../../../python/m_inc/test_property_based.py#L435)
- [Cache correctness**](./../../../python/m_inc/test_property_based.py#L472)
**Property 8:**
- [Wealth total consistency**](./../../../python/m_inc/test_property_based.py#L490)
- [Wealth total consistency**](./../../../python/m_inc/test_property_based.py#L500)
**Property 9:**
- [Raid value non-negative**](./../../../python/m_inc/test_property_based.py#L513)
- [Raid value non-negative**](./../../../python/m_inc/test_property_based.py#L527)
**Property 10:**
- [Defend stake calculation**](./../../../python/m_inc/test_property_based.py#L539)
- [Defend stake calculation**](./../../../python/m_inc/test_property_based.py#L553)