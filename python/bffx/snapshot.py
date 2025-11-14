"""
Snapshot management for BFF populations.

Provides functions to save and load population states to/from compressed JSON files.
This enables checkpointing experiments and sharing results.
"""

import gzip
import json
from typing import Any, Dict, List, Optional


def save_population_json_gz(
    path: str,
    population: List[bytearray],
    meta: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save a population to a gzip-compressed JSON file.
    
    Args:
        path: File path to write to (should end with .json.gz)
        population: List of 64-byte programs
        meta: Optional metadata dictionary to include in the snapshot
        
    The file format is:
    {
        "meta": {...},  # Optional metadata
        "programs_hex": ["3e3e2b...", "5b2d5d...", ...]  # Hex-encoded programs
    }
    """
    # Convert programs to hex strings
    programs_hex = [prog.hex() for prog in population]
    
    # Create JSON payload
    payload = {
        "programs_hex": programs_hex
    }
    
    # Add metadata if provided
    if meta is not None:
        payload["meta"] = meta
    
    # Write to gzip-compressed file
    with gzip.open(path, 'wt', encoding='utf-8') as f:
        json.dump(payload, f)


def load_population_json_gz(path: str) -> tuple[list[bytearray], dict]:
    """
    Load a population from a gzip-compressed JSON file.
    
    Args:
        path: File path to read from
        
    Returns:
        Tuple of (programs, metadata) where:
        - programs: List of 64-byte bytearrays
        - metadata: Dictionary of metadata (empty dict if no metadata in file)
        
    Raises:
        ValueError: If any program is not exactly 64 bytes
        KeyError: If programs_hex field is missing
    """
    # Read gzip-compressed JSON file
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        payload = json.load(f)
    
    # Parse programs_hex and convert from hex to bytearray
    programs_hex = payload["programs_hex"]
    programs = []
    
    for hex_str in programs_hex:
        prog = bytearray.fromhex(hex_str)
        
        # Validate all programs are exactly 64 bytes
        if len(prog) != 64:
            raise ValueError(f"Invalid program size: {len(prog)} bytes (expected 64)")
        
        programs.append(prog)
    
    # Extract metadata (default to empty dict if not present)
    metadata = payload.get("meta", {})
    
    return (programs, metadata)
