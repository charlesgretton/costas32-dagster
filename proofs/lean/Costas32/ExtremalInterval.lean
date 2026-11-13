import Costas32.Negation
namespace Costas32

/-- Lower and negated-upper pools for one realised duplicate-free selection. -/
structure ExtremalSelection where
  lowerPool : List Int
  upperNegPool : List Int
  selected : List Int
  lower_sorted : lowerPool.Pairwise (· ≤ ·)
  upperNeg_sorted : upperNegPool.Pairwise (· ≤ ·)
  selected_nodup : selected.Nodup
  selected_mem_lower : ∀ x ∈ selected, x ∈ lowerPool
  selected_neg_mem_upper : ∀ x ∈ selected, -x ∈ upperNegPool

theorem selection_lower (E : ExtremalSelection) :
    (E.lowerPool.take E.selected.length).sum ≤ E.selected.sum := by
  exact take_sum_le E.lowerPool E.lower_sorted E.selected
    E.selected_nodup E.selected_mem_lower

theorem selection_upper (E : ExtremalSelection) :
    E.selected.sum ≤ -(E.upperNegPool.take E.selected.length).sum := by
  have hn : (E.selected.map (fun x => -x)).Nodup :=
    nodup_map_neg E.selected_nodup
  have hm : ∀ x ∈ E.selected.map (fun x => -x), x ∈ E.upperNegPool := by
    intro x hx
    obtain ⟨y, hy, hxy⟩ := List.mem_map.1 hx
    subst x
    exact E.selected_neg_mem_upper y hy
  have h := take_sum_le E.upperNegPool E.upperNeg_sorted
    (E.selected.map (fun x => -x)) hn hm
  rw [List.length_map, sum_map_neg] at h
  omega

theorem selection_between (E : ExtremalSelection) :
    (E.lowerPool.take E.selected.length).sum ≤ E.selected.sum ∧
      E.selected.sum ≤ -(E.upperNegPool.take E.selected.length).sum := by
  exact ⟨selection_lower E, selection_upper E⟩

end Costas32
