"""Threshold confirmation for the pair-marginal LP (LP-2), with LP-0 (assignment only) and LP-1 (McCormick) controls.
Sampling: random walk over locally admissible prefixes (native checks + forward checking), recording the log of the
product of branching factors so that results can be reweighted to the uniform depth layer; dead prefixes also record
their native subtree size (node-weighted view). Ground truth: catalogue containment (n<=13) or CaDiCaL (n>=14).
Output: one JSON line per prefix.  usage: threshold.py N DEPTHS DEAD_PER_CELL ALIVE_PER_CELL SEED OUTFILE"""
import sys, random, json, math, subprocess, time, numpy as np
from itertools import combinations
from scipy.optimize import linprog
n=int(sys.argv[1]); DEPTHS=[int(x) for x in sys.argv[2].split(',')]; NDEAD=int(sys.argv[3]); NALIVE=int(sys.argv[4])
random.seed(int(sys.argv[5])); OUT=open(sys.argv[6],'a')
sys.argv=['lp_relax.py',str(n),'5','1','1']
g={'__name__':'lp'}; exec(open('lp_relax.py').read().split("t=time.time()")[0],g)
legal=g['ns']['legal']; models={'LP1':g['models']['weak'],'LP2':g['models']['strong']}
lp0=g['build'](True)[0]                       # equalities only; LP-0 uses just the column/row rows below
NV=g['NV']; xid=g['xid']
def lp0_feasible(dots):
    A=lp0[0][:2*n]; b=lp0[1][:2*n]; lb=np.zeros(NV); ub=np.ones(NV)
    for c,r in dots: lb[xid(c,r)]=1
    return linprog(np.zeros(NV),A_eq=A,b_eq=b,bounds=np.column_stack([lb,ub]),method='highs').status==0
catalogue=None
if n<=13:
    A=[tuple(map(int,l.split(','))) for l in subprocess.run(['/tmp/listall','exact',str(n)],capture_output=True,text=True).stdout.splitlines() if ',' in l]
    ix={}
    for k,a in enumerate(A):
        for c,r in enumerate(a): ix.setdefault((c,r),set()).add(k)
    def completable(dots):
        s=None
        for d in dots:
            t=ix.get(d,set()); s=t if s is None else s&t
            if not s: return False
        return True
else:
    def completable(dots): return g['S'].solve(assumptions=[g['X'](c,r) for c,r in dots])
def walk(D):
    while True:
        p={}; logw=0.0
        for c in range(D):
            rows=[r for r in range(n) if legal(p,c,r)]
            if not rows: break
            logw+=math.log(len(rows)); p[c]=random.choice(rows)
        if len(p)<D: continue
        if all(any(legal(p,c,r) for r in range(n)) for c in range(D,n)): return sorted(p.items()), logw
t0=time.time()
for D in DEPTHS:
    nd=na=0
    while nd<NDEAD or na<NALIVE:
        dots,logw=walk(D); comp=completable(dots)
        if comp and na>=NALIVE: continue
        if (not comp) and nd>=NDEAD: continue
        rec={'n':n,'k':D,'logw':logw,'dead':not comp,'LP0':not lp0_feasible(dots),
             'LP1':not g['lp_feasible'](models['LP1'],dots),'LP2':not g['lp_feasible'](models['LP2'],dots)}
        if not comp: rec['subtree']=int(subprocess.run(['/tmp/subtree',str(n)]+[str(r) for _,r in dots],capture_output=True,text=True).stdout)
        if comp and rec['LP2']: print("HALT: a completable prefix was cut by LP-2", dots, flush=True); sys.exit(2)
        OUT.write(json.dumps(rec)+"\n"); OUT.flush()
        nd+= not comp; na+= comp
    print(f"n={n} k={D} done ({time.time()-t0:.0f} s)", flush=True)
