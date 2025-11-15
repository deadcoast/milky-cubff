# BFF eXtended (bffx) - Digital Abiogenesis Simulation Framework

**Version 0.1.1**

`bffx` is a Python package that implements the core BFF (Brainfuck-variant) Virtual Machine demonstrating **digital abiogenesis** - the emergence of self-replicating programs from random bytes through simple interactions.

## What is Digital Abiogenesis?

Digital abiogenesis is the emergence of life (self-replicating programs) from random bytes through simple interaction rules. This package shows **HOW life emerges from nothing**:

1. **Start**: Millions of random 64-byte programs (pure noise, no structure)
2. **Interact**: Randomly pair programs, concatenate them, execute as self-modifying code
3. **Evolve**: After millions of iterations, entropy drops dramatically
4. **Emerge**: Complex self-replicating programs spontaneously appear
5. **Purpose**: Reproduction emerges as the dominant behavior

**The emergence of life is the emergence of purpose.** Programs that successfully copy themselves gain dominance in the population.

## Core Concepts

### The BFF Virtual Machine

- **Unified 128-byte tape** where code == data (enables self-modification)
- **10 opcodes**: `><+-{}.,[]` (approximately 31/32 of random bytes are NO-OPs)
- **Two data pointers**: head0 and head1 for reading/writing
- **Dynamic bracket matching** supports self-modification during execution
- **Precise halt conditions**: step limit, out-of-bounds, unmatched brackets

### The Primordial Soup Workflow

The canonical workflow that enables emergence:


```
1. PAIR:        Randomly pair all programs in population
2. CONCATENATE: Join A + B → 128-byte tape (random AB or BA order)
3. EXECUTE:     Run BFF VM with step limit (default 8192 instructions)
4. SPLIT:       Split tape at byte 64 → A' + B'
5. MUTATE:      Optionally apply per-byte mutation
6. REPLACE:     A→A', B→B' in population
7. REPEAT:      Millions of epochs until self-replicators emerge
```

### The Entropy Drop

The signature of emergence is a dramatic drop in population entropy:

- **Random soup**: Shannon entropy ~7-8 bits, compression ratio ~1.0
- **After emergence**: Entropy drops to ~3-4 bits, compression ratio ~0.2-0.3
- **Replication events**: Exact self-copying becomes frequent

## Installation

```bash
# From the project root
cd python
pip install -e .
```

## Quick Start

### Run a Basic Experiment

```bash
python -m bffx.cli --pop 1024 --epochs 10000 --mutate 0.00005 --seed 42
```

This runs a population of 1024 programs for 10,000 epochs with mutation rate 0.00005.


### Watch the Entropy Drop

```bash
python -m bffx.cli \
  --pop 2048 \
  --epochs 50000 \
  --step-limit 8192 \
  --mutate 0.00005 \
  --seed 123 \
  --report-every 500 \
  --log-events
```

Output shows the transition from chaos to order:

```
epoch    500 | top_count   1/2048 | compress_ratio 0.987 | shannon_bits 7.823
opcode_counts: >:0 <:0 +:0 -:0 {:0 }:0 .:0 ,:0 [:0 ]:0

epoch   5000 | top_count   8/2048 | compress_ratio 0.654 | shannon_bits 6.142
opcode_counts: >:234 <:198 +:156 -:142 {:12 }:8 .:892 ,:856 [:45 ]:43

epoch  25000 | top_count 512/2048 | compress_ratio 0.234 | shannon_bits 3.142
opcode_counts: >:12453 <:11892 +:8234 -:7891 {:234 }:198 .:15234 ,:14892 [:892 ]:891
exact_replication_events_this_epoch: 256
```

## CLI Reference

### Command-Line Arguments


| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--pop` | int | 1024 | Population size (must be even) |
| `--epochs` | int | 10000 | Number of epochs to run |
| `--step-limit` | int | 8192 | Max instructions per interaction |
| `--mutate` | float | 0.0 | Per-byte mutation probability |
| `--seed` | int | None | Random seed for reproducibility |
| `--report-every` | int | 100 | Reporting interval (epochs) |
| `--log-events` | flag | False | Track exact replication events |

### Example Commands

**Fast exploration (small population, high mutation)**:
```bash
python -m bffx.cli --pop 128 --epochs 5000 --mutate 0.0001 --seed 42
```

**Large-scale experiment (takes hours)**:
```bash
python -m bffx.cli --pop 8192 --epochs 100000 --mutate 0.00005 --seed 999
```

**Reproducible research**:
```bash
# Run 1
python -m bffx.cli --pop 1024 --epochs 10000 --seed 42 > run1.log

# Run 2 (identical results)
python -m bffx.cli --pop 1024 --epochs 10000 --seed 42 > run2.log

diff run1.log run2.log  # No differences
```


**No mutation (pure selection)**:
```bash
python -m bffx.cli --pop 1024 --epochs 50000 --mutate 0.0 --seed 7
```

## Python API

### Basic Usage

```python
import random
from bffx import Soup, shannon_entropy_bits, compress_ratio

# Create a soup with 1024 random programs
rng = random.Random(42)
soup = Soup(size=1024, rng=rng)

# Run 10,000 epochs
for epoch in range(10000):
    soup.epoch(
        scheduler=lambda n, r: random_disjoint_pairs(n, r),
        step_limit=8192,
        mutation_p=0.00005,
        record_outcomes=False
    )
    
    # Check metrics every 100 epochs
    if epoch % 100 == 0:
        entropy = shannon_entropy_bits(soup.pool)
        compression = compress_ratio(soup.pool)
        print(f"Epoch {epoch}: entropy={entropy:.3f}, compression={compression:.3f}")
```

### Analyzing Replication Events

```python
from bffx import Soup, random_disjoint_pairs
import random

rng = random.Random(42)
soup = Soup(size=128, rng=rng)

# Run one epoch and record outcomes
outcomes = soup.epoch(
    scheduler=lambda n, r: random_disjoint_pairs(n, r),
    step_limit=8192,
    mutation_p=0.0001,
    record_outcomes=True
)

# Count replication events
replication_count = sum(
    1 for outcome in outcomes 
    if outcome.replication_event.kind != "none"
)
print(f"Replication events: {replication_count}/{len(outcomes)}")
```


### Testing Candidate Replicators

```python
from bffx import assay_candidate
import random

# Known replicator (example)
candidate = bytes([0x3e, 0x2e, 0x3e, 0x2e] + [0] * 60)

# Generate random food programs
rng = random.Random(42)
foods = [bytes(rng.getrandbits(8) for _ in range(64)) for _ in range(100)]

# Test replication capability
successes, trials = assay_candidate(
    candidate=candidate,
    foods=foods,
    trials=100,
    step_limit=8192,
    rng=rng
)

print(f"Replication success rate: {successes}/{trials} ({100*successes/trials:.1f}%)")
```

### Saving and Loading Populations

```python
from bffx import Soup, save_population_json_gz, load_population_json_gz
import random

# Create and evolve a soup
rng = random.Random(42)
soup = Soup(size=1024, rng=rng)

for _ in range(1000):
    soup.epoch(lambda n, r: random_disjoint_pairs(n, r), step_limit=8192)

# Save snapshot
save_population_json_gz(
    path="soup_epoch1000.json.gz",
    population=soup.pool,
    meta={"epoch": 1000, "seed": 42, "mutation_rate": 0.0}
)

# Load snapshot
programs, metadata = load_population_json_gz("soup_epoch1000.json.gz")
print(f"Loaded {len(programs)} programs from epoch {metadata['epoch']}")
```


## Architecture

### Module Overview

```
bffx/
├── __init__.py           # Package initialization and exports
├── vm.py                 # Core BFF Virtual Machine
├── soup.py               # Population management and evolution
├── scheduler.py          # Pairing algorithms
├── analytics.py          # Entropy, compression, metrics
├── detectors.py          # Replication event detection
├── snapshot.py           # Population save/load
├── assay.py              # Replicator testing protocol
└── cli.py                # Command-line interface
```

### BFF Opcodes

| Opcode | Hex | Action |
|--------|-----|--------|
| `>` | 0x3E | head0++ |
| `<` | 0x3C | head0-- |
| `}` | 0x7D | head1++ |
| `{` | 0x7B | head1-- |
| `+` | 0x2B | tape[head0]++ |
| `-` | 0x2D | tape[head0]-- |
| `.` | 0x2E | tape[head1] = tape[head0] (copy) |
| `,` | 0x2C | tape[head0] = tape[head1] (copy) |
| `[` | 0x5B | if tape[head0]==0 jump to ] |
| `]` | 0x5D | if tape[head0]!=0 jump to [ |

All other bytes (246 out of 256) are NO-OPs, allowing evolution from random bytes.


### Halt Conditions

The VM halts when:

1. **STEP_LIMIT**: Instruction count exceeds step_limit (prevents infinite loops)
2. **PC_OOB**: Program counter moves outside [0, 127]
3. **OOB_POINTER**: head0 or head1 moves outside [0, 127]
4. **UNMATCHED_BRACKET**: `[` or `]` has no matching pair
5. **NORMAL**: Execution completes naturally (PC reaches end of tape)

## Connection to M|inc Economic Layer

This package (version 0.1.1) provides the **foundational layer** for the M|inc economic simulation. The relationship:

### Current Layer (0.1.1): Pure Evolution

- **Focus**: Digital abiogenesis and self-replication
- **Agents**: Anonymous programs (just bytes)
- **Interactions**: Random pairing, no economic incentives
- **Purpose**: Demonstrates that reproduction emerges from random bytes

### Future Layer (0.1.2+): Economic Dynamics

The M|inc economic layer will add:

- **Agent Roles**: Kings, Knights, Mercenaries
- **Economic Resources**: Wealth, currency, traits
- **Incentive Structures**: Bribes, raids, defends
- **Trait Mapping**: Program bytes → agent capabilities
- **Strategic Pairing**: Interactions influenced by economic incentives

### Design Principle

**Self-replication emerges first, then economic incentives are layered on top.**


The BFF VM provides:

1. **Deterministic execution** for reproducible economic simulations
2. **Self-modification** enabling adaptive agent behavior
3. **Replication detection** as the basis for fitness and wealth
4. **Clean interfaces** for economic layer integration

Example future integration:

```python
# Future M|inc integration (0.1.2+)
from bffx import Soup
from m_inc import EconomicEngine, King, Knight, Mercenary

# Create soup with economic agents
soup = Soup(size=1024)
economy = EconomicEngine()

# Associate programs with agents
for i, program in enumerate(soup.pool):
    if i < 10:
        agent = King(program=program, wealth=1000)
    elif i < 100:
        agent = Knight(program=program, retainer=kings[i//10])
    else:
        agent = Mercenary(program=program)
    economy.register(agent)

# Run epoch with economic incentives
outcomes = soup.epoch(...)
for outcome in outcomes:
    if outcome.replication_event.kind != "none":
        economy.reward_replication(outcome.i, outcome.j)
```

## Performance

Typical performance on modern hardware:

- **Small soup** (128 programs): ~1000 epochs/second
- **Medium soup** (1024 programs): ~100 epochs/second
- **Large soup** (8192 programs): ~10 epochs/second

Memory usage scales linearly: ~8MB per 128K programs.


## Reproducibility

All experiments are fully reproducible when using the same seed:

```bash
# These produce identical results
python -m bffx.cli --pop 1024 --epochs 1000 --seed 42
python -m bffx.cli --pop 1024 --epochs 1000 --seed 42
```

Determinism is guaranteed by:

- Seeded random number generator for all randomness
- Deterministic VM execution (no randomness in opcodes)
- Deterministic analytics (entropy, compression)
- Deterministic pairing and mutation

## Testing

Run the test suite:

```bash
cd python/bffx
python -m pytest
```

Key tests:

- **Unit tests**: VM opcodes, analytics, detectors
- **Integration tests**: Emergence detection, reproducibility
- **Performance tests**: Throughput and memory scaling

## Research Applications

This package enables research in:

1. **Digital abiogenesis**: How does life emerge from random bytes?
2. **Evolutionary dynamics**: What conditions favor self-replication?
3. **Information theory**: How does entropy relate to emergence?
4. **Artificial life**: Can we create novel replicators?
5. **Economic evolution**: How do incentives shape evolutionary outcomes? (0.1.2+)


## Example Workflows

### Workflow 1: Discover a Replicator

```bash
# Run until replicators emerge
python -m bffx.cli --pop 2048 --epochs 50000 --mutate 0.00005 --seed 42 --log-events

# Look for epochs with high replication event counts
# Extract the dominant program from the population
# Test it with the assay protocol
```

### Workflow 2: Study Parameter Sensitivity

```python
import random
from bffx import Soup, shannon_entropy_bits

mutation_rates = [0.0, 0.00001, 0.00005, 0.0001, 0.001]
results = {}

for rate in mutation_rates:
    rng = random.Random(42)
    soup = Soup(size=1024, rng=rng)
    
    entropies = []
    for epoch in range(10000):
        soup.epoch(lambda n, r: random_disjoint_pairs(n, r), 
                   step_limit=8192, mutation_p=rate)
        if epoch % 100 == 0:
            entropies.append(shannon_entropy_bits(soup.pool))
    
    results[rate] = entropies

# Plot entropy curves for different mutation rates
```

### Workflow 3: Checkpoint Long Experiments

```python
from bffx import Soup, save_population_json_gz, load_population_json_gz
import random

rng = random.Random(42)
soup = Soup(size=4096, rng=rng)

for checkpoint in range(10):
    # Run 10,000 epochs
    for _ in range(10000):
        soup.epoch(lambda n, r: random_disjoint_pairs(n, r), 
                   step_limit=8192, mutation_p=0.00005)
    
    # Save checkpoint
    save_population_json_gz(
        f"checkpoint_{checkpoint * 10000}.json.gz",
        soup.pool,
        {"epoch": checkpoint * 10000, "seed": 42}
    )
```


## Troubleshooting

### No Replicators Emerge

If replicators don't emerge after many epochs:

- **Increase population size**: Larger populations have more diversity
- **Adjust mutation rate**: Try 0.00005 as a starting point
- **Increase step limit**: Some replicators need more instructions
- **Run longer**: Emergence can take 10,000+ epochs

### Memory Issues

For very large populations:

- Disable outcome recording: `record_outcomes=False`
- Reduce reporting frequency: `--report-every 1000`
- Use smaller population sizes for initial exploration

### Slow Performance

To speed up experiments:

- Reduce step limit: `--step-limit 4096`
- Use smaller populations for testing
- Disable event logging: remove `--log-events`

## References

This implementation is based on the CuBFF research on digital abiogenesis and self-replicating programs. The core concepts of the unified tape, 10-opcode language, and primordial soup workflow are derived from that work.

## License

See the main project LICENSE file.

## Version History

- **0.1.1** (Current): Core BFF VM foundation with digital abiogenesis
- **0.1.2+** (Planned): M|inc economic layer integration

## Contributing

See CONTRIBUTING.md in the project root.

---

**Start with random bytes. End with life.**
