---
title: "CuBFF Documentation Hub"
description: "Complete documentation for CuBFF and Mercenaries Incorporated (m.inc) version"
version: "0.1.0-m.inc"
last_updated: "2025-01-27"
source_files:
  - main.cc
  - python/bff_interpreter.py
  - Makefile
  - CMakeLists.txt
dependencies:
  - architecture/README.md
  - build/README.md
  - api/README.md
  - tools/README.md
  - os/README.md
---

# CuBFF Documentation Hub

Welcome to the comprehensive documentation for CuBFF (CUDA Brainfuck Forth) and its enhanced version, Mercenaries Incorporated (m.inc). This documentation is optimized for AI agent consumption and cross-platform development.

## Quick Navigation

### [Architecture](0.0.1/architecture/README.md)
Core concepts, implementation details, and design principles
- [BFF Fundamentals](architecture/core_concepts.md)
- [Technical Implementation](architecture/implementation/)
- [m.inc Extensions](architecture/extensions/)
- [Research Background](architecture/research/)

### [Build Systems](build/README.md)
Cross-platform build instructions and dependency management
- [Cross-Platform Guide](build/cross_platform.md)
- [Dependencies](build/dependencies.md)
- [Troubleshooting](build/troubleshooting.md)

### [API Reference](0.0.1/api/README.md)
Complete API documentation for C++ and Python interfaces
- [C++ API](api/cpp/)
- [Python API](api/python/)
- [Code Examples](api/examples/)

### [Tools](tools/README.md)
Analysis tools, visualization, and debugging utilities
- [Python Analysis Tools](tools/python_tools.md)
- [Visualization](tools/visualization.md)
- [Debugging](tools/debugging.md)

### [Platform Guides](build/os/README.md)
Operating system specific installation and configuration
- [Windows](build/os/windows)
- [macOS](os/macos/)
- [Linux](os/linux/)

## Project Overview

CuBFF is an implementation of Blaise Agüera y Arcas' BFF (Brainfuck Forth) experiment, demonstrating the emergence of self-replicating programs from random code interactions. The project includes:

- **Core Implementation**: C++/CUDA with Python bindings
- **Language Support**: BFF, Forth, SUBLEQ, Z80 emulation
- **Cross-Platform**: Windows (native + WSL2), macOS, Linux
- **Analysis Tools**: Python-based visualization and analysis

## Source Code Structure

```
cubff/
 main.cc                    # Main entry point
 common.h/.cc              # Core VM implementation
 *.cu                      # Language implementations
 python/                   # Python tools and bindings
    bff_interpreter.py    # Pure Python BFF interpreter
    analyse_soup.py       # Soup analysis tools
    bff-visualizer.html   # Web-based visualization
 Makefile                  # Primary build system
 CMakeLists.txt           # CMake build configuration
 build_windows.ps1        # Windows PowerShell build script
```

## Quick Start

### Prerequisites
- C++17 compiler (GCC 8+, Clang 6+, MSVC 2017+)
- Brotli compression library
- OpenMP (for parallel processing)
- Python 3.8+ (for analysis tools)

### Build and Run
```bash
# Cross-platform build
make CUDA=0

# Run simulation
./bin/main --lang bff_noheads

# Python analysis
python python/analyse_soup.py
```

## m.inc Enhancements

The Mercenaries Incorporated version includes:

- Enhanced documentation architecture
- Improved cross-platform support
- Extended analysis tools
- Better visualization capabilities
- Comprehensive API documentation

## Documentation Features

### AI Agent Optimized
- Structured YAML frontmatter
- Machine-readable cross-references
- Consistent naming conventions
- Version-controlled documentation

### Cross-Platform Coverage
- Unified build instructions
- Platform-specific variants
- Dependency management
- Troubleshooting guides

### GitHub-Style MOC
- Hierarchical navigation
- Automatic link generation
- Citation management
- Search optimization

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and contribution instructions.

## Changelog

- [Version 0.1.0-m.inc](0.0.1/changelogs/0.1.0-m.inc.md) - Mercenaries Incorporated enhancements
- [Version 0.0.1](0.0.1/changelogs/0.0.1.md) - Initial release with build fixes

## License

This project is licensed under the Apache License 2.0. See [LICENSE](../LICENSE) for details.

---

*This documentation is designed for AI agent consumption and cross-platform development. For human-readable guides, see the platform-specific documentation in the [os/](build/os) directory.*
