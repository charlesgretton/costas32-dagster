import Costas32.Core

namespace Costas32

/-!
# From the telescoping identity to the certificate balance equation
-/

/-- Splitting both exact sides into fixed and unresolved contributions preserves
    the telescoping equality. -/
theorem telescope_decomposition_balance
    (lagTotal endpointTotal lagFixed lagOpen endpointFixed posOpen negOpen : Int)
    (htelescope : lagTotal = endpointTotal)
    (hlag : lagTotal = lagFixed + lagOpen)
    (hend : endpointTotal = endpointFixed + posOpen - negOpen) :
    lagFixed + lagOpen = endpointFixed + posOpen - negOpen := by
  omega

/-- List-valued version used directly by `TmState.balance`. -/
theorem telescope_list_balance
    (lagTotal endpointTotal lagFixed endpointFixed : Int)
    (lagOpen positiveRows negativeRows : List Int)
    (htelescope : lagTotal = endpointTotal)
    (hlag : lagTotal = lagFixed + lagOpen.sum)
    (hend : endpointTotal = endpointFixed + positiveRows.sum - negativeRows.sum) :
    lagFixed + lagOpen.sum =
      endpointFixed + positiveRows.sum - negativeRows.sum := by
  exact telescope_decomposition_balance lagTotal endpointTotal
    lagFixed lagOpen.sum endpointFixed positiveRows.sum negativeRows.sum
    htelescope hlag hend

/-- The typechecked telescoping theorem supplies the exact total equality once
    `lagTotal` and `endpointTotal` are unfolded to their sequence definitions. -/
theorem telescope_supplies_total
    (f : Nat → Int) (m k : Nat) :
    tsum (fun i => f (i + m) - f i) k =
      win f k m - win f 0 m := by
  exact telescope f m k

end Costas32
