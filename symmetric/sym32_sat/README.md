# Transpose-symmetric order-32 Costas: SAT campaign

Target: **does a transpose-symmetric Costas array of order 32 exist?** Open
question; the reachable half of the open order-32/33 problem.

    python3 regions.py regions.csv                  # the 44,947 regions
    python3 gen_sym32_v2.py 0,1,3,7 out/            # one region -> CNF + mono DAG
    python3 split_certified.py out/ split/          # certified case split
    KISSAT=... python3 check_split.py split/        # discharge the gates
    cd validation && KISSAT=... python3 test_*.py   # regression suite
    python3 project.py ledger.csv kissat            # censored cost analysis

## ESTABLISHED

* **44,947 regions.** Every transpose-symmetric permutation has exactly one
  fixed-point set F; F must be a Golomb ruler with |F| in {0,2,4,6} (f=8 needs
  span 34 > 31; f odd impossible for even n). Reflection-canonical:
  f=0:1, f=2:256, f=4:13,587, f=6:31,103. Disjoint and exhaustive — the
  partition is forced by the mathematics, not chosen by a partitioner.
* **v2 encoding, exhaustively validated both directions.**
  n=8: 39 regions, 18 direct solutions = 18 models, 0 rejected, 0 invalid.
  n=10: 106 regions, 28 = 28, 0, 0.
* **158-array regression.** All 158 historical involutive Costas arrays,
  orders 12–22, accepted by direct clause evaluation.
* **Certified split for F={0,1,3,7}.** 27 full-CNF children, coverage UNSAT,
  351/351 disjointness UNSAT, bound to parent CNF digest d5e79b689d7cded4.
* **Reproducible archive.** No /tmp dependencies; generator, catalogue and
  harnesses archived and digested.
* **Fail-closed solver interpretation.** Kissat exit 10 = SAT, 20 = UNSAT,
  anything else UNKNOWN. An empty model or proof file is never read
  semantically.

## IMPLEMENTED, NOT PERFORMANCE-VALIDATED

* direct Kissat arm; Dagster mono arm; certified Dagster split arm
* RMST and restricted-work reporting in `project.py`

## PLANNED

* real-core stratified pilot; adaptive splitting of survivors;
  wall/core/allocated-time comparison; proof-producing final campaign

## NOT ESTABLISHED

* existence or non-existence at order 32
* full-campaign cost, and any unrestricted mean runtime
* whether Dagster accelerates this computation
* whether the current split rule balances children
* any theorem-level UNSAT result

## RETIRED — do not use, and do not cite its numbers

`gen_sym32.py` (v1) encoded only pairwise transposition conflicts. A repeated
displacement is a relation among up to four cycles, so v1 was a **relaxation**:
a model was found with 112 repeated displacements. **All v1 results are void**,
including its DAG timings, its "SAT" verdicts, and its 22-child split for
F={0,1,3,7}. v2 gives 27 children for the same region — v1's seed filter had
removed five edges — so the old certificate described a *different partition*,
not merely an unpinned one.

Also retired: any reading of `nan` as the only output for an all-censored
stratum, and any "lower bound" quoted without its horizon and estimand.

Also retired: `sample_campaign.py`. It still drove the v1 generator and the
non-partition `dag_splitK`, so the automated pilot contradicted RUN_PROTOCOL.md.
It now exits with status 3. It is replaced by `pilot_driver.py`, the v2-correct three-arm driver, tested
end to end on known-SAT and known-UNSAT regions. Cluster job scripts are in `hpc/`.

## Two cost quantities, never conflated

    sample observed-work lower bound   sum over ACTUAL runs of t_i or c_i.
                                       Deterministic; work already demanded.
    population restricted-work proj.   sum_f N_f * RMST_f(cap).  An
                                       EXTRAPOLATION counting work only THROUGH
                                       the horizon. It does NOT estimate the
                                       cost of finishing; beyond-cap work is
                                       unidentified.

A stratum with zero completions has an undefined median but a defined RMST, and
contributes to the projection rather than vanishing.
