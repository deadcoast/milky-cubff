# Source Code Assets

## Meta-Implementations (GoL running GoL)

[Life in Life in Life](https://github.com/mrphlip/life3) - mrphlip/life3

- <https://github.com/mrphlip/life3>
- Generates nested GoL using OTCA Metapixels, creates videos of Life simulating Life
- Lua scripts for Golly + C++ rendering code

[Lisp in Life](https://github.com/woodrush/lisp-in-life) - woodrush/lisp-in-life

- <https://github.com/woodrush/lisp-in-life>
- Full Lisp interpreter running in GoL via the QFT computer
- Includes compiler from C → QFTASM → VarLife → GoL

[QFT Development Kit](https://github.com/woodrush/QFT-devkit) - woodrush/QFT-devkit

- <https://github.com/woodrush/QFT-devkit>
- Tools for working with Quest for Tetris computer architecture
- Python scripts for ROM/RAM preparation, metafier for VarLife → GoL conversion

## Quest for Tetris (The Big One)

[Main Repository](https://github.com/QuestForTetris/QFT) - QuestForTetris/QFT

- <https://github.com/QuestForTetris/QFT>
- Original Tetris-in-GoL project with all construction tools

[Tetris Writeup](https://github.com/QuestForTetris/tetris-writeup) - QuestForTetris/tetris-writeup

- <https://github.com/QuestForTetris/tetris-writeup>
- Complete documentation of the architecture, including VarLife explanation

[COGOL](https://github.com/QuestForTetris/Cogol) - QuestForTetris/Cogol

- <https://github.com/QuestForTetris/Cogol>
- Higher-level language ("C of Game of Life") that compiles to QFTASM

[GCC Backend](https://github.com/QuestForTetris/qftasm-gcc) - QuestForTetris/qftasm-gcc

- <https://github.com/QuestForTetris/qftasm-gcc>
- Modified GCC that targets the QFTASM architecture

Online Interpreter:

- QFTASM: <http://play.starmaninnovations.com/qftasm/>
- VarLife: <http://play.starmaninnovations.com/varlife/>

## HashLife Implementations

[Python](https://github.com/johnhw/hashlife) - johnhw/hashlife
- Clean Python implementation with detailed explanation
- Companion article: [Hashlife Repository Index](https://johnhw.github.io/hashlife/index.md.html)

[JavaScript](https://github.com/raganwald/hashlife) - raganwald/hashlife

[C](https://github.com/farhiongit/hashlife) - farhiongit/hashlife
- Handles universes up to 10^77 × 10^77, includes Gosper paper references

[Rust](https://github.com/slightknack/hashlife) - slightknack/hashlife
- Optimized Rust implementation (no UI, core algorithm only)

## Golly (The Standard Simulator)

Official Source - AlephAlpha/golly or jimblandy/golly

- <https://github.com/AlephAlpha/golly>
- C++ with wxWidgets GUI
- Includes HashLife, QuickLife algorithms, scriptable via Python/Lua
- Sourceforge: <http://golly.sourceforge.net/>

GollyGang Organization - <https://github.com/GollyGang>

- Rule table repository and supplemental patterns

## SmoothLife (Continuous GoL)

C (tsoding) - tsoding/SmoothLife

- <https://github.com/tsoding/SmoothLife>
- OpenGL/GLSL shaders, FFT-based convolution

Original (engibeer) - engibeer/smooth-life

- <https://github.com/engibeer/smooth-life>
- Mirror of sourceforge project with 2D/3D graphics

Python+NumPy (duckythescientist) - duckythescientist/SmoothLife

- <https://github.com/duckythescientist/SmoothLife>
- Math-light explanation with visualization

Swift/Metal (tscheepers) - tscheepers/SmoothLife-Swift

- <https://github.com/tscheepers/SmoothLife-Swift>
- GPU implementation with Metal shaders + vDSP version

## Wireworld

JavaScript (Xalava) - Xalava/WireWorld

- <https://github.com/Xalava/WireWorld>
- Browser-based circuit designer

Python (yackx) - yackx/wireworld

- <https://github.com/yackx/wireworld>
- Simple implementation with GUI, includes circuit samples (XOR gates, etc.)

C++/SFML (RainingComputers/Wireboi) - RainingComputers/Wireboi

- <https://github.com/RainingComputers/Wireboi>
- Load circuits from PNG files, includes prime number computer

Mathematica (daneelsan) - daneelsan/Wireworld

- <https://github.com/daneelsan/Wireworld>
- Paclet with Zig-compiled LibraryLink backend

## Key Technical Details from Repos

VarLife (8-state CA) is the intermediate layer for QFT:

- Each cell becomes a 2048×2048 OTCA Metapixel when converted to GoL
- 1 VarLife generation = 35,328 GoL generations
- Rule file: `Varlife.rule` in QFT repos

QFTASM has these critical features:

- Asynchronous architecture (data carries its own clock signal)
- RISC-based with multiple opcodes: MLZ, MNZ, ADD, SUB, AND, OR, XOR, ANT, SL, SRL, SRA
- Tetris uses <300 instructions in the final assembly

The metafier scripts (particularly MetafierV3.py) convert VarLife → GoL using template files to avoid recomputing metapixel structures.

Which implementation interests you most? The QFT architecture is especially deep if you want to understand computer design in cellular automata.
