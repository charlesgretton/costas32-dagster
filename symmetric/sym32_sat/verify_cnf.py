#!/usr/bin/env python3
"""Regenerate region CNFs from a ledger and check them against the recorded digests.

The driver deletes each region's CNF after solving it. That is safe only because
the CNF is a deterministic function of the fixed-point set and the generator, and
the ledger records both digests. This script proves it for any ledger rows.

usage: COSTAS_N=32 verify_cnf.py <ledger.jsonl> [max_regions]
"""
import sys, os, json, hashlib, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_sym32_v2 import build, write
here = os.path.dirname(os.path.abspath(__file__))
gen = hashlib.sha256(open(f"{here}/gen_sym32_v2.py", "rb").read()).hexdigest()
seen = {}; lim = int(sys.argv[2]) if len(sys.argv) > 2 else 10**9
for l in open(sys.argv[1]):
    r = json.loads(l)
    if "parent_cnf_sha256" in r and r["region_id"] not in seen and len(seen) < lim:
        seen[r["region_id"]] = r
bad = 0
for rid, r in seen.items():
    if r.get("generator_sha256") != gen:
        print(f"{rid}: GENERATOR DIFFERS -- ledger {r.get('generator_sha256','')[:12]} vs this tree {gen[:12]}"); bad += 1; continue
    d = tempfile.mkdtemp()
    try:
        F, nv, var, cl, rep, edge = build(r["fixed_points"])
        if r.get("symmetry_breaking") == "rho":
            from symbreak import rho_clauses; from gen_sym32_v2 import N as _N
            cl = cl + rho_clauses(r["fixed_points"], var, _N)
        for t in r.get("fixed_transpositions") or []: cl = cl + [[edge[tuple(t)]]]
        write(F, nv, var, cl, rep, d)
        got = hashlib.sha256(open(f"{d}/model.cnf", "rb").read()).hexdigest()
    finally:
        shutil.rmtree(d)
    ok = got == r["parent_cnf_sha256"]; bad += not ok
    print(f"{rid}: {'OK' if ok else 'MISMATCH'}  {got[:16]}")
print(f"\nVERIFY {'PASS' if bad == 0 else 'FAIL'}: {len(seen)-bad}/{len(seen)} regions regenerate to their recorded digest")
sys.exit(1 if bad else 0)
