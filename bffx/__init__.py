"""BFFX - Complete BFF VM implementation with economic layer integration."""

__version__ = "0.1.1"

from .vm import BFFVM, RunResult, HaltReason
from .soup import Soup, PairOutcome
from .scheduler import random_disjoint_pairs
from .analytics import shannon_entropy_bits, compress_ratio, opcode_histogram, top_programs
from .detectors import detect_exact_replication, ReplicationEvent
from .snapshot import save_population_json_gz, load_population_json_gz
from .assay import assay_candidate

__all__ = [
    "BFFVM",
    "RunResult",
    "HaltReason",
    "Soup",
    "PairOutcome",
    "random_disjoint_pairs",
    "shannon_entropy_bits",
    "compress_ratio",
    "opcode_histogram",
    "top_programs",
    "detect_exact_replication",
    "ReplicationEvent",
    "save_population_json_gz",
    "load_population_json_gz",
    "assay_candidate",
]
