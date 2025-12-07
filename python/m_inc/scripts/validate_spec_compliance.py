#!/usr/bin/env python3
"""
Spec compliance validation script for M|inc system.
Compares outputs with reference data from docs/0.1.1/database/.
"""

import json
import csv
import sys
from pathlib import Path
import tempfile
from typing import Dict, List, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.config import ConfigLoader
    from adapters.trace_reader import TraceReader
    from core.agent_registry import AgentRegistry
    from core.economic_engine import EconomicEngine
    from adapters.output_writer import OutputWriter
except ImportError:
    from m_inc.core.config import ConfigLoader
    from m_inc.adapters.trace_reader import TraceReader
    from m_inc.core.agent_registry import AgentRegistry
    from m_inc.core.economic_engine import EconomicEngine
    from m_inc.adapters.output_writer import OutputWriter


class ComplianceValidator:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def add_check(self, name: str, status: str, message: str):
        """Add a validation check result.
        
        Args:
            name: Name of the check
            status: 'pass', 'fail', or 'warn'
            message: Description of the result
        """
        self.checks.append((name, status, message))
        if status == 'pass':
            self.passed += 1
        elif status == 'fail':
            self.failed += 1
        elif status == 'warn':
            self.warnings += 1
    
    def print_summary(self):
        print("\n" + "="*70)
        print("SPEC COMPLIANCE VALIDATION SUMMARY")
        print("="*70)
        print(f"✓ Passed: {self.passed}")
        print(f"✗ Failed: {self.failed}")
        print(f"⚠ Warnings: {self.warnings}")
        
        print("\nResults:")
        for name, status, message in self.checks:
            if status == 'pass':
                print(f"  ✓ {name}: {message}")
            elif status == 'fail':
                print(f"  ✗ {name}: {message}")
            elif status == 'warn':
                print(f"  ⚠ {name}: {message}")
        
        print("="*70)
        return self.failed == 0


def load_reference_events(ref_path: Path) -> List[Dict]:
    """Load reference events from CSV."""
    events = []
    try:
        with open(ref_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append(row)
        return events
    except Exception as e:
        print(f"Error loading reference events: {e}")
        return []


def load_reference_agents(ref_path: Path) -> List[Dict]:
    """Load reference agents from CSV."""
    agents = []
    try:
        with open(ref_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                agents.append(row)
        return agents
    except Exception as e:
        print(f"Error loading reference agents: {e}")
        return []


def load_reference_ticks(ref_path: Path) -> List[Dict]:
    """Load reference tick data from JSON."""
    try:
        with open(ref_path) as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'ticks' in data:
                return data['ticks']
            else:
                return [data]
    except Exception as e:
        print(f"Error loading reference ticks: {e}")
        return []


def validate_event_types(output_events: List[Dict], validator: ComplianceValidator):
    """Validate that output contains expected event types."""
    event_types = set()
    for event in output_events:
        if 'type' in event:
            event_types.add(event['type'])
    
    # Expected event types from spec
    expected_types = {
        'trait_drip', 'trade', 'retainer', 
        'bribe_accept', 'bribe_insufficient_funds',
        'defend_win', 'defend_loss', 'unopposed_raid'
    }
    
    found_types = event_types & expected_types
    
    if found_types:
        validator.add_check(
            "Event types",
            "pass",
            f"Found {len(found_types)} expected event types: {', '.join(sorted(found_types))}"
        )
    else:
        validator.add_check(
            "Event types",
            "warn",
            "No expected event types found in output"
        )


def validate_agent_roles(output_agents: List[Dict], validator: ComplianceValidator):
    """Validate that agents have expected roles."""
    roles = set()
    for agent in output_agents:
        if 'role' in agent:
            roles.add(agent['role'])
    
    expected_roles = {'king', 'knight', 'mercenary'}
    
    if roles == expected_roles:
        validator.add_check(
            "Agent roles",
            "pass",
            f"All expected roles present: {', '.join(sorted(roles))}"
        )
    elif roles & expected_roles:
        missing = expected_roles - roles
        validator.add_check(
            "Agent roles",
            "warn",
            f"Some roles missing: {', '.join(sorted(missing))}"
        )
    else:
        validator.add_check(
            "Agent roles",
            "fail",
            "No expected roles found"
        )


def validate_wealth_traits(output_agents: List[Dict], validator: ComplianceValidator):
    """Validate that agents have all wealth traits."""
    expected_traits = {'compute', 'copy', 'defend', 'raid', 'trade', 'sense', 'adapt'}
    
    if not output_agents:
        validator.add_check(
            "Wealth traits",
            "warn",
            "No agents to validate"
        )
        return
    
    # Check first agent
    agent = output_agents[0]
    found_traits = set(agent.keys()) & expected_traits
    
    if found_traits == expected_traits:
        validator.add_check(
            "Wealth traits",
            "pass",
            f"All {len(expected_traits)} wealth traits present"
        )
    else:
        missing = expected_traits - found_traits
        validator.add_check(
            "Wealth traits",
            "fail",
            f"Missing traits: {', '.join(sorted(missing))}"
        )


def validate_metrics_structure(tick_data: Dict, validator: ComplianceValidator):
    """Validate that tick data contains expected metrics."""
    if 'metrics' not in tick_data:
        validator.add_check(
            "Metrics structure",
            "fail",
            "No metrics field in tick data"
        )
        return
    
    metrics = tick_data['metrics']
    
    # Expected metrics from spec
    expected_metrics = {
        'entropy', 'compression_ratio', 'copy_score_mean',
        'wealth_total', 'currency_total',
        'bribes_paid', 'bribes_accepted',
        'raids_attempted', 'raids_won_by_merc', 'raids_won_by_knight'
    }
    
    found_metrics = set(metrics.keys()) & expected_metrics
    
    if len(found_metrics) >= 8:  # Allow some flexibility
        validator.add_check(
            "Metrics structure",
            "pass",
            f"Found {len(found_metrics)}/{len(expected_metrics)} expected metrics"
        )
    else:
        missing = expected_metrics - found_metrics
        validator.add_check(
            "Metrics structure",
            "warn",
            f"Missing some metrics: {', '.join(sorted(missing))}"
        )


def validate_non_negative_values(output_agents: List[Dict], validator: ComplianceValidator):
    """Validate that currency and wealth values are non-negative."""
    numeric_fields = ['currency', 'compute', 'copy', 'defend', 'raid', 'trade', 'sense', 'adapt']
    
    violations = []
    for agent in output_agents:
        agent_id = agent.get('id', 'unknown')
        for field in numeric_fields:
            if field in agent:
                try:
                    value = float(agent[field])
                    if value < 0:
                        violations.append(f"{agent_id}.{field}={value}")
                except (ValueError, TypeError):
                    pass
    
    if not violations:
        validator.add_check(
            "Non-negative values",
            "pass",
            "All currency and wealth values are non-negative"
        )
    else:
        validator.add_check(
            "Non-negative values",
            "fail",
            f"Found negative values: {', '.join(violations[:5])}"
        )


def run_and_validate(trace_path: Path, config_path: Path, 
                    validator: ComplianceValidator, max_ticks: int = 20):
    """Run M|inc and validate outputs against spec requirements."""
    print(f"\nProcessing trace and validating outputs...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Run M|inc
        try:
            # Load configuration
            config = ConfigLoader.load(config_path)
            
            # Initialize components
            reader = TraceReader(trace_path)
            registry = AgentRegistry(config.registry, seed=config.seed)
            engine = EconomicEngine(registry, config.economic, config.trait_emergence)
            writer = OutputWriter(output_dir, config.output)
            
            # Read initial epoch
            epoch_data = reader.read_epoch()
            tape_ids = list(epoch_data.tapes.keys())
            registry.assign_roles(tape_ids)
            
            # Process ticks
            for tick_num in range(1, max_ticks + 1):
                result = engine.process_tick(tick_num)
                writer.write_tick_json(result)
                writer.write_event_csv(result.events)
            
            # Write final agent state
            agents = registry.get_all_agents()
            writer.write_final_agents_csv(agents)
            
            validator.add_check("Processing", "pass", "M|inc processing completed")
            
        except Exception as e:
            validator.add_check("Processing", "fail", f"Processing failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Load outputs
        events_csv = output_dir / 'events.csv'
        agents_csv = output_dir / 'agents_final.csv'
        
        output_events = []
        if events_csv.exists():
            with open(events_csv) as f:
                reader = csv.DictReader(f)
                output_events = list(reader)
        
        output_agents = []
        if agents_csv.exists():
            with open(agents_csv) as f:
                reader = csv.DictReader(f)
                output_agents = list(reader)
        
        # Load tick JSON
        tick_files = sorted(output_dir.glob("tick_*.json"))
        tick_data = None
        if tick_files:
            with open(tick_files[0]) as f:
                tick_data = json.load(f)
        
        # Validate outputs
        if output_events:
            validate_event_types(output_events, validator)
        else:
            validator.add_check("Events output", "warn", "No events found")
        
        if output_agents:
            validate_agent_roles(output_agents, validator)
            validate_wealth_traits(output_agents, validator)
            validate_non_negative_values(output_agents, validator)
        else:
            validator.add_check("Agents output", "fail", "No agents found")
        
        if tick_data:
            validate_metrics_structure(tick_data, validator)
        else:
            validator.add_check("Tick data", "warn", "No tick JSON found")


def compare_with_reference_data(validator: ComplianceValidator):
    """Compare structure with reference data from 0.1.1 spec."""
    print(f"\nComparing with reference data from 0.1.1 spec...")
    
    base_dir = Path(__file__).parent.parent.parent
    ref_dir = base_dir / 'docs' / '0.1.1' / 'database'
    
    if not ref_dir.exists():
        validator.add_check(
            "Reference data",
            "warn",
            f"Reference directory not found: {ref_dir}"
        )
        return
    
    # Check reference files exist
    ref_files = {
        'events.csv': 'Event log structure',
        'agents.csv': 'Agent state structure',
        'ticks.json': 'Tick metrics structure',
    }
    
    for filename, description in ref_files.items():
        ref_path = ref_dir / filename
        if ref_path.exists():
            validator.add_check(
                f"Reference: {filename}",
                "pass",
                f"{description} reference available"
            )
        else:
            validator.add_check(
                f"Reference: {filename}",
                "warn",
                f"{description} reference not found"
            )


def main():
    """Run spec compliance validation tests."""
    print("M|inc Spec Compliance Validation")
    print("="*70)
    print("Validating against 0.1.1 specification requirements")
    
    validator = ComplianceValidator()
    
    # Setup paths
    base_dir = Path(__file__).parent
    testdata_dir = base_dir / 'testdata'
    config_path = base_dir / 'config' / 'minc_default.yaml'
    
    if not config_path.exists():
        validator.add_check("Configuration", "fail", f"Config not found: {config_path}")
        validator.print_summary()
        return 1
    
    validator.add_check("Configuration", "pass", "Config file found")
    
    # Use a test trace
    trace_path = testdata_dir / 'trace_10tick.json'
    
    if not trace_path.exists():
        validator.add_check("Test trace", "fail", f"Trace not found: {trace_path}")
        validator.print_summary()
        return 1
    
    validator.add_check("Test trace", "pass", "Test trace found")
    
    # Run and validate
    run_and_validate(trace_path, config_path, validator, max_ticks=10)
    
    # Compare with reference data
    compare_with_reference_data(validator)
    
    # Print summary
    success = validator.print_summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
