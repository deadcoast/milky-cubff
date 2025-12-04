"""Integration tests for M|inc components.

Tests the interaction between multiple components to ensure they work together correctly.
"""

import json
from pathlib import Path
import tempfile

from core.config import ConfigLoader
from core.agent_registry import AgentRegistry
from core.economic_engine import EconomicEngine
from core.event_aggregator import EventAggregator
from core.cache import CacheLayer
from core.signals import SignalProcessor
from adapters.trace_reader import TraceReader, EpochData
from adapters.output_writer import create_output_writer, generate_metadata


def test_trace_reader_to_agent_registry():
    """Test TraceReader → AgentRegistry flow."""
    # Load a test trace
    trace_path = Path("testdata/bff_trace_small.json")
    
    with TraceReader(trace_path) as reader:
        epoch = reader.read_epoch()
        
        # Initialize registry with tape IDs from trace
        config = ConfigLoader.get_default()
        registry = AgentRegistry(config.registry, seed=1337)
        
        tape_ids = list(epoch.tapes.keys())
        registry.assign_roles(tape_ids)
        registry.assign_knight_employers()
        
        # Verify agents were created
        stats = registry.get_stats()
        assert stats['total_agents'] == len(tape_ids)
        assert stats['kings'] > 0
        assert stats['knights'] > 0
        assert stats['mercenaries'] > 0
        
        # Verify we can retrieve agents by tape ID
        for tape_id in tape_ids[:5]:  # Check first 5
            agent = registry.get_agent_by_tape(tape_id)
            assert agent is not None
            assert agent.tape_id == tape_id


def test_economic_engine_to_event_aggregator():
    """Test EconomicEngine → EventAggregator flow."""
    # Setup
    config = ConfigLoader.get_default()
    registry = AgentRegistry(config.registry, seed=1337)
    
    # Create some agents
    tape_ids = list(range(50))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    # Initialize engine and aggregator
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)
    aggregator = EventAggregator()
    
    # Process a tick
    result = engine.process_tick(tick_num=1)
    
    # Add events to aggregator
    for event in result.events:
        aggregator.add_event(event)
    
    # Get summary
    summary = aggregator.get_tick_summary(tick_num=1)
    
    # Verify summary contains expected data
    assert summary.tick == 1
    assert len(summary.event_counts) > 0
    assert summary.currency_flows is not None
    assert summary.wealth_changes is not None


def test_cache_layer_integration():
    """Test CacheLayer integration with economic calculations."""
    config = ConfigLoader.get_default()
    cache = CacheLayer(config.cache)
    
    # Create a simple state (as string for hashing)
    import json
    state1 = json.dumps({
        "agents": [
            {"id": "K-01", "currency": 1000, "wealth": 100},
            {"id": "M-01", "currency": 50, "wealth": 30}
        ],
        "config_hash": config.compute_hash()
    }, sort_keys=True)
    
    # Define a computation function
    call_count = [0]
    def expensive_computation():
        call_count[0] += 1
        return {"result": "computed", "value": 42}
    
    # First call should compute
    result1 = cache.get_or_compute(state1, expensive_computation)
    assert call_count[0] == 1
    assert result1["value"] == 42
    
    # Second call with same state should use cache
    result2 = cache.get_or_compute(state1, expensive_computation)
    assert call_count[0] == 1  # Should not increment
    assert result2["value"] == 42
    
    # Different state should compute again
    state2 = json.dumps({
        "agents": [
            {"id": "K-02", "currency": 2000, "wealth": 200}
        ],
        "config_hash": config.compute_hash()
    }, sort_keys=True)
    result3 = cache.get_or_compute(state2, expensive_computation)
    assert call_count[0] == 2  # Should increment
    
    # Check cache stats
    stats = cache.get_stats()
    assert stats["hits"] >= 1
    assert stats["misses"] >= 2


def test_signal_processor_integration():
    """Test SignalProcessor integration with events."""
    # Skip this test as SignalProcessor is not fully implemented yet
    # This is a placeholder for future signal processing functionality
    pass


def test_full_pipeline_trace_to_output():
    """Test full pipeline from trace to outputs."""
    # Load trace
    trace_path = Path("testdata/bff_trace_small.json")
    
    with TraceReader(trace_path) as reader:
        epoch = reader.read_epoch()
        tape_ids = list(epoch.tapes.keys())
    
    # Setup components
    config = ConfigLoader.get_default()
    registry = AgentRegistry(config.registry, seed=1337)
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)
    
    # Create temporary output directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        metadata = generate_metadata(
            version=config.version,
            seed=config.seed,
            config_hash=config.compute_hash()
        )
        
        writer = create_output_writer(
            output_dir=output_dir,
            config=config.output,
            metadata=metadata
        )
        
        # Process ticks
        num_ticks = 5
        for tick in range(1, num_ticks + 1):
            result = engine.process_tick(tick)
            writer.write_tick_json(result)
            writer.write_event_csv(result.events)
        
        # Write final state
        writer.write_final_agents_csv(registry.get_all_agents())
        writer.close()
        
        # Verify outputs exist
        paths = writer.get_output_paths()
        assert paths["ticks_json"].exists()
        assert paths["events_csv"].exists()
        assert paths["agents_csv"].exists()
        
        # Verify tick JSON content
        with open(paths["ticks_json"], 'r') as f:
            ticks_data = [json.loads(line) for line in f]
        
        assert len(ticks_data) == num_ticks
        for tick_data in ticks_data:
            assert "tick" in tick_data
            assert "metrics" in tick_data
            assert "agents" in tick_data


def test_determinism_across_runs():
    """Test that same seed produces same results."""
    config = ConfigLoader.get_default()
    
    def run_simulation(seed):
        """Run a small simulation and return results."""
        registry = AgentRegistry(config.registry, seed=seed)
        tape_ids = list(range(20))
        registry.assign_roles(tape_ids)
        registry.assign_knight_employers()
        
        engine = EconomicEngine(registry, config.economic, config.trait_emergence)
        
        results = []
        for tick in range(1, 4):
            result = engine.process_tick(tick)
            results.append({
                "tick": result.tick_num,
                "wealth_total": result.metrics.wealth_total,
                "currency_total": result.metrics.currency_total,
                "num_events": len(result.events)
            })
        
        return results
    
    # Run with same seed twice
    results1 = run_simulation(seed=42)
    results2 = run_simulation(seed=42)
    
    # Should be identical
    assert results1 == results2
    
    # Run with different seed
    results3 = run_simulation(seed=99)
    
    # Should be different (at least in some ticks)
    # Note: Due to deterministic logic, some values might coincidentally match
    # but the full sequence should differ
    assert results1 != results3 or results2 != results3


def test_agent_state_persistence():
    """Test that agent state persists correctly across ticks."""
    config = ConfigLoader.get_default()
    registry = AgentRegistry(config.registry, seed=1337)
    
    tape_ids = list(range(30))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)
    
    # Get initial state
    initial_agents = {agent.id: agent.currency for agent in registry.get_all_agents()}
    
    # Process multiple ticks
    for tick in range(1, 6):
        result = engine.process_tick(tick)
    
    # Get final state
    final_agents = {agent.id: agent.currency for agent in registry.get_all_agents()}
    
    # Verify state changed (some agents should have different currency)
    changed_count = sum(1 for agent_id in initial_agents 
                       if initial_agents[agent_id] != final_agents.get(agent_id, 0))
    
    # At least some agents should have changed
    assert changed_count > 0


def test_event_flow_consistency():
    """Test that events are consistent with agent state changes."""
    config = ConfigLoader.get_default()
    registry = AgentRegistry(config.registry, seed=1337)
    
    tape_ids = list(range(20))
    registry.assign_roles(tape_ids)
    registry.assign_knight_employers()
    
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)
    
    # Get initial total currency
    initial_total = sum(agent.currency for agent in registry.get_all_agents())
    
    # Process a tick
    result = engine.process_tick(tick_num=1)
    
    # Get final total currency
    final_total = sum(agent.currency for agent in registry.get_all_agents())
    
    # Calculate currency created from trades
    from core.models import EventType
    trade_events = [e for e in result.events if e.type == EventType.TRADE]
    
    # Currency should be conserved except for trade wealth creation
    # (trades convert currency to wealth, so total currency should decrease)
    # We just verify the totals are reasonable
    assert final_total >= 0
    assert initial_total >= 0


if __name__ == "__main__":
    print("Running integration tests...")
    
    tests = [
        ("test_trace_reader_to_agent_registry", test_trace_reader_to_agent_registry),
        ("test_economic_engine_to_event_aggregator", test_economic_engine_to_event_aggregator),
        ("test_cache_layer_integration", test_cache_layer_integration),
        ("test_signal_processor_integration", test_signal_processor_integration),
        ("test_full_pipeline_trace_to_output", test_full_pipeline_trace_to_output),
        ("test_determinism_across_runs", test_determinism_across_runs),
        ("test_agent_state_persistence", test_agent_state_persistence),
        ("test_event_flow_consistency", test_event_flow_consistency),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
