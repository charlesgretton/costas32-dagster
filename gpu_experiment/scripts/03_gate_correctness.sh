#!/bin/sh
# Device correctness gates. Any failure BLOCKS all timing. Fail-closed.
cd "$(dirname "$0")/.."; mkdir -p evidence/results; R=evidence/results; fail=0
[ -x ./costas_gpu_phase4 ] || { echo "no GPU binary; run 01_build.sh on a CUDA host"; exit 1; }
g(){ # backend threads catalogue oracle label
  ./costas_gpu_phase4 --gpu --backend=$1 --threads=$2 --read-prefixes=$3 --write-results=$R/$5.txt >/dev/null 2>&1 \
    || { echo "  FAIL  $5 (launch/exec error)"; fail=1; return; }
  if cmp -s $4 $R/$5.txt; then echo "  PASS  $5"; else echo "  FAIL  $5 (result mismatch)"; fail=1
    diff $4 $R/$5.txt 2>/dev/null | head -4 | sed 's/^/        /'; fi; }
echo "Gate A - compact known-answer, 16 units:"
g local  32 catalogues/prefixes_N16_D1_v2.txt oracles/results_N16_D1_v2_cpu.txt gateA_local_t32
g shared 32 catalogues/prefixes_N16_D1_v2.txt oracles/results_N16_D1_v2_cpu.txt gateA_shared_t32
echo "Gate B - multi-block, 37,573 units:"
g local  32 catalogues/prefixes_N20_D4_v2.txt oracles/results_N20_D4_v2_cpu.txt gateB_local_t32
g shared 32 catalogues/prefixes_N20_D4_v2.txt oracles/results_N20_D4_v2_cpu.txt gateB_shared_t32
if [ $fail -eq 0 ]; then echo "CORRECTNESS GATES PASS - proceed to 04"; else
  echo "GATES FAILED - result is INCOMPLETE/UNKNOWN, never a zero-solution finding"; exit 1; fi
