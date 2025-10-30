---
title: "API Reference"
description: "Complete API documentation for C++ and Python interfaces"
version: "0.1.0-m.inc"
last_updated: "2025-01-27"
source_files:
  - main.cc:1-50
  - common.h:1-100
  - common.cc:1-150
  - python/bff_interpreter.py:1-100
  - cubff_py.cc:1-50
dependencies:
  - cpp/
  - python/
  - examples/
cross_references:
  - ../architecture/README.md
  - ../tools/README.md
---

# API Reference

Complete API documentation for CuBFF's C++ and Python interfaces. This reference covers all public APIs, data structures, and usage patterns.

## Quick Navigation

- [C++ API](cpp/) - Core C++ interfaces and classes
- [Python API](python/) - Python bindings and analysis tools
- [Code Examples](examples/) - Usage examples and tutorials

## API Overview

### Core Components

#### 1. Virtual Machine (`common.h`, `common.cc`)
- LanguageInterface: Base class for language implementations
- SimulationParams: Configuration for simulation runs
- SimulationState: Runtime state and metrics

#### 2. Language Implementations
- BFF: Brainfuck Forth implementation
- Forth: Stack-based language
- SUBLEQ: One-instruction computer
- Z80: 8080/Z80 emulation

#### 3. Python Interface
- bff_interpreter.py: Pure Python BFF implementation
- Analysis Tools: Soup analysis and visualization
- C++ Bindings: Python access to C++ functionality

## C++ API Reference

### Core Classes

#### `LanguageInterface`
```cpp
class LanguageInterface {
public:
    virtual void RunSingleProgram(const std::string& program, 
                                  size_t max_steps, 
                                  bool debug) = 0;
    virtual void RunSimulation(const SimulationParams& params,
                               const std::optional<std::string>& initial_program,
                               std::function<bool(const SimulationState&)> callback) = 0;
    virtual void PrintProgram(size_t tape_size,
                              const uint8_t* tape,
                              size_t program_size,
                              const size_t* separators,
                              size_t num_separators) = 0;
};
```

#### `SimulationParams`
```cpp
struct SimulationParams {
    size_t num_programs = 128 * 1024;
    std::optional<size_t> reset_interval;
    size_t seed = 0;
    std::optional<std::string> load_from;
    uint32_t mutation_prob = 0;
    bool permute_programs = true;
    bool fixed_shuffle = false;
    bool zero_init = false;
    bool eval_selfrep = false;
    std::optional<std::string> save_to;
    uint32_t save_interval = 256;
    uint32_t callback_interval = 64;
    std::vector<std::vector<size_t>> allowed_interactions;
};
```

#### `SimulationState`
```cpp
struct SimulationState {
    size_t epoch;
    double elapsed_s;
    size_t total_ops;
    double mops_s;
    double ops_per_run;
    size_t brotli_size;
    double brotli_bpb;
    double bytes_per_prog;
    double h0;
    double higher_entropy;
    std::vector<uint8_t> soup;
    std::vector<uint8_t> replication_per_prog;
    std::vector<std::pair<std::string, double>> frequent_bytes;
    std::vector<std::pair<std::string, double>> uncommon_bytes;
    std::vector<std::array<uint8_t, 3>> byte_colors;
};
```

### Language Factory

#### `GetLanguage(const std::string& name)`
```cpp
const LanguageInterface* GetLanguage(const std::string& name);
```

Parameters:
- `name`: Language identifier ("bff", "bff_noheads", "forth", "subleq", "rsubleq4")

Returns: Pointer to language implementation

Source: `common.cc:200-220`

### Utility Functions

#### `ResetColors()`
```cpp
const char* ResetColors();
```

Returns: ANSI color reset sequence

Source: `common.cc:50-60`

## Python API Reference

### API Core Classes

#### `BffOp` (Enum)
```python
class BffOp(Enum):
    LOOP_START = 0
    LOOP_END = 1
    PLUS = 2
    MINUS = 3
    COPY01 = 4
    COPY10 = 5
    DEC0 = 6
    INC0 = 7
    DEC1 = 8
    INC1 = 9
    NULL = 10
    NOOP = 11
```

Source: `python/bff_interpreter.py:30-43`

#### `BFFVM` (Virtual Machine)
```python
class BFFVM:
    def __init__(self, tape: bytearray, step_limit: int = 8192,
                 init_head0: int = 0, init_head1: int = 64):
        """Initialize BFF virtual machine"""
    
    def run(self) -> RunResult:
        """Execute BFF program and return results"""
    
    def _heads_in_bounds(self) -> bool:
        """Check if both heads are within tape bounds"""
    
    def _pc_in_bounds(self) -> bool:
        """Check if program counter is within tape bounds"""
```

Source: `python/bff_interpreter.py:64-196`

#### `RunResult` (Data Class)
```python
@dataclass
class RunResult:
    tape: bytearray
    steps: int
    reason: HaltReason
    oob_pointer: Optional[str] = None
    unmatched_at: Optional[int] = None
```

Source: `python/bff_interpreter.py:56-63`

### Core Functions

#### `parse(bff_str: str) -> bytearray`
```python
def parse(bff_str: str) -> bytearray:
    """Parse a BFF program string into a bytearray of instructions"""
```

Parameters:
- `bff_str`: BFF program string

Returns: 128-byte program tape

Source: `python/bff_interpreter.py:99-152`

#### `evaluate(tape: bytearray, stepcount: int, debug: bool = False) -> int`
```python
def evaluate(tape: bytearray, stepcount: int, debug: bool = False) -> int:
    """Evaluate the BFF program for a given number of steps"""
```

Parameters:
- `tape`: 128-byte program tape
- `stepcount`: Maximum steps to execute
- `debug`: Enable debug output

Returns: Number of actual steps executed

Source: `python/bff_interpreter.py:284-327`

#### `evaluate_and_save(tape: bytearray, file_path: str, stepcount: int, debug: bool = False) -> int`
```python
def evaluate_and_save(tape: bytearray, file_path: str, stepcount: int, debug: bool = False) -> int:
    """Evaluate BFF program and save execution trace"""
```

Parameters:
- `tape`: 128-byte program tape
- `file_path`: Path to save trace file
- `stepcount`: Maximum steps to execute
- `debug`: Enable debug output

Returns: Number of actual steps executed

Source: `python/bff_interpreter.py:328-396`

### Analysis Functions

#### `shannon_entropy_bits(population: List[bytearray]) -> float`
```python
def shannon_entropy_bits(population: List[bytearray]) -> float:
    """Calculate Shannon entropy of population in bits"""
```

Source: `python/analyse_soup.py:50-70`

#### `compress_ratio(population: List[bytearray]) -> float`
```python
def compress_ratio(population: List[bytearray]) -> float:
    """Calculate compression ratio of population"""
```

Source: `python/analyse_soup.py:72-85`

#### `find_selfrep_parents(soup: List[bytearray], threshold: int = 10) -> List[Tuple[int, int]]`
```python
def find_selfrep_parents(soup: List[bytearray], threshold: int = 10) -> List[Tuple[int, int]]:
    """Find potential self-replicating programs in soup"""
```

Source: `python/find_selfrep_parents.py:100-150`

## Usage Examples

### Basic C++ Usage
```cpp
#include "common.h"

// Get language implementation
const LanguageInterface* lang = GetLanguage("bff_noheads");

// Run single program
lang->RunSingleProgram("++[>+<-]", 1000, true);

// Run simulation
SimulationParams params;
params.num_programs = 1000;
params.seed = 42;
lang->RunSimulation(params, std::nullopt, [](const SimulationState& state) {
    return state.epoch > 1000;
});
```

### Basic Python Usage
```python
from bff_interpreter import BFFVM, parse, evaluate

# Parse and run program
program = parse("++[>+<-]")
vm = BFFVM(program)
result = vm.run()

print(f"Executed {result.steps} steps")
print(f"Final tape: {result.tape.hex()}")
```

### Analysis Example
```python
from analyse_soup import analyse_soup, find_selfrep_parents

# Analyze population
soup = [bytearray(64) for _ in range(1000)]
# ... populate soup ...

# Find self-replicators
replicators = find_selfrep_parents(soup, threshold=5)
print(f"Found {len(replicators)} potential replicators")

# Calculate metrics
entropy = shannon_entropy_bits(soup)
compression = compress_ratio(soup)
print(f"Entropy: {entropy:.3f}, Compression: {compression:.3f}")
```

## Error Handling

### C++ Exceptions
- Invalid Language: Throws `std::invalid_argument`
- File I/O Errors: Throws `std::runtime_error`
- Memory Errors: Throws `std::bad_alloc`

### Python Exceptions
- ValueError: Invalid program size or parameters
- FileNotFoundError: Missing trace files
- RuntimeError: VM execution errors

## Performance Considerations

### C++ Performance
- CUDA Acceleration: 10-100x speedup on GPU
- Memory Usage: ~1MB per 1000 programs
- Thread Safety: Not thread-safe, use separate instances

### Python Performance
- Pure Python: Slower but more flexible
- C++ Bindings: Near-native performance
- Memory Usage: Higher due to Python overhead

---

*For detailed implementation examples, see the [Code Examples](examples/) section.*
