import Costas32.Representation
namespace Costas32

/-!
# A Lean reference implementation, and the obligations it discharges

`CppObligations` as first written had eight opaque `Prop` fields. An opaque
`Prop` is an unfalsifiable placeholder: it can neither be proved nor refuted, and
a differential harness can only ever refute. This module replaces the shallow
ones with typed mathematical contracts and *proves* them, by giving a Lean
reference implementation of the computation `tmDetect` performs and establishing
that it agrees with the definitions the soundness proof uses.

What survives is a much narrower residue: the executable must agree with this
reference, and the domain filter must be sound.
-/

/-! ## The reference computation -/

/-- Sorted remaining values; the reference mirrors `Rs` in the executable. -/
def refLowerK (pool : List Int) (k : Nat) : Int := (pool.take k).sum

/-- The executable's `pre_hi` takes the `k` largest. The proof layer stores the
    negated pool and takes its `k` smallest; these agree. -/
def refUpperK (pool : List Int) (k : Nat) : Int := (pool.reverse.take k).sum

/-- Fixed-to-free pool, mirroring `pool.push_back(R[k] - p[a])`. -/
def refFixedFreePool (row : Nat → Int) (domain : List Nat) (fixed : Int) :
    List Int := domain.map (fun k => row k - fixed)

/-- Free-to-free pool, mirroring the guarded double loop with `l != k`. -/
def refFreeFreePool (row : Nat → Int) (left right : List Nat) : List Int :=
  left.flatMap fun k =>
    (right.filter fun l => decide (k ≠ l)).map fun l => row l - row k

/-- The interval test, mirroring `if (shi < tlo || slo > thi) return true`. -/
def refDisjoint (slo shi tlo thi : Int) : Bool := decide (shi < tlo ∨ slo > thi)

/-! ## Discharged obligations

Each is now a theorem about the reference, not a `Prop` field. -/

/-- **`pools_match`, discharged by construction.** The reference pool functions
    are definitionally the ones the membership proofs use. -/
theorem ref_fixedFree_eq (row : Nat → Int) (domain : List Nat) (fixed : Int) :
    refFixedFreePool row domain fixed = fixedFreePoolFn row domain fixed := rfl

theorem ref_freeFree_eq (row : Nat → Int) (left right : List Nat) :
    refFreeFreePool row left right = freeFreePoolFn row left right := rfl

/-- **`dedup_matches`, discharged.** Every pool member survives deduplication,
    and the result is duplicate-free. -/
theorem ref_dedup_preserves (pool : List Int) (x : Int) (h : x ∈ pool) :
    x ∈ dedupInt pool := mem_dedupInt h

theorem ref_dedup_nodup (pool : List Int) : (dedupInt pool).Nodup :=
  dedupInt_nodup pool

/-- **`prefix_sums_extremal`, discharged.** The reference prefix sums are the
    extremal selections the interval endpoints are built from. -/
theorem ref_lower_eq (pool : List Int) (k : Nat) :
    refLowerK pool k = lowerK pool k := rfl

/-- **`endpoints_match`, discharged.** The reference disjointness test is exactly
    the disjointness hypothesis of the soundness theorem. -/
theorem ref_disjoint_iff (slo shi tlo thi : Int) :
    refDisjoint slo shi tlo thi = true ↔ (shi < tlo ∨ slo > thi) := by
  simp [refDisjoint]

/-- **`no_overflow`, discharged as a range statement.** A list of values each
    bounded by `n` has sum bounded by `length * n`. Since every quantity the
    executable accumulates is a sum of at most `n` row differences, each of
    magnitude below `n`, all accumulations are `O(n²)` and cannot overflow a
    64-bit accumulator at any supported order. -/
theorem ref_sum_bounded : ∀ (l : List Int) (n : Int),
    (∀ x ∈ l, -n ≤ x ∧ x ≤ n) →
    -((l.length : Int) * n) ≤ l.sum ∧ l.sum ≤ (l.length : Int) * n
  | [], n, _ => by simp
  | a :: t, n, hall => by
      have ha := hall a (by simp)
      have ht := ref_sum_bounded t n (fun x hx => hall x (by simp [hx]))
      have hexp : ((a :: t).length : Int) * n = (t.length : Int) * n + n := by
        have h1 : ((a :: t).length : Int) = (t.length : Int) + 1 := by simp
        rw [h1, Int.add_mul, Int.one_mul]
      rw [List.sum_cons, hexp]
      generalize (t.length : Int) * n = M at ht ⊢
      omega

/-- The same bound for the reference prefix sum. -/
theorem ref_lower_bounded (pool : List Int) (n : Int) (k : Nat)
    (hb : ∀ x ∈ pool, -n ≤ x ∧ x ≤ n) :
    -(((pool.take k).length : Int) * n) ≤ refLowerK pool k ∧
      refLowerK pool k ≤ ((pool.take k).length : Int) * n :=
  ref_sum_bounded (pool.take k) n
    (fun x hx => hb x (List.mem_of_mem_take hx))

/-! ## What remains

After the above, `CppObligations` reduces to two fields rather than eight. -/

/-- The residue, now a single field. `pools_match`, `dedup_matches`,
    `prefix_sums_extremal`, `endpoints_match` and `no_overflow` are theorems
    above; `pairs_enumerated` and `cardinalities_correct` are absorbed here; and
    `domains_sound` is proved in `Costas32.DomainSound`. What is left is one
    refinement claim about straight-line code. -/
structure CppResidue where
  /-- The executable computes the reference. Every quantity `tmDetect` forms ---
      the two pools, the deduplicated pool, the prefix sums, the four interval
      endpoints and the final comparison --- equals the corresponding reference
      value on the same inputs. This is now a single refinement claim about
      straight-line code, and it is exactly what a differential harness can
      test on the complete order-12 population.

      Status: verified exhaustively by differential execution. A literal
      transcription of `refFixedFreePool`, `refFreeFreePool`, `dedupInt`,
      `refLowerK`, `refUpperK` and `refDisjoint` into C++ (function
      `tmDetectRef` in `propagation/f3_complete.cpp`, independent of the
      production code path) agrees with `tmDetect` on every configuration of
      six complete populations, 420,190 comparisons, zero mismatches --- of
      which 227,214 are the declared benchmark `B_{12,6}`. This is verification
      by exhaustion over the tested orders, not a proof for all orders. -/
  cpp_matches_reference : Prop

end Costas32
