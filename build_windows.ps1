# PowerShell build script for Windows
# This script helps build CuBFF on Windows with proper error handling

Write-Host "CuBFF Windows Build Script" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "Makefile")) {
    Write-Host "Error: Makefile not found. Are you in the CuBFF directory?" -ForegroundColor Red
    exit 1
}

# Function to check if a command exists
function Test-Command {
    param($cmd)
    try {
        Get-Command $cmd -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Check for WSL
if (Test-Command "wsl") {
    Write-Host "`nWSL detected. Recommended approach:" -ForegroundColor Yellow
    Write-Host "Run this in WSL2 instead for the easiest build experience." -ForegroundColor Yellow
    Write-Host "Use: wsl" then follow the instructions in WINDOWS_BUILD.md`n" -ForegroundColor Yellow
}

# Check for available compilers
$compiler = $null
$useCuda = $false

if (Test-Command "g++") {
    $compiler = "g++"
    Write-Host "Found GCC compiler" -ForegroundColor Green
} elseif (Test-Command "cl") {
    $compiler = "cl"
    Write-Host "Found MSVC compiler" -ForegroundColor Green
} else {
    Write-Host "Error: No suitable C++ compiler found!" -ForegroundColor Red
    Write-Host "Please install:" -ForegroundColor Yellow
    Write-Host "  - MinGW/MSYS2 with g++" -ForegroundColor Yellow
    Write-Host "  - Visual Studio with cl" -ForegroundColor Yellow
    Write-Host "  - Or use WSL2 (recommended)" -ForegroundColor Yellow
    exit 1
}

# Check for CUDA
if (Test-Command "nvcc") {
    Write-Host "CUDA compiler found" -ForegroundColor Green
    $response = Read-Host "Build with CUDA support? (y/n)"
    if ($response -eq "y") {
        $useCuda = $true
    }
} else {
    Write-Host "CUDA not found, building CPU-only version" -ForegroundColor Yellow
}

# Create build directories
New-Item -ItemType Directory -Force -Path "build" | Out-Null
New-Item -ItemType Directory -Force -Path "bin" | Out-Null

# Build
Write-Host "`nBuilding CuBFF..." -ForegroundColor Cyan
if ($compiler -eq "cl") {
    # Visual Studio build
    if ($useCuda) {
        Write-Host "Note: CUDA builds with MSVC are complex. Consider using WSL2." -ForegroundColor Yellow
    }
    # Use the Windows-specific Makefile if it exists
    if (Test-Path "Makefile.windows") {
        make -f Makefile.windows CUDA=0
    } else {
        Write-Host "Error: Makefile.windows not found" -ForegroundColor Red
        exit 1
    }
} else {
    # GCC/MinGW build
    if ($useCuda) {
        make CUDA=1
    } else {
        make CUDA=0
    }
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild successful!" -ForegroundColor Green
    Write-Host "Run with: .\bin\main.exe --lang bff_noheads" -ForegroundColor Cyan
} else {
    Write-Host "`nBuild failed. Check errors above." -ForegroundColor Red
    exit 1
}
