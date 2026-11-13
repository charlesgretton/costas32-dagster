#!/bin/bash
# Build an immutable manifest of a completed campaign, rerun both checkers, and write a hashed tarball.
# usage: archive_campaign.sh CAMPAIGN_DIR EXPECTED_NODES EXPECTED_ARRAYS [DEST_DIR]
# default DEST_DIR: $ARCHIVE_DIR, else $HOME/costas32_archive (choose durable storage on your system)
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd); C=$(cd "$1" && pwd); NODES=$2; ARR=$3
DEST=${4:-${ARCHIVE_DIR:-$HOME/costas32_archive}}; mkdir -p "$DEST"
STAMP=$(date -u +%Y%m%dT%H%M%SZ); NAME=campaign32_inv_n32_$STAMP
echo "== rerun merge.py from the stored files"
python3 "$HERE/../merge.py" "$C/tasks.txt" "$C/results" --expect-nodes "$NODES" --expect-arrays "$ARR" > "$C/merge_rerun_$STAMP.txt"
echo "== independent parser"
python3 "$HERE/independent_check.py" "$C" "$NODES" "$ARR" | tee "$C/independent_check_$STAMP.txt"
echo "== manifest"
cp "$HERE/../inv32.cpp" "$HERE/../merge.py" "$HERE/../selftest.sh" "$HERE/../run_campaign.pbs" "$C/" 2>/dev/null || true
( cd "$C" && find . -type f ! -name 'SHA256SUMS' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS )
python3 - "$C" "$STAMP" "$NODES" "$ARR" <<'PY'
import json, sys, os, glob, hashlib
c, stamp, nodes, arr = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
h = lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
summ = json.load(open(os.path.join(c,'summary.json'))) if os.path.exists(os.path.join(c,'summary.json')) else {}
build = sorted(glob.glob(os.path.join(c,'build_*.txt')))
man = {"campaign": "order-32 transpose-symmetric Costas search (direct, exhaustive)", "archived_utc": stamp,
       "campaign_path": c, "jobs": [os.path.basename(b)[6:-4] for b in build],
       "build_records": {os.path.basename(b): open(b).read().splitlines() for b in build},
       "tasks_sha256": h(os.path.join(c,'tasks.txt')), "chunks": len(glob.glob(os.path.join(c,'chunks','chunk_*'))),
       "results_files": len(glob.glob(os.path.join(c,'results','*.out'))),
       "expected_nodes": nodes, "expected_arrays": arr, "summary": summ,
       "sha256sums_file_sha256": h(os.path.join(c,'SHA256SUMS'))}
json.dump(man, open(os.path.join(c,'CAMPAIGN_MANIFEST.json'),'w'), indent=1)
print("manifest written:", os.path.join(c,'CAMPAIGN_MANIFEST.json'))
PY
echo "== archive"
tar -czf "$DEST/$NAME.tar.gz" -C "$(dirname "$C")" "$(basename "$C")"
( cd "$DEST" && sha256sum "$NAME.tar.gz" > "$NAME.tar.gz.sha256" && cat "$NAME.tar.gz.sha256" )
echo "ARCHIVE COMPLETE: $DEST/$NAME.tar.gz"
