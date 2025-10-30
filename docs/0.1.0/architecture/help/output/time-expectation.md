# Time Expectation

When Blaise says “~5.6 million times,” he’s talking about interactions in his artificial‑life “soup,” not wall‑clock time. In his write‑up he shows that in one early run, a whole‑tape self‑replicator appears “at about 5.6 million interactions”; he also notes that as the system evolves, the number of computations (“ops”) per interaction rises from a few to thousands. ([Nautilus](https://nautil.us/in-the-beginning-there-was-computation-787023/ "In the Beginning, There Was Computation - Nautilus"))

---

## What “5.6 million times” maps to in your telemetry

| Term Blaise uses               | What it means in the bff “soup”                                                                                                                                                                                              | What to look for in your metrics                                                                                                            |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Interaction                | Pick two tapes, concatenate (A‖B), execute for a fixed step budget (or until halt), split back into A′ and B′ and return to the soup.                                                                                        | A counter of pairwise executions. If you don’t expose this directly, infer it as: `interactions ≈ ops_total / avg_ops_per_interaction`. |
| Epoch                      | One sweep of pairings through the population. In spatial runs each program can be used at most once per epoch → ≈ N/2 interactions per epoch (N = number of tapes/programs). Non‑spatial runs are implemented similarly. | You’ll need population size (N) to convert epochs ↔ interactions: `interactions ≈ epochs * (N/2)`.                                      |
| ops                        | Primitive instructions actually executed during those interactions.                                                                                                                                                          | You already log this (`ops`).                                                                                                               |
| MOps/s                     | Throughput (millions of ops per second).                                                                                                                                                                                     | You already log this (`MOps/s`).                                                                                                            |
| Brotli size / “complexity” | A proxy for Kolmogorov complexity used by the team (they approximate complexity via compression, e.g., brotli -q2). Not a timing signal, but a good “phase‑transition” indicator.                                        | Your “Brotli size” field aligns with their complexity proxy.                                                                                |

> In his article Blaise’s exact phrasing is that the sharp transition to whole‑tape replication happens around 5.6M interactions in one run; figures in the paper show many runs transition earlier or later (e.g., ~40% within 16k epochs, depending on settings). ([Nautilus](https://nautil.us/in-the-beginning-there-was-computation-787023/ "In the Beginning, There Was Computation - Nautilus"))

---

> Terminal Output
```
    Elapsed:  16498.174        ops:          28112339053234     MOps/s:     1900.921 Epochs:        287489 ops/prog/epoch:   1883.321
Brotli size:    1560037 Brotli bpb:                  1.4878 bytes/prog:      11.9021     H0:        7.5077 higher entropy:   6.019970 number of repicators:         -1
0  4.55% <  3.92% ,  3.51% [  3.38% }  3.12% ]  1.61% ǿ  1.50% ā  0.85% Ǿ  0.68% Ǽ  0.67% ǻ  0.61% ſ  0.61% Ɖ  0.56% Ʃ  0.55% ǵ  0.55% Ǝ  0.55%
ƨ  0.18% ŋ  0.18% ƞ  0.17% Ɓ  0.17% ŵ  0.16% Ƙ  0.16% Ŀ  0.15% Ǧ  0.15% Ƹ  0.15% Ɗ  0.14% Ğ  0.13% Ƃ  0.11% +  0.03% -  0.02% {  0.00% >  0.00%
```

→ an interaction is one pairwise execution of `A‖B` with the step budget, split back into `A′, B′`, and returned to the soup. That’s exactly the unit he’s talking about.

---

## What to look at in _his_ runner

- If the build prints an interactions / pairs counter, just run until it hits 5,600,000.
- If it only prints epochs (the default graphs in the paper are in epochs), use the runner’s built‑in relationship:

    - In the 2‑D grid (default shown in §2.2: 240×135 ⇒ N = 32,400), each epoch pairs each program at most once ⇒ ≈ N/2 interactions per epoch. So 5.6M interactions ≈ 2·5.6M / N ≈ 346 epochs.
    - In the 0‑D soup used in other figures (the paper describes a soup of 2^17 tapes), the same “pair once per epoch” idea applies; with N = 131,072, 5.6M interactions ≈ 86 epochs.

> The paper explicitly describes the 2‑D epoch procedure (shuffle programs; pick a neighbor; mark both as taken; execute all taken pairs), which is why the N/2 per epoch relationship is guaranteed there.

---

## “How long in time?” (still within Blaise’s system)

Wall‑clock time depends on your measured throughput and the step budget per interaction:

- In BFF, each interaction halts after a fixed instruction budget of 2^13 = 8,192 character reads (i.e., max ~8,192 instructions/ops per interaction). That’s the hard upper bound.
- Your runner already reports ops and MOps/s. So:

$\textbf{seconds to 5.6M} ;=; \frac{;5.6\times10^6 \times \text{(avg ops/interaction)};}{\text{MOps/s}\times10^6}$

Two quick, in‑system bounds using your mock telemetry (`MOps/s = 1,477.055`, `ops = 3.045684\times10^{12}`, `epochs = 34,753`):

- If you’re on the 2^17 (0‑D) configuration:  
    interactions so far $(=) epochs × (N/2) (=) 34,753 × 65,536 = 2,277,572,608$ →  
    avg ops/interaction $(=) (3.045684\times10^{12})/2.277572608×10^9 ≈ 1,337.25$ →  
    time to 5.6M $≈ ((5.6\times10^6×1,337.25)/(1,477.055\times10^6)) ≈ 5.07 s$.

- If you’re on the $240×135$ (2‑D) configuration:  
    interactions so far $(=) 34,753 × 16,200 = 562,998,600$ →  
    avg ops/interaction $≈ (3.045684\times10^{12})/5.629986×10^8 ≈ ≈5,410$ →  
    time to 5.6M $≈ ((5.6\times10^6×5,410)/(1,477.055\times10^6)) ≈ 20.5 s$.

- Absolute worst‑case (every interaction runs to the $2^13$ limit):  
    ops needed $(=) (5.6\times10^6×8{,}192 = 4.58752\times10^{10})$ →  
    time $≈ (4.58752\times10^{10}/1.477055\times10^9) ≈ 31.1 s$

---

### TL;DR for Blaise’s system

- Target: 5.6M interactions (pairwise executions).
- If you only see epochs: multiply epochs by $N/2$ ($2‑D: N=32,400 → ~346 epochs; 0‑D: N=2^17 → ~86 epochs$) to compare with 5.6M.
- Wall‑clock: use $MOps/s$ and your current ops/interaction; bounded above by the $2^13$ per‑interaction budget.
