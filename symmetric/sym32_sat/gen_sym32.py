#!/usr/bin/env python3
"""Transpose-symmetric order-32 Costas: full-space SAT campaign generator.

THE PARTITION.  Every transpose-symmetric permutation has exactly one
fixed-point set F, and by the Golomb-ruler lemma F must be a Golomb ruler with
f = |F| in {0,2,4,6} (f=8 needs span 34 > 31; f odd is impossible for even n).
Reflection-canonicalising gives

    f=0:      1     f=2:    256     f=4: 13,587     f=6: 31,103
    total 44,947 regions, disjoint and exhaustive.

That is a mathematically forced partition of the search space -- not an imposed
cut. Each region is a self-contained UNSAT proof over the FULL clause set.
So: split the space, never the clauses; every sibling terminal; no join; no
cross-node clause learning.

usage:  gen_sym32.py <a,b,c,d | -> out/       ('-' means f=0)
"""
import sys, os, json
from itertools import combinations
N = 32

def far(x, y): return abs(x - y) >= 16
def disp(pts):
    out = []
    for (x, hx), (y, hy) in combinations(sorted(pts), 2):
        lo, hi = (x, y) if x < y else (y, x)
        out.append((hi - lo, (hy - hx) if x < y else (hx - hy)))
    return out

def build(F):
    F = sorted(F); free = [i for i in range(N) if i not in F]
    seed = [(x, x) for x in F]
    if F and len({b-a for a, b in combinations(F, 2)}) != len(F)*(len(F)-1)//2:
        raise SystemExit("F is not a Golomb ruler -- region is empty by lemma D2")
    nv = 0; var = {}; cl = []
    def V(m):
        nonlocal nv; nv += 1; var[nv] = m; return nv
    edge = {}
    for a, b in combinations(free, 2):
        d = disp(seed + [(a, b), (b, a)])
        if len(set(d)) != len(d): continue          # incompatible with the seed
        edge[(a, b)] = V({"t": "edge", "a": a, "b": b, "len": b - a})
    rep = sorted(edge.values())
    # every free coordinate in exactly one transposition
    for c in free:
        inc = [edge[e] for e in edge if c in e]
        cl.append(inc)
        for u, v in combinations(inc, 2): cl.append([-u, -v])
    # Costas forces distinct transposition lengths
    for dd in range(1, N):
        es = [edge[e] for e in edge if e[1]-e[0] == dd]
        for u, v in combinations(es, 2): cl.append([-u, -v])
    # pairwise Costas conflicts, generated straight from the definition
    ek = sorted(edge)
    for i in range(len(ek)):
        for j in range(i+1, len(ek)):
            (a, b), (c, d2) = ek[i], ek[j]
            if len({a, b, c, d2}) < 4: continue
            ds = disp(seed + [(a, b), (b, a), (c, d2), (d2, c)])
            if len(set(ds)) != len(ds):
                cl.append([-edge[(a, b)], -edge[(c, d2)]])
    return F, nv, var, cl, rep, edge

def write(F, nv, var, cl, rep, out, ranks):
    os.makedirs(out, exist_ok=True); n = len(cl)
    with open(f"{out}/model.cnf", "w") as f:
        f.write(f"c sym32 region F={F}\np cnf {nv} {n}\n")
        for c in cl: f.write(" ".join(map(str, c)) + " 0\n")
    R = f"{rep[0]}-{rep[-1]}"
    # monolithic baseline
    open(f"{out}/dag_mono.dag", "w").write(
        f"DAG-FILE\nNODES:1\nGRAPH:\nCLAUSES:\n0:0-{n-1}\nREPORTING:\n{R}\n")
    # space-split, k terminal siblings, FULL clauses each, NO join.
    # Siblings are split on the lowest free coordinate's incident edges: a
    # disjoint, exhaustive case split, so global UNSAT = every sibling UNSAT.
    first = min(i for i in range(N) if i not in F)
    inc = sorted(k for k in var if var[k]["t"] == "edge"
                 and first in (var[k]["a"], var[k]["b"]))
    k = min(ranks, len(inc))
    grp = [inc[i::k] for i in range(k)]
    g = "\n".join(f"0->{i+1}:" + ",".join(map(str, x)) for i, x in enumerate(grp))
    c = "\n".join([f"0:0-{n-1}"] + [f"{i+1}:0-{n-1}" for i in range(k)])
    open(f"{out}/dag_split{k}.dag", "w").write(
        f"DAG-FILE\nNODES:{k+1}\nGRAPH:\n{g}\nCLAUSES:\n{c}\nREPORTING:\n{R}\n")
    json.dump({"region_F": F, "f": len(F), "vars": nv, "clauses": n,
               "edge_vars": len(rep), "split_on_coordinate": first,
               "split_siblings": k}, open(f"{out}/meta.json", "w"), indent=1)
    return n, len(rep), k, first

if __name__ == "__main__":
    arg = sys.argv[1]; out = sys.argv[2]; ranks = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    F = [] if arg == "-" else [int(x) for x in arg.split(",")]
    F, nv, var, cl, rep, edge = build(F)
    n, e, k, first = write(F, nv, var, cl, rep, out, ranks)
    print(f"region F={F} (f={len(F)}): vars={nv} clauses={n:,} edge vars={e}")
    print(f"  split on coordinate {first}: {k} terminal siblings, full clauses, no join")
