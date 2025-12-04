#!/usr/bin/env python3
"""
Integration validation script for M|inc system.
Tests processing of existing BFF traces and validates outputs.
"""

import json
import sys
from pathlib import Path
import tempfile
import shutil
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.schemas import AgentSchema, EventSchema, TickMetricsSchema
    from core.config import ConfigLoader
    from adapters.trace_reader import TraceReader
    from core.agent_registry import AgentRegistry
    from core.economic_engine import EconomicEngine
    from adapters.output_writer import OutputWriter
except ImportError:
    # Try absolute imports
    from m_inc.core.schemas import AgentSchema, EventSchema, TickMetricsSchema
    from m_inc.core.config import ConfigLoader
    from m_inc.adapters.trace_reader import TraceReader
    from m_inc.core.agent_registry import AgentRegistry
    from m_inc.core.economic_engine import EconomicEngine
    from m_inc.adapters.output_writer import OutputWriter


class ValidationResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed.append((test_name, message))
    
    def add_fail(self, test_name: str, message: str):
        self.failed.append((test_name, message))
    
    def add_warning(self, test_name: str, message: str):
        self.warnings.append((test_name, message))
    
    def print_summary(self):
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)
        print(f"✓ Passed: {len(self.passed)}")
        print(f"✗ Failed: {len(self.failed)}")
        print(f"⚠ Warnings: {len(self.warnings)}")
        
        if self.warnings:
            print("\nWarnings:")
            for name, msg in self.warnings:
                print(f"  ⚠ {name}: {msg}")
        
        if self.failed:
            print("\nFailures:")
            for name, msg in self.failed:
                print(f"  ✗ {name}: {msg}")
        
        print("="*70)
        return len(self.failed) == 0


def validate_json_schema(data: Dict, schema_class, test_name: str, result: ValidationResult):
    """Validate data against a Pydantic schema."""
    try:
        schema_class(**data)
        result.add_pass(test_name, "Schema validation passed")
        return True
    except Exception as e:
        result.add_fail(test_name, f"Schema validation failed: {e}")
        return False


def validate_output_files(output_dir: Path, result: ValidationResult):
    """Validate that expected output files exist and have correct structure."""
    
    # Check for required files
    required_files = {
        'events.csv': 'Event log CSV',
        'agents_final.csv': 'Final agent state CSV',
    }
    
    for filename, description in required_files.items():
        filepath = output_dir / filename
        if filepath.exists():
            result.add_pass(f"Output file: {filename}", f"{description} exists")
            
            # Check file is not empty
            if filepath.stat().st_size == 0:
                result.add_warning(f"Output file: {filename}", "File is empty")
        else:
            result.add_fail(f"Output file: {filename}", f"{description} not found")
    
    # Check for tick JSON files
    tick_files = list(output_dir.glob("tick_*.json"))
    if tick_files:
        result.add_pass("Tick JSON files", f"Found {len(tick_files)} tick files")
        
        # Validate first tick file structure
        if tick_files:
            first_tick = sorted(tick_files)[0]
            try:
                with open(first_tick) as f:
                    tick_data = json.load(f)
                
                # Check required fields
                required_fields = ['tick', 'metrics', 'agents', 'meta']
                for field in required_fields:
                    if field in tick_data:
                        result.add_pass(f"Tick JSON: {field}", "Field present")
                    else:
                        result.add_fail(f"Tick JSON: {field}", "Field missing")
                
                # Validate metrics schema
                if 'metrics' in tick_data:
                    validate_json_schema(
                        tick_data['metrics'],
                        TickMetricsSchema,
                        "Tick metrics schema",
                        result
                    )
                
                # Validate agent schemas
                if 'agents' in tick_data:
                    for i, agent in enumerate(tick_data['agents'][:3]):  # Check first 3
                        validate_json_schema(
                            agent,
                            AgentSchema,
                            f"Agent schema (agent {i})",
                            result
                        )
                
            except json.JSONDecodeError as e:
                result.add_fail("Tick JSON parsing", f"Invalid JSON: {e}")
            except Exception as e:
                result.add_fail("Tick JSON validation", f"Error: {e}")
    else:
        result.add_warning("Tick JSON files", "No tick files found")


def validate_csv_structure(csv_path: Path, expected_columns: List[str], 
                          test_name: str, result: ValidationResult):
    """Validate CSV file has expected columns."""
    try:
        with open(csv_path) as f:
            header = f.readline().strip()
            columns = [col.strip() for col in header.split(',')]
            
            missing = set(expected_columns) - set(columns)
            if missing:
                result.add_fail(test_name, f"Missing columns: {missing}")
            else:
                result.add_pass(test_name, "All expected columns present")
                
    except Exception as e:
        result.add_fail(test_name, f"Error reading CSV: {e}")


def run_trace_processing(trace_path: Path, output_dir: Path, 
                         config_path: Path, max_ticks: int = None) -> bool:
    """Run M|inc processing on a trace file."""
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
        
        # Determine number of ticks
        num_ticks = max_ticks if max_ticks else 10
        
        # Process ticks
        for tick_num in range(1, num_ticks + 1):
            result = engine.process_tick(tick_num)
            writer.write_tick_json(result)
            writer.write_event_csv(result.events)
        
        # Write final agent state
        agents = registry.get_all_agents()
        writer.write_final_agents_csv(agents)
        
        return True
            
    except Exception as e:
        print(f"Error processing trace: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_trace_processing(trace_name: str, trace_path: Path, 
                              config_path: Path, result: ValidationResult,
                              max_ticks: int = None):
    """Process a trace and validate outputs."""
    print(f"\n{'='*70}")
    print(f"Processing trace: {trace_name}")
    print(f"{'='*70}")
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Run processing
        success = run_trace_processing(trace_path, output_dir, config_path, max_ticks)
        
        if not success:
            result.add_fail(f"Trace processing: {trace_name}", "Processing failed")
            return
        
        result.add_pass(f"Trace processing: {trace_name}", "Processing completed")
        
        # Validate outputs
        validate_output_files(output_dir, result)
        
        # Validate CSV structures
        events_csv = output_dir / 'events.csv'
        if events_csv.exists():
            expected_event_columns = ['tick', 'type', 'king', 'knight', 'merc', 
                                     'amount', 'stake', 'p_knight', 'notes']
            validate_csv_structure(
                events_csv,
                expected_event_columns,
                f"Events CSV structure: {trace_name}",
                result
            )
        
        agents_csv = output_dir / 'agents_final.csv'
        if agents_csv.exists():
            expected_agent_columns = ['id', 'role', 'currency', 'compute', 'copy',
                                     'defend', 'raid', 'trade', 'sense', 'adapt',
                                     'wealth_total']
            validate_csv_structure(
                agents_csv,
                expected_agent_columns,
                f"Agents CSV structure: {trace_name}",
                result
            )


def main():
    """Run integration validation tests."""
    print("M|inc Integration Validation")
    print("="*70)
    
    result = ValidationResult()
    
    # Setup paths
    base_dir = Path(__file__).parent
    testdata_dir = base_dir / 'testdata'
    config_path = base_dir / 'config' / 'minc_default.yaml'
    
    # Check config exists
    if not config_path.exists():
        result.add_fail("Configuration", f"Config file not found: {config_path}")
        result.print_summary()
        return 1
    
    result.add_pass("Configuration", "Config file found")
    
    # Test traces to validate
    test_traces = [
        ('trace_10tick.json', 10),
        ('trace_100tick.json', 20),  # Only process first 20 ticks for speed
        ('bff_trace_small.json', None),
    ]
    
    for trace_name, max_ticks in test_traces:
        trace_path = testdata_dir / trace_name
        
        if not trace_path.exists():
            result.add_warning(f"Trace file: {trace_name}", "File not found, skipping")
            continue
        
        validate_trace_processing(trace_name, trace_path, config_path, result, max_ticks)
    
    # Print summary
    success = result.print_summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
