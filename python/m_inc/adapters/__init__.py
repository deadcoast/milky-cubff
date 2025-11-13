"""Adapters for interfacing with BFF traces and external systems."""

from .trace_reader import TraceReader, EpochData
from .trace_normalizer import TraceNormalizer, load_and_normalize_trace
from .output_writer import OutputWriter, StreamingOutputWriter, create_output_writer, generate_metadata

__all__ = [
    "TraceReader",
    "EpochData",
    "TraceNormalizer",
    "load_and_normalize_trace",
    "OutputWriter",
    "StreamingOutputWriter",
    "create_output_writer",
    "generate_metadata",
]
