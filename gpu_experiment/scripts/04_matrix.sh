#!/bin/sh
# Six-cell factorial: {original, exact, refined-proxy} x {local, shared}.
# Requires 03_gate_correctness.sh to have passed. Kernel-only timing comes from
# the binary's own CUDA-event TIMING line; shell time is recorded separately.
cd "$(dirname "$0")/.."; R=evidence/results; mkdir -p $R
REPS=${REPS:-5}; TH=${TH:-32}
# exact schedule for the unrefined frontier is derived, not shipped
[ -f catalogues/prefixes_N20_D4_exact.txt ] || \
  ./costas_cpu_phase4 --read-prefixes=catalogues/prefixes_N20_D4_v2.txt --schedule=exact \
    --oracle-results=oracles/results_N20_D4_v2_cpu.txt \
    --write-prefixes=catalogues/prefixes_N20_D4_exact.txt --write-results=/dev/null >/dev/null
cell(){ # label catalogue oracle backend predicted_lane_eff
  echo "== $1  (predicted lane eff $5)"
  ./costas_gpu_phase4 --gpu --backend=$4 --threads=$TH --read-prefixes=$2 \
     --write-results=$R/$1_warmup.txt >/dev/null 2>&1   # discarded warm-up
  i=1; while [ $i -le $REPS ]; do
    ./costas_gpu_phase4 --gpu --backend=$4 --threads=$TH --read-prefixes=$2 \
       --write-results=$R/$1_run$i.txt 2>&1 | grep -E '^TIMING' | sed "s/^/  rep$i /" \
       | tee -a $R/$1_timing.txt
    cmp -s $3 $R/$1_run$i.txt || { echo "  *** rep$i RESULT MISMATCH - cell invalid ***"; exit 1; }
    i=$((i+1)); done
  echo "  all $REPS reps byte-identical to oracle"; }
cell original_local  catalogues/prefixes_N20_D4_v2.txt          oracles/results_N20_D4_v2_cpu.txt          local  26.5%
cell exact_local     catalogues/prefixes_N20_D4_exact.txt       oracles/results_N20_D4_v2_cpu.txt          local  98.4%
cell refined_local   catalogues/prefixes_N20_refined400_pb2.txt oracles/results_N20_refined400_pb2_cpu.txt local  63.4%
cell original_shared catalogues/prefixes_N20_D4_v2.txt          oracles/results_N20_D4_v2_cpu.txt          shared 26.5%
cell exact_shared    catalogues/prefixes_N20_D4_exact.txt       oracles/results_N20_D4_v2_cpu.txt          shared 98.4%
cell refined_shared  catalogues/prefixes_N20_refined400_pb2.txt oracles/results_N20_refined400_pb2_cpu.txt shared 63.4%
echo; echo "MATRIX COMPLETE. Timings in $R/*_timing.txt"
echo "Aggregate entered nodes: unrefined 4706251, refined 4705851 (use these for nodes/s)."
