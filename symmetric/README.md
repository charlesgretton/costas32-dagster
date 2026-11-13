# Transpose-symmetric Costas arrays

Arising from the observation that the fixed points of a transpose-symmetric
Costas array form a Golomb ruler.

## Why transpose symmetry is the only case

The non-trivial stabilisers in D4 reduce to one conjugacy class:

- horizontal flip: fixed means h_i = h_{n-1-i}, not injective.
- vertical flip: fixed means 2h_i = n-1, impossible.
- 180 rotation: the pair (i,j) and its image (n-1-j, n-1-i) have *identical*
  displacement (j-i, h_j-h_i), distinct unless i+j = n-1. Impossible for n>=3.
- 90 rotation: its square is 180.
- anti-diagonal: conjugate to the main diagonal in D4.

So a search over h = h^{-1} is exhaustive for the symmetric question.

## Baselines (three independent implementations agree on entered nodes)

| n | nodes | arrays |
|---|---|---|
| 16 | 160,797 | 40 |
| 18 | 864,774 | 20 |
| 20 | 4,710,666 | 8 |
| 22 | 25,853,570 | 10 |
| 24 | 142,822,399 | **0** |

Growth ratio ~5.5 per step of two orders (16, 18, ..., 26), projecting ~1.4e11 nodes and
about 1-2 core-days at n=32. (Corrected: an earlier ~6e14 applied the ratio once per order.)

## The fixed-point bound, and why it does not prune

Fixed points form a Golomb ruler, so C(f,2) <= n-1 gives f <= 8 at n=32, and
OGR(8)=34 > 31 excludes f=8. Hence f in {0,2,4,6}.

Implemented as a prune it fires **zero times** at n=16,18,20,22: the incremental
Costas check already subsumes it (a repeated fixed-point distance *is* a repeated
displacement). Measured maximum fixed-count reached is 4 at n=16 and 5 at n=20,22
against caps of 4 and 6. Retained as structure, not as a search optimisation.

## The f=2, M_LL=0 branch, closed

`src/f2_mll0_branch_search.cpp` exhausts it. M_LL=0 (no far pair maps to a far pair)
forces all transposition lengths <= 15 and all fixed points within a window of
15, so f=0 and f=6 die and f in {2,4}. At f=2 the 15 transposition lengths are
forced to be exactly 1..15.

Writing m_d = a_d + b_d for the doubled centre:

```
32,769,242  --FG-->  9,180  --FS-->  4  --Costas-->  0
```

- FG: m_{d+k} - m_d injective in d, for every gap k.
- FS: m_e - m_d injective among pairs with d+e = s, for every sum s.

FG alone removes 99.972%. The four survivors form two reflection orbits, each
killed by one explicit displacement identity (see z1/results/f2_mll0_residual_certificates.txt).

First-failure histogram over the fixed-sum fibres peaks at s=11, **not** at the
maximal-cardinality fibres s=15,16,17 — fibre size does not predict strength.
Note this is a first-failure count under a fixed testing order, not an
order-independent measure of per-fibre strength.

## The f=4, M_LL=0 branch, closed

`src/f4_mll0_cover_census.cpp`. Four fixed points form a Golomb ruler of diameter <= 15,
14 transpositions take distinct lengths from {1..15} with one omitted length r,
and parity couples them by a = r+1 (mod 2).

    N_F = 2,735  ->  N_(F,r) = 20,360  ->  N_domain = 20,360  ->  N_cover = 0

Nothing reaches FG, SFG, FS, the anchor tests or the Costas oracle.

**The algebraic filters are non-binding.** |A(F)| = 10 for *every* ruler and
N_domain = N_(F,r) exactly — not one pair loses a domain. Domain sizes run
89..196, median 143. The branch dies only at the global endpoint-cover layer.

## Corollary: M_LL = 0 is empty

f=0 needs 16 distinct lengths from {1..15}; f=6 needs a six-mark Golomb ruler in
a window of 15 against OGR(6)=17; f=2 and f=4 are the theorems above. So no
transpose-symmetric order-32 Costas array has M_LL = 0.

## Cell-count convention

Seven $(branch, f)$ labels are admissible under $Z=1$. One of them,
$Z{=}1\mathrm T$ with $f=6$, is empty **deductively** — six fixed points cannot
form a Golomb ruler inside a window of diameter 15 against OGR(6)=17 — so it is
not a computational cell. The remaining **six computational cells** are the
denominator used throughout. Five labels are now closed (four computationally,
plus the deductive one); two four-fixed-point cells remain active.

Do not alternate between "four of six" and "five closed" without stating which
denominator is meant.

## Z = 1 stratification: COMPLETE — all seven labels closed

Every remaining candidate has Z = sum_{d,e>=16} M_{d,e} >= 1. Since M is
symmetric, Z = D_L (mod 2), so Z=1 means exactly one long transposition (branch
T) or one long fixed pair (branch F).

| branch | f | result |
|---|---|---|
| Z=1T | 0 | **closed**  36 -> 1 -> 0 |
| Z=1F | 2 | **closed**  36 -> 0 (structural) |
| Z=1T | 2 | **closed**  72 -> 0 under full Costas |
| Z=1F | 6 | **closed**  728 -> 0 (structural *and* full Costas) |
| Z=1T | 6 | **closed deductively** — OGR(6)=17 > 15 window |
| Z=1F | 4 | **closed** — 19,405 -> 0, structural *and* full Costas; root space derived independently here |
| Z=1T | 4 | **closed** — 2,735 -> 0 under full Costas; premise totals match my independent derivation |

Reports and release bundles for the last two are in `z1/closed_cells/`.

**Cell 3 (Z=1T, f=2).** 326,480 parity-admissible tuples over 72 reflection-
normalised roots; predicate `EXACT_Z1_AND_FULL_COSTAS`. Census: 4,311,722,774
nodes, 16,310,601,351 Costas-collision prunes, 3,160,848,312 Z-budget prunes,
3,495.6 worker-seconds.

**Cell Z=1F, f=6.** *Complete result archive present* (`z1/closed_cells/z1f6_results.tar.gz`,
sha256 8aeb7f6e30158c44...), independently re-tallied in this repository: 728
structural + 728 full root records, identical key sets across modes, every record
terminal, zero covers, zero survivor files. Root space derives as 13 board-reflection orbits of the
unique normalised six-mark ruler shape (0,4,11,13,14,19) times 56 opposite-parity
omitted-length pairs = 728 roots. Closed twice over: structurally
(132,439,106 nodes, 0 covers) and under full Costas (310,755 nodes, 0 covers).
The structural closure is the stronger statement — no root admits even a
complete transposition cover.

## Validation dossier

| layer | what it validates |
|---|---|
| T4-8 positive arm | recursive termination, counting and emission under a satisfiable **weakened** spec |
| T4-5 / A5 | incremental Z accounting vs direct recomputation |
| production census | exhaustive failure under the **enforced** Z=1 and full-Costas conditions |
| independent root-space derivation | the premise space |
| independent archive retally | the stored evidence |
| **open: F+** | a separately written solver — no further testing of these can supply it |

## Retired implementations

`z1/retired/` holds the quarantined fast full-Costas prototype and a post-mortem.
Two independent defects, both found by measurement *after* I had argued from the
source that the code was correct: same-placement collision loss (under-prunes)
and a `static` recursive snapshot (over-prunes, can manufacture false zeros).
Its 13,928 / 14,602 / 15,707 benchmark and zero counts are withdrawn in full.

Required pattern for incremental oracles here: per-frame snapshot or reversible
trail, never static; a per-placement pending set; explicit insertion of the new
transposition's internal pair; and the popcount invariant
`displacements == C(points,2)` compiled in behind a debug flag.

## Scope

Closed: M_LL = 0 entirely. Open: everything with M_LL != 0, which is the bulk of
the symmetric problem, and the unrestricted order-32 question.
