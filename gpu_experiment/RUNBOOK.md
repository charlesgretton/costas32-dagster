# Costas transpose-symmetric GPU calibration experiment

A **calibration and validation** experiment, not the order-32 production run. It
answers two questions that need hardware, and nothing else.

1. How much of the predicted 26.5% → 98.4% lane-efficiency range appears in wall
   time once latency hiding is accounted for?
2. Does explicit shared-memory placement of the rollback log beat
   compiler-managed local memory, once schedule is controlled?

Everything else was settled on CPU. Do not re-open it on GPU time.

## Run order

```sh
scripts/00_capture_environment.sh   # FIRST. Unrecoverable afterwards.
scripts/01_build.sh                 # ARCH=sm_89 default; captures ptxas -v
scripts/02_verify_cpu.sh            # MANDATORY. Blocks everything if it fails.
scripts/03_gate_correctness.sh      # MANDATORY. Blocks all timing if it fails.
scripts/04_matrix.sh                # six cells, REPS=5 + discarded warm-up
scripts/05_profile.sh               # ncu on both backends, exact schedule
scripts/06_blocksize.sh             # 32/64/128 local, 32/64 shared
```

02 and 03 are gates, not formalities. `03` re-verifies every per-unit counter and
both fingerprints against the CPU oracle; `04` re-checks on **every repetition**
and aborts the cell on any mismatch.

## Source

One file, `src/costas_gpu_phase4.cu`, two build modes — `g++ -x c++` for CPU,
`nvcc` for CUDA. The earlier `costas_cpu_phase4.cpp` was a byte-identical copy
and has been removed; keeping two hashes of one file invites divergence.

## The six cells

| cell | schedule | log | predicted lane eff |
|---|---|---|---|
| original_local | depth-4 catalogue order | local | 26.5% |
| exact_local | exact size desc | local | 98.4% |
| refined_local | top-400 b2 refined, p↑ b2↓ | local | 63.4% |
| original_shared | depth-4 catalogue order | shared | 26.5% |
| exact_shared | exact size desc | shared | 98.4% |
| refined_shared | top-400 b2 refined, p↑ b2↓ | shared | 63.4% |

Lane efficiencies are **covariates, not predicted speed-ups**. The exact schedule
for the unrefined frontier is derived by `04_matrix.sh`; the other two catalogues
are shipped.

Aggregate entered nodes for throughput: **4,706,251** unrefined, **4,705,851**
refined. Prefixes/second is not comparable across cells — the frontiers differ in
unit count (37,573 vs 41,479).

## Decision rules, fixed in advance

**Scheduling.** $S = T_{\text{original}}/T_{\text{exact}}$, against a lockstep
upper bound of $98.4/26.5 = 3.71$.
- near 1× — latency hiding absorbs imbalance; the 63.4% proxy is sufficient and
  the scheduler is finished.
- 1.5–2.5× — scheduling matters, less than the static model says.
- near 3.71× — warp packing dominates; a body-ranking estimator is worth real
  effort, and a coarser frontier with affordable size estimation should be
  revisited.

Then $T_{\text{refined}}/T_{\text{exact}}$: if small despite 63.4% vs 98.4%
predicted, stop. If large, the missing third is the target.

**Storage.** $T_{\text{local}}/T_{\text{shared}}$ under the *same* schedule and
block size. Select shared only if verified entered nodes/second improves. Lower
spill counts alone are not sufficient if occupancy falls enough to offset them.

## What to record and why

From `ptxas -v`, per kernel: registers/thread, stack-frame bytes, spill stores,
spill loads. The explicit per-thread state is **1,734 B** — change log 992,
masks 256, add 256, stack 198, board 32 — against a 255-register budget of
1,020 B, so spilling is arithmetic, not tuning. The change log is 57% of it and
is the piece with no need to be in registers.

Shared backend at 64 threads requests 63,488 B and needs the
`cudaFuncSetAttribute` opt-in; at 128 it would request 126,976 B and the launcher
refuses unless `sharedMemPerBlockOptin` allows it. 32 threads (31,744 B) runs
inside the 48 KB default.

## Fail-closed

A run is admissible only when every prefix ID appears exactly once, every unit
reports `exhausted=1`, `error=0`, `invariant_failures=0`, and the canonical GPU
result file is byte-identical to its CPU oracle.

**A crash, timeout, launch failure, missing unit, duplicate ID, invariant failure
or mismatch is INCOMPLETE/UNKNOWN — never a zero-solution result.**

## Established CPU baselines

| | |
|---|---|
| order 16 empty root | 160,797 nodes, 40 solutions, `0x964a2027eb628c96` |
| order 20 empty root | 4,710,666 nodes, 8 solutions, `0x113d3b0a071c068e` |
| order 24 empty root | 142,822,399 nodes, **0 solutions** |
| N=20 depth-4 decomposition | 4,706,251 + 4,415 above cut = 4,710,666 |
| refined frontier | 4,705,851 = 4,706,251 − 400 refined parents |

Independently cross-checked against a separate implementation at orders 16–20
and 24, on entered nodes as well as solution counts.

## Known negative results — do not re-litigate on GPU time

- Restart-based node probing is economically dominated: at depth 4 the cheapest
  schedule clearing 90% lane efficiency costs 148% of the production search.
- Deeper uniform cuts make probing worse, not better: R(512) → 100% by depth 5.
- Static board features cap at 50.9% lane efficiency; $b_1$ is worse than free.
- Selective refinement raises the *ceiling* (98.4 → 99.6%) but not the achieved
  proxy efficiency (63.1 → 63.4%). Tail control and body ordering are
  independent problems.
