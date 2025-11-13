"""Trace normalization utilities for handling various BFF trace formats."""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json


class TraceNormalizer:
    """Normalizer for various BFF trace formats.
    
    Handles different trace formats and converts them to a standard EpochData format.
    """
    
    @staticmethod
    def normalize_bff_trace(data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize BFF trace data to standard format.
        
        Handles various formats:
        - save_bff_trace.py output
        - Custom trace formats
        - Legacy formats
        
        Args:
            data: Raw trace data dictionary
            
        Returns:
            Normalized trace data
        """
        normalized = {
            "epoch": data.get("epoch", 0),
            "tapes": {},
            "interactions": [],
            "metrics": {}
        }
        
        # Normalize tapes
        if "tapes" in data:
            normalized["tapes"] = TraceNormalizer._normalize_tapes(data["tapes"])
        elif "programs" in data:
            normalized["tapes"] = TraceNormalizer._normalize_tapes(data["programs"])
        elif "population" in data:
            normalized["tapes"] = TraceNormalizer._normalize_tapes(data["population"])
        
        # Normalize interactions
        if "interactions" in data:
            normalized["interactions"] = TraceNormalizer._normalize_interactions(data["interactions"])
        elif "pairs" in data:
            normalized["interactions"] = TraceNormalizer._normalize_interactions(data["pairs"])
        
        # Normalize metrics
        if "metrics" in data:
            normalized["metrics"] = data["metrics"]
        else:
            # Extract metrics from top-level keys
            metric_keys = ["entropy", "compression_ratio", "copy_score_mean", "h0", "higher_entropy"]
            normalized["metrics"] = {
                key: data[key] for key in metric_keys if key in data
            }
        
        return normalized
    
    @staticmethod
    def _normalize_tapes(tapes_data: Any) -> Dict[int, str]:
        """Normalize tapes to dict format with hex strings.
        
        Args:
            tapes_data: Tapes in various formats
            
        Returns:
            Dict mapping tape_id to hex string
        """
        result = {}
        
        if isinstance(tapes_data, dict):
            # Already in dict format
            for key, value in tapes_data.items():
                tape_id = int(key) if isinstance(key, str) else key
                if isinstance(value, str):
                    result[tape_id] = value
                elif isinstance(value, (bytes, bytearray)):
                    result[tape_id] = value.hex()
                elif isinstance(value, list):
                    result[tape_id] = bytes(value).hex()
        
        elif isinstance(tapes_data, list):
            # List format: index is tape_id
            for tape_id, value in enumerate(tapes_data):
                if isinstance(value, str):
                    result[tape_id] = value
                elif isinstance(value, (bytes, bytearray)):
                    result[tape_id] = value.hex()
                elif isinstance(value, list):
                    result[tape_id] = bytes(value).hex()
        
        return result
    
    @staticmethod
    def _normalize_interactions(interactions_data: Any) -> List[List[int]]:
        """Normalize interactions to list of pairs.
        
        Args:
            interactions_data: Interactions in various formats
            
        Returns:
            List of [tape_a_id, tape_b_id] pairs
        """
        result = []
        
        if isinstance(interactions_data, list):
            for item in interactions_data:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    result.append([int(item[0]), int(item[1])])
                elif isinstance(item, dict):
                    # Dict format: {"a": 0, "b": 1} or {"first": 0, "second": 1}
                    a = item.get("a", item.get("first", item.get("tape_a", 0)))
                    b = item.get("b", item.get("second", item.get("tape_b", 1)))
                    result.append([int(a), int(b)])
        
        return result
    
    @staticmethod
    def validate_tape_size(tape_hex: str, expected_size: int = 64) -> bool:
        """Validate that a tape hex string represents the correct size.
        
        Args:
            tape_hex: Hex string of tape
            expected_size: Expected size in bytes (default 64)
            
        Returns:
            True if valid size
        """
        try:
            tape_bytes = bytes.fromhex(tape_hex)
            return len(tape_bytes) == expected_size
        except ValueError:
            return False
    
    @staticmethod
    def pad_or_truncate_tape(tape_hex: str, target_size: int = 64) -> str:
        """Pad or truncate a tape to the target size.
        
        Args:
            tape_hex: Hex string of tape
            target_size: Target size in bytes (default 64)
            
        Returns:
            Hex string of tape with correct size
        """
        try:
            tape_bytes = bytearray.fromhex(tape_hex)
        except ValueError:
            # Invalid hex, create empty tape
            tape_bytes = bytearray(target_size)
        
        if len(tape_bytes) < target_size:
            # Pad with zeros
            tape_bytes.extend([0] * (target_size - len(tape_bytes)))
        elif len(tape_bytes) > target_size:
            # Truncate
            tape_bytes = tape_bytes[:target_size]
        
        return tape_bytes.hex()
    
    @staticmethod
    def extract_metrics_from_soup(tapes: Dict[int, str]) -> Dict[str, float]:
        """Extract basic metrics from a soup of tapes.
        
        Args:
            tapes: Dict of tape_id to hex string
            
        Returns:
            Dict of computed metrics
        """
        if not tapes:
            return {
                "entropy": 0.0,
                "compression_ratio": 1.0,
                "copy_score_mean": 0.0
            }
        
        # Convert to bytes
        tape_bytes = [bytes.fromhex(tape_hex) for tape_hex in tapes.values()]
        
        # Compute simple entropy (byte frequency)
        all_bytes = b''.join(tape_bytes)
        byte_counts = {}
        for byte in all_bytes:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1
        
        total = len(all_bytes)
        entropy = 0.0
        for count in byte_counts.values():
            if count > 0:
                p = count / total
                entropy -= p * (p.bit_length() - 1)  # Approximate log2
        
        # Estimate compression ratio (unique bytes / total bytes)
        compression_ratio = len(byte_counts) / 256.0 if total > 0 else 1.0
        
        # Compute copy score (placeholder - would need actual BFF execution)
        copy_score_mean = 0.5
        
        return {
            "entropy": round(entropy, 3),
            "compression_ratio": round(compression_ratio, 3),
            "copy_score_mean": round(copy_score_mean, 3)
        }
    
    @staticmethod
    def handle_missing_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle missing or malformed data in trace.
        
        Args:
            data: Trace data that may be incomplete
            
        Returns:
            Trace data with defaults filled in
        """
        # Ensure required fields exist
        if "epoch" not in data:
            data["epoch"] = 0
        
        if "tapes" not in data or not data["tapes"]:
            data["tapes"] = {}
        
        if "interactions" not in data:
            data["interactions"] = []
        
        if "metrics" not in data:
            # Compute metrics from tapes if possible
            data["metrics"] = TraceNormalizer.extract_metrics_from_soup(data["tapes"])
        
        return data
    
    @staticmethod
    def convert_legacy_format(data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert legacy BFF trace formats to current format.
        
        Args:
            data: Legacy format trace data
            
        Returns:
            Converted trace data
        """
        # Handle old format where tapes were stored as base64
        if "tapes_b64" in data:
            import base64
            tapes = {}
            for tape_id, b64_str in data["tapes_b64"].items():
                tape_bytes = base64.b64decode(b64_str)
                tapes[int(tape_id)] = tape_bytes.hex()
            data["tapes"] = tapes
            del data["tapes_b64"]
        
        # Handle old format where interactions were stored differently
        if "pairings" in data:
            data["interactions"] = data["pairings"]
            del data["pairings"]
        
        return data


def load_and_normalize_trace(path: Path) -> List[Dict[str, Any]]:
    """Load a trace file and normalize all epochs.
    
    Args:
        path: Path to trace file
        
    Returns:
        List of normalized epoch data
    """
    with open(path, 'r') as f:
        raw_data = json.load(f)
    
    # Handle single epoch or list of epochs
    if isinstance(raw_data, dict):
        epochs = [raw_data]
    else:
        epochs = raw_data
    
    # Normalize each epoch
    normalized_epochs = []
    for epoch_data in epochs:
        # Convert legacy format if needed
        epoch_data = TraceNormalizer.convert_legacy_format(epoch_data)
        
        # Normalize to standard format
        normalized = TraceNormalizer.normalize_bff_trace(epoch_data)
        
        # Handle missing data
        normalized = TraceNormalizer.handle_missing_data(normalized)
        
        normalized_epochs.append(normalized)
    
    return normalized_epochs
