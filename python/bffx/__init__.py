"""
BFF eXtended (bffx) - Digital Abiogenesis Simulation Framework

This package implements the core BFF (Brainfuck-variant) Virtual Machine
that demonstrates digital abiogenesis - the emergence of self-replicating
programs from random bytes through simple interactions.

Core Components:
- vm: BFF Virtual Machine with self-modification support
- soup: Population management and evolution
- scheduler: Program pairing algorithms
- analytics: Entropy, compression, and diversity metrics
- detectors: Replication event detection
- snapshot: Population save/load functionality
- assay: Replicator testing protocol
- cli: Command-line interface for experiments
"""

# Core constants
PROGRAM_SIZE = 64        # Bytes per program
TAPE_SIZE = 128          # Bytes per tape (2 programs concatenated)
DEFAULT_STEP_LIMIT = 8192  # Max instructions per interaction

__version__ = "0.1.1"

__all__ = [
    "PROGRAM_SIZE",
    "TAPE_SIZE",
    "DEFAULT_STEP_LIMIT",
]
