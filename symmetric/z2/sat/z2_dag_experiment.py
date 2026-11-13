#!/usr/bin/env python3
"""Z=2 decomposition experiment.

Question this settles: for an S0-type root (two long transpositions, large
skeleton), does a DAG decomposition beat a monolithic UNSAT proof, given that
each node must enumerate to completion?

Emits, for one root, ONE CNF and THREE DAGs over it:
  A  monolithic   1 node, all clauses            -- the baseline
  B  two-node     skeleton (long edges + lengths) -> remainder
  C  three-node   long-lengths -> placements -> remainder

All three must agree on the reported solution set. Only then is timing
meaningful.

usage:  python3 z2_dag_experiment.py 0,1,3,7 2 outdir
"""
import sys, os, json
from itertools import combinations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import z2_common as Z

def build(F, q):
    F = sorted(F); free = [i for i in range(Z.N) if i not in F]
    seed = [(x, x) for x in F]
    I_F = len(Z.fixed_far_pairs(F))
    nv = 0; var = {}; cl = []; fam = []
    def V(meta):
        nonlocal nv
        nv += 1; var[nv] = meta; return nv
    def C(lits, f):
        cl.append(list(lits)); fam.append(f)

    edge = {}
    for a, b in combinations(free, 2):
        pts = seed + Z.edge_graph_points(a, b); ds = Z.displacements_of(pts)
        if len(set(ds)) != len(ds): continue
        hh = {x: x for x in F}; hh[a] = b; hh[b] = a
        if any(x < y and Z.is_far(x, y) and Z.is_far(hh[x], hh[y])
               and not ((x in F and y in F) or (hh[x] == y and hh[y] == x))
               for x in hh for y in hh): continue
        if q == 0 and Z.is_far(a, b): continue
        edge[(a, b)] = V({"type": "edge", "a": a, "b": b, "length": b - a})
    rep = sorted(edge.values())
    longe = [edge[e] for e in edge if Z.is_far(*e)]

    # clause families, recorded with their index ranges so the DAG can own them
    marks = {}
    def mark(name, fn):
        s = len(cl); fn(); marks[name] = (s, len(cl) - 1) if len(cl) > s else None

    def endpoints():
        for c in free:
            inc = [edge[e] for e in edge if c in e]
            C(inc, "endpoint_alo")
            for u, v in combinations(inc, 2): C([-u, -v], "endpoint_amo")
    mark("endpoint", endpoints)
    def lengths():
        for d in range(1, Z.N):
            es = [edge[e] for e in edge if e[1]-e[0] == d]
            for u, v in combinations(es, 2): C([-u, -v], "length_amo")
    mark("length", lengths)
    def longcard():
        if q == 0:
            for v in longe: C([-v], "long_card")
        else:
            for S in combinations(longe, q+1): C([-v for v in S], "long_card")
            C(longe, "long_card")
    mark("longcard", longcard)
    def costas():
        ek = sorted(edge)
        for i in range(len(ek)):
            for j in range(i+1, len(ek)):
                (a,b),(c2,d2) = ek[i], ek[j]
                if len({a,b,c2,d2}) < 4: continue
                pts = seed + Z.edge_graph_points(a,b) + Z.edge_graph_points(c2,d2)
                ds = Z.displacements_of(pts)
                if len(set(ds)) != len(ds):
                    C([-edge[(a,b)], -edge[(c2,d2)]], "costas_pair"); continue
                hh = {x:x for x in F}; hh[a]=b; hh[b]=a; hh[c2]=d2; hh[d2]=c2
                if any(x<y and Z.is_far(x,y) and Z.is_far(hh[x],hh[y])
                       and not ((x in F and y in F) or (hh[x]==y and hh[y]==x))
                       for x in hh for y in hh):
                    C([-edge[(a,b)], -edge[(c2,d2)]], "orbit_pair")
    mark("costas", costas)
    return dict(F=F, q=q, I_F=I_F, nv=nv, var=var, cl=cl, fam=fam,
                edge=edge, rep=rep, longe=longe, marks=marks)

def rng(m): return f"{m[0]}-{m[1]}" if m else ""

def write(M, out, tag):
    os.makedirs(out, exist_ok=True)
    n = len(M["cl"]); rep = M["rep"]
    with open(f"{out}/model.cnf", "w") as f:
        f.write(f"c z2 root F={M['F']} q={M['q']} I_F={M['I_F']}\n")
        f.write(f"p cnf {M['nv']} {n}\n")
        for c in M["cl"]: f.write(" ".join(map(str,c)) + " 0\n")
    R = f"{rep[0]}-{rep[-1]}"
    L = ",".join(map(str, M["longe"])) if M["longe"] else R
    # A monolithic
    open(f"{out}/dag_A_monolithic.dag","w").write(
        f"DAG-FILE\nNODES:1\nGRAPH:\nCLAUSES:\n0:0-{n-1}\nREPORTING:\n{R}\n")
    # B two-node: long-edge skeleton, then the remainder
    mk = M["marks"]
    sk = f"{rng(mk['longcard'])}"
    open(f"{out}/dag_B_twonode.dag","w").write(
        f"DAG-FILE\nNODES:2\nGRAPH:\n0->1:{L}\nCLAUSES:\n0:{sk}\n1:0-{n-1}\nREPORTING:\n{R}\n")
    # C three-node: skeleton, then endpoint matching, then Costas
    open(f"{out}/dag_C_threenode.dag","w").write(
        f"DAG-FILE\nNODES:3\nGRAPH:\n0->1:{L}\n1->2:{R}\nCLAUSES:\n"
        f"0:{sk}\n1:{rng(mk['endpoint'])},{rng(mk['length'])}\n2:0-{n-1}\nREPORTING:\n{R}\n")
    # D  fan-out + join: one skeleton source, k siblings each holding a DIFFERENT
    #    clause subset and refuting what it can alone, then a join.
    #    Needs only: every message killed by SOME sibling. Not independence.
    ep=mk['endpoint']; co=mk['costas']
    if ep and co:
        e0,e1=ep; c0,c1=co
        em=(e0+e1)//2; cm=(c0+c1)//2
        open(f"{out}/dag_D_fanout.dag","w").write(
            "DAG-FILE\nNODES:5\nGRAPH:\n"
            f"0->1:{L}\n0->2:{L}\n0->3:{L}\n1->4:{R}\n2->4:{R}\n3->4:{R}\n"
            f"CLAUSES:\n0:{sk}\n1:{e0}-{em}\n2:{em+1}-{e1}\n3:{c0}-{c1}\n4:0-{n-1}\n"
            f"REPORTING:\n{R}\n")
        # E  fan-out, wider: split the costas/orbit family too
        open(f"{out}/dag_E_fanout4.dag","w").write(
            "DAG-FILE\nNODES:6\nGRAPH:\n"
            f"0->1:{L}\n0->2:{L}\n0->3:{L}\n0->4:{L}\n"
            f"1->5:{R}\n2->5:{R}\n3->5:{R}\n4->5:{R}\n"
            f"CLAUSES:\n0:{sk}\n1:{e0}-{em}\n2:{em+1}-{e1}\n3:{c0}-{cm}\n4:{cm+1}-{c1}\n5:0-{n-1}\n"
            f"REPORTING:\n{R}\n")
    json.dump({"root":M["F"],"q":M["q"],"I_F":M["I_F"],"vars":M["nv"],
               "clauses":n,"edges":len(rep),"long_edge_vars":len(M["longe"]),
               "families":{k:(v if v else "empty") for k,v in mk.items()}},
              open(f"{out}/meta.json","w"), indent=1)
    return n, len(rep), len(M["longe"])

if __name__ == "__main__":
    F=[int(x) for x in sys.argv[1].split(",")]; q=int(sys.argv[2]); out=sys.argv[3]
    M=build(F,q); n,e,l=write(M,out,"")
    print(f"root F={F} q={q} I_F={M['I_F']}: vars={M['nv']} clauses={n} edges={e} long-edge vars={l}")
    print(f"  wrote model.cnf and dag_A_monolithic / dag_B_twonode / dag_C_threenode")
