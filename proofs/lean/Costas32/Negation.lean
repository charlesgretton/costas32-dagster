import Costas32.Extremal
namespace Costas32

theorem sum_map_neg : ∀ xs : List Int,
    (xs.map (fun x => -x)).sum = -xs.sum
  | [] => by simp
  | x :: xs => by
      simp only [List.map_cons, List.sum_cons, sum_map_neg xs]
      omega

/-- `Function.Injective` and `neg_injective` are Mathlib; membership under
    negation is proved directly instead. -/
theorem mem_map_neg {x : Int} {xs : List Int} :
    -x ∈ xs.map (fun y => -y) ↔ x ∈ xs := by
  constructor
  · intro h
    obtain ⟨y, hy, hxy⟩ := List.mem_map.1 h
    have : y = x := by omega
    exact this ▸ hy
  · intro h
    exact List.mem_map.2 ⟨x, h, rfl⟩

theorem nodup_map_neg : ∀ {xs : List Int}, xs.Nodup →
    (xs.map (fun x => -x)).Nodup
  | [], _ => by simp
  | x :: xs, h => by
      have hx : x ∉ xs := (List.nodup_cons.1 h).1
      have hxs : xs.Nodup := (List.nodup_cons.1 h).2
      simp only [List.map_cons]
      refine List.nodup_cons.2 ⟨?_, nodup_map_neg hxs⟩
      intro hmem
      exact hx (mem_map_neg.1 hmem)

end Costas32
