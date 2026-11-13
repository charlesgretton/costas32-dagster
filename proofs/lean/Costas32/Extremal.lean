namespace Costas32
/-- `List.Perm.sum_eq` is Mathlib-only; this is the instance we need, by induction. -/
theorem sum_erase_mem : ∀ (S : List Int) (u : Int), u ∈ S → S.sum = u + (S.erase u).sum
  | a :: S, u, h => by
      by_cases hau : a = u
      · subst hau; simp
      · have hmem : u ∈ S := by
          cases List.mem_cons.1 h with
          | inl h' => exact absurd h'.symm hau
          | inr h' => exact h'
        have he : (a :: S).erase u = a :: S.erase u := by
          simp [List.erase_cons, hau]
        rw [he, List.sum_cons, List.sum_cons, sum_erase_mem S u hmem]
        omega

/-- Pigeonhole: a duplicate-free list contained in another is no longer. -/
theorem nodup_length_le : ∀ (S U : List Int), S.Nodup → (∀ x ∈ S, x ∈ U) → S.length ≤ U.length
  | [], _, _, _ => Nat.zero_le _
  | a :: S, U, hS, hsub => by
      have ha : a ∈ U := hsub a (by simp)
      have hS' : S.Nodup := hS.of_cons
      have hna : a ∉ S := by
        intro h; exact (List.nodup_cons.1 hS).1 h
      have hsub' : ∀ x ∈ S, x ∈ U.erase a := by
        intro x hx
        have hxU : x ∈ U := hsub x (by simp [hx])
        have hxa : x ≠ a := by intro h; exact hna (h ▸ hx)
        exact (List.mem_erase_of_ne hxa).2 hxU
      have ih := nodup_length_le S (U.erase a) hS' hsub'
      have hpos : 0 < U.length := List.length_pos_of_mem ha
      have hlen : (U.erase a).length + 1 = U.length := by
        rw [List.length_erase_of_mem ha]; omega
      simp only [List.length_cons]; omega

/-- Swapping a new minimum into a prefix cannot raise its sum: if `u` is below
    every element of `l`, then `u + (l.take k).sum ≤ (l.take (k+1)).sum`. -/
theorem take_succ_sum_ge : ∀ (l : List Int) (k : Nat), k < l.length →
    ∀ u : Int, (∀ y ∈ l, u ≤ y) → u + (l.take k).sum ≤ (l.take (k+1)).sum
  | a :: l', 0, _, u, hle => by
      have : u ≤ a := hle a (by simp)
      simp; omega
  | a :: l', k+1, hk, u, hle => by
      have hk' : k < l'.length := by simp at hk; omega
      have hle' : ∀ y ∈ l', u ≤ y := fun y hy => hle y (by simp [hy])
      have ih := take_succ_sum_ge l' k hk' u hle'
      simp only [List.take_succ_cons, List.sum_cons]
      omega

/-- **The extremal lemma.** If `U` is sorted ascending and `S` is a duplicate-free
    sublist-by-membership of `U`, then the sum of the `|S|` smallest elements of
    `U` is at most the sum of `S`. This is the outer bound the `T_m` rule needs on
    the difference side. -/
theorem take_sum_le : ∀ (U : List Int), U.Pairwise (· ≤ ·) →
    ∀ S : List Int, S.Nodup → (∀ x ∈ S, x ∈ U) →
    (U.take S.length).sum ≤ S.sum
  | [], _, S, _, hsub => by
      have : S = [] := by
        cases S with
        | nil => rfl
        | cons a _ => exact absurd (hsub a (by simp)) (by simp)
      subst this; simp
  | u :: U', hU, S, hS, hsub => by
      have hU' : U'.Pairwise (· ≤ ·) := (List.pairwise_cons.1 hU).2
      have hle : ∀ y ∈ U', u ≤ y := (List.pairwise_cons.1 hU).1
      by_cases hu : u ∈ S
      · -- u is used: peel it off both sides
        have hSe : S.erase u |>.Nodup := hS.erase u
        have hsube : ∀ x ∈ S.erase u, x ∈ U' := by
          intro x hx
          have hxS : x ∈ S := List.mem_of_mem_erase hx
          have hxne : x ≠ u := by
            intro h; subst h
            exact (List.nodup_cons.1 ((List.perm_cons_erase hu).nodup_iff.1 hS)).1 hx
          have := hsub x hxS
          cases List.mem_cons.1 this with
          | inl h => exact absurd h hxne
          | inr h => exact h
        have ih := take_sum_le U' hU' (S.erase u) hSe hsube
        have hlen : S.length = (S.erase u).length + 1 := by
          rw [List.length_erase_of_mem hu]
          have : 0 < S.length := List.length_pos_of_mem hu
          omega
        have hsum : S.sum = u + (S.erase u).sum := sum_erase_mem S u hu
        rw [hlen, hsum]
        show u + (U'.take (S.erase u).length).sum ≤ u + (S.erase u).sum
        omega
      · -- u is unused: S lives entirely in U', and u is below everything there
        have hsub' : ∀ x ∈ S, x ∈ U' := by
          intro x hx
          cases List.mem_cons.1 (hsub x hx) with
          | inl h => exact absurd (h ▸ hx) hu
          | inr h => exact h
        have ih := take_sum_le U' hU' S hS hsub'
        have hk : S.length ≤ U'.length := nodup_length_le S U' hS hsub'
        -- (u :: U').take k  vs  U'.take k : swap u in for the k-th element
        have key : ((u :: U').take S.length).sum ≤ (U'.take S.length).sum := by
          cases hS0 : S.length with
          | zero => simp
          | succ k =>
              have hk' : k < U'.length := by omega
              have h2 := take_succ_sum_ge U' k hk' u hle
              simp only [List.take_succ_cons, List.sum_cons]
              omega
        omega
end Costas32
