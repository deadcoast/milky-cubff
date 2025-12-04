"""Tests for TraceReader and TraceNormalizer components."""

import json
from pathlib import Path

from m_inc.adapters.trace_reader import TraceReader, EpochData
from m_inc.adapters.trace_normalizer import TraceNormalizer, load_and_normalize_trace


def test_trace_reader_json():
    """Test TraceReader with JSON file."""
    trace_path = Path("python/m_inc/testdata/bff_trace_small.json")
    
    with TraceReader(trace_path) as reader:
        # Read first epoch
        epoch = reader.read_epoch()
        
        assert epoch is not None
        assert isinstance(epoch, EpochData)
        assert epoch.epoch_num == 0
        assert len(epoch.tapes) == 50
        assert len(epoch.interactions) > 0
        assert "entropy" in epoch.metrics
        
        # Verify tape format
        tape_0 = epoch.get_tape(0)
        assert tape_0 is not None
        assert len(tape_0) == 64  # 64 bytes
        
        # Read second epoch
        epoch2 = reader.read_epoch()
        assert epoch2 is not None
        assert epoch2.epoch_num == 1


def test_trace_reader_get_tape_by_id():
    """Test get_tape_by_id method."""
    trace_path = Path("python/m_inc/testdata/bff_trace_small.json")
    
    with TraceReader(trace_path) as reader:
        epoch = reader.read_epoch()
        
        # Get specific tape
        tape = reader.get_tape_by_id(5, epoch)
        assert tape is not None
        assert len(tape) == 64
        
        # Get non-existent tape
        tape_missing = reader.get_tape_by_id(999, epoch)
        assert tape_missing is None


def test_trace_reader_get_population_snapshot():
    """Test get_population_snapshot method."""
    trace_path = Path("python/m_inc/testdata/bff_trace_small.json")
    
    with TraceReader(trace_path) as reader:
        epoch = reader.read_epoch()
        
        # Get all tapes
        population = reader.get_population_snapshot(epoch)
        assert len(population) == 50
        assert all(len(tape) == 64 for tape in population)


def test_trace_reader_read_all_epochs():
    """Test reading all epochs."""
    trace_path = Path("python/m_inc/testdata/bff_trace_small.json")
    
    with TraceReader(trace_path) as reader:
        epochs = list(reader.read_all_epochs())
        
        assert len(epochs) > 0
        assert all(isinstance(epoch, EpochData) for epoch in epochs)
        
        # Verify epoch numbers are sequential
        for i, epoch in enumerate(epochs):
            assert epoch.epoch_num == i


def test_trace_normalizer_normalize_bff_trace():
    """Test TraceNormalizer.normalize_bff_trace."""
    # Test with standard format
    data = {
        "epoch": 5,
        "tapes": {
            "0": "aa" * 64,
            "1": "bb" * 64
        },
        "interactions": [[0, 1]],
        "metrics": {"entropy": 5.0}
    }
    
    normalized = TraceNormalizer.normalize_bff_trace(data)
    
    assert normalized["epoch"] == 5
    assert len(normalized["tapes"]) == 2
    assert len(normalized["interactions"]) == 1
    assert normalized["metrics"]["entropy"] == 5.0


def test_trace_normalizer_handle_missing_data():
    """Test TraceNormalizer.handle_missing_data."""
    # Test with minimal data
    data = {}
    
    normalized = TraceNormalizer.handle_missing_data(data)
    
    assert "epoch" in normalized
    assert "tapes" in normalized
    assert "interactions" in normalized
    assert "metrics" in normalized
    assert normalized["epoch"] == 0


def test_trace_normalizer_validate_tape_size():
    """Test TraceNormalizer.validate_tape_size."""
    # Valid 64-byte tape
    valid_tape = "aa" * 64
    assert TraceNormalizer.validate_tape_size(valid_tape, 64)
    
    # Invalid size
    invalid_tape = "aa" * 32
    assert not TraceNormalizer.validate_tape_size(invalid_tape, 64)
    
    # Invalid hex
    assert not TraceNormalizer.validate_tape_size("zzzz", 64)


def test_trace_normalizer_pad_or_truncate_tape():
    """Test TraceNormalizer.pad_or_truncate_tape."""
    # Too short - should pad
    short_tape = "aa" * 32
    padded = TraceNormalizer.pad_or_truncate_tape(short_tape, 64)
    assert len(bytes.fromhex(padded)) == 64
    
    # Too long - should truncate
    long_tape = "aa" * 128
    truncated = TraceNormalizer.pad_or_truncate_tape(long_tape, 64)
    assert len(bytes.fromhex(truncated)) == 64
    
    # Correct size - should remain unchanged
    correct_tape = "aa" * 64
    unchanged = TraceNormalizer.pad_or_truncate_tape(correct_tape, 64)
    assert unchanged == correct_tape


def test_load_and_normalize_trace():
    """Test load_and_normalize_trace function."""
    trace_path = Path("python/m_inc/testdata/bff_trace_small.json")
    
    epochs = load_and_normalize_trace(trace_path)
    
    assert len(epochs) > 0
    assert all("epoch" in epoch for epoch in epochs)
    assert all("tapes" in epoch for epoch in epochs)
    assert all("interactions" in epoch for epoch in epochs)
    assert all("metrics" in epoch for epoch in epochs)


if __name__ == "__main__":
    print("Running TraceReader tests...")
    
    test_trace_reader_json()
    print("✓ test_trace_reader_json")
    
    test_trace_reader_get_tape_by_id()
    print("✓ test_trace_reader_get_tape_by_id")
    
    test_trace_reader_get_population_snapshot()
    print("✓ test_trace_reader_get_population_snapshot")
    
    test_trace_reader_read_all_epochs()
    print("✓ test_trace_reader_read_all_epochs")
    
    test_trace_normalizer_normalize_bff_trace()
    print("✓ test_trace_normalizer_normalize_bff_trace")
    
    test_trace_normalizer_handle_missing_data()
    print("✓ test_trace_normalizer_handle_missing_data")
    
    test_trace_normalizer_validate_tape_size()
    print("✓ test_trace_normalizer_validate_tape_size")
    
    test_trace_normalizer_pad_or_truncate_tape()
    print("✓ test_trace_normalizer_pad_or_truncate_tape")
    
    test_load_and_normalize_trace()
    print("✓ test_load_and_normalize_trace")
    
    print("\nAll tests passed!")
