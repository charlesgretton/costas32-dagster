#!/bin/bash
# Submit f=2 campaign batches written by 'f2_campaign.py plan'. Depth 3, full node per region.
#   bash hpc/submit_f2.sh [first] [last]      e.g. 0 9 submits batch_000 .. batch_009
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); source "$ROOT/hpc/env.sh"; cd "$ROOT"
CAP=${CAP:-3600}; B="$COSTAS_DATA/campaign_f2"
files=("$B"/batch_*.txt); first=${1:-0}; last=${2:-$(( ${#files[@]} - 1 ))}
BASE=${BASELINE:-$COSTAS_DATA/results/tail_all.jsonl}; [ -f "$BASE" ] || BASE=/dev/null
for i in $(seq "$first" "$last"); do
  f=$(printf "%s/batch_%03d.txt" "$B" "$i"); [ -s "$f" ] || continue
  n=$(grep -c . "$f"); mins=$(( n * (CAP + 120) / 60 + 15 ))
  wt=$(printf "%02d:%02d:00" $(( mins / 60 )) $(( mins % 60 )))
  id=$(qsub -N "f2-$(printf %03d $i)" -l walltime=$wt \
       -v SLOT=104,IDS=$f,BASELINE=$BASE,CAP=$CAP,GRID='tini_d3|3|-m 0 -e 0 -b 0 -g 0' hpc/dagster_scale.pbs)
  echo "batch $(printf %03d $i): $n regions, walltime $wt -> $id"
done
