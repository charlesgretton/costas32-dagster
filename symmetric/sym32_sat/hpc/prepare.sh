#!/bin/bash
# hpc/prepare.sh -- run ONCE on a login node before any job. Stops on the first failure.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); source "$ROOT/hpc/env.sh"
python3 -c 'import sys; assert sys.version_info>=(3,7)' || { echo "need python>=3.7"; exit 1; }
# 1. Dagster: must be AFSAT-Integration (-e 3)
[ -x "$DAGSTER_BIN" ] || { echo "no Dagster at $DAGSTER_BIN (see README_HPC.md)"; exit 1; }
grep -q "ENUMERATE_SOLUTIONS==3" "$DAGSTER_DIR/Worker.cpp" \
  || { echo "Dagster has no -e 3 mode: use the AFSAT-Integration branch"; exit 1; }
# 2. Kissat, built once into $HOME/local
if [ ! -x "$KISSAT" ]; then
  [ -n "${KISSAT_SRC:-}" ] || { echo "set KISSAT_SRC to an unpacked kissat source tree"; exit 1; }
  ( cd "$KISSAT_SRC" && ./configure && make -j 8 )
  mkdir -p $HOME/local/bin && cp "$KISSAT_SRC/build/kissat" "$KISSAT"
fi
bash "$ROOT/hpc/kissat_check.sh" || exit 1
# 3. Provenance -- refuse to proceed without it
mkdir -p "$COSTAS_DATA/results"
{ date -Is; uname -a; echo "kissat: $(realpath $KISSAT)"; sha256sum "$KISSAT"; "$KISSAT" --version
  echo "dagster: $(realpath $DAGSTER_BIN)"; sha256sum "$DAGSTER_BIN"
  ( cd "$DAGSTER_DIR" && git log -1 --format='commit %H %s' ) 2>/dev/null || true
  mpirun --version 2>&1 | head -1; python3 --version
  echo "source files:"; ( cd "$ROOT" && find . -name '*.py' -o -name '*.sh' -o -name '*.pbs' | sort | xargs sha256sum )
} > "$COSTAS_DATA/provenance.txt"
cat "$COSTAS_DATA/provenance.txt"
# 4. Gate 0.2 -- frozen regression suite ON THE CLUSTER. Any difference stops everything.
( cd "$ROOT/validation"
  o=$(python3 test_completeness.py);  echo "$o"; grep -q "n=10.*COMPLETENESS PASS" <<<"$o" &&
  o=$(python3 test_soundness.py);     echo "$o"; grep -q "n=10.*SOUNDNESS PASS"    <<<"$o" &&
  o=$(python3 test_historical158.py); echo "$o"; grep -q "accepted 158, rejected 0" <<<"$o" ) \
  || { echo "REGRESSION SUITE DIFFERS FROM VALIDATION.json -- STOP"; exit 2; }
# 5. Regions and the stratified sample
( cd "$ROOT" && python3 regions.py "$COSTAS_DATA/regions.csv" )
python3 "$ROOT/hpc/sample.py" "$COSTAS_DATA/regions.csv" "$COSTAS_DATA/sample.txt"
echo "PREPARE OK. Next: qsub hpc/smoke.pbs"
