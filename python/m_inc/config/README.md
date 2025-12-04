# M|inc Configuration Files

This directory contains YAML configuration files for M|inc economic simulation.

## Available Configurations

### minc_default.yaml

Standard configuration with full features enabled:
- **Cache**: Enabled (10,000 entries, 5% witness sampling)
- **Refractory periods**: Standard (raid: 2, defend: 1, bribe: 1, trade: 0)
- **Output**: All formats (JSON ticks, CSV events, CSV final agents)
- **Trait emergence**: Enabled (copy drip rule)
- **Role ratios**: 10% Kings, 20% Knights, 70% Mercenaries

**Use for**: Production runs, comprehensive analysis, reproducible experiments

### minc_fast.yaml

Optimized configuration for quick experiments:
- **Cache**: Disabled (no overhead)
- **Refractory periods**: None (all set to 0)
- **Output**: JSON ticks only (minimal I/O)
- **Trait emergence**: Disabled
- **Role ratios**: Same as default

**Use for**: Rapid prototyping, debugging, quick tests

## Configuration Structure

All configuration files follow this structure:

```yaml
version: "0.1.1"
seed: <integer>

roles:
  ratios: { king, knight, mercenary }
  mutation_rate: <float>
  initial_currency: { king, knight, mercenary }

economic:
  currency_to_wealth_ratio: [currency, wealth]
  bribe_leakage: <float>
  exposure_factors: { king, knight, mercenary }
  raid_value_weights: { alpha_raid, beta_sense_adapt, gamma_king_defend, delta_king_exposed }
  defend_resolution: { base_knight_winrate, trait_advantage_weight, clamp_min, clamp_max, ... }
  trade: { invest_per_tick, created_wealth_units, distribution }
  retainer: { default_fee }
  on_failed_bribe: { king_currency_loss_frac, king_wealth_loss_frac }

refractory:
  raid: <ticks>
  defend: <ticks>
  bribe: <ticks>
  trade: <ticks>

cache:
  enabled: <boolean>
  max_size: <integer>
  witness_sample_rate: <float>
  validation_interval: <integer>

output:
  json_ticks: <boolean>
  csv_events: <boolean>
  csv_final_agents: <boolean>
  compress: <boolean>
  pretty_print: <boolean>

trait_emergence:
  enabled: <boolean>
  rules: [list of emergence rules]
```

## Usage

### With CLI

```bash
# Use default configuration
python -m m_inc.cli --trace data.json --config config/minc_default.yaml

# Use fast configuration
python -m m_inc.cli --trace data.json --config config/minc_fast.yaml
```

### Programmatically

```python
from m_inc.core.config import ConfigLoader

loader = ConfigLoader("config/minc_default.yaml")
config = loader.load()
```

## Creating Custom Configurations

1. Copy an existing configuration file
2. Modify parameters as needed
3. Validate with: `python -c "import yaml; yaml.safe_load(open('your_config.yaml'))"`
4. Use with M|inc CLI or API

## Parameter Guidelines

### Role Ratios
- Must sum to 1.0
- Typical: 10% Kings, 20% Knights, 70% Mercenaries
- Adjust for different economic dynamics

### Economic Parameters
- **Bribe leakage**: 0.05 = 5% wealth loss on successful bribe
- **Raid value weights**: Control bribe threshold calculation
- **Defend resolution**: Control knight vs mercenary combat outcomes

### Refractory Periods
- Measured in ticks
- 0 = no cooldown (events can fire every tick)
- Higher values = more stability, less oscillation

### Cache Settings
- Enable for deterministic runs with repeated states
- Disable for maximum transparency and debugging
- Witness sampling validates cache correctness

### Output Options
- Enable all formats for comprehensive analysis
- Disable CSV for faster processing
- Use compression for large datasets

## See Also

- [Trace Format Documentation](../testdata/TRACE_FORMAT.md)
- [M|inc README](../README.md)
- [Requirements Document](../../.kiro/specs/minc-integration/requirements.md)
