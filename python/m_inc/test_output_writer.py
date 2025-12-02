"""Tests for output writer."""

import json
import csv
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
