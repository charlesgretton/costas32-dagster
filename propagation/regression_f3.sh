#!/bin/sh
# Regression guard for the two bugs that produced the wrong F3 verdict.
#   bug 1  singleton shaving no-op (filterAC reinitialised domains on entry):
#          would collapse |D_L3| at (12,6) from 77,074 to about 2,206.
#   bug 2  fixed-prefix relation filtered against its own difference:
#          would make RA reject every input, giving nonzero false positives.
set -e
g++ -O2 -std=c++17 f3_complete.cpp -o /tmp/f3_reg
OUT=$(/tmp/f3_reg 12 6)
echo "$OUT"
echo "$OUT" | grep -q "|D_L3|            = 77074"  || { echo "FAIL: shaving regression (bug 1)"; exit 1; }
echo "$OUT" | grep -q "|D_T|             = 117880" || { echo "FAIL: T_m coverage changed"; exit 1; }
echo "$OUT" | grep -q "false positives: RA 0, L3 0, T 0" || { echo "FAIL: soundness (bug 2)"; exit 1; }
echo "$OUT" | grep -q "VERDICT: PASS"              || { echo "FAIL: verdict changed"; exit 1; }
echo "REGRESSION PASS"

# --- F3' regression: all propagator modes must agree on solution set
g++ -O3 -march=native -std=c++17 f3prime_solver.cpp -o /tmp/f3p_reg
A=$(/tmp/f3p_reg --order 11 --prop inc  | grep -o '"hash_xor":"[^"]*"')
B=$(/tmp/f3p_reg --order 11 --prop l3   | grep -o '"hash_xor":"[^"]*"')
C=$(/tmp/f3p_reg --order 11 --prop l3tm | grep -o '"hash_xor":"[^"]*"')
[ "$A" = "$B" ] && [ "$B" = "$C" ] || { echo "FAIL: solution sets differ across propagators"; exit 1; }
/tmp/f3p_reg --order 11 --prop l3tm | grep -q '"nodes":259414' || { echo "FAIL: L3+Tm node count changed"; exit 1; }
/tmp/f3p_reg --order 11 --prop l3   | grep -q '"nodes":379290' || { echo "FAIL: L3 node count changed"; exit 1; }
echo "F3-PRIME REGRESSION PASS"

# --- exact solution-set equality (not merely hash agreement)
for m in inc l3 l3tm; do
  /tmp/f3p_reg --order 11 --prop $m --emit /tmp/reg_$m.txt > /dev/null
  LC_ALL=C sort /tmp/reg_$m.txt -o /tmp/reg_$m.srt
done
cmp -s /tmp/reg_inc.srt /tmp/reg_l3.srt && cmp -s /tmp/reg_inc.srt /tmp/reg_l3tm.srt \
  || { echo "FAIL: solution sets differ byte-for-byte"; exit 1; }
echo "EXACT SOLUTION-SET EQUALITY PASS"

# --- cpp_matches_reference: production tmDetect vs literal Lean transcription
/tmp/f3_reg2_build 2>/dev/null || g++ -O2 -std=c++17 f3_complete.cpp -o /tmp/f3_reg2
/tmp/f3_reg2 12 6 | grep -q "cpp_matches_reference: 227214 comparisons, 0 mismatches" \
  || { echo "FAIL: production tmDetect diverged from the Lean reference"; exit 1; }
echo "CPP-MATCHES-REFERENCE PASS"
