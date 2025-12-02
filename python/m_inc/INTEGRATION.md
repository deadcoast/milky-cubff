# M|inc Integration Guide

This guide explains how to integrate M|inc with existing BFF tools and workflows.

## Overview

M|inc is designed as a non-invasive layer that sits on top of BFF simulations. It consumes BFF trace data and produces economic analysis without modifying the core BFF system.

## Integration Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Existing BFF System                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │
│  │ main.cc  │───▶│ Soup VM  │───▶│ save_bff_trace.py│   │
│  │(C++/CUDA)│    │ (*.cu)   │    │ (trace output)   │   │
│  └──────────┘    └──────────┘    └──────────┬───────┘   │
└──────────────────────────────────────────────┼───────────┘
                                               │
                                               ▼
┌──────────────────────────────────────────────────────────┐
│                   M|inc Adapter Layer                    │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │ BFF Bridge   │───▶│Agent Registry│───▶│ Economic  │  │
│  │              │    │ & Mapper     │    │ Engine    │  │
│  └──────────────┘    └──────────────┘    └─────┬─────┘  │
│                                                 │        │
│  ┌──────────────┐    ┌──────────────┐          │        │
│  │ Event        │◀───│ Output       │◀─────────┘        │
│  │ Aggregator   │    │ Writer       │                   │
│  └──────────────┘    └──────────────┘                   │
└──────────────────────────────────────────────────────────┘
                                │
                                ▼
                  ┌──────────────────────────┐
                  │  JSON Ticks, CSV Events, │
                  │  Final Agent State       │
                  └──────────────────────────┘
```

## Integration Points

### 1. BFF Bridge Adapter

**Location**: `python/m_inc/adapters/bff_bridge.py`

**Purpose**: Converts BFF binary traces to M|inc EpochData format

**Key Features**:
- Reads binary format from `save_bff_trace.py`
- Splits 128-byte tapes into two 64-byte tapes
- Supports both file and stream inputs
- Handles format validation and error checking

**Usage**:
```python
from m_inc.adapters.bff_bridge import BFFBridge

# Read BFF trace
bridge = BFFBridge("trace.bin")
epoch = bridge.read_state_as_epoch()

# Access tape data
tape0 = epoch.tapes[0]  # First 64 bytes
tape1 = epoch.tapes[1]  # Last 64 bytes

# Get metrics
pc = epoch.metrics["pc"]
head0 = epoch.metrics["head0"]
```

### 2. Wrapper Script

**Location**: `python/run_minc_on_bff.py`

**Purpose**: Orchestrates BFF simulation and M|inc analysis

**Modes**:

1. **Run and Analyze**: Execute BFF program and analyze results
   ```bash
   python run_minc_on_bff.py \
     --bff-program testdata/bff.txt \
     --config m_inc/config/minc_default.yaml \
     --output results/
   ```

2. **Analyze Existing**: Process pre-generated BFF trace
   ```bash
   python run_minc_on_bff.py \
     --bff-trace trace.bin \
     --config m_inc/config/minc_default.yaml \
     --output results/
   ```

3. **Convert Only**: Convert BFF trace to JSON
   ```bash
   python run_minc_on_bff.py \
     --convert trace.bin \
     --output trace.json
   ```

### 3. Standalone Converter

**Location**: `python/convert_bff_trace.py`

**Purpose**: Simple trace conversion without M|inc dependencies

**Usage**:
```bash
python convert_bff_trace.py input.bin output.json [num_states]
```

**Benefits**:
- No package installation required
- Fast conversion for data preparation
- Useful for debugging and inspection

## Data Flow

### BFF Trace Format

Binary format produced by `save_bff_trace.py`:

```
Header (12 bytes):
  - Magic: 'BFF\0' (4 bytes)
  - Version: 1 (4 bytes, little-endian uint32)
  - Tape Size: 128 (4 bytes, little-endian uint32)

State Records (140 bytes each):
  - PC: Program counter (4 bytes, little-endian uint32)
  - Head0: First head position (4 bytes, little-endian uint32)
  - Head1: Second head position (4 bytes, little-endian uint32)
  - Tape: Full tape contents (128 bytes)
```

### M|inc EpochData Format

Python dataclass used internally:

```python
@dataclass
class EpochData:
    epoch_num: int                          # Sequential epoch number
    tapes: Dict[int, bytearray]             # {0: tape0, 1: tape1}
    interactions: List[Tuple[int, int]]     # [(0, 1)]
    metrics: Dict[str, float]               # {pc, head0, head1, state_num}
```

### JSON Output Format

Converted format for M|inc processing:

```json
[
  {
    "epoch": 0,
    "tapes": {
      "0": "4fd621fab9e8...",  // 128 hex chars (64 bytes)
      "1": "84410c5e600a..."   // 128 hex chars (64 bytes)
    },
    "interactions": [[0, 1]],
    "metrics": {
      "pc": 2.0,
      "head0": 10.0,
      "head1": 20.0,
      "state_num": 0.0
    }
  }
]
```

## Example Workflows

### Workflow 1: Quick Analysis

Analyze a BFF program with default settings:

```bash
# Run BFF and analyze in one command
python python/run_minc_on_bff.py \
  --bff-program testdata/bff.txt \
  --config python/m_inc/config/minc_default.yaml \
  --output output/quick/ \
  --ticks 50
```

### Workflow 2: Batch Processing

Process multiple BFF traces:

```bash
# Generate traces
for prog in testdata/*.txt; do
  python python/save_bff_trace.py "$prog" "traces/$(basename $prog .txt).bin"
done

# Process with M|inc
for trace in traces/*.bin; do
  python python/run_minc_on_bff.py \
    --bff-trace "$trace" \
    --config python/m_inc/config/minc_default.yaml \
    --output "results/$(basename $trace .bin)/" \
    --ticks 100
done
```

### Workflow 3: Custom Analysis Pipeline

Build a custom analysis pipeline:

```python
from pathlib import Path
from m_inc.adapters.bff_bridge import BFFBridge
from m_inc.core.config import ConfigLoader
from m_inc.core.agent_registry import AgentRegistry
from m_inc.core.economic_engine import EconomicEngine

# Load configuration
config = ConfigLoader("config/minc_default.yaml").load()

# Initialize components
bridge = BFFBridge("trace.bin")
registry = AgentRegistry(config.registry, seed=42)
engine = EconomicEngine(registry, config.economic, config.trait_emergence)

# Get initial tape IDs
first_epoch = bridge.read_state_as_epoch()
tape_ids = list(first_epoch.tapes.keys())
registry.assign_roles(tape_ids)
registry.assign_knight_employers()

# Process ticks
results = []
for tick in range(1, 101):
    result = engine.process_tick(tick)
    results.append(result)
    
    # Custom analysis
    if result.metrics.wealth_total > 1000:
        print(f"Tick {tick}: High wealth detected!")

# Save results
import json
with open("custom_results.json", "w") as f:
    json.dump([r.to_dict() for r in results], f, indent=2)
```

### Workflow 4: Real-time Monitoring

Monitor BFF simulation in real-time:

```bash
# Terminal 1: Run BFF simulation
bin/main --lang bff_noheads > bff_output.txt

# Terminal 2: Monitor with M|inc
tail -f bff_output.txt | python -m m_inc.cli \
  --stream \
  --config python/m_inc/config/minc_fast.yaml \
  --output live_results/
```

## Compatibility

### BFF Versions

M|inc is compatible with:
- BFF trace format version 1
- Tape size: 128 bytes (2 × 64-byte tapes)
- All BFF language variants (bff, bff_noheads, bff8, etc.)

### Python Versions

- Python 3.8+
- Dependencies: pyyaml, pandas, numpy, pydantic

### Operating Systems

- Linux (tested)
- macOS (tested)
- Windows (via WSL2)

## Troubleshooting

### Issue: "Invalid BFF trace format"

**Cause**: Trace file is not in BFF binary format

**Solution**: Ensure trace was generated with `save_bff_trace.py`:
```bash
python python/save_bff_trace.py input.txt output.bin
```

### Issue: "Module not found: m_inc"

**Cause**: M|inc package not installed

**Solution**: Install the package:
```bash
cd python/m_inc
pip install -e .
```

### Issue: "Unsupported BFF trace version"

**Cause**: Trace file version mismatch

**Solution**: Regenerate trace with current version of `save_bff_trace.py`

### Issue: "Unexpected tape size"

**Cause**: Trace file has non-standard tape size

**Solution**: M|inc expects 128-byte tapes. Check BFF configuration.

## Performance Tips

1. **Use Fast Config**: For quick experiments, use `minc_fast.yaml`
2. **Limit Ticks**: Process fewer ticks for initial testing
3. **Disable Caching**: Set `cache.enabled: false` for deterministic debugging
4. **Batch Processing**: Process multiple traces in parallel
5. **Stream Mode**: Use streaming for real-time analysis

## Advanced Integration

### Custom Trace Readers

Implement custom trace readers for other formats:

```python
from m_inc.adapters.trace_reader import EpochData

class CustomTraceReader:
    def read_epoch(self) -> EpochData:
        # Read from custom format
        # Convert to EpochData
        return EpochData(
            epoch_num=0,
            tapes={0: tape0, 1: tape1},
            interactions=[(0, 1)],
            metrics={}
        )
```

### Custom Economic Policies

Define custom policies in YAML:

```yaml
policies:
  raid_value:
    formula: "custom_formula"
    params:
      custom_param: 1.5
```

### Event Hooks

Add custom event processing:

```python
from m_inc.core.economic_engine import EconomicEngine

class CustomEngine(EconomicEngine):
    def process_tick(self, tick_num):
        result = super().process_tick(tick_num)
        
        # Custom processing
        for event in result.events:
            if event.type == "bribe_accept":
                self.on_bribe(event)
        
        return result
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/paradigms-of-intelligence/cubff/issues
- Documentation: `docs/0.1.1/`
- Spec: `.kiro/specs/minc-integration/`

## References

- [BFF Paper](https://arxiv.org/abs/2406.19108)
- [M|inc Requirements](../../.kiro/specs/minc-integration/requirements.md)
- [M|inc Design](../../.kiro/specs/minc-integration/design.md)
- [Trace Format](testdata/TRACE_FORMAT.md)
