#!/bin/bash
# Make Dagster's master time things by WALL clock instead of its own CPU time.
#   - checkpoints (-v N) then fire every N seconds; before, a master that sleeps while
#     waiting barely accumulates CPU time, so they effectively never fired
#   - per-message statistics (the 'MASTER: Timings' line) then measure real time
# usage: bash hpc/patch_dagster_wallclock.sh $DAGSTER_DIR   then rebuild with make
set -euo pipefail
D=${1:?give the dagster source directory, the one containing Master.cpp}
HERE=$(cd "$(dirname "$0")" && pwd)
for f in Master.cpp StatisticsModule.h; do [ -f "$D/$f" ] || { echo "no $D/$f"; exit 1; }; done
grep -q '#include "wallclock.h"' "$D/Master.cpp" && { echo "already patched"; exit 0; }
cp "$HERE/dagster_wallclock.h" "$D/wallclock.h"
for f in Master.cpp StatisticsModule.h; do
  cp "$D/$f" "$D/$f.orig"
  sed -i 's/\bclock()/wall_clock()/g' "$D/$f"
  sed -i '0,/#include/s//#include "wallclock.h"\n#include/' "$D/$f"
done
# grep -c exits 1 when it counts zero; under pipefail that would kill the script on the
# SUCCESSFUL path, so tolerate it explicitly.
left=$( { grep -c '\bclock()' "$D/Master.cpp" "$D/StatisticsModule.h" || true; } | awk -F: '{s+=$2} END{print s+0}')
n=$( { grep -c 'wall_clock()' "$D/Master.cpp" "$D/StatisticsModule.h" || true; } | awk -F: '{s+=$2} END{print s+0}')
echo "replaced clock() -> wall_clock(): $n uses; clock() remaining: $left (originals kept as *.orig)"
[ "$left" = 0 ] || { echo "WARNING: some clock() calls remain -- inspect before building"; exit 1; }
echo "now rebuild:  bash hpc/build_dagster.sh $D"
