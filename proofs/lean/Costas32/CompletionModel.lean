import Costas32.ConcreteTm
import Costas32.LagAggregate

namespace Costas32

/-!
# Completion model for a leading-column search state

This layer records the exact mathematical obligations supplied by a genuine
Costas completion. It does not expose bit-level implementation details.
-/

/-- A completion assigns a remaining-row index to every free column. -/
structure PrefixCompletion (freeColumns remainingRows : Nat) where
  rowIndex : Nat → Nat
  columnInRange : ∀ c, c < freeColumns → rowIndex c < remainingRows
  injectiveOnFree : ∀ a b,
    a < freeColumns → b < freeColumns → rowIndex a = rowIndex b → a = b

/-- Domain soundness: every selected row index is admitted by its position
    domain. -/
def DomainsSound {C : Type} (chosen : C → Nat → Nat)
    (domains : Nat → List Nat) : Prop :=
  ∀ σ c, chosen σ c ∈ domains c

/-- Distinct free columns choose distinct remaining-row indices. -/
theorem chosen_indices_distinct
    {fc rr : Nat} (σ : PrefixCompletion fc rr)
    {a b : Nat} (ha : a < fc) (hb : b < fc) (hab : a ≠ b) :
    σ.rowIndex a ≠ σ.rowIndex b := by
  intro h
  exact hab (σ.injectiveOnFree a b ha hb h)

/-- Fixed-to-free branch instantiated from a sound domain. -/
theorem completion_fixed_free_pool
    {C : Type} (row : C → Nat → Int)
    (domains : Nat → List Nat) (chosen : C → Nat → Nat)
    (hsound : DomainsSound chosen domains)
    (σ : C) (column : Nat) (fixed : Int) :
    row σ (chosen σ column) - fixed ∈
      fixedFreePoolFn (row σ) (domains column) fixed := by
  exact fixed_free_mem_pool_fn (row σ) (domains column) fixed
    (chosen σ column) (hsound σ column)

/-- Free-to-free branch instantiated from two sound position domains. -/
theorem completion_free_free_pool
    {C : Type} (row : C → Nat → Int)
    (domains : Nat → List Nat) (chosen : C → Nat → Nat)
    (hsound : DomainsSound chosen domains)
    (distinct : ∀ σ a b, a ≠ b → chosen σ a ≠ chosen σ b)
    (σ : C) (a b : Nat) (hab : a ≠ b) :
    row σ (chosen σ b) - row σ (chosen σ a) ∈
      freeFreePoolFn (row σ) (domains a) (domains b) := by
  exact free_free_mem_pool_fn (row σ) (domains a) (domains b)
    (chosen σ a) (chosen σ b)
    (hsound σ a) (hsound σ b) (distinct σ a b hab)

end Costas32
