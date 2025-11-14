"""
Analytics module for BFF population metrics.

Provides functions to detect the entropy drop that signals emergence of self-replicators.
"""

import math
import zlib
from collections import Counter
from typing import List, Tuple


def shannon_entropy_bits(population: List[bytearray]) -> float:
    """
    Calculate Shannon entropy in bits for the population byte distribution.
    
    High entropy (~7-8 bits) indicates random soup.
    Low entropy indicates structured, self-replicating population.
    
    Args:
        population: List of programs (each 64 bytes)
        
    Returns:
        Shannon entropy in bits: -Σ(p * log2(p))
    """
    # Concatenate all programs into single byte sequence
    all_bytes = b''.join(bytes(prog) for prog in population)
    
    if not all_bytes:
        return 0.0
    
    # Count byte frequencies
    byte_counts = Counter(all_bytes)
    total = len(all_bytes)
    
    # Calculate Shannon entropy: -Σ(p * log2(p))
    entropy = 0.0
    for count in byte_counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    
    return entropy


def compress_ratio(population: List[bytearray]) -> float:
    """
    Calculate compression ratio using zlib level 9 compression.
    
    Near 1.0 for random soup (incompressible).
    Lower values (better compression) indicate structured population.
    
    Args:
        population: List of programs (each 64 bytes)
        
    Returns:
        Ratio: compressed_size / original_size
    """
    # Concatenate all programs into single byte sequence
    all_bytes = b''.join(bytes(prog) for prog in population)
    
    if not all_bytes:
        return 1.0
    
    # Compress using zlib level 9
    compressed = zlib.compress(all_bytes, level=9)
    
    # Return compressed_size / original_size ratio
    return len(compressed) / len(all_bytes)


def opcode_histogram(population: List[bytearray]) -> Counter:
    """
    Generate opcode histogram counting each of the 10 valid opcodes.
    
    Valid opcodes: ><+-{}.,[]
    
    Args:
        population: List of programs (each 64 bytes)
        
    Returns:
        Counter object with opcode counts
    """
    # Define the 10 valid opcodes
    valid_opcodes = {
        ord('>'): '>',
        ord('<'): '<',
        ord('+'): '+',
        ord('-'): '-',
        ord('{'): '{',
        ord('}'): '}',
        ord('.'): '.',
        ord(','): ',',
        ord('['): '[',
        ord(']'): ']'
    }
    
    # Count occurrences of each opcode
    opcode_counts = Counter()
    
    for program in population:
        for byte in program:
            if byte in valid_opcodes:
                opcode_counts[valid_opcodes[byte]] += 1
    
    return opcode_counts


def top_programs(population: List[bytearray], k: int = 5) -> List[Tuple[bytes, int]]:
    """
    Identify the top K most common programs with their counts.
    
    Shows dominance of successful replicators.
    
    Args:
        population: List of programs (each 64 bytes)
        k: Number of top programs to return (default 5)
        
    Returns:
        List of (program, count) tuples, sorted by count descending
    """
    # Convert programs to bytes for hashing
    program_counts = Counter(bytes(prog) for prog in population)
    
    # Return most_common(k) as list of (program, count) tuples
    return program_counts.most_common(k)


def hamming(a: bytes, b: bytes) -> int:
    """
    Calculate Hamming distance between two byte sequences.
    
    Counts the number of positions where bytes differ.
    
    Args:
        a: First byte sequence
        b: Second byte sequence
        
    Returns:
        Number of positions where bytes differ
        
    Raises:
        ValueError: If inputs have different lengths
    """
    # Validate both inputs have same length
    if len(a) != len(b):
        raise ValueError(f"Inputs must have same length: {len(a)} != {len(b)}")
    
    # Count positions where bytes differ
    return sum(byte_a != byte_b for byte_a, byte_b in zip(a, b))
