# Costas Array Literature Search: 2022–2026

**Prepared:** 21 October 2026 · **Scope:** recent work relevant to Papers 1, 2, and 10 (state-of-the-art account; order-32 near-solution N32; LP-2 transition and native-search scaling), plus the two pivotal external claims flagged in the internal review (the August 2026 near-solution gist; the October 2026 restricted-class GPU sweep).

**Method.** Primary sources were fetched and read directly where accessible (gist, arXiv abstracts, publisher pages, HAL PDF excerpts). Every reference below was checked against at least one primary page (publisher, arXiv, HAL, or the author's own listing). Evidence levels are stated explicitly. This search is broad but not exhaustive: it covered web and arXiv-indexed literature, not a full MathSciNet/ZBblat sweep; the CSPLib and OEIS reference lists were used as discovery aids only.

---

## A. Audit of the two pivotal claims

### A1. The August 2026 near-solution gist — VERIFIED, metrics independently reproduced

**Source:** Vuk Rosić, "Order-32 Costas array: reproducible bounded partial result," GitHub gist, created 2026-08-19 04:05 (2 revisions; README status date 2026-08-19). https://gist.github.com/vukrosic/afa4096cd8b16fe17dbf413f63422b72

**The array (zero-based):**

```
0 1 28 20 27 17 18 21 30 26 14 9 25 11 31 29
23 5 13 6 16 15 12 3 7 19 24 8 22 2 4 10
```

**Claims verified in this search:**
- 496 point pairs, 494 distinct displacement vectors, 2 repeated-vector occurrences — **numerically reproduced by me** (independent script): the repeated classes are (1,1) on pairs (0,1),(5,6) and (5,17) on pairs (0,5),(1,6); excess-multiplicity score 2; pair-collision score 2. Both defect metrics equal 2, so any metric convention coincides here.
- DRAT-checked Hamming-ball exclusion: "No order-32 Costas permutation is within Hamming distance ≤ 12 of the candidate" — **reported in the document with artifacts**: 21 checked DRAT branch proofs over a disjoint 118-cell exact-shell-12 partition, checked radius-11 dependency, drat-trim checker (commit 2e3b2dc0…), coverage check PASS, certificate receipts and hashes included in the gist. The 3.79 GB proof package is retained outside the gist and was **not independently checked by me**.
- Exact C++ enumeration of Hamming shells 12–16 with no witness — reported as exhaustive-program evidence (the gist itself distinguishes this from the DRAT-backed radius-12 claim).
- D4 corollary: the eight radius-12 balls around the candidate's D4 orbit are disjoint, excluding 334,181,973,139,327,080 permutations ≈ 1.27×10⁻¹⁸ of 32!. Explicitly not a global nonexistence proof.
- Global CaDiCaL/Kissat/CP-SAT runs returned UNKNOWN or were interrupted; no verdict treated as evidence.

**Priority.** The gist was created 19 August 2026 with the candidate and certificate receipts already present (manifest verification 2026-08-19T03:17:22Z). The gist itself disclaims priority/novelty claims. Per the internal review, the same array (up to symmetry) is Paper 2's N32, found independently; the equivalence is **user-reported** — I reproduced the gist's metrics and computed its D4-canonical (lexicographically minimal) form, which equals the array above; compare against Paper 2's N32 to confirm. A defensible statement is "publicly documented by 19 August 2026," not "first discovered."

**Action for Paper 2:** cite the gist for prior public documentation of the array and for the Hamming-ball certificate type; state the independent-discovery circumstance; do not claim priority.

### A2. The October 2026 restricted-class GPU sweep — VERIFIED as a real preprint; claims as reported

**Source:** Bogdan Dumitru and Cristian Budala (University of Bucharest), "Local Patterns and the Cost of Costas Array Search," HAL preprint hal-05731061v1, October 2026 (not peer-reviewed). https://hal.science/hal-05731061 · Artifact repository: https://github.com/bogdan27182/costas-paper

**Claims as reported in the preprint (excerpts read; landing page did not parse, content verified via the PDF and search-index excerpts):**
- Restricts Costas-array search at a new order using seven-dot difference signatures observed at smaller orders.
- At order 28, a vocabulary built only from the 204 arrays of order 27 recovers 67 of the 89 known classes, up to rotations and reflections.
- Completed restricted sweeps at orders 30 and 31 return exactly the known arrays and no others (order 31: the four solutions of the one known class, 512 shards).
- At order 32 the restricted class is **empty**: 1.08×10¹⁰ depth-7 prefixes enumerated, 295,628 passing the filter, 1.22×10⁹ depth-10 subtrees solved in 102 GPU-hours.
- Cost calibration: sampled estimate of 43.7 CPU-years for unrestricted order-28 search; GPU projection of 7.97 GPU-years at order 30.
- The preprint explicitly states the empty restricted class is **not** evidence against order-32 existence; any surviving array would be sporadic (its first-seven-dot signature would not occur in the orders-24–31 vocabulary).

**Caveats for citation:** (1) preprint, not peer-reviewed; (2) the "empty" result is restricted-class emptiness, not unrestricted order-32 evidence — the preprint says so itself; (3) the same author pair wrote the symmetric census below (hal-05730608 / arXiv:2608.28690), so treat the two as one research group's outputs, not independent corroboration; (4) I did not rerun their benchmarks.

---

## B. Verified 2022–2026 references

| # | Reference | Status | Key claim | Suggested placement |
|---|---|---|---|---|
| 1 | Rosić, gist, 2026-08-19 | Unpublished gist (documented) | Order-32 permutation, defect 2; DRAT-verified Hamming-ball exclusion (radius 12); shells 13–16 empty | Paper 2 (priority + certificate type); Paper 1 (state of the art) |
| 2 | Dumitru & Budala, HAL hal-05731061, Oct 2026 | Preprint | Seven-dot-signature restricted sweeps; order-32 restricted class empty; GPU cost model | Papers 1 and 10 (cost calibration, restricted-search frontier) |
| 3 | Dumitru & Budala, arXiv:2608.28690, 26 Aug 2026 | Preprint | Exhaustive census of main-diagonal symmetric Costas arrays, orders 37–42 (4, 0, 16, 2, 12, 4); no sporadic symmetric arrays at orders 24–42; collision model for random involutions, λ_sym(n) = (n−1)(n−2)/18 + n^{3/2}/360 + O(n) | Papers 1 and 10 (involution campaign; collision model directly relevant to symmetric-search density modeling) |
| 4 | Vulakh & Finkel, Soft Computing 26(12):5765–5772, 2022 | Peer-reviewed (journal) | mDRACO ant-colony search; order-32 permutation with 17 Costas-property violations after >10,000 CPU-days (Appendix) | Papers 1 and 2 (near-solution landscape comparison) |
| 5 | Warnke, Correll & Swanson, IEEE Trans. Inf. Theory 69(1):575–581, 2023 | Peer-reviewed (journal) | Density C(n)/n! of Costas arrays decays exponentially: C(n)/n! ≤ e^{−cn} | Paper 10 (density caveat: measured transitions at orders 12–16 sit at the count peak; exponential decay of density underwrites the extrapolation risk); Paper 1 |
| 6 | Correll & Swanson, Des. Codes Cryptogr. 91(3):779–794, 2023 | Peer-reviewed (journal) | Difference-based structure: number of positive first differences of an order-n Costas array within 2.5 of (n−1)/2; this property alone gives O(n^{−1/2}) density | Paper 10 (moment-cut / density-of-injectivity observation — must-cite); Paper 1 |
| 7 | Gulec & Abolghasemi, IEEE ICC 2026 (Glasgow, 24–28 May 2026), arXiv:2602.03407 | Peer-reviewed conference (presented May 2026) | Universal Costas Matrices framework; reconstruction-based search; confirms enumeration frontier remains 29; ICC DOI 10.1109/icc59461.2026.11588169 (proceedings p. 6946) | Paper 1 (most recent construction work) |
| 8 | Ardalani & Pott, IEICE Trans. Fundamentals E106-A(12), Dec 2023 | Peer-reviewed (journal) | A new transformation for Costas arrays (DOI 10.1587/TRANSFUN.2023SDP0005); see also Ardalani, PhD dissertation, U. Halle, 2023 | Paper 1 (optional) |
| 9 | Liu & Wang, arXiv:2506.12559 (v2, 27 Dec 2025) | Preprint | Cross-correlation bounds for large-size Costas families (extended Welch, power-permutation, PW families) | Paper 1 (optional; applications side) |
| 10 | Liu & Winterhof, IEEE Trans. Inf. Theory 70(11):7848–7852, 2024 | Peer-reviewed (journal) | Cross-correlation of Golomb Costas permutations | Paper 1 (optional) |
| 11 | Codognet, EvoCOP 2022, LNCS 13222, pp. 143–158 | Peer-reviewed (conference) | Costas Array Problem in QUBO for quantum annealing | Paper 1 (optional) |
| 12 | Rubio & Torres, arXiv:2208.02378, 2022 | Preprint | Multidimensional Costas arrays and periodicity; non-existence results | Paper 1 (optional) |
| 13 | Diaz, Richoux, Codognet, Caniou & Abreu, LION 6, 2012 | Peer-reviewed (conference) | Constraint-based local search (Adaptive Search) for Costas | Baseline for local-search line (optional) |

---

## C. Foundational references touched during the search (pre-2022)

- **Beard, Russo, Erickson, Monteleone & Wright**, "Costas Array Generation and Search Methodology," IEEE Trans. Aerosp. Electron. Syst. 43(2):522–538, 2007. DOI 10.1109/TAES.2007.4285351. Orders 24–26 exhaustive disclosure; bitmask difference-table native search.
- **Russo, Erickson & Beard**, "Costas array search technique that maximizes backtrack and symmetry exploitation," CISS 2010, pp. 1–8. DOI 10.1109/CISS.2010.5464772. The "benchmark Russo search" later used by Gulec & Abolghasemi.
- **Drakakis**, "Open problems in Costas arrays," arXiv:1102.5727 (2011). The standard open-problem survey. **Caveat for Paper 1:** its Table 1 prints **12752** for order 14 — a transposition typo; the correct count is **17252** (confirmed by OEIS A008404 and your own reproduction). Cite the corrected figure or note the erratum.
- **OEIS A008404** (counts through order 29: …, 7852, 12828, 17252, 19612, 21104, 18276, 15096, 10240, 6464, 3536, 2052, 872, 200, 88, 56, 204, 712, 164). Your self-reproduced counts at 12–14 match exactly.

## D. Leads — not citable as primary sources

- **TheoremDB** (theoremdb.org) and **FrontierShift** (aitonomy.org) — aggregators; useful leads only; multiple pages repeating one preprint are not independent confirmation.
- **butkeraites/costas-array** GitHub repository and butkeraites.com ("The N=32 Wall") — unpublished research; the dyadic non-obstruction finding (dyadic-feasible permutations abundant; power-of-two structure alone is not an obstruction) is a useful unpublished lead for any order-32-specific theorem, but cite only if it reaches a citable form.
- **Matpic essay** and **artwaste.land** — journalistic/essayistic; the latter documents the Drakakis survey's 12752 typo.
- **James K. Beard's database** — "Costas arrays and enumeration to order 1030," IEEE DataPort, DOI 10.21227/H21P42 (the CA_Database_3-100.zip the gist used for provenance).

## E. Corrections and cautions to carry into the papers

1. **Order 31 has eight *known* arrays, not exactly eight** — complete enumeration stops at 29; do not build density arguments on an exact order-31 count.
2. **The gist's proof package was not independently checked here** — the DRAT result is "reported with in-gist receipts/hashes"; the 3.79 GB proofs are external. If Paper 2 leans on it, either replay the verification script against the retained package or state the evidence level.
3. **Restricted-class emptiness ≠ unrestricted evidence** — the HAL preprint states this itself; keep the distinction verbatim when citing.
4. **Priority language** — "publicly documented by 19 August 2026" is defensible; "first discovered" is not (the gist disclaims priority; private computations cannot be excluded).
5. **Author overlap** — the two Dumitru & Budala preprints are one group; do not cite them as independent corroboration of each other.
6. **N32–gist equivalence is user-reported** — the comparison criterion is now cheap: the gist array's D4-canonical form is the array listed in §A1 (it is the lexicographic minimum of its own orbit).

## F. Endorsed amendments (in answer to "Shall I make the Paper 2 and Paper 10 changes?")

Yes — proceed, with these placements:

- **Paper 2:** add the gist citation (prior public documentation of the defect-2 array; independent discovery noted; Hamming-ball certificate and its artifact/receipt model referenced). Optionally contrast with Vulakh & Finkel's 17-violation witness (different metric — state the metric when comparing).
- **Paper 1:** update the state of the art to include items 2–7 of the table (Warnke–Correll–Swanson, Correll–Swanson, Vulakh–Finkel, Gulec–Abolghasemi, both Dumitru–Budala preprints, the gist); correct or footnote the Drakakis Table 1 order-14 figure if the survey is cited.
- **Paper 10:** add the binary-AC depth-distribution measurement, the moment-cut test with the density-of-injectivity observation (citing Correll & Swanson 2023, whose positive-first-differences result is the published antecedent), and the explicit transition-fraction stability assumption — now supportable by citing Warnke–Correll–Swanson 2023 (exponential density decay) as the reason the orders-12–16 extrapolation needs the orders-18–20 check. The Dumitru–Budala involution collision model is directly relevant to the symmetric-campaign modeling.
