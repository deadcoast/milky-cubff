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

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) CUDA-enabled GPU for BFF simulation

### From source

```bash
cd python/m_inc
pip install -e .
```

This installs M|inc in editable mode with core dependencies:
- pyyaml: Configuration file parsing
- pandas: Data manipulation and CSV output
- numpy: Numerical computations
- pydantic: Data validation and schemas

### With development dependencies

```bash
pip install -e ".[dev]"
```

This includes additional tools for development:
- pytest: Testing framework
- black: Code formatting
- ruff: Linting
- mypy: Type checking

### Verify installation

```bash
minc --version
python -c "import m_inc; print(m_inc.__version__)"
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

M|inc uses YAML configuration files to control all economic parameters and system behavior. See `config/minc_default.yaml` for a complete example.

### Configuration Reference

#### Roles Section

Controls agent role assignment and initialization:

```yaml
roles:
  ratios:
    king: 0.10        # 10% of agents are Kings
    knight: 0.20      # 20% of agents are Knights
    mercenary: 0.70   # 70% of agents are Mercenaries
  mutation_rate: 0.0  # Probability of role change per tick (0 = disabled)
  
  initial_currency:
    king: [5000, 7000]      # Kings start with 5000-7000 currency
    knight: [100, 300]      # Knights start with 100-300 currency
    mercenary: [0, 50]      # Mercenaries start with 0-50 currency
  
  initial_wealth:
    king: [10, 30]          # Kings start with 10-30 per trait
    knight: [5, 15]         # Knights start with 5-15 per trait
    mercenary: [0, 10]      # Mercenaries start with 0-10 per trait
```

#### Economic Section

Core economic parameters:

```yaml
economic:
  currency_to_wealth_ratio: [100, 5]  # 100 currency = 5 wealth units
  bribe_leakage: 0.05                 # 5% wealth loss on successful bribe
  
  exposure_factors:
    king: 1.0        # Kings expose 100% of wealth
    knight: 0.5      # Knights expose 50% of wealth
    mercenary: 0.4   # Mercenaries expose 40% of wealth
  
  raid_value_weights:
    alpha_raid: 1.0           # Weight for mercenary raid trait
    beta_sense_adapt: 0.25    # Weight for mercenary sense+adapt
    gamma_king_defend: 0.60   # Weight for king defense projection
    delta_king_exposed: 0.40  # Weight for king exposed wealth
  
  defend_resolution:
    base_knight_winrate: 0.50      # Base probability (50%)
    trait_advantage_weight: 0.30   # Sigmoid scaling factor
    clamp_min: 0.05                # Minimum win probability
    clamp_max: 0.95                # Maximum win probability
    stake_currency_frac: 0.10      # 10% of combined currency as stake
    bounty_wealth_frac: 0.07       # 7% of merc traits as bounty
  
  trade:
    invest_per_tick: 100      # Currency cost per trade
    created_wealth_units: 5   # Total wealth created
    distribution:
      defend: 3               # 3 units to defend trait
      trade: 2                # 2 units to trade trait
  
  retainer:
    base_fee: 50              # Base retainer payment per tick
    
  on_failed_bribe:
    king_currency_loss_frac: 0.50   # King loses 50% currency
    king_wealth_loss_frac: 0.25     # King loses 25% wealth
    merc_currency_gain_frac: 0.50   # Merc gains 50% of king's currency
    merc_wealth_gain_frac: 0.25     # Merc gains 25% of king's wealth
```

#### Refractory Section

Cooldown periods to prevent event oscillations:

```yaml
refractory:
  raid: 2      # Raid channel blocked for 2 ticks after firing
  defend: 1    # Defend channel blocked for 1 tick
  bribe: 1     # Bribe channel blocked for 1 tick
  trade: 0     # Trade has no refractory period
```

#### Cache Section

Performance optimization settings:

```yaml
cache:
  enabled: true              # Enable/disable caching
  max_size: 10000           # Maximum cache entries
  witness_sample_rate: 0.05 # Store 5% of entries for validation
  ttl: 3600                 # Time-to-live in seconds (optional)
```

#### Output Section

Control output file generation:

```yaml
output:
  json_ticks: true          # Generate per-tick JSON snapshots
  csv_events: true          # Generate CSV event log
  csv_final_agents: true    # Generate final agent state CSV
  compress: false           # Enable gzip compression
  pretty_print: true        # Pretty-print JSON (vs minified)
```

#### Trait Emergence Section

Rules for trait growth based on BFF activity:

```yaml
trait_emergence:
  enabled: true
  rules:
    - condition: "copy >= 12 AND tick % 2 == 0"
      delta: {copy: 1}
    - condition: "compute >= 15"
      delta: {compute: 1, sense: 1}
```

### Configuration Presets

M|inc includes several preset configurations:

- **minc_default.yaml**: Balanced parameters for standard experiments
- **minc_fast.yaml**: Optimized for quick experiments (caching disabled, minimal output)
- **policy_example.yaml**: Example of custom policy definitions

### Creating Custom Configurations

1. Copy a preset configuration:
   ```bash
   cp config/minc_default.yaml config/my_experiment.yaml
   ```

2. Edit parameters as needed

3. Run with custom config:
   ```bash
   minc --config config/my_experiment.yaml --trace data.json --output results/
   ```

### Configuration Validation

M|inc validates all configuration on load and reports errors:

```bash
minc --validate-config config/my_experiment.yaml
```

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

## Visualization

M|inc includes visualization tools to analyze economic dynamics through plots and charts.

### Installation

Install visualization dependencies:

```bash
pip install matplotlib seaborn
```

### Creating Visualizations

Use the visualization example script:

```bash
cd examples

# Display plots interactively
python 05_visualize_outputs.py

# Save plots to files
python 05_visualize_outputs.py --save

# Use custom output directory
python 05_visualize_outputs.py --output-dir /path/to/output --save
```

### Available Visualizations

#### Wealth Distribution Over Time

Shows how total wealth evolves for each role (Kings, Knights, Mercenaries):
- Absolute wealth by role
- Percentage distribution (stacked area)

#### Currency Flows

Visualizes currency transfers between roles:
- Currency holdings over time
- Flow totals by type (bribes, retainers, stakes)
- Final currency distribution (pie chart)

#### Event Frequency Heatmap

Displays when different event types occur throughout the simulation:
- Event counts by tick and type
- Color-coded intensity

#### Agent Trajectories

Tracks individual agent wealth paths:
- Top N agents by final wealth
- Wealth distribution statistics (mean, median, percentiles)

#### Wealth Traits Breakdown

Shows evolution of individual wealth traits:
- Stacked area chart of all traits
- Individual trait lines

### Programmatic Visualization

Create custom visualizations using the data loading functions:

```python
from pathlib import Path
import json

# Load tick data
output_dir = Path("output/")
with open(output_dir / "ticks.json", 'r') as f:
    tick_data = json.load(f)

# Extract wealth by role
for tick in tick_data:
    agents = tick['agents']
    king_wealth = sum(sum(a['wealth'].values()) 
                     for a in agents if a['role'] == 'king')
    print(f"Tick {tick['tick']}: Kings have {king_wealth} wealth")

# Load event data
import pandas as pd
events = pd.read_csv(output_dir / "events.csv")

# Analyze event patterns
event_counts = events['type'].value_counts()
print(event_counts)
```

See `examples/05_visualize_outputs.py` for complete implementation examples.

## API Documentation

### Core Classes

#### AgentRegistry

Manages agent role assignment and state tracking.

```python
from m_inc.core.agent_registry import AgentRegistry, RegistryConfig
from m_inc.core.models import Role

# Initialize registry
config = RegistryConfig(
    role_ratios={"king": 0.1, "knight": 0.2, "mercenary": 0.7},
    seed=1337
)
registry = AgentRegistry(config)

# Assign roles to tape IDs
tape_ids = list(range(100))
registry.assign_roles(tape_ids)

# Get agent by ID
agent = registry.get_agent("K-01")
print(f"Agent {agent.id}: {agent.role}, {agent.currency} currency")

# Get agents by role
kings = registry.get_agents_by_role(Role.KING)
print(f"Found {len(kings)} kings")

# Update agent state
agent.currency += 100
registry.update_agent(agent)
```

**Key Methods:**
- `assign_roles(tape_ids: List[int])`: Assign roles to tape IDs based on ratios
- `get_agent(agent_id: str) -> Agent`: Retrieve agent by ID
- `get_agents_by_role(role: Role) -> List[Agent]`: Filter agents by role
- `update_agent(agent: Agent)`: Persist agent state changes

#### EconomicEngine

Processes economic ticks and interactions.

```python
from m_inc.core.economic_engine import EconomicEngine, EconomicConfig

# Initialize engine
config = EconomicConfig.from_yaml("config/minc_default.yaml")
engine = EconomicEngine(registry, config)

# Process a single tick
result = engine.process_tick(tick_num=1)

# Access results
print(f"Tick {result.tick_num}")
print(f"Events: {len(result.events)}")
print(f"Total wealth: {result.metrics.wealth_total}")
print(f"Total currency: {result.metrics.currency_total}")

# Iterate through events
for event in result.events:
    print(f"{event.type}: {event.king} -> {event.merc}")
```

**Key Methods:**
- `process_tick(tick_num: int) -> TickResult`: Execute full tick sequence
- `_soup_drip() -> List[Event]`: Apply trait emergence rules
- `_execute_trades() -> List[Event]`: Process king trade operations
- `_pay_retainers() -> List[Event]`: Transfer retainer payments
- `_execute_interactions() -> List[Event]`: Process raids/bribes/defends

#### TraceReader

Reads BFF trace data.

```python
from m_inc.adapters.trace_reader import TraceReader

# Read from file
reader = TraceReader("testdata/bff_trace.json")

# Read epochs sequentially
epoch = reader.read_epoch()
print(f"Epoch {epoch.epoch_num}: {len(epoch.tapes)} tapes")

# Get specific tape
tape_bytes = reader.get_tape_by_id(42)
print(f"Tape 42: {len(tape_bytes)} bytes")

# Get full population snapshot
all_tapes = reader.get_population_snapshot()
```

**Key Methods:**
- `read_epoch() -> EpochData`: Read next epoch from trace
- `get_tape_by_id(tape_id: int) -> bytearray`: Retrieve specific tape
- `get_population_snapshot() -> List[bytearray]`: Get all tapes

#### OutputWriter

Writes M|inc results to files.

```python
from m_inc.adapters.output_writer import OutputWriter, OutputConfig

# Initialize writer
config = OutputConfig(
    json_ticks=True,
    csv_events=True,
    csv_final_agents=True,
    compress=False
)
writer = OutputWriter("output/", config)

# Write tick result
writer.write_tick_json(tick_result)

# Write events
writer.write_event_csv(events)

# Write final agent state
writer.write_final_agents_csv(agents)

# Validate against schema
is_valid = writer.validate_schema(data, "tick_result")
```

**Key Methods:**
- `write_tick_json(result: TickResult)`: Write tick snapshot to JSON
- `write_event_csv(events: List[Event])`: Append events to CSV log
- `write_final_agents_csv(agents: List[Agent])`: Write final state CSV
- `validate_schema(data: Dict, schema: str) -> bool`: Validate data structure

### Data Models

#### Agent

Represents an economic agent with role and attributes.

```python
from m_inc.core.models import Agent, WealthTraits, Role

agent = Agent(
    id="K-01",
    tape_id=0,
    role=Role.KING,
    currency=5000,
    wealth=WealthTraits(
        compute=10, copy=12, defend=20,
        raid=5, trade=15, sense=8, adapt=7
    ),
    bribe_threshold=500,
    alive=True
)

# Access wealth
total_wealth = agent.wealth.total()
print(f"Total wealth: {total_wealth}")

# Modify wealth
agent.wealth.defend += 5
agent.wealth.scale(0.95)  # Apply 5% reduction
```

**Fields:**
- `id: str`: Unique agent identifier (e.g., "K-01", "N-07", "M-12")
- `tape_id: int`: Associated BFF tape ID
- `role: Role`: KING, KNIGHT, or MERCENARY
- `currency: int`: Fungible currency balance
- `wealth: WealthTraits`: Seven trait values
- `employer: Optional[str]`: Employer ID (for Knights)
- `retainer_fee: int`: Retainer amount (for Knights)
- `bribe_threshold: int`: Bribe offer amount (for Kings)
- `alive: bool`: Agent status

#### WealthTraits

Seven-dimensional wealth representation.

```python
from m_inc.core.models import WealthTraits

wealth = WealthTraits(
    compute=10,
    copy=12,
    defend=20,
    raid=5,
    trade=15,
    sense=8,
    adapt=7
)

# Get total
total = wealth.total()  # 77

# Scale all traits
wealth.scale(0.9)  # Reduce by 10%

# Access individual traits
wealth.defend += 3
```

**Traits:**
- `compute`: Computational capability
- `copy`: Self-replication ability
- `defend`: Defense strength
- `raid`: Attack capability
- `trade`: Economic productivity
- `sense`: Environmental awareness
- `adapt`: Adaptability

#### Event

Records an economic interaction.

```python
from m_inc.core.models import Event, EventType

event = Event(
    tick=1,
    type=EventType.BRIBE_ACCEPT,
    king="K-01",
    merc="M-12",
    amount=350,
    notes="success"
)
```

**Event Types:**
- `TRAIT_DRIP`: Trait emergence from BFF activity
- `TRADE`: King trade operation
- `RETAINER`: Knight retainer payment
- `BRIBE_ACCEPT`: Successful bribe
- `BRIBE_INSUFFICIENT`: Failed bribe (insufficient funds)
- `DEFEND_WIN`: Knight wins defend contest
- `DEFEND_LOSS`: Mercenary wins defend contest
- `UNOPPOSED_RAID`: Raid with no defenders

### Economic Functions

Pure calculation functions for economic mechanics.

```python
from m_inc.core.economics import (
    wealth_total,
    wealth_exposed,
    raid_value,
    p_knight_win,
    resolve_bribe,
    resolve_defend,
    sigmoid,
    clamp
)

# Calculate exposed wealth
exposed = wealth_exposed(king, config)

# Calculate raid value
rv = raid_value(merc, king, knights, config)

# Calculate knight win probability
p_win = p_knight_win(knight, merc, config)

# Resolve bribe
outcome = resolve_bribe(king, merc, knights, config)
if outcome.accepted:
    print(f"Bribe accepted: {outcome.amount} currency")

# Resolve defend contest
defend_outcome = resolve_defend(knight, merc, config)
print(f"Winner: {defend_outcome.winner}")
```

### Policy DSL

Compile custom economic policies from YAML.

```python
from m_inc.policies.policy_dsl import PolicyCompiler

# Load and compile policies
compiler = PolicyCompiler.from_yaml("config/policy_example.yaml")
policies = compiler.compile()

# Use compiled policies
rv = policies.raid_value(merc, king, knights)
outcome = policies.bribe_outcome(king, merc, knights)
```

### Cache Layer

Memoize deterministic outcomes for performance.

```python
from m_inc.core.cache import CacheLayer, CacheConfig

# Initialize cache
config = CacheConfig(enabled=True, max_size=10000)
cache = CacheLayer(config)

# Use cache
def expensive_computation(state):
    # ... complex calculation ...
    return result

result = cache.get_or_compute(canonical_state, expensive_computation)

# Get cache statistics
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")
print(f"Size: {stats.size}/{stats.max_size}")

# Invalidate cache
cache.invalidate("config_changed")
```

## Development

### Running tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_economic_engine.py

# Run with coverage
pytest --cov=m_inc --cov-report=html

# Run verbose
pytest -v
```

### Code formatting

```bash
# Format code
black .

# Check formatting
black --check .

# Lint code
ruff check .

# Fix linting issues
ruff check --fix .
```

### Type checking

```bash
# Check types
mypy m_inc

# Check specific module
mypy m_inc/core/economic_engine.py
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
