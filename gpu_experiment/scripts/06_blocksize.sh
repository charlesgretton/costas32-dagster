#!/bin/sh
# Block-size sweep. Shared at 128 threads needs 126,976 B opt-in; the launcher
# queries sharedMemPerBlockOptin and refuses if unsupported.
cd "$(dirname "$0")/.."; R=evidence/results; mkdir -p $R
for t in 32 64 128; do
  ./costas_gpu_phase4 --gpu --backend=local --threads=$t \
    --read-prefixes=catalogues/prefixes_N20_D4_exact.txt --write-results=$R/bs_local_t$t.txt \
    2>&1 | grep -E '^TIMING' | sed "s/^/local  t$t /"
  cmp -s oracles/results_N20_D4_v2_cpu.txt $R/bs_local_t$t.txt || echo "  MISMATCH local t$t"
done
for t in 32 64; do
  ./costas_gpu_phase4 --gpu --backend=shared --threads=$t \
    --read-prefixes=catalogues/prefixes_N20_D4_exact.txt --write-results=$R/bs_shared_t$t.txt \
    2>&1 | grep -E '^TIMING' | sed "s/^/shared t$t /"
  cmp -s oracles/results_N20_D4_v2_cpu.txt $R/bs_shared_t$t.txt || echo "  MISMATCH shared t$t"
done
