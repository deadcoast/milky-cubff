# M|inc Quick Start

## Installation

```bash
cd python/m_inc
pip install -e .
```

## Running M|inc

### Basic Usage

```bash
# Show help
python -m m_inc.cli --help

# Process a BFF trace
python -m m_inc.cli \
  --trace testdata/trace_10tick.json \
  --config config/minc_default.yaml \
  --output output/ \
  --ticks 10
```

### Using the Wrapper Script

```bash
# From project root
python python/m_inc/scripts/run_minc_on_bff.py --help
```

## Running Tests

```bash
cd python/m_inc

# Run all tests
pytest

# Run specific test file
pytest tests/test_economic_engine.py -v

# Run with coverage
pytest --cov=m_inc tests/
```

## Running Validation Scripts

```bash
cd python/m_inc

# Run all validations
python scripts/run_all_validations.py

# Run specific validation
python scripts/validate_determinism.py
python scripts/validate_integration.py
python scripts/validate_performance.py
python scripts/validate_spec_compliance.py
```

## Examples

```bash
cd python/m_inc/examples

# Process historical trace
python 01_process_historical_trace.py

# Analyze outputs
python 03_analyze_outputs.py

# Visualize results
python 05_visualize_outputs.py
```

## Directory Structure

```
python/m_inc/
├── core/              # Core implementation
├── adapters/          # BFF integration adapters
├── policies/          # Policy DSL compiler
├── config/            # YAML configuration files
├── tests/             # All test files
├── scripts/           # Validation and utility scripts
├── examples/          # Usage examples
├── testdata/          # Test data and traces
└── cli.py             # Main CLI entry point
```

## Common Issues

### Import Errors

If you get import errors, make sure you've installed the package:
```bash
cd python/m_inc
pip install -e .
```

### Missing Dependencies

Install all dependencies:
```bash
pip install -e .[dev]
```

## Documentation

- Full documentation: `README.md`
- API reference: `API.md`
- Integration guide: `INTEGRATION.md`
- Spec documents: `../../.kiro/specs/minc-integration/`
