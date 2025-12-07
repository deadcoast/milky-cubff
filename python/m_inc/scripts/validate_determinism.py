#!/usr/bin/env python3
"""
Determinism validation script for M|inc system.
Verifies that same seed produces identical outputs across multiple runs.
"""

import json
import sys
import hashlib
from pathlib import Path
import tempfile
from typing import Dict, List

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


class DeterminismValidator:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def add_result(self, test_name: str, passed: bool, message: str):
        self.results.append((test_name, passed, message))
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "="*70)
        print("DETERMINISM VALIDATION SUMMARY")
        print("="*70)
        print(f"✓ Passed: {self.passed}")
        print(f"✗ Failed: {self.failed}")
        
        for name, passed, message in self.results:
            status = "✓" if passed else "✗"
            print(f"  {status} {name}: {message}")
        
        print("="*70)
        return self.failed == 0


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_json_hash(filepath: Path) -> str:
    """Compute hash of JSON file content (normalized)."""
    with open(filepath) as f:
        data = json.load(f)
    
    # Normalize JSON by sorting keys
    normalized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(normalized.encode()).hexdigest()


def run_minc_processing(trace_path: Path, output_dir: Path, 
                        config_path: Path, seed: int, max_ticks: int = None) -> bool:
    """Run M|inc processing with specified seed."""
    try:
        import random
        
        # Set seed
        random.seed(seed)
        
        # Load configuration
        config = ConfigLoader.load(config_path)
        config.seed = seed
        
        # Initialize components
        reader = TraceReader(trace_path)
        registry = AgentRegistry(config.registry, seed=seed)
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
        print(f"Error processing: {e}")
        import traceback
        traceback.print_exc()
        return False


def compare_outputs(dir1: Path, dir2: Path, validator: DeterminismValidator):
    """Compare outputs from two runs."""
    
    # Compare events.csv
    events1 = dir1 / 'events.csv'
    events2 = dir2 / 'events.csv'
    
    if events1.exists() and events2.exists():
        hash1 = compute_file_hash(events1)
        hash2 = compute_file_hash(events2)
        
        if hash1 == hash2:
            validator.add_result("events.csv", True, "Identical across runs")
        else:
            validator.add_result("events.csv", False, "Differs between runs")
    else:
        validator.add_result("events.csv", False, "File missing in one or both runs")
    
    # Compare agents_final.csv
    agents1 = dir1 / 'agents_final.csv'
    agents2 = dir2 / 'agents_final.csv'
    
    if agents1.exists() and agents2.exists():
        hash1 = compute_file_hash(agents1)
        hash2 = compute_file_hash(agents2)
        
        if hash1 == hash2:
            validator.add_result("agents_final.csv", True, "Identical across runs")
        else:
            validator.add_result("agents_final.csv", False, "Differs between runs")
    else:
        validator.add_result("agents_final.csv", False, "File missing in one or both runs")
    
    # Compare tick JSON files
    tick_files1 = sorted(dir1.glob("tick_*.json"))
    tick_files2 = sorted(dir2.glob("tick_*.json"))
    
    if len(tick_files1) != len(tick_files2):
        validator.add_result("Tick JSON count", False, 
                           f"Different number of files: {len(tick_files1)} vs {len(tick_files2)}")
        return
    
    validator.add_result("Tick JSON count", True, 
                        f"Same number of files: {len(tick_files1)}")
    
    # Compare each tick file
    mismatches = 0
    for f1, f2 in zip(tick_files1, tick_files2):
        hash1 = compute_json_hash(f1)
        hash2 = compute_json_hash(f2)
        
        if hash1 != hash2:
            mismatches += 1
    
    if mismatches == 0:
        validator.add_result("Tick JSON content", True, 
                           f"All {len(tick_files1)} tick files identical")
    else:
        validator.add_result("Tick JSON content", False, 
                           f"{mismatches}/{len(tick_files1)} tick files differ")


def validate_determinism_for_trace(trace_name: str, trace_path: Path,
                                   config_path: Path, seed: int,
                                   max_ticks: int = None) -> bool:
    """Validate determinism for a specific trace."""
    print(f"\n{'='*70}")
    print(f"Testing determinism: {trace_name} (seed={seed})")
    print(f"{'='*70}")
    
    validator = DeterminismValidator()
    
    with tempfile.TemporaryDirectory() as tmpdir1:
        with tempfile.TemporaryDirectory() as tmpdir2:
            output_dir1 = Path(tmpdir1)
            output_dir2 = Path(tmpdir2)
            
            # Run 1
            print("Run 1...")
            success1 = run_minc_processing(trace_path, output_dir1, config_path, 
                                          seed, max_ticks)
            
            if not success1:
                print("✗ Run 1 failed")
                return False
            
            # Run 2
            print("Run 2...")
            success2 = run_minc_processing(trace_path, output_dir2, config_path, 
                                          seed, max_ticks)
            
            if not success2:
                print("✗ Run 2 failed")
                return False
            
            # Compare outputs
            print("Comparing outputs...")
            compare_outputs(output_dir1, output_dir2, validator)
            
            return validator.print_summary()


def main():
    """Run determinism validation tests."""
    print("M|inc Determinism Validation")
    print("="*70)
    print("Testing that same seed produces identical outputs")
    
    # Setup paths
    base_dir = Path(__file__).parent
    testdata_dir = base_dir / 'testdata'
    config_path = base_dir / 'config' / 'minc_default.yaml'
    
    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        return 1
    
    # Test with different traces and seeds
    test_cases = [
        ('trace_10tick.json', 1337, 10),
        ('trace_10tick.json', 42, 10),
        ('bff_trace_small.json', 1337, None),
    ]
    
    all_passed = True
    
    for trace_name, seed, max_ticks in test_cases:
        trace_path = testdata_dir / trace_name
        
        if not trace_path.exists():
            print(f"⚠ Trace file not found: {trace_name}, skipping")
            continue
        
        passed = validate_determinism_for_trace(trace_name, trace_path, 
                                               config_path, seed, max_ticks)
        
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✓ All determinism tests passed")
        return 0
    else:
        print("✗ Some determinism tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
