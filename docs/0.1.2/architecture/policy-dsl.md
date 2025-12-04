# Policy DSL - Hot-Swappable Economic Rules

**Version**: 0.1.2  
**Status**: Planned  
**Dependencies**: Core economic engine (0.1.1)

## Overview

The Policy DSL (Domain-Specific Language) allows economic rules to be defined in YAML and compiled to Python callables at runtime. This enables:

- **Hot-swapping**: Change economic rules without restarting the simulation
- **A/B Testing**: Run multiple policy variants simultaneously
- **Experimentation**: Rapidly iterate on economic mechanics
- **Versioning**: Track policy changes over time
- **Validation**: Ensure policies are mathematically sound before deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Policy DSL System                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ YAML Policy  │───▶│   Parser &   │───▶│  Compiled    │   │
│  │ Definition   │    │   Validator  │    │  Callable    │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Policy       │◀───│   Runtime    │◀───│  Economic    │   │
│  │ Registry     │    │   Executor   │    │  Engine      │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │ Hot Reload   │───▶│  Versioning  │                       │
│  │ Watcher      │    │  & Rollback  │                       │
│  └──────────────┘    └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Policy Definition Format

### Basic Structure

```yaml
policy:
  name: "balanced_economy_v1"
  version: "1.0.0"
  description: "Balanced economic rules with moderate knight advantage"
  author: "M|inc Team"
  
  # Policy parameters
  parameters:
    employment_bonus: 0.08
    bribe_leakage: 0.05
    stake_fraction: 0.10
    
  # Economic functions
  functions:
    raid_value:
      formula: "alpha*merc.raid + beta*(merc.sense+merc.adapt) - gamma*king_defend + delta*king_exposed"
      parameters:
        alpha: 1.0
        beta: 0.25
        gamma: 0.60
        delta: 0.40
      
    p_knight_win:
      formula: "clamp(0.05, 0.95, 0.5 + sigmoid(weight * trait_delta) - 0.5 + employment_bonus)"
      parameters:
        weight: 0.30
        employment_bonus: 0.08
      variables:
        trait_delta: "(knight.defend + knight.sense + knight.adapt) - (merc.raid + merc.sense + merc.adapt)"
        employment_bonus: "0.08 if knight.employer else 0.0"
    
    bribe_outcome:
      conditions:
        - if: "threshold >= raid_value AND king.currency >= threshold"
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
              defend: "+3"
              trade: "+2"
          result: "success"
        - else:
          result: "insufficient_funds"
```

### Advanced Features

#### Conditional Logic

```yaml
functions:
  dynamic_bribe_threshold:
    conditions:
      - if: "king.wealth_total < 50"
        then: "king.currency * 0.1"  # Desperate kings offer less
      - if: "king.wealth_total > 200"
        then: "king.currency * 0.3"  # Wealthy kings offer more
      - else: "king.currency * 0.2"  # Default
```

#### Time-Based Rules

```yaml
functions:
  seasonal_trade_bonus:
    conditions:
      - if: "tick % 100 < 25"  # Spring: growth season
        then:
          wealth_multiplier: 1.5
      - if: "tick % 100 < 50"  # Summer: normal
        then:
          wealth_multiplier: 1.0
      - if: "tick % 100 < 75"  # Fall: harvest
        then:
          wealth_multiplier: 2.0
      - else:  # Winter: scarcity
        then:
          wealth_multiplier: 0.5
```

#### Agent-Specific Rules

```yaml
functions:
  role_specific_bonuses:
    king:
      trade_efficiency: 1.2
      bribe_effectiveness: 1.1
    knight:
      defend_bonus: 0.08
      loyalty_reward: 1.05
    mercenary:
      raid_bonus: 1.15
      stealth_factor: 0.9
```

## Policy Compiler

### Compilation Process

1. **Parse YAML**: Load policy definition
2. **Validate Syntax**: Check for errors and type mismatches
3. **Resolve Dependencies**: Ensure all referenced variables exist
4. **Generate Python Code**: Convert formulas to Python functions
5. **Compile**: Create callable objects
6. **Register**: Add to policy registry

### Example Compilation

**Input (YAML)**:
```yaml
functions:
  raid_value:
    formula: "alpha*merc.raid + beta*(merc.sense+merc.adapt)"
    parameters:
      alpha: 1.0
      beta: 0.25
```

**Output (Python)**:
```python
def raid_value(merc, config):
    alpha = config.get('alpha', 1.0)
    beta = config.get('beta', 0.25)
    return alpha * merc.wealth.raid + beta * (merc.wealth.sense + merc.wealth.adapt)
```

## Runtime Execution

### Policy Registry

```python
class PolicyRegistry:
    def __init__(self):
        self.policies = {}
        self.active_policy = None
        self.version_history = []
    
    def register(self, policy: CompiledPolicy):
        """Register a compiled policy."""
        self.policies[policy.name] = policy
        self.version_history.append({
            'name': policy.name,
            'version': policy.version,
            'timestamp': datetime.now()
        })
    
    def activate(self, policy_name: str):
        """Activate a policy for use."""
        if policy_name not in self.policies:
            raise ValueError(f"Policy {policy_name} not found")
        self.active_policy = self.policies[policy_name]
    
    def rollback(self, version: str):
        """Rollback to a previous policy version."""
        for entry in reversed(self.version_history):
            if entry['version'] == version:
                self.activate(entry['name'])
                return
        raise ValueError(f"Version {version} not found")
```

### Hot Reload

```python
class PolicyHotReloader:
    def __init__(self, policy_file: Path, registry: PolicyRegistry):
        self.policy_file = policy_file
        self.registry = registry
        self.last_modified = None
        self.watcher = FileSystemWatcher(policy_file)
    
    def check_and_reload(self):
        """Check if policy file changed and reload if needed."""
        if self.watcher.has_changed():
            try:
                new_policy = PolicyCompiler.compile(self.policy_file)
                self.registry.register(new_policy)
                self.registry.activate(new_policy.name)
                logger.info(f"Hot-reloaded policy: {new_policy.name}")
            except Exception as e:
                logger.error(f"Failed to reload policy: {e}")
```

## Validation

### Syntax Validation

```python
class PolicyValidator:
    def validate(self, policy_yaml: dict) -> List[ValidationError]:
        errors = []
        
        # Check required fields
        if 'policy' not in policy_yaml:
            errors.append(ValidationError("Missing 'policy' root key"))
        
        # Check function definitions
        for func_name, func_def in policy_yaml.get('functions', {}).items():
            if 'formula' not in func_def and 'conditions' not in func_def:
                errors.append(ValidationError(
                    f"Function {func_name} missing formula or conditions"
                ))
        
        # Check parameter types
        for param_name, param_value in policy_yaml.get('parameters', {}).items():
            if not isinstance(param_value, (int, float)):
                errors.append(ValidationError(
                    f"Parameter {param_name} must be numeric"
                ))
        
        return errors
```

### Mathematical Validation

```python
class MathValidator:
    def validate_formula(self, formula: str, context: dict) -> bool:
        """Ensure formula is mathematically sound."""
        try:
            # Parse formula into AST
            tree = ast.parse(formula, mode='eval')
            
            # Check for undefined variables
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if node.id not in context:
                        raise ValidationError(f"Undefined variable: {node.id}")
            
            # Check for dangerous operations
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom, ast.Call)):
                    if not self.is_safe_operation(node):
                        raise ValidationError("Unsafe operation detected")
            
            return True
        except Exception as e:
            logger.error(f"Formula validation failed: {e}")
            return False
```

## A/B Testing

### Running Multiple Policies

```python
class ABTestRunner:
    def __init__(self, policies: List[CompiledPolicy], split_ratio: float = 0.5):
        self.policy_a = policies[0]
        self.policy_b = policies[1]
        self.split_ratio = split_ratio
        self.results_a = []
        self.results_b = []
    
    def run_tick(self, agents: List[Agent], tick: int):
        """Run tick with both policies and collect results."""
        # Split agents
        split_point = int(len(agents) * self.split_ratio)
        agents_a = agents[:split_point]
        agents_b = agents[split_point:]
        
        # Run with policy A
        engine_a = EconomicEngine(agents_a, self.policy_a)
        result_a = engine_a.process_tick(tick)
        self.results_a.append(result_a)
        
        # Run with policy B
        engine_b = EconomicEngine(agents_b, self.policy_b)
        result_b = engine_b.process_tick(tick)
        self.results_b.append(result_b)
    
    def compare_results(self) -> dict:
        """Compare performance of both policies."""
        return {
            'policy_a': {
                'avg_wealth': np.mean([r.metrics.wealth_total for r in self.results_a]),
                'avg_currency': np.mean([r.metrics.currency_total for r in self.results_a]),
                'knight_win_rate': np.mean([r.metrics.raids_won_by_knight / r.metrics.raids_attempted for r in self.results_a])
            },
            'policy_b': {
                'avg_wealth': np.mean([r.metrics.wealth_total for r in self.results_b]),
                'avg_currency': np.mean([r.metrics.currency_total for r in self.results_b]),
                'knight_win_rate': np.mean([r.metrics.raids_won_by_knight / r.metrics.raids_attempted for r in self.results_b])
            }
        }
```

## Built-in Policies

### Default Policy
- Balanced economic rules
- Moderate knight advantage
- Standard bribe/raid mechanics

### Aggressive Policy
- Higher raid values
- Lower bribe effectiveness
- Faster wealth accumulation

### Defensive Policy
- Stronger knight bonuses
- Higher bribe thresholds
- Slower but stable growth

### Experimental Policy
- Dynamic thresholds
- Time-based modifiers
- Agent-specific bonuses

## Performance Considerations

- **Compilation Overhead**: Policies compiled once, reused many times
- **Hot Reload Impact**: <1ms to reload and activate new policy
- **Execution Speed**: Compiled policies run at native Python speed
- **Memory Usage**: ~1KB per compiled policy

## Security

- **Sandboxing**: Policies run in restricted execution environment
- **No System Access**: Cannot import modules or access filesystem
- **Safe Operations Only**: Limited to mathematical operations
- **Validation**: All policies validated before compilation

## Future Enhancements

- **Visual Policy Editor**: GUI for creating policies
- **Policy Marketplace**: Share and download community policies
- **Machine Learning**: Auto-generate policies from simulation data
- **Policy Optimization**: Genetic algorithms to evolve optimal policies

---

**Next**: [Cache Layer Architecture](cache-layer.md)
