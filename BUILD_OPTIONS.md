# CuBFF Build Options on Windows

## Quick Decision Guide

**Which method should I use?**

1. **Use WSL2** if you want the easiest setup (works like Linux)
2. **Use CMake** if you want a native Windows build with modern tools
3. **Use Makefile** if you're comfortable with traditional Unix tools

## Detailed Comparison

### WSL2 Method
- **Pros**: Easiest, no code changes needed, uses original Makefile
- **Cons**: Requires WSL2 installation, runs in Linux environment
- **Best for**: Getting started quickly, Linux-like development
- **Commands**:
  ```bash
  wsl
  sudo apt install build-essential libbrotli-dev
  make CUDA=0
  ```

### CMake Method (Native Windows)
- **Pros**: Cross-platform, modern, integrates with Visual Studio
- **Cons**: Requires CMake and vcpkg setup
- **Best for**: Long-term development, team projects
- **Commands**:
  ```bash
  mkdir build && cd build
  cmake .. -DUSE_CUDA=OFF
  cmake --build . --config Release
  ```

### Makefile Method (Native Windows)
- **Pros**: Simple, similar to original workflow
- **Cons**: Requires pkg-config or manual library paths
- **Best for**: Quick builds if you have MinGW/MSYS2
- **Commands**:
  ```bash
  make -f Makefile.windows CUDA=0
  ```

## Required Dependencies

### All Methods Need:
- C++17 compiler (GCC 8+, Clang 6+, MSVC 2017+)
- Brotli compression library
- OpenMP (for parallel processing)

### CUDA (Optional):
- NVIDIA GPU with CUDA support
- CUDA Toolkit 10.0+
- Use `CUDA=0` to disable if not available

## Installation Guide Links

- WSL2: See `WINDOWS_BUILD.md` → Option 1
- CMake: See `WINDOWS_BUILD.md` → Option 3
- Makefile: See `WINDOWS_BUILD.md` → Option 4

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| "pkg-config not found" | Use WSL2 or install via MSYS2 |
| CUDA errors | Add `CUDA=0` flag |
| Missing brotli | Install via apt/vcpkg/pacman |
| Build errors | Check you have C++17 support |

## Test Your Build

After building, test with:
```bash
./bin/main --lang bff_noheads
```

Or on Windows:
```bash
.\bin\main.exe --lang bff_noheads
```

You should see simulation output with metrics and program visualization.

