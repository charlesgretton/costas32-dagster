# Costas arrays of order 32 — investigation repository

Orders 32 and 33 are the smallest for which the existence of a Costas array is
unknown. This repository holds the complete software and data record of a
systematic investigation: the consolidated report, every tool that produced a
result in it, the catalogues those tools consume, and the raw output of the long
runs.

Start with `report/costas32_report.pdf` (44 pages). Everything here is referenced
from it.

> The investigation does not resolve existence at order 32. It proves two
> census-complete deletion-minor exclusions, classifies the generated
> augmentation channel from order 30, reconstructs and independently verifies the
> order-29 census, and introduces a sound telescoping-sum propagator that passes a
> prospective complete-population benchmark with substantial marginal coverage at
> low additional measured work. The remaining existence problem consists of arrays
> outside the tested construction and deletion-minor channels, and no current
> structural classification controls that residual class.

## Version

See `VERSION`. `make manifest` regenerates `MANIFEST.sha256`, which every
released archive should carry.

## Quick start

```bash
make            # builds all C++ tools
make selftest   # seven independent checks; all must pass before trusting anything
```

`make selftest` runs: the rung engine reproducing the published k=1 and k=2
results; both coordinate screens recovering degree 1 for Welch and Golomb
including GF(2^5); the SAT encoder agreeing with brute force on every permutation
at N=6,7,8; the diagonal parity floor holding identically; the signed-clique
exhaustion establishing m_2 >= 1; and the F3 regression guard, which fails loudly
if either of the two fixed propagator bugs reappears.

## Results, and what produced them

### Census-complete theorems

| result | evidence | tool |
|---|---|---|
| No order-32 Costas array contains an **order-29** Costas deletion minor | 565,836,800 placements over all 164 arrays / 23 classes, `CENSUS MATCH` | `rung/` |
| No order-32 Costas array contains an **order-28** Costas deletion minor | 115,087,822,400 placements over all 712 arrays / 89 classes, 89 units all `EXHAUSTED` | `rung/` |

The two are **logically independent**: deriving either from the other needs a
hereditary-minor property that the order-28 heredity measurement shows is far
from automatic (a single corner deletion preserves the Costas property 14.6% of
the time). They close different extension channels.

The k=2 rung is catalogue-relative — order 30 has never been enumerated, so its
664 cores are the generated set, not a census.

### F3: telescoping-sum propagation — passed a prospectively frozen gate

The one prospectively gated positive result in the investigation.

```
benchmark  B_{12,6}  every Costas-valid SIX-LEADING-COLUMN prefix at order 12
                     (not arbitrary six-cell assignments)
                     304,288 valid / 296,656 infeasible / 7,632 completable
                     split independently reproduced by a second completion procedure
baseline   D_B = D_RA u D_L3          77,074   (25.98%)
candidate  D_T = D_B + T_m rule      117,880   (39.74%)
marginal   |D_T \ D_B|                40,806
gate       >= ceil(1.104167*|D_B|) = 85,103     -> PASS
cost       declared propagation-work ratio 1.050 -> within 2x
soundness  0 rejections of 7,632 completable prefixes -> PASS
```

The inference rule is **proved sound**, not merely validated: the telescoping
identity sum_i (s_{i+m} - s_i) = (sum of last m) - (sum of first m) holds for
every sequence, the k undetermined differences are distinct because the
completion is Costas, and both interval constructions are outer approximations,
so disjointness can never be manufactured.

Two implementation bugs produced an earlier wrong verdict and are recorded as
findings: singleton shaving was a silent no-op, and RA rejected every input. The
second was caught immediately by the complete positive arm — which supports a
general point. **Testing only known-infeasible configurations can measure
detection power but cannot establish even empirical soundness.**

### F3': does it reduce an actual search?

One solver, three propagator flags, every non-propagation choice identical, and
an invocation schedule declared a priori and never tuned.

```
 n   solutions      N_inc      N_L3   N_L3+Tm   R_tree  W ratio    t_L3   t_L3+Tm
11       4,368  1,437,514   379,290   259,414    0.316    1.055     5.0s     5.9s
12       7,852  6,977,361 1,522,289 1,119,809    0.264    1.047    31.8s    36.8s
13      12,828 33,831,238 5,785,132 4,175,962    0.278    1.037   174.4s   197.1s
```

Solution-set identity is established **exactly**: each mode emits every solution
in canonical form and the sorted files are compared byte for byte. All three
modes produce identical files at orders 11, 12 and 13 (sha256 prefixes
3b346690b48c2527, 2baed7d03cc6f9de, b6cf5cfc1580bff2). The 64-bit aggregate
hashes are kept only as a fast regression guard — they are not collision-free
certificates of set equality.

At order 13 L3+T_m explores just 12.3% of the incremental-only tree
(4,175,962 against 33,831,238 nodes) and still takes 197s against 3.1s. The
problem is cost per propagated node, not lack of deduction.

**Scientific gate: PASS.** Identical solution sets; tree ratios 0.684 / 0.736 /
0.722 against a required <= 0.90; work ratios 1.055 / 1.047 / 1.037 against a
required <= 1.25.

**Operational gate: FAIL.** 0 of 3 orders show a wall-time improvement; L3+T_m is
12-18% slower than L3.

The larger finding concerns the baseline, not the candidate: incremental-only
search explores 5.5-8.1x more nodes yet runs 53-63x faster, because the exact
bitmask check is nearly free and shaving is not. Heavyweight propagation is an
operational loss in *either* configuration at these orders, and T_m inherits
that. The node-reduction trend is flat rather than growing, so nothing here
supports projecting a crossover.

### The extinction model

A first-moment model with constraint cost about n^2/12, derived before fitting
and confirmed to 2% by the published sporadic equivalence-class counts, tracks
the sporadic curve across four orders of magnitude and places extinction at n=27
against an observed n=28. Extrapolated, order 32 expects about 1e-4 sporadic
classes.

This is **conditional on a structural assumption the data do not establish**. A
cubic fits the same eight points *better* and extrapolates to explosion; the
convexity that carries the conclusion fails empirically at the last three data
points. Under superlinear growth P(no further sporadic) = 0.97; under linear
growth at the terminal slope it is 0.54 and the series diverges. See report
section 12.5.

### Coordinate classification of the order-28 census

All 712 arrays classified by coordinate system with no provenance information:
84 classes single-exponential over GF(29), 3 dual-exponential over GF(2^5), 1
dual-exponential over GF(31), 1 generic in both. The published breakdown is
84 W1 + 3 G4 + 1 G3 + 1 G1 — the multisets {84,3,1,1} agree exactly, class by
class, from independent derivations.

### Closed lines

Additive-node polynomial screening (no discriminating power — assigns known
algebraic arrays the same statistics as random permutations). Unconditioned m_2
minimisation. One-step survivor-hypergraph escape (Lambda_k identically 0 for
Costas arrays and random permutations alike). Inverted construction search over
low-degree permutation polynomials. Details and the reason each closed are in
the structural-approaches and extinction-model sections.

## Proof certification

`make proof-status` reports the tracker. All 35 formal claims in the report are
inventoried in `proofs/INVENTORY.md` with a Lean certification state each.

**Three of the 35 tracked report claims are fully proved in Lean, and two have partially formalised cores.** Sixteen theorems typecheck under Lean
4.15.0 with **no Mathlib, no sorry and no native_decide** — ten depend on no
axioms at all. `make lean` reproduces (needs a 4.15.0 toolchain on PATH).
Proved: the telescoping identity and T_m = T_(n-m); that a cut labelling is
consistent at every clique size; and the prime-power obstruction at order 32.
Cores proved for the T_m soundness lemma and the diagonal parity floor. The
inventory separates:

- **Tier A (13)** deductive claims formalisable from the statement alone. Best
  first targets: the diagonal parity floor, and the T_m soundness lemma — the
  latter would upgrade the F3 result from "no false positives observed" to
  "cannot produce a false positive".
- **Tier B (9)** computational claims needing `decide`, `native_decide`, or a
  verified checker consuming an external certificate. The order-29 census
  reconstruction is the cheapest real certificate available and underwrites a
  census-complete theorem.
- **Tier C (13)** heuristics, model fits and measurements — not Lean targets as
  stated.

A caution recorded in the inventory: a Tier B certificate proves that a given
algorithm on given data produced a given answer. It does not prove the algorithm
implements the intended object. The two F3 bugs are the cautionary case — both
were internally consistent and would have passed a naive certificate; a
positive-arm test caught them, not a proof.

## Transpose-symmetric order-32 campaign

Fixed points of a transpose-symmetric Costas array form a Golomb ruler, so
f <= 8 at order 32, and OGR(8)=34 > 31 gives f in {0,2,4,6}. Rotational and
axial stabilisers are impossible outright, so transpose symmetry is the only
case and an involution search is exhaustive for the symmetric question.

Baselines (three independent implementations agree on entered nodes):
n=16: 160,797 nodes / 40 arrays; n=20: 4,710,666 / 8; n=24: 142,822,399 / **0**.
Growth ~5.5 per two orders projects ~1.4e11 nodes at order 32, about 1-2 core-days
(corrected from an earlier ~6e14, which applied the ratio per order).

**Corollary: no transpose-symmetric order-32 Costas array has M_LL = 0.**
f=0 and f=6 die structurally; f=2 by centre-fibre classification with two
explicit collision certificates; f=4 by an exhaustive zero-cover census over
20,360 parameter pairs, where the anchor algebra proved entirely non-binding
and only global endpoint packing bites.

f=2 detail:

    32,769,242  --FG-->  9,180  --FS-->  4  --Costas-->  0

exhaustive over all 168 fixed-point pairs. The four survivors form two
reflection orbits, each with an explicit one-line collision certificate
(`symmetric/z1/results/f2_mll0_residual_certificates.txt`), so the exclusion does not rest on a
terminal zero count.

## Where results come from

`symmetric/CLAIMS.md` is the inventory: every claim, its evidence class
(deductive / finite computation / reproduced twice / measurement), and the exact
file that establishes it. Withdrawn results and the defects that caused the
withdrawal are listed there too, not deleted.

`proofs/STATUS.json` carries the same in machine-readable form, including a
`withdrawn` block.

Anything under a `scratch/` directory is provenance and is the basis of nothing.

## Status

| area | state |
|---|---|
| augmentation ladder k=1..4 | census-complete; no order-29 or order-28 deletion minor |
| order-29 Lean certificate | 23/23 seeds kernel-checked; orbit modules need >4 GB |
| GPU experiment | pre-hardware validation complete; 6-cell matrix ready |
| transpose-symmetric: M_LL = 0 | **closed entirely** |
| transpose-symmetric: Z = 1 | **all 7 labels closed**; hence every remaining symmetric candidate needs Z >= 2 |
| unrestricted order 32 | open, untouched by the above |

## Layout

```
report/         the consolidated report, LaTeX source and PDF
catalogues/     verified Costas array catalogues
solver/         exact depth-first search
rung/           augmentation ladder: engine, fail-closed merger, raw results
propagation/    RA closure, L3, the T_m propagator, benchmark generator, regression
screening/      polynomial coordinate classification
algebraic/      finite-field construction families
dyadic/         2-adic defect filtration
symmetric/      transpose-symmetric search, f=2 branch closure, certificates
proofs/         proof inventory, Lean status tracker, statement drafts
structure/      matroid and distinct-difference-configuration tests
sat/            CNF/DAG generation for distributed SAT
```

## Catalogues

| file | contents | status |
|---|---|---|
| `cat11.txt` / `cat12.txt` / `cat13.txt` | 4,368 / 7,852 / 12,828 arrays | complete censuses |
| `cat28.txt` | 712 arrays, 89 classes | **complete census**, generated not imported |
| `cat29_census.txt` | 164 arrays, 23 classes | **complete census**, reconstructed and verified |
| `cat29_ec_representatives.txt` | 23 representatives with construction labels | source rows for the above |
| `cat29_algebraic148.txt` | 148 arrays, 21 classes | what corner surgery reaches |
| `missing_orbit_representative.txt` | 1 array | the orbit a deletion-only generator misses |

**`cat28.txt` is generated, not imported.** `./rung/costas_rung cat 28 out.txt`
reproduces it from W1(29), G2(29), G2(31), G2(32), W1(31) closed under corner
deletion **and corner addition**. The addition step is what a downward-only
closure misses — G2(29) has order 27 and reaches 28 only upwards — and omitting
it costs exactly one orbit. Two sets of size 712, one inside the other, so they
coincide; no trust in provenance is required.

**`cat29_census.txt` was reconstructed** from the 23 equivalence-class
representatives published with the order-29 enumeration. Every representative was
independently validated as a Costas permutation before D4 expansion, and all
published figures are reproduced: 164 arrays, 23 classes, 5 symmetric, per-method
counts G0 4 / G2 64 / G3 24 / W0 24 / W2 32 / RW0 16.

The 16-array gap between the generated 148 and the census 164 is exactly the two
RW0 classes. The Rickard-Welch method appends a blank row, cyclically shifts, and
adjoins a column — not corner surgery — so no closure under corner operations
reaches them. Order 29 has **zero sporadic** arrays; those 16 are *emergent*.

## Reproducing the runs

```bash
# census-complete k=3 (12 s)
./rung/costas_rung run 29 catalogues/cat29_census.txt 0 1 --thresh 4 > u.txt
python3 rung/merge_rung.py u.txt

# k=4 across N workers (40 core-minutes total)
for u in $(seq 0 88); do
  ./rung/costas_rung run 28 catalogues/cat28.txt $u 89 --thresh 0 > units/unit_$u.txt &
done; wait
python3 rung/merge_rung.py units/*.txt

# re-verify the archived k=4 run from its raw units
tar -xzf rung/results/rung4_units.tar.gz && python3 rung/merge_rung.py units/*.txt

# F3 protocol run and the full external-validation sweep (~1 min)
./propagation/f3_complete 12 6
for c in "10 5" "10 6" "11 6" "11 7" "12 7"; do ./propagation/f3_complete $c; done

# coordinate classification, dyadic profile
python3 screening/dual_exponential_screen.py classify catalogues/cat28.txt 28
python3 dyadic/dyadic_profile.py calibrate catalogues/cat28.txt 28
```

## Discipline

Four conventions are load-bearing. Each was adopted after a failure in this
project, and each is the reason a later error was caught.

**Assert the invariant before computing on the object.** Every tool validates its
input as a Costas permutation and stops rather than proceeding. An analysis here
once reached structural conclusions about arrays that were not Costas, having
bypassed exactly this guard.

**Test the positive arm, not just the negative one.** Detection power is measured
on infeasible inputs; *soundness* can only be measured on feasible ones. The RA
bug that rejected every input was invisible to detection counts and obvious the
moment the completable arm was checked.

**Compute the null analytically when sampling cannot resolve it.** Three separate
analyses drew conclusions from samples far below the resolution of the quantity
estimated — 1e4 Monte Carlo draws against a null of 5e-53, ~250 polynomials
against a window penalty of 4e-15, and a 296-element benchmark whose standard
error was 8. In each case a zero count was read as absence.

**Fail closed on coverage.** `merge_rung.py` refuses an exhaustive verdict unless
every unit reports `EXHAUSTED`, all units agree on parameters and catalogue hash,
coverage is exactly 0..N-1 with no gap or duplicate, and every low-defect
configuration re-scores from scratch.

## Status and what remains

**Not resolved.** Existence at order 32 is open.

**Live work, in order.**

1. *Publication.* The census-complete rungs, the order-29 reconstruction, the F3
   result with its soundness lemma, and the coordinate classification are
   coherent and finished.
2. *F3'.* Integrate L3+T_m into the depth-first solver and measure full-search
   **tree reduction** at orders with complete ground truth. Detection coverage on
   static prefixes is not runtime improvement in a search.
3. *Order-30 enumeration.* Now a hypothesis test, not data collection: the
   extinction model predicts only W1(31) and G2(32) derivatives and zero sporadic
   classes. One sporadic array there refutes the model and reopens 32. Roughly
   550 modern core-years at the measured 5.24x growth ratio — a cloud or
   volunteer-computing problem, not a mathematical one. The acceptance test is
   non-negotiable and cheap: reproduce orders 27, 28 and 29 exactly first.
4. *The asymptotic theorem.* A proof that f(n) = log n! - log C(n) satisfies
   f(n) - log(n!/8) -> +infinity, with f(n) >= c n^2 or f(n) >= (1+eps) n log n
   as sufficient forms. Monotonicity and convexity are informative intermediates
   but neither implies extinction. This is the missing ingredient in every
   probabilistic statement in the extinction-model section, and unlike the existence question it is
   uniform in n.

**A caution carried through the report.** A successful non-existence argument
must distinguish order 32 from 31 and 36, where arrays exist. That is a research
heuristic, not an impossibility theorem — a theorem can be uniform in n while its
arithmetic hypothesis varies with n, as Bruck-Ryser is. What the measurements
establish is narrower: every *particular* relaxation tested returns the same
verdict at 31, 32 and 36.

## Exploratory material

`dyadic/anneal.cpp`, `anneal2.cpp`, `m2_milp.py`, `m2_small.py` are stochastic
and MILP searches for m_2, retained as an accurate record. They are exploratory,
not proof-certifying, and the unconditioned m_2 programme is closed as an
order-32 route. `propagation/tm_propagator.cpp` is the earlier F3 suite,
superseded by `f3_complete.cpp` but kept because the two bugs it contained are
documented findings.

## Licence

Source code is licensed under the Apache License, Version 2.0 (`LICENSE`). The reports, papers,
documentation and project-generated data are licensed under Creative Commons Attribution 4.0
International (CC BY 4.0, `LICENSE-CC-BY-4.0.md`). `LICENSING.md` gives the mapping of files to licences;
material by others keeps its original terms.

## Errata

We welcome reports of errors, omissions and overlooked prior work. Please send them to the corresponding
author, Charles Gretton, at charles.gretton@anu.edu.au. Every report that leads to a correction will be
acknowledged in the errata and in any revised edition, cited as a private communication; where the point
was already made in a publication that appeared before the report's publication date, that publication
will be cited as well.

