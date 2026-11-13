#!/bin/sh
# Run FIRST on the GPU host. Captures what cannot be recovered after the session ends.
set -e; cd "$(dirname "$0")/.."; E=evidence; mkdir -p $E
{ date --iso-8601=seconds; hostname; uname -a; } > $E/host.txt
nvidia-smi > $E/nvidia-smi.txt 2>&1 || echo "nvidia-smi unavailable" > $E/nvidia-smi.txt
nvidia-smi --query-gpu=name,uuid,driver_version,vbios_version,memory.total,power.limit,clocks.max.sm,clocks.max.memory,compute_cap --format=csv > $E/gpu-properties.csv 2>&1 || true
{ nvcc --version 2>&1; echo; ncu --version 2>&1; } > $E/toolchain.txt || true
sha256sum src/costas_gpu_phase4.cu catalogues/*.txt oracles/*.txt > $E/input-sha256.txt
echo "environment captured -> $E/"
