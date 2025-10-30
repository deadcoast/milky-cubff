# Module Additions

* Unified 128‑byte tape from two 64‑byte programs
* PC + head0 + head1, all indexing the same tape
* 10 opcodes only: `><+-{}.,[]`
* Runtime termination on step limit, out‑of‑bounds pointers, or unmatched loop brackets
* Random disjoint pairing → concatenate → execute → split
* Optional mutation after split
* Deterministic / reproducible with seeding
* Instrumentation (entropy, compressibility, opcode histograms)
* Snapshot/restore, replicator assay, exact replication event detection, schedulers

> How to use: Create a folder `bffx/` and save each file below to it (filenames shown). Then run `python -m bffx.cli --help`.

---

## `bffx/vm.py`

```python
# bffx/vm.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

PROGRAM_SIZE = 64
TAPE_SIZE = 128
DEFAULT_STEP_LIMIT = 8192

# Opcodes (single-byte)
OP_RSHIFT        = ord('>')  # head0++
OP_LSHIFT        = ord('<')  # head0--
OP_RSHIFT_H1     = ord('}')  # head1++
OP_LSHIFT_H1     = ord('{')  # head1--
OP_INC           = ord('+')  # tape[head0]++
OP_DEC           = ord('-')  # tape[head0]--
OP_COPY_0_TO_1   = ord('.')  # tape[head1] = tape[head0]
OP_COPY_1_TO_0   = ord(',')  # tape[head0] = tape[head1]
OP_LBRACKET      = ord('[')  # if tape[head0]==0 jump forward to matching ]
OP_RBRACKET      = ord(']')  # if tape[head0]!=0 jump back to matching [
VALID_OPS = {
    OP_RSHIFT, OP_LSHIFT,
    OP_RSHIFT_H1, OP_LSHIFT_H1,
    OP_INC, OP_DEC,
    OP_COPY_0_TO_1, OP_COPY_1_TO_0,
    OP_LBRACKET, OP_RBRACKET,
}

class HaltReason(Enum):
    STEP_LIMIT = auto()
    OOB_POINTER = auto()
    UNMATCHED_BRACKET = auto()
    PC_OOB = auto()
    NORMAL = auto()   # no explicit halt instruction in BFF; treat same as STEP_LIMIT reached

@dataclass
class RunResult:
    tape: bytearray
    steps: int
    reason: HaltReason
    oob_pointer: Optional[str] = None   # 'pc' | 'head0' | 'head1' if applicable
    unmatched_at: Optional[int] = None  # pc index where unmatched bracket discovered

class BFFVM:
    """
    Brainfuck-variant VM with a unified 128-byte tape (code==data).
    - PC starts at 0
    - head0 starts at 0
    - head1 starts at 64 (start of second 64-byte region)
    - Unrecognized bytes are NO-OPs
    - Bracket matching is resolved dynamically at runtime (scanned each time)
    Execution halts on: step limit, pointer out-of-bounds, PC out-of-bounds, unmatched brackets.
    """
    __slots__ = ("tape", "pc", "head0", "head1", "steps", "step_limit")

    def __init__(self, tape: bytearray, step_limit: int = DEFAULT_STEP_LIMIT,
                 init_head0: int = 0, init_head1: int = PROGRAM_SIZE):
        if len(tape) != TAPE_SIZE:
            raise ValueError(f"tape must be {TAPE_SIZE} bytes")
        self.tape = tape
        self.pc = 0
        self.head0 = init_head0
        self.head1 = init_head1
        self.steps = 0
        self.step_limit = step_limit

    def _heads_in_bounds(self) -> bool:
        return 0 <= self.head0 < TAPE_SIZE and 0 <= self.head1 < TAPE_SIZE

    def _pc_in_bounds(self) -> bool:
        return 0 <= self.pc < TAPE_SIZE

    def _find_matching_forward(self, start_pc: int) -> int:
        depth = 1
        i = start_pc + 1
        while i < TAPE_SIZE:
            b = self.tape[i]
            if b == OP_LBRACKET:
                depth += 1
            elif b == OP_RBRACKET:
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    def _find_matching_backward(self, start_pc: int) -> int:
        depth = 1
        i = start_pc - 1
        while i >= 0:
            b = self.tape[i]
            if b == OP_RBRACKET:
                depth += 1
            elif b == OP_LBRACKET:
                depth -= 1
                if depth == 0:
                    return i
            i -= 1
        return -1

    def run(self) -> RunResult:
        while self.steps < self.step_limit:
            if not self._pc_in_bounds():
                return RunResult(self.tape, self.steps, HaltReason.PC_OOB, oob_pointer="pc")

            op = self.tape[self.pc]

            # NO-OP fast path
            if op not in VALID_OPS:
                self.pc += 1
                self.steps += 1
                continue

            # pointer moves
            if op == OP_RSHIFT:
                self.head0 += 1
                if not self._heads_in_bounds():
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer="head0")
            elif op == OP_LSHIFT:
                self.head0 -= 1
                if not self._heads_in_bounds():
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer="head0")
            elif op == OP_RSHIFT_H1:
                self.head1 += 1
                if not self._heads_in_bounds():
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer="head1")
            elif op == OP_LSHIFT_H1:
                self.head1 -= 1
                if not self._heads_in_bounds():
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer="head1")

            # mutations / copies (require in-bounds heads)
            elif op == OP_INC:
                if not self._heads_in_bounds():
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer="head0")
                self.tape[self.head0] = (self.tape[self.head0] + 1) & 0xFF
            elif op == OP_DEC:
                if not self._heads_in_bounds():
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer="head0")
                self.tape[self.head0] = (self.tape[self.head0] - 1) & 0xFF
            elif op == OP_COPY_0_TO_1:
                if not self._heads_in_bounds():
                    # either head out-of-bounds is OOB
                    which = "head0" if not (0 <= self.head0 < TAPE_SIZE) else "head1"
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer=which)
                self.tape[self.head1] = self.tape[self.head0]
            elif op == OP_COPY_1_TO_0:
                if not self._heads_in_bounds():
                    which = "head0" if not (0 <= self.head0 < TAPE_SIZE) else "head1"
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer=which)
                self.tape[self.head0] = self.tape[self.head1]

            # loops (dynamic bracket scan)
            elif op == OP_LBRACKET:
                if not (0 <= self.head0 < TAPE_SIZE):
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer="head0")
                if self.tape[self.head0] == 0:
                    match = self._find_matching_forward(self.pc)
                    if match < 0:
                        return RunResult(self.tape, self.steps, HaltReason.UNMATCHED_BRACKET, unmatched_at=self.pc)
                    self.pc = match
            elif op == OP_RBRACKET:
                if not (0 <= self.head0 < TAPE_SIZE):
                    return RunResult(self.tape, self.steps, HaltReason.OOB_POINTER, oob_pointer="head0")
                if self.tape[self.head0] != 0:
                    match = self._find_matching_backward(self.pc)
                    if match < 0:
                        return RunResult(self.tape, self.steps, HaltReason.UNMATCHED_BRACKET, unmatched_at=self.pc)
                    self.pc = match

            # advance
            self.pc += 1
            self.steps += 1

        return RunResult(self.tape, self.steps, HaltReason.STEP_LIMIT)
```

---

## `bffx/scheduler.py`

```python
# bffx/scheduler.py
from __future__ import annotations
import random
from typing import List, Tuple

def random_disjoint_pairs(n: int, rng: random.Random) -> List[Tuple[int, int]]:
    """
    Return a list of disjoint index pairs covering n elements (n must be even).
    """
    if n % 2 != 0:
        raise ValueError("n must be even")
    idx = list(range(n))
    rng.shuffle(idx)
    return [(idx[i], idx[i+1]) for i in range(0, n, 2)]
```

---

## `bffx/analytics.py`

```python
# bffx/analytics.py
from __future__ import annotations
import math
import zlib
from collections import Counter
from typing import List, Tuple

PROGRAM_SIZE = 64

def shannon_entropy_bits(population: List[bytearray]) -> float:
    data = b"".join(population)
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    h = 0.0
    for c in counts.values():
        p = c / total
        h -= p * math.log2(p)
    return h

def compress_ratio(population: List[bytearray]) -> float:
    data = b"".join(population)
    if not data:
        return 1.0
    comp = zlib.compress(data, 9)
    return len(comp) / len(data)

def opcode_histogram(population: List[bytearray]) -> Counter:
    return Counter(b for p in population for b in p)

def top_programs(population: List[bytearray], k: int = 5) -> List[Tuple[bytes, int]]:
    counts = Counter(bytes(p) for p in population)
    return counts.most_common(k)

def hamming(a: bytes, b: bytes) -> int:
    if len(a) != len(b):
        raise ValueError("length mismatch")
    return sum(x != y for x, y in zip(a, b))
```

---

## `bffx/detectors.py`

```python
# bffx/detectors.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

PROGRAM_SIZE = 64

@dataclass
class ReplicationEvent:
    kind: Literal["A_exact_replicator", "B_exact_replicator", "none"]
    # A_before + B_before -> A_after + B_after
    A_before: bytes
    B_before: bytes
    A_after: bytes
    B_after: bytes

def detect_exact_replication(A_before: bytes, B_before: bytes,
                             A_after: bytes, B_after: bytes) -> ReplicationEvent:
    """
    Exact-event detector with no thresholds or heuristics:
    - If A_after == A_before and B_after == A_before  -> A_exact_replicator
    - If A_after == B_before and B_after == B_before  -> B_exact_replicator
    - Else -> none
    """
    if len(A_before) != PROGRAM_SIZE or len(B_before) != PROGRAM_SIZE:
        raise ValueError("program length must be 64")
    if len(A_after) != PROGRAM_SIZE or len(B_after) != PROGRAM_SIZE:
        raise ValueError("program length must be 64")

    if A_after == A_before and B_after == A_before:
        return ReplicationEvent("A_exact_replicator", A_before, B_before, A_after, B_after)
    if A_after == B_before and B_after == B_before:
        return ReplicationEvent("B_exact_replicator", A_before, B_before, A_after, B_after)
    return ReplicationEvent("none", A_before, B_before, A_after, B_after)
```

---

## `bffx/snapshot.py`

```python
# bffx/snapshot.py
from __future__ import annotations
import gzip
import json
from typing import Any, Dict, List

PROGRAM_SIZE = 64

def save_population_json_gz(path: str, population: List[bytearray], meta: Dict[str, Any] | None = None) -> None:
    payload = {
        "meta": meta or {},
        "programs_hex": [p.hex() for p in population],
    }
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))

def load_population_json_gz(path: str) -> tuple[list[bytearray], dict]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        payload = json.load(f)
    progs = [bytearray.fromhex(h) for h in payload["programs_hex"]]
    if not all(len(p) == PROGRAM_SIZE for p in progs):
        raise ValueError("loaded program with unexpected size")
    return progs, payload.get("meta", {})
```

---

## `bffx/soup.py`

```python
# bffx/soup.py
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Tuple

from .vm import BFFVM, RunResult, HaltReason, PROGRAM_SIZE, TAPE_SIZE, DEFAULT_STEP_LIMIT
from .detectors import ReplicationEvent, detect_exact_replication

PairScheduler = Callable[[int, random.Random], List[Tuple[int, int]]]

@dataclass
class PairOutcome:
    i: int
    j: int
    order: str  # "AB" or "BA"
    result: RunResult
    replication_event: ReplicationEvent

class Soup:
    """
    Population of 64-byte programs. Each epoch:
      - Disjoint pairing via scheduler
      - Concatenate pair -> 128-byte tape (randomize AB vs BA)
      - Run VM
      - Split back -> overwrite both
      - Optional post-split mutation
    """

    def __init__(self, size: int, rng: Optional[random.Random] = None):
        if size < 2 or size % 2 != 0:
            raise ValueError("size must be an even integer >= 2")
        self.rng = rng or random.Random()
        self.pool: List[bytearray] = [bytearray(self.rng.getrandbits(8) for _ in range(PROGRAM_SIZE))
                                      for _ in range(size)]
        self.epoch_index: int = 0

    def inject_mutation(self, per_byte_p: float) -> None:
        if per_byte_p <= 0.0:
            return
        for prog in self.pool:
            for k in range(PROGRAM_SIZE):
                if self.rng.random() < per_byte_p:
                    prog[k] = self.rng.getrandbits(8)

    def epoch(self,
              scheduler: PairScheduler,
              step_limit: int = DEFAULT_STEP_LIMIT,
              mutation_p: float = 0.0,
              record_outcomes: bool = False) -> List[PairOutcome]:
        pairs = scheduler(len(self.pool), self.rng)
        outcomes: List[PairOutcome] = []
        next_gen: List[bytearray] = [bytearray(PROGRAM_SIZE) for _ in range(len(self.pool))]

        for (i, j) in pairs:
            A_before = bytes(self.pool[i])
            B_before = bytes(self.pool[j])

            if self.rng.random() < 0.5:
                order = "AB"
                tape = bytearray(A_before + B_before)
            else:
                order = "BA"
                tape = bytearray(B_before + A_before)

            vm = BFFVM(tape, step_limit=step_limit)
            rr: RunResult = vm.run()

            first = bytearray(rr.tape[:PROGRAM_SIZE])
            second = bytearray(rr.tape[PROGRAM_SIZE:])

            if order == "AB":
                A_after, B_after = first, second
            else:
                A_after, B_after = second, first

            # replacement + optional mutation
            if mutation_p > 0.0:
                # mutate in place
                for idx in range(PROGRAM_SIZE):
                    if self.rng.random() < mutation_p:
                        A_after[idx] = self.rng.getrandbits(8)
                    if self.rng.random() < mutation_p:
                        B_after[idx] = self.rng.getrandbits(8)

            next_gen[i] = A_after
            next_gen[j] = B_after

            if record_outcomes:
                revent = detect_exact_replication(A_before, B_before, bytes(A_after), bytes(B_after))
                outcomes.append(PairOutcome(i=i, j=j, order=order, result=rr, replication_event=revent))

        self.pool = next_gen
        self.epoch_index += 1
        return outcomes
```

---

## `bffx/assay.py`

```python
# bffx/assay.py
from __future__ import annotations
import random
from typing import List, Tuple

from .vm import BFFVM, DEFAULT_STEP_LIMIT, PROGRAM_SIZE
from .detectors import detect_exact_replication

def assay_candidate(candidate: bytes,
                    foods: List[bytes],
                    trials: int = 100,
                    step_limit: int = DEFAULT_STEP_LIMIT,
                    rng: random.Random | None = None) -> Tuple[int, int]:
    """
    Deterministic replicator assay (no thresholds, no guesses):
    For each trial, pick a random food program F, run exec(S+F) and exec(F+S),
    and count a 'success' if BOTH outputs equal S (exact duplication).
    Returns: (successes, total_trials)
    """
    if len(candidate) != PROGRAM_SIZE:
        raise ValueError("candidate must be 64 bytes")
    if not foods:
        raise ValueError("foods list is empty")
    rng = rng or random.Random()

    successes = 0
    for _ in range(trials):
        F = rng.choice(foods)
        # AB
        tape_ab = bytearray(candidate + F)
        rr_ab = BFFVM(tape_ab, step_limit=step_limit).run()
        A1 = bytes(rr_ab.tape[:PROGRAM_SIZE])
        B1 = bytes(rr_ab.tape[PROGRAM_SIZE:])
        # BA
        tape_ba = bytearray(F + candidate)
        rr_ba = BFFVM(tape_ba, step_limit=step_limit).run()
        A2 = bytes(rr_ba.tape[:PROGRAM_SIZE])
        B2 = bytes(rr_ba.tape[PROGRAM_SIZE:])

        e1 = detect_exact_replication(candidate, F, A1, B1).kind == "A_exact_replicator"
        e2 = detect_exact_replication(F, candidate, A2, B2).kind == "B_exact_replicator"
        if e1 and e2:
            successes += 1
    return successes, trials
```

---

## `bffx/cli.py`

```python
# bffx/cli.py
from __future__ import annotations
import argparse
import random
import sys
from typing import Optional

from .soup import Soup
from .scheduler import random_disjoint_pairs
from .analytics import shannon_entropy_bits, compress_ratio, top_programs, opcode_histogram

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="BFF self-modifying soup runner")
    ap.add_argument("--pop", type=int, default=1024, help="population size (even)")
    ap.add_argument("--epochs", type=int, default=10000, help="number of epochs")
    ap.add_argument("--step-limit", type=int, default=8192, help="instruction step cap per interaction")
    ap.add_argument("--mutate", type=float, default=0.0, help="per-byte mutation probability after split")
    ap.add_argument("--seed", type=int, default=None, help="random seed")
    ap.add_argument("--report-every", type=int, default=100, help="report interval in epochs")
    ap.add_argument("--log-events", action="store_true", help="track exact replication events per epoch")
    args = ap.parse_args(argv)

    rng = random.Random(args.seed)
    soup = Soup(size=args.pop, rng=rng)

    for e in range(1, args.epochs + 1):
        outcomes = soup.epoch(
            scheduler=random_disjoint_pairs,
            step_limit=args.step_limit,
            mutation_p=args.mutate,
            record_outcomes=args.log_events
        )

        if (e % args.report_every) == 0:
            H = shannon_entropy_bits(soup.pool)
            CR = compress_ratio(soup.pool)
            top = top_programs(soup.pool, 1)
            top_str = f"{top[0][1]:>5}/{args.pop}" if top else "0"
            sys.stdout.write(
                f"epoch {e:>7} | top_count {top_str} | "
                f"compress_ratio {CR:.3f} | shannon_bits {H:.3f}\n"
            )
            sys.stdout.flush()

            # Optional opcode mix snapshot (useful when a population begins to structure)
            hist = opcode_histogram(soup.pool)
            summary = {k: hist.get(ord(k), 0) for k in "><+-{}.,[]"}
            sys.stdout.write("opcode_counts: " + " ".join(f"{k}:{v}" for k, v in summary.items()) + "\n")
            sys.stdout.flush()

            if args.log_events:
                exact_reps = sum(1 for o in outcomes if o.replication_event.kind != "none")
                sys.stdout.write(f"exact_replication_events_this_epoch: {exact_reps}\n")
                sys.stdout.flush()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

---

## Why these modules

* `vm.py`: exact BFF mechanics (no extras), dynamic bracket resolution (self-mod-safe), explicit halt reasons.
* `soup.py`: canonical AB/BA concatenation → execute → split workflow with mutation and optional replication event logging.
* `scheduler.py`: deterministic disjoint random pairing.
* `analytics.py`: measurable, deterministic metrics (entropy, compressibility, opcode histogram, top programs).
* `detectors.py`: exact, threshold‑free replication event classification (no guessing).
* `snapshot.py`: portable snapshots (`.json.gz`) with hex for raw bytes.
* `assay.py`: a strict replicator assay that tests a candidate against random foods in both AB and BA orientations.
* `cli.py`: minimal driver to run experiments and report metrics.

## Quick start

```bash
# from the parent folder that contains bffx/
python -m bffx.cli --pop 1024 --epochs 2000 --report-every 100 --seed 123 --mutate 0.00005
```

## Extend later (safe hooks provided)

* Plug your own scheduler (e.g., spatial neighborhoods) by passing a function with signature `(n, rng) -> list[(i,j)]`.
* Alter step limit / heads init (pass in via `BFFVM` if you integrate custom runners).
* Add snapshotting around epochs with `snapshot.save_population_json_gz(...)`.

If you want additional modules (e.g., CSV telemetry writer, periodic snapshotter, or a replicator hunting harness that isolates top candidates and assays them automatically), say the word and I’ll add them fully implemented.
