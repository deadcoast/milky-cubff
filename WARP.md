# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

CuBFF is a (optionally) CUDA-based implementation of self-modifying programs demonstrating emergence of self-replicators. Based on the "Computational Life: How Well-formed, Self-replicating Programs Emerge from Simple Interaction" paper ([arXiv:2406.19108](https://arxiv.org/abs/2406.19108)).

**Core languages implemented:**
- BFF (Brainfuck Forth) - primary language with multiple variants
- Forth - stack-based language
- SUBLEQ - single-instruction architecture
- Various BFF derivatives (bff_noheads, bff8, bff_perm, etc.)

## Build Commands

### Standard Build (macOS/Linux)
```bash
# CPU-only build (default on macOS)
make CUDA=0

# CUDA build (Linux only, requires CUDA toolkit)
make

# Clean build artifacts
make clean
```

### CMake Build (Cross-platform)
```bash
mkdir build && cd build
cmake .. -DUSE_CUDA=OFF
cmake --build . --config Release
```

### Windows Build
```bash
# WSL2 (recommended)
wsl
sudo apt install build-essential libbrotli-dev pkg-config
make CUDA=0

# PowerShell (native)
.\build_windows.ps1
```

### Python Bindings
```bash
# Build with Python bindings
make PYTHON=1 CUDA=0

# This creates bin/cubff.*.so which can be imported in Python
```

## Testing

### Run Tests
```bash
# Test a specific language (generates reference output if needed)
./test.sh bff_noheads

# The script expects testdata/<lang>.txt to exist
# Generate reference data with:
./bin/main --lang bff_noheads --max_epochs 256 --disable_output --log testdata/bff_noheads.txt --seed 10248
```

## Running Simulations

### Basic Usage
```bash
# Run simulation with a specific language
./bin/main --lang bff_noheads

# Run with specific parameters
./bin/main --lang bff_noheads --num 65536 --seed 42 --max_epochs 1000

# Run a single program with debugging
./bin/main --lang bff_noheads --run "program_string" --debug

# Save logs and checkpoints
./bin/main --lang bff_noheads --log output.log --checkpoint_dir ./checkpoints

# Load from checkpoint
./bin/main --lang bff_noheads --load checkpoint_file.bin
```

### Important Flags
- `--lang <name>`: Language to run (bff, bff_noheads, forth, subleq, etc.)
- `--num <n>`: Number of programs in soup (default: 128*1024)
- `--seed <n>`: Random seed
- `--max_epochs <n>`: Maximum number of epochs to run
- `--mutation_prob <f>`: Mutation probability (default: 1/(256*16))
- `--run <prog>`: Run a single program
- `--debug`: Enable step-by-step debugging output
- `--log <file>`: Log file for metrics
- `--checkpoint_dir <dir>`: Directory for periodic checkpoints
- `--load <file>`: Load from previous checkpoint

## Architecture

### Core Abstractions

**Language Registration System:**
- Each language (*.cu file) implements a `Language` struct with static methods
- Uses `REGISTER(Language)` macro for automatic registration
- Languages are accessed via `GetLanguage(name)` which returns `LanguageInterface*`

**Dual-Mode Execution:**
The codebase supports both CUDA and CPU execution through preprocessor abstraction:
- `#ifdef __CUDACC__`: CUDA mode with kernel launches
- CPU mode uses OpenMP for parallelization
- `common_language.h` provides unified interface (`DeviceMemory`, `RUN`, `Synchronize`, etc.)

**Program Soup Model:**
- Fixed-size programs: `kSingleTapeSize = 64` bytes each
- Programs are stored in a contiguous "soup" array
- Each epoch: programs are paired, mutated, and executed
- Interaction between pairs allows self-replication
- Compression ratio (Brotli) tracks emergence of patterns

### Language Implementation Pattern

Each language (*.cu file) follows this structure:

1. **Op enum**: Defines instruction set
2. **Language struct**: 
   - `static const char* name()`: Language identifier
   - `static BffOp GetOpKind(char c)`: Parse opcodes
   - `static size_t Evaluate(uint8_t* tape, size_t stepcount, bool debug)`: Execute program
   - `static void InitByteColors()`: For visualization
   - `static std::vector<uint8_t> Parse(string)`: Parse program strings
3. **Registration**: `REGISTER(Language)` at end of file

### Key Files

**main.cc:**
- Command-line flag parsing system
- Main simulation loop orchestration
- Calls into language-specific implementations via `LanguageInterface`

**common.h / common.cc:**
- `SimulationParams`: Configuration for runs
- `SimulationState`: Metrics and current state
- `LanguageInterface`: Abstract interface all languages implement
- `Simulation<Language>`: Template implementing the interface

**common_language.h:**
- CUDA/CPU abstraction layer
- `DeviceMemory<T>`: Unified memory management
- `InitPrograms()`: Initialize random program soup
- `MutateAndRunPrograms()`: Core evolution kernel
- Random number generation (`SplitMix64`)

**bff.inc.h / forth.inc.h:**
- Shared implementation details for BFF and Forth variants
- Character representation and parsing logic
- Colorization for terminal output

### Python Integration

**cubff_py.cc:**
- Pybind11 bindings exposing C++ API to Python
- Exposes `SimulationParams`, `SimulationState`, `LanguageInterface`
- Allows running simulations and analysis from Python

**python/bff_interpreter.py:**
- Pure Python BFF interpreter (no C++ dependency)
- Used for analysis and validation
- Provides same interface as C++ version

**python/analyse_soup.py:**
- Analysis tools for soup state
- Entropy calculation, pattern detection
- Self-replicator identification

## Development Notes

### Adding a New Language

1. Create `newlang.cu` with Language struct
2. Implement required static methods (name, GetOpKind, Evaluate, Parse)
3. Add `REGISTER(NewLang)` at end
4. Language automatically available via `--lang newlang`

### CUDA vs CPU

- CUDA mode: programs execute in parallel on GPU
- CPU mode: OpenMP parallelizes across cores
- Same code compiles for both via abstraction macros
- Set `CUDA=0` in Makefile for CPU-only builds

### Checkpointing

Simulations save complete state including:
- All program contents (soup)
- Shuffle indices
- Epoch counter
- RNG seed state

Resume exactly where left off with `--load`.

### Self-Replication Threshold

`kSelfrepThreshold = 5` defines minimum copies for a program to be considered self-replicating. Tracked per-program in `replication_per_prog`.

## Dependencies

- **C++17 compiler** (GCC 8+, Clang 6+, MSVC 2017+)
- **Brotli library** (libbrotlienc, libbrotlicommon) - for compression metrics
- **OpenMP** - CPU parallelization (optional but recommended)
- **CUDA toolkit** - GPU acceleration (optional, Linux only)
- **Python 3.8+** - for Python bindings and analysis tools
- **pybind11** - C++/Python bindings (if building Python module)

## Documentation Structure

The `docs/` directory contains extensive documentation including:
- Architecture guides in `docs/architecture/`
- API reference in `docs/api/`
- Platform-specific guides in `docs/build/os/`
- Changelog and version history

Refer to `docs/README.md` for comprehensive documentation hub.
