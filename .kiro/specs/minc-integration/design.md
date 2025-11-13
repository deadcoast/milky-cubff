# Design Document

## Overview

The M|inc integration design follows a **layered adapter architecture** that sits between the existing BFF simulation and new economic analysis outputs. The design prioritizes non-invasiveness, determinism, and modularity. All M|inc functionality is implemented as a separate Python package (`python/m_inc/`) that consumes BFF soup traces and produces economic telemetry without modifying core simulation code.

### Design Principles

1. **Separation of Concerns**: BFF simulation remains pure; M|inc adapter is a separate layer
2. **Read-Only Consumption**: M|inc reads BFF traces without modifying them
3. **Deterministic Processing**: All economic calculations are pure functions
4. **Configurable Behavior**: YAML-driven configuration for all parameters
5. **Extensible Architecture**: Plugin-style design for future economic models

## Architecture

### High-Level Data Flow

```
┌────────────────────────────────────────────────────────────┐
│                    Existing BFF System                     │
│   ┌──────────┐    ┌──────────┐    ┌──────────────────┐     │
│   │ main.cc  │--->│ Soup VM  │--->│ save_bff_trace.py│     │
│   │(C++/CUDA)│    │ (*.cu)   │    │ (trace output)   │     │
│   └──────────┘    └──────────┘    └──────────┬───────┘     │
└──────────────────────────────────────────────┼─────────────┘
                                               │
                                               v
┌────────────────────────────────────────────────────────────┐
│                    M|inc Adapter Layer                     │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐   │
│  │ Trace Reader │--->│Agent Registry│--->│ Economic    │   │
│  │              │    │ & Mapper     │    │ Engine      │   │
│  └──────────────┘    └──────────────┘    └──────┬──────┘   │
│                                                 │          │
│  ┌──────────────┐    ┌──────────────┐           │          │
│  │ Cache Layer  │<---│ Policy DSL   │<----------+          │
│  │              │    │ Compiler     │                      │
│  └──────────────┘    └──────────────┘                      │
│                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Signal       │--->│ Event        │--->│ Output       │  │
│  │ Processor    │    │ Aggregator   │    │ Writer       │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
└─────────────────────────────────────────────────┼──────────┘
                                                  │
                                                  v
                                    ┌──────────────────────────┐
                                    │  JSON Ticks, CSV Events, │
                                    │  Final Agent State       │
                                    └──────────────────────────┘
```

### Component Architecture

#### 1. Trace Reader (`m_inc/trace_reader.py`)

**Purpose**: Bridge between BFF soup output and M|inc processing

**Responsibilities**:
- Parse BFF trace files or live soup snapshots
- Extract tape IDs, byte contents, and execution metadata
- Normalize data into M|inc-compatible format
- Handle both historical traces and streaming data

**Key Classes**:
```python
class TraceReader:
    def __init__(self, source: Union[Path, Stream])
    def read_epoch(self) -> EpochData
    def get_tape_by_id(self, tape_id: int) -> bytearray
    def get_population_snapshot(self) -> List[bytearray]
```

**Data Structures**:
```python
@dataclass
class EpochData:
    epoch_num: int
    tapes: Dict[int, bytearray]  # tape_id -> 64-byte program
    interactions: List[Tuple[int, int]]  # (tape_a_id, tape_b_id)
    metrics: Dict[str, float]  # entropy, compression, etc.
```

#### 2. Agent Registry (`m_inc/agent_registry.py`)

**Purpose**: Map BFF tapes to M|inc agents with roles and economic state

**Responsibilities**:
- Assign roles (King, Knight, Mercenary) to tape IDs
- Initialize and maintain agent economic attributes
- Handle role mutations (optional)
- Provide agent lookup and filtering

**Key Classes**:
```python
class AgentRegistry:
    def __init__(self, config: RegistryConfig)
    def assign_roles(self, tape_ids: List[int]) -> None
    def get_agent(self, tape_id: int) -> Agent
    def get_agents_by_role(self, role: Role) -> List[Agent]
    def update_agent(self, agent: Agent) -> None
    
@dataclass
class Agent:
    id: str  # e.g., "K-01", "N-07", "M-12"
    tape_id: int
    role: Role  # King, Knight, Mercenary
    currency: int
    wealth: WealthTraits
    employer: Optional[str]  # for Knights
    retainer_fee: int  # for Knights
    bribe_threshold: int  # for Kings
    alive: bool
```

**Data Structures**:
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
    
    def total(self) -> int:
        return sum(astuple(self))
    
    def scale(self, factor: float) -> None:
        for field in fields(self):
            setattr(self, field.name, int(getattr(self, field.name) * factor))

class Role(Enum):
    KING = "king"
    KNIGHT = "knight"
    MERCENARY = "mercenary"
```

#### 3. Economic Engine (`m_inc/economic_engine.py`)

**Purpose**: Execute M|inc tick logic and economic interactions

**Responsibilities**:
- Orchestrate tick sequence (drip → trade → retainer → interactions)
- Compute raid values, bribe outcomes, defend probabilities
- Apply wealth/currency transfers
- Enforce invariants (non-negative values, deterministic resolution)
- Generate event records

**Key Classes**:
```python
class EconomicEngine:
    def __init__(self, registry: AgentRegistry, config: EconomicConfig)
    def process_tick(self, tick_num: int) -> TickResult
    def _soup_drip(self) -> List[Event]
    def _execute_trades(self) -> List[Event]
    def _pay_retainers(self) -> List[Event]
    def _execute_interactions(self) -> List[Event]
    def _compute_metrics(self) -> TickMetrics

@dataclass
class TickResult:
    tick_num: int
    events: List[Event]
    metrics: TickMetrics
    agent_snapshots: List[AgentSnapshot]
```

**Core Economic Functions**:
```python
def raid_value(merc: Agent, king: Agent, knights: List[Agent], 
               config: EconomicConfig) -> float:
    """Compute deterministic raid value for bribe evaluation"""
    kd = king_defend_projection(king, knights, attackers=1, config)
    return max(0.0,
        config.alpha_raid * merc.wealth.raid +
        config.beta_sense_adapt * (merc.wealth.sense + merc.wealth.adapt) -
        config.gamma_king_defend * kd +
        config.delta_king_exposed * wealth_exposed(king, config)
    )

def p_knight_win(knight: Agent, merc: Agent, config: EconomicConfig) -> float:
    """Compute deterministic knight win probability"""
    base = config.base_knight_winrate
    trait_delta = (
        (knight.wealth.defend + knight.wealth.sense + knight.wealth.adapt) -
        (merc.wealth.raid + merc.wealth.sense + merc.wealth.adapt)
    )
    raw = base + (sigmoid(config.trait_weight * trait_delta) - 0.5)
    return clamp(raw, config.clamp_min, config.clamp_max)

def resolve_bribe(king: Agent, merc: Agent, knights: List[Agent],
                  config: EconomicConfig) -> BribeOutcome:
    """Deterministic bribe resolution"""
    rv = raid_value(merc, king, knights, config)
    threshold = king.bribe_threshold
    
    if threshold >= rv and king.currency >= threshold:
        return BribeOutcome(
            accepted=True,
            amount=threshold,
            king_currency_delta=-threshold,
            merc_currency_delta=threshold,
            king_wealth_leakage=config.bribe_leakage
        )
    elif threshold >= rv:
        return BribeOutcome(accepted=False, reason="insufficient_funds")
    else:
        return BribeOutcome(accepted=False, reason="threshold_too_low")
```

#### 4. Policy DSL Compiler (`m_inc/policy_dsl.py`)

**Purpose**: Compile YAML policy definitions into executable Python functions

**Responsibilities**:
- Parse YAML policy expressions
- Generate pure Python callables
- Validate policy syntax and semantics
- Support hot-swapping policies without code changes

**Key Classes**:
```python
class PolicyCompiler:
    def __init__(self, yaml_config: Dict)
    def compile(self) -> CompiledPolicies
    def validate(self) -> List[ValidationError]

@dataclass
class CompiledPolicies:
    bribe_outcome: Callable[[Agent, Agent, List[Agent]], BribeOutcome]
    raid_value: Callable[[Agent, Agent, List[Agent]], float]
    p_knight_win: Callable[[Agent, Agent], float]
    trade_action: Callable[[Agent, int], TradeOutcome]
```

**YAML Policy Example**:
```yaml
policies:
  raid_value:
    formula: "alpha*merc.raid + beta*(merc.sense+merc.adapt) - gamma*king_defend + delta*king_exposed"
    params:
      alpha: 1.0
      beta: 0.25
      gamma: 0.60
      delta: 0.40
  
  bribe_outcome:
    condition: "threshold >= raid_value AND king.currency >= threshold"
    on_success:
      king_currency: "-threshold"
      merc_currency: "+threshold"
      king_wealth_leakage: 0.05
```

#### 5. Cache Layer (`m_inc/cache.py`)

**Purpose**: Memoize deterministic economic outcomes for performance

**Responsibilities**:
- Compute canonical state representations
- Generate cache keys from state + config hash
- Store and retrieve cached outcomes
- Maintain witness samples for validation
- Invalidate cache on config changes

**Key Classes**:
```python
class CacheLayer:
    def __init__(self, config: CacheConfig)
    def get_or_compute(self, state: CanonicalState, 
                       compute_fn: Callable) -> EncounterOutcome
    def invalidate(self, reason: str) -> None
    def get_stats(self) -> CacheStats

@dataclass
class CanonicalState:
    agents: List[Dict]  # sorted by ID
    roles: Dict[str, str]
    params_hash: str
    
    def hash(self) -> str:
        return hashlib.sha256(
            json.dumps(self, sort_keys=True).encode()
        ).hexdigest()[:16]
```

**Caching Strategy**:
- Cache key = `hash(canonical_state) + config_hash + adapter_version`
- Store witness samples (5% of cache writes) for validation
- LRU eviction policy with configurable max size
- Periodic cache validation against witness samples

#### 6. Signal Processor (`m_inc/signals.py`)

**Purpose**: Manage event channels with priorities and refractory periods

**Responsibilities**:
- Route events to appropriate channels (raid, defend, bribe, trade)
- Enforce refractory periods to prevent oscillations
- Queue and coalesce events during refractory windows
- Apply priority-based scheduling

**Key Classes**:
```python
class SignalProcessor:
    def __init__(self, config: SignalConfig)
    def process_events(self, events: List[Event]) -> List[Signal]
    def update_refractory(self, tick_num: int) -> None
    def is_channel_active(self, channel: Channel) -> bool

@dataclass
class Signal:
    channel: Channel
    priority: int
    payload: Dict
    timestamp: int
    refractory_until: Optional[int]

class Channel(Enum):
    RAID = "raid"
    DEFEND = "defend"
    BRIBE = "bribe"
    TRADE = "trade"
    RETAINER = "retainer"
```

**Refractory Logic**:
```python
def update_signals(events: List[Event], refractory_cfg: Dict) -> List[Signal]:
    """Apply refractory periods and priority scheduling"""
    signals = []
    for event in events:
        channel = event.channel
        if is_in_refractory(channel):
            queue_event(event)
        else:
            signal = create_signal(event)
            signal.refractory_until = current_tick + refractory_cfg[channel]
            signals.append(signal)
    return sorted(signals, key=lambda s: s.priority, reverse=True)
```

#### 7. Event Aggregator (`m_inc/event_aggregator.py`)

**Purpose**: Collect and summarize micro-events into tick-level summaries

**Responsibilities**:
- Aggregate events by type and tick
- Compute event statistics (counts, totals, distributions)
- Generate tick summary objects
- Prepare data for output writers

**Key Classes**:
```python
class EventAggregator:
    def __init__(self)
    def add_event(self, event: Event) -> None
    def get_tick_summary(self, tick_num: int) -> TickSummary

@dataclass
class TickSummary:
    tick: int
    event_counts: Dict[str, int]
    currency_flows: Dict[str, int]
    wealth_changes: Dict[str, Dict[str, int]]
    agent_states: List[AgentSnapshot]
```

#### 8. Output Writer (`m_inc/output_writer.py`)

**Purpose**: Serialize M|inc data to JSON and CSV formats

**Responsibilities**:
- Write per-tick JSON snapshots
- Write CSV event logs
- Write final agent state CSV
- Validate outputs against schemas
- Handle file I/O and compression

**Key Classes**:
```python
class OutputWriter:
    def __init__(self, output_dir: Path, config: OutputConfig)
    def write_tick_json(self, tick_result: TickResult) -> None
    def write_event_csv(self, events: List[Event]) -> None
    def write_final_agents_csv(self, agents: List[Agent]) -> None
    def validate_schema(self, data: Dict, schema_name: str) -> bool
```

**Output Schemas**:

JSON Tick Schema:
```json
{
  "tick": 1,
  "metrics": {
    "entropy": 5.91,
    "compression_ratio": 2.70,
    "copy_score_mean": 0.64,
    "wealth_total": 399,
    "currency_total": 12187,
    "bribes_paid": 1,
    "bribes_accepted": 0,
    "raids_attempted": 2,
    "raids_won_by_merc": 0,
    "raids_won_by_knight": 1
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
  ],
  "meta": {
    "version": "0.1.1",
    "seed": 1337,
    "config_hash": "a3f2b9c1",
    "timestamp": "2025-01-27T10:30:00Z"
  }
}
```

CSV Event Schema:
```csv
tick,type,king,knight,merc,amount,stake,p_knight,notes
1,bribe_accept,K-01,,M-12,350,,,success
1,defend_win,K-01,N-07,M-19,,250,0.52,
2,trade,K-02,,,100,,,+5 wealth
```

## Data Models

### Core Data Structures

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

class EventType(Enum):
    TRAIT_DRIP = "trait_drip"
    TRADE = "trade"
    RETAINER = "retainer"
    BRIBE_ACCEPT = "bribe_accept"
    BRIBE_INSUFFICIENT = "bribe_insufficient_funds"
    DEFEND_WIN = "defend_win"
    DEFEND_LOSS = "defend_loss"
    UNOPPOSED_RAID = "unopposed_raid"

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

## Error Handling

### Error Categories

1. **Configuration Errors**: Invalid YAML, missing required fields
2. **Data Validation Errors**: Schema violations, negative values
3. **Cache Errors**: Corruption, version mismatches
4. **I/O Errors**: File not found, permission denied

### Error Handling Strategy

```python
class MIncError(Exception):
    """Base exception for M|inc errors"""
    pass

class ConfigurationError(MIncError):
    """Configuration validation failed"""
    pass

class DataValidationError(MIncError):
    """Data schema validation failed"""
    pass

class CacheError(MIncError):
    """Cache operation failed"""
    pass

# Error handling in economic engine
def process_tick(self, tick_num: int) -> TickResult:
    try:
        events = []
        events.extend(self._soup_drip())
        events.extend(self._execute_trades())
        events.extend(self._pay_retainers())
        events.extend(self._execute_interactions())
        
        metrics = self._compute_metrics()
        snapshots = self._snapshot_agents()
        
        return TickResult(tick_num, events, metrics, snapshots)
    
    except DataValidationError as e:
        logger.error(f"Tick {tick_num} validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Tick {tick_num} processing failed: {e}")
        raise MIncError(f"Tick processing failed: {e}") from e
```

## Testing Strategy

### Unit Tests

**Target**: Individual functions and classes

**Coverage**:
- Economic calculation functions (raid_value, p_knight_win, etc.)
- Agent registry operations
- Cache layer operations
- Policy DSL compilation
- Event aggregation logic

**Example**:
```python
def test_raid_value_calculation():
    merc = Agent(id="M-01", role=Role.MERCENARY, 
                 wealth=WealthTraits(raid=10, sense=5, adapt=4, ...))
    king = Agent(id="K-01", role=Role.KING,
                 wealth=WealthTraits(defend=20, ...))
    knights = []
    config = EconomicConfig(alpha_raid=1.0, beta_sense_adapt=0.25, ...)
    
    rv = raid_value(merc, king, knights, config)
    
    assert rv > 0
    assert isinstance(rv, float)
```

### Integration Tests

**Target**: Component interactions

**Coverage**:
- Trace reader → Agent registry flow
- Economic engine → Event aggregator flow
- Cache layer → Economic engine integration
- Signal processor → Event aggregator integration

**Example**:
```python
def test_tick_processing_flow():
    registry = AgentRegistry(config)
    engine = EconomicEngine(registry, config)
    
    result = engine.process_tick(tick_num=1)
    
    assert result.tick_num == 1
    assert len(result.events) > 0
    assert result.metrics.wealth_total >= 0
```

### End-to-End Tests

**Target**: Full pipeline from BFF trace to M|inc outputs

**Coverage**:
- Load BFF trace → Process ticks → Write outputs
- Determinism verification (same seed → same outputs)
- Schema validation for all outputs
- Performance benchmarks

**Example**:
```python
def test_full_pipeline():
    trace_file = "testdata/bff_trace_10ticks.json"
    output_dir = "test_output/"
    
    pipeline = MIncPipeline(trace_file, output_dir, config)
    pipeline.run(num_ticks=10)
    
    # Verify outputs exist
    assert (output_dir / "ticks.json").exists()
    assert (output_dir / "events.csv").exists()
    assert (output_dir / "agents_final.csv").exists()
    
    # Verify determinism
    pipeline2 = MIncPipeline(trace_file, "test_output2/", config)
    pipeline2.run(num_ticks=10)
    
    assert files_identical("test_output/ticks.json", "test_output2/ticks.json")
```

### Property-Based Tests

**Target**: Invariants and mathematical properties

**Coverage**:
- Currency/wealth never negative
- Total currency/wealth conserved (except trade creation)
- Deterministic resolution given same inputs
- Cache correctness (cached == computed)

**Example**:
```python
@given(
    king_currency=st.integers(min_value=0, max_value=10000),
    merc_currency=st.integers(min_value=0, max_value=10000),
    bribe_amount=st.integers(min_value=0, max_value=1000)
)
def test_bribe_currency_conservation(king_currency, merc_currency, bribe_amount):
    king = Agent(id="K-01", currency=king_currency, ...)
    merc = Agent(id="M-01", currency=merc_currency, ...)
    
    total_before = king.currency + merc.currency
    
    outcome = resolve_bribe(king, merc, [], config)
    apply_bribe_outcome(king, merc, outcome)
    
    total_after = king.currency + merc.currency
    
    # Currency conserved (no creation/destruction in bribe)
    assert total_after == total_before
```

## Performance Considerations

### Optimization Strategies

1. **Caching**: Memoize deterministic outcomes for repeated states
2. **Batch Processing**: Process multiple ticks before I/O
3. **Lazy Evaluation**: Compute metrics only when needed
4. **Efficient Data Structures**: Use numpy arrays for wealth traits
5. **Parallel Processing**: Process independent agent interactions in parallel

### Performance Targets

- **Tick Processing**: < 10ms per tick for 1000 agents
- **Cache Hit Rate**: > 80% for repeated state encounters
- **Memory Usage**: < 100MB for 10,000 agents
- **I/O Throughput**: > 1000 ticks/second to disk

### Profiling Points

```python
import cProfile
import pstats

def profile_tick_processing():
    profiler = cProfile.Profile()
    profiler.enable()
    
    engine.process_tick(tick_num=1)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

## Configuration Schema

### YAML Configuration Structure

```yaml
version: "0.1.1"
seed: 1337

roles:
  ratios:
    king: 0.10
    knight: 0.20
    mercenary: 0.70
  mutation_rate: 0.0  # optional role changes per tick

economic:
  currency_to_wealth_ratio: [100, 5]
  bribe_leakage: 0.05
  exposure_factors:
    king: 1.0
    knight: 0.5
    mercenary: 0.4
  
  raid_value_weights:
    alpha_raid: 1.0
    beta_sense_adapt: 0.25
    gamma_king_defend: 0.60
    delta_king_exposed: 0.40
  
  defend_resolution:
    base_knight_winrate: 0.50
    trait_advantage_weight: 0.30
    clamp_min: 0.05
    clamp_max: 0.95
    stake_currency_frac: 0.10
  
  trade:
    invest_per_tick: 100
    created_wealth_units: 5
    distribution:
      defend: 3
      trade: 2
  
  on_failed_bribe:
    king_currency_loss_frac: 0.50
    king_wealth_loss_frac: 0.25

refractory:
  raid: 2  # ticks
  defend: 1
  bribe: 1
  trade: 0

cache:
  enabled: true
  max_size: 10000
  witness_sample_rate: 0.05

output:
  json_ticks: true
  csv_events: true
  csv_final_agents: true
  compress: false

trait_emergence:
  enabled: true
  rules:
    - condition: "copy >= 12 AND tick % 2 == 0"
      delta: {copy: 1}
```

## Deployment Considerations

### Installation

```bash
# Install M|inc as a Python package
cd python/
pip install -e ./m_inc/

# Or install with dependencies
pip install -e ./m_inc/[dev]  # includes testing tools
```

### CLI Usage

```bash
# Run M|inc on existing BFF trace
python -m m_inc.cli \
  --trace testdata/bff_trace.json \
  --config config/minc_default.yaml \
  --output output/ \
  --ticks 100

# Run M|inc with live BFF simulation
./bin/main --lang bff_noheads | python -m m_inc.cli --stream --config config.yaml

# Analyze M|inc outputs
python -m m_inc.analyze \
  --ticks output/ticks.json \
  --events output/events.csv \
  --plot wealth_distribution
```

### Integration Points

1. **Standalone Mode**: Process historical BFF traces
2. **Streaming Mode**: Consume live BFF simulation output
3. **Batch Mode**: Process multiple trace files in parallel
4. **Analysis Mode**: Post-process M|inc outputs for visualization

## Future Extensions

### Planned Enhancements

1. **Learning Policies**: Replace fixed formulas with adaptive strategies
2. **Spatial Neighborhoods**: Limit interactions to local agent clusters
3. **Multi-King Alliances**: Enable king-king cooperation mechanisms
4. **Mercenary Guilds**: Allow mercenary coordination
5. **Visualization Dashboard**: Real-time web UI for M|inc metrics
6. **Interop with GoL/QFT**: Use external cellular automata as data sources

### Extension Points

- **Policy DSL**: Add new policy types via YAML
- **Event Channels**: Define custom channels with priorities
- **Metrics**: Register custom metric calculators
- **Output Formats**: Add new serialization formats (Parquet, HDF5)

---

*This design document provides the architectural foundation for integrating M|inc into CuBFF. Implementation details are specified in the tasks document.*
