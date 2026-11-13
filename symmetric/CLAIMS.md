# Transpose-symmetric order-32: claims and their evidential basis

Every row names the exact artefact that establishes it. Anything in `scratch/`
is provenance only and is the basis of nothing.

Evidence classes:
- **D** deductive — a proof, checkable by reading
- **F** finite computation — exhaustive search with a fail-closed terminal status
- **F+** finite computation reproduced by two independent implementations — *no claim currently carries this label; S-F6 and S-F7 are asserted reproduced by the external audit but the second implementation is not registered here*
- **M** measurement — a number, not a theorem

---

## Deductive results

| # | claim | basis |
|---|---|---|
| D1 | No order-$n\ge3$ Costas array has 180° rotational symmetry; horizontal, vertical and 90° stabilisers are also impossible. Hence transpose symmetry is the only case and an involution search is exhaustive for the symmetric question. | report §14.1, one-line proof |
| D2 | Fixed points of a transpose-symmetric Costas array form a Golomb ruler. With OGR(8)=34>31 this gives $f\in\{0,2,4,6\}$ at order 32. | report Prop 14.2; checked on all 158 arrays, 0 exceptions |
| D3 | Quadrant-mass identity $X_r-Z_r=-r^2+(2n-1)r-\binom n2$. At $n=32,r=15$: $X-Z=224$, so $M_{SS}\ne0$. | report §14.3; single-valued on every array at $n=12..22$ |
| D4 | $\operatorname{Aut}(G_{15})=\{\mathrm{id},\rho\}$, so the off-diagonal displacement quadrants cannot both vanish. | exhaustive automorphism search, 32 vertices, $\lvert\mathrm{Aut}\rvert=2$ |
| D5 | Parity: $c\equiv a\pmod 2$; hence $o(R)\equiv a+L$ (branch T), $o(R)\equiv a$ (branch F). With $R=\varnothing$ this forces $L$ even. | verified exhaustively over all admissible $(f,a,c)$ |
| D7 | **Orbit decomposition** $Z = I_F + q + 2C$ for involutions: tau{x,y}={h(x),h(y)} has orbits of size 1 or 2, and singletons are exactly the fixed-fixed far pairs plus the long transpositions. | `z2/README.md`; verified on 12,000 random involutions (n=16,20,24,32) and all 158 historical arrays, **0 violations** |
| D6 | **Unit-slope rigidity.** In an involution, adjacent difference $-1$ is either a length-1 transposition or has a distinct transpose partner with the same displacement; dually $+1$ and adjacent fixed points. So an involutive Costas permutation admits $-1$ only at its length-1 transposition. | two-line proof; **0 violations on all 158 historical arrays** |

## Finite-computation results

| # | claim | certificate | basis |
|---|---|---|---|
| F1 | No order-32 transpose-symmetric Costas array has $f=2$, $M_{LL}=0$ | $32{,}769{,}242 \to 9{,}180 \to 4 \to 0$ | `src/f2_mll0_branch_search.cpp`; 4 residues reduce to 2 reflection orbits, each with a displayed collision certificate in `z1/results/f2_mll0_residual_certificates.txt` |
| F2 | No order-32 transpose-symmetric Costas array has $f=4$, $M_{LL}=0$ | $2{,}735 \to 20{,}360 \to 20{,}360 \to 0$ | `src/f4_mll0_cover_census.cpp`; dies at exact cover, before any algebraic filter |
| F3 | **Corollary: $M_{LL}=0$ is empty.** $f=0$ and $f=6$ die structurally; $f=2,4$ are F1, F2. | — | report Cor 14.8 |
| F4 | $Z{=}1\mathrm T$, $f=0$ empty | $36 \to 1 \to 0$ | `z1/results/z1_T_f0_census36_complete.csv`, 36/36 `modeB_complete=1`; the single residue $(28,0)$ exhaustively classified by `census/z1_jobB_28_0.cpp` |
| F5 | $Z{=}1\mathrm F$, $f=2$ empty | $36 \to 0$ | `z1/results/z1F_f2_ledger.csv`, 36/36, structural |
| F6 | $Z{=}1\mathrm T$, $f=2$ empty | $72 \to 0$ | `z1/closed_cells/costas32_cell3_public_release.tar.gz` + manifest + report. **Complete result set re-tallied here**: 72/72 root records, exact expected key set, all `EXHAUSTED_NO_COSTAS_Z1_COVER`, zero covers, zero survivors. 4,311,722,774 nodes, 1.63e10 collision prunes, 3,495.6 worker-seconds, predicate `EXACT_Z1_AND_FULL_COSTAS`, source `7f5f2a8e01f86b0c`. |
| F9 | $Z{=}1\mathrm T$, $f=4$ empty — **the last $Z=1$ label** | $2{,}735 \to 0$ | `z1/closed_cells/z1t_f4_results.tar.gz` (sha `70bf07955fc02a18`) + manifest + source + report. **Root space derived here before the solver existed**; the campaign's internal totals — 297,838 long placements and 15,642,886 parity-admissible records — equal my independent figures exactly, so the census covered the intended premise space, not merely one record per outer root. 2,735/2,735 terminal, zero covers, zero survivors, 2.49e10 nodes, 10.03 core-hours. **T4-8 positive arm closed under a weakened Z-budget specification**: with only the `Zp+zadd>1` prune and terminal `Zp!=1` test removed, the unchanged recursion reaches accepted terminals and emits valid completions on F0000 — 3,498,614 lines during a 60-second bounded run (not a total), 2,000 sampled and 2,000 accepted by an independent checker, duplicate-free over the first 200,000. Establishes the recursion, acceptance, counter and emission machinery are operational; does **not** establish correctness of the enforced Z=1 budget, which is A5/T4-5. |
| F8 | $Z{=}1\mathrm F$, $f=4$ empty | $19{,}405 \to 0$ | `z1/closed_cells/z1f4_results.tar.gz` (sha `9b1fadb129200ed0`) + manifest + source. **Root space derived independently here** (2,573 canonical rulers, 19,405 roots — exact match) and **both censuses re-tallied**: 19,405 structural + 19,405 full records, identical key sets, keys equal my derived root space, all terminal, zero covers. 5.89e10 structural nodes / 4.54e8 full nodes. |
| F7 | $Z{=}1\mathrm F$, $f=6$ empty | $728 \to 0$ | `z1/closed_cells/z1f6_results.tar.gz` (sha `8aeb7f6e30158c44`) + manifest + report. **Complete result set present and re-tallied here**: 728 structural + 728 full records, identical key sets, all terminal, zero covers, zero survivor files. 132,439,106 structural nodes / 310,755 full nodes. |

## Measurements, not theorems

| # | statement | note |
|---|---|---|
| M1 | Baselines $n=16..24$: 160,797 / 864,774 / 4,710,666 / 25,853,570 / 142,822,399 nodes; 40/20/8/10/**0** arrays | three independent implementations agree on entered nodes |
| M2 | Growth ~5.5 per two orders, projecting ~1.4e11 nodes (~1-2 core-days) at order 32 | extrapolation from orders 16-26; corrects an earlier ~6e14, which applied the ratio per order |
| M3 | The D2 fixed-point cap fires **zero** times as a search prune | true but non-binding; the incremental Costas check subsumes it. Recorded so it is not implemented twice |
| M4 | Node profiles across $L$ and $u$ | placement-dependent; not a monotonicity law |

## Withdrawn

| id | statement | reason |
|---|---|---|
| W1 | 13,928 / 14,602 / 15,707 node benchmark and its zero counts for Cell 3 | produced by `z1/retired/cell3_full_costas_UNSOUND_d778ab05.cpp`, which has two independent defects: same-placement collision loss (under-prunes) and a `static` recursive snapshot (over-prunes, **can manufacture false zeros**) |
| W2 | 10 pre-audit $Z{=}1\mathrm T$, $f=2$ root results | produced by a lag-1 binary with a stale-bit rollback defect; retained as provenance only |
| W3 | "the defect only threatens false positives" | wrong — the static snapshot over-prunes and can produce false zeros. Diagnosis was incomplete and generalised from |

## Registry hygiene

 now derives its summary from the claims list rather than
carrying hand-maintained counts. Fixing this exposed a pre-existing defect: the
summary asserted 36 claims across three tiers including 13 Tier C, while the
list held 22 objects and no Tier C entries at all. Recorded in the registry
under . STATUS CHECK PASS: 35 claims, 2 withdrawn, 1 known gaps fails the build if the summary and
list ever diverge again.

## All seven Z=1 labels closed

$$Z{=}1 \text{ is empty for transpose-symmetric order-32 Costas arrays.}$$

| branch | $f$ | certificate |
|---|---|---|
| T | 0 | $36 \to 1 \to 0$ |
| F | 2 | $36 \to 0$ |
| T | 2 | $72 \to 0$ |
| T | 6 | deductive (OGR(6)$=17>15$) |
| F | 6 | $728 \to 0$, twice over |
| F | 4 | $19{,}405 \to 0$, twice over |
| T | 4 | $2{,}735 \to 0$ |

### Next layer: Z = 2

The lemma splits it into exactly two types — S ($I_F+q=2$, $C=0$) and X
($I_F=q=0$, $C=1$) — with $I_F+q=1$ excluded outright. Ten feasible cells;
census in `z2/README.md`. The fixed-point catalogue there reproduces all three
Z=1 catalogues (2,735 / 2,573 / 13) as special cases of one formula.

Combined with the $M_{LL}=0$ closure, **every remaining order-32
transpose-symmetric candidate satisfies $Z \ge 2$.** That is the new frontier.

**Denominator convention.** Seven $(branch,f)$ labels exist under $Z=1$; one,
$Z{=}1\mathrm T$ $f=6$, is deductively empty and is not a computational cell.
Six computational cells is the denominator. **Six labels closed, one active** ($Z{=}1\mathrm T$, $f=4$).
