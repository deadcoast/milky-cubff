"""Tests for Policy DSL Compiler."""

import pytest
from m_inc.policies.policy_dsl import PolicyCompiler, PolicyValidationError, PolicyCompilationError, CompiledPolicies
from m_inc.core.models import Agent, Role, WealthTraits
from m_inc.core.config import EconomicConfig


@pytest.fixture
def sample_policy_config():
    """Sample policy configuration for testing."""
    return {
        'policies': {
            'raid_value': {
                'formula': 'alpha*merc.wealth.raid + beta*(merc.wealth.sense+merc.wealth.adapt) - gamma*king_defend + delta*king_exposed',
                'params': {
                    'alpha': 1.0,
                    'beta': 0.25,
                    'gamma': 0.60,
                    'delta': 0.40
                }
            },
            'bribe_outcome': {
                'condition': 'threshold >= raid_value and king.currency >= threshold',
                'on_success': {
                    'king_currency': '-threshold',
                    'merc_currency': '+threshold',
                    'king_wealth_leakage': 0.05
                }
            },
            'p_knight_win': {
                'formula': 'clamp(base + (sigmoid(weight * trait_delta) - 0.5), clamp_min, clamp_max)',
                'params': {
                    'base': 0.5,
                    'weight': 0.3,
                    'employment_bonus': 0.25,
                    'clamp_min': 0.05,
                    'clamp_max': 0.95
                }
            },
            'trade_action': {
                'params': {
                    'invest_per_tick': 100,
                    'created_wealth_units': 5,
                    'distribution': {'defend': 3, 'trade': 2}
                }
            }
        }
    }


@pytest.fixture
def sample_agents():
    """Create sample agents for testing."""
    king = Agent(
        id="K-01",
        tape_id=1,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(compute=10, copy=12, defend=20, raid=2, trade=15, sense=5, adapt=7),
        bribe_threshold=300
    )
    
    knight = Agent(
        id="N-01",
        tape_id=2,
        role=Role.KNIGHT,
        currency=200,
        wealth=WealthTraits(compute=3, copy=2, defend=15, raid=1, trade=0, sense=8, adapt=5),
        employer="K-01"
    )
    
    merc = Agent(
        id="M-01",
        tape_id=3,
        role=Role.MERCENARY,
        currency=50,
        wealth=WealthTraits(compute=1, copy=3, defend=0, raid=12, trade=0, sense=6, adapt=4)
    )
    
    return king, knight, merc


def test_policy_compiler_initialization(sample_policy_config):
    """Test PolicyCompiler initialization."""
    compiler = PolicyCompiler(sample_policy_config)
    assert compiler.config == sample_policy_config
    assert 'raid_value' in compiler.policies


def test_policy_validation_success(sample_policy_config):
    """Test successful policy validation."""
    compiler = PolicyCompiler(sample_policy_config)
    errors = compiler.validate()
    assert len(errors) == 0


def test_policy_validation_missing_policy():
    """Test validation fails when required policy is missing."""
    config = {'policies': {'raid_value': {'formula': 'merc.raid'}}}
    compiler = PolicyCompiler(config)
    errors = compiler.validate()
    assert len(errors) > 0
    assert any('bribe_outcome' in err for err in errors)


def test_policy_validation_invalid_syntax():
    """Test validation fails with invalid formula syntax."""
    config = {
        'policies': {
            'raid_value': {'formula': 'merc.raid +'},  # Invalid syntax
            'bribe_outcome': {'condition': 'True'},
            'p_knight_win': {'formula': '0.5'},
            'trade_action': {'params': {}}
        }
    }
    compiler = PolicyCompiler(config)
    errors = compiler.validate()
    assert len(errors) > 0


def test_policy_compilation_success(sample_policy_config):
    """Test successful policy compilation."""
    compiler = PolicyCompiler(sample_policy_config)
    compiled = compiler.compile()
    
    assert isinstance(compiled, CompiledPolicies)
    assert callable(compiled.raid_value)
    assert callable(compiled.bribe_outcome)
    assert callable(compiled.p_knight_win)
    assert callable(compiled.trade_action)


def test_compiled_raid_value(sample_policy_config, sample_agents):
    """Test compiled raid_value function."""
    king, knight, merc = sample_agents
    config = EconomicConfig()
    
    compiler = PolicyCompiler(sample_policy_config)
    compiled = compiler.compile()
    
    rv = compiled.raid_value(merc, king, [knight], config)
    
    assert isinstance(rv, float)
    assert rv >= 0.0


def test_compiled_bribe_outcome(sample_policy_config, sample_agents):
    """Test compiled bribe_outcome function."""
    king, knight, merc = sample_agents
    config = EconomicConfig()
    
    compiler = PolicyCompiler(sample_policy_config)
    compiled = compiler.compile()
    
    # Compute raid value first
    rv = compiled.raid_value(merc, king, [knight], config)
    
    # Test bribe outcome
    outcome = compiled.bribe_outcome(king, merc, [knight], config, rv)
    
    assert hasattr(outcome, 'accepted')
    assert isinstance(outcome.accepted, bool)


def test_compiled_p_knight_win(sample_policy_config, sample_agents):
    """Test compiled p_knight_win function."""
    king, knight, merc = sample_agents
    config = EconomicConfig()
    
    compiler = PolicyCompiler(sample_policy_config)
    compiled = compiler.compile()
    
    p = compiled.p_knight_win(knight, merc, config)
    
    assert isinstance(p, float)
    assert 0.0 <= p <= 1.0


def test_compiled_trade_action(sample_policy_config, sample_agents):
    """Test compiled trade_action function."""
    king, knight, merc = sample_agents
    config = EconomicConfig()
    
    initial_currency = king.currency
    initial_defend = king.wealth.defend
    
    compiler = PolicyCompiler(sample_policy_config)
    compiled = compiler.compile()
    
    created = compiled.trade_action(king, config)
    
    assert created == 5
    assert king.currency == initial_currency - 100
    assert king.wealth.defend == initial_defend + 3


def test_formula_with_safe_functions(sample_agents):
    """Test formula evaluation with safe functions."""
    config = {
        'policies': {
            'raid_value': {
                'formula': 'max(0, merc.wealth.raid - 5)',
                'params': {}
            },
            'bribe_outcome': {'condition': 'True'},
            'p_knight_win': {'formula': '0.5'},
            'trade_action': {'params': {}}
        }
    }
    
    king, knight, merc = sample_agents
    econ_config = EconomicConfig()
    
    compiler = PolicyCompiler(config)
    compiled = compiler.compile()
    
    rv = compiled.raid_value(merc, king, [knight], econ_config)
    assert rv == max(0, merc.wealth.raid - 5)


def test_unsafe_operation_rejected():
    """Test that unsafe operations are rejected during validation."""
    config = {
        'policies': {
            'raid_value': {
                'formula': '__import__("os").system("ls")',  # Unsafe!
                'params': {}
            },
            'bribe_outcome': {'condition': 'True'},
            'p_knight_win': {'formula': '0.5'},
            'trade_action': {'params': {}}
        }
    }
    
    compiler = PolicyCompiler(config)
    
    with pytest.raises(PolicyCompilationError):
        compiler.compile()


def test_attribute_access(sample_policy_config, sample_agents):
    """Test that attribute access works in formulas."""
    king, knight, merc = sample_agents
    config = EconomicConfig()
    
    compiler = PolicyCompiler(sample_policy_config)
    compiled = compiler.compile()
    
    # The formula accesses merc.raid, merc.sense, etc.
    rv = compiled.raid_value(merc, king, [knight], config)
    
    # Should not raise an error
    assert isinstance(rv, float)


def test_pure_functions():
    """Test that compiled functions are pure (no side effects except trade)."""
    config = {
        'policies': {
            'raid_value': {
                'formula': 'merc.wealth.raid * 2',
                'params': {}
            },
            'bribe_outcome': {'condition': 'False'},
            'p_knight_win': {'formula': '0.5'},
            'trade_action': {'params': {'invest_per_tick': 100}}
        }
    }
    
    king = Agent(
        id="K-01", tape_id=1, role=Role.KING, currency=5000,
        wealth=WealthTraits(compute=10, copy=12, defend=20, raid=2, trade=15, sense=5, adapt=7)
    )
    merc = Agent(
        id="M-01", tape_id=3, role=Role.MERCENARY, currency=50,
        wealth=WealthTraits(compute=1, copy=3, defend=0, raid=12, trade=0, sense=6, adapt=4)
    )
    
    econ_config = EconomicConfig()
    compiler = PolicyCompiler(config)
    compiled = compiler.compile()
    
    # Call raid_value multiple times
    initial_raid = merc.wealth.raid
    rv1 = compiled.raid_value(merc, king, [], econ_config)
    rv2 = compiled.raid_value(merc, king, [], econ_config)
    
    # Should be deterministic and not modify agents
    assert rv1 == rv2
    assert merc.wealth.raid == initial_raid


# ============================================================================
# Task 7.3: Additional validation and testing
# ============================================================================

def test_formula_syntax_validation_before_compilation():
    """Test that formula syntax is validated before compilation."""
    # Test various invalid syntax cases
    invalid_configs = [
        {
            'policies': {
                'raid_value': {'formula': 'merc.raid +'},  # Incomplete expression
                'bribe_outcome': {'condition': 'True'},
                'p_knight_win': {'formula': '0.5'},
                'trade_action': {'params': {}}
            }
        },
        {
            'policies': {
                'raid_value': {'formula': 'merc.raid * * 2'},  # Double operator
                'bribe_outcome': {'condition': 'True'},
                'p_knight_win': {'formula': '0.5'},
                'trade_action': {'params': {}}
            }
        },
        {
            'policies': {
                'raid_value': {'formula': 'merc.raid'},
                'bribe_outcome': {'condition': '(threshold >= raid_value'},  # Unmatched paren
                'p_knight_win': {'formula': '0.5'},
                'trade_action': {'params': {}}
            }
        },
    ]
    
    for config in invalid_configs:
        compiler = PolicyCompiler(config)
        errors = compiler.validate()
        assert len(errors) > 0, f"Expected validation errors for config: {config}"


def test_unsafe_operations_validation():
    """Test that unsafe operations are caught during validation."""
    unsafe_configs = [
        {
            'policies': {
                'raid_value': {'formula': 'eval("1+1")'},  # eval is unsafe
                'bribe_outcome': {'condition': 'True'},
                'p_knight_win': {'formula': '0.5'},
                'trade_action': {'params': {}}
            }
        },
        {
            'policies': {
                'raid_value': {'formula': 'exec("print(1)")'},  # exec is unsafe
                'bribe_outcome': {'condition': 'True'},
                'p_knight_win': {'formula': '0.5'},
                'trade_action': {'params': {}}
            }
        },
        {
            'policies': {
                'raid_value': {'formula': 'open("/etc/passwd")'},  # file access is unsafe
                'bribe_outcome': {'condition': 'True'},
                'p_knight_win': {'formula': '0.5'},
                'trade_action': {'params': {}}
            }
        },
    ]
    
    for config in unsafe_configs:
        compiler = PolicyCompiler(config)
        with pytest.raises((PolicyCompilationError, PolicyValidationError)):
            compiler.compile()


def test_generated_functions_with_known_inputs():
    """Test generated functions against known inputs with expected outputs."""
    config = {
        'policies': {
            'raid_value': {
                'formula': '2 * merc.wealth.raid + 10',
                'params': {}
            },
            'bribe_outcome': {
                'condition': 'threshold >= raid_value and king.currency >= threshold',
                'on_success': {
                    'king_currency': '-threshold',
                    'merc_currency': '+threshold',
                    'king_wealth_leakage': 0.05
                }
            },
            'p_knight_win': {
                'formula': '0.6',  # Fixed probability for testing
                'params': {}
            },
            'trade_action': {
                'params': {
                    'invest_per_tick': 100,
                    'created_wealth_units': 5,
                    'distribution': {'defend': 3, 'trade': 2}
                }
            }
        }
    }
    
    # Create test agents with known values
    king = Agent(
        id="K-01", tape_id=1, role=Role.KING, currency=1000,
        wealth=WealthTraits(compute=5, copy=5, defend=10, raid=0, trade=5, sense=3, adapt=2),
        bribe_threshold=50
    )
    merc = Agent(
        id="M-01", tape_id=3, role=Role.MERCENARY, currency=100,
        wealth=WealthTraits(compute=1, copy=1, defend=0, raid=20, trade=0, sense=2, adapt=1)
    )
    knight = Agent(
        id="N-01", tape_id=2, role=Role.KNIGHT, currency=200,
        wealth=WealthTraits(compute=2, copy=1, defend=15, raid=0, trade=0, sense=5, adapt=3)
    )
    
    econ_config = EconomicConfig()
    compiler = PolicyCompiler(config)
    compiled = compiler.compile()
    
    # Test raid_value with known formula: 2 * 20 + 10 = 50
    rv = compiled.raid_value(merc, king, [knight], econ_config)
    assert rv == 50.0, f"Expected raid_value=50.0, got {rv}"
    
    # Test p_knight_win with fixed value
    p = compiled.p_knight_win(knight, merc, econ_config)
    assert p == 0.6, f"Expected p_knight_win=0.6, got {p}"
    
    # Test bribe_outcome with threshold=50, raid_value=50 (should succeed)
    outcome = compiled.bribe_outcome(king, merc, [knight], econ_config, rv)
    assert outcome.accepted == True, "Expected bribe to be accepted"
    assert outcome.amount == 50, f"Expected bribe amount=50, got {outcome.amount}"


def test_determinism_of_compiled_policies():
    """Test that compiled policies produce deterministic results."""
    config = {
        'policies': {
            'raid_value': {
                'formula': 'alpha*merc.wealth.raid + beta*(merc.wealth.sense+merc.wealth.adapt)',
                'params': {'alpha': 1.5, 'beta': 0.3}
            },
            'bribe_outcome': {
                'condition': 'threshold >= raid_value and king.currency >= threshold',
                'on_success': {
                    'king_currency': '-threshold',
                    'merc_currency': '+threshold',
                    'king_wealth_leakage': 0.05
                }
            },
            'p_knight_win': {
                'formula': 'clamp(0.5 + sigmoid(0.3 * trait_delta) - 0.5, 0.05, 0.95)',
                'params': {}
            },
            'trade_action': {
                'params': {
                    'invest_per_tick': 100,
                    'created_wealth_units': 5,
                    'distribution': {'defend': 3, 'trade': 2}
                }
            }
        }
    }
    
    # Create test agents
    king = Agent(
        id="K-01", tape_id=1, role=Role.KING, currency=5000,
        wealth=WealthTraits(compute=10, copy=12, defend=20, raid=2, trade=15, sense=5, adapt=7),
        bribe_threshold=300
    )
    merc = Agent(
        id="M-01", tape_id=3, role=Role.MERCENARY, currency=50,
        wealth=WealthTraits(compute=1, copy=3, defend=0, raid=12, trade=0, sense=6, adapt=4)
    )
    knight = Agent(
        id="N-01", tape_id=2, role=Role.KNIGHT, currency=200,
        wealth=WealthTraits(compute=3, copy=2, defend=15, raid=1, trade=0, sense=8, adapt=5)
    )
    
    econ_config = EconomicConfig()
    
    # Compile policies multiple times
    compiler1 = PolicyCompiler(config)
    compiled1 = compiler1.compile()
    
    compiler2 = PolicyCompiler(config)
    compiled2 = compiler2.compile()
    
    # Test raid_value determinism
    rv1_a = compiled1.raid_value(merc, king, [knight], econ_config)
    rv1_b = compiled1.raid_value(merc, king, [knight], econ_config)
    rv2 = compiled2.raid_value(merc, king, [knight], econ_config)
    
    assert rv1_a == rv1_b, "Same compiled function should produce same result"
    assert rv1_a == rv2, "Different compilations should produce same result"
    
    # Test p_knight_win determinism
    p1_a = compiled1.p_knight_win(knight, merc, econ_config)
    p1_b = compiled1.p_knight_win(knight, merc, econ_config)
    p2 = compiled2.p_knight_win(knight, merc, econ_config)
    
    assert p1_a == p1_b, "Same compiled function should produce same result"
    assert p1_a == p2, "Different compilations should produce same result"
    
    # Test bribe_outcome determinism
    outcome1_a = compiled1.bribe_outcome(king, merc, [knight], econ_config, rv1_a)
    outcome1_b = compiled1.bribe_outcome(king, merc, [knight], econ_config, rv1_a)
    outcome2 = compiled2.bribe_outcome(king, merc, [knight], econ_config, rv2)
    
    assert outcome1_a.accepted == outcome1_b.accepted, "Same compiled function should produce same result"
    assert outcome1_a.accepted == outcome2.accepted, "Different compilations should produce same result"


def test_determinism_with_different_agent_states():
    """Test that policies are deterministic for various agent states."""
    config = {
        'policies': {
            'raid_value': {
                'formula': 'merc.wealth.raid * 1.5',
                'params': {}
            },
            'bribe_outcome': {
                'condition': 'threshold >= raid_value and king.currency >= threshold',
                'on_success': {
                    'king_currency': '-threshold',
                    'merc_currency': '+threshold',
                    'king_wealth_leakage': 0.05
                }
            },
            'p_knight_win': {
                'formula': '0.5',
                'params': {}
            },
            'trade_action': {
                'params': {'invest_per_tick': 100}
            }
        }
    }
    
    compiler = PolicyCompiler(config)
    compiled = compiler.compile()
    econ_config = EconomicConfig()
    
    # Test with multiple different agent configurations
    test_cases = [
        (10, 5, 8),   # (merc_raid, knight_defend, king_defend)
        (20, 15, 10),
        (5, 25, 30),
        (0, 0, 0),
        (100, 50, 75),
    ]
    
    for merc_raid, knight_defend, king_defend in test_cases:
        king = Agent(
            id="K-01", tape_id=1, role=Role.KING, currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=king_defend, raid=2, trade=15, sense=5, adapt=7),
            bribe_threshold=300
        )
        merc = Agent(
            id="M-01", tape_id=3, role=Role.MERCENARY, currency=50,
            wealth=WealthTraits(compute=1, copy=3, defend=0, raid=merc_raid, trade=0, sense=6, adapt=4)
        )
        knight = Agent(
            id="N-01", tape_id=2, role=Role.KNIGHT, currency=200,
            wealth=WealthTraits(compute=3, copy=2, defend=knight_defend, raid=1, trade=0, sense=8, adapt=5)
        )
        
        # Call multiple times with same inputs
        rv1 = compiled.raid_value(merc, king, [knight], econ_config)
        rv2 = compiled.raid_value(merc, king, [knight], econ_config)
        
        assert rv1 == rv2, f"Non-deterministic result for raid={merc_raid}"
        assert rv1 == merc_raid * 1.5, f"Incorrect calculation for raid={merc_raid}"


def test_validation_catches_missing_formula_and_condition():
    """Test that validation catches policies missing both formula and condition."""
    config = {
        'policies': {
            'raid_value': {
                'params': {'alpha': 1.0}  # Missing formula
            },
            'bribe_outcome': {'condition': 'True'},
            'p_knight_win': {'formula': '0.5'},
            'trade_action': {'params': {}}
        }
    }
    
    compiler = PolicyCompiler(config)
    errors = compiler.validate()
    
    assert len(errors) > 0
    assert any('formula' in err.lower() or 'condition' in err.lower() for err in errors)


def test_validation_with_complex_formulas():
    """Test validation with complex but valid formulas."""
    config = {
        'policies': {
            'raid_value': {
                'formula': 'max(0, alpha*merc.wealth.raid + beta*(merc.wealth.sense+merc.wealth.adapt) - gamma*king_defend + delta*king_exposed)',
                'params': {'alpha': 1.0, 'beta': 0.25, 'gamma': 0.6, 'delta': 0.4}
            },
            'bribe_outcome': {
                'condition': 'threshold >= raid_value and king.currency >= threshold',
                'on_success': {
                    'king_currency': '-threshold',
                    'merc_currency': '+threshold',
                    'king_wealth_leakage': 0.05
                }
            },
            'p_knight_win': {
                'formula': 'clamp(0.5 + (sigmoid(0.3 * trait_delta) - 0.5), 0.05, 0.95)',
                'params': {}
            },
            'trade_action': {
                'params': {'invest_per_tick': 100}
            }
        }
    }
    
    compiler = PolicyCompiler(config)
    errors = compiler.validate()
    
    assert len(errors) == 0, f"Valid complex formulas should not produce errors: {errors}"


def test_compiled_functions_are_pure():
    """Test that compiled functions don't modify input agents (except trade_action)."""
    config = {
        'policies': {
            'raid_value': {
                'formula': 'merc.wealth.raid + king.wealth.defend',
                'params': {}
            },
            'bribe_outcome': {
                'condition': 'False',  # Always reject
                'on_success': {}
            },
            'p_knight_win': {
                'formula': 'knight.wealth.defend / (knight.wealth.defend + merc.wealth.raid + 1)',
                'params': {}
            },
            'trade_action': {
                'params': {'invest_per_tick': 100}
            }
        }
    }
    
    king = Agent(
        id="K-01", tape_id=1, role=Role.KING, currency=5000,
        wealth=WealthTraits(compute=10, copy=12, defend=20, raid=2, trade=15, sense=5, adapt=7),
        bribe_threshold=300
    )
    merc = Agent(
        id="M-01", tape_id=3, role=Role.MERCENARY, currency=50,
        wealth=WealthTraits(compute=1, copy=3, defend=0, raid=12, trade=0, sense=6, adapt=4)
    )
    knight = Agent(
        id="N-01", tape_id=2, role=Role.KNIGHT, currency=200,
        wealth=WealthTraits(compute=3, copy=2, defend=15, raid=1, trade=0, sense=8, adapt=5)
    )
    
    # Save initial states
    king_initial = (king.currency, king.wealth.defend, king.wealth.trade)
    merc_initial = (merc.currency, merc.wealth.raid)
    knight_initial = (knight.currency, knight.wealth.defend)
    
    compiler = PolicyCompiler(config)
    compiled = compiler.compile()
    econ_config = EconomicConfig()
    
    # Call raid_value (should be pure)
    rv = compiled.raid_value(merc, king, [knight], econ_config)
    assert (king.currency, king.wealth.defend, king.wealth.trade) == king_initial
    assert (merc.currency, merc.wealth.raid) == merc_initial
    
    # Call p_knight_win (should be pure)
    p = compiled.p_knight_win(knight, merc, econ_config)
    assert (knight.currency, knight.wealth.defend) == knight_initial
    assert (merc.currency, merc.wealth.raid) == merc_initial
    
    # Call bribe_outcome (should be pure)
    outcome = compiled.bribe_outcome(king, merc, [knight], econ_config, rv)
    assert (king.currency, king.wealth.defend, king.wealth.trade) == king_initial
    assert (merc.currency, merc.wealth.raid) == merc_initial


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
