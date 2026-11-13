namespace Costas32

/-- Injectivity of realised fixed-lag differences implies duplicate-freeness of
    their list. This isolates the exact consequence of the Costas property used
    by the T_m certificate. -/
theorem fixed_lag_values_nodup
    (row : Nat → Int) (m : Nat) :
    ∀ starts : List Nat,
      starts.Nodup →
      (∀ i ∈ starts, ∀ j ∈ starts,
        row (i + m) - row i = row (j + m) - row j → i = j) →
      (starts.map (fun i => row (i + m) - row i)).Nodup
  | [], _, _ => by simp
  | i :: starts, hstarts, hinj => by
      have hi : i ∉ starts := (List.nodup_cons.1 hstarts).1
      have ht : starts.Nodup := (List.nodup_cons.1 hstarts).2
      apply List.nodup_cons.2
      constructor
      · intro hmem
        obtain ⟨j, hj, heq⟩ := List.mem_map.1 hmem
        have hij : i = j := hinj i (by simp) j (by simp [hj]) heq.symm
        exact hi (hij ▸ hj)
      · apply fixed_lag_values_nodup row m starts ht
        intro a ha b hb heq
        exact hinj a (by simp [ha]) b (by simp [hb]) heq

end Costas32
