#!/bin/sh
# Typecheck the Lean development and audit its axioms.
# Lean 4.15.0, no Mathlib. Set LEAN=/path/to/lean if not on PATH.
LEAN=${LEAN:-lean}
command -v "$LEAN" >/dev/null 2>&1 || { echo "lean not found; see README"; exit 127; }
set -e
export LEAN_PATH="$PWD"
for m in Core Extremal Negation ExtremalInterval Dedup FixedLag DomainPoolSimple \
         TmCertificate PoolBounds EndpointBounds LagAggregate TelescopeBridge \
         ConcreteTm CompletionModel TmAssembly Representation Reference DomainSound; do
  "$LEAN" -o "Costas32/$m.olean" "Costas32/$m.lean"
  echo "  ok  $m"
done
echo "TYPECHECK PASS: 18 modules"
cat > /tmp/_ax.lean <<'AX'
import Costas32.TmAssembly
import Costas32.CompletionModel
import Costas32.TelescopeBridge
import Costas32.Representation
import Costas32.Reference
import Costas32.DomainSound
open Costas32
#print axioms tm_assembly_sound
#print axioms tm_certificate_sound
#print axioms concrete_tm_sound
#print axioms take_sum_le
#print axioms largest_take_sum_ge
#print axioms selection_between
#print axioms aggregate_lag_nodup_of_injective
#print axioms mem_dedupInt_iff
#print axioms dedupInt_nodup
#print axioms fixed_lag_values_nodup
#print axioms telescope
#print axioms T_symm
#print axioms mem_domainList
#print axioms mem_domainValues
#print axioms mem_domainList_of_submask
#print axioms cpp_sound_given_obligations
#print axioms ref_fixedFree_eq
#print axioms ref_dedup_preserves
#print axioms ref_lower_eq
#print axioms ref_disjoint_iff
#print axioms ref_sum_bounded
#print axioms sound_erase
#print axioms no_adm_of_empty
#print axioms unary_sound
#print axioms arc_sound
#print axioms shave_sound
#print axioms filter_pipeline_sound
AX
"$LEAN" /tmp/_ax.lean | tee /tmp/_ax.out
grep -q "sorryAx" /tmp/_ax.out && { echo "FAIL: depends on sorryAx"; exit 1; }
grep -q "ofReduceBool" /tmp/_ax.out && { echo "FAIL: depends on native_decide"; exit 1; }
! grep -rq "sorry" Costas32/*.lean || { echo "FAIL: sorry in source"; exit 1; }
echo "AXIOM AUDIT PASS: no sorryAx, no native_decide"
