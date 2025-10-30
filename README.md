# CuBFF

This project provides a (optionally) CUDA-based implementation of a
self-modifying soup of programs which show emergence of self-replicators. Most
experiments in the "Computational Life: How Well-formed, Self-replicating Programs 
Emerge from Simple Interaction" paper (arxiv link (https://arxiv.org/abs/2406.19108) were done using this code.

## Dependencies

### Linux
On debian-based systems, install `build-essential` and `libbrotli-dev` (and optionally CUDA):

  `sudo apt install build-essential libbrotli-dev`

On Arch Linux, install the `brotli` and `base-devel` packages.

The project also provides a `flake.nix` file, so you may also make the
dependencies available with Nix using `nix develop`.

### Windows
**For Windows users, please see the Windows-specific build instructions:**

- Quick Start: See `QUICKSTART_WINDOWS.md`
- Detailed Guide: See `WINDOWS_BUILD.md`
- Build Options: See `BUILD_OPTIONS.md`

The easiest method is using **WSL2** - see the quick start guide for details.

## Build Instructions

### Linux/Mac
Compile the code by running `make` (for the CUDA-enabled version) or `make CUDA=0`.

### Windows
See `WINDOWS_BUILD.md` for detailed instructions. Quick start with WSL2:
```bash
wsl
sudo apt install build-essential libbrotli-dev pkg-config
make CUDA=0
```

### CMake (Cross-platform)
Alternatively, build using CMake:
```bash
mkdir build && cd build
cmake .. -DUSE_CUDA=OFF
cmake --build . --config Release
```

## Run Instructions

You can run a simulation, for example with:
  `bin/main --lang bff_noheads`

Or on Windows:
  `.\bin\main.exe --lang bff_noheads`

The file `cubff_example.py` provides an example of how to use the Python bindings.
