#!/bin/sh
# One source, two build modes. ARCH defaults to Ada (RTX 4090).
set -e; cd "$(dirname "$0")/.."; ARCH=${ARCH:-sm_89}; mkdir -p evidence
g++ -x c++ -std=c++20 -O3 -DNDEBUG -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror \
    src/costas_gpu_phase4.cu -o costas_cpu_phase4
echo "CPU build ok"
if command -v nvcc >/dev/null 2>&1; then
  nvcc -std=c++20 -O3 -lineinfo -arch=$ARCH -Xptxas=-v src/costas_gpu_phase4.cu \
       -o costas_gpu_phase4 2>&1 | tee evidence/ptxas-$ARCH.txt
  cuobjdump --dump-resource-usage ./costas_gpu_phase4 > evidence/resource-usage-$ARCH.txt
  echo "CUDA build ok. Record from evidence/ptxas-$ARCH.txt, per kernel:"
  echo "  registers/thread, stack-frame bytes, spill stores, spill loads"
  echo "  Compare against the 1734 B explicit per-thread state estimate (README)."
else
  echo "nvcc absent: CPU-only build; GPU cells will be skipped."
fi
