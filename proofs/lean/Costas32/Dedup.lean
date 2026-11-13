namespace Costas32

/-!
# Duplicate removal and membership

A small core-Lean replacement for the executable's
`sort(pool); erase(unique(...))`. Only membership preservation is needed for
soundness. Ordering is handled separately by the certificate constructor.
-/

/-- Remove later duplicate integers, retaining one representative. -/
def dedupInt : List Int → List Int
  | [] => []
  | x :: xs =>
      if x ∈ xs then dedupInt xs else x :: dedupInt xs

/-- Duplicate removal preserves and reflects membership. -/
theorem mem_dedupInt_iff : ∀ (xs : List Int) (x : Int), x ∈ dedupInt xs ↔ x ∈ xs
  | [], x => by simp [dedupInt]
  | y :: ys, x => by
      by_cases hy : y ∈ ys
      · have he : dedupInt (y :: ys) = dedupInt ys := by simp [dedupInt, hy]
        rw [he, mem_dedupInt_iff ys x]
        constructor
        · intro h; exact List.mem_cons.2 (Or.inr h)
        · intro h
          cases List.mem_cons.1 h with
          | inl he' => exact he' ▸ hy
          | inr h' => exact h'
      · have he : dedupInt (y :: ys) = y :: dedupInt ys := by simp [dedupInt, hy]
        rw [he, List.mem_cons, List.mem_cons, mem_dedupInt_iff ys x]

/-- Every source member survives duplicate removal. -/
theorem mem_dedupInt {x : Int} {xs : List Int} (h : x ∈ xs) :
    x ∈ dedupInt xs := (mem_dedupInt_iff xs x).2 h

/-- The result of duplicate removal is duplicate-free. -/
theorem dedupInt_nodup : ∀ xs : List Int, (dedupInt xs).Nodup
  | [] => by simp [dedupInt]
  | x :: xs => by
      by_cases hx : x ∈ xs
      · have he : dedupInt (x :: xs) = dedupInt xs := by simp [dedupInt, hx]
        rw [he]; exact dedupInt_nodup xs
      · have he : dedupInt (x :: xs) = x :: dedupInt xs := by simp [dedupInt, hx]
        rw [he]
        refine List.nodup_cons.2 ⟨?_, dedupInt_nodup xs⟩
        intro h
        exact hx ((mem_dedupInt_iff xs x).1 h)

end Costas32
