#!/usr/bin/env python3
"""Z=2 Type S SAT model generator.

One reflection-canonical fixed-point root -> one self-contained model package.
The CNF and the DAG are both emitted from ONE authoritative intermediate
representation, never generated independently of each other.

Variables
  x_ab   primary transposition edge, a<b, a,b not fixed        <- REPORTING
  y_d    length d is used   (EQUIVALENCE, not implication)
  aux    cardinality-encoding auxiliaries                      (never reported)

Type S cell: I_F + q = 2, C = 0.  Every cross large-large orbit is forbidden,
so the Z condition compiles almost entirely into unit and binary clauses.
"""
import json, sys, hashlib, os
from itertools import combinations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import z2_common as Z

class Model:
    def __init__(self, F, q):
        self.F = sorted(F); self.q = q
        self.nv = 0; self.vars = {}; self.clauses = []; self.fam = []
    def newvar(self, meta):
        self.nv += 1; self.vars[self.nv] = meta; return self.nv
    def add(self, lits, family):
        self.clauses.append(list(lits)); self.fam.append(family)

def build(F, q, cell_label):
    F = sorted(F); f = len(F); m = Z    # shorthand
    I_F = len(Z.fixed_far_pairs(F))
    assert I_F + q == 2, f"Type S needs I_F+q=2, got I_F={I_F} q={q}"
    M = Model(F, q)
    free = [i for i in range(Z.N) if i not in F]
    seed_pts = [(x, x) for x in F]

    # --- primary edge variables, with mathematically impossible edges dropped
    edge = {}
    dropped = []
    for a, b in combinations(free, 2):
        pts = seed_pts + Z.edge_graph_points(a, b)
        ds = Z.displacements_of(pts)
        if len(set(ds)) != len(ds):                      # self-conflict with seed
            dropped.append((a, b, "seed_costas")); continue
        # Type S: this edge must not create a cross large-large orbit with the seed
        hh = {x: x for x in F}; hh[a] = b; hh[b] = a
        bad = False
        for x in list(hh):
            for y in list(hh):
                if x < y and Z.is_far(x, y) and Z.is_far(hh[x], hh[y]):
                    # allowed only if it is a singleton witness
                    if not ((x in F and y in F) or (hh[x] == y and hh[y] == x)):
                        bad = True
        if bad: dropped.append((a, b, "seed_cross_orbit")); continue
        if q == 0 and Z.is_far(a, b):
            dropped.append((a, b, "long_edge_forbidden_q0")); continue
        edge[(a, b)] = M.newvar({"type": "edge", "a": a, "b": b,
                                 "length": b - a, "reporting": True})
    reporting = sorted(edge.values())

    # --- length variables, as EQUIVALENCES
    lenvar = {}
    for d in range(1, Z.N):
        es = [edge[e] for e in edge if e[1]-e[0] == d]
        if not es: continue
        yd = M.newvar({"type": "length", "length": d, "reporting": False})
        lenvar[d] = yd
        for v in es: M.add([-v, yd], "length_edge_implies_selected")
        M.add([-yd] + es, "length_selected_implies_edge")

    # --- each free coordinate in exactly one edge  (pairwise AMO + ALO)
    for c in free:
        inc = [edge[e] for e in edge if c in e]
        M.add(inc, "endpoint_at_least_one")
        for u, v in combinations(inc, 2):
            M.add([-u, -v], "endpoint_at_most_one")

    # --- at most one edge per length (Costas forces distinct lengths)
    for d, yd in lenvar.items():
        es = [edge[e] for e in edge if e[1]-e[0] == d]
        for u, v in combinations(es, 2):
            M.add([-u, -v], "length_at_most_one")

    # --- long-length cardinality: exactly q long lengths used
    longs = [lenvar[d] for d in lenvar if d >= Z.FAR]
    if q == 0:
        for v in longs: M.add([-v], "long_length_cardinality")
    else:
        for S in combinations(longs, q+1): M.add([-v for v in S], "long_length_cardinality")
        M.add(longs, "long_length_cardinality") if q >= 1 else None

    # --- pairwise Costas conflicts and Type S cross-orbit exclusions
    ek = sorted(edge)
    for i in range(len(ek)):
        for j in range(i+1, len(ek)):
            (a, b), (c, d) = ek[i], ek[j]
            if len({a, b, c, d}) < 4: continue          # share an endpoint: already excluded
            pts = seed_pts + Z.edge_graph_points(a, b) + Z.edge_graph_points(c, d)
            ds = Z.displacements_of(pts)
            if len(set(ds)) != len(ds):
                M.add([-edge[(a,b)], -edge[(c,d)]], "costas_pair_conflict"); continue
            hh = {x: x for x in F}; hh[a]=b; hh[b]=a; hh[c]=d; hh[d]=c
            bad = False
            for x in list(hh):
                for y in list(hh):
                    if x < y and Z.is_far(x, y) and Z.is_far(hh[x], hh[y]):
                        if not ((x in F and y in F) or (hh[x]==y and hh[y]==x)):
                            bad = True
            if bad:
                M.add([-edge[(a,b)], -edge[(c,d)]], "type_s_pair_orbit_exclusion")
    return M, edge, lenvar, reporting, dropped, I_F

def emit(M, edge, lenvar, reporting, dropped, I_F, F, q, out, cell):
    os.makedirs(out, exist_ok=True)
    f = len(F)
    root = {"schema":"costas32-z2-root-v1","order":Z.N,
      "cell":{"z":2,"type":"S","fixed_count":f,"fixed_far_pairs":I_F,
              "required_long_transpositions":q,"required_cross_orbits":0},
      "root_key":cell,"fixed_points":F,"fixed_sum":sum(F),
      "even_fixed_points":sum(1 for x in F if x%2==0),
      "fixed_differences":sorted({b-a for a,b in combinations(F,2)}),
      "fixed_far_pair_list":[list(p) for p in Z.fixed_far_pairs(F)],
      "transposition_count":(Z.N-f)//2,
      "omitted_short_lengths":Z.omitted_short_count(f,q)}
    json.dump(root, open(f"{out}/root.json","w"), indent=1)
    json.dump({"schema":"costas32-z2-variables-v1","maximum_variable":M.nv,
      "reporting_variables":{"type":"edge","ids":reporting},
      "variables":{str(k):v for k,v in M.vars.items()},
      "dropped_edges":[{"a":a,"b":b,"reason":r} for a,b,r in dropped]},
      open(f"{out}/variables.json","w"), indent=1)
    fams={}
    for i,fm in enumerate(M.fam): fams.setdefault(fm,[]).append(i)
    json.dump({"schema":"costas32-z2-clauses-v1","index_base":0,
      "number_of_clauses":len(M.clauses),
      "families":{k:{"count":len(v),"first":v[0],"last":v[-1]} for k,v in fams.items()}},
      open(f"{out}/clauses.json","w"), indent=1)
    with open(f"{out}/model.cnf","w") as fh:
        fh.write(f"c {cell}\nc REPORTING {reporting[0]}-{reporting[-1]}\n")
        fh.write(f"p cnf {M.nv} {len(M.clauses)}\n")
        for cl in M.clauses: fh.write(" ".join(map(str,cl))+" 0\n")
    json.dump({"schema":"costas32-z2-expected-v1","root_key":cell,"order":Z.N,
      "fixed_count":f,"fixed_far_pairs":I_F,"required_long_transpositions":q,
      "required_cross_orbits":0,"transposition_count":(Z.N-f)//2,"required_z":2,
      "primary_edge_variables":len(reporting),"reporting_variables":len(reporting),
      "positive_fixture":False,
      "note":"primary edge count is AFTER dropping mathematically impossible edges; do not hard-code"},
      open(f"{out}/expected.json","w"), indent=1)
    return len(reporting), M.nv, len(M.clauses), fams

if __name__ == "__main__":
    F = [int(x) for x in sys.argv[1].split(",")]
    q = int(sys.argv[2]); out = sys.argv[3]
    I_F = len(Z.fixed_far_pairs(F))
    cell = f"Z2-S{I_F}-f{len(F):02d}-" + "".join(f"{x:02d}" for x in F)
    M, edge, lenvar, rep, dropped, I_F = build(F, q, cell)
    nr, nv, nc, fams = emit(M, edge, lenvar, rep, dropped, I_F, F, q, out, cell)
    print(f"{cell}\n  edges kept {nr}  dropped {len(dropped)}  vars {nv}  clauses {nc}")
    for k,v in sorted(fams.items()): print(f"    {k:<38} {len(v):>7}")
