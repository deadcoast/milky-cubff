# Build Fix Summary

## Issue Fixed

The original `Makefile` had a malformed definition on line 14-15 where linker flags were accidentally placed in the compile flags section. This caused the build to fail with errors like "linker input file unused because linking not done".

## Changes Made

### Makefile (Fixed)
**Line 14-16**: Fixed the broken `COMMON_FLAGS` definition by:
- Removing the misplaced linker flags from the compile flags
- Properly including linker flags in the `LINK_FLAGS` variable

```makefile
# Before (broken):
COMMON_FLAGS := -g -std=c++17 -O3 \
                $(shell pkg-config --cflags libbrotlienc libbrotlicommon) \
                ${EXTRA_LDFLAGS}
 -lbrotlienc -lbrotlidec

LINK_FLAGS := $(shell pkg-config --libs libbrotlienc libbrotlicommon)

# After (fixed):
COMMON_FLAGS := -g -std=c++17 -O3 \
                $(shell pkg-config --cflags libbrotlienc libbrotlicommon) \
                ${EXTRA_LDFLAGS}

LINK_FLAGS := -lbrotlienc -lbrotlidec $(shell pkg-config --libs libbrotlienc libbrotlicommon)
```

### Documentation Updates

Updated all documentation files to include `pkg-config` in the dependency installation:

1. **QUICKSTART_WINDOWS.md**: Added `pkg-config` to apt install command
2. **WINDOWS_BUILD.md**: Added `pkg-config` to dependency list
3. **README.md**: Added `pkg-config` to Windows installation instructions

## Verification

The build now completes successfully on WSL2:
- All `.cu` files compile correctly as C++ when `CUDA=0`
- Main executable (`bin/main`) is created
- Program runs successfully with simulation output

## Build Command

```bash
# In WSL2
sudo apt install build-essential libbrotli-dev pkg-config
make CUDA=0
./bin/main --lang bff_noheads
```

## Notes

- The source code itself required no changes
- Only configuration files (Makefile) and documentation were modified
- The build now works on Windows via WSL2 without any source code modifications
