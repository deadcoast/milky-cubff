# GLYPH BLOCK OUTPUT HELP

Short version: that giant glyph block is not “Brainfuck code”. It’s a raw byte dump of soup contents, rendered with a byte→Unicode mapping so you can _see_ patterns. In Blaise’s system the soup is a bag of arbitrary bytes (0–255). Only a small subset of bytes are interpreted as opcodes (e.g., Brainfuck’s `+ - < > . , [ ]`); the rest are non-ops/data/filler depending on the substrate. When you print raw bytes straight to the terminal, you get lots of extended glyphs like `ǿ Ō Ĩ …`—that’s expected.

What that means:

- The histogram line is a quick unigram frequency readout of symbols across the soup. You can see some BF tokens high up (e.g., `< 3.97%`, `[ 3.57%`, `] 3.12%`) alongside non-BF tokens (`}` isn’t BF). Near the end you see `+ 0.02%` and `- 0.02%`: in _this_ instant, increment/decrement bytes are rare in the pool. That doesn’t contradict BF being the substrate; it just tells you the current byte distribution in your soup has very few `+`/`-` bytes and is heavier on movement/structure markers (`< [ ] …`) and lots of non-op bytes.
- The huge glyph block below the histogram is just sampled program bytes printed directly. It’s there to let you spot motifs (repeated bracket rhythms, recurring “stamps”, digit runs) spreading through the pool. It is not a pretty-printed, BF-only listing.

If you want to _see_ “only the Brainfuck syntax”:

- Filter to BF ops when printing:
    - Regex idea: keep only `[+\-<>.,\[\]]`
   	- Example (Linux/macOS/WSL) if you can pipe soup bytes/text out:
        ```bash
        your_dump_cmd | tr -cd '+\-<>.,[]' | fold -w80
        ```

- Or write a tiny post-processor to show BF-only tokens and count them
    ```python
    import sys, re, collections
    ops = set('+-<>.,[]')
    buf = sys.stdin.read()
    bf = ''.join(ch for ch in buf if ch in ops)
    print(bf[:2000])  # preview
    print(collections.Counter(bf))
    ```

- If your build supports it, switch the dump to an opcode-aware view (some runners have a “pretty” or “BF-only” mode or a flag to elide non-ops).

Why you’re seeing lots of non-BF glyphs at all:

- The alphabet of the soup is bytes, not “ASCII BF tokens only.” The interpreter maps some bytes to semantics (the BF op set) and the rest typically act as no-ops/data. Evolution happens over all bytes; selection favors byte patterns that, when concatenated/executed, do useful things (copy, loop, etc.). So raw dumps will always look “noisy.”

How to read your specific lines quickly:

- `Brotli bpb 1.4906`, `H0 7.5136`, `higher entropy 6.023` → high unigram entropy but predictable structure in context (higher-order entropy significantly lower). Good sign of emergent motifs.
- `bytes/prog 11.9247` → still short genomes on average; if this grows while bpb drops, you’re seeing templated repetition; if both grow, that’s more random bloat.
- `ops/prog/epoch 1827.815` → interactions are doing non-trivial work on average (this tends to climb around interesting transitions).
- `number of replicators: -1` → detector not run/disabled; enable the replicator analysis pass if you want a meaningful count.
