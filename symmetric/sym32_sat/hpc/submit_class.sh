#!/bin/bash
# Submit Kissat class batches written by 'campaign.py --f F plan'.
#   F=6 bash hpc/submit_class.sh [first] [last]     (CAP, WALLTIME may be set; defaults by class)
# Defaults: f=6 -> cap 600 s, walltime 2 h;  f=4 -> cap 3600 s, walltime 8 h.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); source "$ROOT/hpc/env.sh"; cd "$ROOT"
F=${F:?set F to the fixed-point class, e.g. F=6}
case $F in 6) CAP=${CAP:-600};  WT=${WALLTIME:-02:00:00};;
           4) CAP=${CAP:-3600}; WT=${WALLTIME:-08:00:00};;
           *) CAP=${CAP:?set CAP}; WT=${WALLTIME:?set WALLTIME};; esac
B="$COSTAS_DATA/campaign_f$F"; files=("$B"/batch_*.txt)
first=${1:-0}; last=${2:-$(( ${#files[@]} - 1 ))}
for i in $(seq "$first" "$last"); do
  f=$(printf "%s/batch_%03d.txt" "$B" "$i"); [ -s "$f" ] || continue
  id=$(qsub -N "f$F-$(printf %03d $i)" -l walltime=$WT -v IDS=$f,CAP=$CAP hpc/kissat_class.pbs)
  echo "f=$F batch $(printf %03d $i): $(grep -c . "$f") regions, cap ${CAP}s, walltime $WT -> $id"
done
