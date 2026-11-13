import Costas32.ConcreteTm
import Costas32.LagAggregate
import Costas32.TelescopeBridge

namespace Costas32

/-!
# Final theorem-level assembly of the T_m rule

`TmAssemblyData` packages the mathematical facts that the executable's domain
construction must establish. The theorem below constructs the `TmState` fields
and invokes `concrete_tm_sound`.
-/

structure TmAssemblyData (Completion : Type) where
  lagPairs : List (LagPairRealisation Completion)
  lagPairsNodup : lagPairs.Nodup
  lagInjective : ∀ σ p, p ∈ lagPairs → ∀ q, q ∈ lagPairs →
    p.realised σ = q.realised σ → p = q

  lagLowerPool : List Int
  lagUpperNegPool : List Int
  lagLowerSorted : lagLowerPool.Pairwise (· ≤ ·)
  lagUpperNegSorted : lagUpperNegPool.Pairwise (· ≤ ·)
  lagPoolCovers : ∀ d ∈ dedupInt (aggregateLagPool lagPairs),
    d ∈ lagLowerPool
  lagNegPoolCovers : ∀ d ∈ dedupInt (aggregateLagPool lagPairs),
    -d ∈ lagUpperNegPool

  positiveRows : Completion → RowSelection
  negativeRows : Completion → RowSelection
  posCard : Nat
  negCard : Nat
  posLength : ∀ σ, (positiveRows σ).chosen.length = posCard
  negLength : ∀ σ, (negativeRows σ).chosen.length = negCard

  lagFixed : Int
  endpointFixed : Int
  balance : ∀ σ,
    lagFixed + (aggregateLagValues lagPairs σ).sum =
      endpointFixed + (positiveRows σ).chosen.sum -
        (negativeRows σ).chosen.sum

  endpointLoValue : Int
  endpointHiValue : Int
  endpointStable : ∀ σ,
    endpointFixed
      + lowerK (positiveRows σ).lowerPool posCard
      - upperKFromNeg (negativeRows σ).upperNegPool negCard
        = endpointLoValue ∧
    endpointFixed
      + upperKFromNeg (positiveRows σ).upperNegPool posCard
      - lowerK (negativeRows σ).lowerPool negCard
        = endpointHiValue

/-- Every realised lag difference is covered by both extremal pools. -/
theorem assembly_lag_mem_lower
    {C : Type} (A : TmAssemblyData C) (σ : C) :
    ∀ d ∈ aggregateLagValues A.lagPairs σ, d ∈ A.lagLowerPool := by
  intro d hd
  apply A.lagPoolCovers d
  exact aggregate_lag_mem_dedup A.lagPairs σ d hd

/-- Negated realised lag differences are covered by the upper pool. -/
theorem assembly_lag_neg_mem_upper
    {C : Type} (A : TmAssemblyData C) (σ : C) :
    ∀ d ∈ aggregateLagValues A.lagPairs σ, -d ∈ A.lagUpperNegPool := by
  intro d hd
  apply A.lagNegPoolCovers d
  exact aggregate_lag_mem_dedup A.lagPairs σ d hd

/-- Construct the state-level certificate from the completed assembly data. -/
def TmAssemblyData.toState {C : Type} (A : TmAssemblyData C) : TmState C where
  lagFixed := A.lagFixed
  endpointFixed := A.endpointFixed
  lagLowerPool := A.lagLowerPool
  lagUpperNegPool := A.lagUpperNegPool
  lagLowerSorted := A.lagLowerSorted
  lagUpperNegSorted := A.lagUpperNegSorted
  lagChosen := aggregateLagValues A.lagPairs
  lagChosenNodup := fun σ =>
    aggregate_lag_nodup_of_injective A.lagPairs σ
      (A.lagInjective σ) A.lagPairsNodup
  lagMemLower := assembly_lag_mem_lower A
  lagNegMemUpper := assembly_lag_neg_mem_upper A
  lagCard := A.lagPairs.length
  lagLength := aggregate_lag_length A.lagPairs
  positiveRows := A.positiveRows
  negativeRows := A.negativeRows
  posCard := A.posCard
  negCard := A.negCard
  posLength := A.posLength
  negLength := A.negLength
  balance := A.balance

/-- Completed mathematical soundness theorem for assembled domain and endpoint
    certificates. -/
theorem tm_assembly_sound {C : Type} (A : TmAssemblyData C)
    (hdisjoint :
      stateLagHi A.toState < A.endpointLoValue ∨
      A.endpointHiValue < stateLagLo A.toState) :
    C → False := by
  exact concrete_tm_sound A.toState A.endpointLoValue A.endpointHiValue
    A.endpointStable hdisjoint

end Costas32
