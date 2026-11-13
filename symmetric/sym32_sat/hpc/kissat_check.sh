#!/bin/bash
# Verify the Kissat behaviour pilot_driver.py depends on. Fails closed.
# Run on a login node AND on a compute node:  bash hpc/kissat_check.sh
set -uo pipefail
K=${KISSAT:-$HOME/local/bin/kissat}
fail() { echo "KISSAT CHECK FAILED: $*"; exit 1; }
[ -x "$K" ] || fail "no executable at $K"
v=$("$K" --version 2>&1) || fail "--version did not run (wrong architecture?)"
echo "kissat $v at $(realpath "$K")"; sha256sum "$K"
[ "$v" = "4.0.4" ] || echo "WARNING: version $v, validation used 4.0.4 -- record this"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
printf 'p cnf 2 2\n1 2 0\n-1 0\n' > "$T/sat.cnf"
printf 'p cnf 1 2\n1 0\n-1 0\n'   > "$T/unsat.cnf"
python3 -c "
n=12; v=lambda p,h:p*(n-1)+h+1; c=[]
for p in range(n): c.append([v(p,h) for h in range(n-1)])
for h in range(n-1):
  for a in range(n):
    for b in range(a+1,n): c.append([-v(a,h),-v(b,h)])
print('p cnf',n*(n-1),len(c)); [print(*x,0) for x in c]" > "$T/hard.cnf"
o=$("$K" "$T/sat.cnf");   r=$?; [ $r = 10 ] && grep -q "^s SATISFIABLE"   <<<"$o" || fail "SAT gave exit $r"
echo "  SAT     -> exit 10, s SATISFIABLE      ok"
o=$("$K" "$T/unsat.cnf"); r=$?; [ $r = 20 ] && grep -q "^s UNSATISFIABLE" <<<"$o" || fail "UNSAT gave exit $r"
echo "  UNSAT   -> exit 20, s UNSATISFIABLE    ok"
o=$("$K" --time=1 "$T/hard.cnf"); r=$?
[ $r = 0 ] && grep -q "^s UNKNOWN" <<<"$o" || fail "time limit gave exit $r (driver expects 0 + s UNKNOWN)"
echo "  --time  -> exit 0,  s UNKNOWN          ok   (driver records this as TIMEOUT)"
echo "KISSAT CHECK OK"
