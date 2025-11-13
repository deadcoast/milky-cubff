# M|inc Integration Spec

## Overview

This specification defines the integration of the Mercenaries Incorporated (M|inc) economic incentive system into the CuBFF framework. M|inc extends the BFF self-replicating soup experiment by layering economic behaviors on top of the existing tape-based evolutionary system.

## Spec Status

- **Requirements**: ✅ Complete (15 requirements)
- **Design**: ✅ Complete (8 components, full architecture)
- **Tasks**: ✅ Complete (17 major tasks, 60+ subtasks)

## Quick Links

- [Requirements Document](requirements.md) - User stories and acceptance criteria
- [Design Document](design.md) - Architecture and component specifications
- [Implementation Tasks](tasks.md) - Step-by-step implementation plan

## Key Features

### Economic Layer
- **Roles**: Kings, Knights, Mercenaries with distinct incentive structures
- **Currency & Wealth**: Fungible currency and seven wealth traits (compute, copy, defend, raid, trade, sense, adapt)
- **Interactions**: Bribes, raids, defends, trades, retainers

### Technical Features
- **Non-Invasive**: Separate Python package, no changes to BFF core
- **Deterministic**: Pure functions, reproducible with seed
- **Configurable**: YAML-driven parameters
- **Performant**: Caching, memoization, batch processing
- **Observable**: JSON/CSV outputs with comprehensive metrics

## Architecture Summary

```
BFF Simulation (C++/CUDA)
    ↓
Trace Reader (Python)
    ↓
Agent Registry (role assignment)
    ↓
Economic Engine (tick processing)
    ├─ Soup Drip (trait emergence)
    ├─ Trade Operations (wealth creation)
    ├─ Retainer Payments (knight income)
    └─ Interactions (bribes, raids, defends)
    ↓
Event Aggregator (metrics)
    ↓
Output Writer (JSON/CSV)
```

## Implementation Approach

### Phase 1: Core Infrastructure (Tasks 1-4)
- Set up project structure
- Implement data models and schemas
- Create Trace Reader
- Build Agent Registry

### Phase 2: Economic Engine (Tasks 5-6)
- Implement tick orchestration
- Add economic calculation functions
- Build bribe and defend resolution

### Phase 3: Advanced Features (Tasks 7-11)
- Add Policy DSL Compiler
- Implement Cache Layer
- Build Signal Processor
- Create Event Aggregator
- Implement Output Writer

### Phase 4: Integration (Tasks 12-14)
- Build CLI interface
- Create configuration files
- Integrate with existing BFF tools

### Phase 5: Validation (Tasks 15-17)
- Write comprehensive tests
- Create documentation
- Validate against spec outputs

## Getting Started

### For Implementers

1. Read the [Requirements Document](requirements.md) to understand what needs to be built
2. Review the [Design Document](design.md) for architectural details
3. Follow the [Implementation Tasks](tasks.md) in order
4. Start with Task 1 (project structure) and work sequentially

### For Reviewers

1. Verify requirements cover all use cases
2. Check design for completeness and consistency
3. Ensure tasks map to requirements and design
4. Validate that optional tasks are appropriately marked

## Key Design Decisions

### 1. Non-Invasive Integration
- M|inc is a separate Python package under `python/m_inc/`
- No modifications to existing C++ code or Python tools
- Read-only consumption of BFF traces

### 2. Deterministic Processing
- All economic calculations are pure functions
- Tie-breaking uses lexicographic ID comparison
- Randomness only in BFF pairing (existing behavior)

### 3. Layered Architecture
- Clear separation between BFF simulation and M|inc adapter
- Modular components with well-defined interfaces
- Plugin-style design for extensibility

### 4. Configuration-Driven
- YAML files for all parameters
- Config hash for cache invalidation
- Hot-swappable policies via DSL

### 5. Performance Optimization
- Caching of deterministic outcomes
- Batch processing of ticks
- Lazy evaluation of metrics
- Optional parallel processing

## Testing Strategy

### Unit Tests (Required)
- Economic calculation functions
- Data model validation
- Component initialization

### Integration Tests (Required)
- Component interactions
- Data flow pipelines
- Cache integration

### End-to-End Tests (Required)
- Full pipeline from trace to outputs
- Determinism verification
- Schema validation

### Property-Based Tests (Optional)
- Invariant checking
- Conservation laws
- Cache correctness

## Output Formats

### JSON Ticks (`ticks.json`)
Per-tick snapshots with metrics and agent states:
```json
{
  "tick": 1,
  "metrics": {
    "entropy": 5.91,
    "compression_ratio": 2.70,
    "wealth_total": 399,
    "currency_total": 12187
  },
  "agents": [...]
}
```

### CSV Events (`events.csv`)
Event log with all interactions:
```csv
tick,type,king,knight,merc,amount,stake,p_knight,notes
1,bribe_accept,K-01,,M-12,350,,,success
1,defend_win,K-01,N-07,M-19,,250,0.52,
```

### CSV Final Agents (`agents_final.csv`)
Final agent state after all ticks:
```csv
id,role,currency,compute,copy,defend,raid,trade,sense,adapt,wealth_total
K-01,king,5400,14,16,22,3,18,7,9,89
```

## Configuration Example

```yaml
version: "0.1.1"
seed: 1337

roles:
  ratios:
    king: 0.10
    knight: 0.20
    mercenary: 0.70

economic:
  currency_to_wealth_ratio: [100, 5]
  bribe_leakage: 0.05
  raid_value_weights:
    alpha_raid: 1.0
    beta_sense_adapt: 0.25
    gamma_king_defend: 0.60
    delta_king_exposed: 0.40

refractory:
  raid: 2
  defend: 1
  bribe: 1
  trade: 0

cache:
  enabled: true
  max_size: 10000
```

## Dependencies

### Required
- Python 3.8+
- pyyaml
- pandas
- numpy
- pydantic

### Optional (for development)
- pytest (testing)
- hypothesis (property-based testing)
- black (code formatting)
- mypy (type checking)

## Timeline Estimate

- **Phase 1** (Core Infrastructure): 2-3 days
- **Phase 2** (Economic Engine): 3-4 days
- **Phase 3** (Advanced Features): 4-5 days
- **Phase 4** (Integration): 2-3 days
- **Phase 5** (Validation): 2-3 days

**Total**: 13-18 days for full implementation

**MVP** (core features only, skip optional tasks): 8-10 days

## Success Criteria

### Functional
- [ ] All required tasks completed
- [ ] All tests passing
- [ ] Outputs match 0.1.1 spec reference data
- [ ] Determinism verified (same seed → same outputs)

### Non-Functional
- [ ] Tick processing < 10ms for 1000 agents
- [ ] Cache hit rate > 80%
- [ ] Memory usage < 100MB for 10,000 agents
- [ ] Documentation complete and clear

## References

- [CuBFF Repository](https://github.com/paradigms-of-intelligence/cubff)
- [BFF Paper](https://arxiv.org/abs/2406.19108)
- [M|inc Overview](../../docs/OVERVIEW.md)
- [0.1.1 Spec Documentation](../../docs/0.1.1/)

## Contact

For questions or clarifications about this spec, please refer to:
- Requirements document for "what" needs to be built
- Design document for "how" it should be built
- Tasks document for "when" and "in what order"

---

**Spec Version**: 1.0  
**Created**: 2025-01-27  
**Status**: Ready for Implementation
