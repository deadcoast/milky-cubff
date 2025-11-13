# M|inc 0.1.2 - Map of Content

**Navigation Guide for AI Agents and Developers**

## Quick Start

- **New to M|inc?** Start with [README](README.md)
- **Upgrading from 0.1.1?** See [Migration Guide](guides/migration-guide.md)
- **Want to write policies?** Check [Policy Writing Guide](guides/policy-writing.md)
- **Need performance?** Read [Performance Tuning](guides/performance-tuning.md)

## Core Documentation

### Architecture
- [Policy DSL](architecture/policy-dsl.md) - Hot-swappable economic rules
- [Cache Layer](architecture/cache-layer.md) - Memoization and performance
- [Signal Processing](architecture/signal-processing.md) - Event channels and refractory periods
- [Spatial Dynamics](architecture/spatial-dynamics.md) - 2D grid and localized interactions
- [Learning Agents](architecture/learning-agents.md) - Adaptive behaviors and strategies
- [Integrations](architecture/integrations.md) - Bridges to GoL, Wireworld, SmoothLife

### API Reference
- [Policy API](api/policy-api.md) - Policy DSL language reference
- [Cache API](api/cache-api.md) - Caching interface and functions
- [Spatial API](api/spatial-api.md) - Spatial grid and neighborhood functions
- [Visualization API](api/visualization-api.md) - Dashboard REST API

### Guides
- [Migration Guide](guides/migration-guide.md) - Upgrading from 0.1.1 to 0.1.2
- [Policy Writing](guides/policy-writing.md) - Creating custom economic policies
- [Performance Tuning](guides/performance-tuning.md) - Optimization strategies
- [Spatial Setup](guides/spatial-setup.md) - Configuring spatial dynamics

### Examples
- [Custom Policies](examples/custom-policies/) - Example policy YAML files
- [Spatial Configs](examples/spatial-configs/) - Spatial configuration examples
- [Integration Demos](examples/integration-demos/) - External system integration examples

## Feature Matrix

| Feature | 0.1.0 | 0.1.1 | 0.1.2 |
|---------|-------|-------|-------|
| Core Economic Engine | ❌ | ✅ | ✅ |
| Agent Roles (K/N/M) | ❌ | ✅ | ✅ |
| Employment Bonus | ❌ | ✅ | ✅ |
| JSON/CSV Output | ❌ | ✅ | ✅ |
| CLI Interface | ❌ | ✅ | ✅ |
| Policy DSL | ❌ | ❌ | ✅ |
| Cache Layer | ❌ | ❌ | ✅ |
| Signal Processing | ❌ | ❌ | ✅ |
| Spatial Dynamics | ❌ | ❌ | ✅ |
| Learning Agents | ❌ | ❌ | ✅ |
| Visualization | ❌ | ❌ | ✅ |
| External Integrations | ❌ | ❌ | ✅ |

## Implementation Status

### ✅ Completed (0.1.1)
- Core economic engine
- Agent registry and roles
- Economic interactions (bribes, raids, defends, trades)
- Deterministic event resolution
- Configuration management
- Output writers (JSON/CSV)
- CLI with streaming support

### 🚧 In Progress (0.1.2)
- Policy DSL compiler
- Cache layer
- Signal processor
- Event aggregator

### 📋 Planned (0.1.2)
- Spatial dynamics
- Learning agents
- Advanced analytics
- Visualization dashboard
- External integrations

### 🔮 Future (0.1.3+)
- Multi-agent reinforcement learning
- Genetic algorithm for trait evolution
- Network topology (beyond 2D grid)
- Time-series forecasting
- Blockchain integration for currency

## Dependencies

### From 0.1.0
- BFF research and background
- Variations research (GoL, Wireworld, etc.)
- Initial architecture concepts

### From 0.1.1
- Core data models
- Economic engine
- Agent registry
- Configuration system
- Output formats

### New in 0.1.2
- Policy DSL parser
- Cache infrastructure
- Signal processing framework
- Spatial grid system
- Learning algorithms
- Visualization framework
- Integration bridges

## Cross-References

### Related to Policy DSL
- [Policy API](api/policy-api.md)
- [Policy Writing Guide](guides/policy-writing.md)
- [Custom Policy Examples](examples/custom-policies/)

### Related to Performance
- [Cache Layer Architecture](architecture/cache-layer.md)
- [Cache API](api/cache-api.md)
- [Performance Tuning Guide](guides/performance-tuning.md)

### Related to Spatial Dynamics
- [Spatial Architecture](architecture/spatial-dynamics.md)
- [Spatial API](api/spatial-api.md)
- [Spatial Setup Guide](guides/spatial-setup.md)
- [Spatial Config Examples](examples/spatial-configs/)

### Related to Learning
- [Learning Agents Architecture](architecture/learning-agents.md)
- [Adaptive Strategies](architecture/learning-agents.md#adaptive-strategies)

### Related to Integrations
- [Integrations Architecture](architecture/integrations.md)
- [Integration Demos](examples/integration-demos/)
- [GoL Bridge](architecture/integrations.md#game-of-life)
- [Wireworld Bridge](architecture/integrations.md#wireworld)

## Version History

- **0.1.0** (2024-Q4): Initial planning and research
- **0.1.1** (2025-Q1): Core implementation with basic economic engine
- **0.1.2** (2025-Q2): Advanced features and optimizations ← **You are here**
- **0.1.3** (2025-Q3): Planned - ML/AI enhancements
- **0.2.0** (2025-Q4): Planned - Production-ready release

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting pull requests
- Writing documentation

## License

Apache License 2.0 - See [LICENSE](../../LICENSE) for details.

---

**Last Updated**: 2025-01-27  
**Maintainers**: CuBFF M|inc Team  
**Status**: Planning Phase
