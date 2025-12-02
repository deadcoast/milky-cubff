# M|inc Usage Examples

This directory contains example scripts demonstrating various ways to use M|inc for economic analysis of BFF simulations.

## Examples

### 01_process_historical_trace.py

**Purpose**: Process an existing BFF trace file with M|inc

**What it demonstrates**:
- Loading configuration from YAML
- Initializing M|inc components (registry, engine, writer)
- Assigning roles to agents
- Processing multiple ticks
- Writing output files (JSON, CSV)
- Displaying summary statistics

**Usage**:
```bash
cd python/m_inc/examples
python 01_process_historical_trace.py
```

**Output**: Creates `output/historical/` directory with:
- `ticks.json`: Per-tick snapshots
- `events.csv`: Event log
- `agents_final.csv`: Final agent states

---

### 02_live_bff_simulation.py

**Purpose**: Run M|inc alongside a live BFF simulation

**What it demonstrates**:
- Using the `run_minc_on_bff.py` wrapper script
- Coordinating BFF simulation with M|inc processing
- Processing trace data as it's generated
- Alternative approaches using the Python API

**Usage**:
```bash
cd python/m_inc/examples
python 02_live_bff_simulation.py
```

**Requirements**: 
- BFF simulation binary compiled
- `testdata/bff.txt` program file

**Output**: Creates `output/live/` directory with M|inc results

---

### 03_analyze_outputs.py

**Purpose**: Load and analyze M|inc output files

**What it demonstrates**:
- Loading JSON tick data
- Loading CSV event data
- Analyzing wealth dynamics over time
- Analyzing event patterns and frequencies
- Computing economic efficiency metrics
- Calculating wealth concentration statistics

**Usage**:
```bash
cd python/m_inc/examples
python 03_analyze_outputs.py
```

**Requirements**: Run `01_process_historical_trace.py` first to generate output files

**Optional**: Install pandas for enhanced analysis:
```bash
pip install pandas
```

---

### 04_custom_policy.py

**Purpose**: Create and test custom economic policies

**What it demonstrates**:
- Loading and modifying YAML configuration
- Creating custom policy parameters
- Running comparative simulations
- Analyzing the impact of parameter changes
- Policy customization best practices

**Usage**:
```bash
cd python/m_inc/examples
python 04_custom_policy.py
```

**Output**: 
- Creates `custom_aggressive.yaml` configuration file
- Displays side-by-side comparison of default vs custom policies

---

## Running All Examples

To run all examples in sequence:

```bash
cd python/m_inc/examples

# Process historical trace
python 01_process_historical_trace.py

# Analyze the outputs
python 03_analyze_outputs.py

# Compare custom policies
python 04_custom_policy.py

# (Optional) Run live simulation if BFF is compiled
python 02_live_bff_simulation.py
```

## Example Output Structure

After running the examples, you'll have:

```
examples/
├── output/
│   ├── historical/
│   │   ├── ticks.json
│   │   ├── events.csv
│   │   └── agents_final.csv
│   └── live/
│       ├── ticks.json
│       ├── events.csv
│       └── agents_final.csv
├── custom_aggressive.yaml
└── README.md
```

## Customization

Each example can be customized by modifying the configuration variables at the top of the script:

```python
# Configuration
trace_file = Path("path/to/your/trace.json")
config_file = Path("path/to/your/config.yaml")
output_dir = Path("path/to/output")
num_ticks = 100  # Number of ticks to process
```

## Troubleshooting

### "Trace file not found"

Make sure you're running from the correct directory and that test data exists:
```bash
cd python/m_inc/examples
ls ../testdata/  # Should show bff_trace_small.json
```

### "Module not found"

Install M|inc in development mode:
```bash
cd python/m_inc
pip install -e .
```

### "BFF program not found" (example 02)

Ensure BFF is compiled and testdata exists:
```bash
cd ../../  # Go to project root
ls testdata/bff.txt  # Should exist
```

## Further Reading

- [M|inc README](../README.md): Main documentation
- [Requirements](../../../.kiro/specs/minc-integration/requirements.md): System requirements
- [Design](../../../.kiro/specs/minc-integration/design.md): Architecture details
- [Configuration Reference](../config/README.md): YAML configuration guide

## Contributing

To add new examples:

1. Create a new numbered script (e.g., `05_my_example.py`)
2. Follow the existing format with clear docstrings
3. Add error handling and helpful output messages
4. Update this README with the new example
5. Test the example from a clean environment
