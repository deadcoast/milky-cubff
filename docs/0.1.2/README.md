# M|inc Version 0.1.2 - Advanced Features Specification

**Version**: 0.1.2  
**Status**: Planning  
**Previous Version**: 0.1.1 (Implemented)  
**Target Release**: Q2 2025

## Overview

Version 0.1.2 represents the next evolution of the Mercenaries Incorporated (M|inc) economic layer for CuBFF. This release focuses on implementing advanced features that were envisioned in earlier specifications but not yet realized, including:

- **Policy DSL** for hot-swappable economic rules
- **Cache Layer** with memoization for performance
- **Signal Processing** with refractory periods
- **Advanced Metrics** and analytics
- **Spatial Dynamics** for localized interactions
- **Learning Agents** with adaptive strategies
- **Visualization Tools** for real-time monitoring
- **Integration with Variations** (GoL, Wireworld, SmoothLife)

## What's New in 0.1.2

### Implemented in 0.1.1 ✅
- Core economic engine with deterministic tick processing
- Agent roles (Kings, Knights, Mercenaries) with distinct incentives
- Economic interactions (bribes, raids, defends, trades, retainers)
- Employment bonus for hired knights
- Balanced trait distributions
- JSON/CSV output formats
- CLI interface with streaming support
- Configuration management via YAML

### Planned for 0.1.2 🚀

#### 1. Policy DSL & Hot-Swapping
- YAML-based policy definition language
- Runtime policy compilation to Python callables
- Hot-swap policies without restarting simulation
- Policy versioning and rollback
- A/B testing framework for policy comparison

#### 2. Performance Optimization
- Cache layer with canonical state hashing
- Memoization of deterministic outcomes
- Witness sampling for cache validation
- Parallel tick processing
- Batch event aggregation

#### 3. Signal Processing & Refractory Periods
- Event channels with priorities
- Refractory periods to prevent oscillations
- Event queuing and coalescing
- Channel-based event routing

#### 4. Spatial Dynamics
- 2D grid placement for agents
- Localized interactions (neighborhood-based)
- Spatial diffusion of wealth/currency
- Territory control mechanics
- Migration and clustering behaviors

#### 5. Learning & Adaptation
- Adaptive bribe thresholds based on success rates
- Knight strategy learning (when to defend vs retreat)
- Mercenary target selection optimization
- King alliance formation heuristics
- Trait evolution based on performance

#### 6. Advanced Analytics
- Wealth inequality metrics (Gini coefficient, Lorenz curves)
- Economic cycle detection
- Agent lineage tracking
- Strategy effectiveness analysis
- Emergent behavior classification

#### 7. Visualization & Monitoring
- Real-time web dashboard
- Agent state visualization
- Economic flow diagrams
- Event timeline viewer
- Spatial heatmaps (if spatial mode enabled)

#### 8. Integration with Variations
- GoL (Game of Life) as external data source
- Wireworld circuit simulation integration
- SmoothLife continuous dynamics
- HashLife optimization techniques
- Cross-system agent migration

## Architecture Changes

### New Components

```
m_inc/
├── policies/
│   ├── policy_dsl.py          # Policy compiler
│   ├── policy_runtime.py      # Runtime policy execution
│   └── builtin_policies/      # Standard policy templates
├── cache/
│   ├── cache_layer.py         # Memoization system
│   ├── canonical_state.py     # State normalization
│   └── witness_validator.py   # Cache validation
├── signals/
│   ├── signal_processor.py    # Event channel management
│   ├── refractory.py          # Cooldown mechanics
│   └── event_router.py        # Priority-based routing
├── spatial/
│   ├── grid.py                # 2D spatial grid
│   ├── neighborhoods.py       # Locality functions
│   └── diffusion.py           # Spatial dynamics
├── learning/
│   ├── adaptive_agents.py     # Learning behaviors
│   ├── strategy_optimizer.py  # Strategy evolution
│   └── heuristics.py          # Decision-making rules
├── analytics/
│   ├── inequality_metrics.py  # Wealth distribution analysis
│   ├── cycle_detector.py      # Economic pattern recognition
│   └── lineage_tracker.py     # Agent genealogy
├── visualization/
│   ├── dashboard.py           # Web UI server
│   ├── static/                # Frontend assets
│   └── api/                   # REST API for data
└── integrations/
    ├── gol_bridge.py          # Game of Life integration
    ├── wireworld_bridge.py    # Wireworld integration
    └── smoothlife_bridge.py   # SmoothLife integration
```

## Migration Path from 0.1.1

All 0.1.1 features remain fully functional. New features are opt-in via configuration:

```yaml
version: "0.1.2"

# Enable advanced features
features:
  policy_dsl: true
  cache_layer: true
  signal_processing: true
  spatial_dynamics: false  # Opt-in
  learning_agents: false   # Opt-in
  visualization: true
  integrations: []         # Empty = disabled

# Policy DSL configuration
policies:
  source: "policies/custom_policy.yaml"
  hot_reload: true
  validation: strict

# Cache configuration
cache:
  enabled: true
  max_size: 100000
  witness_sample_rate: 0.05
  ttl_seconds: 3600

# Signal processing
signals:
  refractory_enabled: true
  channels:
    raid: {priority: 1, refractory_ticks: 2}
    defend: {priority: 2, refractory_ticks: 1}
    bribe: {priority: 3, refractory_ticks: 1}
    trade: {priority: 4, refractory_ticks: 0}

# Spatial dynamics (if enabled)
spatial:
  grid_size: [100, 100]
  neighborhood_radius: 5
  diffusion_rate: 0.1
  migration_cost: 10

# Learning (if enabled)
learning:
  adaptation_rate: 0.01
  exploration_rate: 0.1
  memory_length: 100
```

## Performance Targets

| Metric | 0.1.1 | 0.1.2 Target |
|--------|-------|--------------|
| Ticks/second (1000 agents) | 100 | 500 |
| Memory usage (10k agents) | 100MB | 150MB |
| Cache hit rate | N/A | >80% |
| Tick processing latency | 10ms | 2ms |

## Compatibility

- **Backward Compatible**: All 0.1.1 configs work in 0.1.2
- **Data Format**: JSON/CSV schemas unchanged
- **API**: New endpoints added, existing ones preserved
- **Python Version**: 3.8+ (same as 0.1.1)

## Documentation Structure

```
docs/0.1.2/
├── README.md                    # This file
├── MOC.md                       # Map of content
├── architecture/
│   ├── policy-dsl.md           # Policy language spec
│   ├── cache-layer.md          # Caching architecture
│   ├── signal-processing.md    # Event channels
│   ├── spatial-dynamics.md     # Spatial mechanics
│   ├── learning-agents.md      # Adaptive behaviors
│   └── integrations.md         # External system bridges
├── api/
│   ├── policy-api.md           # Policy DSL reference
│   ├── cache-api.md            # Cache interface
│   ├── spatial-api.md          # Spatial functions
│   └── visualization-api.md    # Dashboard API
├── guides/
│   ├── migration-guide.md      # Upgrading from 0.1.1
│   ├── policy-writing.md       # Creating custom policies
│   ├── performance-tuning.md   # Optimization guide
│   └── spatial-setup.md        # Enabling spatial mode
└── examples/
    ├── custom-policies/        # Example policy files
    ├── spatial-configs/        # Spatial configuration examples
    └── integration-demos/      # Integration examples
```

## Development Roadmap

### Phase 1: Core Infrastructure (Weeks 1-2)
- [ ] Policy DSL compiler
- [ ] Cache layer implementation
- [ ] Signal processor with refractory periods
- [ ] Event aggregator enhancements

### Phase 2: Advanced Features (Weeks 3-4)
- [ ] Spatial dynamics system
- [ ] Learning agent behaviors
- [ ] Advanced analytics modules
- [ ] Visualization dashboard

### Phase 3: Integrations (Weeks 5-6)
- [ ] GoL bridge implementation
- [ ] Wireworld integration
- [ ] SmoothLife connector
- [ ] Cross-system protocols

### Phase 4: Testing & Documentation (Weeks 7-8)
- [ ] Comprehensive test suite
- [ ] Performance benchmarks
- [ ] User guides and tutorials
- [ ] API documentation

## Success Criteria

- [ ] All 0.1.1 tests pass
- [ ] 5x performance improvement with caching
- [ ] Policy hot-swap works without restart
- [ ] Spatial mode supports 10k+ agents
- [ ] Learning agents show measurable adaptation
- [ ] Dashboard renders real-time data
- [ ] At least one external integration working

## References

- [0.1.0 Specification](../0.1.0/README.md)
- [0.1.1 Specification](../0.1.1/README.md)
- [Implementation Spec](.kiro/specs/minc-integration/README.md)
- [BFF Research](../0.1.0/architecture/m.inc-3.research-LEGACY.md)
- [Variations Research](../0.1.0/architecture/m.inc-2.variations-LEGACY.md)

---

**Status**: This specification is in planning phase. Implementation will begin after 0.1.1 is stable and deployed.
