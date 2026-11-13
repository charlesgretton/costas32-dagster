import Costas32.DomainPoolSimple
import Costas32.Dedup
import Costas32.FixedLag

namespace Costas32

/-!
# Aggregating unresolved lag pairs

Each unresolved pair contributes one realised difference and one mathematical
candidate pool. Soundness is pointwise membership; aggregation and executable
pool deduplication preserve it.
-/

/-- One unresolved lag pair, abstracting over fixed-to-free and free-to-free
    construction after their branch-specific membership lemmas have fired. -/
structure LagPairRealisation (Completion : Type) where
  pool : List Int
  realised : Completion → Int
  realised_mem : ∀ σ, realised σ ∈ pool

/-- Concatenation of all pair pools. -/
def aggregateLagPool {C : Type} (pairs : List (LagPairRealisation C)) : List Int :=
  pairs.flatMap LagPairRealisation.pool

/-- Realised lag differences, one per unresolved pair. -/
def aggregateLagValues {C : Type}
    (pairs : List (LagPairRealisation C)) (σ : C) : List Int :=
  pairs.map fun p => p.realised σ

/-- Every realised unresolved difference occurs in the aggregate pool. -/
theorem aggregate_lag_mem
    {C : Type} (pairs : List (LagPairRealisation C)) (σ : C) :
    ∀ d ∈ aggregateLagValues pairs σ, d ∈ aggregateLagPool pairs := by
  intro d hd
  obtain ⟨p, hp, rfl⟩ := List.mem_map.1 hd
  apply List.mem_flatMap.2
  exact ⟨p, hp, p.realised_mem σ⟩

/-- Membership remains true after the executable-style duplicate removal. -/
theorem aggregate_lag_mem_dedup
    {C : Type} (pairs : List (LagPairRealisation C)) (σ : C) :
    ∀ d ∈ aggregateLagValues pairs σ,
      d ∈ dedupInt (aggregateLagPool pairs) := by
  intro d hd
  exact mem_dedupInt (aggregate_lag_mem pairs σ d hd)

/-- Mapping preserves the number of unresolved pairs. -/
theorem aggregate_lag_length
    {C : Type} (pairs : List (LagPairRealisation C)) (σ : C) :
    (aggregateLagValues pairs σ).length = pairs.length := by
  simp [aggregateLagValues]

/-- If realised fixed-lag values are injective over pair positions, the
    aggregate realised list is duplicate-free. -/
theorem aggregate_lag_nodup_of_injective
    {C : Type} (pairs : List (LagPairRealisation C)) (σ : C)
    (hinj : ∀ p ∈ pairs, ∀ q ∈ pairs,
      p.realised σ = q.realised σ → p = q)
    (hpairs : pairs.Nodup) :
    (aggregateLagValues pairs σ).Nodup := by
  revert hinj hpairs
  induction pairs with
  | nil => intro _ _; simp [aggregateLagValues]
  | cons p ps ih =>
      intro hinj hpairs
      have hp : p ∉ ps := (List.nodup_cons.1 hpairs).1
      have hps : ps.Nodup := (List.nodup_cons.1 hpairs).2
      simp only [aggregateLagValues, List.map_cons]
      refine List.nodup_cons.2 ⟨?_, ?_⟩
      · intro hm
        obtain ⟨q, hq, heq⟩ := List.mem_map.1 hm
        have hpq : p = q := hinj p (by simp) q (by simp [hq]) heq.symm
        exact hp (hpq ▸ hq)
      · exact ih (fun a ha b hb hab => hinj a (by simp [ha]) b (by simp [hb]) hab) hps

end Costas32
