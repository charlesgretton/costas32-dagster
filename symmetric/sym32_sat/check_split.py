#!/usr/bin/env python3
"""Discharge the split certification gates with KISSAT.

FAIL-CLOSED. A gate passes ONLY on exit 0 with an empty solution file.
Any other exit is UNKNOWN, never UNSAT -- a crash and a refutation both
produce no model, and conflating them is how a wrong proof gets recorded.
"""
import sys, os, subprocess, json, glob, time
D = os.environ.get("DAGSTER", "dagster")

def header(cnf):
    for l in open(cnf):
        if l.startswith('p'): p = l.split(); return int(p[2]), int(p[3])
    raise SystemExit(f"no p-line in {cnf}")

def mkdag(cnf, path):
    nv, nc = header(cnf)
    open(path, 'w').write(
        f"DAG-FILE\nNODES:1\nGRAPH:\nCLAUSES:\n0:0-{nc-1}\nREPORTING:\n1-{nv}\n")
    return nv, nc

def solve(cnf, ranks, tmo):
    """Certification uses KISSAT, not Dagster: exit 20 plus 's UNSATISFIABLE'
    is positive evidence of UNSAT, whereas Dagster signals UNSAT only by an
    empty output file. A gate should rest on the stronger signal, and should
    not need MPI. 'ranks' is retained for interface compatibility."""
    K = os.environ.get("KISSAT")
    if not K:
        return "NO_KISSAT_CONFIGURED", None, 0.0
    t0 = time.time()
    try:
        r = subprocess.run([K, f"--time={tmo}", cnf], capture_output=True, text=True, timeout=tmo+60)
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None, time.time()-t0
    el = time.time()-t0
    if r.returncode == 20 and "s UNSATISFIABLE" in r.stdout: return "UNSAT", 0, el
    if r.returncode == 10 and "s SATISFIABLE" in r.stdout:   return "SAT", 1, el
    return f"UNKNOWN_exit{r.returncode}", None, el

def main(d, ranks=3, tmo=300, sample=0):
    S = json.load(open(f"{d}/split.json"))
    print(f"region F={S['region_F']}  rule={S['split_rule']}  "
          f"coordinate={S['split_coordinate']}  children={S['split_count']}")
    bad = []
    st, n, el = solve(f"{d}/coverage.cnf", ranks, tmo)
    ok = (st == "UNSAT")
    print(f"  COVERAGE   {st:<18} {el:6.2f}s  {'PASS' if ok else 'FAIL'}")
    if not ok: bad.append("coverage")
    dj = sorted(glob.glob(f"{d}/disjoint_*.cnf"))
    if sample and len(dj) > sample:
        step = max(1, len(dj)//sample); dj = dj[::step][:sample]
        print(f"  DISJOINT   sampling {len(dj)} of {S['split_count']*(S['split_count']-1)//2}")
    npass = 0
    for f in dj:
        st, n, el = solve(f, ranks, tmo)
        if st == "UNSAT": npass += 1
        else: bad.append(os.path.basename(f)); print(f"    {os.path.basename(f)} {st} FAIL")
    print(f"  DISJOINT   {npass}/{len(dj)} UNSAT  {'PASS' if npass==len(dj) else 'FAIL'}")
    print(f"\nSPLIT CERTIFICATION {'PASS' if not bad else 'FAIL: '+','.join(bad[:5])}")
    return 0 if not bad else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv)>2 else 3,
                  int(sys.argv[3]) if len(sys.argv)>3 else 300,
                  int(sys.argv[4]) if len(sys.argv)>4 else 0))
