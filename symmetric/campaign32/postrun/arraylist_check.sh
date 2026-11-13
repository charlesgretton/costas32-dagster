#!/bin/bash
# Compare the SORTED LISTS of arrays (not just counts) from the split campaign pipeline with an independent
# unsplit reference, the project's printing search (symmetric/src/involution_dfs_printing.cpp).
# usage: arraylist_check.sh [orders...]   (default 16 18 20 22); run from campaign32/postrun
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); SRC=$HERE/../../src/involution_dfs_printing.cpp; T=$(mktemp -d)
g++ -O3 -o "$T/inv32" "$HERE/../inv32.cpp"; g++ -O3 -o "$T/ref" "$SRC"
for N in ${@:-16 18 20 22}; do
  "$T/ref" $N | grep -v '^n=' | sed 's/ *$//; s/ /,/g' | sort > "$T/ref_$N"
  "$T/inv32" split $N 3 > "$T/tasks_$N"; grep '^T' "$T/tasks_$N" | "$T/inv32" run $N | awk '/^ARRAY/{print $3}' | sort > "$T/split_$N"
  if cmp -s "$T/ref_$N" "$T/split_$N"; then echo "order $N: $(wc -l < "$T/ref_$N") arrays; split list identical to the independent reference"
  else echo "ARRAY LIST MISMATCH at order $N"; diff "$T/ref_$N" "$T/split_$N" | head; rm -rf "$T"; exit 1; fi
done
rm -rf "$T"; echo "ARRAY LIST CHECK PASS"
