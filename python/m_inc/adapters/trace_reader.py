"""Trace reader for BFF soup data."""

import json
import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union, Iterator, Tuple
import sys


@dataclass
class EpochData:
    """Data from a single BFF epoch.
    
    An epoch represents one complete cycle of BFF soup pairwise interactions.
    """
    epoch_num: int
    tapes: Dict[int, bytearray]  # tape_id -> 64-byte program
    interactions: List[Tuple[int, int]]  # (tape_a_id, tape_b_id) pairs
    metrics: Dict[str, float]  # entropy, compression, etc.
    
    def get_tape(self, tape_id: int) -> Optional[bytearray]:
        """Get a tape by ID.
        
        Args:
            tape_id: Tape identifier
            
        Returns:
            64-byte tape or None if not found
        """
        return self.tapes.get(tape_id)
    
    def get_population(self) -> List[bytearray]:
        """Get all tapes as a list.
        
        Returns:
            List of all 64-byte tapes
        """
        return list(self.tapes.values())
    
    def num_tapes(self) -> int:
        """Get number of tapes in this epoch."""
        return len(self.tapes)


class TraceReader:
    """Reader for BFF trace files and streams.
    
    Supports multiple formats:
    - JSON files (plain or gzipped)
    - Binary trace files
    - Streaming input from stdin
    """
    
    def __init__(self, source: Union[Path, str, None] = None):
        """Initialize trace reader.
        
        Args:
            source: Path to trace file, or None for stdin
        """
        self.source = Path(source) if source else None
        self.current_epoch = 0
        self._file_handle = None
        self._is_stream = source is None
        self._format = None
        
        if self.source and self.source.exists():
            self._detect_format()
    
    def _detect_format(self) -> None:
        """Detect the format of the trace file."""
        if not self.source:
            self._format = "stream"
            return
        
        suffix = self.source.suffix.lower()
        if suffix == ".gz":
            self._format = "json_gz"
        elif suffix == ".json":
            self._format = "json"
        elif suffix == ".bin":
            self._format = "binary"
        else:
            # Try to detect by reading first bytes
            with open(self.source, 'rb') as f:
                header = f.read(2)
                if header == b'\x1f\x8b':  # gzip magic number
                    self._format = "json_gz"
                elif header[0:1] == b'{':  # JSON starts with {
                    self._format = "json"
                else:
                    self._format = "binary"
    
    def read_epoch(self) -> Optional[EpochData]:
        """Read the next epoch from the trace.
        
        Returns:
            EpochData for the next epoch, or None if end of trace
        """
        if self._format == "json" or self._format == "json_gz":
            return self._read_epoch_json()
        elif self._format == "binary":
            return self._read_epoch_binary()
        elif self._format == "stream":
            return self._read_epoch_stream()
        else:
            raise ValueError(f"Unknown format: {self._format}")
    
    def _read_epoch_json(self) -> Optional[EpochData]:
        """Read epoch from JSON file."""
        if not self._file_handle:
            if self._format == "json_gz":
                self._file_handle = gzip.open(self.source, 'rt', encoding='utf-8')
            else:
                self._file_handle = open(self.source, 'r', encoding='utf-8')
            
            # Load entire JSON (could be single object or array)
            try:
                data = json.load(self._file_handle)
                self._file_handle.close()
                self._file_handle = None
                
                # Store data for iteration
                if isinstance(data, list):
                    self._json_data = data
                    self._json_index = 0
                else:
                    self._json_data = [data]
                    self._json_index = 0
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in trace file: {e}")
        
        # Return next epoch from loaded data
        if hasattr(self, '_json_data') and self._json_index < len(self._json_data):
            epoch_data = self._json_data[self._json_index]
            self._json_index += 1
            return self._parse_json_epoch(epoch_data)
        
        return None
    
    def _parse_json_epoch(self, data: Dict) -> EpochData:
        """Parse a single epoch from JSON data.
        
        Expected format:
        {
            "epoch": 1,
            "tapes": {"0": "hex_string", "1": "hex_string", ...},
            "interactions": [[0, 1], [2, 3], ...],
            "metrics": {"entropy": 5.91, "compression_ratio": 2.70, ...}
        }
        """
        epoch_num = data.get("epoch", self.current_epoch)
        self.current_epoch = epoch_num + 1
        
        # Parse tapes
        tapes = {}
        tapes_data = data.get("tapes", {})
        if isinstance(tapes_data, dict):
            for tape_id_str, tape_hex in tapes_data.items():
                tape_id = int(tape_id_str)
                tapes[tape_id] = bytearray.fromhex(tape_hex)
        elif isinstance(tapes_data, list):
            # List format: each element is a tape
            for tape_id, tape_hex in enumerate(tapes_data):
                tapes[tape_id] = bytearray.fromhex(tape_hex)
        
        # Parse interactions
        interactions = []
        interactions_data = data.get("interactions", [])
        for pair in interactions_data:
            if isinstance(pair, list) and len(pair) == 2:
                interactions.append((pair[0], pair[1]))
        
        # Parse metrics
        metrics = data.get("metrics", {})
        
        return EpochData(
            epoch_num=epoch_num,
            tapes=tapes,
            interactions=interactions,
            metrics=metrics
        )
    
    def _read_epoch_binary(self) -> Optional[EpochData]:
        """Read epoch from binary file.
        
        Binary format (simplified):
        - 4 bytes: epoch number (uint32)
        - 4 bytes: number of tapes (uint32)
        - For each tape:
          - 4 bytes: tape_id (uint32)
          - 64 bytes: tape data
        - 4 bytes: number of interactions (uint32)
        - For each interaction:
          - 4 bytes: tape_a_id (uint32)
          - 4 bytes: tape_b_id (uint32)
        """
        if not self._file_handle:
            self._file_handle = open(self.source, 'rb')
        
        # Read epoch number
        epoch_bytes = self._file_handle.read(4)
        if not epoch_bytes or len(epoch_bytes) < 4:
            self._file_handle.close()
            return None
        
        epoch_num = int.from_bytes(epoch_bytes, byteorder='little')
        
        # Read number of tapes
        num_tapes_bytes = self._file_handle.read(4)
        if len(num_tapes_bytes) < 4:
            self._file_handle.close()
            return None
        num_tapes = int.from_bytes(num_tapes_bytes, byteorder='little')
        
        # Read tapes
        tapes = {}
        for _ in range(num_tapes):
            tape_id_bytes = self._file_handle.read(4)
            tape_data = self._file_handle.read(64)
            if len(tape_id_bytes) < 4 or len(tape_data) < 64:
                break
            tape_id = int.from_bytes(tape_id_bytes, byteorder='little')
            tapes[tape_id] = bytearray(tape_data)
        
        # Read number of interactions
        num_interactions_bytes = self._file_handle.read(4)
        if len(num_interactions_bytes) < 4:
            num_interactions = 0
        else:
            num_interactions = int.from_bytes(num_interactions_bytes, byteorder='little')
        
        # Read interactions
        interactions = []
        for _ in range(num_interactions):
            a_bytes = self._file_handle.read(4)
            b_bytes = self._file_handle.read(4)
            if len(a_bytes) < 4 or len(b_bytes) < 4:
                break
            a_id = int.from_bytes(a_bytes, byteorder='little')
            b_id = int.from_bytes(b_bytes, byteorder='little')
            interactions.append((a_id, b_id))
        
        self.current_epoch = epoch_num + 1
        
        return EpochData(
            epoch_num=epoch_num,
            tapes=tapes,
            interactions=interactions,
            metrics={}
        )
    
    def _read_epoch_stream(self) -> Optional[EpochData]:
        """Read epoch from stdin stream.
        
        Expects JSON lines format: one JSON object per line.
        """
        try:
            line = sys.stdin.readline()
            if not line:
                return None
            
            data = json.loads(line.strip())
            return self._parse_json_epoch(data)
        except json.JSONDecodeError:
            return None
        except EOFError:
            return None
    
    def read_all_epochs(self) -> Iterator[EpochData]:
        """Read all epochs from the trace.
        
        Yields:
            EpochData for each epoch in the trace
        """
        while True:
            epoch = self.read_epoch()
            if epoch is None:
                break
            yield epoch
    
    def get_tape_by_id(self, tape_id: int, epoch: Optional[EpochData] = None) -> Optional[bytearray]:
        """Get a specific tape by ID.
        
        Args:
            tape_id: Tape identifier
            epoch: EpochData to search in (if None, reads next epoch)
            
        Returns:
            64-byte tape or None if not found
        """
        if epoch is None:
            epoch = self.read_epoch()
            if epoch is None:
                return None
        
        return epoch.get_tape(tape_id)
    
    def get_population_snapshot(self, epoch: Optional[EpochData] = None) -> List[bytearray]:
        """Get all tapes as a population snapshot.
        
        Args:
            epoch: EpochData to get population from (if None, reads next epoch)
            
        Returns:
            List of all 64-byte tapes
        """
        if epoch is None:
            epoch = self.read_epoch()
            if epoch is None:
                return []
        
        return epoch.get_population()
    
    def close(self) -> None:
        """Close the trace reader and any open file handles."""
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


def create_sample_trace(output_path: Path, num_epochs: int = 10, num_tapes: int = 100) -> None:
    """Create a sample trace file for testing.
    
    Args:
        output_path: Path to write sample trace
        num_epochs: Number of epochs to generate
        num_tapes: Number of tapes per epoch
    """
    import random
    
    epochs = []
    for epoch_num in range(num_epochs):
        # Generate random tapes
        tapes = {}
        for tape_id in range(num_tapes):
            tape = bytearray(random.randint(0, 255) for _ in range(64))
            tapes[tape_id] = tape.hex()
        
        # Generate random interactions
        interactions = []
        for _ in range(num_tapes // 2):
            a = random.randint(0, num_tapes - 1)
            b = random.randint(0, num_tapes - 1)
            if a != b:
                interactions.append([a, b])
        
        # Generate sample metrics
        metrics = {
            "entropy": 6.0 - (epoch_num * 0.05),
            "compression_ratio": 2.5 + (epoch_num * 0.05),
            "copy_score_mean": 0.5 + (epoch_num * 0.02)
        }
        
        epochs.append({
            "epoch": epoch_num,
            "tapes": tapes,
            "interactions": interactions,
            "metrics": metrics
        })
    
    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.suffix == ".gz":
        with gzip.open(output_path, 'wt', encoding='utf-8') as f:
            json.dump(epochs, f, indent=2)
    else:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(epochs, f, indent=2)
