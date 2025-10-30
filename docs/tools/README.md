---
title: "Analysis and Development Tools"
description: "Documentation for Python analysis tools and utilities"
version: "0.1.0-m.inc"
last_updated: "2025-01-27"
source_files:
  - python/analyse_soup.py:1-50
  - python/find_selfrep_parents.py:1-100
  - python/bff-visualizer.html:1-50
  - python/cond_exp.py:1-30
  - python/cond_prob.py:1-30
dependencies:
  - python_tools.md
  - visualization.md
  - debugging.md
cross_references:
  - ../api/python/
  - ../architecture/README.md
---

# Analysis and Development Tools

CuBFF provides a comprehensive suite of Python-based analysis tools for studying the evolution of self-replicating programs. These tools enable detailed analysis of population dynamics, replication events, and program behavior.

## Quick Navigation

- [Python Analysis Tools](python_tools.md) - Core analysis functions and utilities
- [Visualization](visualization.md) - Web-based and command-line visualization
- [Debugging](debugging.md) - Debugging and development tools

## Tool Categories

### Analysis Tools Category
- Soup Analysis: Population entropy, compression, diversity metrics
- Replication Detection: Finding and analyzing self-replicating programs
- Statistical Analysis: Conditional probabilities, expectation calculations
- Program Classification: Categorizing program types and behaviors

### Visualization Tools Category
- Web Visualizer: Interactive browser-based visualization
- Command-Line Display: Terminal-based program visualization
- Trace Analysis: Step-by-step execution visualization
- Population Monitoring: Real-time population state display

### Debugging Tools Category
- Single Program Testing: Isolated program execution and debugging
- Trace Generation: Detailed execution traces for analysis
- State Inspection: Program state examination and modification
- Performance Profiling: Execution time and memory usage analysis

## Core Analysis Tools

### `analyse_soup.py`
Purpose: Comprehensive soup analysis and metrics calculation

Key Functions:
```python
def analyse_soup(soup: List[bytearray]) -> Dict[str, Any]:
    """Analyze population and return comprehensive metrics"""

def shannon_entropy_bits(population: List[bytearray]) -> float:
    """Calculate Shannon entropy in bits per byte"""

def compress_ratio(population: List[bytearray]) -> float:
    """Calculate compression ratio using zlib"""

def opcode_histogram(population: List[bytearray]) -> Counter:
    """Generate histogram of opcode usage"""
```

Source: `python/analyse_soup.py:1-213`

Usage:
```python
from analyse_soup import analyse_soup

# Analyze population
soup = [bytearray(64) for _ in range(1000)]
# ... populate soup ...

metrics = analyse_soup(soup)
print(f"Entropy: {metrics['entropy']:.3f}")
print(f"Compression: {metrics['compression']:.3f}")
```

### `find_selfrep_parents.py`
Purpose: Detection and analysis of self-replicating programs

Key Functions:
```python
def find_selfrep_parents(soup: List[bytearray], threshold: int = 10) -> List[Tuple[int, int]]:
    """Find potential self-replicating programs"""

def test_replication(candidate: bytes, food: bytes, steps: int = 1000) -> bool:
    """Test if candidate can replicate using food"""

def analyze_replicator(replicator: bytes) -> Dict[str, Any]:
    """Analyze replicator structure and behavior"""
```

Source: `python/find_selfrep_parents.py:1-370`

Usage:
```python
from find_selfrep_parents import find_selfrep_parents

# Find replicators
replicators = find_selfrep_parents(soup, threshold=5)
print(f"Found {len(replicators)} potential replicators")

for i, (parent1, parent2) in enumerate(replicators):
    print(f"Replicator {i}: programs {parent1} and {parent2}")
```

### `cond_exp.py` and `cond_prob.py`
Purpose: Statistical analysis of program behavior

Key Functions:
```python
# cond_exp.py
def conditional_expectation(data: List[float], condition: Callable) -> float:
    """Calculate conditional expectation"""

# cond_prob.py
def conditional_probability(events: List[bool], condition: Callable) -> float:
    """Calculate conditional probability"""
```

Source: `python/cond_exp.py:1-68`, `python/cond_prob.py:1-108`

## Visualization Tools

### `bff-visualizer.html`
Purpose: Interactive web-based visualization of BFF programs

Features:
- Real-time program execution visualization
- Tape state display with color coding
- Head position tracking
- Step-by-step execution control
- Export capabilities for traces

Source: `python/bff-visualizer.html:1-923`

Usage:
```bash
# Open in web browser
python -m http.server 8000
# Navigate to http://localhost:8000/python/bff-visualizer.html
```

### Command-Line Visualization
Purpose: Terminal-based program display and analysis

Tools:
- `print_program()`: Display program with highlighting
- `show_execution()`: Step-by-step execution display
- `population_summary()`: Population overview

Usage:
```python
from bff_interpreter import print_program, show_execution

# Display program
print_program(head0_pos, head1_pos, pc_pos, tape)

# Show execution
show_execution(tape, steps=100, debug=True)
```

## Debugging Tools

### `run_single_bff_program.py`
Purpose: Isolated testing of individual BFF programs

Features:
- Single program execution
- Debug output control
- Step limit configuration
- Trace generation

Source: `python/run_single_bff_program.py:1-40`

Usage:
```bash
python run_single_bff_program.py program.bff 1000
```

### `save_bff_trace.py`
Purpose: Generate detailed execution traces

Features:
- Binary trace format
- State snapshots
- Performance metrics
- Replay capabilities

Source: `python/save_bff_trace.py:1-27`

Usage:
```python
from save_bff_trace import save_trace

# Save execution trace
save_trace(tape, "trace.bff", steps=1000)
```

## Advanced Analysis

### `selfrep_spawning.py`
Purpose: Analysis of self-replication spawning patterns

Key Functions:
```python
def analyze_spawning_patterns(soup: List[bytearray]) -> Dict[str, Any]:
    """Analyze how replicators spawn and spread"""

def track_replication_events(traces: List[Dict]) -> List[ReplicationEvent]:
    """Track replication events over time"""
```

Source: `python/selfrep_spawning.py:1-67`

### `time_to_sr.py`
Purpose: Analysis of time-to-self-replication metrics

Key Functions:
```python
def calculate_time_to_sr(soup: List[bytearray]) -> Dict[str, float]:
    """Calculate time-to-self-replication statistics"""

def analyze_sr_distribution(events: List[ReplicationEvent]) -> Dict[str, Any]:
    """Analyze distribution of self-replication events"""
```

Source: `python/time_to_sr.py:1-77`

## Tool Integration

### Analysis Pipeline
```python
# Complete analysis pipeline
from analyse_soup import analyse_soup
from find_selfrep_parents import find_selfrep_parents
from cond_exp import conditional_expectation

# 1. Analyze population
metrics = analyse_soup(soup)

# 2. Find replicators
replicators = find_selfrep_parents(soup, threshold=5)

# 3. Calculate conditional metrics
if replicators:
    sr_rate = conditional_expectation(
        [1 if i in [r[0] for r in replicators] else 0 for i in range(len(soup))],
        lambda x: x > 0
    )
    print(f"Self-replication rate: {sr_rate:.3f}")
```

### Visualization Pipeline
```python
# Complete visualization pipeline
from bff_interpreter import BFFVM, print_program
from analyse_soup import opcode_histogram

# 1. Run program
vm = BFFVM(tape)
result = vm.run()

# 2. Display execution
print_program(vm.head0, vm.head1, vm.pc, result.tape)

# 3. Show population statistics
hist = opcode_histogram(soup)
print("Opcode usage:", dict(hist.most_common(10)))
```

## Performance Considerations

### Memory Usage
- Large Populations: Use streaming analysis for >10K programs
- Trace Files: Compress traces to save disk space
- Visualization: Limit display to subset for performance

### CPU Usage
- Parallel Analysis: Use multiprocessing for large datasets
- Caching: Cache expensive calculations
- Sampling: Use statistical sampling for very large populations

## Troubleshooting

### Common Issues
1. Memory Errors: Reduce population size or use streaming
2. Slow Visualization: Limit display range or use sampling
3. Trace File Size: Use compression or limit trace length

### Debug Mode
```python
# Enable debug output
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debug flags
vm = BFFVM(tape, debug=True)
result = vm.run()
```

---

*For detailed usage examples and advanced techniques, see the individual tool documentation pages.*
