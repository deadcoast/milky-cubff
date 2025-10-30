# METRICS OUTPUT HELP

- ops: `29,421,409,669,002`  
    Total primitive instructions executed so far. This is the big “work done” odometer.

- MOps/s: `1834.230`  
    Current throughput (millions of ops per second) at the moment of the print. It fluctuates with load/OS scheduling.

- Epochs: `298,305`  
    Count of completed sweeps of the population according to the runner’s pairing policy. Useful as a progress axis.

- ops/prog/epoch: `1827.815`  
    Average instructions executed per program per epoch. This is a great “activity” indicator: it rises when interactions run longer (e.g., as more executable structure emerges) and dips when lots of pairs halt quickly.

- Brotli size: `1,563,000` (bytes)  
    Compressed size of the _entire_ soup/program pool. It’s your coarse complexity proxy: bigger = less compressible (more irregular information); smaller = more compressible (more repetition/regularity).

- Brotli bpb: `1.4906`  
    “Bits per byte” under Brotli for the whole soup. 8.0 would be pure randomness for byte data; lower numbers mean the data is more compressible/regular. Tracking bpb alongside size lets you compare runs with different pool sizes.

- bytes/prog: `11.9247`  
    Average program length (bytes) across the pool. If this trends up, your genomes are, on average, getting longer; if it stabilizes with lower bpb, you’re seeing repeated motifs/templates.

- H0: `7.5136`  
    Zero-order (unigram) Shannon entropy of the byte distribution over the soup (max 8 for bytes). Near-max values mean symbol frequencies are closer to uniform; dips can indicate biased alphabets (e.g., heavy use of a bracket set or opcodes).

- higher entropy: `6.023001`  
    A higher-order entropy estimate (conditioned on context). Typically lower than H0 when there’s structure/predictability in sequences. If H0 is high but higher-order drops, you’ve got locally patterned structure despite overall “random-looking” marginals.

- number of replicators: `-1`  
    Detector is disabled, uncomputed, or the pass that fills it didn’t run. It’s not “negative one replicators.” If you want it populated, enable the detector pass or run the analysis script that writes this field.

- Histogram line:
    ```
    0  4.73% <  3.97% ,  3.57% [  3.41% }  3.12% ]  1.62% ǿ  0.67% Ǝ  ...
    ```

    This is a unigram symbol-frequency snapshot for the soup’s alphabet. Seeing brackets (`< [ } ]`) and punctuation near the top tells you that those tokens are heavily represented in the current genomes (often scaffolding/stack-control symbols, depending on the substrate). Watching this line over time helps spot alphabet shifts (e.g., when a subset of opcodes/markers becomes dominant).

- The giant block of glyphs/noise:  
    That’s a raw byte→glyph dump of sampled programs (or a stream of soup content) printed with a direct byte→Unicode mapping. It’s not meant for semantic reading; it’s for spotting motifs—repeated symbol clusters, bracket rhythms, numeric runs (`0`, `K`, etc.). You’ll often see:

    - periodic bracket/marker patterns (possible replication scaffolds),
    - runs of digits/letters (tape constants or copied regions),
    - recurring short “stamps” spreading through the dump (phenotypic signatures).

## State-of-soup reading

- Activity level: `ops/prog/epoch ≈ 1.83k` is active. If this number trends upward sharply (e.g., into several thousands) without a matching rise in H0, that often coincides with more elaborate executions per interaction (e.g., copying strides, longer-lived programs).

- Complexity / compressibility:

    - Brotli size up (vs your prior ~1.50 MB) and bpb = 1.49 ⇒ the pool is less compressible than before—more irregularity or more diverse genomes.
    - H0 = 7.51 (very high) but higher-order = 6.02 (well below H0) ⇒ despite near-uniform single-symbol frequencies, there’s contextual structure the compressor/entropy model can exploit. That’s the pattern you expect when building blocks/copying templates start to appear.

- Alphabet bias: Brackets and punctuation near the top of the histogram implies structural tokens remain central. If (over future prints) you see one or two tokens shoot up while others drop, that can indicate a successful template dominating.
- Average length: `bytes/prog ≈ 11.9` keeps you in the short-program regime. If you later see average length rise while bpb drops (more compressible), that’s a sign of templated length growth (repeating macros). If length rises and bpb rises, that’s more random bloat.
- Replicator counter: `-1` means the detector didn’t run or is off; don’t read it as “none.” If you care about that readout, enable the detector or run the analysis stage that populates it.

## How to use this in practice

1. Track curves, not single points:

    - `ops/prog/epoch` (expect step-ups at transitions),
    - `Brotli bpb` (drops = more regular structure; spikes = noise/novelty),
    - `bytes/prog` (growth pattern: bloat vs templated replication),
    - `H0` vs higher entropy (divergence widens when structure strengthens).

2. Watch the histogram drift: stable peaks imply a “vocabulary” is winning; chaotic churn means no dominant template yet.
3. Turn on the replicator pass (or post-hoc detector) if you want that field meaningful.
4. Spot a phase change when you see a coincident shift:  
    histogram stabilizes + `ops/prog/epoch` jumps + bpb bends (down or sharply up then down) + higher-order entropy dips further than H0.
