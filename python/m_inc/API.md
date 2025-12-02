# M|inc API Reference

Complete API reference for the M|inc (Mercenaries Incorporated) economic incentive system.

## Table of Contents

- [Core Modules](#core-modules)
  - [agent_registry](#agent_registry)
  - [economic_engine](#economic_engine)
  - [economics](#economics)
  - [models](#models)
  - [config](#config)
  - [cache](#cache)
  - [signals](#signals)
  - [event_aggregator](#event_aggregator)
- [Adapter Modules](#adapter-modules)
  - [trace_reader](#trace_reader)
  - [bff_bridge](#bff_bridge)
  - [output_writer](#output_writer)
- [Policy Modules](#policy-modules)
  - [policy_dsl](#policy_dsl)

---

## Core Modules

### agent_registry

Manages agent role assignment and state tracking.

#### Classes

##### `AgentRegistry`

Main registry for managing agents and their economic state.

```python
class AgentRegistry:
    def __init__(self, config: RegistryConfig)
```

**Parameters**:
- `config` (RegistryConfig): Configuration for role ratios and initialization

**Methods**:

###### `assign_roles(tape_ids: List[int]) -> None`

Assign roles to tape IDs based on configured ratios.

```python
registry.assign_roles([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
```

**Parameters**:
- `tape_ids` (List[int]): List of BFF tape IDs to assign roles to

**Raises**:
- `ValueError`: If tape_ids is empty or contains duplicates

---

###### `get_agent(agent_id: str) -> Agent`

Retrieve an agent by ID.

```python
agent = registry.get_agent("K-01")
print(f"Agent: {agent.role}, Currency: {agent.currency}")
```

**Parameters**:
- `agent_id` (str): Agent identifier (e.g., "K-01", "N-07", "M-12")

**Returns**:
- `Agent`: The agent object

**Raises**:
- `KeyError`: If agent_id not found

---

###### `get_agents_by_role(role: Union[Role, str]) -> List[Agent]`

Get all agents with a specific role.

```python
kings = registry.get_agents_by_role(Role.KING)
# or
kings = registry.get_agents_by_role("king")
```

**Parameters**:
- `role` (Role or str): Role to filter by

**Returns**:
- `List[Agent]`: List of agents with the specified role

---

###### `update_agent(agent: Agent) -> None`

Update an agent's state in the registry.

```python
agent.currency += 100
registry.update_agent(agent)
```

**Parameters**:
- `agent` (Agent): Agent object with updated state

---

###### `get_all_agents() -> List[Agent]`

Get all agents in the registry.

```python
all_agents = registry.get_all_agents()
```

**Returns**:
- `List[Agent]`: All agents

---

##### `RegistryConfig`

Configuration for agent registry.

```python
@dataclass
class RegistryConfig:
    role_ratios: Dict[str, float]
    seed: int = 1337
    initial_currency: Optional[Dict[str, Tuple[int, int]]] = None
    initial_wealth: Optional[Dict[str, Tuple[int, int]]] = None
```

**Fields**:
- `role_ratios`: Dictionary mapping role names to proportions (must sum to 1.0)
- `seed`: Random seed for deterministic role assignment
- `initial_currency`: Optional currency ranges by role
- `initial_wealth`: Optional wealth ranges by role

**Example**:
```python
config = RegistryConfig(
    role_ratios={"king": 0.1, "knight": 0.2, "mercenary": 0.7},
    seed=42
)
```

---

### economic_engine

Processes economic ticks and interactions.

#### Classes

##### `EconomicEngine`

Main engine for processing M|inc economic logic.

```python
class EconomicEngine:
    def __init__(self, registry: AgentRegistry, config: EconomicConfig)
```

**Parameters**:
- `registry` (AgentRegistry): Agent registry instance
- `config` (EconomicConfig): Economic parameters

**Methods**:

###### `process_tick(tick_num: int) -> TickResult`

Process a complete economic tick.

```python
result = engine.process_tick(1)
print(f"Tick {result.tick_num}: {len(result.events)} events")
```

**Parameters**:
- `tick_num` (int): Current tick number

**Returns**:
- `TickResult`: Complete tick results including events, metrics, and agent snapshots

**Tick Sequence**:
1. Soup drip (trait emergence)
2. Trade operations
3. Retainer payments
4. Raid/bribe/defend interactions
5. Metrics computation
6. Agent state snapshots

---

##### `EconomicConfig`

Configuration for economic parameters.

```python
@dataclass
class EconomicConfig:
    currency_to_wealth_ratio: Tuple[int, int]
    bribe_leakage: float
    exposure_factors: Dict[str, float]
    raid_value_weights: Dict[str, float]
    defend_resolution: Dict[str, float]
    trade: Dict[str, Any]
    retainer: Dict[str, int]
    on_failed_bribe: Dict[str, float]
```

**Class Methods**:

###### `from_dict(data: Dict) -> EconomicConfig`

Create config from dictionary.

```python
config = EconomicConfig.from_dict({
    "currency_to_wealth_ratio": [100, 5],
    "bribe_leakage": 0.05,
    # ... other parameters
})
```

---

##### `TickResult`

Results from processing a single tick.

```python
@dataclass
class TickResult:
    tick_num: int
    events: List[Event]
    metrics: TickMetrics
    agent_snapshots: List[AgentSnapshot]
```

**Fields**:
- `tick_num`: Tick number
- `events`: All events that occurred
- `metrics`: Computed metrics for the tick
- `agent_snapshots`: State of all agents after tick

---

### economics

Pure calculation functions for economic mechanics.

#### Functions

##### `wealth_total(agent: Agent) -> int`

Calculate total wealth across all traits.

```python
total = wealth_total(agent)
```

**Parameters**:
- `agent` (Agent): Agent to calculate wealth for

**Returns**:
- `int`: Sum of all wealth traits

---

##### `wealth_exposed(agent: Agent, config: EconomicConfig) -> float`

Calculate exposed wealth based on role.

```python
exposed = wealth_exposed(king, config)
```

**Parameters**:
- `agent` (Agent): Agent to calculate for
- `config` (EconomicConfig): Economic configuration

**Returns**:
- `float`: Exposed wealth value

**Formula**: `wealth_total(agent) * exposure_factors[agent.role]`

---

##### `raid_value(merc: Agent, king: Agent, knights: List[Agent], config: EconomicConfig) -> float`

Calculate raid value for bribe evaluation.

```python
rv = raid_value(merc, king, knights, config)
```

**Parameters**:
- `merc` (Agent): Attacking mercenary
- `king` (Agent): Target king
- `knights` (List[Agent]): Defending knights
- `config` (EconomicConfig): Economic configuration

**Returns**:
- `float`: Computed raid value

**Formula**:
```
raid_value = max(0,
    alpha * merc.raid +
    beta * (merc.sense + merc.adapt) -
    gamma * king_defend_projection +
    delta * wealth_exposed(king)
)
```

---

##### `p_knight_win(knight: Agent, merc: Agent, config: EconomicConfig) -> float`

Calculate knight win probability in defend contest.

```python
p_win = p_knight_win(knight, merc, config)
```

**Parameters**:
- `knight` (Agent): Defending knight
- `merc` (Agent): Attacking mercenary
- `config` (EconomicConfig): Economic configuration

**Returns**:
- `float`: Win probability (0.0 to 1.0)

**Formula**:
```
trait_delta = (knight.defend + knight.sense + knight.adapt) -
              (merc.raid + merc.sense + merc.adapt)
p_win = clamp(
    base_winrate + sigmoid(trait_weight * trait_delta) - 0.5,
    clamp_min,
    clamp_max
)
```

---

##### `resolve_bribe(king: Agent, merc: Agent, knights: List[Agent], config: EconomicConfig) -> BribeOutcome`

Resolve bribe attempt.

```python
outcome = resolve_bribe(king, merc, knights, config)
if outcome.accepted:
    print(f"Bribe accepted: {outcome.amount}")
```

**Parameters**:
- `king` (Agent): King offering bribe
- `merc` (Agent): Mercenary target
- `knights` (List[Agent]): Available defenders
- `config` (EconomicConfig): Economic configuration

**Returns**:
- `BribeOutcome`: Outcome with transfers and leakage

**Logic**:
- Bribe accepted if: `threshold >= raid_value AND king.currency >= threshold`
- On success: Transfer currency, apply wealth leakage
- On failure: Proceed to defend contest

---

##### `resolve_defend(knight: Agent, merc: Agent, config: EconomicConfig) -> DefendOutcome`

Resolve defend contest.

```python
outcome = resolve_defend(knight, merc, config)
print(f"Winner: {outcome.winner}")
```

**Parameters**:
- `knight` (Agent): Defending knight
- `merc` (Agent): Attacking mercenary
- `config` (EconomicConfig): Economic configuration

**Returns**:
- `DefendOutcome`: Outcome with winner and transfers

**Logic**:
- Calculate `p_win = p_knight_win(knight, merc, config)`
- Knight wins if: `p_win > 0.5 OR (p_win == 0.5 AND knight.id < merc.id)`
- Apply appropriate transfers based on winner

---

##### `sigmoid(x: float) -> float`

Sigmoid activation function.

```python
y = sigmoid(0.5)  # Returns ~0.622
```

**Parameters**:
- `x` (float): Input value

**Returns**:
- `float`: Sigmoid output (0.0 to 1.0)

**Formula**: `1 / (1 + exp(-x))`

---

##### `clamp(value: float, min_val: float, max_val: float) -> float`

Clamp value to range.

```python
clamped = clamp(0.97, 0.05, 0.95)  # Returns 0.95
```

**Parameters**:
- `value` (float): Value to clamp
- `min_val` (float): Minimum bound
- `max_val` (float): Maximum bound

**Returns**:
- `float`: Clamped value

---

### models

Core data models and types.

#### Classes

##### `Agent`

Represents an economic agent.

```python
@dataclass
class Agent:
    id: str
    tape_id: int
    role: Role
    currency: int
    wealth: WealthTraits
    employer: Optional[str] = None
    retainer_fee: int = 0
    bribe_threshold: int = 0
    alive: bool = True
```

**Fields**:
- `id`: Unique identifier (e.g., "K-01", "N-07", "M-12")
- `tape_id`: Associated BFF tape ID
- `role`: Agent role (KING, KNIGHT, MERCENARY)
- `currency`: Fungible currency balance
- `wealth`: Seven-dimensional wealth traits
- `employer`: Employer ID (for Knights only)
- `retainer_fee`: Retainer payment amount (for Knights)
- `bribe_threshold`: Bribe offer amount (for Kings)
- `alive`: Whether agent is active

**Example**:
```python
agent = Agent(
    id="K-01",
    tape_id=0,
    role=Role.KING,
    currency=5000,
    wealth=WealthTraits(10, 12, 20, 5, 15, 8, 7)
)
```

---

##### `WealthTraits`

Seven-dimensional wealth representation.

```python
@dataclass
class WealthTraits:
    compute: int
    copy: int
    defend: int
    raid: int
    trade: int
    sense: int
    adapt: int
```

**Methods**:

###### `total() -> int`

Sum of all traits.

```python
total = wealth.total()
```

---

###### `scale(factor: float) -> None`

Scale all traits by factor.

```python
wealth.scale(0.95)  # Reduce by 5%
```

**Parameters**:
- `factor` (float): Scaling factor

---

###### `to_dict() -> Dict[str, int]`

Convert to dictionary.

```python
d = wealth.to_dict()
# {"compute": 10, "copy": 12, ...}
```

---

##### `Event`

Records an economic interaction.

```python
@dataclass
class Event:
    tick: int
    type: EventType
    king: Optional[str] = None
    knight: Optional[str] = None
    merc: Optional[str] = None
    amount: Optional[int] = None
    stake: Optional[int] = None
    p_knight: Optional[float] = None
    notes: Optional[str] = None
```

**Fields**:
- `tick`: Tick number when event occurred
- `type`: Event type (see EventType enum)
- `king`: King agent ID (if applicable)
- `knight`: Knight agent ID (if applicable)
- `merc`: Mercenary agent ID (if applicable)
- `amount`: Currency amount transferred
- `stake`: Stake amount in contest
- `p_knight`: Knight win probability (for contests)
- `notes`: Additional information

---

##### `EventType`

Enumeration of event types.

```python
class EventType(Enum):
    TRAIT_DRIP = "trait_drip"
    TRADE = "trade"
    RETAINER = "retainer"
    BRIBE_ACCEPT = "bribe_accept"
    BRIBE_INSUFFICIENT = "bribe_insufficient_funds"
    DEFEND_WIN = "defend_win"
    DEFEND_LOSS = "defend_loss"
    UNOPPOSED_RAID = "unopposed_raid"
```

---

##### `Role`

Enumeration of agent roles.

```python
class Role(Enum):
    KING = "king"
    KNIGHT = "knight"
    MERCENARY = "mercenary"
```

---

##### `TickMetrics`

Metrics computed for a tick.

```python
@dataclass
class TickMetrics:
    entropy: float
    compression_ratio: float
    copy_score_mean: float
    wealth_total: int
    currency_total: int
    bribes_paid: int
    bribes_accepted: int
    raids_attempted: int
    raids_won_by_merc: int
    raids_won_by_knight: int
```

---

### config

Configuration loading and management.

#### Classes

##### `ConfigLoader`

Loads and validates YAML configuration.

```python
class ConfigLoader:
    @staticmethod
    def load(path: Union[str, Path]) -> Config
```

**Methods**:

###### `load(path: Union[str, Path]) -> Config`

Load configuration from YAML file.

```python
config = ConfigLoader.load("config/minc_default.yaml")
```

**Parameters**:
- `path`: Path to YAML configuration file

**Returns**:
- `Config`: Loaded and validated configuration

**Raises**:
- `FileNotFoundError`: If config file doesn't exist
- `ConfigurationError`: If config is invalid

---

###### `validate(config: Dict) -> List[str]`

Validate configuration dictionary.

```python
errors = ConfigLoader.validate(config_dict)
if errors:
    print("Validation errors:", errors)
```

**Parameters**:
- `config` (Dict): Configuration dictionary

**Returns**:
- `List[str]`: List of validation errors (empty if valid)

---

##### `Config`

Complete configuration object.

```python
@dataclass
class Config:
    version: str
    seed: int
    roles: RolesConfig
    economic: Dict
    refractory: Dict
    cache: CacheConfig
    output: OutputConfig
    trait_emergence: Dict
```

---

### cache

Caching and memoization for performance.

#### Classes

##### `CacheLayer`

Memoizes deterministic economic outcomes.

```python
class CacheLayer:
    def __init__(self, config: CacheConfig)
```

**Parameters**:
- `config` (CacheConfig): Cache configuration

**Methods**:

###### `get_or_compute(state: CanonicalState, compute_fn: Callable) -> Any`

Get cached result or compute and cache.

```python
result = cache.get_or_compute(state, lambda: expensive_computation())
```

**Parameters**:
- `state` (CanonicalState): Canonical state representation
- `compute_fn` (Callable): Function to compute result if not cached

**Returns**:
- Result from cache or computation

---

###### `invalidate(reason: str) -> None`

Invalidate all cache entries.

```python
cache.invalidate("config_changed")
```

**Parameters**:
- `reason` (str): Reason for invalidation (for logging)

---

###### `get_stats() -> CacheStats`

Get cache statistics.

```python
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate:.2%}")
```

**Returns**:
- `CacheStats`: Statistics including hits, misses, size

---

##### `CacheConfig`

Configuration for cache layer.

```python
@dataclass
class CacheConfig:
    enabled: bool = True
    max_size: int = 10000
    witness_sample_rate: float = 0.05
    ttl: Optional[int] = None
```

---

### signals

Event channel management with refractory periods.

#### Classes

##### `SignalProcessor`

Manages event channels and refractory periods.

```python
class SignalProcessor:
    def __init__(self, config: SignalConfig)
```

**Parameters**:
- `config` (SignalConfig): Signal configuration

**Methods**:

###### `process_events(events: List[Event]) -> List[Signal]`

Process events and route to channels.

```python
signals = processor.process_events(events)
```

**Parameters**:
- `events` (List[Event]): Events to process

**Returns**:
- `List[Signal]`: Processed signals

---

###### `update_refractory(tick_num: int) -> None`

Update refractory state for current tick.

```python
processor.update_refractory(tick_num)
```

**Parameters**:
- `tick_num` (int): Current tick number

---

###### `is_channel_active(channel: Channel) -> bool`

Check if channel is active (not in refractory).

```python
if processor.is_channel_active(Channel.RAID):
    # Process raid
    pass
```

**Parameters**:
- `channel` (Channel): Channel to check

**Returns**:
- `bool`: True if channel is active

---

### event_aggregator

Aggregates events into tick summaries.

#### Classes

##### `EventAggregator`

Collects and summarizes events.

```python
class EventAggregator:
    def __init__(self)
```

**Methods**:

###### `add_event(event: Event) -> None`

Add event to aggregator.

```python
aggregator.add_event(event)
```

**Parameters**:
- `event` (Event): Event to add

---

###### `get_tick_summary(tick_num: int) -> TickSummary`

Get summary for a tick.

```python
summary = aggregator.get_tick_summary(1)
```

**Parameters**:
- `tick_num` (int): Tick number

**Returns**:
- `TickSummary`: Aggregated summary

---

###### `reset() -> None`

Reset aggregator state.

```python
aggregator.reset()
```

---

## Adapter Modules

### trace_reader

Reads BFF trace data.

#### Classes

##### `TraceReader`

Reads and parses BFF trace files.

```python
class TraceReader:
    def __init__(self, source: Union[str, Path, IO])
```

**Parameters**:
- `source`: File path or stream to read from

**Methods**:

###### `read_epoch() -> EpochData`

Read next epoch from trace.

```python
epoch = reader.read_epoch()
print(f"Epoch {epoch.epoch_num}: {len(epoch.tapes)} tapes")
```

**Returns**:
- `EpochData`: Epoch data including tapes and interactions

**Raises**:
- `EOFError`: If no more epochs available

---

###### `get_tape_by_id(tape_id: int) -> bytearray`

Get specific tape by ID.

```python
tape = reader.get_tape_by_id(42)
```

**Parameters**:
- `tape_id` (int): Tape ID to retrieve

**Returns**:
- `bytearray`: Tape contents (64 bytes)

**Raises**:
- `KeyError`: If tape_id not found

---

###### `get_population_snapshot() -> List[bytearray]`

Get all tapes in current epoch.

```python
all_tapes = reader.get_population_snapshot()
```

**Returns**:
- `List[bytearray]`: All tape contents

---

##### `EpochData`

Data for a single epoch.

```python
@dataclass
class EpochData:
    epoch_num: int
    tapes: Dict[int, bytearray]
    interactions: List[Tuple[int, int]]
    metrics: Dict[str, float]
```

---

### bff_bridge

Bridges BFF binary format to M|inc.

#### Classes

##### `BFFBridge`

Converts BFF binary traces to M|inc format.

```python
class BFFBridge:
    def __init__(self, trace_file: Union[str, Path])
```

**Parameters**:
- `trace_file`: Path to BFF binary trace

**Methods**:

###### `read_all_states_as_epochs() -> Iterator[EpochData]`

Read all states as epochs.

```python
with BFFBridge("trace.bin") as bridge:
    for epoch in bridge.read_all_states_as_epochs():
        # Process epoch
        pass
```

**Yields**:
- `EpochData`: Each state as an epoch

---

#### Functions

##### `stream_bff_to_minc(trace_file: Union[str, Path]) -> Iterator[EpochData]`

Stream BFF trace data.

```python
for epoch in stream_bff_to_minc("trace.bin"):
    result = engine.process_tick(epoch.epoch_num)
```

**Parameters**:
- `trace_file`: Path to BFF binary trace

**Yields**:
- `EpochData`: Epochs from trace

---

### output_writer

Writes M|inc results to files.

#### Classes

##### `OutputWriter`

Serializes M|inc data to JSON and CSV.

```python
class OutputWriter:
    def __init__(self, output_dir: Path, config: OutputConfig)
```

**Parameters**:
- `output_dir` (Path): Directory for output files
- `config` (OutputConfig): Output configuration

**Methods**:

###### `write_tick_json(result: TickResult) -> None`

Write tick snapshot to JSON.

```python
writer.write_tick_json(tick_result)
```

**Parameters**:
- `result` (TickResult): Tick result to write

---

###### `write_event_csv(events: List[Event]) -> None`

Write events to CSV log.

```python
writer.write_event_csv(events)
```

**Parameters**:
- `events` (List[Event]): Events to write

---

###### `write_final_agents_csv(agents: List[Agent]) -> None`

Write final agent states to CSV.

```python
writer.write_final_agents_csv(agents)
```

**Parameters**:
- `agents` (List[Agent]): Agents to write

---

###### `validate_schema(data: Dict, schema_name: str) -> bool`

Validate data against schema.

```python
is_valid = writer.validate_schema(data, "tick_result")
```

**Parameters**:
- `data` (Dict): Data to validate
- `schema_name` (str): Schema name

**Returns**:
- `bool`: True if valid

---

##### `OutputConfig`

Configuration for output writer.

```python
@dataclass
class OutputConfig:
    json_ticks: bool = True
    csv_events: bool = True
    csv_final_agents: bool = True
    compress: bool = False
    pretty_print: bool = True
```

---

## Policy Modules

### policy_dsl

Compiles YAML policies to Python functions.

#### Classes

##### `PolicyCompiler`

Compiles policy definitions from YAML.

```python
class PolicyCompiler:
    def __init__(self, yaml_config: Dict)
```

**Parameters**:
- `yaml_config` (Dict): YAML configuration dictionary

**Class Methods**:

###### `from_yaml(path: Union[str, Path]) -> PolicyCompiler`

Create compiler from YAML file.

```python
compiler = PolicyCompiler.from_yaml("config/policy.yaml")
```

**Parameters**:
- `path`: Path to YAML file

**Returns**:
- `PolicyCompiler`: Compiler instance

---

**Methods**:

###### `compile() -> CompiledPolicies`

Compile policies to callables.

```python
policies = compiler.compile()
rv = policies.raid_value(merc, king, knights)
```

**Returns**:
- `CompiledPolicies`: Compiled policy functions

---

###### `validate() -> List[ValidationError]`

Validate policy syntax.

```python
errors = compiler.validate()
if errors:
    print("Policy errors:", errors)
```

**Returns**:
- `List[ValidationError]`: Validation errors

---

##### `CompiledPolicies`

Compiled policy functions.

```python
@dataclass
class CompiledPolicies:
    bribe_outcome: Callable
    raid_value: Callable
    p_knight_win: Callable
    trade_action: Callable
```

---

## Type Aliases

Common type aliases used throughout the API:

```python
AgentID = str
TapeID = int
Tick = int
Currency = int
Wealth = int
Probability = float  # 0.0 to 1.0
```

---

## Error Handling

### Exception Hierarchy

```
MIncError (base)
├── ConfigurationError
├── DataValidationError
├── CacheError
└── PolicyCompilationError
```

### Common Exceptions

#### `MIncError`

Base exception for all M|inc errors.

```python
try:
    result = engine.process_tick(1)
except MIncError as e:
    print(f"M|inc error: {e}")
```

---

#### `ConfigurationError`

Configuration validation failed.

```python
try:
    config = ConfigLoader.load("invalid.yaml")
except ConfigurationError as e:
    print(f"Config error: {e}")
```

---

#### `DataValidationError`

Data schema validation failed.

```python
try:
    writer.write_tick_json(invalid_data)
except DataValidationError as e:
    print(f"Validation error: {e}")
```

---

## Constants

### Default Values

```python
DEFAULT_SEED = 1337
DEFAULT_CACHE_SIZE = 10000
DEFAULT_WITNESS_RATE = 0.05
DEFAULT_BRIBE_LEAKAGE = 0.05
DEFAULT_BASE_WINRATE = 0.50
```

### Limits

```python
MIN_PROBABILITY = 0.05
MAX_PROBABILITY = 0.95
MIN_CURRENCY = 0
MIN_WEALTH = 0
```

---

## Version Information

```python
import m_inc

print(m_inc.__version__)  # "0.1.1"
print(m_inc.__author__)   # "M|inc Contributors"
```

---

## See Also

- [README](README.md): Main documentation
- [Examples](examples/README.md): Usage examples
- [Requirements](../../.kiro/specs/minc-integration/requirements.md): System requirements
- [Design](../../.kiro/specs/minc-integration/design.md): Architecture details
