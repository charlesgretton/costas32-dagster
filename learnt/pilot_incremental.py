"""Pilot: does a persistent CDCL solver reuse reasoning across related Costas subproblems?
Measured in solver operations (conflicts, propagations), which exclude formula loading, so any saving is
reasoning carried over between subproblems (learnt clauses or heuristic state), not setup.
Encoding (transparent): x[i][j] <=> pi(i)=j;  z[d,i,e] <=> pi(i+d)-pi(i)=e, implied by placements;
at most one start position per displacement class (d,e). First column restricted to p0 <= (n-1)/2."""
import sys, random, time
from itertools import combinations
from pysat.solvers import Solver
n=int(sys.argv[1]) if len(sys.argv)>1 else 24
PARENT_DEPTH=int(sys.argv[2]) if len(sys.argv)>2 else 2
NPARENTS=int(sys.argv[3]) if len(sys.argv)>3 else 12
SEED=int(sys.argv[4]) if len(sys.argv)>4 else 1
random.seed(SEED)
X=lambda i,j: i*n+j+1
zid={}; nv=n*n
def Z(d,i,e):
    global nv
    k=(d,i,e)
    if k not in zid: nv+=1; zid[k]=nv
    return zid[k]
cnf=[]
for i in range(n):
    cnf.append([X(i,j) for j in range(n)]); cnf+= [[-X(i,a),-X(i,b)] for a,b in combinations(range(n),2)]
for j in range(n):
    cnf.append([X(i,j) for i in range(n)]); cnf+= [[-X(a,j),-X(b,j)] for a,b in combinations(range(n),2)]
cnf+= [[-X(0,a)] for a in range(n) if a>(n-1)//2]
for d in range(1,n):
    for i in range(n-d):
        for a in range(n):
            for b in range(n):
                if a!=b: cnf.append([-X(i,a),-X(i+d,b),Z(d,i,b-a)])
    for e in [x for x in range(-(n-1),n) if x]:
        starts=[i for i in range(n-d) if (d,i,e) in zid]
        cnf+= [[-Z(d,i,e),-Z(d,k,e)] for i,k in combinations(starts,2)]
# native search, for valid prefixes and subtree sizes
def ok(p,r):
    c=len(p)
    if r in p: return False
    if c==0 and r>(n-1)//2: return False
    for i in range(c):
        d=c-i; e=r-p[i]
        for k in range(i):          # same lag d among earlier pairs
            if k+d<c and p[k+d]-p[k]==e: return False
    return True
def ok_fast(p,r,used):
    c=len(p)
    if r in p or (c==0 and r>(n-1)//2): return False
    return all((c-i, r-p[i]) not in used for i in range(c))
def subtree(p):
    used={(j-i,p[j]-p[i]) for i in range(len(p)) for j in range(i+1,len(p))}
    cnt=0; stack=[]
    def rec(p,used):
        nonlocal cnt
        if len(p)==n: return
        for r in range(n):
            if ok_fast(p,r,used):
                new=[(len(p)-i, r-p[i]) for i in range(len(p))]
                cnt+=1; used.update(new); p.append(r); rec(p,used); p.pop(); used.difference_update(new)
    rec(list(p),used); return cnt
def children(p):
    used={(j-i,p[j]-p[i]) for i in range(len(p)) for j in range(i+1,len(p))}
    return [p+[r] for r in range(n) if ok_fast(p,r,used)]
def random_prefix(depth):
    while True:
        p=[]
        while len(p)<depth:
            ch=children(p)
            if not ch: break
            p=random.choice(ch)
        if len(p)==depth: return p
parents=[]; seen=set()
while len(parents)<NPARENTS:
    p=random_prefix(PARENT_DEPTH)
    if tuple(p) not in seen: seen.add(tuple(p)); parents.append(p)
families=[(p,children(p)) for p in parents]
cubes=[c for _,ch in families for c in ch]
assume=lambda c: [X(i,c[i]) for i in range(len(c))]
print(f"n={n}: {nv} variables, {len(cnf)} clauses; {len(parents)} parents at depth {PARENT_DEPTH}, {len(cubes)} child cubes")
import subprocess, os
t=time.time(); native=[int(subprocess.run([os.path.join(os.path.dirname(os.path.abspath(__file__)),'subtree'),str(n)]+[str(v) for v in c],capture_output=True,text=True).stdout) for c in cubes]
print(f"native search: {sum(native):,} nodes below the cubes in total ({time.time()-t:.0f} s)", flush=True)
def stats_diff(a,b): return {k:b[k]-a.get(k,0) for k in ('conflicts','propagations','decisions')}
def run_fresh():
    out=[]
    for c in cubes:
        s=Solver(name='cadical195',bootstrap_with=cnf); r=s.solve(assumptions=assume(c)); out.append((r,stats_diff({},s.accum_stats()))); s.delete()
    return out
def run_family(order_seed):
    rnd=random.Random(order_seed); out={}
    for p,ch in families:
        s=Solver(name='cadical195',bootstrap_with=cnf); prev={}
        seq=list(ch); rnd.shuffle(seq)
        for k,c in enumerate(seq):
            r=s.solve(assumptions=assume(c)); st=s.accum_stats(); out[tuple(c)]=(r,stats_diff(prev,st),k); prev=dict(st)
        s.delete()
    return [out[tuple(c)] for c in cubes]
def run_global(order_seed):
    rnd=random.Random(order_seed); seq=list(range(len(cubes))); rnd.shuffle(seq); out={}
    s=Solver(name='cadical195',bootstrap_with=cnf); prev={}
    for k in seq:
        r=s.solve(assumptions=assume(cubes[k])); st=s.accum_stats(); out[k]=(r,stats_diff(prev,st)); prev=dict(st)
    s.delete(); return [out[k] for k in range(len(cubes))]
t=time.time(); F=run_fresh(); tf=time.time()-t
t=time.time(); P1=run_family(11); P2=run_family(12); tp=(time.time()-t)/2
t=time.time(); G=run_global(13); tg=time.time()-t
assert [a[0] for a in F]==[a[0] for a in P1]==[a[0] for a in P2]==[a[0] for a in G], "verdicts disagree"
nsat=sum(a[0] for a in F); print(f"verdicts agree in every mode: {nsat} SAT, {len(cubes)-nsat} UNSAT")
tot=lambda R,k: sum(a[1][k] for a in R)
print(f"{'mode':<34} {'conflicts':>11} {'propagations':>14} {'decisions':>11} {'seconds':>8}")
for name,R,tt in [("fresh solver per cube",F,tf),("persistent per sibling family (A)",P1,tp),("persistent per sibling family (B)",P2,tp),("one persistent solver, all cubes",G,tg)]:
    print(f"{name:<34} {tot(R,'conflicts'):>11,} {tot(R,'propagations'):>14,} {tot(R,'decisions'):>11,} {tt:>8.1f}")
for name,R in [("family (A)",P1),("family (B)",P2),("global",G)]:
    print(f"fresh / {name}: conflicts x{tot(F,'conflicts')/max(1,tot(R,'conflicts')):.2f}, propagations x{tot(F,'propagations')/max(1,tot(R,'propagations')):.2f}")
# learning curve within families: conflicts of the k-th sibling, relative to the same cube solved fresh
from collections import defaultdict
pos=defaultdict(lambda:[0,0])
for f,p in zip(F,P1): pos[p[2]][0]+=f[1]['conflicts']; pos[p[2]][1]+=p[1]['conflicts']
print("within-family learning curve, family (A): sibling position -> fresh conflicts / persistent conflicts")
print("  "+"  ".join(f"{k}:{v[0]/max(1,v[1]):.2f}" for k,v in sorted(pos.items()) if k<16))
print(f"native nodes per conflict (fresh): {sum(native)/max(1,tot(F,'conflicts')):.1f}")
