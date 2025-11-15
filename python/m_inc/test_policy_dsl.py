"""Tests for Policy DSL Compiler."""

import pytest
from pathlib import Path
from policies.policy_dsl import PolicyCompiler, ValidationError, CompilationError
from core.models import Agent, Role, WealthTraits
from core.config import EconomicConfig


def test_policy_compiler_from_file():
    """Test loading policy from YAML file."""
    policy_file = Path("config/minc_default_policy.yaml")
    
    if not policy_file.exists():
        pytest.skip("Policy file not found")
    
    compiler = PolicyCompiler.from_file(policy_file)
    
    assert compiler.name == "balanced_economy_v1"
    assert compiler.version == "1.0.0"
    assert 'employment_bonus' in compiler.parameters


def test_policy_validation():
    """Test policy validation."""
    # Valid policy
    valid_policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': 'merc.wealth.raid * 1.0'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(valid_policy)
    errors = compiler.validate()
    assert len(errors) == 0
    
    # Invalid policy - missing functions
    invalid_policy = {
        'policy': {
            'name': 'test',
            'functions': {}
        }
    }
    
    compiler = PolicyCompiler(invalid_policy)
    errors = compiler.validate()
    assert len(errors) > 0
    assert any('raid_value' in err for err in errors)


def test_policy_compilation():
    """Test compiling a simple policy."""
    policy = {
        'policy': {
            'name': 'test_policy',
            'version': '1.0.0',
            'functions': {
                'raid_value': {
                    'formula': 'merc.wealth.raid * 1.0',
                },
                'p_knight_win': {
                    'formula': '0.5',
                },
                'bribe_outcome': {
                    'conditions': [
                        {'if': 'king.currency >= 100', 'result': 'accepted'},
                        {'else': True, 'result': 'rejected'}
                    ]
                },
                'trade_action': {
                    'conditions': [
                        {'if': 'king.currency >= invest_amount', 'result': 'success'},
                        {'else': True, 'result': 'insufficient_funds'}
                    ]
                }
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    compiled = compiler.compile()
    
    assert compiled.name == 'test_policy'
    assert compiled.version == '1.0.0'
    assert callable(compiled.raid_value)
    assert callable(compiled.p_knight_win)
    assert callable(compiled.bribe_outcome)
    assert callable(compiled.trade_action)


def test_raid_value_function():
    """Test compiled raid_value function."""
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {
                    'formula': 'merc.wealth.raid * 2.0',
                },
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    compiled = compiler.compile()
    
    # Create test agents
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
        wealth=WealthTraits(defend=20)
    )
    
    config = EconomicConfig()
    
    # Test raid value calculation
    rv = compiled.raid_value(merc, king, [], config)
    
    # Should be merc.raid * 2.0 = 10 * 2.0 = 20.0
    assert rv == 20.0


def test_p_knight_win_function():
    """Test compiled p_knight_win function."""
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': '0.0'},
                'p_knight_win': {
                    'formula': 'clamp(0.05, 0.95, 0.5 + sigmoid(0.3 * trait_delta) - 0.5)',
                    'variables': {
                        'trait_delta': '(knight.wealth.defend) - (merc.wealth.raid)'
                    }
                },
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    compiled = compiler.compile()
    
    # Create test agents
    knight = Agent(
        id="N-01",
        tape_id=1,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(defend=15)
    )
    
    merc = Agent(
        id="M-01",
        tape_id=2,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(raid=10)
    )
    
    config = EconomicConfig()
    
    # Test p_knight_win calculation
    p = compiled.p_knight_win(knight, merc, config)
    
    # Should be clamped between 0.05 and 0.95
    assert 0.05 <= p <= 0.95


def test_bribe_outcome_function():
    """Test compiled bribe_outcome function."""
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': '100.0'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {
                    'conditions': [
                        {
                            'if': 'threshold >= raid_value and king.currency >= threshold',
                            'then': {
                                'king_currency': '-threshold',
                                'merc_currency': '+threshold',
                                'king_wealth_leakage': 0.05
                            },
                            'result': 'accepted'
                        },
                        {'else': True, 'result': 'rejected'}
                    ]
                },
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    compiled = compiler.compile()
    
    # Create test agents
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(defend=20),
        bribe_threshold=150
    )
    
    merc = Agent(
        id="M-01",
        tape_id=2,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(raid=10)
    )
    
    config = EconomicConfig()
    
    # Test bribe outcome
    outcome = compiled.bribe_outcome(king, merc, [], config, compiled.raid_value)
    
    # Should be accepted since threshold (150) >= raid_value (100) and king has currency
    assert outcome['accepted'] == True
    assert outcome['amount'] == 150


def test_trade_action_function():
    """Test compiled trade_action function."""
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': '0.0'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {
                    'conditions': [
                        {
                            'if': 'king.currency >= invest_amount',
                            'then': {
                                'king_currency': '-invest_amount',
                                'king_wealth': {'defend': 3, 'trade': 2}
                            },
                            'result': 'success'
                        },
                        {'else': True, 'result': 'insufficient_funds'}
                    ]
                }
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    compiled = compiler.compile()
    
    # Create test agent
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(defend=20)
    )
    
    config = EconomicConfig()
    
    # Test trade action
    outcome = compiled.trade_action(king, config)
    
    # Should succeed since king has enough currency
    assert outcome['success'] == True
    assert outcome['invest'] == 100


def test_unsafe_operations_rejected():
    """Test that unsafe operations are rejected during validation."""
    # Policy with import statement
    unsafe_policy = {
        'policy': {
            'name': 'unsafe',
            'functions': {
                'raid_value': {'formula': 'import os; os.system("ls")'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(unsafe_policy)
    errors = compiler.validate()
    
    # Should have validation errors
    assert len(errors) > 0


def test_pure_functions():
    """Test that compiled functions are pure (no side effects)."""
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': 'merc.wealth.raid * 1.0'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    compiled = compiler.compile()
    
    # Create test agents
    merc = Agent(
        id="M-01",
        tape_id=1,
        role=Role.MERCENARY,
        currency=100,
        wealth=WealthTraits(raid=10)
    )
    
    king = Agent(
        id="K-01",
        tape_id=2,
        role=Role.KING,
        currency=1000,
        wealth=WealthTraits(defend=20)
    )
    
    config = EconomicConfig()
    
    # Call function multiple times
    rv1 = compiled.raid_value(merc, king, [], config)
    rv2 = compiled.raid_value(merc, king, [], config)
    
    # Should return same result (deterministic)
    assert rv1 == rv2
    
    # Agent state should not be modified
    assert merc.currency == 100
    assert king.currency == 1000


def test_formula_validation_enhanced():
    """Test enhanced formula validation."""
    # Test empty formula
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': ''},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    errors = compiler.validate()
    assert len(errors) > 0
    assert any('non-empty string' in err for err in errors)
    
    # Test formula with method calls
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': 'merc.wealth.some_method()'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    errors = compiler.validate()
    assert len(errors) > 0
    assert any('Method calls not allowed' in err for err in errors)
    
    # Test formula with syntax error (assignments not allowed in eval mode)
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': 'x = 5'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    errors = compiler.validate()
    assert len(errors) > 0
    # Assignment in eval mode causes syntax error
    assert any('Syntax error' in err or 'Assignments not allowed' in err for err in errors)


def test_compiled_policies_against_known_inputs():
    """Test compiled policies against known inputs."""
    policy = {
        'policy': {
            'name': 'test',
            'version': '1.0.0',
            'functions': {
                'raid_value': {
                    'formula': 'merc.wealth.raid * 1.5 + merc.wealth.sense * 0.5',
                },
                'p_knight_win': {
                    'formula': 'clamp(0.05, 0.95, 0.5)',
                },
                'bribe_outcome': {
                    'conditions': [
                        {'if': 'king.currency >= 500', 'result': 'accepted'},
                        {'else': True, 'result': 'rejected'}
                    ]
                },
                'trade_action': {
                    'conditions': [
                        {'if': 'king.currency >= 100', 'result': 'success'},
                        {'else': True, 'result': 'insufficient_funds'}
                    ]
                }
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    compiled = compiler.compile()
    
    # Create test agents
    test_agents = {
        'merc': Agent(
            id="M-01",
            tape_id=1,
            role=Role.MERCENARY,
            currency=100,
            wealth=WealthTraits(raid=10, sense=6, adapt=3)
        ),
        'king': Agent(
            id="K-01",
            tape_id=2,
            role=Role.KING,
            currency=1000,
            wealth=WealthTraits(defend=20)
        ),
        'knight': Agent(
            id="N-01",
            tape_id=3,
            role=Role.KNIGHT,
            currency=200,
            wealth=WealthTraits(defend=15)
        ),
        'knights': []
    }
    
    config = EconomicConfig()
    
    # Test against known inputs
    results = compiler.test_compiled_policies(compiled, test_agents, config)
    
    assert results['passed'] == True
    assert 'raid_value' in results['tests']
    assert 'p_knight_win' in results['tests']
    assert 'bribe_outcome' in results['tests']
    assert 'trade_action' in results['tests']
    
    # Verify raid_value calculation
    # Should be: 10 * 1.5 + 6 * 0.5 = 15 + 3 = 18
    assert results['tests']['raid_value']['result'] == 18.0
    assert results['tests']['raid_value']['valid'] == True
    
    # Verify p_knight_win is in valid range
    assert results['tests']['p_knight_win']['valid'] == True
    assert 0.0 <= results['tests']['p_knight_win']['result'] <= 1.0
    
    # Verify bribe_outcome structure
    assert results['tests']['bribe_outcome']['valid'] == True
    assert 'accepted' in results['tests']['bribe_outcome']['result']
    
    # Verify trade_action structure
    assert results['tests']['trade_action']['valid'] == True
    assert 'success' in results['tests']['trade_action']['result']


def test_determinism_verification():
    """Test that compiled policies are deterministic."""
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {
                    'formula': 'merc.wealth.raid * 2.0 + king.wealth.defend * 0.5',
                },
                'p_knight_win': {
                    'formula': 'clamp(0.05, 0.95, 0.5 + sigmoid(0.3 * (knight.wealth.defend - merc.wealth.raid)) - 0.5)',
                },
                'bribe_outcome': {
                    'conditions': [
                        {'if': 'threshold >= raid_value', 'result': 'accepted'},
                        {'else': True, 'result': 'rejected'}
                    ]
                },
                'trade_action': {
                    'conditions': [
                        {'if': 'king.currency >= invest_amount', 'result': 'success'},
                        {'else': True, 'result': 'insufficient_funds'}
                    ]
                }
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    compiled = compiler.compile()
    
    # Create test agents
    test_agents = {
        'merc': Agent(
            id="M-01",
            tape_id=1,
            role=Role.MERCENARY,
            currency=100,
            wealth=WealthTraits(raid=10, sense=5, adapt=3)
        ),
        'king': Agent(
            id="K-01",
            tape_id=2,
            role=Role.KING,
            currency=1000,
            wealth=WealthTraits(defend=20),
            bribe_threshold=150
        ),
        'knight': Agent(
            id="N-01",
            tape_id=3,
            role=Role.KNIGHT,
            currency=200,
            wealth=WealthTraits(defend=15)
        ),
        'knights': []
    }
    
    config = EconomicConfig()
    
    # Verify determinism
    results = compiler.verify_determinism(compiled, test_agents, config, iterations=20)
    
    assert results['deterministic'] == True
    assert len(results['errors']) == 0
    
    # Check each function
    assert results['functions']['raid_value']['deterministic'] == True
    assert results['functions']['p_knight_win']['deterministic'] == True
    assert results['functions']['bribe_outcome']['deterministic'] == True
    assert results['functions']['trade_action']['deterministic'] == True
    
    # Verify all values in raid_value are identical
    rv_values = results['functions']['raid_value']['values']
    assert all(v == rv_values[0] for v in rv_values)


def test_policy_purity_no_side_effects():
    """Test that policies don't modify agent state (pure functions)."""
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': 'merc.wealth.raid * 1.0'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    compiled = compiler.compile()
    
    # Create test agents
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
    
    knight = Agent(
        id="N-01",
        tape_id=3,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(defend=15)
    )
    
    config = EconomicConfig()
    
    # Store original values
    merc_currency_orig = merc.currency
    merc_raid_orig = merc.wealth.raid
    king_currency_orig = king.currency
    king_defend_orig = king.wealth.defend
    knight_currency_orig = knight.currency
    knight_defend_orig = knight.wealth.defend
    
    # Call all functions multiple times
    for _ in range(5):
        compiled.raid_value(merc, king, [], config)
        compiled.p_knight_win(knight, merc, config)
        compiled.bribe_outcome(king, merc, [], config, compiled.raid_value)
        compiled.trade_action(king, config)
    
    # Verify no state changes
    assert merc.currency == merc_currency_orig
    assert merc.wealth.raid == merc_raid_orig
    assert king.currency == king_currency_orig
    assert king.wealth.defend == king_defend_orig
    assert knight.currency == knight_currency_orig
    assert knight.wealth.defend == knight_defend_orig


def test_invalid_formula_syntax():
    """Test that invalid formula syntax is caught during validation."""
    # Test with syntax error
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': 'merc.wealth.raid * ('},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    errors = compiler.validate()
    
    assert len(errors) > 0
    assert any('Syntax error' in err for err in errors)


def test_unsafe_function_calls():
    """Test that unsafe function calls are rejected."""
    # Test with eval
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': 'eval("1 + 1")'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    errors = compiler.validate()
    
    assert len(errors) > 0
    assert any('eval not allowed' in err for err in errors)
    
    # Test with __import__
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {'formula': '__import__("os")'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    errors = compiler.validate()
    
    assert len(errors) > 0
    assert any('__import__ not allowed' in err for err in errors)


def test_safe_builtin_functions():
    """Test that safe builtin functions are allowed."""
    policy = {
        'policy': {
            'name': 'test',
            'functions': {
                'raid_value': {
                    'formula': 'max(0, min(100, abs(merc.wealth.raid - king.wealth.defend)))'
                },
                'p_knight_win': {
                    'formula': 'clamp(0.05, 0.95, sigmoid(0.3 * knight.wealth.defend))'
                },
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    errors = compiler.validate()
    
    # Should have no errors - all functions are safe
    assert len(errors) == 0
    
    # Should compile successfully
    compiled = compiler.compile()
    assert compiled is not None


def test_parameter_validation():
    """Test that parameters are validated correctly."""
    # Test with non-numeric parameter
    policy = {
        'policy': {
            'name': 'test',
            'parameters': {
                'alpha': 1.0,
                'beta': 'not_a_number',  # Invalid
            },
            'functions': {
                'raid_value': {'formula': 'merc.wealth.raid * alpha'},
                'p_knight_win': {'formula': '0.5'},
                'bribe_outcome': {'conditions': [{'if': 'True', 'result': 'accepted'}]},
                'trade_action': {'conditions': [{'if': 'True', 'result': 'success'}]},
            }
        }
    }
    
    compiler = PolicyCompiler(policy)
    errors = compiler.validate()
    
    assert len(errors) > 0
    assert any('beta' in err and 'numeric' in err for err in errors)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
