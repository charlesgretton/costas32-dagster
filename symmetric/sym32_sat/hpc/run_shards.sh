#!/bin/bash
# Split the sample into shards, each pinned to its own W cores with taskset, all in one job.
# usage: run_shards.sh <sample> <out> <cap> <arms> <cores_per_shard> <total_cores>
# Shards are pinned to the CPUs this job actually owns (a partial-node PBS job may be given
# any subset of the node's cores, not 0..N-1). After the run, every region in the sample
# must have a ledger row; any missing region is reported and the script exits nonzero.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
S=$1; OUT=$2; CAP=$3; ARMS=$4; W=$5; TOT=$6
mapfile -t CPUS < <(python3 -c '
import os; print("\n".join(str(c) for c in sorted(os.sched_getaffinity(0))))')
(( ${#CPUS[@]} >= W )) || { echo "only ${#CPUS[@]} CPUs available, need >= $W per shard"; exit 1; }
K=$(( TOT / W )); (( K * W <= ${#CPUS[@]} )) || K=$(( ${#CPUS[@]} / W ))
echo "CPUs owned by this job: ${#CPUS[@]} (${CPUS[0]}..${CPUS[-1]}); shards: $K x $W cores"
i=0; pids=(); mkdir -p "$OUT"
if [ "${QUEUE:-0}" = 1 ]; then
  # Shared queue: each shard claims the next region when free, so the job ends one region
  # after the work runs out, instead of waiting for the unluckiest pre-assigned list.
  Q="${PBS_JOBFS:-${TMPDIR:-/tmp}}/rs_queue_$$"; mkdir -p "$Q"
  grep . "$S" > "$Q/ids.txt"; echo 0 > "$Q/next"
  N=$(wc -l < "$Q/ids.txt"); (( K > N )) && K=$N
  echo "shared queue: $N regions for $K shards in $Q"
  for i in $(seq 0 $(( K - 1 ))); do
    set_=$(IFS=,; echo "${CPUS[*]:$(( i*W )):$W}")
    taskset -c "$set_" python3 "$ROOT/pilot_driver.py" --regions "$COSTAS_DATA/regions.csv" \
       --ids "queue:$Q" --out "$OUT/shard$i" --cap "$CAP" --ranks "$W" --arms "$ARMS" \
       > "$OUT/shard$i.log" 2>&1 &
    pids+=($!)
  done
else
  mkdir -p "$OUT/shards"
  split -n r/$K -d -a 3 "$S" "$OUT/shards/ids."
  for f in "$OUT"/shards/ids.*; do
    [ -s "$f" ] || continue
    set_=$(IFS=,; echo "${CPUS[*]:$(( i*W )):$W}")
    taskset -c "$set_" python3 "$ROOT/pilot_driver.py" --regions "$COSTAS_DATA/regions.csv" \
       --ids @"$f" --out "$OUT/shard$i" --cap "$CAP" --ranks "$W" --arms "$ARMS" \
       > "$OUT/shard$i.log" 2>&1 &
    pids+=($!); i=$((i+1))
  done
fi
fail=0; for p in "${pids[@]}"; do wait $p || fail=1; done
cat "$OUT"/shard*/ledger.jsonl > "$OUT/ledger.jsonl" 2>/dev/null || true
missing=$(python3 - "$S" "$OUT/ledger.jsonl" <<'PY'
import json, sys
want = [l.strip() for l in open(sys.argv[1]) if l.strip()]
try: have = {json.loads(l)["region_id"] for l in open(sys.argv[2]) if l.strip()}
except FileNotFoundError: have = set()
print(" ".join(r for r in want if r not in have))
PY
)
if [ -n "$missing" ]; then
  echo "MISSING RESULTS for $(wc -w <<<"$missing") region(s): $missing"
  echo "see the matching $OUT/shard*.log"; exit 4
fi
[ $fail -eq 0 ] || { echo "A SHARD EXITED NONZERO -- see $OUT/shard*.log"; exit 3; }
echo "all $(grep -c . "$S") regions have results"
