# Lean proofs

**These typecheck.** Lean 4.15.0, **no Mathlib**, no `sorry`, no `native_decide`.
18 modules, ~100 declarations. Axioms are limited to `propext`, `Quot.sound` and
`Classical.choice` — all part of Lean's standard trusted base.

```sh
export PATH=/path/to/lean-4.15.0-linux/bin:$PATH
./check.sh          # typechecks all 15 modules, then audits axioms
```

Avoiding Mathlib is deliberate: everything is over core `List`/`Int` rather than
`Finset`, so the development checks in seconds from a bare toolchain with no
dependency resolution.

## The chain

```
Core              telescoping identity, T_m = T_(n-m), abstract interval soundness
Extremal          lower subset-sum bound (k smallest)
Negation          negation/map lemmas
ExtremalInterval  two-sided selection bounds
Dedup             duplicate removal preserves membership
FixedLag          Costas property => fixed-lag differences are distinct
DomainPoolSimple  fixed-to-free and free-to-free pool membership
TmCertificate     certificate-level interval soundness
PoolBounds        pool-level bounds
EndpointBounds    signed positive-minus-negative endpoint bounds
LagAggregate      aggregation across all unresolved lag pairs
TelescopeBridge   telescoping identity supplies the balance obligation
ConcreteTm        state-level interval soundness
CompletionModel   prefix-completion model, distinctness of row choices
TmAssembly        assembled soundness theorem
Representation    bitmask/list bridge (proved) + obligation scaffolding
Reference         Lean reference implementation; discharges five of eight obligations
DomainSound       soundness of unary filtering, arc consistency and shaving
```

Top-level: `tm_assembly_sound` — if the lag-side and endpoint-side intervals
built from sound domain pools are disjoint, no completion exists.

## The representation boundary

`Representation.lean` turns the gap between the proved contracts and
`f3_complete.cpp` into an object rather than a paragraph.

**Proved there:** the bitmask/list bridge. `domainList mask K` is the list of
indices a mask selects, `mem_domainList` characterises membership exactly, and
`mem_domainList_of_submask` shows that every filtering step (`D[u] &= ~(1u<<k)`
produces a submask) only shrinks a domain — so pool membership proved against the
*filtered* domains reads back as membership in the original.

**Reduced from eight obligations to two.** `Reference.lean` gives a Lean
reference implementation of what `tmDetect` computes and *proves* the shallow
obligations against it, rather than leaving them as opaque `Prop` fields. An
opaque `Prop` is unfalsifiable — it can neither be proved nor refuted, and a
differential harness can only ever refute. Discharged as theorems:

| was an obligation | now |
|---|---|
| `pools_match` | `ref_fixedFree_eq`, `ref_freeFree_eq` — `rfl`, no axioms |
| `dedup_matches` | `ref_dedup_preserves`, `ref_dedup_nodup` |
| `prefix_sums_extremal` | `ref_lower_eq` — `rfl`, no axioms |
| `endpoints_match` | `ref_disjoint_iff` |
| `no_overflow` | `ref_sum_bounded`: a list bounded by `n` has sum bounded by `length * n`, so all accumulations are `O(n²)` |
| `pairs_enumerated`, `cardinalities_correct` | absorbed into `cpp_matches_reference` |

**`domains_sound` is now proved too** (`DomainSound.lean`), so `CppResidue` has
**one** field. The argument turns on a single invariant: a domain family is
*sound* when every admissible assignment lies inside it.

| theorem | content | axioms |
|---|---|---|
| `sound_erase` | **the pruning principle** — removing a value no admissible assignment takes preserves soundness | standard |
| `no_adm_of_empty` | **the wipeout principle** — a sound family with an empty domain refutes | **none** |
| `unary_sound` | the `dmask` clash test removes only impossible values | **none** |
| `arc_sound` | if every surviving value at `w` clashes with `r` at `u`, no completion puts `r` at `u` | **none** |
| `shave_sound` | pinning `u` to `r` and wiping out refutes `r` at `u` | **none** |
| `filter_pipeline_sound` | any sequence of the three leaves a sound family | standard |

Four of the six depend on **no axioms at all**. This upgrades the result from
*the T_m rule is sound given sound domains* to *the L3+T_m inference pipeline is
mathematically sound*.

The single remaining field is `cpp_matches_reference` — one refinement claim
about straight-line code, and the only place a differential harness is the right
instrument, since there refutation is the useful outcome.

## What this does and does not establish

It establishes the **abstract** soundness of the `T_m` interval rule: given the
membership, distinctness and telescoping-balance contracts, disjointness excludes
every completion.

It does **not** yet prove that `f3_complete.cpp` constructs a value satisfying
those contracts. That is implementation correspondence — bitmask membership
equals list membership, the nested loops enumerate the mathematical pools,
sort/unique matches `dedupInt`, `lo[k]`/`hi[k]` equal the extremal row sums, and
no integer overflows at supported orders. That is the remaining gap, and it is a
refinement question rather than a hole in the abstract argument.

`DomainPool.lean` (the executable-shaped model using `List.getElem?`) is **not**
included: it fails to typecheck at 4.15.0 on optional-indexing API names. The
theorem-name-light `DomainPoolSimple.lean` is the active target.

## Provenance of the fixes

The drafts had never been typechecked. Six defects were found and repaired:
`Function.Injective`/`neg_injective` are Mathlib (replaced by a direct
`mem_map_neg`); `Dedup` recursion through `simp` left unsolved goals (rewritten
with explicit `rw`); two `let`-bound structure literals whose projections never
reduced (inlined, with `dsimp only`); `List.mem_map` orientation in
`LagAggregate` plus a missing `revert` before induction; and two `apply
tm_interval_sound` calls that left the interval endpoints as metavariables
(pinned with named arguments).
