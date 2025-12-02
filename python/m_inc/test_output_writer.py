"""Tests for output writer."""

import json
import csv
import gzip
import tempfile
from pathlib import Path

import pytest

from m_inc.adapters.output_writer import OutputWriter, create_output_writer, generate_metadata
from m_inc.core.models import (
    Agent, WealthTraits, Role, Event, EventType, TickResult, 
    TickMetrics, AgentSnapshot
)
from m_inc.core.config import OutputConfig


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_agent():
    """Create a sample agent."""
    return Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(
            compute=10, copy=12, defend=20, raid=3,
            trade=15, sense=7, adapt=8
        ),
        bribe_threshold=350
    )


@pytest.fixture
def sample_events():
    """Create sample events."""
    return [
        Event(
            tick=1,
            type=EventType.TRADE,
            king="K-01",
            amount=100,
            invest=100,
            wealth_created=5,
            notes="trade success"
        ),
        Event(
            tick=1,
            type=EventType.BRIBE_ACCEPT,
            king="K-01",
            merc="M-12",
            amount=350,
            rv=320.5,
            notes="bribe accepted"
        )
    ]


@pytest.fixture
def sample_tick_result(sample_agent):
    """Create a sample tick result."""
    metrics = TickMetrics(
        entropy=5.91,
        compression_ratio=2.70,
        copy_score_mean=0.64,
        wealth_total=399,
        currency_total=12187,
        bribes_paid=1,
        bribes_accepted=0,
        raids_attempted=2,
        raids_won_by_merc=0,
        raids_won_by_knight=1
    )
    
    snapshot = AgentSnapshot.from_agent(sample_agent)
    
    return TickResult(
        tick_num=1,
        events=[],
        metrics=metrics,
        agent_snapshots=[snapshot]
    )


def test_output_writer_init(temp_output_dir):
    """Test OutputWriter initialization."""
    config = OutputConfig()
    metadata = {"version": "0.1.1", "seed": 1337}
    
    writer = OutputWriter(temp_output_dir, config, metadata)
    
    assert writer.output_dir == temp_output_dir
    assert writer.config == config
    assert writer.metadata == metadata
    assert temp_output_dir.exists()


def test_write_tick_json(temp_output_dir, sample_tick_result):
    """Test writing tick results to JSON."""
    config = OutputConfig(json_ticks=True)
    metadata = {"version": "0.1.1", "seed": 1337, "config_hash": "abc123"}
    
    writer = OutputWriter(temp_output_dir, config, metadata)
    writer.write_tick_json(sample_tick_result)
    writer.flush_ticks()
    
    # Verify file exists
    ticks_path = temp_output_dir / "ticks.json"
    assert ticks_path.exists()
    
    # Verify content
    with open(ticks_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["tick"] == 1
    assert "metrics" in data[0]
    assert "agents" in data[0]
    assert "meta" in data[0]
    assert data[0]["meta"]["version"] == "0.1.1"


def test_write_event_csv(temp_output_dir, sample_events):
    """Test writing events to CSV."""
    config = OutputConfig(csv_events=True)
    
    writer = OutputWriter(temp_output_dir, config)
    writer.write_event_csv(sample_events)
    
    # Verify file exists
    events_path = temp_output_dir / "events.csv"
    assert events_path.exists()
    
    # Verify content
    with open(events_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["tick"] == "1"
    assert rows[0]["type"] == "trade"
    assert rows[0]["king"] == "K-01"
    assert rows[1]["type"] == "bribe_accept"


def test_write_final_agents_csv(temp_output_dir, sample_agent):
    """Test writing final agent state to CSV."""
    config = OutputConfig(csv_final_agents=True)
    
    writer = OutputWriter(temp_output_dir, config)
    writer.write_final_agents_csv([sample_agent])
    
    # Verify file exists
    agents_path = temp_output_dir / "agents_final.csv"
    assert agents_path.exists()
    
    # Verify content
    with open(agents_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["id"] == "K-01"
    assert rows[0]["role"] == "king"
    assert rows[0]["currency"] == "5000"
    assert rows[0]["wealth_total"] == "75"


def test_validate_schema(temp_output_dir, sample_tick_result, sample_agent, sample_events):
    """Test schema validation."""
    config = OutputConfig()
    writer = OutputWriter(temp_output_dir, config)
    
    # Valid tick_result
    tick_dict = sample_tick_result.to_dict()
    tick_dict["meta"] = {"version": "0.1.1", "seed": 1337}
    assert writer.validate_schema(tick_dict, "tick_result") is True
    
    # Valid agent
    agent_dict = sample_agent.to_dict()
    assert writer.validate_schema(agent_dict, "agent") is True
    
    # Valid event
    event_dict = sample_events[0].to_dict()
    assert writer.validate_schema(event_dict, "event") is True
    
    # Valid tick_metrics
    metrics_dict = sample_tick_result.metrics.to_dict()
    assert writer.validate_schema(metrics_dict, "tick_metrics") is True
    
    # Valid agent_snapshot
    snapshot_dict = sample_tick_result.agent_snapshots[0].to_dict()
    assert writer.validate_schema(snapshot_dict, "agent_snapshot") is True
    
    # Invalid schema name
    assert writer.validate_schema(tick_dict, "unknown_schema") is False


def test_context_manager(temp_output_dir, sample_tick_result):
    """Test OutputWriter as context manager."""
    config = OutputConfig(json_ticks=True)
    metadata = {"version": "0.1.1"}
    
    with OutputWriter(temp_output_dir, config, metadata) as writer:
        writer.write_tick_json(sample_tick_result)
    
    # Verify data was flushed
    ticks_path = temp_output_dir / "ticks.json"
    assert ticks_path.exists()


def test_multiple_ticks(temp_output_dir, sample_tick_result):
    """Test writing multiple ticks."""
    config = OutputConfig(json_ticks=True)
    
    writer = OutputWriter(temp_output_dir, config)
    
    # Write multiple ticks
    for i in range(1, 4):
        tick_result = TickResult(
            tick_num=i,
            events=[],
            metrics=sample_tick_result.metrics,
            agent_snapshots=sample_tick_result.agent_snapshots
        )
        writer.write_tick_json(tick_result)
    
    writer.flush_ticks()
    
    # Verify all ticks written
    with open(temp_output_dir / "ticks.json", 'r') as f:
        data = json.load(f)
    
    assert len(data) == 3
    assert data[0]["tick"] == 1
    assert data[1]["tick"] == 2
    assert data[2]["tick"] == 3


def test_disabled_outputs(temp_output_dir, sample_tick_result, sample_events, sample_agent):
    """Test that outputs are not written when disabled."""
    config = OutputConfig(
        json_ticks=False,
        csv_events=False,
        csv_final_agents=False
    )
    
    writer = OutputWriter(temp_output_dir, config)
    writer.write_tick_json(sample_tick_result)
    writer.write_event_csv(sample_events)
    writer.write_final_agents_csv([sample_agent])
    writer.flush_ticks()
    
    # Verify no files created
    assert not (temp_output_dir / "ticks.json").exists()
    assert not (temp_output_dir / "events.csv").exists()
    assert not (temp_output_dir / "agents_final.csv").exists()


def test_create_output_writer_factory(temp_output_dir):
    """Test factory function."""
    config = OutputConfig()
    metadata = {"version": "0.1.1"}
    
    # Regular writer
    writer = create_output_writer(temp_output_dir, config, metadata, streaming=False)
    assert isinstance(writer, OutputWriter)
    
    # Streaming writer
    from m_inc.adapters.output_writer import StreamingOutputWriter
    streaming_writer = create_output_writer(temp_output_dir, config, metadata, streaming=True)
    assert isinstance(streaming_writer, StreamingOutputWriter)


def test_generate_metadata():
    """Test metadata generation."""
    metadata = generate_metadata(
        version="0.1.1",
        seed=1337,
        config_hash="abc123",
        additional={"custom": "value"}
    )
    
    assert metadata["version"] == "0.1.1"
    assert metadata["seed"] == 1337
    assert metadata["config_hash"] == "abc123"
    assert "timestamp" in metadata
    assert metadata["generator"] == "m_inc"
    assert metadata["custom"] == "value"


def test_append_events(temp_output_dir):
    """Test appending events to CSV."""
    config = OutputConfig(csv_events=True)
    writer = OutputWriter(temp_output_dir, config)
    
    # Write first batch
    events1 = [
        Event(tick=1, type=EventType.TRADE, king="K-01", amount=100)
    ]
    writer.write_event_csv(events1)
    
    # Write second batch
    events2 = [
        Event(tick=2, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-12", amount=350)
    ]
    writer.write_event_csv(events2)
    
    # Verify both batches in file
    with open(temp_output_dir / "events.csv", 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["tick"] == "1"
    assert rows[1]["tick"] == "2"


def test_json_encoder_with_numpy_types(temp_output_dir):
    """Test JSON encoder handles numpy types correctly."""
    try:
        import numpy as np
        has_numpy = True
    except ImportError:
        has_numpy = False
        pytest.skip("numpy not installed")
    
    from m_inc.adapters.output_writer import MIncJSONEncoder
    
    # Test numpy integer types
    data = {
        "int64": np.int64(42),
        "int32": np.int32(100),
        "float64": np.float64(3.14159),
        "float32": np.float32(2.71828),
        "bool": np.bool_(True),
        "array": np.array([1, 2, 3, 4, 5]),
        "nested": {
            "value": np.int64(999)
        }
    }
    
    # Serialize with custom encoder
    json_str = json.dumps(data, cls=MIncJSONEncoder)
    
    # Deserialize and verify
    result = json.loads(json_str)
    assert result["int64"] == 42
    assert result["int32"] == 100
    assert abs(result["float64"] - 3.14159) < 0.0001
    assert abs(result["float32"] - 2.71828) < 0.0001
    assert result["bool"] is True
    assert result["array"] == [1, 2, 3, 4, 5]
    assert result["nested"]["value"] == 999


def test_json_encoder_with_enums(temp_output_dir):
    """Test JSON encoder handles Enum types correctly."""
    from m_inc.adapters.output_writer import MIncJSONEncoder
    
    data = {
        "role": Role.KING,
        "event_type": EventType.TRADE,
        "nested": {
            "role": Role.MERCENARY
        }
    }
    
    # Serialize with custom encoder
    json_str = json.dumps(data, cls=MIncJSONEncoder)
    
    # Deserialize and verify
    result = json.loads(json_str)
    assert result["role"] == "king"
    assert result["event_type"] == "trade"
    assert result["nested"]["role"] == "mercenary"


def test_json_encoder_with_datetime(temp_output_dir):
    """Test JSON encoder handles datetime objects correctly."""
    from m_inc.adapters.output_writer import MIncJSONEncoder
    from datetime import datetime
    
    dt = datetime(2025, 1, 27, 10, 30, 0)
    data = {
        "timestamp": dt,
        "nested": {
            "created_at": dt
        }
    }
    
    # Serialize with custom encoder
    json_str = json.dumps(data, cls=MIncJSONEncoder)
    
    # Deserialize and verify
    result = json.loads(json_str)
    assert result["timestamp"] == "2025-01-27T10:30:00"
    assert result["nested"]["created_at"] == "2025-01-27T10:30:00"


def test_json_encoder_with_custom_objects(temp_output_dir):
    """Test JSON encoder handles objects with to_dict() method."""
    from m_inc.adapters.output_writer import MIncJSONEncoder
    
    agent = Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(compute=10, copy=12, defend=20)
    )
    
    data = {
        "agent": agent,
        "wealth": agent.wealth
    }
    
    # Serialize with custom encoder
    json_str = json.dumps(data, cls=MIncJSONEncoder)
    
    # Deserialize and verify
    result = json.loads(json_str)
    assert result["agent"]["id"] == "K-01"
    assert result["agent"]["role"] == "king"
    assert result["agent"]["currency"] == 5000
    assert result["wealth"]["compute"] == 10


def test_json_encoder_with_path_objects(temp_output_dir):
    """Test JSON encoder handles Path objects correctly."""
    from m_inc.adapters.output_writer import MIncJSONEncoder
    
    data = {
        "output_dir": Path("/tmp/output"),
        "file": Path("data.json")
    }
    
    # Serialize with custom encoder
    json_str = json.dumps(data, cls=MIncJSONEncoder)
    
    # Deserialize and verify
    result = json.loads(json_str)
    assert result["output_dir"] == "/tmp/output"
    assert result["file"] == "data.json"


def test_write_tick_json_with_numpy_metrics(temp_output_dir):
    """Test writing tick results with numpy-typed metrics."""
    try:
        import numpy as np
        has_numpy = True
    except ImportError:
        has_numpy = False
        pytest.skip("numpy not installed")
    
    config = OutputConfig(json_ticks=True)
    metadata = {"version": "0.1.1", "seed": 1337}
    
    # Create tick result with numpy types
    metrics = TickMetrics(
        entropy=np.float64(5.91),
        compression_ratio=np.float64(2.70),
        copy_score_mean=np.float64(0.64),
        wealth_total=np.int64(399),
        currency_total=np.int64(12187),
        bribes_paid=np.int32(1),
        bribes_accepted=np.int32(0),
        raids_attempted=np.int32(2),
        raids_won_by_merc=np.int32(0),
        raids_won_by_knight=np.int32(1)
    )
    
    agent = Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(compute=10, copy=12, defend=20)
    )
    
    snapshot = AgentSnapshot.from_agent(agent)
    
    tick_result = TickResult(
        tick_num=1,
        events=[],
        metrics=metrics,
        agent_snapshots=[snapshot]
    )
    
    writer = OutputWriter(temp_output_dir, config, metadata)
    writer.write_tick_json(tick_result)
    writer.flush_ticks()
    
    # Verify file exists and can be read
    ticks_path = temp_output_dir / "ticks.json"
    assert ticks_path.exists()
    
    with open(ticks_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["tick"] == 1
    assert abs(data[0]["metrics"]["entropy"] - 5.91) < 0.01


def test_compressed_json_output(temp_output_dir, sample_tick_result):
    """Test writing compressed JSON output."""
    config = OutputConfig(json_ticks=True, compress=True)
    metadata = {"version": "0.1.1", "seed": 1337}
    
    writer = OutputWriter(temp_output_dir, config, metadata)
    writer.write_tick_json(sample_tick_result)
    writer.flush_ticks()
    
    # Verify compressed file exists
    ticks_path = temp_output_dir / "ticks.json.gz"
    assert ticks_path.exists()
    
    # Verify can read compressed file
    with gzip.open(ticks_path, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["tick"] == 1
    assert "meta" in data[0]


def test_json_serialization_preserves_precision(temp_output_dir):
    """Test that JSON serialization preserves numeric precision."""
    config = OutputConfig(json_ticks=True)
    
    # Create metrics with precise values
    metrics = TickMetrics(
        entropy=5.912345678,
        compression_ratio=2.701234567,
        copy_score_mean=0.641234567,
        wealth_total=399,
        currency_total=12187
    )
    
    agent = Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(compute=10)
    )
    
    snapshot = AgentSnapshot.from_agent(agent)
    
    tick_result = TickResult(
        tick_num=1,
        events=[],
        metrics=metrics,
        agent_snapshots=[snapshot]
    )
    
    writer = OutputWriter(temp_output_dir, config)
    writer.write_tick_json(tick_result)
    writer.flush_ticks()
    
    # Read back and verify precision (rounded to 3 decimals as per to_dict())
    with open(temp_output_dir / "ticks.json", 'r') as f:
        data = json.load(f)
    
    # Metrics are rounded to 3 decimals in to_dict()
    assert data[0]["metrics"]["entropy"] == 5.912
    assert data[0]["metrics"]["compression_ratio"] == 2.701
    assert data[0]["metrics"]["copy_score_mean"] == 0.641


def test_csv_handles_missing_values(temp_output_dir):
    """Test that CSV serialization handles missing/None values gracefully."""
    config = OutputConfig(csv_events=True, csv_final_agents=True)
    writer = OutputWriter(temp_output_dir, config)
    
    # Create events with various missing fields
    events = [
        Event(tick=1, type=EventType.TRADE, king="K-01", amount=100),
        Event(tick=1, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-12", amount=350, rv=320.5),
        Event(tick=2, type=EventType.DEFEND_WIN, king="K-02", knight="N-05", merc="M-08", stake=50, p_knight=0.65),
        Event(tick=2, type=EventType.TRAIT_DRIP, agent="M-03", trait="copy", delta=1),
    ]
    writer.write_event_csv(events)
    
    # Verify CSV can be read and missing values are handled
    with open(temp_output_dir / "events.csv", 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 4
    # Trade event should have empty knight and merc
    assert rows[0]["knight"] == ""
    assert rows[0]["merc"] == ""
    # Bribe event should have empty knight
    assert rows[1]["knight"] == ""
    # Trait drip should have empty king, knight, merc
    assert rows[3]["king"] == ""
    assert rows[3]["knight"] == ""
    assert rows[3]["merc"] == ""


def test_csv_column_ordering(temp_output_dir):
    """Test that CSV columns are in the correct order."""
    config = OutputConfig(csv_events=True, csv_final_agents=True)
    writer = OutputWriter(temp_output_dir, config)
    
    # Write events
    events = [Event(tick=1, type=EventType.TRADE, king="K-01", amount=100)]
    writer.write_event_csv(events)
    
    # Verify event CSV column order
    with open(temp_output_dir / "events.csv", 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
    
    expected_event_columns = [
        "tick", "type", "king", "knight", "merc", "amount", "stake",
        "p_knight", "notes", "trait", "delta", "invest", "wealth_created",
        "rv", "threshold", "employer", "agent"
    ]
    assert header == expected_event_columns
    
    # Write agents
    agent = Agent(
        id="K-01",
        tape_id=0,
        role=Role.KING,
        currency=5000,
        wealth=WealthTraits(compute=10, copy=12, defend=20)
    )
    writer.write_final_agents_csv([agent])
    
    # Verify agent CSV column order
    with open(temp_output_dir / "agents_final.csv", 'r', newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
    
    expected_agent_columns = [
        "id", "role", "currency", "compute", "copy", "defend", "raid",
        "trade", "sense", "adapt", "wealth_total", "employer",
        "retainer_fee", "bribe_threshold", "alive"
    ]
    assert header == expected_agent_columns


def test_csv_streaming_append_mode(temp_output_dir):
    """Test that CSV append mode works correctly for streaming writes."""
    config = OutputConfig(csv_events=True)
    writer = OutputWriter(temp_output_dir, config)
    
    # Write events in multiple batches (simulating streaming)
    batch1 = [Event(tick=1, type=EventType.TRADE, king="K-01", amount=100)]
    batch2 = [Event(tick=2, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-12", amount=350)]
    batch3 = [Event(tick=3, type=EventType.DEFEND_WIN, king="K-02", knight="N-05", merc="M-08", stake=50)]
    
    writer.write_event_csv(batch1)
    writer.write_event_csv(batch2)
    writer.write_event_csv(batch3)
    
    # Verify all events are in the file with only one header
    with open(temp_output_dir / "events.csv", 'r', newline='') as f:
        content = f.read()
        lines = content.strip().split('\n')
    
    # Should have 1 header + 3 data rows
    assert len(lines) == 4
    # First line should be header
    assert lines[0].startswith("tick,type,king")
    # Subsequent lines should be data
    assert lines[1].startswith("1,trade")
    assert lines[2].startswith("2,bribe_accept")
    assert lines[3].startswith("3,defend_win")


def test_csv_all_agent_attributes(temp_output_dir):
    """Test that all agent attributes are written to CSV."""
    config = OutputConfig(csv_final_agents=True)
    writer = OutputWriter(temp_output_dir, config)
    
    # Create agents with all possible attributes
    agents = [
        Agent(
            id="K-01",
            tape_id=0,
            role=Role.KING,
            currency=5000,
            wealth=WealthTraits(compute=10, copy=12, defend=20, raid=3, trade=15, sense=7, adapt=8),
            bribe_threshold=350,
            alive=True
        ),
        Agent(
            id="N-07",
            tape_id=7,
            role=Role.KNIGHT,
            currency=250,
            wealth=WealthTraits(compute=5, copy=3, defend=15, raid=2, trade=0, sense=8, adapt=5),
            employer="K-01",
            retainer_fee=50,
            alive=True
        ),
        Agent(
            id="M-12",
            tape_id=12,
            role=Role.MERCENARY,
            currency=100,
            wealth=WealthTraits(compute=2, copy=4, defend=1, raid=15, trade=0, sense=6, adapt=5),
            alive=False
        )
    ]
    
    writer.write_final_agents_csv(agents)
    
    # Verify all attributes are present
    with open(temp_output_dir / "agents_final.csv", 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    
    # Check King
    assert rows[0]["id"] == "K-01"
    assert rows[0]["role"] == "king"
    assert rows[0]["currency"] == "5000"
    assert rows[0]["compute"] == "10"
    assert rows[0]["copy"] == "12"
    assert rows[0]["defend"] == "20"
    assert rows[0]["raid"] == "3"
    assert rows[0]["trade"] == "15"
    assert rows[0]["sense"] == "7"
    assert rows[0]["adapt"] == "8"
    assert rows[0]["wealth_total"] == "75"
    assert rows[0]["employer"] == ""
    assert rows[0]["bribe_threshold"] == "350"
    assert rows[0]["alive"] == "True"
    
    # Check Knight
    assert rows[1]["id"] == "N-07"
    assert rows[1]["role"] == "knight"
    assert rows[1]["employer"] == "K-01"
    assert rows[1]["retainer_fee"] == "50"
    
    # Check Mercenary
    assert rows[2]["id"] == "M-12"
    assert rows[2]["role"] == "mercenary"
    assert rows[2]["alive"] == "False"


def test_csv_empty_lists(temp_output_dir):
    """Test that writing empty lists doesn't create files or cause errors."""
    config = OutputConfig(csv_events=True, csv_final_agents=True)
    writer = OutputWriter(temp_output_dir, config)
    
    # Write empty lists
    writer.write_event_csv([])
    writer.write_final_agents_csv([])
    
    # Verify no files were created
    assert not (temp_output_dir / "events.csv").exists()
    assert not (temp_output_dir / "agents_final.csv").exists()


def test_csv_special_characters_in_notes(temp_output_dir):
    """Test that CSV handles special characters in notes field."""
    config = OutputConfig(csv_events=True)
    writer = OutputWriter(temp_output_dir, config)
    
    # Create events with special characters in notes
    events = [
        Event(tick=1, type=EventType.TRADE, king="K-01", amount=100, notes="Success, no issues"),
        Event(tick=2, type=EventType.BRIBE_ACCEPT, king="K-01", merc="M-12", amount=350, notes='Quote: "accepted"'),
        Event(tick=3, type=EventType.DEFEND_WIN, king="K-02", knight="N-05", merc="M-08", notes="Line1\nLine2"),
    ]
    
    writer.write_event_csv(events)
    
    # Verify CSV can be read correctly with special characters
    with open(temp_output_dir / "events.csv", 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0]["notes"] == "Success, no issues"
    assert rows[1]["notes"] == 'Quote: "accepted"'
    assert rows[2]["notes"] == "Line1\nLine2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
