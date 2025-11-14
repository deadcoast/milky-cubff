# M|inc - Mercenaries Incorporated

Economic incentive layer for CuBFF (CUDA Brainfuck Forth) self-replicating soup experiments.

## Overview

M|inc extends the BFF experiment by layering economic behaviors on top of the tape-based evolutionary system. Agents are assigned roles (Kings, Knights, Mercenaries) and engage in economic interactions including bribes, raids, defends, trades, and retainers.

## Features

- **Non-invasive integration**: Separate Python package, no changes to BFF core
- **Deterministic processing**: Pure functions, reproducible with seed
- **Configurable behavior**: YAML-driven parameters
- **Comprehensive metrics**: Entropy, compression, wealth distribution, event tracking
- **Multiple output formats**: JSON snapshots, CSV event logs

## Installation

### From source

```bash
cd python/m_inc
pip install -e .
```

### With development dependencies

```bash
pip install -e ".[dev]"
```

## Quick Start

### Process a BFF trace file

```bash
minc --trace testdata/bff_trace.json \
     --config config/minc_default.yaml \
     --output output/ \
     --ticks 100
```

### Run with live BFF simulation

```bash
./bin/main --lang bff_noheads | minc --stream --config config.yaml
```

### Python API

```python
from m_inc import AgentRegistry, EconomicEngine
from m_inc.adapters import TraceReader
from m_inc.core import ConfigLoader

# Load configuration
config = ConfigLoader.load("config/minc_default.yaml")

# Initialize components
trace_reader = TraceReader("testdata/bff_trace.json")
registry = AgentRegistry(config.registry)
engine = EconomicEngine(registry, config.economic)

# Process ticks
for tick in range(1, 101):
    epoch_data = trace_reader.read_epoch()
    result = engine.process_tick(tick)
    print(f"Tick {tick}: {result.metrics.wealth_total} total wealth")
```

## Configuration

M|inc uses YAML configuration files. See `config/minc_default.yaml` for a complete example.

### Key configuration sections

- **roles**: Agent role ratios and initialization
- **economic**: Economic parameters (raid weights, defend resolution, etc.)
- **refractory**: Cooldown periods for event channels
- **cache**: Caching and memoization settings
- **output**: Output format options

## Architecture

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

## Output Formats

### JSON Ticks

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
  "agents": [
    {
      "id": "K-01",
      "role": "king",
      "currency": 5400,
      "wealth": {
        "compute": 14,
        "copy": 16,
        "defend": 22,
        "raid": 3,
        "trade": 18,
        "sense": 7,
        "adapt": 9
      }
    }
  ]
}
```

### CSV Events

Event log with all interactions:

```csv
tick,type,king,knight,merc,amount,stake,p_knight,notes
1,bribe_accept,K-01,,M-12,350,,,success
1,defend_win,K-01,N-07,M-19,,250,0.52,
```

## Development

### Running tests

```bash
pytest
```

### Code formatting

```bash
black .
ruff check .
```

### Type checking

```bash
mypy m_inc
```

## Documentation

- [Requirements](../../.kiro/specs/minc-integration/requirements.md)
- [Design](../../.kiro/specs/minc-integration/design.md)
- [Implementation Tasks](../../.kiro/specs/minc-integration/tasks.md)
- [M|inc Overview](../../docs/OVERVIEW.md)
- [0.1.1 Spec](../../docs/0.1.1/)

## License

Apache License 2.0 - See LICENSE file for details.

## References

- [CuBFF Repository](https://github.com/paradigms-of-intelligence/cubff)
- [BFF Paper](https://arxiv.org/abs/2406.19108)
- Agüera y Arcas, B. (2024). "Computational Life: How Well-formed, Self-replicating Programs Emerge from Simple Interaction"
