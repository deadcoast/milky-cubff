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

## BFF Integration

M|inc integrates seamlessly with existing BFF tools through adapters and wrapper scripts.

### Using the Wrapper Script

The `run_minc_on_bff.py` wrapper provides three modes of operation:

#### 1. Run BFF simulation and analyze

```bash
python ../run_minc_on_bff.py \
  --bff-program ../../testdata/bff.txt \
  --config config/minc_default.yaml \
  --output output/ \
  --ticks 100
```

This will:
1. Run the BFF program using `save_bff_trace.py`
2. Convert the binary trace to JSON format
3. Process with M|inc economic engine
4. Generate output files

#### 2. Analyze existing BFF trace

```bash
python ../run_minc_on_bff.py \
  --bff-trace path/to/trace.bin \
  --config config/minc_default.yaml \
  --output output/ \
  --ticks 100
```

#### 3. Convert BFF trace to JSON

```bash
python ../run_minc_on_bff.py \
  --convert path/to/trace.bin \
  --output trace.json
```

### BFF Bridge Adapter

The BFF bridge adapter (`adapters/bff_bridge.py`) handles conversion between BFF binary format and M|inc EpochData:

```python
from m_inc.adapters.bff_bridge import BFFBridge, stream_bff_to_minc

# Read BFF trace and convert to epochs
with BFFBridge("trace.bin") as bridge:
    for epoch in bridge.read_all_states_as_epochs():
        print(f"Epoch {epoch.epoch_num}: {len(epoch.tapes)} tapes")

# Stream BFF data for processing
for epoch in stream_bff_to_minc("trace.bin"):
    # Process epoch with M|inc
    pass
```

### Trace Format

BFF binary traces use the format produced by `save_bff_trace.py`:

```
Header:
- 4 bytes: Magic number ('BFF\0')
- 4 bytes: Format version (1)
- 4 bytes: Tape size (128)

For each state:
- 4 bytes: Program counter
- 4 bytes: Head 0 position
- 4 bytes: Head 1 position
- 128 bytes: Tape contents
```

The bridge splits each 128-byte tape into two 64-byte tapes for M|inc processing.

### Integration Workflow

```
┌─────────────────┐
│ BFF Simulation  │
│   (main.cc)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│save_bff_trace.py│
│  (binary trace) │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   BFF Bridge    │
│  (conversion)   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  M|inc Engine   │
│  (economics)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Output Files    │
│ (JSON/CSV)      │
└─────────────────┘
```

### Standalone Converter

For simple trace conversion without M|inc dependencies:

```bash
python ../convert_bff_trace.py input.bin output.json [num_states]
```

This standalone script converts BFF binary traces to JSON format without requiring the M|inc package to be installed.

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
