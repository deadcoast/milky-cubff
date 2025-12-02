#!/usr/bin/env python3
"""Wrapper script to run M|inc on BFF simulation output.

This script provides integration between BFF simulations and M|inc economic analysis.
It can:
1. Run a BFF simulation and pipe output to M|inc
2. Convert existing BFF binary traces to M|inc format
3. Process BFF traces with M|inc analysis

Usage:
    # Run BFF simulation and analyze with M|inc
    python run_minc_on_bff.py --bff-program testdata/bff.txt --config m_inc/config/minc_default.yaml --output output/

    # Convert existing BFF trace to JSON
    python run_minc_on_bff.py --convert bff_trace.bin --output trace.json

    # Process existing BFF trace with M|inc
    python run_minc_on_bff.py --bff-trace bff_trace.bin --config m_inc/config/minc_default.yaml --output output/
"""

import argparse
import subprocess
import sys
import tempfile
import logging
from pathlib import Path
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_bff_simulation(bff_program_path: Path, output_trace_path: Path, 
                       max_steps: int = 128 * 1024) -> bool:
    """Run BFF simulation using save_bff_trace.py.
    
    Args:
        bff_program_path: Path to BFF program file
        output_trace_path: Path to write trace output
        max_steps: Maximum number of steps to execute
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Running BFF simulation on {bff_program_path}")
        
        # Find save_bff_trace.py
        save_script = Path(__file__).parent / "save_bff_trace.py"
        if not save_script.exists():
            logger.error(f"save_bff_trace.py not found at {save_script}")
            return False
        
        # Run save_bff_trace.py
        cmd = [
            sys.executable,
            str(save_script),
            str(bff_program_path),
            str(output_trace_path)
        ]
        
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"BFF simulation failed: {result.stderr}")
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
            return False
        
        logger.info(f"BFF simulation completed, trace saved to {output_trace_path}")
        if result.stdout:
            logger.debug(f"Output: {result.stdout}")
        return True
    
    except Exception as e:
        logger.error(f"Error running BFF simulation: {e}")
        return False


def convert_bff_to_json_format(bff_trace_path: Path, json_output_path: Path,
                                num_states: Optional[int] = None) -> bool:
    """Convert BFF binary trace to JSON format using standalone converter.
    
    Args:
        bff_trace_path: Path to BFF binary trace
        json_output_path: Path to write JSON output
        num_states: Number of states to convert (None for all)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Converting BFF trace {bff_trace_path} to JSON")
        
        # Use standalone converter script
        converter_script = Path(__file__).parent / "convert_bff_trace.py"
        if not converter_script.exists():
            logger.error(f"Converter script not found: {converter_script}")
            return False
        
        cmd = [
            sys.executable,
            str(converter_script),
            str(bff_trace_path),
            str(json_output_path)
        ]
        
        if num_states is not None:
            cmd.append(str(num_states))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Conversion failed: {result.stderr}")
            return False
        
        if result.stdout:
            logger.info(result.stdout.strip())
        
        return True
    
    except Exception as e:
        logger.error(f"Error converting BFF trace: {e}")
        return False


def process_bff_with_minc(bff_trace_path: Path, config_path: Path, 
                          output_dir: Path, num_ticks: int,
                          verbose: bool = False) -> dict:
    """Process BFF trace with M|inc analysis.
    
    Args:
        bff_trace_path: Path to BFF binary trace
        config_path: Path to M|inc configuration
        output_dir: Output directory for M|inc results
        num_ticks: Number of ticks to process
        verbose: Enable verbose logging
        
    Returns:
        Dict with processing results
    """
    try:
        # Convert BFF trace to JSON format in temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json_trace_path = Path(tmp.name)
        
        logger.info(f"Converting BFF trace to JSON format")
        if not convert_bff_to_json_format(bff_trace_path, json_trace_path, num_states=num_ticks):
            return {"success": False, "error": "Failed to convert BFF trace"}
        
        # Run M|inc CLI
        logger.info(f"Processing with M|inc (ticks={num_ticks})")
        
        cli_script = Path(__file__).parent / "m_inc" / "cli.py"
        cmd = [
            sys.executable,
            str(cli_script),
            '--trace', str(json_trace_path),
            '--config', str(config_path),
            '--output', str(output_dir),
            '--ticks', str(num_ticks)
        ]
        
        if verbose:
            cmd.append('--verbose')
        
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp file
        json_trace_path.unlink()
        
        if result.returncode != 0:
            logger.error(f"M|inc processing failed: {result.stderr}")
            return {"success": False, "error": result.stderr}
        
        logger.info("M|inc processing completed successfully")
        if result.stdout:
            logger.info(f"Output: {result.stdout}")
        
        return {"success": True, "output": result.stdout}
    
    except Exception as e:
        logger.error(f"Error processing BFF trace with M|inc: {e}")
        return {"success": False, "error": str(e)}


def run_bff_and_analyze(bff_program_path: Path, config_path: Path,
                       output_dir: Path, num_ticks: int,
                       verbose: bool = False) -> dict:
    """Run BFF simulation and analyze with M|inc.
    
    Args:
        bff_program_path: Path to BFF program file
        config_path: Path to M|inc configuration
        output_dir: Output directory for results
        num_ticks: Number of ticks to process
        verbose: Enable verbose logging
        
    Returns:
        Dict with processing results
    """
    try:
        # Create temp file for BFF trace
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bff', delete=False) as tmp:
            bff_trace_path = Path(tmp.name)
        
        # Run BFF simulation
        if not run_bff_simulation(bff_program_path, bff_trace_path):
            return {"success": False, "error": "BFF simulation failed"}
        
        # Process with M|inc
        result = process_bff_with_minc(
            bff_trace_path=bff_trace_path,
            config_path=config_path,
            output_dir=output_dir,
            num_ticks=num_ticks,
            verbose=verbose
        )
        
        # Clean up temp file
        bff_trace_path.unlink()
        
        return result
    
    except Exception as e:
        logger.error(f"Error in run_bff_and_analyze: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Main entry point for the wrapper script."""
    parser = argparse.ArgumentParser(
        description="Run M|inc on BFF simulation output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run BFF simulation and analyze with M|inc
  %(prog)s --bff-program testdata/bff.txt --config m_inc/config/minc_default.yaml --output output/

  # Convert existing BFF trace to JSON
  %(prog)s --convert bff_trace.bin --output trace.json

  # Process existing BFF trace with M|inc
  %(prog)s --bff-trace bff_trace.bin --config m_inc/config/minc_default.yaml --output output/
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--bff-program',
        type=Path,
        help='Path to BFF program file (runs simulation then analyzes)'
    )
    mode_group.add_argument(
        '--bff-trace',
        type=Path,
        help='Path to existing BFF binary trace (analyzes only)'
    )
    mode_group.add_argument(
        '--convert',
        type=Path,
        help='Path to BFF trace to convert to JSON (conversion only)'
    )
    
    # Common arguments
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to M|inc configuration YAML (required for analysis modes)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output directory for M|inc results or JSON file for conversion'
    )
    parser.add_argument(
        '--ticks',
        type=int,
        default=100,
        help='Number of ticks to process (default: 100)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Execute based on mode
    if args.convert:
        # Conversion mode
        if not args.convert.exists():
            logger.error(f"BFF trace not found: {args.convert}")
            sys.exit(1)
        
        success = convert_bff_to_json_format(args.convert, args.output)
        sys.exit(0 if success else 1)
    
    elif args.bff_program:
        # Run simulation and analyze
        if not args.config:
            logger.error("--config is required when using --bff-program")
            sys.exit(1)
        
        if not args.bff_program.exists():
            logger.error(f"BFF program not found: {args.bff_program}")
            sys.exit(1)
        
        if not args.config.exists():
            logger.error(f"Config file not found: {args.config}")
            sys.exit(1)
        
        result = run_bff_and_analyze(
            bff_program_path=args.bff_program,
            config_path=args.config,
            output_dir=args.output,
            num_ticks=args.ticks,
            verbose=args.verbose
        )
        
        if result['success']:
            logger.info("Processing completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    elif args.bff_trace:
        # Analyze existing trace
        if not args.config:
            logger.error("--config is required when using --bff-trace")
            sys.exit(1)
        
        if not args.bff_trace.exists():
            logger.error(f"BFF trace not found: {args.bff_trace}")
            sys.exit(1)
        
        if not args.config.exists():
            logger.error(f"Config file not found: {args.config}")
            sys.exit(1)
        
        result = process_bff_with_minc(
            bff_trace_path=args.bff_trace,
            config_path=args.config,
            output_dir=args.output,
            num_ticks=args.ticks,
            verbose=args.verbose
        )
        
        if result['success']:
            logger.info("Processing completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == '__main__':
    main()
