# Building CuBFF on Windows

This guide explains how to build and run CuBFF on Windows.

## Prerequisites

### Option 1: WSL2 (Recommended - Easiest)
The easiest way to run this project on Windows is using WSL2 (Windows Subsystem for Linux):

1. Install WSL2 with Ubuntu:
   - Open PowerShell as Administrator
   - Run: `wsl --install`
   - Reboot your computer when prompted

2. Once in Ubuntu terminal, install dependencies:
   ```bash
   sudo apt update
   sudo apt install build-essential libbrotli-dev pkg-config
   ```

3. If you have NVIDIA GPU and want CUDA support:
   - Install CUDA Toolkit in WSL2 following NVIDIA's guide
   - Or simply use `make CUDA=0` for CPU-only mode

4. Build and run:
   ```bash
   cd /mnt/c/Users/ryanf/github/assets/cubff
   make CUDA=0
   ./bin/main --lang bff_noheads
   ```

### Option 2: Native Windows Build with MinGW/MSYS2

Requires MSYS2 environment:

1. Download and install [MSYS2](https://www.msys2.org/)

2. Open MSYS2 MinGW 64-bit terminal and install dependencies:
   ```bash
   pacman -Syu
   pacman -S base-devel mingw-w64-x86_64-gcc mingw-w64-x86_64-brotli mingw-w64-x86_64-pkg-config git make
   ```

3. Add MSYS2 to your PATH:
   - Add `C:\msys64\mingw64\bin` to your Windows PATH environment variable

4. Build from Command Prompt or PowerShell:
   ```bash
   cd C:\Users\ryanf\github\assets\cubff
   mingw32-make CUDA=0
   ```

5. Run:
   ```bash
   ./bin/main.exe --lang bff_noheads
   ```

### Option 3: Native Windows Build with CMake (Recommended for Native Windows)

This is the most reliable method for native Windows builds:

1. Install dependencies:
   - **Visual Studio 2022** with "Desktop development with C++" workload
   - **CMake 3.15 or newer** (usually comes with Visual Studio)
   - **Brotli library** via vcpkg:
     ```bash
     git clone https://github.com/microsoft/vcpkg.git
     cd vcpkg
     .\bootstrap-vcpkg.bat
     .\vcpkg install brotli:x64-windows
     ```

2. Build with CMake:
   ```bash
   mkdir build
   cd build
   cmake .. -DCMAKE_TOOLCHAIN_FILE=C:\path\to\vcpkg\scripts\buildsystems\vcpkg.cmake -DUSE_CUDA=OFF
   cmake --build . --config Release
   ```

3. Run:
   ```bash
   .\bin\main.exe --lang bff_noheads
   ```

### Option 4: Native Windows Build with Makefile

Alternative method using the provided `Makefile.windows`:

1. Install dependencies (same as Option 3)
2. Build using the Windows Makefile:
   ```bash
   make -f Makefile.windows CUDA=0
   ```
3. Run:
   ```bash
   .\bin\main.exe --lang bff_noheads
   ```

## Important Notes

- The project uses C++17 features
- CUDA is optional - use `CUDA=0` for CPU-only builds
- The build creates `bin/main.exe` (or `bin/main` on WSL)
- Input files are in the `testdata/` directory

## Troubleshooting

### If `pkg-config` is not found:
The Makefile uses `pkg-config` which isn't standard on Windows. Use the WSL2 option or compile manually with the flags.

### If CUDA path cannot be found:
Use `CUDA=0` to build without CUDA support.

### If OpenMP errors occur:
Some Windows builds may need to disable OpenMP or link to specific OpenMP libraries depending on your compiler.

## Quick Start (WSL2 recommended)

```bash
# In WSL2/Ubuntu terminal
sudo apt install build-essential libbrotli-dev
make CUDA=0
./bin/main --lang bff_noheads
```
