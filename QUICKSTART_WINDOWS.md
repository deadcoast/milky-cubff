# Quick Start Guide for Windows

## Easiest Method: Use WSL2

1. **Install WSL2** (if not already installed):
   - Open PowerShell as Administrator
   - Run: `wsl --install`
   - Restart your computer

2. **Open WSL2** and navigate to the project:
   ```bash
   wsl
   cd /mnt/c/Users/ryanf/github/assets/cubff
   ```

3. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install build-essential libbrotli-dev pkg-config python3 python3-pip python3-venv
   ```

4. **Create and activate virtual environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install Python dependencies** (if using Python features):
   ```bash
   pip install --upgrade pip
   ```

6. **Build**:
   ```bash
   make CUDA=0
   ```

7. **Run**:
   ```bash
   ./bin/main --lang bff_noheads
   ```

**To deactivate the virtual environment when done**:
   ```bash
   deactivate
   ```

## Alternative: Native Windows Build with MSYS2

1. **Download and install MSYS2** from https://www.msys2.org/

2. **Open MSYS2 MinGW 64-bit terminal** and run:
   ```bash
   pacman -Syu
   pacman -S base-devel mingw-w64-x86_64-gcc mingw-w64-x86_64-brotli mingw-w64-x86_64-pkg-config make
   ```

3. **Add to PATH**: Add `C:\msys64\mingw64\bin` to your Windows PATH

4. **Build** (from Command Prompt or PowerShell):
   ```bash
   make CUDA=0
   ```

5. **Run**:
   ```bash
   .\bin\main.exe --lang bff_noheads
   ```

## Using the PowerShell Build Script

If you have a C++ compiler installed, you can use the helper script:

```powershell
.\build_windows.ps1
```

This script will detect your compiler and guide you through the build process.

## What to Expect

After building, you should see the simulation running with output showing:
- Elapsed time
- Operations per second
- Epochs
- Brotli compression metrics
- Program visualization

Press Ctrl+C to stop the simulation.

## Output Statistics Cheat Sheet

Here's what the simulation output metrics mean:

| Statistic | Example Value | Description |
|-----------|--------------|-------------|
| **Elapsed** | 2000.661 | Total time the simulation has been running (in seconds) |
| **ops** | 3,045,684,413,663 | Total number of operations executed across all programs |
| **MOps/s** | 1477.055 | Millions of operations per second (performance metric) |
| **Epochs** | 34,753 | Number of evolution cycles completed |
| **ops/prog/epoch** | 1384.035 | Average operations per program per epoch |
| **Brotli size** | 1,544,287 | Compressed size of the entire program soup (bytes) |
| **Brotli bpb** | 1.4727 | Bits per byte (compression ratio - lower = more organized) |
| **bytes/prog** | 11.7820 | Average bytes per program (original soup size) |
| **H0** | 7.4826 | Shannon entropy (randomness measure - max ~7.5 for 64-byte programs) |
| **higher entropy** | 6.009810 | Additional entropy beyond expected random distribution |
| **number of replicators** | -1 | Count of detected self-replicators (-1 if not tracking) |

### Byte Frequency Section

The lines showing byte frequencies indicate how often specific program bytes appear:

- **Top row**: Most frequent bytes (show emerging patterns)
- **Bottom row**: Uncommon bytes (show disappearing patterns)
- Numbers show percentage occurrence in the soup

Example: `0  5.20%` means the byte value 0 appears in 5.20% of all program positions.

### What to Look For

- **Low Brotli bpb (< 2.0)**: Programs are becoming organized/self-similar
- **Increasing ops/prog/epoch**: More complex interactions are happening
- **Replicators > 0**: Self-replicating programs have emerged!
- **Stable byte frequencies**: Evolution has converged to certain patterns

## Troubleshooting

**Build fails with "pkg-config not found"**:
- Use WSL2 (recommended) or install pkg-config through MSYS2

**CUDA-related errors**:
- Use `CUDA=0` flag to build without CUDA support

**Permission errors**:
- Make sure you have write permissions in the project directory
- Try running PowerShell/Command Prompt as Administrator

**Virtual environment issues**:
- If `source venv/bin/activate` fails, make sure you're in the WSL2 terminal (not PowerShell)
- The `(venv)` prefix in your terminal prompt indicates the virtual environment is active
- Always activate venv before building or running (except for first-time builds before venv is created)

## Complete Workflow Summary (Quick Reference)

Here's the complete end-to-end workflow in one block for easy copy-paste:

```bash
# 1. Enter WSL2
wsl

# 2. Navigate to project
cd /mnt/c/Users/ryanf/github/assets/cubff

# 3. Install system dependencies (first time only)
sudo apt update
sudo apt install build-essential libbrotli-dev pkg-config python3 python3-pip python3-venv

# 4. Create virtual environment (first time only)
python3 -m venv venv

# 5. Activate virtual environment
source venv/bin/activate

# 6. Build the project
make CUDA=0

# 7. Run the simulation
./bin/main --lang bff_noheads --num 128 --max_epochs 10

# 8. When done, deactivate venv
deactivate
```

**Subsequent runs** (after initial setup):
```bash
wsl
cd /mnt/c/Users/ryanf/github/assets/cubff
source venv/bin/activate
./bin/main --lang bff_noheads
```

## Need Help?

See `WINDOWS_BUILD.md` for more detailed information and alternative build methods.
