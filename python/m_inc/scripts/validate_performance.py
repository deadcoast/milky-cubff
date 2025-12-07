#!/usr/bin/env python3
"""
Performance validation script for M|inc system.
Benchmarks tick processing speed, cache hit rates, and memory usage.
"""

import json
import sys
import time
import tracemalloc
from pathlib import Path
import tempfile
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from adapters.trace_reader import TraceReader
from core.agent_registry import AgentRegistry
from core.economic_engine import EconomicEngine
from core.config import ConfigLoader
from core.cache import CacheLayer


class PerformanceMetrics:
    def __init__(self):
        self.metrics = {}
        self.benchmarks = []
    
    def add_metric(self, name: str, value: float, unit: str, threshold: float = None):
        self.metrics[name] = {
            'value': value,
            'unit': unit,
            'threshold': threshold,
            'passed': threshold is None or value <= threshold
        }
    
    def add_benchmark(self, name: str, duration: float, operations: int):
        ops_per_sec = operations / duration if duration > 0 else 0
        self.benchmarks.append({
            'name': name,
            'duration': duration,
            'operations': operations,
            'ops_per_sec': ops_per_sec
        })
    
    def print_summary(self):
        print("\n" + "="*70)
        print("PERFORMANCE VALIDATION SUMMARY")
        print("="*70)
        
        print("\nMetrics:")
        for name, data in self.metrics.items():
            status = "✓" if data['passed'] else "✗"
            threshold_str = f" (threshold: {data['threshold']} {data['unit']})" if data['threshold'] else ""
            print(f"  {status} {name}: {data['value']:.2f} {data['unit']}{threshold_str}")
        
        print("\nBenchmarks:")
        for bench in self.benchmarks:
            print(f"  • {bench['name']}:")
            print(f"    Duration: {bench['duration']:.3f}s")
            print(f"    Operations: {bench['operations']}")
            print(f"    Throughput: {bench['ops_per_sec']:.1f} ops/sec")
        
        print("="*70)
        
        # Check if all metrics passed
        all_passed = all(m['passed'] for m in self.metrics.values())
        return all_passed


def benchmark_tick_processing(trace_path: Path, config_path: Path, 
                              num_ticks: int = 100) -> Tuple[float, int, Dict]:
    """Benchmark tick processing speed."""
    print(f"\nBenchmarking tick processing ({num_ticks} ticks)...")
    
    # Load configuration
    config = ConfigLoader.load(config_path)
    
    # Initialize components
    reader = TraceReader(trace_path)
    registry = AgentRegistry(config.registry, seed=config.seed)
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)
    
    # Read initial epoch to populate registry
    epoch_data = reader.read_epoch()
    tape_ids = list(epoch_data.tapes.keys())
    registry.assign_roles(tape_ids)
    
    # Benchmark tick processing
    start_time = time.time()
    
    for tick_num in range(1, num_ticks + 1):
        result = engine.process_tick(tick_num)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Get cache stats if available
    cache_stats = {}
    if hasattr(engine, 'cache') and engine.cache:
        cache_stats = engine.cache.get_stats()
    
    return duration, num_ticks, cache_stats


def benchmark_memory_usage(trace_path: Path, config_path: Path, 
                           num_ticks: int = 100) -> Tuple[float, float]:
    """Benchmark memory usage during processing."""
    print(f"\nBenchmarking memory usage ({num_ticks} ticks)...")
    
    # Start memory tracking
    tracemalloc.start()
    
    # Load configuration
    config = ConfigLoader.load(config_path)
    
    # Initialize components
    reader = TraceReader(trace_path)
    registry = AgentRegistry(config.registry, seed=config.seed)
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)
    
    # Read initial epoch
    epoch_data = reader.read_epoch()
    tape_ids = list(epoch_data.tapes.keys())
    registry.assign_roles(tape_ids)
    
    # Get baseline memory
    baseline_current, baseline_peak = tracemalloc.get_traced_memory()
    
    # Process ticks
    for tick_num in range(1, num_ticks + 1):
        result = engine.process_tick(tick_num)
    
    # Get final memory
    final_current, final_peak = tracemalloc.get_traced_memory()
    
    tracemalloc.stop()
    
    # Convert to MB
    baseline_mb = baseline_current / (1024 * 1024)
    peak_mb = final_peak / (1024 * 1024)
    
    return baseline_mb, peak_mb


def benchmark_cache_performance(trace_path: Path, config_path: Path,
                                num_ticks: int = 50) -> Dict:
    """Benchmark cache hit rates."""
    print(f"\nBenchmarking cache performance ({num_ticks} ticks)...")
    
    # Load configuration with cache enabled
    config = ConfigLoader.load(config_path)
    
    # Ensure cache is enabled
    if not config.cache.enabled:
        print("  ⚠ Cache not enabled in config, skipping cache benchmark")
        return {}
    
    # Initialize components
    reader = TraceReader(trace_path)
    registry = AgentRegistry(config.registry, seed=config.seed)
    engine = EconomicEngine(registry, config.economic, config.trait_emergence)
    
    # Read initial epoch
    epoch_data = reader.read_epoch()
    tape_ids = list(epoch_data.tapes.keys())
    registry.assign_roles(tape_ids)
    
    # Process ticks
    for tick_num in range(1, num_ticks + 1):
        result = engine.process_tick(tick_num)
    
    # Get cache stats
    if hasattr(engine, 'cache') and engine.cache:
        stats = engine.cache.get_stats()
        
        # Calculate hit rate
        total_requests = stats.get('hits', 0) + stats.get('misses', 0)
        hit_rate = (stats.get('hits', 0) / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': stats.get('hits', 0),
            'misses': stats.get('misses', 0),
            'hit_rate': hit_rate,
            'size': stats.get('size', 0)
        }
    
    return {}


def main():
    """Run performance validation tests."""
    print("M|inc Performance Validation")
    print("="*70)
    
    metrics = PerformanceMetrics()
    
    # Setup paths
    base_dir = Path(__file__).parent
    testdata_dir = base_dir / 'testdata'
    config_path = base_dir / 'config' / 'minc_default.yaml'
    
    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        return 1
    
    # Use trace_100tick for benchmarking
    trace_path = testdata_dir / 'trace_100tick.json'
    
    if not trace_path.exists():
        print(f"✗ Trace file not found: {trace_path}")
        print("  Trying alternative trace...")
        trace_path = testdata_dir / 'trace_10tick.json'
        
        if not trace_path.exists():
            print(f"✗ No suitable trace files found")
            return 1
    
    print(f"Using trace: {trace_path.name}")
    
    # Benchmark 1: Tick processing speed
    try:
        duration, num_ticks, cache_stats = benchmark_tick_processing(
            trace_path, config_path, num_ticks=50
        )
        
        avg_tick_time = (duration / num_ticks) * 1000  # Convert to ms
        ticks_per_sec = num_ticks / duration
        
        metrics.add_metric("Avg tick time", avg_tick_time, "ms", threshold=100.0)
        metrics.add_benchmark("Tick processing", duration, num_ticks)
        
        print(f"  ✓ Processed {num_ticks} ticks in {duration:.2f}s")
        print(f"  ✓ Average: {avg_tick_time:.2f}ms per tick")
        print(f"  ✓ Throughput: {ticks_per_sec:.1f} ticks/sec")
        
    except Exception as e:
        print(f"  ✗ Tick processing benchmark failed: {e}")
        traceback.print_exc()
    
    # Benchmark 2: Memory usage
    try:
        baseline_mb, peak_mb = benchmark_memory_usage(
            trace_path, config_path, num_ticks=50
        )
        
        metrics.add_metric("Baseline memory", baseline_mb, "MB")
        metrics.add_metric("Peak memory", peak_mb, "MB", threshold=200.0)
        
        print(f"  ✓ Baseline memory: {baseline_mb:.2f} MB")
        print(f"  ✓ Peak memory: {peak_mb:.2f} MB")
        
    except Exception as e:
        print(f"  ✗ Memory benchmark failed: {e}")
        traceback.print_exc()
    
    # Benchmark 3: Cache performance
    try:
        cache_stats = benchmark_cache_performance(
            trace_path, config_path, num_ticks=50
        )
        
        if cache_stats:
            hit_rate = cache_stats.get('hit_rate', 0)
            metrics.add_metric("Cache hit rate", hit_rate, "%", threshold=None)
            
            print(f"  ✓ Cache hits: {cache_stats.get('hits', 0)}")
            print(f"  ✓ Cache misses: {cache_stats.get('misses', 0)}")
            print(f"  ✓ Hit rate: {hit_rate:.1f}%")
            print(f"  ✓ Cache size: {cache_stats.get('size', 0)} entries")
        
    except Exception as e:
        print(f"  ✗ Cache benchmark failed: {e}")
        traceback.print_exc()
    
    # Print summary
    success = metrics.print_summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
