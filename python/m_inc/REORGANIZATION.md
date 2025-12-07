# M|inc Directory Reorganization

## What Was Fixed

The `python/m_inc/` directory had all test files and utility scripts dumped in the root directory, making it cluttered and unprofessional. This has been reorganized into a clean, standard Python package structure.

## Changes Made

### 1. Created New Directories

- `tests/` - All test files moved here
- `scripts/` - All validation and utility scripts moved here

### 2. Moved Files

**Test files moved to `tests/`:**
- test_agent_registry.py
- test_bff_bridge.py
- test_cache.py
- test_cli_comprehensive.sh
- test_core_models.py
- test_economic_engine.py
- test_economics.py
- test_event_aggregator.py
- test_integration.py
- test_interactions.py
- test_minc.py
- test_output_writer.py
- test_policy_dsl.py
- test_property_based.py
- test_retainer_payments.py
- test_signals.py
- test_trace_reader.py
- test_trace_reader_simple.py
- test_trade_operations.py
- test_visualizations.py

**Scripts moved to `scripts/`:**
- analyze_results.py
- analyze_traits.py
- example_policy_usage.py
- run_all_validations.py
- run_minc_on_bff.py
- run_simulation.py
- test_cli_comprehensive.sh
- validate_determinism.py
- validate_integration.py
- validate_performance.py
- validate_spec_compliance.py

### 3. Added Configuration

- `pytest.ini` - Pytest configuration pointing to tests/ directory
- `tests/__init__.py` - Makes tests a proper Python package
- `scripts/__init__.py` - Makes scripts a proper Python package

### 4. Added Documentation

- `QUICKSTART.md` - Quick start guide for new users
- `REORGANIZATION.md` - This file
- Updated `README.md` with directory structure section

## New Directory Structure

```
python/m_inc/
├── core/              # Core implementation
├── adapters/          # BFF integration adapters
├── policies/          # Policy DSL compiler
├── config/            # YAML configuration files
├── tests/             # All test files ← NEW
├── scripts/           # Validation and utility scripts ← NEW
├── examples/          # Usage examples
├── testdata/          # Test data and traces
├── utils/             # Utility functions
├── cli.py             # Main CLI entry point
├── pytest.ini         # Pytest configuration ← NEW
├── QUICKSTART.md      # Quick start guide ← NEW
├── README.md          # Full documentation (updated)
├── API.md             # API reference
└── INTEGRATION.md     # Integration guide
```

## How to Use

### Running Tests

```bash
cd python/m_inc

# Run all tests
pytest

# Run specific test file
pytest tests/test_economic_engine.py -v

# Run with coverage
pytest --cov=m_inc tests/
```

### Running Scripts

```bash
cd python/m_inc

# Run validation scripts
python scripts/validate_determinism.py
python scripts/validate_integration.py
python scripts/validate_performance.py
python scripts/validate_spec_compliance.py

# Run all validations
python scripts/run_all_validations.py

# Run M|inc on BFF
python scripts/run_minc_on_bff.py --help
```

### Running Examples

```bash
cd python/m_inc/examples

python 01_process_historical_trace.py
python 03_analyze_outputs.py
python 05_visualize_outputs.py
```

## Benefits

1. **Cleaner root directory** - Only essential files in the package root
2. **Standard Python structure** - Follows Python packaging best practices
3. **Easier navigation** - Tests and scripts are in dedicated directories
4. **Better IDE support** - IDEs recognize the standard structure
5. **Simpler pytest configuration** - Tests are in one place
6. **Professional appearance** - Looks like a well-maintained project

## No Breaking Changes

All functionality remains the same. Tests still work, scripts still run, and the package can still be installed with `pip install -e .`

The only difference is file organization - everything is cleaner and more professional.
