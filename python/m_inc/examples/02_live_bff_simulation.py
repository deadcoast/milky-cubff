#!/usr/bin/env python3
"""
Example: Run M|inc with Live BFF Simulation

This example demonstrates how to run M|inc alongside a live BFF simulation,
processing trace data as it's generated.

Usage:
    python 02_live_bff_simulation.py
    
Note: This example uses the run_minc_on_bff.py wrapper script to coordinate
      BFF simulation and M|inc processing.
"""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Run M|inc with live BFF simulation."""
    
    print("=" * 60)
    print("M|inc Example: Live BFF Simulation")
    print("=" * 60)
    print()
    
    # Configuration
    bff_program = Path(__file__).parent.parent.parent.parent / "testdata" / "bff.txt"
    config_file = Path(__file__).parent.parent / "config" / "minc_default.yaml"
    output_dir = Path(__file__).parent / "output" / "live"
    wrapper_script = Path(__file__).parent.parent / "run_minc_on_bff.py"
    num_ticks = 20
    
    print(f"BFF program: {bff_program}")
    print(f"Config: {config_file}")
    print(f"Output: {output_dir}")
    print(f"Ticks: {num_ticks}")
    print()
    
    # Check if files exist
    if not bff_program.exists():
        print(f"Error: BFF program not found: {bff_program}")
        print("Please ensure you're running from the correct directory.")
        return 1
    
    if not wrapper_script.exists():
        print(f"Error: Wrapper script not found: {wrapper_script}")
        return 1
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build command
    cmd = [
        sys.executable,
        str(wrapper_script),
        "--bff-program", str(bff_program),
        "--config", str(config_file),
        "--output", str(output_dir),
        "--ticks", str(num_ticks)
    ]
    
    print("Running BFF simulation with M|inc processing...")
    print(f"Command: {' '.join(cmd)}")
    print()
    print("-" * 60)
    
    # Run the wrapper script
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print("-" * 60)
        print()
        print("Simulation complete!")
        print(f"Output files written to: {output_dir}")
        print()
        return 0
        
    except subprocess.CalledProcessError as e:
        print("-" * 60)
        print()
        print(f"Error: Simulation failed with exit code {e.returncode}")
        return e.returncode
    
    except FileNotFoundError:
        print("-" * 60)
        print()
        print("Error: Python interpreter not found")
        return 1


def show_alternative_approach():
    """Show alternative approach using Python API directly."""
    
    print("\n" + "=" * 60)
    print("Alternative: Using Python API Directly")
    print("=" * 60)
    print()
    print("You can also process BFF traces programmatically:")
    print()
    print("```python")
    print("from m_inc.adapters.bff_bridge import stream_bff_to_minc")
    print("from m_inc.core.economic_engine import EconomicEngine")
    print()
    print("# Stream BFF trace data")
    print("for epoch in stream_bff_to_minc('trace.bin'):")
    print("    # Process with M|inc")
    print("    result = engine.process_tick(epoch.epoch_num)")
    print("    print(f'Tick {result.tick_num}: {result.metrics.wealth_total}')")
    print("```")
    print()


if __name__ == "__main__":
    exit_code = main()
    
    if exit_code == 0:
        show_alternative_approach()
    
    sys.exit(exit_code)
