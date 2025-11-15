# Policy DSL - Hot-Swappable Economic Rules

The Policy DSL allows economic rules to be defined in YAML and compiled to Python callables at runtime.

## Quick Start

### 1. Define a Policy in YAML

```yaml
policy:
  name: "my_custom_policy"
  version: "1.0.0"
  description: "Custom economic rules"
  
  parameters:
    employment_bonus: 0.08
    bribe_leakage: 0.05
  
  functions:
    raid_value:
      formula: "alpha*merc.wealth.raid + beta*(merc.wealth.sense+merc.wealth.adapt) - gamma*king_defend + delta*king_exposed"
      parameters:
        alpha: 1.0
        beta: 0.25
        gamma: 0.60
        delta: 0.40
    
    p_knight_win:
      formula: "clamp(0.05, 0.95, 0.5 + sigmoid(weight * trait_delta) - 0.5 + employment_bonus)"
      parameters:
        weight: 0.30
      variables:
        trait_delta: "(knight.wealth.defend + knight.wealth.sense + knight.wealth.adapt) - (merc.wealth.raid + merc.wealth.sense + merc.wealth.adapt)"
        employment_bonus: "0.08 if knight.employer else 0.0"
    
    bribe_outcome:
      conditions:
        - if: "threshold >= raid_value and king.currency >= threshold"
          then:
            king_currency: "-threshold"
            merc_currency: "+threshold"
            king_wealth_leakage: 0.05
          result: "accepted"
        - if: "threshold >= raid_value"
          result: "insufficient_funds"
        - else:
          result: "rejected"
    
    trade_action:
      conditions:
        - if: "king.currency >= invest_amount"
          then:
            king_currency: "-invest_amount"
            king_wealth:
              defend: 3
              trade: 2
          result: "success"
        - else:
          result: "insufficient_funds"
```

### 2. Compile the Policy

```python
from policies import PolicyCompiler

# Load from file
compiler = PolicyCompiler.from_file("config/my_policy.yaml")

# Validate
errors = compiler.validate()
if errors:
    print("Validation errors:", errors)
    exit(1)

# Compile
compiled = compiler.compile()

print(f"Compiled policy: {compiled.name} v{compiled.version}")
```

### 3. Use Compiled Functions

```python
from core.models import Agent, Role, WealthTraits
from core.config import EconomicConfig

# Create agents
merc = Agent(
    id="M-01",
    tape_id=1,
    role=Role.MERCENARY,
    currency=100,
    wealth=WealthTraits(raid=10, sense=5, adapt=3)
)

king = Agent(
    id="K-01",
    tape_id=2,
    role=Role.KING,
    currency=1000,
    wealth=WealthTraits(defend=20),
    bribe_threshold=150
)

config = EconomicConfig()

# Use compiled functions
rv = compiled.raid_value(merc, king, [], config)
print(f"Raid value: {rv}")

outcome = compiled.bribe_outcome(king, merc, [], config, compiled.raid_value)
print(f"Bribe outcome: {outcome}")
```

## Available Functions

### Built-in Math Functions

The following functions are available in formulas:

- `abs(x)` - Absolute value
- `min(a, b, ...)` - Minimum value
- `max(a, b, ...)` - Maximum value
- `round(x)` - Round to nearest integer
- `int(x)` - Convert to integer
- `float(x)` - Convert to float
- `sum(list)` - Sum of list
- `len(list)` - Length of list
- `sigmoid(x)` - Sigmoid function: 1 / (1 + exp(-x))
- `clamp(value, min, max)` - Clamp value between min and max

### Agent Attributes

Access agent attributes in formulas:

- `agent.id` - Agent ID
- `agent.role` - Agent role (king, knight, mercenary)
- `agent.currency` - Currency balance
- `agent.wealth.compute` - Compute trait
- `agent.wealth.copy` - Copy trait
- `agent.wealth.defend` - Defend trait
- `agent.wealth.raid` - Raid trait
- `agent.wealth.trade` - Trade trait
- `agent.wealth.sense` - Sense trait
- `agent.wealth.adapt` - Adapt trait
- `agent.employer` - Employer ID (for knights)
- `agent.bribe_threshold` - Bribe threshold (for kings)

## Function Types

### Formula Functions

Simple mathematical expressions:

```yaml
raid_value:
  formula: "merc.wealth.raid * 2.0 + merc.wealth.sense * 0.5"
  parameters:
    multiplier: 2.0
```

### Conditional Functions

Branching logic with conditions:

```yaml
bribe_outcome:
  conditions:
    - if: "condition1"
      then: {...}
      result: "outcome1"
    - if: "condition2"
      result: "outcome2"
    - else:
      result: "default"
```

### Variables

Define intermediate calculations:

```yaml
p_knight_win:
  formula: "clamp(0.05, 0.95, base + adjustment)"
  variables:
    trait_delta: "(knight.wealth.defend) - (merc.wealth.raid)"
    adjustment: "sigmoid(0.3 * trait_delta) - 0.5"
  parameters:
    base: 0.5
```

## Security

The Policy DSL is designed to be safe:

- **No imports**: Cannot import modules or access filesystem
- **No system calls**: Cannot execute system commands
- **Sandboxed execution**: Runs in restricted environment
- **Validation**: All policies validated before compilation
- **Pure functions**: Generated functions have no side effects

## Examples

See `config/minc_default_policy.yaml` for a complete example.

## Testing

Run tests with:

```bash
python -m pytest test_policy_dsl.py -v
```

## Requirements

Policies must define all four required functions:

1. `raid_value` - Compute raid value for bribe evaluation
2. `p_knight_win` - Compute knight win probability
3. `bribe_outcome` - Determine bribe outcome
4. `trade_action` - Determine trade action outcome

## Error Handling

The compiler provides detailed error messages:

```python
try:
    compiled = compiler.compile()
except ValidationError as e:
    print(f"Validation failed: {e}")
except CompilationError as e:
    print(f"Compilation failed: {e}")
```
