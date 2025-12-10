"""Policy DSL Compiler for M|inc.

This module compiles YAML policy definitions into executable Python functions.
Policies define economic behaviors (bribe outcomes, raid values, etc.) using
declarative formulas that can be hot-swapped without code changes.
"""

import ast
import operator
import math
from dataclasses import dataclass
from typing import Dict, Any, Callable, List, Optional, Union
from ..core.models import Agent
from ..core.economics import (
    BribeOutcome, DefendOutcome, sigmoid, clamp,
    wealth_total, wealth_exposed, king_defend_projection
)


class PolicyValidationError(Exception):
    """Raised when policy validation fails."""
    pass


class PolicyCompilationError(Exception):
    """Raised when policy compilation fails."""
    pass


@dataclass
class CompiledPolicies:
    """Container for compiled policy functions.
    
    Attributes:
        bribe_outcome: Function to compute bribe outcome
        raid_value: Function to compute raid value
        p_knight_win: Function to compute knight win probability
        trade_action: Function to compute trade outcome
    """
    bribe_outcome: Callable
    raid_value: Callable
    p_knight_win: Callable
    trade_action: Callable


class PolicyCompiler:
    """Compiler for YAML-based policy definitions.

    The PolicyCompiler parses YAML policy configurations and generates
    pure Python callable functions. This enables hot-swapping economic
    policies without modifying code while keeping the execution surface
    area auditable—every compiled expression is inspected via the AST
    pipeline before it can run.

    Example YAML policy:
        policies:
          raid_value:
            formula: "alpha*merc.raid + beta*(merc.sense+merc.adapt) - gamma*king_defend + delta*king_exposed"
            params:
              alpha: 1.0
              beta: 0.25
              gamma: 0.60
              delta: 0.40

    Security Note:
        Attribute access is restricted to a whitelist to prevent access to
        dangerous attributes like __class__, __dict__, __init__, etc.
    """

    # Safe operators allowed in formulas
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # Safe functions allowed in formulas
    SAFE_FUNCTIONS = {
        'abs': abs,
        'min': min,
        'max': max,
        'sigmoid': sigmoid,
        'clamp': clamp,
        'sqrt': math.sqrt,
        'exp': math.exp,
        'log': math.log,
        'wealth_total': wealth_total,
        'wealth_exposed': wealth_exposed,
        'king_defend_projection': king_defend_projection,
    }

    # Whitelist of allowed attributes per object type
    # Only these attributes can be accessed on objects in formulas
    SAFE_ATTRIBUTES = {
        # Agent attributes
        'id', 'role', 'currency', 'employer', 'retainer_fee',
        'bribe_threshold', 'wealth',
        # Wealth trait attributes
        'compute', 'copy', 'defend', 'raid', 'trade', 'sense', 'adapt',
        # Config attributes (read-only access to specific fields)
        'stake_frac', 'exposed_frac', 'bribe_leakage',
    }
    
    def __init__(self, yaml_config: Dict[str, Any]):
        """Initialize the policy compiler.
        
        Args:
            yaml_config: YAML configuration dictionary containing policy definitions
        """
        self.config = yaml_config
        self.policies = yaml_config.get('policies', {})
        self.validation_errors: List[str] = []
    
    def validate(self) -> List[str]:
        """Validate policy syntax and semantics.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check that required policies are present
        required_policies = ['raid_value', 'bribe_outcome', 'p_knight_win', 'trade_action']
        for policy_name in required_policies:
            if policy_name not in self.policies:
                errors.append(f"Missing required policy: {policy_name}")
        
        # Validate each policy
        for policy_name, policy_def in self.policies.items():
            policy_errors = self._validate_policy(policy_name, policy_def)
            errors.extend(policy_errors)
        
        self.validation_errors = errors
        return errors
    
    def _validate_policy(self, name: str, definition: Dict[str, Any]) -> List[str]:
        """Validate a single policy definition.
        
        Args:
            name: Policy name
            definition: Policy definition dictionary
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # trade_action is parameter-based only, doesn't need formula/condition
        if name == 'trade_action':
            if 'params' not in definition:
                errors.append(f"Policy '{name}' missing 'params'")
            return errors
        
        # Check for formula or condition
        if 'formula' not in definition and 'condition' not in definition:
            errors.append(f"Policy '{name}' missing 'formula' or 'condition'")
            return errors
        
        # Validate formula syntax if present
        if 'formula' in definition:
            formula = definition['formula']
            try:
                self._parse_formula(formula)
            except SyntaxError as e:
                errors.append(f"Policy '{name}' has invalid formula syntax: {e}")
            except Exception as e:
                errors.append(f"Policy '{name}' formula validation failed: {e}")
        
        # Validate condition syntax if present
        if 'condition' in definition:
            condition = definition['condition']
            try:
                self._parse_formula(condition)
            except SyntaxError as e:
                errors.append(f"Policy '{name}' has invalid condition syntax: {e}")
            except Exception as e:
                errors.append(f"Policy '{name}' condition validation failed: {e}")
        
        return errors
    
    def _parse_formula(self, formula: str) -> ast.Expression:
        """Parse a formula string into an AST.
        
        Args:
            formula: Formula string to parse
            
        Returns:
            Parsed AST expression
            
        Raises:
            SyntaxError: If formula has invalid syntax
            PolicyValidationError: If formula contains unsafe operations
        """
        try:
            tree = ast.parse(formula, mode='eval')
        except SyntaxError as e:
            raise SyntaxError(f"Invalid formula syntax: {e}")
        
        # Validate that only safe operations are used
        self._validate_ast_safety(tree)
        
        return tree
    
    def _validate_ast_safety(self, node: ast.AST) -> None:
        """Validate that an AST only contains safe operations.

        Args:
            node: AST node to validate

        Raises:
            PolicyValidationError: If unsafe operations are found

        Security:
            - Rejects dunder attributes (starting with '_')
            - Only allows whitelisted attributes from SAFE_ATTRIBUTES
            - Only allows whitelisted functions from SAFE_FUNCTIONS
            - Only allows whitelisted operators from SAFE_OPERATORS
        """
        if isinstance(node, ast.Expression):
            self._validate_ast_safety(node.body)
        elif isinstance(node, ast.BinOp):
            if type(node.op) not in self.SAFE_OPERATORS:
                raise PolicyValidationError(f"Unsafe operator: {type(node.op).__name__}")
            self._validate_ast_safety(node.left)
            self._validate_ast_safety(node.right)
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in self.SAFE_OPERATORS:
                raise PolicyValidationError(f"Unsafe unary operator: {type(node.op).__name__}")
            self._validate_ast_safety(node.operand)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id not in self.SAFE_FUNCTIONS:
                    raise PolicyValidationError(f"Unsafe function: {node.func.id}")
            else:
                raise PolicyValidationError("Only simple function calls are allowed")
            for arg in node.args:
                self._validate_ast_safety(arg)
        elif isinstance(node, ast.Attribute):
            # SECURITY: Validate attribute access against whitelist
            attr_name = node.attr

            # Block dunder attributes (e.g., __class__, __dict__, __init__)
            if attr_name.startswith('_'):
                raise PolicyValidationError(
                    f"Access to private/dunder attributes not allowed: {attr_name}"
                )

            # Check against whitelist
            if attr_name not in self.SAFE_ATTRIBUTES:
                raise PolicyValidationError(
                    f"Attribute not in whitelist: {attr_name}. "
                    f"Allowed: {sorted(self.SAFE_ATTRIBUTES)}"
                )

            # Recursively validate the object being accessed
            self._validate_ast_safety(node.value)
        elif isinstance(node, ast.Name):
            # Variable names are safe
            pass
        elif isinstance(node, ast.Constant):
            # Constants are safe
            pass
        elif isinstance(node, ast.Compare):
            # Comparisons are safe
            self._validate_ast_safety(node.left)
            for comparator in node.comparators:
                self._validate_ast_safety(comparator)
        elif isinstance(node, ast.BoolOp):
            # Boolean operations are safe
            for value in node.values:
                self._validate_ast_safety(value)
        else:
            raise PolicyValidationError(f"Unsafe AST node type: {type(node).__name__}")
    
    def compile(self) -> CompiledPolicies:
        """Compile policies into callable functions.
        
        Returns:
            CompiledPolicies with all policy functions
            
        Raises:
            PolicyCompilationError: If compilation fails
        """
        # Validate first
        errors = self.validate()
        if errors:
            raise PolicyCompilationError(f"Policy validation failed: {errors}")
        
        # Compile each policy
        try:
            bribe_outcome_fn = self._compile_bribe_outcome()
            raid_value_fn = self._compile_raid_value()
            p_knight_win_fn = self._compile_p_knight_win()
            trade_action_fn = self._compile_trade_action()
        except Exception as e:
            raise PolicyCompilationError(f"Policy compilation failed: {e}")
        
        return CompiledPolicies(
            bribe_outcome=bribe_outcome_fn,
            raid_value=raid_value_fn,
            p_knight_win=p_knight_win_fn,
            trade_action=trade_action_fn
        )
    
    def _compile_raid_value(self) -> Callable:
        """Compile raid_value policy into a callable function.
        
        Returns:
            Callable that computes raid value
        """
        policy_def = self.policies['raid_value']
        formula = policy_def['formula']
        params = policy_def.get('params', {})
        
        # Parse formula
        tree = self._parse_formula(formula)
        
        def raid_value_fn(merc: Agent, king: Agent, knights: List[Agent], config: Any) -> float:
            """Compute raid value using compiled policy."""
            # Build context with available variables
            context = {
                'merc': merc,
                'king': king,
                'knights': knights,
                'config': config,
                **params,
                **self.SAFE_FUNCTIONS
            }
            
            # Add computed values
            context['king_defend'] = king_defend_projection(king, knights, 1, config)
            context['king_exposed'] = wealth_exposed(king, config)
            
            # Evaluate formula
            result = self._eval_ast(tree.body, context)
            return max(0.0, float(result))
        
        return raid_value_fn
    
    def _compile_bribe_outcome(self) -> Callable:
        """Compile bribe_outcome policy into a callable function.
        
        Returns:
            Callable that computes bribe outcome
        """
        policy_def = self.policies['bribe_outcome']
        condition = policy_def.get('condition', '')
        on_success = policy_def.get('on_success', {})
        
        # Parse condition
        condition_tree = self._parse_formula(condition) if condition else None
        
        def bribe_outcome_fn(king: Agent, merc: Agent, knights: List[Agent], 
                            config: Any, raid_value: float) -> BribeOutcome:
            """Compute bribe outcome using compiled policy."""
            threshold = king.bribe_threshold
            
            # Build context
            context = {
                'king': king,
                'merc': merc,
                'knights': knights,
                'config': config,
                'threshold': threshold,
                'raid_value': raid_value,
                **self.SAFE_FUNCTIONS
            }
            
            # Evaluate condition
            if condition_tree:
                condition_result = self._eval_ast(condition_tree.body, context)
            else:
                # Default condition
                condition_result = threshold >= raid_value and king.currency >= threshold
            
            if condition_result:
                # Parse on_success actions
                king_currency_delta = self._eval_expression(
                    on_success.get('king_currency', '-threshold'), context
                )
                merc_currency_delta = self._eval_expression(
                    on_success.get('merc_currency', '+threshold'), context
                )
                king_wealth_leakage = float(on_success.get('king_wealth_leakage', 0.05))
                
                return BribeOutcome(
                    accepted=True,
                    amount=threshold,
                    king_currency_delta=int(king_currency_delta),
                    merc_currency_delta=int(merc_currency_delta),
                    king_wealth_leakage=king_wealth_leakage,
                    reason="success"
                )
            elif threshold >= raid_value:
                return BribeOutcome(accepted=False, reason="insufficient_funds")
            else:
                return BribeOutcome(accepted=False, reason="threshold_too_low")
        
        return bribe_outcome_fn
    
    def _compile_p_knight_win(self) -> Callable:
        """Compile p_knight_win policy into a callable function.
        
        Returns:
            Callable that computes knight win probability
        """
        policy_def = self.policies['p_knight_win']
        formula = policy_def.get('formula', '')
        params = policy_def.get('params', {})
        
        # Parse formula
        tree = self._parse_formula(formula) if formula else None
        
        def p_knight_win_fn(knight: Agent, merc: Agent, config: Any) -> float:
            """Compute knight win probability using compiled policy."""
            # Build context
            knight_traits = knight.wealth.defend + knight.wealth.sense + knight.wealth.adapt
            merc_traits = merc.wealth.raid + merc.wealth.sense + merc.wealth.adapt
            trait_delta = knight_traits - merc_traits
            
            context = {
                'knight': knight,
                'merc': merc,
                'config': config,
                'trait_delta': trait_delta,
                'knight_traits': knight_traits,
                'merc_traits': merc_traits,
                **params,
                **self.SAFE_FUNCTIONS
            }
            
            if tree:
                result = self._eval_ast(tree.body, context)
            else:
                # Default formula
                base = params.get('base', 0.5)
                weight = params.get('weight', 0.3)
                result = base + (sigmoid(weight * trait_delta) - 0.5)
                
                # Employment bonus
                if knight.employer:
                    result += params.get('employment_bonus', 0.25)
            
            # Clamp result
            clamp_min = params.get('clamp_min', 0.05)
            clamp_max = params.get('clamp_max', 0.95)
            return clamp(float(result), clamp_min, clamp_max)
        
        return p_knight_win_fn
    
    def _compile_trade_action(self) -> Callable:
        """Compile trade_action policy into a callable function.
        
        Returns:
            Callable that computes trade outcome
        """
        policy_def = self.policies['trade_action']
        params = policy_def.get('params', {})
        
        def trade_action_fn(king: Agent, config: Any) -> int:
            """Compute trade outcome using compiled policy."""
            invest = params.get('invest_per_tick', 100)
            
            if king.currency < invest:
                return 0
            
            # Deduct currency
            king.add_currency(-invest)
            
            # Add wealth according to distribution
            created = params.get('created_wealth_units', 5)
            distribution = params.get('distribution', {'defend': 3, 'trade': 2})
            
            for trait_name, amount in distribution.items():
                king.add_wealth(trait_name, amount)
            
            return created
        
        return trade_action_fn
    
    def _eval_expression(self, expr: str, context: Dict[str, Any]) -> Any:
        """Evaluate a simple expression string.
        
        Args:
            expr: Expression string (e.g., "-threshold", "+100")
            context: Variable context
            
        Returns:
            Evaluated result
        """
        # Handle simple cases
        if expr.startswith('-'):
            var_name = expr[1:]
            if var_name in context:
                return -context[var_name]
            else:
                return -int(var_name)
        elif expr.startswith('+'):
            var_name = expr[1:]
            if var_name in context:
                return context[var_name]
            else:
                return int(var_name)
        else:
            # Try to parse as formula
            try:
                tree = self._parse_formula(expr)
                return self._eval_ast(tree.body, context)
            except:
                # Try as literal
                try:
                    return int(expr)
                except:
                    return float(expr)
    
    def _eval_ast(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """Evaluate an AST node with given context.

        Args:
            node: AST node to evaluate
            context: Variable context

        Returns:
            Evaluated result

        Security:
            Runtime enforcement of attribute whitelist as defense-in-depth.
        """
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            else:
                raise NameError(f"Undefined variable: {node.id}")
        elif isinstance(node, ast.Attribute):
            # SECURITY: Runtime check of attribute whitelist (defense-in-depth)
            attr_name = node.attr

            # Block dunder attributes
            if attr_name.startswith('_'):
                raise PolicyValidationError(
                    f"Access to private/dunder attributes not allowed: {attr_name}"
                )

            # Check whitelist
            if attr_name not in self.SAFE_ATTRIBUTES:
                raise PolicyValidationError(
                    f"Attribute not in whitelist: {attr_name}"
                )

            obj = self._eval_ast(node.value, context)
            return getattr(obj, attr_name)
        elif isinstance(node, ast.BinOp):
            left = self._eval_ast(node.left, context)
            right = self._eval_ast(node.right, context)
            op = self.SAFE_OPERATORS[type(node.op)]
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_ast(node.operand, context)
            op = self.SAFE_OPERATORS[type(node.op)]
            return op(operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name and func_name in context:
                func = context[func_name]
                args = [self._eval_ast(arg, context) for arg in node.args]
                return func(*args)
            else:
                raise NameError(f"Undefined function: {func_name}")
        elif isinstance(node, ast.Compare):
            left = self._eval_ast(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_ast(comparator, context)
                if isinstance(op, ast.Eq):
                    if not (left == right):
                        return False
                elif isinstance(op, ast.NotEq):
                    if not (left != right):
                        return False
                elif isinstance(op, ast.Lt):
                    if not (left < right):
                        return False
                elif isinstance(op, ast.LtE):
                    if not (left <= right):
                        return False
                elif isinstance(op, ast.Gt):
                    if not (left > right):
                        return False
                elif isinstance(op, ast.GtE):
                    if not (left >= right):
                        return False
                left = right
            return True
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result = True
                for value in node.values:
                    result = result and self._eval_ast(value, context)
                    if not result:
                        return False
                return result
            elif isinstance(node, ast.Or):
                result = False
                for value in node.values:
                    result = result or self._eval_ast(value, context)
                    if result:
                        return True
                return result
        else:
            raise ValueError(f"Unsupported AST node type: {type(node).__name__}")
