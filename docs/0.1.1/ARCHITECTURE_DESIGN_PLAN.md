# Mercenaries Incorporated (m.inc) Documentation Architecture Design Plan

## Executive Summary

This document outlines a comprehensive documentation architecture for the CuBFF project, enhanced for the "Mercenaries Incorporated" (m.inc) version. The design prioritizes AI agent consumption, cross-platform compatibility, and GitHub-style MOC (Map of Contents) structure with proper inter-linking and citations.

## Current State Analysis

### Source Code Structure
- **Core Implementation**: C++/CUDA with Python bindings
- **Build Systems**: Makefile, CMakeLists.txt, PowerShell build script
- **Python Components**: Pure Python BFF interpreter, analysis tools, visualization
- **Cross-Platform**: Windows (native + WSL2), macOS, Linux support
- **Language Variants**: BFF, Forth, SUBLEQ, Z80 emulation

### Existing Documentation Gaps
- Inconsistent cross-referencing between source and docs
- Missing technical implementation details in architecture docs
- No unified MOC structure
- Limited build system documentation
- Python tools not properly documented
- OS-specific guides need better integration

## Design Principles

### 1. AI Agent Optimization
- Structured data formats (YAML frontmatter, JSON metadata)
- Consistent naming conventions
- Machine-readable cross-references
- Clear dependency mapping
- Version-controlled documentation

### 2. Cross-Platform Documentation
- Unified build instructions with platform-specific variants
- Consistent file structure across OS directories
- Clear dependency management
- Platform-specific troubleshooting

### 3. GitHub-Style MOC
- Hierarchical navigation structure
- Automatic link generation
- Citation management
- Version tracking
- Search optimization

## Documentation Architecture

### Root Structure
```
docs/
 README.md                    # Main MOC and project overview
 ARCHITECTURE_DESIGN_PLAN.md  # This document
 BUILD_SYSTEMS.md            # Unified build documentation
 API_REFERENCE.md            # Complete API documentation
 CONTRIBUTING.md             # Development guidelines
 CHANGELOG.md                # Version history
 architecture/               # Core architecture documentation
    README.md              # Architecture MOC
    core_concepts.md       # BFF fundamentals
    implementation/        # Technical implementation details
    extensions/            # m.inc specific enhancements
    research/              # Research background and papers
 build/                     # Build system documentation
    README.md             # Build system MOC
    cross_platform.md     # Cross-platform build guide
    dependencies.md       # Dependency management
    troubleshooting.md    # Build troubleshooting
 api/                      # API documentation
    README.md            # API MOC
    cpp/                 # C++ API reference
    python/              # Python API reference
    examples/            # Code examples
 os/                      # OS-specific documentation
    README.md           # OS MOC
    windows/            # Windows-specific docs
    macos/              # macOS-specific docs
    linux/              # Linux-specific docs
 tools/                   # Tool documentation
    README.md          # Tools MOC
    python_tools.md    # Python analysis tools
    visualization.md   # Visualization tools
    debugging.md       # Debugging tools
 changelogs/             # Version-specific changelogs
     README.md          # Changelog MOC
     0.0.1.md          # Existing changelog
     0.1.0-m.inc.md    # m.inc specific changes
```

## Detailed Module Specifications

### 1. Core Architecture Documentation

#### `docs/architecture/README.md`
```yaml
---
title: "CuBFF Architecture Overview"
description: "Core architecture and design principles for CuBFF and m.inc"
version: "0.1.0-m.inc"
last_updated: "2025-01-27"
dependencies:
  - core_concepts.md
  - implementation/
  - extensions/
  - research/
cross_references:
  - ../api/README.md
  - ../build/README.md
  - ../tools/README.md
---

# CuBFF Architecture Overview

## Quick Navigation
- [Core Concepts](core_concepts.md) - BFF fundamentals and design principles
- [Implementation Details](implementation/) - Technical implementation
- [m.inc Extensions](extensions/) - Mercenaries Incorporated enhancements
- [Research Background](research/) - Academic papers and references

## Architecture Principles
[Content with proper cross-linking]
```

#### `docs/architecture/core_concepts.md`
```yaml
---
title: "BFF Core Concepts"
description: "Fundamental concepts of the BFF language and execution model"
version: "0.1.0-m.inc"
source_files:
  - python/bff_interpreter.py
  - bff.cu
  - bff.inc.h
dependencies:
  - ../api/python/bff_interpreter.md
  - ../build/dependencies.md
---

# BFF Core Concepts

## Language Design
[Detailed explanation with code references]

## Execution Model
[VM architecture with source citations]

## Self-Modification
[Technical details with implementation references]
```

### 2. Build System Documentation

#### `docs/build/README.md`
```yaml
---
title: "Build Systems Overview"
description: "Comprehensive build system documentation for all platforms"
version: "0.1.0-m.inc"
source_files:
  - Makefile
  - CMakeLists.txt
  - build_windows.ps1
platforms:
  - windows
  - macos
  - linux
dependencies:
  - cross_platform.md
  - dependencies.md
  - troubleshooting.md
---

# Build Systems Overview

## Quick Start
[Platform-specific quick start guides]

## Detailed Guides
- [Cross-Platform Build](cross_platform.md)
- [Dependencies](dependencies.md)
- [Troubleshooting](troubleshooting.md)

## Source Code References
[Links to actual build files with line numbers]
```

#### `docs/build/cross_platform.md`
```yaml
---
title: "Cross-Platform Build Guide"
description: "Unified build instructions for Windows, macOS, and Linux"
version: "0.1.0-m.inc"
source_files:
  - Makefile:12-38
  - CMakeLists.txt:1-122
  - build_windows.ps1:1-96
platforms:
  - windows
  - macos
  - linux
dependencies:
  - ../os/windows/build-guide.md
  - ../os/macos/build-guide.md
  - ../os/linux/build-guide.md
---

# Cross-Platform Build Guide

## Build System Comparison
[Table comparing Makefile, CMake, and PowerShell approaches]

## Platform-Specific Instructions
[Detailed instructions with source code references]
```

### 3. API Documentation

#### `docs/api/README.md`
```yaml
---
title: "API Reference"
description: "Complete API documentation for C++ and Python interfaces"
version: "0.1.0-m.inc"
source_files:
  - main.cc
  - common.h
  - common.cc
  - python/bff_interpreter.py
  - cubff_py.cc
dependencies:
  - cpp/
  - python/
  - examples/
---

# API Reference

## Quick Navigation
- [C++ API](cpp/) - Core C++ interfaces
- [Python API](python/) - Python bindings and tools
- [Examples](examples/) - Code examples and tutorials

## Source Code Mapping
[Direct links to source files with line numbers]
```

#### `docs/api/python/bff_interpreter.md`
```yaml
---
title: "Python BFF Interpreter API"
description: "Complete API reference for the Python BFF interpreter"
version: "0.1.0-m.inc"
source_file: "python/bff_interpreter.py"
line_range: "1-477"
dependencies:
  - ../cpp/vm.md
  - ../../tools/python_tools.md
---

# Python BFF Interpreter API

## Class Reference
[Detailed class and method documentation with source citations]

## Usage Examples
[Code examples with line number references]
```

### 4. OS-Specific Documentation

#### `docs/os/README.md`
```yaml
---
title: "Operating System Specific Documentation"
description: "Platform-specific installation and build guides"
version: "0.1.0-m.inc"
platforms:
  - windows
  - macos
  - linux
dependencies:
  - windows/
  - macos/
  - linux/
---

# OS-Specific Documentation

## Platform Support Matrix
[Table showing feature support across platforms]

## Quick Platform Selection
[Decision tree for choosing platform-specific guides]
```

#### `docs/os/windows/README.md`
```yaml
---
title: "Windows Build and Installation"
description: "Complete Windows build guide with multiple options"
version: "0.1.0-m.inc"
source_files:
  - build_windows.ps1
  - CMakeLists.txt:30-40
  - Makefile:2-8
dependencies:
  - build-guide.md
  - quickstart.md
  - troubleshooting.md
---

# Windows Build Guide

## Build Options
[WSL2, Native Windows, CMake comparison]

## Step-by-Step Instructions
[Detailed instructions with source code references]
```

### 5. Tools Documentation

#### `docs/tools/README.md`
```yaml
---
title: "Analysis and Development Tools"
description: "Documentation for Python analysis tools and utilities"
version: "0.1.0-m.inc"
source_files:
  - python/analyse_soup.py
  - python/find_selfrep_parents.py
  - python/bff-visualizer.html
  - python/cond_exp.py
  - python/cond_prob.py
dependencies:
  - python_tools.md
  - visualization.md
  - debugging.md
---

# Analysis and Development Tools

## Tool Categories
[Analysis, Visualization, Debugging tools]

## Quick Reference
[Command-line usage and examples]
```

## Implementation Strategy

### Phase 1: Foundation (Week 1)
1. Create root MOC structure
2. Implement YAML frontmatter system
3. Set up cross-reference validation
4. Create basic template files

### Phase 2: Core Documentation (Week 2)
1. Complete architecture documentation
2. Implement build system docs
3. Create API reference structure
4. Add source code mapping

### Phase 3: Platform Integration (Week 3)
1. Complete OS-specific documentation
2. Integrate existing changelogs
3. Add tool documentation
4. Implement search optimization

### Phase 4: Enhancement and Validation (Week 4)
1. Add m.inc specific enhancements
2. Validate all cross-references
3. Implement automated link checking
4. Add version control integration

## Technical Implementation Details

### YAML Frontmatter Schema
```yaml
---
title: "Document Title"
description: "Brief description"
version: "0.1.0-m.inc"
last_updated: "YYYY-MM-DD"
source_files:
  - "path/to/file.ext:start_line-end_line"
dependencies:
  - "relative/path/to/doc.md"
cross_references:
  - "target_doc.md#section"
platforms:
  - "windows"
  - "macos" 
  - "linux"
tags:
  - "architecture"
  - "api"
  - "build"
---
```

### Cross-Reference System
- Use relative paths for internal links
- Include line number references for source code
- Implement automatic link validation
- Support anchor links for sections

### Version Control Integration
- Track documentation changes with source code
- Maintain version compatibility matrix
- Implement automated changelog generation
- Support branch-specific documentation

## Quality Assurance

### Automated Checks
- Link validation
- Cross-reference verification
- Source code mapping validation
- YAML frontmatter validation
- Platform compatibility checking

### Manual Review Process
- Technical accuracy verification
- Cross-platform consistency
- AI agent usability testing
- Documentation completeness

## Success Metrics

### Quantitative
- 100% source code coverage
- 0 broken internal links
- Complete cross-platform coverage
- All API methods documented

### Qualitative
- AI agent can navigate without human intervention
- Clear development workflow
- Consistent documentation style
- Effective troubleshooting guides

## Maintenance Strategy

### Regular Updates
- Sync with source code changes
- Update cross-references
- Maintain version compatibility
- Refresh platform-specific information

### Automation
- Automated link checking
- Source code change detection
- Documentation generation from comments
- Version bump automation

This design plan provides a comprehensive framework for creating AI agent-optimized documentation that accurately reflects the source code while supporting the m.inc enhancement goals. The structure prioritizes machine readability, cross-platform compatibility, and maintainability.
