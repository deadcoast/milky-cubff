"""Tests for OutputWriter."""

import sys
import json
import csv
import tempfile
import gzip
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from adapters.output_writer import OutputWriter, create_output_writer, generate_metadata, MIncJSONEncoder, HAS_NUMPY
    from core.config import OutputConfig
    from core.models import (
        TickResult, Event, EventType, Agent, Role, WealthTraits,
        TickMetrics, AgentSnapshot
    )
except ImportError:
    # Try running as a module
    from m_inc.adapters.output_writer import OutputWriter, create_output_writer, generate_metadata, MIncJSONEncoder, HAS_NUMPY
    from m_inc.core.config import OutputConfig
    from m_inc.core.models import (
        TickResult, Event, EventType, Agent, Role, WealthTraits,
        TickMetrics, AgentSnapshot
    )


def test_output_writer_initialization():
    """Test OutputWriter initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig(json_ticks=True, csv_events=True, csv_final_agents=True)
        writer = OutputWriter(tmpdir, config)
        
        assert writer.output_dir == Path(tmpdir)
        assert writer.config == config
        assert writer.ticks_path == Path(tmpdir) / "ticks.json"
        assert writer.events_path == Path(tmpdir) / "events.csv"
        assert writer.final_agents_path == Path(tmpdir) / "agents_final.csv"
        print("✓ OutputWriter initialization works")


def test_write_tick_json():
    """Test writing tick results to JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig(json_ticks=True, csv_events=False, csv_final_agents=False)
        metadata = generate_metadata("0.1.1", 1337, "test_hash")
        
        with OutputWriter(tmpdir, config, metadata) as writer:
            # Create test tick result
            metrics = TickMetrics(
                entropy=5.91,
                compression_ratio=2.70,
                copy_score_mean=0.64,
                wealth_total=399,
                currency_total=12187
            )
            
            agent_snapshot = AgentSnapshot(
                id="K-01",
                role="king",
                currency=5400,
                wealth={
                    "compute": 14,
                    "copy": 16,
                    "defend": 22,
                    "raid": 3,
                    "trade": 18,
                    "sense": 7,
                    "adapt": 9
                }
            )
            
            tick_result = TickResult(
                tick_num=1,
                events=[],
                metrics=metrics,
                agent_snapshots=[agent_snapshot]
            )
            
            writer.write_tick_json(tick_result)
        
        # Verify file was written
        ticks_path = Path(tmpdir) / "ticks.json"
        assert ticks_path.exists()
        
        # Verify content
        with open(ticks_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["tick"] == 1
        assert data[0]["metrics"]["entropy"] == 5.91
        assert data[0]["agents"][0]["id"] == "K-01"
        assert "meta" in data[0]
        assert data[0]["meta"]["version"] == "0.1.1"
        print("✓ write_tick_json works")


def test_write_event_csv():
    """Test writing events to CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig(json_ticks=False, csv_events=True, csv_final_agents=False)
        
        with OutputWriter(tmpdir, config) as writer:
            # Create test events
            events = [
                Event(
                    tick=1,
                    type=EventType.BRIBE_ACCEPT,
                    king="K-01",
                    merc="M-12",
                    amount=350,
                    notes="success"
                ),
                Event(
                    tick=1,
                    type=EventType.TRADE,
                    king="K-02",
                    invest=100,
                    wealth_created=5
                )
            ]
            
            writer.write_event_csv(events)
        
        # Verify file was written
        events_path = Path(tmpdir) / "events.csv"
        assert events_path.exists()
        
        # Verify content
        with open(events_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["tick"] == "1"
        assert rows[0]["type"] == "bribe_accept"
        assert rows[0]["king"] == "K-01"
        assert rows[0]["merc"] == "M-12"
        assert rows[0]["amount"] == "350"
        print("✓ write_event_csv works")


def test_write_final_agents_csv():
    """Test writing final agent state to CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig(json_ticks=False, csv_events=False, csv_final_agents=True)
        
        with OutputWriter(tmpdir, config) as writer:
            # Create test agents
            agents = [
                Agent(
                    id="K-01",
                    tape_id=0,
                    role=Role.KING,
                    currency=5400,
                    wealth=WealthTraits(
                        compute=14,
                        copy=16,
                        defend=22,
                        raid=3,
                        trade=18,
                        sense=7,
                        adapt=9
                    ),
                    bribe_threshold=350
                ),
                Agent(
                    id="N-01",
                    tape_id=1,
                    role=Role.KNIGHT,
                    currency=250,
                    wealth=WealthTraits(
                        compute=5,
                        copy=3,
                        defend=15,
                        raid=2,
                        trade=0,
                        sense=8,
                        adapt=5
                    ),
                    employer="K-01",
                    retainer_fee=50
                )
            ]
            
            writer.write_final_agents_csv(agents)
        
        # Verify file was written
        agents_path = Path(tmpdir) / "agents_final.csv"
        assert agents_path.exists()
        
        # Verify content
        with open(agents_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]["id"] == "K-01"
        assert rows[0]["role"] == "king"
        assert rows[0]["currency"] == "5400"
        assert rows[0]["wealth_total"] == "89"
        assert rows[1]["employer"] == "K-01"
        assert rows[1]["retainer_fee"] == "50"
        print("✓ write_final_agents_csv works")


def test_validate_schema():
    """Test schema validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig()
        writer = OutputWriter(tmpdir, config)
        
        # Valid tick result
        valid_data = {
            "tick": 1,
            "metrics": {
                "entropy": 5.91,
                "compression_ratio": 2.70,
                "copy_score_mean": 0.64,
                "wealth_total": 399,
                "currency_total": 12187
            },
            "agents": [
                {
                    "id": "K-01",
                    "role": "king",
                    "currency": 5400,
                    "wealth": {
                        "compute": 14,
                        "copy": 16,
                        "defend": 22,
                        "raid": 3,
                        "trade": 18,
                        "sense": 7,
                        "adapt": 9
                    }
                }
            ]
        }
        
        assert writer.validate_schema(valid_data, "tick_result") is True
        
        # Invalid data (negative currency)
        invalid_data = {
            "tick": 1,
            "metrics": {
                "entropy": 5.91,
                "compression_ratio": 2.70,
                "copy_score_mean": 0.64,
                "wealth_total": 399,
                "currency_total": -100  # Invalid
            },
            "agents": []
        }
        
        assert writer.validate_schema(invalid_data, "tick_result") is False
        print("✓ validate_schema works")


def test_context_manager():
    """Test OutputWriter as context manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig(json_ticks=True)
        metadata = generate_metadata("0.1.1", 1337, "test_hash")
        
        with OutputWriter(tmpdir, config, metadata) as writer:
            metrics = TickMetrics(
                entropy=5.91,
                compression_ratio=2.70,
                copy_score_mean=0.64,
                wealth_total=399,
                currency_total=12187
            )
            
            tick_result = TickResult(
                tick_num=1,
                events=[],
                metrics=metrics,
                agent_snapshots=[]
            )
            
            writer.write_tick_json(tick_result)
        
        # Verify file was written after context exit
        ticks_path = Path(tmpdir) / "ticks.json"
        assert ticks_path.exists()
        print("✓ Context manager works")


def test_create_output_writer_factory():
    """Test factory function for creating output writers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig()
        
        # Create regular writer
        writer = create_output_writer(tmpdir, config, streaming=False)
        assert isinstance(writer, OutputWriter)
        
        # Create streaming writer
        streaming_writer = create_output_writer(tmpdir, config, streaming=True)
        assert streaming_writer.__class__.__name__ == "StreamingOutputWriter"
        print("✓ create_output_writer factory works")


def test_generate_metadata():
    """Test metadata generation."""
    metadata = generate_metadata("0.1.1", 1337, "test_hash", {"custom": "value"})
    
    assert metadata["version"] == "0.1.1"
    assert metadata["seed"] == 1337
    assert metadata["config_hash"] == "test_hash"
    assert "timestamp" in metadata
    assert metadata["generator"] == "m_inc"
    assert metadata["custom"] == "value"
    print("✓ generate_metadata works")


def test_json_serialization_with_numpy_types():
    """Test JSON serialization handles numpy types correctly."""
    if not HAS_NUMPY:
        print("⊘ Skipping numpy test (numpy not available)")
        return
    
    import numpy as np
    
    # Test various numpy types
    test_data = {
        "int64": np.int64(42),
        "int32": np.int32(100),
        "float64": np.float64(3.14159),
        "float32": np.float32(2.71828),
        "bool": np.bool_(True),
        "array": np.array([1, 2, 3]),
        "nested": {
            "value": np.int64(999)
        }
    }
    
    # Serialize with custom encoder
    json_str = json.dumps(test_data, cls=MIncJSONEncoder)
    
    # Deserialize and verify
    result = json.loads(json_str)
    assert result["int64"] == 42
    assert result["int32"] == 100
    assert abs(result["float64"] - 3.14159) < 0.0001
    assert abs(result["float32"] - 2.71828) < 0.0001
    assert result["bool"] is True
    assert result["array"] == [1, 2, 3]
    assert result["nested"]["value"] == 999
    print("✓ JSON serialization handles numpy types")


def test_json_compression():
    """Test JSON output with gzip compression."""
    import gzip
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig(json_ticks=True, compress=True)
        metadata = generate_metadata("0.1.1", 1337, "test_hash")
        
        with OutputWriter(tmpdir, config, metadata) as writer:
            metrics = TickMetrics(
                entropy=5.91,
                compression_ratio=2.70,
                copy_score_mean=0.64,
                wealth_total=399,
                currency_total=12187
            )
            
            tick_result = TickResult(
                tick_num=1,
                events=[],
                metrics=metrics,
                agent_snapshots=[]
            )
            
            writer.write_tick_json(tick_result)
        
        # Verify compressed file was written
        ticks_path = Path(tmpdir) / "ticks.json.gz"
        assert ticks_path.exists()
        
        # Verify we can read it back
        with gzip.open(ticks_path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["tick"] == 1
        assert "meta" in data[0]
        print("✓ JSON compression works")


def test_metadata_in_first_tick_only():
    """Test that metadata is only included in the first tick."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig(json_ticks=True)
        metadata = generate_metadata("0.1.1", 1337, "test_hash")
        
        with OutputWriter(tmpdir, config, metadata) as writer:
            # Write multiple ticks
            for tick_num in range(1, 4):
                metrics = TickMetrics(
                    entropy=5.91,
                    compression_ratio=2.70,
                    copy_score_mean=0.64,
                    wealth_total=399,
                    currency_total=12187
                )
                
                tick_result = TickResult(
                    tick_num=tick_num,
                    events=[],
                    metrics=metrics,
                    agent_snapshots=[]
                )
                
                writer.write_tick_json(tick_result)
        
        # Verify metadata is only in first tick
        ticks_path = Path(tmpdir) / "ticks.json"
        with open(ticks_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 3
        assert "meta" in data[0]
        assert "meta" not in data[1]
        assert "meta" not in data[2]
        assert data[0]["meta"]["version"] == "0.1.1"
        print("✓ Metadata only in first tick")


if __name__ == "__main__":
    test_output_writer_initialization()
    test_write_tick_json()
    test_write_event_csv()
    test_write_final_agents_csv()
    test_validate_schema()
    test_context_manager()
    test_create_output_writer_factory()
    test_generate_metadata()
    test_json_serialization_with_numpy_types()
    test_json_compression()
    test_metadata_in_first_tick_only()
    print("\n✅ All OutputWriter tests passed!")
