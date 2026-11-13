#!/usr/bin/env python3
"""Transpose-symmetric order-32 Costas: CORRECT SAT encoding.

WHY v1 WAS WRONG.  v1 emitted a binary conflict clause only when TWO
transpositions (plus the fixed seed) produced a repeated displacement. A
displacement repeat is a relation among up to FOUR cycles, so v1 was a
relaxation, not the Costas condition. A v1 model was found with 112 repeated
displacements, the first spanning a fixed point and three distinct edges.

THE CORRECT ENCODING.  Introduce a variable per (lag, signed difference):

    d[s][delta]  "some determined pair at lag s has vertical difference delta"

For every ordered pair (x,y) with y-x = s, the value of h(y)-h(x) is determined
by which cycles x and y belong to. So for each such pair and each way of
determining it, add

    (cause)  ->  d[s][delta]

and impose AT MOST ONE d[s][.] per lag... no: at most one PAIR per (s,delta).
Costas says: for each lag s, the |{x : x, x+s both placed}| vertical differences
are pairwise distinct. Equivalently, for each (s,delta), at most one pair
(x,x+s) realises it.

So we need, per (s,delta), an at-most-one over the pair-indicator variables
p[s][x] meaning "pair (x,x+s) has vertical difference delta".
"""
import sys, os, json
from itertools import combinations
N = int(os.environ.get("COSTAS_N", "32"))

def build(F):
    F = sorted(F); free = [i for i in range(N) if i not in F]
    if F and len({b-a for a,b in combinations(F,2)}) != len(F)*(len(F)-1)//2:
        raise SystemExit("F is not a Golomb ruler")
    nv = 0; var = {}; cl = []
    def V(m):
        nonlocal nv; nv += 1; var[nv] = m; return nv
    # x[a][b] : transposition (a,b), a<b, both free
    edge = {}
    for a, b in combinations(free, 2):
        edge[(a,b)] = V({"t":"edge","a":a,"b":b,"len":b-a})
    rep = sorted(edge.values())
    # h[i][j] : h(i) = j.  Needed to express displacements uniformly.
    hv = {}
    for i in range(N):
        for j in range(N):
            if i in F: 
                if i == j: hv[(i,j)] = None      # constant true, no variable
                continue
            if j in F or j == i: continue
            hv[(i,j)] = V({"t":"h","i":i,"j":j})
    def hlit(i,j):
        """literal for h(i)=j, or None if constantly false, True if constant."""
        if i in F: return True if i == j else False
        if j in F or j == i: return False
        return hv[(i,j)]
    # link edges to h
    for (a,b),e in edge.items():
        cl.append([-e, hlit(a,b)]); cl.append([-e, hlit(b,a)])
        cl.append([e, -hlit(a,b)])                 # h(a)=b  ->  edge chosen
    # each free coordinate has exactly one h value
    for i in free:
        row = [hlit(i,j) for j in range(N) if hlit(i,j) not in (True,False)]
        cl.append(row)
        for u,v in combinations(row,2): cl.append([-u,-v])
    # exactly one edge per free coordinate (redundant but strong)
    for c in free:
        inc = [edge[e] for e in edge if c in e]
        cl.append(inc)
        for u,v in combinations(inc,2): cl.append([-u,-v])
    # distinct transposition lengths
    for d in range(1,N):
        es = [edge[e] for e in edge if e[1]-e[0]==d]
        for u,v in combinations(es,2): cl.append([-u,-v])
    # --- the Costas condition, done properly -------------------------------
    # p[s][x][delta] : pair (x,x+s) realises vertical difference delta.
    # It is implied by h(x)=u AND h(x+s)=u+delta.  We introduce it only for
    # realisable (u,delta) combinations, then impose at-most-one per (s,delta).
    pv = {}
    for s in range(1,N):
        bucket = {}
        for x in range(N-s):
            y = x+s
            for u in range(N):
                lu = hlit(x,u)
                if lu is False: continue
                for w in range(N):
                    lw = hlit(y,w)
                    if lw is False: continue
                    delta = w-u
                    key = (s,x,delta)
                    if key not in pv:
                        pv[key] = V({"t":"pair","s":s,"x":x,"delta":delta})
                    P = pv[key]
                    lits = [-P]
                    # P -> (h(x)=u AND h(y)=w) is NOT right (several u give the
                    # same delta).  We need the converse: cause -> P.
                    cause = []
                    if lu is not True: cause.append(-lu)
                    if lw is not True: cause.append(-lw)
                    cl.append(cause + [P])
                    bucket.setdefault(delta, set()).add(P)
        for delta, ps in bucket.items():
            ps = sorted(ps)
            for u,v in combinations(ps,2): cl.append([-u,-v])   # at most one
    return F, nv, var, cl, rep, edge

def write(F, nv, var, cl, rep, out):
    os.makedirs(out, exist_ok=True); n = len(cl)
    with open(f"{out}/model.cnf","w") as f:
        f.write(f"c sym32 v2 region F={F}\np cnf {nv} {n}\n")
        for c in cl: f.write(" ".join(map(str,c))+" 0\n")
    R=f"{rep[0]}-{rep[-1]}"
    open(f"{out}/dag_mono.dag","w").write(
        f"DAG-FILE\nNODES:1\nGRAPH:\nCLAUSES:\n0:0-{n-1}\nREPORTING:\n{R}\n")
    json.dump({"region_F":F,"f":len(F),"vars":nv,"clauses":n,"edge_vars":len(rep),
               "encoding":"v2 pair-indicator, complete Costas"},
              open(f"{out}/meta.json","w"),indent=1)
    return n

if __name__=="__main__":
    arg=sys.argv[1]; out=sys.argv[2]
    F=[] if arg=="-" else [int(x) for x in arg.split(",")]
    F,nv,var,cl,rep,edge=build(F); n=write(F,nv,var,cl,rep,out)
    print(f"region F={F}: vars={nv:,} clauses={n:,} edge vars={len(rep)}")
