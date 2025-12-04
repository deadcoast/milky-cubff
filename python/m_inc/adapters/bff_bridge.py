"""Bridge adapter for BFF trace integration.

This module provides functionality to parse output from save_bff_trace.py
and convert BFF soup format to M|inc EpochData format.
"""

import struct
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Iterator
import sys

from .trace_reader import EpochData


class BFFBridge:
    """Bridge between BFF binary trace format and M|inc EpochData.
    
    This adapter reads the binary format produced by save_bff_trace.py
    (via bff_interpreter.py's evaluate_and_save function) and converts
    it to EpochData objects that M|inc can process.
    
    The BFF binary format is:
    - 4-byte magic number ('BFF\0')
    - 4-byte format version (1)
    - 4-byte tape size (128 bytes)
    - For each state:
      - 4-byte PC position
      - 4-byte head0 position
      - 4-byte head1 position
      - Tape contents (128 bytes)
    """
    
    MAGIC_NUMBER = b'BFF\0'
    EXPECTED_VERSION = 1
    TAPE_SIZE = 128  # Full tape size (2 * 64)
    SINGLE_TAPE_SIZE = 64  # Individual tape size
    
    def __init__(self, source: Union[Path, str, None] = None):
        """Initialize BFF bridge.
        
        Args:
            source: Path to BFF binary trace file, or None for stdin
        """
        self.source = Path(source) if source else None
        self._file_handle = None
        self._is_stream = source is None
        self._header_read = False
        self._tape_size = None
        self._state_count = 0
    
    def _read_header(self) -> None:
        """Read and validate the BFF trace file header."""
        if self._header_read:
            return
        
        if self._is_stream:
            f = sys.stdin.buffer
        else:
            if not self._file_handle:
                self._file_handle = open(self.source, 'rb')
            f = self._file_handle
        
        # Read magic number
        magic = f.read(4)
        if magic != self.MAGIC_NUMBER:
            raise ValueError(f"Invalid BFF trace format: Expected {self.MAGIC_NUMBER}, got {magic}")
        
        # Read version
        version_bytes = f.read(4)
        if len(version_bytes) < 4:
            raise ValueError("Incomplete header: missing version")
        version = struct.unpack('<I', version_bytes)[0]
        if version != self.EXPECTED_VERSION:
            raise ValueError(f"Unsupported BFF trace version: {version}, expected {self.EXPECTED_VERSION}")
        
        # Read tape size
        tape_size_bytes = f.read(4)
        if len(tape_size_bytes) < 4:
            raise ValueError("Incomplete header: missing tape size")
        self._tape_size = struct.unpack('<I', tape_size_bytes)[0]
        if self._tape_size != self.TAPE_SIZE:
            raise ValueError(f"Unexpected tape size: {self._tape_size}, expected {self.TAPE_SIZE}")
        
        self._header_read = True
    
    def _read_state(self) -> Optional[Tuple[int, int, int, bytearray]]:
        """Read a single BFF state from the trace.
        
        Returns:
            Tuple of (pc, head0, head1, tape) or None if end of file
        """
        if not self._header_read:
            self._read_header()
        
        if self._is_stream:
            f = sys.stdin.buffer
        else:
            f = self._file_handle
        
        # Read program counter
        pc_bytes = f.read(4)
        if not pc_bytes or len(pc_bytes) < 4:
            return None
        
        pc = struct.unpack('<I', pc_bytes)[0]
        
        # Read head positions
        head0_bytes = f.read(4)
        head1_bytes = f.read(4)
        if len(head0_bytes) < 4 or len(head1_bytes) < 4:
            return None
        
        head0 = struct.unpack('<I', head0_bytes)[0]
        head1 = struct.unpack('<I', head1_bytes)[0]
        
        # Read tape contents
        tape_bytes = f.read(self._tape_size)
        if len(tape_bytes) < self._tape_size:
            return None
        
        tape = bytearray(tape_bytes)
        
        return pc, head0, head1, tape
    
    def read_state_as_epoch(self) -> Optional[EpochData]:
        """Read a single BFF state and convert to EpochData.
        
        Each BFF state is treated as an epoch with two tapes:
        - Tape 0: First 64 bytes
        - Tape 1: Last 64 bytes
        
        Returns:
            EpochData with two tapes, or None if end of trace
        """
        state = self._read_state()
        if state is None:
            return None
        
        pc, head0, head1, tape = state
        
        # Split the 128-byte tape into two 64-byte tapes
        tape0 = bytearray(tape[:self.SINGLE_TAPE_SIZE])
        tape1 = bytearray(tape[self.SINGLE_TAPE_SIZE:])
        
        # Create tapes dictionary
        tapes = {
            0: tape0,
            1: tape1
        }
        
        # Create interaction representing the two tapes working together
        interactions = [(0, 1)]
        
        # Create metrics from state information
        metrics = {
            "pc": float(pc),
            "head0": float(head0),
            "head1": float(head1),
            "state_num": float(self._state_count)
        }
        
        epoch_data = EpochData(
            epoch_num=self._state_count,
            tapes=tapes,
            interactions=interactions,
            metrics=metrics
        )
        
        self._state_count += 1
        return epoch_data
    
    def read_all_states_as_epochs(self) -> Iterator[EpochData]:
        """Read all BFF states and yield as EpochData objects.
        
        Yields:
            EpochData for each state in the trace
        """
        while True:
            epoch = self.read_state_as_epoch()
            if epoch is None:
                break
            yield epoch
    
    def convert_to_soup_format(self, num_states: Optional[int] = None) -> List[EpochData]:
        """Convert BFF trace to soup-style format.
        
        In soup format, we aggregate multiple states into epochs where
        each epoch represents a collection of tape snapshots.
        
        Args:
            num_states: Number of states to read (None for all)
        
        Returns:
            List of EpochData objects
        """
        epochs = []
        count = 0
        
        for epoch in self.read_all_states_as_epochs():
            epochs.append(epoch)
            count += 1
            if num_states is not None and count >= num_states:
                break
        
        return epochs
    
    def close(self) -> None:
        """Close the bridge and any open file handles."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def convert_bff_trace_to_json(bff_trace_path: Union[Path, str], 
                               output_path: Union[Path, str],
                               num_states: Optional[int] = None) -> None:
    """Convert a BFF binary trace to JSON format for M|inc.
    
    This is a convenience function for converting BFF traces to the
    JSON format that M|inc's TraceReader can consume.
    
    Args:
        bff_trace_path: Path to BFF binary trace file
        output_path: Path to write JSON output
        num_states: Number of states to convert (None for all)
    """
    import json
    
    bridge = BFFBridge(bff_trace_path)
    epochs = bridge.convert_to_soup_format(num_states)
    bridge.close()
    
    # Convert to JSON-serializable format
    json_data = []
    for epoch in epochs:
        json_epoch = {
            "epoch": epoch.epoch_num,
            "tapes": {str(k): v.hex() for k, v in epoch.tapes.items()},
            "interactions": list(epoch.interactions),
            "metrics": epoch.metrics
        }
        json_data.append(json_epoch)
    
    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)


def stream_bff_to_minc(bff_trace_path: Optional[Union[Path, str]] = None) -> Iterator[EpochData]:
    """Stream BFF trace data for M|inc processing.
    
    This function provides a streaming interface for processing BFF traces
    without loading the entire trace into memory.
    
    Args:
        bff_trace_path: Path to BFF binary trace file, or None for stdin
    
    Yields:
        EpochData objects for M|inc processing
    """
    with BFFBridge(bff_trace_path) as bridge:
        yield from bridge.read_all_states_as_epochs()
