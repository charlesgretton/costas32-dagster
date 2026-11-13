#!/bin/bash
# Self-test: at orders 16-24 the split-and-merge pipeline must reproduce the unsplit search exactly,
# and the array counts must match the known values (40, 20, 8, 10, 0).
set -euo pipefail
BIN=${BIN:-./inv32}; W=${WORKERS:-4}; DEPTH=${DEPTH:-3}; TMP=${TMPDIR:-/tmp}/inv32_selftest_$$; mkdir -p "$TMP"
declare -A KNOWN=([16]=40 [18]=20 [20]=8 [22]=10 [24]=0)
for N in ${ORDERS:-16 18 20 22 24}; do
  FULL=$("$BIN" full $N); FN=$(echo "$FULL" | sed 's/.*nodes=\([0-9]*\).*/\1/'); FA=$(echo "$FULL" | sed 's/.*arrays=\([0-9]*\).*/\1/')
  [ "$FA" = "${KNOWN[$N]}" ] || { echo "SELFTEST FAIL: order $N full search found $FA arrays, expected ${KNOWN[$N]}"; exit 1; }
  "$BIN" split $N $DEPTH > "$TMP/tasks_$N.txt"; mkdir -p "$TMP/res_$N"
  grep '^T' "$TMP/tasks_$N.txt" | split -l 20 - "$TMP/chunk_${N}_"
  ls "$TMP"/chunk_${N}_* | xargs -P "$W" -I{} sh -c "\"$BIN\" run $N < {} > {}.part && mv {}.part $TMP/res_$N/\$(basename {}).out"
  python3 "$(dirname "$0")/merge.py" "$TMP/tasks_$N.txt" "$TMP/res_$N" --expect-nodes "$FN" --expect-arrays "$FA" > "$TMP/merge_$N.txt" \
    || { echo "SELFTEST FAIL: order $N split pipeline disagrees with the unsplit search"; cat "$TMP/merge_$N.txt"; exit 1; }
  echo "order $N: unsplit $FN nodes, $FA arrays; split into $(grep -c '^T' "$TMP/tasks_$N.txt") tasks; merge reproduces both exactly"
done
rm -rf "$TMP"; echo "SELFTEST PASS"
