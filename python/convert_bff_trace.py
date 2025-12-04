#!/usr/bin/env python3
"""Simple script to convert BFF binary traces to JSON format.

This is a standalone utility that doesn't require the m_inc package to be installed.
"""

import struct
import json
import sys
from pathlib import Path
from typing import Optional


def convert_bff_trace_to_json(bff_trace_path: Path, json_output_path: Path,
                               num_states: Optional[int] = None) -> bool:
    """Convert BFF binary trace to JSON format.
    
    Args:
        bff_trace_path: Path to BFF binary trace
        json_output_path: Path to write JSON output
        num_states: Number of states to convert (None for all)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(bff_trace_path, 'rb') as f:
            # Read header
            magic = f.read(4)
            if magic != b'BFF\0':
                print(f"Error: Invalid BFF trace format", file=sys.stderr)
                return False
            
            version = struct.unpack('<I', f.read(4))[0]
            if version != 1:
                print(f"Error: Unsupported version {version}", file=sys.stderr)
                return False
            
            tape_size = struct.unpack('<I', f.read(4))[0]
            if tape_size != 128:
                print(f"Error: Unexpected tape size {tape_size}", file=sys.stderr)
                return False
            
            # Read states
            epochs = []
            state_count = 0
            
            while True:
                if num_states is not None and state_count >= num_states:
                    break
                
                # Read state
                pc_bytes = f.read(4)
                if not pc_bytes or len(pc_bytes) < 4:
                    break
                
                pc = struct.unpack('<I', pc_bytes)[0]
                head0 = struct.unpack('<I', f.read(4))[0]
                head1 = struct.unpack('<I', f.read(4))[0]
                tape = f.read(tape_size)
                
                if len(tape) < tape_size:
                    break
                
                # Split into two 64-byte tapes
                tape0 = tape[:64]
                tape1 = tape[64:]
                
                # Create epoch
                epoch = {
                    "epoch": state_count,
                    "tapes": {
                        "0": tape0.hex(),
                        "1": tape1.hex()
                    },
                    "interactions": [[0, 1]],
                    "metrics": {
                        "pc": float(pc),
                        "head0": float(head0),
                        "head1": float(head1),
                        "state_num": float(state_count)
                    }
                }
                
                epochs.append(epoch)
                state_count += 1
            
            # Write JSON
            json_output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_output_path, 'w') as out:
                json.dump(epochs, out, indent=2)
            
            print(f"Converted {state_count} states to {json_output_path}")
            return True
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python convert_bff_trace.py <input.bff> <output.json> [num_states]")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    num_states = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    success = convert_bff_trace_to_json(input_path, output_path, num_states)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
