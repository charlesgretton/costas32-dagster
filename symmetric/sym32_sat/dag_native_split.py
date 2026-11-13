#!/usr/bin/env python3
"""Dagster-native certified split: the case split executed BY Dagster.

  node 0 (source)  : ONLY the exactly-one clauses for coordinate i's incident
                     edges, appended to the CNF as redundant copies. Enumerating
                     it gives exactly one message per partner of i, and the
                     solver proves there are no others.
  node 1 (dest)    : the full v2 CNF. Each message is one independent subproblem.
  edge 0->1        : labelled with i's incident edge variables.

Coverage: every model of the full CNF picks exactly one partner for i, so the
messages cover the space. Each message is the same restriction as one child of
split_certified.py -- this is that partition, distributed by Dagster.

Coordinates may be chained (--depth 2 picks a second coordinate) to raise the
message count. The split coordinate is chosen as the free coordinate with the
smallest partner domain unless --coord is given.

usage: dag_native_split.py <F or -> <outdir> [--depth 1|2] [--coord i]
"""
import sys, os, json, argparse
from itertools import combinations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_sym32_v2 import build, N

ap = argparse.ArgumentParser()
ap.add_argument("F"); ap.add_argument("out")
ap.add_argument("--depth", type=int, default=1); ap.add_argument("--coord", type=int)
ap.add_argument("--symbreak", action="store_true", help="add reflection symmetry breaking (rho(F) == F only)")
ap.add_argument("--fix-trans", default="", help="case split: transpositions fixed by unit clauses, e.g. 0-5")
a = ap.parse_args()
F = [] if a.F == "-" else [int(x) for x in a.F.split(",")]
Fb, nv, var, cl, rep, edge = build(F)
if a.symbreak:
    from symbreak import rho_clauses
    cl = cl + rho_clauses(F, var, N)
TR = [tuple(sorted(map(int, t.split("-")))) for t in a.fix_trans.split(",") if t]
for t in TR: cl = cl + [[edge[t]]]                      # the case: transposition t is present
matched = {c for t in TR for c in t}
free = [i for i in range(N) if i not in F]
inc = {c: sorted(v for (x, y), v in edge.items() if c in (x, y)) for c in free}
order = sorted((c for c in free if c not in matched), key=lambda c: (len(inc[c]), c))
coords = [a.coord] if a.coord is not None else []
rules = []

def seed_refutes(x, y):
    """True if transposition (x,y) repeats a displacement with the fixed points alone,
    so a message pairing x with y is refuted immediately by unit propagation."""
    pts = sorted([(f, f) for f in F] + [d for t in TR for d in (t, t[::-1])] + [(x, y), (y, x)])
    d = [(q[0] - p[0], q[1] - p[1]) for p, q in combinations(pts, 2)]
    return len(set(d)) != len(d)

# Second (and later) coordinates: if the new coordinate could pair with an earlier split
# coordinate, that branch fixes only ONE transposition and is never split again -- in the
# cluster runs it was the critical path (113 s and 169 s against a next-hardest 10.8 s).
# So prefer a coordinate whose pairing with every earlier one is refuted by the seed.
for c in order:
    if len(coords) >= a.depth: break
    if c in coords: continue
    if not coords:
        coords.append(c); rules.append("smallest_domain"); continue
    if all(seed_refutes(c, e) for e in coords):
        coords.append(c); rules.append("seed_refutes_pairing")
# Fallback when no coordinate's pairing with ALL earlier ones is refuted (e.g. a third
# coordinate when f=2, or any second coordinate when f=0): take the coordinate refuted
# against the MOST earlier ones, so the fewest messages are left with an unsplit branch.
while len(coords) < a.depth:
    cand = [c for c in order if c not in coords]
    if not cand: break
    c = max(cand, key=lambda c: (sum(seed_refutes(c, e) for e in coords), -order.index(c)))
    k = sum(seed_refutes(c, e) for e in coords)
    coords.append(c); rules.append(f"fallback_refutes_{k}_of_{len(coords)-1}")
n = len(cl); src = []
for c in coords:
    lits = inc[c]
    src.append(lits)                                            # at least one
    for u, v in combinations(lits, 2): src.append([-u, -v])     # at most one
os.makedirs(a.out, exist_ok=True)
with open(f"{a.out}/model.cnf", "w") as f:
    f.write(f"c native split F={F} coords={coords}\np cnf {nv} {n+len(src)}\n")
    for c in cl + src: f.write(" ".join(map(str, c)) + " 0\n")
label = sorted({v for c in coords for v in inc[c]})
R = f"{rep[0]}-{rep[-1]}"
open(f"{a.out}/dag_split.dag", "w").write(
    "DAG-FILE\nNODES:2\nGRAPH:\n0->1:" + ",".join(map(str, label)) +
    f"\nCLAUSES:\n0:{n}-{n+len(src)-1}\n1:0-{n-1}\nREPORTING:\n{R}\n")
open(f"{a.out}/dag_mono.dag", "w").write(
    f"DAG-FILE\nNODES:1\nGRAPH:\nCLAUSES:\n0:0-{n-1}\nREPORTING:\n{R}\n")
exp = 1
for c in coords: exp *= len(inc[c])
json.dump({"region_F": F, "fixed_transpositions": [list(t) for t in TR], "coords": coords, "coord_rules": rules,
           "domains": [len(inc[c]) for c in coords],
           "expected_messages_upper": exp, "orig_clauses": n, "source_clauses": len(src)},
          open(f"{a.out}/split_meta.json", "w"), indent=1)
print(f"F={F} coords={coords} domains={[len(inc[c]) for c in coords]} "
      f"messages<= {exp}  clauses {n}+{len(src)}")
