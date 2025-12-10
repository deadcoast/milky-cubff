# Implementation Plan

## Overview

This implementation plan tracks the development of M|inc (Mercenaries Incorporated), an economic incentive layer for the CuBFF self-replicating soup experiment. All tasks have been completed and the system is fully operational.

## Status Summary

- **Total Tasks**: 17 major tasks with 60+ subtasks
- **Completed**: All tasks ✓
- **Status**: Production ready

### Recent hygiene fixes

- Removed accidentally committed CPython bytecode (`__pycache__/`, `*.pyc`) so future diffs remain source-only.
- Documented that PR artifact checks (cache scrubbing, smoke runs) are executed manually rather than enforced in CI.

---

- [x] 1. Set up M|inc project structure and core infrastructure
  - Create `python/m_inc/` package directory with `__init__.py`
  - Create subdirectories: `core/`, `adapters/`, `policies/`, `utils/`
  - Set up `pyproject.toml` with dependencies (pyyaml, pandas, numpy, pydantic)
  - Create `README.md` with installation and usage instructions
  - _Requirements: 1.1, 1.2, 1.3_






- [x] 2. Implement core data models and type definitions
  - [x] 2.1 Create `core/models.py` with Agent, WealthTraits, Role, Event, EventType dataclasses
    - Define Agent dataclass with all economic attributes
    - Define WealthTraits dataclass with seven trait fields and helper methods
    - Define Event dataclass with all event fields


    - Define Role and EventType enums
    - Add validation methods to ensure non-negative values
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_

  - [x] 2.2 Create `core/schemas.py` with Pydantic schemas for validation
    - Define AgentSchema for agent state validation


    - Define EventSchema for event validation
    - Define TickMetricsSchema for metrics validation
    - Define ConfigSchema for YAML configuration validation




    - Add JSON schema export methods
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 2.3 Create `core/config.py` for configuration management
    - Implement ConfigLoader to parse YAML files
    - Implement config hash computation


    - Add default configuration values
    - Add configuration validation logic
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_






- [x] 3. Implement Trace Reader component
  - [x] 3.1 Create `adapters/trace_reader.py` with TraceReader class
    - Implement `__init__` to accept file path or stream
    - Implement `read_epoch()` to parse BFF trace data
    - Implement `get_tape_by_id()` for tape lookup

    - Implement `get_population_snapshot()` for full population
    - Add support for both JSON and binary trace formats
    - _Requirements: 1.3, 15.1, 15.3_

  - [x] 3.2 Add trace format detection and normalization
    - Detect trace format (JSON, binary, stream)

    - Normalize data into EpochData structure
    - Handle missing or malformed data gracefully
    - _Requirements: 1.3, 15.1_





- [x] 4. Implement Agent Registry component
  - [x] 4.1 Create `core/agent_registry.py` with AgentRegistry class
    - Implement `__init__` with RegistryConfig
    - Implement `assign_roles()` to map tape IDs to roles based on ratios
    - Implement `get_agent()` for agent lookup by ID

    - Implement `get_agents_by_role()` for role-based filtering
    - Implement `update_agent()` to persist agent state changes
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 4.2 Add agent initialization logic
    - Initialize currency based on role (Kings: 5000-7000, Knights: 100-300, Mercs: 0-50)

    - Initialize wealth traits based on role distributions
    - Assign employer relationships for Knights
    - Set bribe thresholds for Kings
    - _Requirements: 2.4, 7.1_

  - [x] 4.3 Add role mutation support (optional)

    - Implement role mutation probability check
    - Handle role transitions with state preservation
    - Log role mutation events
    - _Requirements: 2.5_

- [x] 5. Implement Economic Engine core

  - [x] 5.1 Create `core/economic_engine.py` with EconomicEngine class
    - Implement `__init__` with AgentRegistry and EconomicConfig
    - Implement `process_tick()` orchestration method
    - Implement tick sequence: drip → trade → retainer → interactions
    - Implement `_compute_metrics()` for tick-level metrics
    - Implement `_snapshot_agents()` for agent state capture


    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2_


  - [x] 5.2 Implement soup drip logic
    - Create `_soup_drip()` method
    - Check copy trait threshold (>= 12)
    - Apply +1 copy every 2 ticks
    - Generate trait_drip events
    - _Requirements: 14.1, 14.2, 14.3, 14.4_


  - [x] 5.3 Implement trade operations
    - Create `_execute_trades()` method
    - Check King currency >= 100
    - Deduct 100 currency, add 3 defend + 2 trade wealth
    - Generate trade events
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_


  - [x] 5.4 Implement retainer payments
    - Create `_pay_retainers()` method
    - Iterate Knights with employers
    - Transfer retainer_fee from King to Knight if funds available
    - Generate retainer events
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_


  - [x] 5.5 Implement interaction orchestration
    - Create `_execute_interactions()` method
    - Iterate Mercenaries in ID order
    - Select target King deterministically (highest wealth_exposed)
    - Assign defending Knights (employer first, then strongest free)
    - Route to bribe evaluation or contest
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Implement economic calculation functions
  - [x] 6.1 Create `core/economics.py` with pure calculation functions
    - Implement `wealth_total(agent)` to sum all traits
    - Implement `wealth_exposed(agent, config)` with exposure factors
    - Implement `king_defend_projection(king, knights, attackers, config)`
    - Implement `raid_value(merc, king, knights, config)` with formula
    - Implement `sigmoid(x)` helper function
    - Implement `clamp(value, min, max)` helper function
    - _Requirements: 4.5, 8.1, 8.2_

  - [x] 6.2 Implement bribe resolution logic
    - Create `resolve_bribe(king, merc, knights, config)` function
    - Compute raid_value
    - Check threshold >= raid_value AND currency >= threshold
    - Return BribeOutcome with transfers and leakage
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 6.3 Implement defend resolution logic
    - Create `p_knight_win(knight, merc, config)` function
    - Compute trait delta and sigmoid transformation
    - Apply clamp to [0.05, 0.95]
    - Create `resolve_defend(knight, merc, config)` function
    - Implement deterministic tie-breaking (knight.id < merc.id)
    - Return DefendOutcome with winner and transfers
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 6.4 Implement wealth and currency transfer functions
    - Create `apply_bribe_outcome(king, merc, outcome)` function
    - Create `apply_wealth_leakage(king, leakage_frac)` function
    - Create `apply_mirrored_losses(king, merc, config)` function
    - Create `apply_bounty(knight, merc, frac)` function
    - Ensure all transfers maintain non-negative invariants
    - _Requirements: 3.5, 4.3, 5.4, 5.5_

- [x] 7. Implement Policy DSL Compiler
  - [x] 7.1 Create `policies/policy_dsl.py` with PolicyCompiler class
    - Implement `__init__` to accept YAML config
    - Implement `compile()` to generate CompiledPolicies
    - Implement `validate()` to check policy syntax
    - Parse formula strings into Python expressions
    - Generate callable functions from YAML definitions
    - _Requirements: 11.1, 11.2, 11.4_

  - [x] 7.2 Add policy function generators
    - Generate `bribe_outcome` callable from YAML
    - Generate `raid_value` callable from YAML
    - Generate `p_knight_win` callable from YAML
    - Generate `trade_action` callable from YAML
    - Ensure generated functions are pure (no side effects)
    - _Requirements: 8.1, 8.2_

  - [x] 7.3 Add policy validation and testing
    - Validate formula syntax before compilation
    - Test generated functions against known inputs
    - Verify determinism of compiled policies
    - _Requirements: 8.1, 8.2, 11.5_

- [x] 8. Implement Cache Layer
  - [x] 8.1 Create `core/cache.py` with CacheLayer class
    - Implement `__init__` with CacheConfig
    - Implement `get_or_compute(state, compute_fn)` with memoization
    - Implement `invalidate(reason)` to clear cache
    - Implement `get_stats()` for cache hit/miss metrics
    - Use LRU eviction policy with configurable max size
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 8.2 Implement canonical state computation
    - Create `compute_canonical_state(agents)` function
    - Sort agents by ID for deterministic ordering
    - Extract relevant fields (role, currency, wealth)
    - Compute state hash with config hash
    - _Requirements: 12.1, 12.2_

  - [x] 8.3 Add witness sampling for cache validation



    - Store 5% of cache writes as witness samples

    - Periodically validate cached outcomes against recomputation
    - Log cache validation failures
    - _Requirements: 12.4_

- [x] 9. Implement Signal Processor

  - [x] 9.1 Create `core/signals.py` with SignalProcessor class
    - Implement `__init__` with SignalConfig
    - Implement `process_events(events)` to route to channels
    - Implement `update_refractory(tick_num)` to manage cooldowns
    - Implement `is_channel_active(channel)` to check refractory state
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_


  - [x] 9.2 Add event queuing and coalescing
    - Queue events that occur during refractory periods
    - Coalesce queued events when refractory expires
    - Apply priority-based scheduling




    - _Requirements: 13.3, 13.4_

- [x] 10. Implement Event Aggregator
  - [x] 10.1 Create `core/event_aggregator.py` with EventAggregator class
    - Implement `__init__` to initialize aggregation state
    - Implement `add_event(event)` to collect events

    - Implement `get_tick_summary(tick_num)` to generate summaries
    - Compute event counts by type
    - Compute currency flows by role
    - Compute wealth changes by role and trait
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_


  - [x] 10.2 Add metrics computation
    - Compute entropy from agent wealth distribution
    - Compute compression ratio proxy





    - Compute copy_score_mean from agent copy traits
    - Compute wealth_total and currency_total
    - Compute Gini coefficient for wealth inequality
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 11. Implement Output Writer

  - [x] 11.1 Create `adapters/output_writer.py` with OutputWriter class
    - Implement `__init__` with output directory and OutputConfig
    - Implement `write_tick_json(tick_result)` for JSON snapshots
    - Implement `write_event_csv(events)` for event log
    - Implement `write_final_agents_csv(agents)` for final state

    - Implement `validate_schema(data, schema_name)` for validation
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 11.2 Add JSON serialization
    - Serialize TickResult to JSON with proper formatting
    - Include metadata (version, seed, config_hash, timestamp)
    - Handle numpy types and custom objects
    - Support optional compression (gzip)
    - _Requirements: 10.1, 10.4_

  - [x] 11.3 Add CSV serialization
    - Write event log with proper column ordering
    - Write final agent state with all attributes
    - Handle missing values gracefully
    - Support append mode for streaming writes
    - _Requirements: 10.2, 10.3_

- [x] 12. Implement CLI interface
  - [x] 12.1 Create `cli.py` with main entry point
    - Parse command-line arguments (trace, config, output, ticks)
    - Load configuration from YAML
    - Initialize all components (registry, engine, writer)
    - Run tick processing loop
    - Handle errors and logging
    - _Requirements: 1.5, 15.2, 15.5_

  - [x] 12.2 Add streaming mode support
    - Accept stdin as trace source
    - Process ticks incrementally
    - Write outputs in real-time
    - _Requirements: 15.2_

  - [x] 12.3 Add batch processing mode
    - Process multiple trace files in parallel
    - Aggregate results across runs
    - Generate summary reports
    - _Requirements: 15.3_

- [x] 13. Create configuration files and examples
  - [x] 13.1 Create `config/minc_default.yaml` with default parameters
    - Set role ratios (10% Kings, 20% Knights, 70% Mercs)
    - Set economic parameters (raid weights, defend resolution, etc.)
    - Set refractory periods
    - Set cache configuration
    - Set output options
    - _Requirements: 11.1, 11.4_

  - [x] 13.2 Create `config/minc_fast.yaml` for quick experiments
    - Disable caching for simplicity
    - Reduce refractory periods
    - Minimal output (JSON only)
    - _Requirements: 11.1_

  - [x] 13.3 Create example trace files in `testdata/`
    - Create small 10-tick trace for testing
    - Create medium 100-tick trace for validation
    - Document trace format
    - _Requirements: 15.3_

- [x] 14. Implement integration with existing BFF tools
  - [x] 14.1 Create `adapters/bff_bridge.py` for BFF integration
    - Parse output from `save_bff_trace.py`
    - Convert BFF soup format to M|inc EpochData
    - Handle both file and stream inputs
    - _Requirements: 15.1, 15.2_

  - [x] 14.2 Create wrapper script `run_minc_on_bff.py`
    - Run BFF simulation with `main.cc`
    - Pipe output to M|inc CLI
    - Collect and display results
    - _Requirements: 15.2, 15.5_

  - [x] 14.3 Update existing tool documentation
    - Add M|inc section to main README.md
    - Document integration points
    - Provide usage examples
    - _Requirements: 15.5_

- [x] 15. Write comprehensive tests
  - [x] 15.1 Create unit tests for economic functions
    - Test `raid_value` with various agent configurations
    - Test `p_knight_win` with edge cases
    - Test `resolve_bribe` outcomes
    - Test `resolve_defend` outcomes
    - Test wealth/currency transfer functions
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 15.2 Create unit tests for data models
    - Test Agent validation and methods
    - Test WealthTraits operations
    - Test Event serialization
    - Test schema validation
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

  - [x] 15.3 Create integration tests for components
    - Test TraceReader → AgentRegistry flow
    - Test EconomicEngine → EventAggregator flow
    - Test CacheLayer integration
    - Test SignalProcessor integration
    - _Requirements: 12.1, 12.2, 12.3, 13.1, 13.2_

  - [x] 15.4 Create end-to-end tests
    - Test full pipeline from trace to outputs
    - Test determinism (same seed → same results)
    - Test schema validation for all outputs
    - Test performance benchmarks
    - _Requirements: 8.5, 10.5_

  - [x] 15.5 Create property-based tests
    - Test currency/wealth conservation invariants
    - Test non-negativity invariants
    - Test deterministic resolution properties
    - Test cache correctness
    - _Requirements: 3.5, 8.1, 8.2, 12.3_

- [x] 16. Create documentation and examples
  - [x] 16.1 Write `python/m_inc/README.md`
    - Installation instructions
    - Quick start guide
    - Configuration reference
    - API documentation
    - _Requirements: 15.5_

  - [x] 16.2 Create usage examples
    - Example: Process historical BFF trace
    - Example: Run M|inc with live BFF simulation
    - Example: Analyze M|inc outputs
    - Example: Custom policy configuration
    - _Requirements: 15.2, 15.5_

  - [x] 16.3 Create API reference documentation
    - Document all public classes and functions
    - Include type signatures and docstrings
    - Provide code examples
    - _Requirements: 15.5_

  - [x] 16.4 Create visualization examples
    - Plot wealth distribution over time
    - Plot currency flows between roles
    - Plot event frequency heatmaps
    - Plot agent trajectories
    - _Requirements: 9.3, 9.4_

- [x] 17. Perform integration validation
  - [x] 17.1 Run M|inc on existing BFF traces
    - Process traces from `testdata/`
    - Verify outputs match expected schemas
    - Check for errors or warnings
    - _Requirements: 15.1, 15.3_

  - [x] 17.2 Validate determinism
    - Run same trace with same seed multiple times
    - Verify bit-identical outputs
    - Test across different Python versions
    - _Requirements: 8.5_

  - [x] 17.3 Validate performance
    - Benchmark tick processing speed
    - Measure cache hit rates
    - Profile memory usage
    - Optimize bottlenecks if needed
    - _Requirements: 12.1, 12.2, 12.3_

  - [x] 17.4 Validate against 0.1.1 spec outputs
    - Compare outputs with reference data in `docs/0.1.1/database/`
    - Verify metrics match expected values
    - Verify event sequences match expected patterns
    - _Requirements: 10.1, 10.2, 10.3_

---

## Implementation Complete ✓

All tasks have been successfully implemented and validated. The M|inc system is fully operational with:

### Core Components
- ✓ Agent registry with role management
- ✓ Economic engine with deterministic processing
- ✓ Policy DSL compiler for configurable behavior
- ✓ Cache layer for performance optimization
- ✓ Signal processor with refractory periods
- ✓ Event aggregator for metrics computation
- ✓ Output writer with JSON/CSV formats

### Integration
- ✓ BFF bridge adapter for trace conversion
- ✓ CLI interface with multiple modes
- ✓ Wrapper scripts for seamless BFF integration
- ✓ Streaming and batch processing support

### Testing & Validation
- ✓ Comprehensive unit tests (100+ tests)
- ✓ Property-based tests for invariants
- ✓ Integration tests for component interactions
- ✓ End-to-end validation scripts
- ✓ Performance benchmarks
- ✓ Determinism verification
- ✓ Spec compliance validation

### Documentation
- ✓ Complete README with installation and usage
- ✓ API reference documentation
- ✓ Configuration guide with examples
- ✓ Integration documentation
- ✓ 5 usage examples with visualizations

### Configuration
- ✓ Default configuration (minc_default.yaml)
- ✓ Fast configuration (minc_fast.yaml)
- ✓ Policy example (policy_example.yaml)
- ✓ Comprehensive parameter documentation

### Next Steps

The M|inc implementation is complete and ready for use. To get started:

1. **Install M|inc**:
   ```bash
   cd python/m_inc
   pip install -e .
   ```

2. **Run examples**:
   ```bash
   cd examples
   python 01_process_historical_trace.py
   python 03_analyze_outputs.py
   python 05_visualize_outputs.py
   ```

3. **Process BFF traces**:
   ```bash
   python run_minc_on_bff.py --bff-trace trace.bin --config config/minc_default.yaml --output results/
   ```

4. **Run validation**:
   ```bash
   python validate_integration.py
   python validate_determinism.py
   python validate_performance.py
   python validate_spec_compliance.py
   ```

For detailed usage instructions, see [python/m_inc/README.md](../../python/m_inc/README.md).
