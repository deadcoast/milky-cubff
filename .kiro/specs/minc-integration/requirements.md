# Requirements Document

## Introduction

This specification defines the integration of the Mercenaries Incorporated (M|inc) economic incentive system into the CuBFF (CUDA Brainfuck Forth) framework. M|inc extends the BFF self-replicating soup experiment by layering economic behaviors (currency, wealth, bribes, raids, defends, trades) on top of the existing tape-based evolutionary system. The integration must be non-invasive, preserving the existing BFF simulation while adding economic tracking and analysis capabilities.

## Glossary

- **BFF**: Brainfuck Forth - A minimal programming language with 10 instructions operating on a unified 128-byte tape
- **Soup**: A population of BFF programs that interact through random pairwise execution
- **M|inc**: Mercenaries Incorporated - The economic incentive layer built on top of BFF
- **Agent**: An entity in the M|inc system with a role (King, Knight, or Mercenary) and economic attributes
- **Tape**: A 64-byte BFF program; two tapes are concatenated into 128 bytes for execution
- **Adapter**: A Python module that bridges BFF soup execution with M|inc economic processing
- **Wealth**: Seven integer traits (compute, copy, defend, raid, trade, sense, adapt) representing agent capabilities
- **Currency**: Fungible resource used for bribes, retainers, and trades
- **Tick**: One complete cycle of economic interactions in the M|inc system
- **Epoch**: One complete cycle of BFF soup pairwise interactions
- **Canonical State**: A normalized representation of agent states for caching and memoization
- **Refractory Period**: A cooldown window preventing immediate re-triggering of events

## Requirements

### Requirement 1: Non-Invasive Integration

**User Story:** As a CuBFF developer, I want to add M|inc economic tracking without modifying the existing BFF simulation code, so that the core framework remains stable and maintainable.

#### Acceptance Criteria

1. THE System SHALL preserve all existing BFF simulation functionality without modification to core C++ files (main.cc, common.h, common.cc, *.cu)
2. THE System SHALL implement M|inc as a separate Python module under python/m_inc/ directory
3. THE System SHALL consume BFF soup traces as read-only inputs
4. THE System SHALL NOT require changes to existing Python analysis tools (bff_interpreter.py, analyse_soup.py)
5. THE System SHALL provide optional CLI flags to enable/disable M|inc processing

### Requirement 2: Agent Role Management

**User Story:** As a simulation operator, I want to assign roles (King, Knight, Mercenary) to BFF programs, so that economic behaviors can be tracked per agent.

#### Acceptance Criteria

1. THE System SHALL maintain an agent registry mapping tape IDs to roles and economic attributes
2. THE System SHALL support configurable role ratios (e.g., 10% Kings, 20% Knights, 70% Mercenaries)
3. THE System SHALL initialize agents with role-specific starting currency and wealth traits
4. WHEN an agent is created, THE System SHALL assign seven wealth traits (compute, copy, defend, raid, trade, sense, adapt) with initial values
5. THE System SHALL support optional role mutation at a configurable low rate (default 0%)

### Requirement 3: Currency and Wealth Tracking

**User Story:** As an economics researcher, I want to track currency and wealth for each agent across ticks, so that I can analyze economic dynamics and emergent behaviors.

#### Acceptance Criteria

1. THE System SHALL maintain per-agent currency balances as non-negative integers
2. THE System SHALL maintain per-agent wealth traits as seven non-negative integers
3. THE System SHALL enforce the conversion ratio of 100 currency = 5 wealth units
4. THE System SHALL apply deterministic wealth and currency updates based on economic events
5. THE System SHALL prevent currency or wealth from becoming negative through clamping operations

### Requirement 4: Bribe Mechanism

**User Story:** As a King agent, I want to offer bribes to Mercenaries to avoid raids, so that I can protect my wealth through economic negotiation.

#### Acceptance Criteria

1. WHEN a Mercenary targets a King, THE System SHALL evaluate the King's bribe threshold against the computed raid value
2. IF the bribe threshold is greater than or equal to the raid value AND the King has sufficient currency, THEN THE System SHALL execute a successful bribe
3. WHEN a bribe succeeds, THE System SHALL transfer currency from King to Mercenary and apply 5% wealth leakage to the King
4. IF the bribe threshold is insufficient OR the King lacks currency, THEN THE System SHALL proceed to raid/defend contest
5. THE System SHALL compute raid value using the formula: raid_value = 1.0×merc.raid + 0.25×(merc.sense+merc.adapt) - 0.60×king_defend_projection + 0.40×king_wealth_exposed

### Requirement 5: Raid and Defend Contests

**User Story:** As a Knight agent, I want to defend my employer King against Mercenary raids, so that I can earn stakes and bounties while protecting the King's assets.

#### Acceptance Criteria

1. WHEN a bribe fails or is rejected, THE System SHALL initiate a raid/defend contest
2. THE System SHALL compute knight win probability using: p_knight_win = clamp(0.05, 0.95, 0.5 + sigmoid(0.3×trait_delta) - 0.5)
3. IF p_knight_win > 0.5 OR (p_knight_win == 0.5 AND knight.id < merc.id), THEN THE System SHALL resolve as knight victory
4. WHEN a knight wins, THE System SHALL transfer stake (10% of combined currency) from Mercenary to Knight and apply 7% bounty from Mercenary's raid/adapt traits
5. WHEN a mercenary wins, THE System SHALL apply mirrored losses (50% currency, 25% wealth) from King to Mercenary and deduct stake from Knight

### Requirement 6: Trade Operations

**User Story:** As a King agent, I want to invest currency in trade operations to grow my wealth, so that I can strengthen my economic position.

#### Acceptance Criteria

1. WHEN a tick begins, THE System SHALL allow each King to invest 100 currency in trade if sufficient funds are available
2. WHEN a King trades, THE System SHALL deduct 100 currency and add 5 wealth units distributed as: 3 to defend, 2 to trade
3. THE System SHALL execute trade operations before raid/defend interactions in each tick
4. THE System SHALL record trade events with timestamp, King ID, investment amount, and wealth created
5. THE System SHALL NOT allow trades if the King's currency balance is below 100

### Requirement 7: Retainer System

**User Story:** As a Knight agent, I want to receive retainer payments from my employer King each tick, so that I have stable income for defending services.

#### Acceptance Criteria

1. WHEN a Knight has an employer King, THE System SHALL attempt to pay the retainer fee each tick
2. IF the employer King has sufficient currency, THEN THE System SHALL transfer the retainer amount from King to Knight
3. THE System SHALL execute retainer payments after trades but before raid/defend interactions
4. THE System SHALL record retainer events with timestamp, employer ID, Knight ID, and amount
5. IF the employer King lacks sufficient currency, THEN THE System SHALL skip the retainer payment without error

### Requirement 8: Deterministic Event Resolution

**User Story:** As a simulation scientist, I want all economic interactions to be deterministic given a seed, so that experiments are reproducible and debuggable.

#### Acceptance Criteria

1. THE System SHALL use pure functions for all economic calculations (bribe, raid_value, p_knight_win, trade)
2. THE System SHALL resolve ties deterministically using lexicographic ID comparison
3. THE System SHALL apply sigmoid and clamp functions with fixed parameters
4. THE System SHALL NOT introduce randomness in economic event resolution (randomness remains in BFF pairing only)
5. WHEN given the same initial state and seed, THE System SHALL produce identical event sequences and final states

### Requirement 9: Metrics and Telemetry

**User Story:** As a data analyst, I want comprehensive metrics on entropy, compression, wealth distribution, and event counts, so that I can analyze system dynamics and emergent patterns.

#### Acceptance Criteria

1. THE System SHALL compute per-tick metrics including: entropy, compression_ratio, copy_score_mean, wealth_total, currency_total
2. THE System SHALL track event counts: bribes_paid, bribes_accepted, raids_attempted, raids_won_by_merc, raids_won_by_knight
3. THE System SHALL calculate wealth distribution statistics (mean, median, Gini coefficient) per role
4. THE System SHALL provide opcode histogram tracking for BFF instruction usage
5. THE System SHALL output metrics in JSON format with tick number, timestamp, and all computed values

### Requirement 10: Data Output Schemas

**User Story:** As an external tool developer, I want well-defined JSON and CSV schemas for M|inc outputs, so that I can build analysis and visualization tools.

#### Acceptance Criteria

1. THE System SHALL output per-tick JSON snapshots containing: tick number, metrics object, and agents array with full state
2. THE System SHALL output CSV event logs with columns: tick, type, king, knight, merc, amount, stake, p_knight, notes
3. THE System SHALL output final agent CSV with columns: id, role, currency, compute, copy, defend, raid, trade, sense, adapt, wealth_total
4. THE System SHALL include metadata in JSON outputs: version, seed, config_hash, timestamp
5. THE System SHALL validate all outputs against documented schemas before writing

### Requirement 11: Configuration Management

**User Story:** As a simulation operator, I want to configure M|inc parameters via YAML files, so that I can run experiments with different economic settings without code changes.

#### Acceptance Criteria

1. THE System SHALL load configuration from YAML files specifying: role ratios, thresholds, exposure factors, refractory periods
2. THE System SHALL compute a config hash and include it in all output metadata
3. WHEN configuration changes, THE System SHALL invalidate cached results
4. THE System SHALL provide default configuration values for all parameters
5. THE System SHALL validate configuration on load and report errors for invalid values

### Requirement 12: Caching and Memoization

**User Story:** As a performance engineer, I want to cache deterministic economic outcomes, so that repeated state encounters execute faster.

#### Acceptance Criteria

1. THE System SHALL compute canonical state representations for agent sets
2. THE System SHALL hash canonical states combined with config hash for cache keys
3. WHEN a cached outcome exists for a state, THE System SHALL reuse it instead of recomputing
4. THE System SHALL store witness samples (input/output pairs) for cache validation
5. THE System SHALL invalidate cache entries when configuration or adapter version changes

### Requirement 13: Refractory Periods

**User Story:** As a system designer, I want to prevent immediate re-triggering of raid/defend events, so that oscillatory loops are avoided and the system remains stable.

#### Acceptance Criteria

1. THE System SHALL maintain refractory windows for event channels (raid, defend, bribe, trade)
2. WHEN an event fires, THE System SHALL block the same channel for the configured refractory period
3. THE System SHALL queue events that occur during refractory periods
4. THE System SHALL coalesce queued events when the refractory period expires
5. THE System SHALL configure refractory periods in ticks or milliseconds via YAML

### Requirement 14: Trait Emergence from BFF Activity

**User Story:** As an emergence researcher, I want agent traits to grow based on BFF tape activity, so that economic capabilities evolve from computational behaviors.

#### Acceptance Criteria

1. WHEN an agent's copy trait reaches 12 or higher, THE System SHALL increment copy by 1 every 2 ticks
2. THE System SHALL define configurable thresholds for other trait emergence rules
3. THE System SHALL apply trait drip operations at the start of each tick before other interactions
4. THE System SHALL record trait_drip events in the event log
5. THE System SHALL support disabling trait emergence via configuration flag

### Requirement 15: Integration with Existing BFF Tools

**User Story:** As a CuBFF user, I want M|inc to work seamlessly with existing analysis tools, so that I can combine economic and computational analysis.

#### Acceptance Criteria

1. THE System SHALL consume output from save_bff_trace.py without modification
2. THE System SHALL provide a CLI wrapper that pipes BFF soup data to M|inc adapter
3. THE System SHALL support running M|inc analysis on historical BFF trace files
4. THE System SHALL NOT break existing Python tool imports or CLI commands
5. THE System SHALL document integration points with existing tools in README
