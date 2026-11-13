"""Mine minimal obstructions: sets of dots, with no repeated displacement, that occur in no Costas array of order n.
1. random prefixes that pass the native checks (distinct displacements, midpoints) and forward checking
   (every unplaced column keeps a legal row);
2. keep those with no Costas completion (UNSAT under assumptions);
3. shrink each to a minimal infeasible set of dots by deletion (each removal re-checked);
4. canonicalise the shape (translate to the origin, least image under the 8 symmetries of its bounding box).
usage: mine_cores.py N DEPTH SAMPLES SEED"""
import sys, random, json, time
from itertools import combinations
from collections import Counter
from pysat.solvers import Solver
n=int(sys.argv[1]); DEPTH=int(sys.argv[2]); SAMPLES=int(sys.argv[3]); SEED=int(sys.argv[4]); random.seed(SEED)
def encode(n):
    X=lambda i,j: i*n+j+1; zid={}; nv=[n*n]
    def Z(k):
        if k not in zid: nv[0]+=1; zid[k]=nv[0]
        return zid[k]
    cnf=[]
    for i in range(n):
        cnf.append([X(i,j) for j in range(n)]); cnf+=[[-X(i,a),-X(i,b)] for a,b in combinations(range(n),2)]
    for j in range(n):
        cnf.append([X(i,j) for i in range(n)]); cnf+=[[-X(a,j),-X(b,j)] for a,b in combinations(range(n),2)]
    for d in range(1,n):
        for i in range(n-d):
            for a in range(n):
                for b in range(n):
                    if a!=b: cnf.append([-X(i,a),-X(i+d,b),Z((d,i,b-a))])
        for e in [x for x in range(-(n-1),n) if x]:
            st=[i for i in range(n-d) if (d,i,e) in zid]; cnf+=[[-Z((d,i,e)),-Z((d,k,e))] for i,k in combinations(st,2)]
    return cnf, X
cnf,X=encode(n); S=Solver(name='cadical195',bootstrap_with=cnf)
def legal(p,c,r):       # can column c take row r, given dots p (dict col->row)?
    if r in p.values(): return False
    seen={}
    for c2,r2 in p.items():
        lag=abs(c-c2); d=(r-r2) if c>c2 else (r2-r)
        if (lag,d) in seen: return False
        seen[(lag,d)]=1
    D={}
    for (a,ra),(b,rb) in combinations(sorted(p.items()),2): D[(b-a,rb-ra)]=1
    return all(k not in D for k in seen)
def random_prefix():
    while True:
        p={}
        for c in range(DEPTH):
            rows=[r for r in range(n) if legal(p,c,r)]
            if not rows: break
            p[c]=random.choice(rows)
        if len(p)<DEPTH: continue
        if all(any(legal(p,c,r) for r in range(n)) for c in range(DEPTH,n)): return p   # forward checking passes
def feasible(dots): return S.solve(assumptions=[X(c,r) for c,r in dots])
def minimise(dots):
    core=list(dots)
    for d in list(core):
        trial=[x for x in core if x!=d]
        if not feasible(trial): core=trial
    return core
def shape(dots):
    c0=min(c for c,_ in dots); r0=min(r for _,r in dots)
    P=[(c-c0,r-r0) for c,r in dots]; W=max(c for c,_ in P); H=max(r for _,r in P)
    ims=[]
    for t in range(8):
        Q=[]
        for c,r in P:
            x,y,w,h=c,r,W,H
            if t&4: x,y,w,h=y,x,H,W
            if t&1: x=w-x
            if t&2: y=h-y
            Q.append((x,y))
        ims.append(tuple(sorted(Q)))
    return min(ims)
t0=time.time(); tried=sat=0; cores=[]
while len(cores)<SAMPLES:
    p=random_prefix(); tried+=1
    dots=sorted(p.items())
    if feasible(dots): sat+=1; continue
    m=minimise(dots); cores.append(m)
sizes=Counter(len(m) for m in cores); shapes=Counter(shape(m) for m in cores)
edge=sum(any(c in (0,n-1) or r in (0,n-1) for c,r in m) for m in cores)
print(f"n={n} depth={DEPTH}: {tried} prefixes passing native checks and forward checking; {sat} completable, {len(cores)} dead")
print(f"minimal obstruction sizes (dots): {dict(sorted(sizes.items()))}")
print(f"distinct shapes: {len(shapes)} among {len(cores)} obstructions; touching the board's edge: {edge}/{len(cores)}")
for sh,k in shapes.most_common(6): print(f"   x{k}: {sh}")
print(f"seconds: {time.time()-t0:.0f}")
json.dump({"n":n,"depth":DEPTH,"cores":cores},open(f"/home/claude/costas32/mining/cores_n{n}_d{DEPTH}_s{SEED}.json","w"))
