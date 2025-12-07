"""Tests for BFF bridge adapter."""

import struct
import tempfile
from pathlib import Path
import pytest

from m_inc.adapters.bff_bridge import BFFBridge, convert_bff_trace_to_json, stream_bff_to_minc


def create_test_bff_trace(path: Path, num_states: int = 5) -> None:
    """Create a test BFF trace file.
    
    Args:
        path: Path to write the trace file
        num_states: Number of states to write
    """
    with open(path, 'wb') as f:
        # Write header
        f.write(b'BFF\0')  # Magic number
        f.write(struct.pack('<I', 1))  # Format version
        f.write(struct.pack('<I', 128))  # Tape size
        
        # Write states
        for i in range(num_states):
            pc = 2 + i
            head0 = 10 + i
            head1 = 20 + i
            
            # Create tape with recognizable pattern
            tape = bytearray(128)
            for j in range(128):
                tape[j] = (i * 10 + j) % 256
            
            f.write(struct.pack('<I', pc))
            f.write(struct.pack('<I', head0))
            f.write(struct.pack('<I', head1))
            f.write(tape)


def test_bff_bridge_read_header():
    """Test reading BFF trace header."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        create_test_bff_trace(tmp_path, num_states=1)
        
        bridge = BFFBridge(tmp_path)
        bridge._read_header()
        
        assert bridge._header_read
        assert bridge._tape_size == 128
        
        bridge.close()
    finally:
        tmp_path.unlink()


def test_bff_bridge_read_state():
    """Test reading a single BFF state."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        create_test_bff_trace(tmp_path, num_states=3)
        
        bridge = BFFBridge(tmp_path)
        
        # Read first state
        state = bridge._read_state()
        assert state is not None
        pc, head0, head1, tape = state
        assert pc == 2
        assert head0 == 10
        assert head1 == 20
        assert len(tape) == 128
        
        # Read second state
        state = bridge._read_state()
        assert state is not None
        pc, head0, head1, tape = state
        assert pc == 3
        assert head0 == 11
        assert head1 == 21
        
        bridge.close()
    finally:
        tmp_path.unlink()


def test_bff_bridge_read_state_as_epoch():
    """Test converting BFF state to EpochData."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        create_test_bff_trace(tmp_path, num_states=2)
        
        bridge = BFFBridge(tmp_path)
        
        # Read first epoch
        epoch = bridge.read_state_as_epoch()
        assert epoch is not None
        assert epoch.epoch_num == 0
        assert len(epoch.tapes) == 2
        assert 0 in epoch.tapes
        assert 1 in epoch.tapes
        assert len(epoch.tapes[0]) == 64
        assert len(epoch.tapes[1]) == 64
        assert epoch.interactions == [(0, 1)]
        assert "pc" in epoch.metrics
        assert epoch.metrics["pc"] == 2.0
        
        # Read second epoch
        epoch = bridge.read_state_as_epoch()
        assert epoch is not None
        assert epoch.epoch_num == 1
        assert epoch.metrics["pc"] == 3.0
        
        bridge.close()
    finally:
        tmp_path.unlink()


def test_bff_bridge_read_all_states():
    """Test reading all states as epochs."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        num_states = 5
        create_test_bff_trace(tmp_path, num_states=num_states)
        
        bridge = BFFBridge(tmp_path)
        epochs = list(bridge.read_all_states_as_epochs())
        
        assert len(epochs) == num_states
        for i, epoch in enumerate(epochs):
            assert epoch.epoch_num == i
            assert len(epoch.tapes) == 2
        
        bridge.close()
    finally:
        tmp_path.unlink()


def test_bff_bridge_convert_to_soup_format():
    """Test converting BFF trace to soup format."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        create_test_bff_trace(tmp_path, num_states=10)
        
        bridge = BFFBridge(tmp_path)
        
        # Convert first 5 states
        epochs = bridge.convert_to_soup_format(num_states=5)
        assert len(epochs) == 5
        
        bridge.close()
    finally:
        tmp_path.unlink()


def test_convert_bff_trace_to_json():
    """Test converting BFF trace to JSON format."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as json_tmp:
        json_path = Path(json_tmp.name)
    
    try:
        create_test_bff_trace(tmp_path, num_states=3)
        
        convert_bff_trace_to_json(tmp_path, json_path, num_states=3)
        
        assert json_path.exists()
        
        # Verify JSON content
        import json
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 3
        
        for i, epoch in enumerate(data):
            assert epoch["epoch"] == i
            assert "tapes" in epoch
            assert "0" in epoch["tapes"]
            assert "1" in epoch["tapes"]
            assert len(epoch["tapes"]["0"]) == 128  # 64 bytes * 2 hex chars
            assert len(epoch["tapes"]["1"]) == 128
            assert "interactions" in epoch
            assert epoch["interactions"] == [[0, 1]]
            assert "metrics" in epoch
    
    finally:
        tmp_path.unlink()
        if json_path.exists():
            json_path.unlink()


def test_stream_bff_to_minc():
    """Test streaming BFF trace for M|inc processing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        create_test_bff_trace(tmp_path, num_states=4)
        
        epochs = list(stream_bff_to_minc(tmp_path))
        
        assert len(epochs) == 4
        for i, epoch in enumerate(epochs):
            assert epoch.epoch_num == i
            assert len(epoch.tapes) == 2
    
    finally:
        tmp_path.unlink()


def test_bff_bridge_invalid_magic():
    """Test handling of invalid magic number."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        # Write invalid magic number
        with open(tmp_path, 'wb') as f:
            f.write(b'XXXX')
            f.write(struct.pack('<I', 1))
            f.write(struct.pack('<I', 128))
        
        bridge = BFFBridge(tmp_path)
        
        with pytest.raises(ValueError, match="Invalid BFF trace format"):
            bridge._read_header()
        
        bridge.close()
    finally:
        tmp_path.unlink()


def test_bff_bridge_invalid_version():
    """Test handling of unsupported version."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        # Write unsupported version
        with open(tmp_path, 'wb') as f:
            f.write(b'BFF\0')
            f.write(struct.pack('<I', 999))  # Invalid version
            f.write(struct.pack('<I', 128))
        
        bridge = BFFBridge(tmp_path)
        
        with pytest.raises(ValueError, match="Unsupported BFF trace version"):
            bridge._read_header()
        
        bridge.close()
    finally:
        tmp_path.unlink()


def test_bff_bridge_context_manager():
    """Test using BFFBridge as context manager."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bff') as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        create_test_bff_trace(tmp_path, num_states=2)
        
        with BFFBridge(tmp_path) as bridge:
            epoch = bridge.read_state_as_epoch()
            assert epoch is not None
        
        # File should be closed after context exit
        assert bridge._file_handle is None
    
    finally:
        tmp_path.unlink()
