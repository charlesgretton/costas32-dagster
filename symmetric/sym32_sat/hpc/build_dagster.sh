#!/bin/bash
# Rebuild Dagster with the same environment as your original build (glog and CUDD in
# $HOME/local, openmpi module). Checks the compiler can find them BEFORE running make.
#   bash hpc/build_dagster.sh [dagster_source_dir]      (default: $DAGSTER_DIR)
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); source "$ROOT/hpc/env.sh"
D=${1:-$DAGSTER_DIR}
[ -f "$D/Master.cpp" ] || { echo "no Dagster source at $D (pass the directory holding Master.cpp)"; exit 1; }
command -v mpic++ >/dev/null || { echo "mpic++ not found: is 'module load openmpi/4.1.0' working?"; exit 1; }
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
probe() {  # <header> <library>
  # cudd.h is not self-contained (uses size_t), so include what a real program would first.
  printf '#include <cstddef>\n#include <cstdio>\n#include <%s>\n' "$1" > "$T/h.cpp"
  if ! err=$(mpic++ -fsyntax-only "$T/h.cpp" 2>&1); then
    if grep -q "No such file or directory" <<<"$err"; then echo "  HEADER NOT FOUND: <$1>"
    else echo "  <$1> found but does not compile: $(grep -m1 error: <<<"$err")"; fi
    return 1
  fi
  echo 'int main(){return 0;}' > "$T/m.cpp"
  if ! err=$(mpic++ "$T/m.cpp" -l"$2" -o "$T/a.out" 2>&1); then
    echo "  LIBRARY NOT FOUND: -l$2  ($(grep -m1 -E 'cannot find|error' <<<"$err"))"; return 1
  fi
  echo "  ok: <$1> and -l$2"
}
echo "checking build dependencies:"; ok=1
probe glog/logging.h glog || ok=0
probe cudd.h cudd || ok=0
if [ $ok = 0 ]; then
  echo; echo "CPATH=${CPATH:-}"; echo "LIBRARY_PATH=${LIBRARY_PATH:-}"
  echo "Find where your original build got them:"
  echo "  find \$HOME -name logging.h -path '*glog*' 2>/dev/null"
  echo "  find \$HOME \\( -name 'libglog*' -o -name 'libcudd*' \\) 2>/dev/null"
  echo "then export CPATH=<include dir> LIBRARY_PATH=<lib dir> LD_LIBRARY_PATH=<lib dir>:\$LD_LIBRARY_PATH"
  echo "and rerun this script.  (Or edit the CPATH/LIBRARY_PATH lines in hpc/env.sh once.)"
  exit 1
fi
cd "$D" && make -j 8 || { echo "make FAILED -- the previous binary, if any, is unchanged"; exit 1; }
[ dagster -nt Master.cpp ] || { echo "binary is older than Master.cpp: not rebuilt"; exit 1; }
echo "wall-clock patch in source: $(grep -q '#include "wallclock.h"' Master.cpp && echo yes || echo no)"
echo "built $D/dagster"; sha256sum dagster
