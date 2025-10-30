# PYTHON USAGE

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BFF (Brainfuck-Variant) Self-Modifying Soup
-------------------------------------------
- Program size: 64 bytes
- Interaction tape: 128 bytes (A + B concatenated)
- Pointers: PC (instruction pointer), head0, head1
- Ops: > < move head0; } { move head1; + - mutate at head0; . , copy between heads; [ ] loops on value at head0
- Semantics: single unified tape (code==data); out-of-bounds on PC/head0/head1 => halt; step limit => halt
- Pairing: random disjoint pairs per epoch; combine, execute, split; overwrite population with offspring
- Mutation: optional per-byte probability after split
- Analytics: top program counts, zlib compress ratio, Shannon byte entropy

Usage:
  python bff_soup.py --pop 1024 --epochs 10000 --report-every 100 --mutate 0.00005 --seed 123
"""

import argparse
import math
import random
import sys
import time
import zlib
from collections import Counter
from typing import Iterable, List, Tuple

PROGRAM_SIZE = 64
TAPE_SIZE = 128
DEFAULT_STEP_LIMIT = 8192

OP_RSHIFT = ord('>')
OP_LSHIFT = ord('<')
OP_RSHIFT_H1 = ord('}')
OP_LSHIFT_H1 = ord('{')
OP_INC = ord('+')
OP_DEC = ord('-')
OP_COPY_0_TO_1 = ord('.')
OP_COPY_1_TO_0 = ord(',')
OP_LBRACKET = ord('[')
OP_RBRACKET = ord(']')

VALID_OPS = {
    OP_RSHIFT, OP_LSHIFT,
    OP_RSHIFT_H1, OP_LSHIFT_H1,
    OP_INC, OP_DEC,
    OP_COPY_0_TO_1, OP_COPY_1_TO_0,
    OP_LBRACKET, OP_RBRACKET
}


class BFFVM:
    """
    Self-modifying Brainfuck-variant virtual machine operating on a single 128-byte tape.
    - PC starts at 0
    - head0 starts at 0
    - head1 starts at 64
    - Unrecognized bytes are NO-OPs
    - Bracket matching is resolved dynamically at runtime (scanned on each [ or ])
    """
    __slots__ = ("tape", "pc", "head0", "head1", "steps", "step_limit")

    def __init__(self, tape: bytearray, step_limit: int = DEFAULT_STEP_LIMIT):
        if len(tape) != TAPE_SIZE:
            raise ValueError(f"tape must be {TAPE_SIZE} bytes")
        self.tape = tape
        self.pc = 0
        self.head0 = 0
        self.head1 = PROGRAM_SIZE  # 64
        self.steps = 0
        self.step_limit = step_limit

    def _find_matching_forward(self, start_pc: int) -> int:
        """Find matching ] for [ at start_pc, scanning current tape; return index or -1 if none."""
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
        """Find matching [ for ] at start_pc, scanning current tape backward; return index or -1 if none."""
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

    def _in_bounds(self) -> bool:
        return (0 <= self.pc < TAPE_SIZE) and (0 <= self.head0 < TAPE_SIZE) and (0 <= self.head1 < TAPE_SIZE)

    def run(self) -> bytearray:
        """Execute up to step_limit or until OOB/unmatched bracket; returns the (mutated) tape."""
        while self.steps < self.step_limit:
            if not (0 <= self.pc < TAPE_SIZE):
                break
            op = self.tape[self.pc]

            if op == OP_RSHIFT:
                self.head0 += 1
            elif op == OP_LSHIFT:
                self.head0 -= 1
            elif op == OP_RSHIFT_H1:
                self.head1 += 1
            elif op == OP_LSHIFT_H1:
                self.head1 -= 1
            elif op == OP_INC:
                self.tape[self.head0] = (self.tape[self.head0] + 1) & 0xFF
            elif op == OP_DEC:
                self.tape[self.head0] = (self.tape[self.head0] - 1) & 0xFF
            elif op == OP_COPY_0_TO_1:
                self.tape[self.head1] = self.tape[self.head0]
            elif op == OP_COPY_1_TO_0:
                self.tape[self.head0] = self.tape[self.head1]
            elif op == OP_LBRACKET:
                if self.tape[self.head0] == 0:
                    match = self._find_matching_forward(self.pc)
                    if match < 0:
                        break  # unmatched; terminate
                    self.pc = match
            elif op == OP_RBRACKET:
                if self.tape[self.head0] != 0:
                    match = self._find_matching_backward(self.pc)
                    if match < 0:
                        break  # unmatched; terminate
                    self.pc = match
            # else: NO-OP for any other byte

            # bounds & step handling
            if not self._in_bounds():
                break
            self.pc += 1
            self.steps += 1

        return self.tape  # mutated in place


class Soup:
    """
    Soup of 64-byte programs. Each epoch:
      - Shuffle pool
      - Pair (A, B)
      - Create 128-byte tape = A+B
      - Execute BFFVM(tape)
      - Split back to A', B' and overwrite
      - Optional mutation on offspring bytes
    """

    def __init__(self, size: int, seed: int | None = None):
        if seed is not None:
            random.seed(seed)
        if size < 2 or size % 2 != 0:
            raise ValueError("population size must be an even integer >= 2")
        self.pool: List[bytearray] = [bytearray(random.getrandbits(8) for _ in range(PROGRAM_SIZE)) for _ in range(size)]

    def _mutate_in_place(self, prog: bytearray, p: float) -> None:
        if p <= 0.0:
            return
        for i in range(PROGRAM_SIZE):
            if random.random() < p:
                prog[i] = random.getrandbits(8)

    def epoch(self, step_limit: int = DEFAULT_STEP_LIMIT, mutation_p: float = 0.0) -> None:
        random.shuffle(self.pool)
        next_gen: List[bytearray] = []
        # disjoint pairs
        for i in range(0, len(self.pool), 2):
            A = self.pool[i]
            B = self.pool[i + 1]

            # randomize order AB or BA
            if random.random() < 0.5:
                tape = bytearray(A + B)
                order = 0  # AB
            else:
                tape = bytearray(B + A)
                order = 1  # BA

            vm = BFFVM(tape, step_limit=step_limit)
            out = vm.run()

            # split to offspring
            first = bytearray(out[:PROGRAM_SIZE])
            second = bytearray(out[PROGRAM_SIZE:])

            # put back in original pair identities
            if order == 0:  # AB -> A', B'
                A_prime, B_prime = first, second
            else:           # BA -> A' = second-of-tape, B' = first-of-tape
                A_prime, B_prime = second, first

            # mutate offspring
            self._mutate_in_place(A_prime, mutation_p)
            self._mutate_in_place(B_prime, mutation_p)

            next_gen.append(A_prime)
            next_gen.append(B_prime)

        self.pool = next_gen

    # ---------- analytics ----------

    def top_k(self, k: int = 5) -> List[Tuple[bytes, int]]:
        counts = Counter(bytes(p) for p in self.pool)
        return counts.most_common(k)

    def shannon_entropy_bits(self) -> float:
        """Shannon entropy (bits) of the byte distribution across the entire population."""
        # concatenate pool
        data = b"".join(self.pool)
        if not data:
            return 0.0
        counts = Counter(data)
        total = len(data)
        h = 0.0
        for c in counts.values():
            p = c / total
            h -= p * math.log2(p)
        return h  # bits per symbol distribution (max 8.0 for uniform)

    def compress_ratio(self) -> float:
        """zlib compressibility ratio: compressed_size / raw_size (lower => more structure)."""
        data = b"".join(self.pool)
        if not data:
            return 1.0
        comp = zlib.compress(data, level=9)
        return len(comp) / len(data)


def run_cli():
    ap = argparse.ArgumentParser(description="BFF self-modifying soup")
    ap.add_argument("--pop", type=int, default=1024, help="population size (even)")
    ap.add_argument("--epochs", type=int, default=10000, help="number of epochs")
    ap.add_argument("--step-limit", type=int, default=DEFAULT_STEP_LIMIT, help="instruction step cap per interaction")
    ap.add_argument("--mutate", type=float, default=0.0, help="per-byte mutation probability after split (e.g. 5e-5)")
    ap.add_argument("--seed", type=int, default=None, help="random seed")
    ap.add_argument("--report-every", type=int, default=100, help="report interval in epochs")
    ap.add_argument("--no-report-top", action="store_true", help="skip printing top program bytes")
    args = ap.parse_args()

    soup = Soup(size=args.pop, seed=args.seed)

    t0 = time.time()
    for e in range(1, args.epochs + 1):
        soup.epoch(step_limit=args.step_limit, mutation_p=args.mutate)
        if (e % args.report_every) == 0:
            top = soup.top_k(1)
            cr = soup.compress_ratio()
            h = soup.shannon_entropy_bits()
            if top:
                top_prog, cnt = top[0]
                sys.stdout.write(
                    f"epoch {e:>7} | top_count {cnt:>5}/{args.pop} | "
                    f"compress_ratio {cr:.3f} | shannon_bits {h:.3f}\n"
                )
                if not args.no_report_top:
                    # print first 32 bytes of the dominant program (hex) for tracking
                    head = top_prog[:32]
                    sys.stdout.write("top_prog_head(hex): " + head.hex() + "\n")
            else:
                sys.stdout.write(f"epoch {e:>7} | (no data)\n")
            sys.stdout.flush()
    t1 = time.time()
    sys.stdout.write(f"done in {t1 - t0:.2f}s\n")


if __name__ == "__main__":
    run_cli()
```