#!/usr/bin/env python3
"""Decode a DIMACS assignment into an involution and check it semantically.
Uses plain loops and the direct definitions only — never the orbit formula as
the definition of Z, always as an audited decomposition."""
import json, sys, os
from itertools import combinations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import z2_common as Z

def decode(pkg, true_vars):
    V = json.load(open(f"{pkg}/variables.json"))
    R = json.load(open(f"{pkg}/root.json"))
    F = R["fixed_points"]
    h = [None]*Z.N
    for x in F: h[x] = x
    edges = []
    for v in true_vars:
        m = V["variables"].get(str(v))
        if m and m["type"] == "edge":
            a, b = m["a"], m["b"]; edges.append((a, b))
            h[a] = b; h[b] = a
    return R, F, h, edges

def check(pkg, true_vars):
    R, F, h, edges = decode(pkg, true_vars)
    E = json.load(open(f"{pkg}/expected.json"))
    bad = []
    if any(v is None for v in h): bad.append("not total")
    else:
        if sorted(h) != list(range(Z.N)): bad.append("not a permutation")
        if any(h[h[i]] != i for i in range(Z.N)): bad.append("not an involution")
        if sorted(i for i in range(Z.N) if h[i]==i) != sorted(F): bad.append("fixed points != root")
        if len(edges) != E["transposition_count"]: bad.append(f"transposition count {len(edges)}")
        L = [b-a for a,b in edges]
        if len(set(L)) != len(L): bad.append("repeated transposition length")
        I_F, q, C, Zd = Z.orbit_decomposition(h)
        if q != E["required_long_transpositions"]: bad.append(f"q={q}")
        if C != E["required_cross_orbits"]:        bad.append(f"C={C}")
        if I_F != E["fixed_far_pairs"]:            bad.append(f"I_F={I_F}")
        # Z computed BOTH ways and required to agree
        Zdirect = sum(1 for x in range(Z.N) for y in range(x+1,Z.N)
                      if abs(x-y)>=16 and abs(h[x]-h[y])>=16)
        if Zdirect != I_F + q + 2*C: bad.append(f"lemma violated: {Zdirect} != {I_F}+{q}+2*{C}")
        if Zdirect != E["required_z"]: bad.append(f"Z={Zdirect}")
        if not Z.is_costas(h): bad.append("signed displacements not distinct")
        # canonical re-encoding must reproduce the reported edge set
        canon = {(min(a,h[a]),max(a,h[a])) for a in range(Z.N) if h[a]!=a}
        if canon != set(edges): bad.append("canonical re-encoding != reported edges")
    return (not bad), bad, h

if __name__ == "__main__":
    pkg = sys.argv[1]
    lits = [int(t) for t in sys.stdin.read().split() if t.lstrip('-').isdigit()]
    ok, bad, h = check(pkg, [l for l in lits if l > 0])
    print("SOLUTION VALID" if ok else "SOLUTION INVALID: " + "; ".join(bad))
    if ok: print("h =", " ".join(map(str, h)))
    sys.exit(0 if ok else 1)
