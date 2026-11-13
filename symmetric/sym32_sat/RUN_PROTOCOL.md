# Three-arm pilot: run protocol

Purpose: decide the campaign mechanism for the order-32 transpose-symmetric
search. It answers three separable questions and nothing else.

    Q1  Is direct Kissat on a v2 region already sufficient?
    Q2  What does the Dagster/MPI execution path cost?          (A vs B)
    Q3  Does certified splitting improve the TAIL enough to pay? (B vs C)

This is a gate, not a miniature campaign. Do not extend it into one.

---

## 0. Before anything runs

### 0.1 Record provenance. Refuse to start without it.

    realpath $KISSAT; sha256sum $KISSAT; $KISSAT --version
    sha256sum $(which dagster); mpirun --version
    uname -a; lscpu | sed -n '1,15p'; free -g
    python3 -V; git rev-parse HEAD 2>/dev/null

Write to `pilot/provenance.json`. Two nominally identical runs using different
Kissat builds is a defect this catches and nothing else will.

### 0.2 Reproduce the frozen regression suite ON THE PILOT MACHINE

    cd validation
    KISSAT=$KISSAT python3 test_completeness.py     # expect PASS n=8, n=10
    KISSAT=$KISSAT python3 test_soundness.py        # expect PASS n=8, n=10
    KISSAT=$KISSAT python3 test_historical158.py    # expect 158/158

**STOP if any differs from VALIDATION.json.** A generator or solver difference
invalidates everything downstream, and it is cheaper to find it here.

### 0.3 Negative control

Deliberately break one coverage check and confirm `check_split.py` FAILS. A gate
that has never failed has not been shown to work.

---

## 1. Sample

    python3 regions.py regions.csv

Strata: f in {0,2,4,6}; within f>0, fixed-point diameter quartiles.
**f=0 is a deterministic singleton** — one region, diameter undefined. Include
it whole; do not pass it through quartile construction.

Target 100-300 regions. Suggested: all of f=0 (1), 24 from f=2, 100 from f=4,
100 from f=6. Record the RNG seed in the manifest.

Also record cheap pre-solve covariates per region, so hardness can later be
regressed on something better than diameter: edge-variable count, clause count,
binary-clause count, post-propagation domain sizes, conflict-graph degree
summary.

---

## 2. Generate, per sampled region

    python3 gen_sym32_v2.py <F> pilot/<rid>/
    python3 split_certified.py pilot/<rid>/ pilot/<rid>/split/
    KISSAT=$KISSAT python3 check_split.py pilot/<rid>/split/

**Every region gets its OWN v2-bound certificate.** Never reuse one because two
regions have the same child count — the v1 episode produced 22 children where
v2 produces 27, from the same F.

Gate: coverage UNSAT and all pairwise disjointness UNSAT. A region failing this
is excluded from timing and reported as a generator defect, not as a datum.

---

## 3. The three arms

Byte-identical parent CNF across all three. Record its digest in every row.

    A  direct kissat   $KISSAT --time=$CAP <rid>/model.cnf
    B  dagster mono    mpirun -n $R dagster -m 0 -g 1 <rid>/dag_mono.dag <rid>/model.cnf -o B.sols
    C  certified split one job per child CNF, same $CAP each

**Randomise arm order within each region.** Machines drift; a fixed A,B,C order
confounds arm with time.

Use identical hardware allocation for the B vs C comparison — same node type,
same rank count, no co-tenancy. B vs C is the only comparison where that matters
and the only one it is easy to get wrong.

Cap: 600 s for the first sweep. If the completion fraction exceeds ~0.9, the cap
is uninformative about the tail — re-run the survivors at 1800 s rather than
raising the cap for everything.

---

## 4. Status handling — fail closed

    kissat exit 10 -> SAT      and "s SATISFIABLE" present
    kissat exit 20 -> UNSAT    and "s UNSATISFIABLE" present
    anything else  -> UNKNOWN / SOLVER_ERROR / TIMEOUT

Dagster uses its own convention; translate in the adapter, never reuse Kissat's.

**An empty model file is not UNSAT.** An exit 134 is a crash. Both have produced
misleading zeros in this project already.

Every SAT model is decoded and independently checked: permutation, involution,
fixed points exactly F, and zero repeated displacements. A model that fails any
of these is a defect report, not a discovery.

---

## 5. Ledger — one row per logical subproblem

    region_id  fixed_points  f  diameter
    arm  split_rule  split_index  split_count  split_literal
    parent_cnf_sha256  child_cnf_sha256  generator_sha256  split_cert_sha256
    solver  solver_sha256  seed  mpi_ranks
    status  exit_code  solution_count  model_validated
    wall_s  cpu_s  core_s  allocated_s  cap_s  max_rss_mb
    conflicts  decisions  propagations

For a split region emit child rows AND an aggregate parent row with

    T_wall(C)  = max_r T_r        (only if children genuinely ran concurrently)
    T_core(C)  = sum_r T_cpu,r
    T_alloc(C) = ranks * T_wall   (label clearly; it is not measured CPU)

---

## 6. Analysis

    python3 project.py pilot/ledger.csv kissat
    python3 project.py pilot/ledger.csv dagster_mono
    python3 project.py pilot/ledger.csv dagster_split

Report per stratum: completion fraction, completed-time quantiles, RMST to the
named cap, sample observed-work lower bound, population restricted-work
projection, number at risk at cap, unresolved tail.

No unrestricted mean. With the largest observations censored the tail is
unidentified.

---

## 7. Decision rules, fixed in advance

**Q1** If Arm A completes >90% of sampled regions within 600 s, the campaign is
a Slurm array of direct Kissat. Dagster is not needed for the bulk.

**Q2** If B is materially slower than A at equal rank count after subtracting
the MPI floor, do not use Dagster for easy regions. Measure the floor on this
machine: a trivial 2-clause UNSAT instance at each rank count.

**Q3** Adopt C only if it reduces the TAIL — timeout fraction, or upper-quantile
wall time — not merely the median. A split halving wall time while multiplying
core time 8x is worth using on a few pathological regions and nowhere else.

Split the decision by stratum. It is a legitimate outcome that A wins on f=2 and
C wins on f=6.

---

## 8. What would stop the pilot

* any regression-suite difference at 0.2
* any split certificate failing coverage or disjointness
* any SAT model failing independent validation
* any arm disagreeing with another on solution count for the same region
* peak RSS approaching node memory — record the 99th percentile before scaling

---

## 9. What the pilot does NOT decide

Existence or non-existence at order 32. Full-campaign cost. Whether the split
rule balances children. Whether adaptive cubing beats the static rule. Whether
theorem-level UNSAT proofs are affordable — that needs DRAT output and
independent checking, and should be costed separately once a mechanism is chosen.
