#!/bin/sh
# Nsight Compute on the two backends under the EXACT schedule, which controls
# warp imbalance so the measurement isolates memory placement.
cd "$(dirname "$0")/.."; mkdir -p evidence/profile
for b in local shared; do
  ncu --set full --target-processes all --export evidence/profile/exact_$b \
    ./costas_gpu_phase4 --gpu --backend=$b --threads=${TH:-32} \
      --read-prefixes=catalogues/prefixes_N20_D4_exact.txt \
      --write-results=evidence/profile/exact_${b}_results.txt || echo "ncu failed for $b"
done
echo "Capture: kernel time, registers/thread, local ld/st transactions, spill bytes,"
echo "         shared transactions + bank conflicts, achieved occupancy,"
echo "         branch efficiency, eligible warps/cycle, long-scoreboard stalls."
