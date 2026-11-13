import Costas32.Core
import Costas32.ExtremalInterval
namespace Costas32

/-- Completion-independent interval pools plus completion-dependent realised
    selections for the two sides of the telescoping identity. -/
structure TmCertificate (Completion : Type) where
  lagLowerPool : List Int
  lagUpperNegPool : List Int
  endpointLowerPool : List Int
  endpointUpperNegPool : List Int
  lagLowerSorted : lagLowerPool.Pairwise (· ≤ ·)
  lagUpperNegSorted : lagUpperNegPool.Pairwise (· ≤ ·)
  endpointLowerSorted : endpointLowerPool.Pairwise (· ≤ ·)
  endpointUpperNegSorted : endpointUpperNegPool.Pairwise (· ≤ ·)
  lagSelected : Completion → List Int
  endpointSelected : Completion → List Int
  lagNodup : ∀ σ, (lagSelected σ).Nodup
  endpointNodup : ∀ σ, (endpointSelected σ).Nodup
  lagMemLower : ∀ σ x, x ∈ lagSelected σ → x ∈ lagLowerPool
  lagNegMemUpper : ∀ σ x, x ∈ lagSelected σ → -x ∈ lagUpperNegPool
  endpointMemLower : ∀ σ x, x ∈ endpointSelected σ → x ∈ endpointLowerPool
  endpointNegMemUpper : ∀ σ x, x ∈ endpointSelected σ → -x ∈ endpointUpperNegPool
  lagCard : Nat
  endpointCard : Nat
  lagLength : ∀ σ, (lagSelected σ).length = lagCard
  endpointLength : ∀ σ, (endpointSelected σ).length = endpointCard
  lagFixed : Int
  endpointFixed : Int
  balance : ∀ σ,
    lagFixed + (lagSelected σ).sum =
      endpointFixed + (endpointSelected σ).sum

def lagLo {C : Type} (D : TmCertificate C) : Int :=
  D.lagFixed + (D.lagLowerPool.take D.lagCard).sum

def lagHi {C : Type} (D : TmCertificate C) : Int :=
  D.lagFixed - (D.lagUpperNegPool.take D.lagCard).sum

def endpointLo {C : Type} (D : TmCertificate C) : Int :=
  D.endpointFixed + (D.endpointLowerPool.take D.endpointCard).sum

def endpointHi {C : Type} (D : TmCertificate C) : Int :=
  D.endpointFixed - (D.endpointUpperNegPool.take D.endpointCard).sum

theorem lag_outer {C : Type} (D : TmCertificate C) (σ : C) :
    lagLo D ≤ D.lagFixed + (D.lagSelected σ).sum ∧
      D.lagFixed + (D.lagSelected σ).sum ≤ lagHi D := by
  have h := selection_between {
    lowerPool := D.lagLowerPool
    upperNegPool := D.lagUpperNegPool
    selected := D.lagSelected σ
    lower_sorted := D.lagLowerSorted
    upperNeg_sorted := D.lagUpperNegSorted
    selected_nodup := D.lagNodup σ
    selected_mem_lower := D.lagMemLower σ
    selected_neg_mem_upper := D.lagNegMemUpper σ }
  dsimp only at h
  rw [D.lagLength σ] at h
  simp only [lagLo, lagHi]
  omega

theorem endpoint_outer {C : Type} (D : TmCertificate C) (σ : C) :
    endpointLo D ≤ D.endpointFixed + (D.endpointSelected σ).sum ∧
      D.endpointFixed + (D.endpointSelected σ).sum ≤ endpointHi D := by
  have h := selection_between {
    lowerPool := D.endpointLowerPool
    upperNegPool := D.endpointUpperNegPool
    selected := D.endpointSelected σ
    lower_sorted := D.endpointLowerSorted
    upperNeg_sorted := D.endpointUpperNegSorted
    selected_nodup := D.endpointNodup σ
    selected_mem_lower := D.endpointMemLower σ
    selected_neg_mem_upper := D.endpointNegMemUpper σ }
  dsimp only at h
  rw [D.endpointLength σ] at h
  simp only [endpointLo, endpointHi]
  omega

/-- Full abstract T_m soundness theorem. -/
theorem tm_certificate_sound {C : Type} (D : TmCertificate C)
    (hdisjoint : lagHi D < endpointLo D ∨ endpointHi D < lagLo D) :
    C → False := by
  apply tm_interval_sound (a := lagLo D) (b := lagHi D)
    (c := endpointLo D) (d := endpointHi D)
    (fun σ => D.lagFixed + (D.lagSelected σ).sum)
  · exact lag_outer D
  · intro σ
    obtain ⟨h1, h2⟩ := endpoint_outer D σ
    have hb := D.balance σ
    omega
  · exact hdisjoint

end Costas32
