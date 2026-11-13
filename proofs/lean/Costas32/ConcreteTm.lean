import Costas32.TmCertificate
import Costas32.EndpointBounds
import Costas32.FixedLag

namespace Costas32

/-- Minimal mathematical interface exposed by one partial-search state at one
    lag. It is intentionally independent of bitmasks and queue scheduling. -/
structure TmState (Completion : Type) where
  lagFixed : Int
  endpointFixed : Int
  lagLowerPool : List Int
  lagUpperNegPool : List Int
  lagLowerSorted : lagLowerPool.Pairwise (· ≤ ·)
  lagUpperNegSorted : lagUpperNegPool.Pairwise (· ≤ ·)
  lagChosen : Completion → List Int
  lagChosenNodup : ∀ σ, (lagChosen σ).Nodup
  lagMemLower : ∀ σ x, x ∈ lagChosen σ → x ∈ lagLowerPool
  lagNegMemUpper : ∀ σ x, x ∈ lagChosen σ → -x ∈ lagUpperNegPool
  lagCard : Nat
  lagLength : ∀ σ, (lagChosen σ).length = lagCard

  positiveRows : Completion → RowSelection
  negativeRows : Completion → RowSelection
  posCard : Nat
  negCard : Nat
  posLength : ∀ σ, (positiveRows σ).chosen.length = posCard
  negLength : ∀ σ, (negativeRows σ).chosen.length = negCard

  /-- The telescoping equality after fixed contributions are separated. -/
  balance : ∀ σ,
    lagFixed + (lagChosen σ).sum =
      endpointFixed + (positiveRows σ).chosen.sum -
        (negativeRows σ).chosen.sum

def stateLagLo {C : Type} (S : TmState C) : Int :=
  S.lagFixed + lowerK S.lagLowerPool S.lagCard

def stateLagHi {C : Type} (S : TmState C) : Int :=
  S.lagFixed + upperKFromNeg S.lagUpperNegPool S.lagCard

/-- Endpoint lower bound for a particular completion. A subsequent
    representation layer proves that the pools are state-invariant, yielding
    the concrete cached bounds used by the C++ propagator. -/
def completionEndpointLo {C : Type} (S : TmState C) (σ : C) : Int :=
  S.endpointFixed
    + lowerK (S.positiveRows σ).lowerPool S.posCard
    - upperKFromNeg (S.negativeRows σ).upperNegPool S.negCard

def completionEndpointHi {C : Type} (S : TmState C) (σ : C) : Int :=
  S.endpointFixed
    + upperKFromNeg (S.positiveRows σ).upperNegPool S.posCard
    - lowerK (S.negativeRows σ).lowerPool S.negCard

theorem state_lag_outer {C : Type} (S : TmState C) (σ : C) :
    stateLagLo S ≤ S.lagFixed + (S.lagChosen σ).sum ∧
      S.lagFixed + (S.lagChosen σ).sum ≤ stateLagHi S := by
  let E : ExtremalSelection := {
    lowerPool := S.lagLowerPool
    upperNegPool := S.lagUpperNegPool
    selected := S.lagChosen σ
    lower_sorted := S.lagLowerSorted
    upperNeg_sorted := S.lagUpperNegSorted
    selected_nodup := S.lagChosenNodup σ
    selected_mem_lower := S.lagMemLower σ
    selected_neg_mem_upper := S.lagNegMemUpper σ
  }
  have h := fixed_card_selection_between S.lagFixed E S.lagCard
    (S.lagLength σ)
  exact h

theorem state_endpoint_outer {C : Type} (S : TmState C) (σ : C) :
    completionEndpointLo S σ
      ≤ S.endpointFixed + (S.positiveRows σ).chosen.sum
          - (S.negativeRows σ).chosen.sum ∧
    S.endpointFixed + (S.positiveRows σ).chosen.sum
          - (S.negativeRows σ).chosen.sum
      ≤ completionEndpointHi S σ := by
  exact signed_endpoint_fixed_card S.endpointFixed
    (S.positiveRows σ) (S.negativeRows σ) S.posCard S.negCard
    (S.posLength σ) (S.negLength σ)

/-- Soundness with explicit state-invariant endpoint bounds. -/
theorem concrete_tm_sound {C : Type} (S : TmState C)
    (endLo endHi : Int)
    (hend : ∀ σ,
      completionEndpointLo S σ = endLo ∧
      completionEndpointHi S σ = endHi)
    (hdisjoint : stateLagHi S < endLo ∨ endHi < stateLagLo S) :
    C → False := by
  apply tm_interval_sound (a := stateLagLo S) (b := stateLagHi S)
    (c := endLo) (d := endHi)
    (fun σ => S.lagFixed + (S.lagChosen σ).sum)
  · exact state_lag_outer S
  · intro σ
    obtain ⟨he1, he2⟩ := state_endpoint_outer S σ
    have hb := S.balance σ
    obtain ⟨hs1, hs2⟩ := hend σ
    omega
  · exact hdisjoint

end Costas32
