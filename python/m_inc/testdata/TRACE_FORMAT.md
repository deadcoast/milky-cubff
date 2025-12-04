# BFF Trace Format Documentation

This document describes the JSON format for BFF (Brainfuck Forth) trace files used by M|inc.

## Overview

A BFF trace file is a JSON array containing epoch objects. Each epoch represents one complete cycle of BFF soup pairwise interactions.

## File Structure

```json
[
  {
    "epoch": 0,
    "tapes": { ... },
    "interactions": [ ... ],
    "metrics": { ... }
  },
  {
    "epoch": 1,
    "tapes": { ... },
    "interactions": [ ... ],
    "metrics": { ... }
  }
  ...
]
```

## Epoch Object Schema

### Fields

- **epoch** (integer): Sequential epoch number starting from 0
- **tapes** (object): Map of tape ID (string) to tape content (hex string)
- **interactions** (array): List of pairwise interactions between tapes
- **metrics** (object): Computed metrics for this epoch

### Tapes Object

The `tapes` object maps tape IDs to their byte content represented as hexadecimal strings.

```json
"tapes": {
  "0": "4fd621fab9e8213388b4d975861ffb87...",
  "1": "84410c5e600ada5bcb1c83a5fa2dfed4...",
  ...
}
```

**Format Details:**
- **Key**: String representation of tape ID (e.g., "0", "1", "2")
- **Value**: 128-character hexadecimal string representing 64 bytes
  - Each byte is represented by 2 hex characters
  - Total: 64 bytes × 2 chars/byte = 128 characters

### Interactions Array

The `interactions` array contains pairs of tape IDs that interacted during this epoch.

```json
"interactions": [
  [15, 13],
  [14, 15],
  [7, 1],
  ...
]
```

**Format Details:**
- Each element is a 2-element array `[tape_a_id, tape_b_id]`
- IDs are integers (not strings)
- Order matters: tape_a is executed first, then tape_b
- The same tape can appear in multiple interactions

### Metrics Object

The `metrics` object contains computed statistics for the epoch.

```json
"metrics": {
  "entropy": 6.0,
  "compression_ratio": 2.5,
  "copy_score_mean": 0.5
}
```

**Standard Metrics:**
- **entropy** (float): Shannon entropy of the tape population
- **compression_ratio** (float): Compression efficiency metric
- **copy_score_mean** (float): Average copy trait score across population

## Example Files

### Small Trace (10 epochs)

`trace_10tick.json` - Quick testing and development
- 10 epochs
- 20 tapes per epoch
- 10 interactions per epoch
- Suitable for unit tests and rapid iteration

### Medium Trace (100 epochs)

`trace_100tick.json` - Validation and integration testing
- 100 epochs
- 20 tapes per epoch
- 10 interactions per epoch
- Suitable for integration tests and performance validation

### Existing Test Data

- `bff_trace_small.json` - Real BFF simulation data (5 epochs)
- `bff_trace_medium.json` - Real BFF simulation data (larger dataset)

## Usage with M|inc

### Loading a Trace

```python
from m_inc.adapters.trace_reader import TraceReader

reader = TraceReader("testdata/trace_10tick.json")
epoch_data = reader.read_epoch()
```

### Processing with CLI

```bash
python -m m_inc.cli \
  --trace testdata/trace_10tick.json \
  --config config/minc_default.yaml \
  --output output/ \
  --ticks 10
```

## Generating Custom Traces

Use the provided script to generate synthetic traces:

```bash
python testdata/generate_example_traces.py
```

Or create custom traces programmatically:

```python
from testdata.generate_example_traces import generate_trace
from pathlib import Path

generate_trace(num_epochs=50, output_file=Path("custom_trace.json"))
```

## Validation

Traces should conform to the following constraints:

1. **Epoch numbers** must be sequential starting from 0
2. **Tape IDs** must be consistent within an epoch
3. **Hex strings** must be exactly 128 characters (64 bytes)
4. **Interactions** must reference valid tape IDs from the same epoch
5. **Metrics** must be numeric values

## Notes

- Tape content is represented as hex for readability and compatibility
- The actual BFF VM operates on the decoded byte values
- M|inc processes epochs sequentially to maintain determinism
- Metrics are optional but recommended for analysis
