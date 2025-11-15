"""Policy DSL Compiler for M|inc economic rules.

This module provides a compiler that transforms YAML policy definitions
into executable Python callables. Policies define economic rules like
raid_value, p_knight_win, bribe_outcome, and trade_action.
"""

import ast
import math
from dataclasses import dataclass
from typing import Dict, Any, Callable, List, Optional
import yaml
from pathlib import Path


class PolicyError(Exception):
    """Base exception for policy-related errors."""
    pass


class ValidationError(PolicyError):
    """Policy validation failed."""
    pass


class CompilationError(PolicyError):
    """Policy compilation failed."""
    pass


@dataclass
class CompiledPolicies:
    """Container for compiled policy functions.
    
    Attributes:
        bribe_outcome: Function to compute bribe outcome
        raid_value: Function to compute raid value
        p_knight_win: Function to compute knight win probability
        trade_action: Function to compute trade action outcome
        name: Policy name
        version: Policy version
        parameters: Policy parameters
    """
    bribe_outcome: Callable
    raid_value: Callable
    p_knight_win: Callable
    trade_action: Callable
    name: str = "default"
    version: str = "1.0.0"
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class PolicyCompiler:
    """Compiler for Policy DSL.
    
    Transforms YAML policy definitions into executable Python functions.
    Validates syntax and ensures policies are pure (no side effects).
    """
    
    def __init__(self, yaml_config: Dict[str, Any]):
        """Initialize compiler with YAML configuration.
        
        Args:
            yaml_config: Dictionary containing policy definition
        """
        self.yaml_config = yaml_config
        self.policy_data = yaml_config.get('policy', {})
        self.parameters = self.policy_data.get('parameters', {})
        self.functions = self.policy_data.get('functions', {})
        self.name = self.policy_data.get('name', 'default')
        self.version = self.policy_data.get('version', '1.0.0')
        
        # Safe built-in functions allowed in formulas
        self.safe_builtins = {
            'abs': abs,
            'min': min,
            'max': max,
            'round': round,
            'int': int,
            'float': float,
            'sum': sum,
            'len': len,
            'sigmoid': self._sigmoid,
            'clamp': self._clamp,
        }
    
    @staticmethod
    def _sigmoid(x: float) -> float:
        """Sigmoid function for use in formulas."""
        try:
            return 1.0 / (1.0 + math.exp(-x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0
    
    @staticmethod
    def _clamp(value: float, min_val: float, max_val: float) -> float:
        """Clamp function for use in formulas."""
        return max(min_val, min(max_val, value))
    
    @classmethod
    def from_file(cls, path: Path | str) -> 'PolicyCompiler':
        """Create compiler from YAML file.
        
        Args:
            path: Path to YAML policy file
            
        Returns:
            PolicyCompiler instance
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Policy file not found: {path}")
        
        with open(path, 'r') as f:
            yaml_config = yaml.safe_load(f)
        
        return cls(yaml_config)
    
    def validate(self) -> List[str]:
        """Validate policy syntax and structure.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for policy root key
        if 'policy' not in self.yaml_config:
            errors.append("Missing 'policy' root key")
            return errors
        
        # Check for functions
        if not self.functions:
            errors.append("No functions defined in policy")
        
        # Validate each function
        required_functions = ['raid_value', 'p_knight_win', 'bribe_outcome', 'trade_action']
        for func_name in required_functions:
            if func_name not in self.functions:
                errors.append(f"Missing required function: {func_name}")
        
        # Validate function definitions
        for func_name, func_def in self.functions.items():
            if not isinstance(func_def, dict):
                errors.append(f"Function {func_name} must be a dictionary")
                continue
            
            # Check for formula or conditions
            if 'formula' not in func_def and 'conditions' not in func_def:
                errors.append(f"Function {func_name} missing 'formula' or 'conditions'")
            
            # Validate formula syntax if present
            if 'formula' in func_def:
                formula_errors = self._validate_formula(func_def['formula'], func_name)
                errors.extend(formula_errors)
        
        # Validate parameters are numeric
        for param_name, param_value in self.parameters.items():
            if not isinstance(param_value, (int, float)):
                errors.append(f"Parameter {param_name} must be numeric, got {type(param_value)}")
        
        return errors
    
    def _validate_formula(self, formula: str, func_name: str) -> List[str]:
        """Validate a formula string.
        
        Args:
            formula: Formula string to validate
            func_name: Name of function (for error messages)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not formula or not isinstance(formula, str):
            errors.append(f"Function {func_name}: Formula must be a non-empty string")
            return errors
        
        try:
            # Parse formula into AST
            tree = ast.parse(formula, mode='eval')
            
            # Check for unsafe operations
            for node in ast.walk(tree):
                # Disallow imports
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    errors.append(f"Function {func_name}: Imports not allowed in formulas")
                
                # Disallow function calls except safe builtins
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id not in self.safe_builtins:
                            errors.append(
                                f"Function {func_name}: Unsafe function call: {node.func.id}"
                            )
                    # Disallow attribute calls (e.g., obj.method())
                    elif isinstance(node.func, ast.Attribute):
                        errors.append(
                            f"Function {func_name}: Method calls not allowed in formulas"
                        )
                
                # Disallow assignments
                if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                    errors.append(f"Function {func_name}: Assignments not allowed in formulas")
                
                # Disallow del statements
                if isinstance(node, ast.Delete):
                    errors.append(f"Function {func_name}: Delete statements not allowed in formulas")
                
                # Disallow exec/eval
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ('exec', 'eval', 'compile', '__import__'):
                        errors.append(f"Function {func_name}: {node.func.id} not allowed in formulas")
        
        except SyntaxError as e:
            errors.append(f"Function {func_name}: Syntax error in formula: {e}")
        except Exception as e:
            errors.append(f"Function {func_name}: Validation error: {e}")
        
        return errors
    
    def compile(self) -> CompiledPolicies:
        """Compile policy into executable functions.
        
        Returns:
            CompiledPolicies with callable functions
            
        Raises:
            ValidationError: If policy validation fails
            CompilationError: If compilation fails
        """
        # Validate first
        errors = self.validate()
        if errors:
            raise ValidationError(f"Policy validation failed:\n" + "\n".join(errors))
        
        try:
            # Compile each function
            bribe_outcome = self._compile_bribe_outcome()
            raid_value = self._compile_raid_value()
            p_knight_win = self._compile_p_knight_win()
            trade_action = self._compile_trade_action()
            
            return CompiledPolicies(
                bribe_outcome=bribe_outcome,
                raid_value=raid_value,
                p_knight_win=p_knight_win,
                trade_action=trade_action,
                name=self.name,
                version=self.version,
                parameters=self.parameters.copy()
            )
        
        except Exception as e:
            raise CompilationError(f"Policy compilation failed: {e}") from e
    
    def test_compiled_policies(self, compiled: CompiledPolicies, test_agents: Dict[str, Any], 
                               config: Any) -> Dict[str, Any]:
        """Test compiled policies against known inputs.
        
        Args:
            compiled: CompiledPolicies to test
            test_agents: Dictionary with test agent instances
            config: Configuration object
            
        Returns:
            Dictionary with test results
        """
        results = {
            'passed': True,
            'tests': {},
            'errors': []
        }
        
        try:
            # Test raid_value
            if 'merc' in test_agents and 'king' in test_agents:
                rv = compiled.raid_value(
                    test_agents['merc'], 
                    test_agents['king'], 
                    test_agents.get('knights', []), 
                    config
                )
                results['tests']['raid_value'] = {
                    'result': rv,
                    'type': type(rv).__name__,
                    'valid': isinstance(rv, (int, float)) and rv >= 0
                }
                if not results['tests']['raid_value']['valid']:
                    results['passed'] = False
                    results['errors'].append('raid_value returned invalid result')
            
            # Test p_knight_win
            if 'knight' in test_agents and 'merc' in test_agents:
                p = compiled.p_knight_win(
                    test_agents['knight'],
                    test_agents['merc'],
                    config
                )
                results['tests']['p_knight_win'] = {
                    'result': p,
                    'type': type(p).__name__,
                    'valid': isinstance(p, (int, float)) and 0.0 <= p <= 1.0
                }
                if not results['tests']['p_knight_win']['valid']:
                    results['passed'] = False
                    results['errors'].append('p_knight_win returned invalid probability')
            
            # Test bribe_outcome
            if 'king' in test_agents and 'merc' in test_agents:
                outcome = compiled.bribe_outcome(
                    test_agents['king'],
                    test_agents['merc'],
                    test_agents.get('knights', []),
                    config,
                    compiled.raid_value
                )
                results['tests']['bribe_outcome'] = {
                    'result': outcome,
                    'valid': isinstance(outcome, dict) and 'accepted' in outcome
                }
                if not results['tests']['bribe_outcome']['valid']:
                    results['passed'] = False
                    results['errors'].append('bribe_outcome returned invalid result')
            
            # Test trade_action
            if 'king' in test_agents:
                outcome = compiled.trade_action(test_agents['king'], config)
                results['tests']['trade_action'] = {
                    'result': outcome,
                    'valid': isinstance(outcome, dict) and 'success' in outcome
                }
                if not results['tests']['trade_action']['valid']:
                    results['passed'] = False
                    results['errors'].append('trade_action returned invalid result')
        
        except Exception as e:
            results['passed'] = False
            results['errors'].append(f'Test execution failed: {e}')
        
        return results
    
    def verify_determinism(self, compiled: CompiledPolicies, test_agents: Dict[str, Any],
                          config: Any, iterations: int = 10) -> Dict[str, Any]:
        """Verify that compiled policies are deterministic.
        
        Args:
            compiled: CompiledPolicies to test
            test_agents: Dictionary with test agent instances
            config: Configuration object
            iterations: Number of times to run each function
            
        Returns:
            Dictionary with determinism test results
        """
        results = {
            'deterministic': True,
            'functions': {},
            'errors': []
        }
        
        try:
            # Test raid_value determinism
            if 'merc' in test_agents and 'king' in test_agents:
                values = []
                for _ in range(iterations):
                    rv = compiled.raid_value(
                        test_agents['merc'],
                        test_agents['king'],
                        test_agents.get('knights', []),
                        config
                    )
                    values.append(rv)
                
                all_equal = all(v == values[0] for v in values)
                results['functions']['raid_value'] = {
                    'deterministic': all_equal,
                    'values': values[:3]  # Store first 3 for inspection
                }
                if not all_equal:
                    results['deterministic'] = False
                    results['errors'].append('raid_value is non-deterministic')
            
            # Test p_knight_win determinism
            if 'knight' in test_agents and 'merc' in test_agents:
                values = []
                for _ in range(iterations):
                    p = compiled.p_knight_win(
                        test_agents['knight'],
                        test_agents['merc'],
                        config
                    )
                    values.append(p)
                
                all_equal = all(v == values[0] for v in values)
                results['functions']['p_knight_win'] = {
                    'deterministic': all_equal,
                    'values': values[:3]
                }
                if not all_equal:
                    results['deterministic'] = False
                    results['errors'].append('p_knight_win is non-deterministic')
            
            # Test bribe_outcome determinism
            if 'king' in test_agents and 'merc' in test_agents:
                outcomes = []
                for _ in range(iterations):
                    outcome = compiled.bribe_outcome(
                        test_agents['king'],
                        test_agents['merc'],
                        test_agents.get('knights', []),
                        config,
                        compiled.raid_value
                    )
                    outcomes.append(outcome)
                
                # Compare outcomes (convert to string for comparison)
                all_equal = all(str(o) == str(outcomes[0]) for o in outcomes)
                results['functions']['bribe_outcome'] = {
                    'deterministic': all_equal,
                    'sample': outcomes[0]
                }
                if not all_equal:
                    results['deterministic'] = False
                    results['errors'].append('bribe_outcome is non-deterministic')
            
            # Test trade_action determinism
            if 'king' in test_agents:
                outcomes = []
                for _ in range(iterations):
                    outcome = compiled.trade_action(test_agents['king'], config)
                    outcomes.append(outcome)
                
                all_equal = all(str(o) == str(outcomes[0]) for o in outcomes)
                results['functions']['trade_action'] = {
                    'deterministic': all_equal,
                    'sample': outcomes[0]
                }
                if not all_equal:
                    results['deterministic'] = False
                    results['errors'].append('trade_action is non-deterministic')
        
        except Exception as e:
            results['deterministic'] = False
            results['errors'].append(f'Determinism test failed: {e}')
        
        return results
    
    def _compile_raid_value(self) -> Callable:
        """Compile raid_value function from policy definition.
        
        Returns:
            Callable that computes raid value
        """
        func_def = self.functions.get('raid_value', {})
        
        if 'formula' in func_def:
            formula = func_def['formula']
            params = func_def.get('parameters', {})
            
            def raid_value_func(merc, king, knights, config):
                # Build context for formula evaluation
                context = {
                    'merc': merc,
                    'king': king,
                    'knights': knights,
                    'config': config,
                    **self.safe_builtins,
                    **params,
                }
                
                # Add computed variables
                context['king_defend'] = self._compute_king_defend(king, knights, config)
                context['king_exposed'] = self._compute_king_exposed(king, config)
                
                # Evaluate formula
                result = eval(formula, {"__builtins__": {}}, context)
                return max(0.0, float(result))
            
            return raid_value_func
        
        # Fallback to default implementation
        return self._default_raid_value
    
    def _compile_p_knight_win(self) -> Callable:
        """Compile p_knight_win function from policy definition.
        
        Returns:
            Callable that computes knight win probability
        """
        func_def = self.functions.get('p_knight_win', {})
        
        if 'formula' in func_def:
            formula = func_def['formula']
            params = func_def.get('parameters', {})
            variables = func_def.get('variables', {})
            
            def p_knight_win_func(knight, merc, config):
                # Build context
                context = {
                    'knight': knight,
                    'merc': merc,
                    'config': config,
                    **self.safe_builtins,
                    **params,
                }
                
                # Evaluate variable definitions
                for var_name, var_formula in variables.items():
                    context[var_name] = eval(var_formula, {"__builtins__": {}}, context)
                
                # Evaluate main formula
                result = eval(formula, {"__builtins__": {}}, context)
                return float(result)
            
            return p_knight_win_func
        
        # Fallback to default implementation
        return self._default_p_knight_win
    
    def _compile_bribe_outcome(self) -> Callable:
        """Compile bribe_outcome function from policy definition.
        
        Returns:
            Callable that computes bribe outcome
        """
        func_def = self.functions.get('bribe_outcome', {})
        
        if 'conditions' in func_def:
            conditions = func_def['conditions']
            
            def bribe_outcome_func(king, merc, knights, config, raid_value_func):
                # Compute raid value
                rv = raid_value_func(merc, king, knights, config)
                threshold = king.bribe_threshold
                
                # Build context
                context = {
                    'king': king,
                    'merc': merc,
                    'knights': knights,
                    'config': config,
                    'raid_value': rv,
                    'threshold': threshold,
                    **self.safe_builtins,
                }
                
                # Evaluate conditions
                for condition in conditions:
                    if 'if' in condition:
                        if eval(condition['if'], {"__builtins__": {}}, context):
                            return self._build_bribe_outcome(condition, rv, threshold)
                    elif 'else' in condition:
                        return self._build_bribe_outcome(condition, rv, threshold)
                
                # Default: rejected
                return {'accepted': False, 'reason': 'rejected'}
            
            return bribe_outcome_func
        
        # Fallback to default implementation
        return self._default_bribe_outcome
    
    def _compile_trade_action(self) -> Callable:
        """Compile trade_action function from policy definition.
        
        Returns:
            Callable that computes trade action outcome
        """
        func_def = self.functions.get('trade_action', {})
        
        if 'conditions' in func_def:
            conditions = func_def['conditions']
            
            def trade_action_func(king, config):
                invest_amount = config.trade.get('invest_per_tick', 100)
                
                # Build context
                context = {
                    'king': king,
                    'config': config,
                    'invest_amount': invest_amount,
                    **self.safe_builtins,
                }
                
                # Evaluate conditions
                for condition in conditions:
                    if 'if' in condition:
                        if eval(condition['if'], {"__builtins__": {}}, context):
                            return self._build_trade_outcome(condition, invest_amount)
                    elif 'else' in condition:
                        return self._build_trade_outcome(condition, invest_amount)
                
                # Default: insufficient funds
                return {'success': False, 'reason': 'insufficient_funds'}
            
            return trade_action_func
        
        # Fallback to default implementation
        return self._default_trade_action
    
    def _build_bribe_outcome(self, condition: Dict, rv: float, threshold: int) -> Dict:
        """Build bribe outcome from condition definition.
        
        Args:
            condition: Condition dictionary from YAML
            rv: Computed raid value
            threshold: King's bribe threshold
            
        Returns:
            Dictionary with bribe outcome
        """
        result = condition.get('result', 'rejected')
        
        if result == 'accepted':
            then_clause = condition.get('then', {})
            return {
                'accepted': True,
                'amount': threshold,
                'king_currency_delta': eval(str(then_clause.get('king_currency', '-threshold')), 
                                           {"__builtins__": {}}, 
                                           {'threshold': threshold}),
                'merc_currency_delta': eval(str(then_clause.get('merc_currency', '+threshold')),
                                           {"__builtins__": {}},
                                           {'threshold': threshold}),
                'king_wealth_leakage': then_clause.get('king_wealth_leakage', 0.05),
            }
        else:
            return {
                'accepted': False,
                'reason': result
            }
    
    def _build_trade_outcome(self, condition: Dict, invest_amount: int) -> Dict:
        """Build trade outcome from condition definition.
        
        Args:
            condition: Condition dictionary from YAML
            invest_amount: Investment amount
            
        Returns:
            Dictionary with trade outcome
        """
        result = condition.get('result', 'insufficient_funds')
        
        if result == 'success':
            then_clause = condition.get('then', {})
            return {
                'success': True,
                'invest': invest_amount,
                'wealth_created': then_clause.get('king_wealth', {}),
            }
        else:
            return {
                'success': False,
                'reason': result
            }
    
    # Helper methods for computing derived values
    
    def _compute_king_defend(self, king, knights, config) -> float:
        """Compute king's defensive projection."""
        if not knights:
            return 0.0
        
        score = sum(
            k.wealth.defend + 0.5 * k.wealth.sense + 0.5 * k.wealth.adapt
            for k in knights
        )
        return score
    
    def _compute_king_exposed(self, king, config) -> float:
        """Compute king's exposed wealth."""
        exposure_factor = config.exposure_factors.get(king.role.value, 1.0)
        return king.wealth_total() * exposure_factor
    
    # Default implementations (fallback if not defined in YAML)
    
    def _default_raid_value(self, merc, king, knights, config) -> float:
        """Default raid value implementation."""
        from ..core.economics import raid_value as default_rv
        return default_rv(merc, king, knights, config)
    
    def _default_p_knight_win(self, knight, merc, config) -> float:
        """Default p_knight_win implementation."""
        from ..core.economics import p_knight_win as default_pkw
        return default_pkw(knight, merc, config)
    
    def _default_bribe_outcome(self, king, merc, knights, config, raid_value_func) -> Dict:
        """Default bribe outcome implementation."""
        from ..core.economics import resolve_bribe
        outcome = resolve_bribe(king, merc, knights, config)
        return {
            'accepted': outcome.accepted,
            'amount': outcome.amount,
            'king_currency_delta': outcome.king_currency_delta,
            'merc_currency_delta': outcome.merc_currency_delta,
            'king_wealth_leakage': outcome.king_wealth_leakage,
            'reason': outcome.reason,
        }
    
    def _default_trade_action(self, king, config) -> Dict:
        """Default trade action implementation."""
        invest = config.trade.get('invest_per_tick', 100)
        
        if king.currency >= invest:
            return {
                'success': True,
                'invest': invest,
                'wealth_created': config.trade.get('distribution', {}),
            }
        else:
            return {
                'success': False,
                'reason': 'insufficient_funds'
            }
