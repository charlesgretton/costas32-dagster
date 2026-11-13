import Costas32.Core
import Costas32.ExtremalInterval

namespace Costas32

/-- Sum of the first `k` values of a sorted pool. -/
def lowerK (pool : List Int) (k : Nat) : Int :=
  (pool.take k).sum

/-- An upper bound represented by a sorted list of negated admissible values. -/
def upperKFromNeg (negPool : List Int) (k : Nat) : Int :=
  -(negPool.take k).sum

/-- Adding a fixed contribution preserves the extremal interval. -/
theorem fixed_plus_selection_between
    (fixed : Int) (E : ExtremalSelection) :
    fixed + lowerK E.lowerPool E.selected.length
        ≤ fixed + E.selected.sum ∧
      fixed + E.selected.sum
        ≤ fixed + upperKFromNeg E.upperNegPool E.selected.length := by
  have h := selection_between E
  constructor <;> simp only [lowerK, upperKFromNeg] <;> omega

/-- If two selections have the same length, their common pool bounds use the
    same cardinality. This is the small rewriting lemma repeatedly needed when
    moving from completion-dependent lists to completion-independent interval
    endpoints. -/
theorem fixed_card_selection_between
    (fixed : Int) (E : ExtremalSelection) (k : Nat)
    (hk : E.selected.length = k) :
    fixed + lowerK E.lowerPool k ≤ fixed + E.selected.sum ∧
      fixed + E.selected.sum ≤ fixed + upperKFromNeg E.upperNegPool k := by
  subst k
  exact fixed_plus_selection_between fixed E

end Costas32
