# Quick Simulation Commands Reference

Quick reference for running CuBFF simulations with various languages and configurations.

## Available Languages

Use with `--lang <name>`:

| Language | Description |
|----------|-------------|
| `bff` | Basic BFF (Brainfuck Forth) - full featured |
| `bff_noheads` | BFF without read/write heads (most commonly used) |
| `bff8` | 8-instruction BFF variant |
| `bff8_noheads` | 8-instruction BFF without heads |
| `bff_noheads_4bit` | 4-bit instruction variant |
| `bff_perm` | BFF with permutation operations |
| `bff_selfmove` | BFF with self-movement capabilities |
| `forth` | Forth stack-based language |
| `forthcopy` | Forth with copy operations |
| `forthtrivial` | Minimal Forth variant |
| `forthtrivial_reset` | Minimal Forth with reset |
| `subleq` | SUBLEQ single-instruction architecture |
| `rsubleq4` | 4-way SUBLEQ variant |

## Essential Command-Line Flags

### Basic Simulation Control
```bash
--lang <name>              # Language to run (required)
--num <n>                  # Number of programs in soup (default: 131072)
--seed <n>                 # Random seed (default: 0)
--max_epochs <n>           # Maximum epochs to run (default: unlimited)
```

### Evolution Parameters
```bash
--mutation_prob <float>    # Mutation probability (default: 0.00024 = 1/(256*16))
--permute_programs         # Shuffle programs between runs (default: true)
--fixed_shuffle            # Use deterministic shuffling pattern (default: false)
--zero_init                # Initialize soup with zeros instead of random (default: false)
```

### Output Control
```bash
--print_interval <n>       # Epochs between output prints (default: 64)
--disable_output           # Disable printing to stdout (default: false)
--log <file>               # Save metrics to log file
```

### Stopping Conditions
```bash
--stopping_bpb <float>              # Stop when compression reaches this bits-per-byte
--stopping_selfrep_count <n>       # Stop when N self-replicators emerge
```

### Checkpointing & State
```bash
--checkpoint_dir <dir>     # Directory for periodic checkpoints
--save_interval <n>        # Epochs between checkpoints (default: 256)
--load <file>              # Resume from checkpoint file
```

### Advanced Options
```bash
--reset_interval <n>       # Reset soup every N epochs
--clear_interval <n>       # Clear interval (default: 2048)
--eval_selfrep             # Evaluate self-replication every epoch (slower)
--interaction_pattern <f>  # File with allowed program interactions (a b pairs)
```

### Visualization
```bash
--draw_to <dir>            # Save 1D visualization frames to directory
--draw_to_2d <dir>         # Save 2D visualization frames (num must be square)
--grid_width_2d <n>        # Width of 2D grid (default: auto)
```

### Single Program Execution
```bash
--run <program>            # Run a single program string
--run_steps <n>            # Max steps for single run (default: 32768)
--debug                    # Print execution step-by-step
```

## Quick Start Examples

### Minimal Test Run
```bash
# Quick test with small soup
./bin/main --lang bff_noheads --num 1024 --max_epochs 10
```

### Standard Simulation
```bash
# Typical evolution run
./bin/main --lang bff_noheads --num 65536 --max_epochs 1000 --seed 42
```

### Fast Replicator Search
```bash
# Small soup, stop when replicators emerge
./bin/main --lang bff_noheads --num 8192 --stopping_selfrep_count 5
```

### Long Run with Logging
```bash
# Long evolution with detailed logging
./bin/main --lang bff_noheads \
  --num 131072 \
  --max_epochs 10000 \
  --seed 12345 \
  --log evolution.log \
  --checkpoint_dir ./checkpoints
```

### Resume from Checkpoint
```bash
# Continue previous run
./bin/main --lang bff_noheads --load checkpoints/checkpoint_epoch_1000.bin
```

### High Mutation Rate
```bash
# Faster evolution with more mutations
./bin/main --lang bff_noheads \
  --num 65536 \
  --mutation_prob 0.001 \
  --max_epochs 5000
```

### Deterministic Run
```bash
# Reproducible results
./bin/main --lang bff_noheads \
  --seed 42 \
  --fixed_shuffle \
  --num 32768 \
  --max_epochs 500
```

## Language-Specific Examples

### BFF No Heads (Most Common)
```bash
# Recommended starting point
./bin/main --lang bff_noheads --num 65536 --max_epochs 1000

# Quick emergence check
./bin/main --lang bff_noheads --num 16384 --stopping_bpb 7.5
```

### Forth Stack Language
```bash
# Forth evolution
./bin/main --lang forth --num 65536 --max_epochs 2000 --seed 100

# Minimal Forth variant
./bin/main --lang forthtrivial --num 32768 --max_epochs 1000
```

### SUBLEQ Single-Instruction
```bash
# SUBLEQ evolution
./bin/main --lang subleq --num 65536 --max_epochs 1500

# 4-way SUBLEQ variant
./bin/main --lang rsubleq4 --num 65536 --max_epochs 1500
```

### BFF Variants
```bash
# 8-instruction variant
./bin/main --lang bff8_noheads --num 65536 --max_epochs 1000

# Self-moving programs
./bin/main --lang bff_selfmove --num 32768 --max_epochs 800

# Permutation operations
./bin/main --lang bff_perm --num 65536 --max_epochs 1000
```

## Common Soup Sizes

Choose based on your computational resources:

| Size | Flag | Use Case |
|------|------|----------|
| 1K | `--num 1024` | Quick testing |
| 8K | `--num 8192` | Fast experiments |
| 32K | `--num 32768` | Medium runs |
| 64K | `--num 65536` | Standard runs |
| 128K | `--num 131072` | Default/long runs |
| 256K | `--num 262144` | Large-scale evolution |

## Output Interpretation

### Metrics Displayed Every `print_interval` Epochs:
- **Elapsed**: Wall-clock time
- **ops**: Total operations executed
- **MOps/s**: Million operations per second
- **Epochs**: Current epoch number
- **ops/prog/epoch**: Average ops per program per epoch
- **Brotli size**: Compressed soup size in bytes
- **Brotli bpb**: Bits per byte (compression ratio)
- **bytes/prog**: Average bytes per program
- **H0**: Shannon entropy
- **higher entropy**: Entropy change from baseline
- **number of replicators**: Count of self-replicating programs (-1 if not evaluated)

### Compression Ratio Guide:
- **8.0 bpb**: Random/unstructured soup
- **7.5-7.8 bpb**: Patterns emerging
- **< 7.0 bpb**: Strong structure (potential replicators)
- **< 6.0 bpb**: Likely self-replicators present

## Single Program Testing

### Run and Debug a Program
```bash
# Execute a specific program with step-by-step output
./bin/main --lang bff_noheads --run "+++++[>++<-]" --debug

# Test program with limited steps
./bin/main --lang bff_noheads --run "+++++[>++<-]" --run_steps 1000
```

### Seed Soup with Initial Program
```bash
# Start with a known program in the soup
./bin/main --lang bff_noheads \
  --initial_program "+++++[>++<-]" \
  --num 32768 \
  --max_epochs 500
```

## Performance Tips

### For Faster Results:
- Use smaller soup sizes (`--num 8192` to `32768`)
- Use `--disable_output` to reduce I/O overhead
- Increase mutation rate (`--mutation_prob 0.001`)
- Use simpler languages (`bff8_noheads`, `forthtrivial`)

### For Better Emergence:
- Use larger soup sizes (`--num 131072` or higher)
- Use default or lower mutation rates
- Run for more epochs (`--max_epochs 10000+`)
- Enable replicator evaluation (`--eval_selfrep`)

### For Reproducibility:
- Always set `--seed` to a specific value
- Use `--fixed_shuffle` for deterministic interactions
- Save checkpoints with `--checkpoint_dir`
- Log metrics with `--log`

## Visualization Workflow

### Generate 1D Frames
```bash
mkdir -p frames_1d
./bin/main --lang bff_noheads \
  --num 65536 \
  --max_epochs 1000 \
  --draw_to frames_1d \
  --print_interval 10
```

### Generate 2D Frames
```bash
mkdir -p frames_2d
# Note: num must be a perfect square (e.g., 65536 = 256²)
./bin/main --lang bff_noheads \
  --num 65536 \
  --max_epochs 1000 \
  --draw_to_2d frames_2d \
  --grid_width_2d 256 \
  --print_interval 10
```

## Batch Experiments

### Multiple Seeds
```bash
# Run same config with different seeds
for seed in 1 2 3 4 5; do
  ./bin/main --lang bff_noheads \
    --num 65536 \
    --max_epochs 1000 \
    --seed $seed \
    --log results_seed_${seed}.log \
    --disable_output
done
```

### Language Comparison
```bash
# Compare emergence across languages
for lang in bff_noheads forth subleq; do
  ./bin/main --lang $lang \
    --num 65536 \
    --max_epochs 1000 \
    --seed 42 \
    --log results_${lang}.log \
    --disable_output
done
```

### Mutation Rate Sweep
```bash
# Test different mutation rates
for mut in 0.0001 0.0005 0.001 0.005; do
  ./bin/main --lang bff_noheads \
    --num 65536 \
    --mutation_prob $mut \
    --max_epochs 1000 \
    --seed 42 \
    --log results_mut_${mut}.log \
    --disable_output
done
```

## Troubleshooting

### Simulation Too Slow
- Reduce `--num` to smaller value
- Increase `--print_interval` to reduce output overhead
- Use `--disable_output`
- Disable `--eval_selfrep` if enabled

### No Replicators Emerging
- Run longer (`--max_epochs` higher)
- Try different seeds (`--seed`)
- Try different languages
- Increase soup size (`--num`)
- Adjust mutation rate (`--mutation_prob`)

### Out of Memory
- Reduce `--num` to smaller value
- Check available RAM (soup size × 64 bytes minimum)

### Want Reproducible Results
- Set `--seed` explicitly
- Use `--fixed_shuffle`
- Record all flags used

## Reference Data Generation

### Create Test Reference
```bash
# Generate reference output for testing
./bin/main --lang bff_noheads \
  --max_epochs 256 \
  --disable_output \
  --log testdata/bff_noheads.txt \
  --seed 10248
```

## Additional Resources

- See `README.md` for project overview
- See `WARP.md` for detailed architecture
- See `CONTRIBUTING.md` for development guidelines
- Explore `testdata/` for example outputs
- Check `docs/` for comprehensive documentation
