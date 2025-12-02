"""Verify JSON serialization implementation."""

import tempfile
import json
import gzip
from pathlib import Path
from m_inc.adapters.output_writer import OutputWriter, generate_metadata
from m_inc.core.config import OutputConfig
from m_inc.core.models import TickResult, TickMetrics, AgentSnapshot

def test_json_formatting():
    """Test that JSON is properly formatted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig(json_ticks=True, compress=False)
        metadata = generate_metadata('0.1.1', 1337, 'abc123')
        
        with OutputWriter(tmpdir, config, metadata) as writer:
            metrics = TickMetrics(
                entropy=5.91234,
                compression_ratio=2.70456,
                copy_score_mean=0.64789,
                wealth_total=399,
                currency_total=12187
            )
            
            snapshot = AgentSnapshot(
                id='K-01',
                role='king',
                currency=5400,
                wealth={'compute': 14, 'copy': 16, 'defend': 22, 'raid': 3, 'trade': 18, 'sense': 7, 'adapt': 9}
            )
            
            tick_result = TickResult(
                tick_num=1,
                events=[],
                metrics=metrics,
                agent_snapshots=[snapshot]
            )
            
            writer.write_tick_json(tick_result)
        
        # Read and verify
        with open(Path(tmpdir) / 'ticks.json', 'r') as f:
            content = f.read()
            print("JSON Output Sample (first 500 chars):")
            print(content[:500])
            print("...")
            
            # Verify it's valid JSON
            data = json.loads(content)
            assert len(data) == 1
            assert data[0]["tick"] == 1
            assert "meta" in data[0]
            assert data[0]["meta"]["version"] == "0.1.1"
            assert data[0]["metrics"]["entropy"] == 5.912
            print("\n✓ JSON formatting correct")

def test_compression():
    """Test that compression works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = OutputConfig(json_ticks=True, compress=True)
        metadata = generate_metadata('0.1.1', 1337, 'abc123')
        
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
        
        # Verify compressed file exists
        compressed_path = Path(tmpdir) / 'ticks.json.gz'
        assert compressed_path.exists()
        
        # Verify we can read it
        with gzip.open(compressed_path, 'rt') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["tick"] == 1
            print("✓ Compression works")

if __name__ == "__main__":
    test_json_formatting()
    test_compression()
    print("\n✅ JSON serialization verification complete!")
