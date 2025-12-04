"""Adapters for interfacing with BFF traces and external systems.

Available adapters:
- TraceReader: Read BFF trace files (JSON, binary, gzipped)
- BFFBridge: Convert CuBFF binary traces to EpochData
- BFFxBridge: Convert live BFFx Soup simulation to EpochData
- TraceNormalizer: Normalize trace formats
- OutputWriter: Write M|inc results to files
"""

from .trace_reader import TraceReader, EpochData
from .trace_normalizer import TraceNormalizer, load_and_normalize_trace
from .output_writer import OutputWriter, StreamingOutputWriter, create_output_writer, generate_metadata
from .bff_bridge import BFFBridge, convert_bff_trace_to_json, stream_bff_to_minc

# BFFx bridge is optional (requires bffx package to be available)
try:
    from .bffx_bridge import (
        BFFxBridge,
        stream_bffx_to_minc,
        create_bffx_to_minc_runner
    )
    _BFFX_AVAILABLE = True
except ImportError:
    _BFFX_AVAILABLE = False
    BFFxBridge = None
    stream_bffx_to_minc = None
    create_bffx_to_minc_runner = None


def bffx_available() -> bool:
    """Check if BFFx integration is available."""
    return _BFFX_AVAILABLE


__all__ = [
    # Core trace handling
    "TraceReader",
    "EpochData",
    "TraceNormalizer",
    "load_and_normalize_trace",
    # Output writing
    "OutputWriter",
    "StreamingOutputWriter",
    "create_output_writer",
    "generate_metadata",
    # CuBFF binary bridge
    "BFFBridge",
    "convert_bff_trace_to_json",
    "stream_bff_to_minc",
    # BFFx live bridge (optional)
    "BFFxBridge",
    "stream_bffx_to_minc",
    "create_bffx_to_minc_runner",
    "bffx_available",
]
