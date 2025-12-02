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

M|inc (Mercenaries Incorporated) is a fully-integrated economic incentive system that layers on top of BFF simulations. It adds economic behaviors (currency, wealth, bribes, raids, defends, trades) to analyze emergent economic dynamics in self-replicating systems.

### Overview

M|inc extends BFF by:
- Assigning economic roles (Kings, Knights, Mercenaries) to BFF programs
- Tracking currency and seven wealth traits (compute, copy, defend, raid, trade, sense, adapt) for each agent
- Simulating deterministic economic interactions (trades, bribes, raids, defends)
- Providing comprehensive metrics, telemetry, and event logging
- Supporting configurable policies via YAML without code changes

### Key Features

- **Non-Invasive Integration**: M|inc operates as a separate Python layer without modifying core BFF C++/CUDA code
- **Deterministic Processing**: All economic calculations are pure functions with reproducible outcomes
- **Performance Optimized**: Includes caching layer with memoization for repeated state encounters
- **Flexible Configuration**: YAML-driven policies and parameters for easy experimentation
- **Comprehensive Testing**: 100+ unit tests, property-based tests, and validation scripts
- **Multiple Output Formats**: JSON tick snapshots, CSV event logs, and final agent state exports

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

#### 3. Use M|inc CLI directly

```bash
python -m m_inc.cli \
  --trace testdata/bff_trace.json \
  --config python/m_inc/config/minc_default.yaml \
  --output output/ \
  --ticks 100
```

### Architecture

M|inc follows a layered adapter architecture with these core components:

1. **Trace Reader** - Parses BFF soup traces and normalizes data
2. **Agent Registry** - Maps tape IDs to economic agents with roles
3. **Economic Engine** - Executes tick logic and economic interactions
4. **Policy DSL Compiler** - Compiles YAML policies into executable functions
5. **Cache Layer** - Memoizes deterministic outcomes for performance
6. **Signal Processor** - Manages event channels with refractory periods
7. **Event Aggregator** - Collects and summarizes economic events
8. **Output Writer** - Serializes results to JSON and CSV formats

### Integration Points

M|inc integrates seamlessly with existing BFF tools:

1. **BFF Bridge Adapter** (`python/m_inc/adapters/bff_bridge.py`)
   - Reads binary traces from `save_bff_trace.py`
   - Converts BFF soup format to M|inc EpochData
   - Supports both file and stream inputs

2. **Wrapper Script** (`python/run_minc_on_bff.py`)
   - Orchestrates BFF simulation and M|inc analysis
   - Handles trace conversion and processing
   - Provides unified CLI interface

3. **Trace Normalizer** (`python/m_inc/adapters/trace_normalizer.py`)
   - Normalizes different trace formats
   - Handles JSON and binary inputs
   - Validates trace structure

### Configuration

M|inc behavior is controlled via YAML configuration files:

- `python/m_inc/config/minc_default.yaml` - Default parameters for production runs
- `python/m_inc/config/minc_fast.yaml` - Optimized for quick experiments
- `python/m_inc/config/policy_example.yaml` - Example custom policy definitions

Key configuration sections:
- **Roles**: Role ratios and mutation rates
- **Economic**: Raid weights, defend resolution, trade parameters
- **Refractory**: Cooldown periods for event channels
- **Cache**: Memoization settings for performance
- **Output**: JSON/CSV format options

### Output Files

M|inc generates three types of output:

1. **Tick JSON** (`ticks.json`) - Per-tick snapshots with metrics and agent states
2. **Event CSV** (`events.csv`) - Detailed log of all economic events
3. **Final Agents CSV** (`agents_final.csv`) - Final state of all agents

All outputs include metadata (version, seed, config_hash, timestamp) for reproducibility.

### Documentation

For detailed documentation, see:
- `python/m_inc/README.md` - Complete M|inc package documentation
- `python/m_inc/API.md` - API reference for all components
- `python/m_inc/INTEGRATION.md` - Integration guide with BFF
- `.kiro/specs/minc-integration/` - Requirements, design, and implementation spec
- `docs/0.1.1/` - Architecture and database schemas
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

### Examples

M|inc includes 5 complete usage examples in `python/m_inc/examples/`:

1. **Process Historical Trace** - Load and analyze existing BFF traces
2. **Live BFF Simulation** - Run BFF and M|inc together
3. **Analyze Outputs** - Compute statistics and metrics from results
4. **Custom Policy** - Define and test custom economic policies
5. **Visualize Outputs** - Generate plots and charts from M|inc data

Run examples:
```bash
cd python/m_inc/examples
python 01_process_historical_trace.py
python 03_analyze_outputs.py
python 05_visualize_outputs.py
```

### Testing

M|inc includes comprehensive test coverage:

```bash
cd python/m_inc

# Run all tests
pytest test_*.py -v

# Run specific test suites
pytest test_economic_engine.py -v
pytest test_property_based.py -v

# Run validation scripts
python validate_integration.py
python validate_determinism.py
python validate_performance.py
python validate_spec_compliance.py
```

### Development Status

M|inc is **production ready** with all planned features implemented:

- ✓ Core economic engine with deterministic processing
- ✓ Agent registry with role management
- ✓ Policy DSL compiler for configurable behavior
- ✓ Cache layer for performance optimization
- ✓ Signal processor with refractory periods
- ✓ Event aggregator for metrics computation
- ✓ Output writer with JSON/CSV formats
- ✓ BFF integration adapters
- ✓ CLI interface with multiple modes
- ✓ Comprehensive test suite (100+ tests)
- ✓ Complete documentation and examples
- ✓ Validation scripts for determinism and spec compliance

### Contributing

M|inc follows the spec-driven development methodology. See `.kiro/specs/minc-integration/` for the complete requirements, design, and implementation specification. All tasks have been completed and validated.
