import Costas32.PoolBounds

namespace Costas32

/-- Sound data for selecting distinct remaining row values. The lower and upper
    pools may be represented independently, matching the fail-closed C++
    implementation and avoiding any assumption that one was computed by
    reversing the other. -/
structure RowSelection where
  lowerPool : List Int
  upperNegPool : List Int
  chosen : List Int
  lowerSorted : lowerPool.Pairwise (· ≤ ·)
  upperNegSorted : upperNegPool.Pairwise (· ≤ ·)
  chosenNodup : chosen.Nodup
  chosenMemLower : ∀ x ∈ chosen, x ∈ lowerPool
  chosenNegMemUpper : ∀ x ∈ chosen, -x ∈ upperNegPool

/-- Convert row-selection data to the generic extremal interface. -/
def RowSelection.toExtremal (R : RowSelection) : ExtremalSelection where
  lowerPool := R.lowerPool
  upperNegPool := R.upperNegPool
  selected := R.chosen
  lower_sorted := R.lowerSorted
  upperNeg_sorted := R.upperNegSorted
  selected_nodup := R.chosenNodup
  selected_mem_lower := R.chosenMemLower
  selected_neg_mem_upper := R.chosenNegMemUpper

/-- Bounds for `fixed + positive rows - negative rows`. The two row selections
    are bounded separately. This matches the endpoint-side arithmetic of `T_m`
    without assuming that the signed contributions themselves are distinct. -/
theorem signed_endpoint_between
    (fixed : Int) (positive negative : RowSelection) :
    fixed
        + lowerK positive.lowerPool positive.chosen.length
        - upperKFromNeg negative.upperNegPool negative.chosen.length
      ≤ fixed + positive.chosen.sum - negative.chosen.sum ∧
    fixed + positive.chosen.sum - negative.chosen.sum
      ≤ fixed
        + upperKFromNeg positive.upperNegPool positive.chosen.length
        - lowerK negative.lowerPool negative.chosen.length := by
  have hp := selection_between positive.toExtremal
  have hn := selection_between negative.toExtremal
  simp only [RowSelection.toExtremal] at hp hn
  obtain ⟨hp1, hp2⟩ := hp
  obtain ⟨hn1, hn2⟩ := hn
  simp only [lowerK, upperKFromNeg]
  omega

/-- Fixed-cardinality form used by a completion-independent endpoint interval. -/
theorem signed_endpoint_fixed_card
    (fixed : Int) (positive negative : RowSelection)
    (kp kn : Nat)
    (hp : positive.chosen.length = kp)
    (hn : negative.chosen.length = kn) :
    fixed + lowerK positive.lowerPool kp
        - upperKFromNeg negative.upperNegPool kn
      ≤ fixed + positive.chosen.sum - negative.chosen.sum ∧
    fixed + positive.chosen.sum - negative.chosen.sum
      ≤ fixed + upperKFromNeg positive.upperNegPool kp
        - lowerK negative.lowerPool kn := by
  subst kp
  subst kn
  exact signed_endpoint_between fixed positive negative

end Costas32
