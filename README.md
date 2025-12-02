# CuBFF

This project provides a (optionally) CUDA-based implementation of a
self-modifying soup of programs which show emergence of self-replicators. Most
experiments in the "Computational Life: How Well-formed, Self-replicating Programs 
Emerge from Simple Interaction" paper (arxiv link (https://arxiv.org/abs/2406.19108) were done using this code.

## Dependencies

### Linux
On debian-based systems, install `build-essential` and `libbrotli-dev` (and optionally CUDA):

  `sudo apt install build-essential libbrotli-dev`

On Arch Linux, install the `brotli` and `base-devel` packages.

The project also provides a `flake.nix` file, so you may also make the
dependencies available with Nix using `nix develop`.

### Windows
**For Windows users, please see the Windows-specific build instructions:**

- Quick Start: See `QUICKSTART_WINDOWS.md`
- Detailed Guide: See `WINDOWS_BUILD.md`
- Build Options: See `BUILD_OPTIONS.md`

The easiest method is using **WSL2** - see the quick start guide for details.

## Build Instructions

### Linux/Mac
Compile the code by running `make` (for the CUDA-enabled version) or `make CUDA=0`.

### Windows
See `WINDOWS_BUILD.md` for detailed instructions. Quick start with WSL2:
```bash
wsl
sudo apt install build-essential libbrotli-dev pkg-config
make CUDA=0
```

### CMake (Cross-platform)
Alternatively, build using CMake:
```bash
mkdir build && cd build
cmake .. -DUSE_CUDA=OFF
cmake --build . --config Release
```

## Run Instructions

You can run a simulation, for example with:
  `bin/main --lang bff_noheads`

Or on Windows:
  `.\bin\main.exe --lang bff_noheads`

The file `cubff_example.py` provides an example of how to use the Python bindings.

## M|inc: Economic Layer Integration

M|inc (Mercenaries Incorporated) is an economic incentive system that layers on top of BFF simulations. It adds economic behaviors (currency, wealth, bribes, raids, defends, trades) to analyze emergent economic dynamics in self-replicating systems.

### Overview

M|inc extends BFF by:
- Assigning economic roles (Kings, Knights, Mercenaries) to BFF programs
- Tracking currency and wealth traits for each agent
- Simulating economic interactions (trades, bribes, raids, defends)
- Providing comprehensive metrics and telemetry

### Installation

Install M|inc as a Python package:

```bash
cd python/m_inc
pip install -e .
```

Or with development dependencies:

```bash
pip install -e .[dev]
```

### Quick Start

#### 1. Run M|inc on existing BFF trace

```bash
# Generate a BFF trace
python python/save_bff_trace.py testdata/bff.txt output/bff_trace.bin

# Process with M|inc
python python/run_minc_on_bff.py \
  --bff-trace output/bff_trace.bin \
  --config python/m_inc/config/minc_default.yaml \
  --output output/minc_results/ \
  --ticks 100
```

#### 2. Run BFF simulation and analyze with M|inc

```bash
python python/run_minc_on_bff.py \
  --bff-program testdata/bff.txt \
  --config python/m_inc/config/minc_default.yaml \
  --output output/minc_results/ \
  --ticks 100
```

#### 3. Convert BFF trace to JSON format

```bash
python python/run_minc_on_bff.py \
  --convert output/bff_trace.bin \
  --output output/trace.json
```

### Integration Points

M|inc integrates with existing BFF tools through:

1. **BFF Bridge Adapter** (`python/m_inc/adapters/bff_bridge.py`)
   - Reads binary traces from `save_bff_trace.py`
   - Converts BFF soup format to M|inc EpochData
   - Supports both file and stream inputs

2. **Wrapper Script** (`python/run_minc_on_bff.py`)
   - Orchestrates BFF simulation and M|inc analysis
   - Handles trace conversion and processing
   - Provides unified CLI interface

3. **Standalone Converter** (`python/convert_bff_trace.py`)
   - Converts BFF binary traces to JSON format
   - No package dependencies required
   - Useful for data preparation and analysis

### Configuration

M|inc behavior is controlled via YAML configuration files:

- `python/m_inc/config/minc_default.yaml` - Default parameters for production runs
- `python/m_inc/config/minc_fast.yaml` - Optimized for quick experiments

Key configuration options:
- Role ratios (Kings, Knights, Mercenaries)
- Economic parameters (raid weights, defend resolution)
- Refractory periods for event channels
- Cache settings for performance
- Output formats (JSON, CSV)

### Output Files

M|inc generates three types of output:

1. **Tick JSON** (`ticks.json`) - Per-tick snapshots with metrics and agent states
2. **Event CSV** (`events.csv`) - Detailed log of all economic events
3. **Final Agents CSV** (`agents_final.csv`) - Final state of all agents

### Documentation

For detailed documentation, see:
- `python/m_inc/README.md` - M|inc package documentation
- `docs/0.1.1/` - Architecture and API reference
- `python/m_inc/testdata/TRACE_FORMAT.md` - Trace format specification

### Example Workflow

```bash
# 1. Run BFF simulation
bin/main --lang bff_noheads > /dev/null

# 2. Save trace
python python/save_bff_trace.py testdata/bff.txt output/trace.bin

# 3. Analyze with M|inc
python python/run_minc_on_bff.py \
  --bff-trace output/trace.bin \
  --config python/m_inc/config/minc_default.yaml \
  --output output/minc/ \
  --ticks 100

# 4. View results
cat output/minc/ticks.json | jq '.[] | {tick, wealth_total, currency_total}'
```

### Advanced Usage

#### Custom Policies

M|inc supports custom economic policies via YAML:

```yaml
policies:
  raid_value:
    formula: "alpha*merc.raid + beta*(merc.sense+merc.adapt) - gamma*king_defend"
    params:
      alpha: 1.0
      beta: 0.25
      gamma: 0.60
```

#### Streaming Mode

Process BFF traces in real-time:

```bash
bin/main --lang bff_noheads | python -m m_inc.cli --stream --config config.yaml
```

#### Batch Processing

Process multiple traces in parallel:

```bash
python -m m_inc.cli --batch traces/*.json --config config.yaml --output results/
```

### Testing

Run M|inc tests:

```bash
cd python/m_inc
pytest test_*.py -v
```

### Contributing

M|inc follows the spec-driven development methodology. See `.kiro/specs/minc-integration/` for requirements, design, and implementation tasks.
