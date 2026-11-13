import Costas32.TmAssembly
import Costas32.DomainPoolSimple
namespace Costas32

/-!
# The representation boundary

`tm_assembly_sound` is proved for any value of `TmAssemblyData`. What is *not*
proved is that `f3_complete.cpp` builds one. This module makes that boundary an
object rather than a paragraph: the parts expressible as mathematics are proved
here, and the parts that are claims *about C++ text* are listed as explicit
fields of `CppObligations`, each tied to the construct it refers to.

Nothing below weakens `tm_assembly_sound`. It states precisely what must be
supplied to instantiate it from the executable.
-/

/-! ## Proved: the bitmask/list bridge

The executable stores position domains as `unsigned D[u]`, bit `k` meaning "the
`k`-th remaining value is still available at position `u`". The Lean development
uses lists of indices. These are the same thing. -/

/-- The list of indices a `K`-bit mask selects. -/
def domainList (mask K : Nat) : List Nat :=
  (List.range K).filter (fun k => mask.testBit k)

theorem mem_domainList {mask K k : Nat} :
    k ∈ domainList mask K ↔ k < K ∧ mask.testBit k := by
  simp [domainList, List.mem_filter, List.mem_range]

theorem mem_domainList_of {mask K k : Nat} (hk : k < K) (hb : mask.testBit k) :
    k ∈ domainList mask K := mem_domainList.2 ⟨hk, hb⟩

/-- Values selected by a mask, under the remaining-row lookup `row`. -/
def domainValues (row : Nat → Int) (mask K : Nat) : List Int :=
  (domainList mask K).map row

theorem mem_domainValues {row : Nat → Int} {mask K k : Nat}
    (hk : k < K) (hb : mask.testBit k) :
    row k ∈ domainValues row mask K :=
  List.mem_map.2 ⟨k, mem_domainList_of hk hb, rfl⟩

/-- Filtering only ever shrinks a domain. Every step of `l3Detect` replaces a
    mask by a submask (`D[u] &= ~(1u << k)`), so any index surviving the filtered
    mask survived the original. This is what lets pool membership proved against
    the *filtered* domains be read back as membership in the original. -/
theorem mem_domainList_of_submask {mask mask' K k : Nat}
    (hsub : mask' &&& mask = mask') (h : k ∈ domainList mask' K) :
    k ∈ domainList mask K := by
  rw [mem_domainList] at h ⊢
  refine ⟨h.1, ?_⟩
  have hb : mask'.testBit k = true := h.2
  rw [← hsub, Nat.testBit_and] at hb
  simp at hb
  exact hb.2

/-! ## Not proved: obligations on the C++ text

Each field is a claim about `f3_complete.cpp` that no Lean proof here discharges.
They are the complete residue between `tm_assembly_sound` and a verified
implementation. -/

structure CppObligations where
  /-- `l3Detect` only ever clears a bit for a value that no completion can take.
      This is *soundness of the domain filter* and is the deepest obligation:
      unary filtering, arc consistency and singleton shaving must each remove
      only unsupported values. -/
  domains_sound : Prop
  /-- The `for (int i = 0; i + m < n; i++)` loop in `tmDetect` visits each
      unresolved lag-`m` pair exactly once, and the `a < s` test classifies it as
      fixed-to-free or free-to-free correctly. -/
  pairs_enumerated : Prop
  /-- The two `pool.push_back` branches generate exactly `fixedFreePoolFn` and
      `freeFreePoolFn`, including the `l != k` guard. -/
  pools_match : Prop
  /-- `sort(pool); pool.erase(unique(...))` has the same membership as
      `dedupInt`, and yields an ascending list. -/
  dedup_matches : Prop
  /-- `pre_lo[k]` and `pre_hi[k]` are the sums of the `k` smallest and `k`
      largest remaining values, i.e. `lowerK` and `upperKFromNeg` of the sorted
      remaining-row list. -/
  prefix_sums_extremal : Prop
  /-- `slo`, `shi`, `tlo`, `thi` equal the Lean interval endpoints, and the final
      `if (shi < tlo || slo > thi)` is exactly interval disjointness. -/
  endpoints_match : Prop
  /-- `fk`, `fR`, `lk`, `lR` are the true cardinalities of the first-`m` and
      last-`m` windows, so `exact_balance` holds with the telescoping identity. -/
  cardinalities_correct : Prop
  /-- No `long long` accumulation overflows at the supported orders. All sums are
      bounded by `n * n`, so this is a range check, not a deep property. -/
  no_overflow : Prop

/-- Given every obligation, the executable's positive verdict is sound. The
    implication is trivial by design: all the mathematics lives in
    `tm_assembly_sound`, and this states that the only remaining risk is
    representational. The obligations argument is deliberately unused: it carries
    no mathematical content, and that is the point --- every obligation is a
    claim about C++ text, outside what Lean can see. -/
theorem cpp_sound_given_obligations {C : Type}
    (_O : CppObligations) (A : TmAssemblyData C)
    (hdisjoint :
      stateLagHi A.toState < A.endpointLoValue ∨
      A.endpointHiValue < stateLagLo A.toState) :
    C → False :=
  tm_assembly_sound A hdisjoint

end Costas32
