# Proof inventory and Lean certification status

Every formal claim in the report, classified by what kind of thing it is and what
a Lean certificate would require.

**Current status: 3 claims proved, 2 partially proved, 31 open.** Sixteen
theorems typecheck under Lean 4.15.0 with **no Mathlib, no `sorry` and no
`native_decide`**; ten depend on no axioms at all and six on `propext` and
`Quot.sound` only. Run `proofs/lean/check.sh` to reproduce, or `make lean`.

Status values: `none` (nothing written) · `draft` (Lean statement written,
unchecked) · `stated` (statement typechecks, proof `sorry`) · `proved` (no
`sorry`, no `native_decide`) · `proved*` (complete but relies on `native_decide`
or another kernel-bypassing tactic) · `n/a` (not a mathematical claim).

---

## Tier A — deductive claims, formalisable from the statement alone

These are ordinary mathematics. A Lean proof is a matter of effort, not of
research.

| # | claim | report | proof given? | effort | status |
|---|---|---|---|---|---|
| A1 | **Diagonal parity floor.** *(arithmetic core proved)* $Z_1^{\mathrm{diag}} = 2\binom{e_0}{2}+2\binom{16-e_0}{2} = 2(e_0-8)^2+112 \ge 112$ | Thm 11.2 | yes | moderate | `core` |
| A2 | **Soundness of the $T_m$ inference rule.** *(logical core proved)* Interval disjointness certifies infeasibility | Lem 7.2 | yes | moderate–hard | `core` |
| A3 | **Automatic loss-free parameterisation.** Loss-free iff $q-1=N$ or $q-2=N$; fails at $N=32$ since 33, 34 are not prime powers | Prop 4.1 | partial | easy | `proved` |
| A4 | **Offset invariance of interpolation degree.** $u\mapsto\lambda u$ sends $a_j\mapsto a_j\lambda^{-j}$; $v\mapsto\mu v$ scales the interpolant; degree fixed | §8.2 | informal | easy | `proved` |
| A5 | **Telescoping identity.** $\sum_i(h_{i+m}-h_i) = (\sum\text{last }m)-(\sum\text{first }m)$, hence $T_m=T_{n-m}$ | §11.1 | yes | easy | **`proved`** |
| A6 | **One off-curve point forces full degree.** $N-1$ collinear points plus one off the line $\Rightarrow \deg P = N-1$ | §8.4 | yes | easy | `none` |
| A7 | **Overdetermination does not imply inconsistency.** $K_s$ with $\lambda_{ik}=w_i\oplus w_k$ is consistent for every $s$ | Rem 11.x | yes | easy | **`proved`** |
| A8 | **Truncation destroys associativity.** Finite counterexample in the truncated relation algebra | Prop 9.x | yes | easy | `none` |
| A9 | **A Costas array is not a representation.** 3,968 non-identity atoms against 992 ordered pairs | Prop 9.x | yes | easy | `none` |
| A10 | **Corrected board-network characterisation.** Board-relative injective network with a nonzero vertical-component axiom | Prop 9.x | definitional | moderate | `none` |
| A11 | **Domination.** The 2-adic tower is strictly dominated by flat exact propagation | Thm 9.x | yes | moderate | `none` |
| A12 | **$\ell_\infty$ collision bound.** Core pairs can collide only if $\mathrm{sign}(\varepsilon)=\mathrm{sign}(\varepsilon')$, $|\delta-\delta'|\le k$, $|\varepsilon-\varepsilon'|\le k$ | Thm 13.1 | yes | moderate | `none` |
| A13 | **Corner deletion is a translation.** Deleting a boundary dot acts by translation on survivors, absorbed by offset freedom | §8.4 | informal | easy | `none` |

A1 is the best first target: it is the only unconditional universal bound in the
report, its proof is a two-step counting argument, and it needs nothing from
Mathlib beyond `Finset.card` and parity.

---

## Tier B — computational claims, requiring verified computation

These are true statements about finite objects, established by search. A Lean
certificate means one of: `decide` (kernel-checked, feasible only for small
instances), `native_decide` (fast but bypasses the kernel — records as
`proved*`), or a verified checker consuming an externally produced certificate.

| # | claim | report | scale | realistic route | status |
|---|---|---|---|---|---|
| B1 | **$m_2 \ge 1$.** No mod-4 word avoids all diagonal level-2 survivors | Prop 11.3 | $2^{17}$ cases, union-find each | verified checker, or find the structural proof | `none` |
| B2 | **Census-complete rung $k=3$.** No order-32 array has an order-29 deletion minor | Thm 6.6 | $5.66\times10^8$ placements | certificate + verified checker | `none` |
| B3 | **Rung results ($k=2$, $k=4$).** Including $1.15\times10^{11}$ placements at $k=4$ | Thm 6.7 | $10^{11}$ | infeasible in-kernel; checker architecture only | `none` |
| B4 | **Completeness of the order-28 catalogue.** 712 arrays, 89 orbits | Prop 6.x | $10^3$ | `decide` plausible on the set equality | `none` |
| B5 | **Order-28 census classification.** 84 / 3 / 1 / 1 by coordinate system | Thm 8.3 | $10^3\times10^3$ | `native_decide` plausible | `none` |
| B6 | **F3, computational.** $|D_B|=77{,}074$, $|D_T|=117{,}880$, cost 1.050, zero false positives | Thm 7.3 | $3\times10^5$ configs | verified checker; soundness half is A2 | `none` |
| B7 | **Heredity is corner-driven.** 14.6% / 3.4% / 0% at $k=1,2,3$ over the order-28 census | Thm 6.x | $10^4$ | `native_decide` plausible | `none` |
| B8 | **The missing orbit.** One orbit unreachable by downward-only closure | Obs 6.x | $10^3$ | `decide` plausible | `none` |
| B9 | **Order-29 census reconstruction.** 164 arrays, 23 classes, 5 symmetric, per-method counts | §6.x | $10^2$ | **`decide` easily** — best Tier B target | `none` |

B9 is the cheapest real certificate available: 23 permutations, verify each is
Costas, expand under $D_4$, check the counts. Entirely within `decide`'s reach
and it underwrites Theorem 6.6's quantifier.

Note that B6's *soundness* component is exactly A2. Certifying A2 upgrades the
F3 result from "no false positives observed on 7,632 prefixes" to "cannot
produce a false positive", which is the more valuable half.

---

## Tier C — heuristics, measurements and methodology

Not mathematical claims as stated. They are calibrations, model fits, or
research guidance. Formalising them would mean formalising a statistical model,
which would certify the arithmetic without certifying the inference.

| # | claim | report | why not a Lean target |
|---|---|---|---|
| C1 | Order-sensitivity requirement | Obs 4.3 | explicitly a heuristic, not a theorem |
| C2 | Implication for rung prioritisation | Heur 6.x | extrapolative analogy |
| C3 | Quadratic collision cost fits the sporadic curve | Obs 12.6 | model fit |
| C4 | Where the forecast's weight sits | Obs 12.8 | statement about model-class dependence |
| C5 | Analytic null for the screening statistic | Obs 8.1 | probabilistic heuristic |
| C6 | Genealogy of the score-2 object | Obs 6.x | a computation's narrative |
| C7 | Independent agreement with the published classification | Obs 8.x | comparison of two computations |
| C8 | The predeclared F3 gate is underpowered | Obs 7.1 | statistical power calculation |
| C9 | Mechanistic reading of $T_m$ | Obs 7.4 | interpretation |
| C10 | F3′ verdict | Obs 7.5 | measurement against a declared gate |
| C11 | Constant factor, not slope (GF(32) family) | Obs 9.x | measurement |
| C12 | Calibration (anti-Ramsey) | Obs 13.x | measurement |
| C13 | Extinction-model observations (remaining) | §12 | model-dependent |

---

## Recommended order of work

1. **B9**, order-29 census reconstruction. Smallest real certificate; underwrites
   a census-complete theorem. A day.
2. **A1**, diagonal parity floor. The only unconditional bound; clean proof.
3. **A5**, **A3**, **A7**, **A6** — short items that clear quickly and build the
   Costas definitional layer the rest will reuse.
4. **A2**, $T_m$ soundness. Highest value per unit effort: it converts F3 from an
   empirical soundness claim into a proved one.
5. **B4**, **B8** by `decide`; **B5**, **B7** by `native_decide`, marked
   `proved*`.
6. **B1**–**B3** only via a checker architecture, and only if someone wants the
   rung theorems machine-checked. B3 at $10^{11}$ placements is not a kernel
   computation under any plausible design.

Everything in Tier A should be built on one shared definitional core: a `Costas`
predicate, the displacement map, the $D_4$ action, and the deletion/augmentation
operations. Getting those definitions right once is the main design decision, and
it is worth doing before proving anything.

## Honesty note

A Lean certificate for a Tier B claim certifies that *a particular algorithm run
on particular data produced a particular answer*. It does not certify that the
algorithm implements the intended mathematical object — that link is A-tier work.
The two F3 bugs are the cautionary case: both implementations were internally
consistent and would have passed a naive certificate; what caught them was a
positive-arm test, not a proof.
