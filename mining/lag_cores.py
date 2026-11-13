"""Minimal lag cores of LP certificates: shrink the set of lags whose displacement-capacity constraints are kept,
one lag at a time, while the strong LP stays infeasible. The result is a minimal set of lags whose capacities,
with the placement and pair-marginal structure, already rule the prefix out."""
import sys, random, time, numpy as np
from collections import Counter
from scipy.optimize import linprog
from scipy.sparse import coo_matrix, vstack
def setup(n,seed):
    sys.argv=['lp_relax.py',str(n),'5','1',str(seed)]
    g={'__name__':'lp'}; exec(open('lp_relax.py').read().split("t=time.time()")[0],g); return g
for n,D,samples,seed in [(12,7,20,7),(14,8,12,8)]:
    g=setup(n,seed); NV=g['NV']; yid=g['yid']; xid=g['xid']
    (Aeq,beq),_=g['build'](True)            # equalities only (columns, rows, pair marginals)
    caps={}
    for (i,j,r,s),v in yid.items(): caps.setdefault(j-i,{}).setdefault(s-r,[]).append(v)
    caprows={}
    for d,classes in caps.items():
        rr=[];cc=[]
        for t,(e,vs) in enumerate(classes.items()):
            for v in vs: rr.append(t); cc.append(v)
        caprows[d]=coo_matrix((np.ones(len(rr)),(rr,cc)),shape=(len(classes),NV)).tocsr()
    def feasible(dots,lags):
        lb=np.zeros(NV); ub=np.ones(NV)
        for c,r in dots: lb[xid(c,r)]=1
        Aub=vstack([caprows[d] for d in lags]) if lags else None
        bub=np.ones(Aub.shape[0]) if lags else None
        return linprog(np.zeros(NV),A_ub=Aub,b_ub=bub,A_eq=Aeq,b_eq=beq,bounds=np.column_stack([lb,ub]),method='highs').status==0
    g['ns']['DEPTH']=D; random.seed(seed); cores=[]; t=time.time()
    while len(cores)<samples:
        pr=g['ns']['random_prefix'](); dots=sorted(pr.items())
        if g['S'].solve(assumptions=[g['X'](c,r) for c,r in dots]): continue
        lags=list(range(1,n))
        if feasible(dots,lags): continue        # not LP-certified
        for d in list(lags):
            trial=[x for x in lags if x!=d]
            if not feasible(dots,trial): lags=trial
        cores.append(tuple(lags))
    sz=Counter(len(c) for c in cores); lagfreq=Counter(d for c in cores for d in c)
    print(f"order {n} depth {D}: {len(cores)} LP-certified dead prefixes; minimal lag-core sizes {dict(sorted(sz.items()))}  [{time.time()-t:.0f} s]")
    print(f"   lags appearing in cores: " + ", ".join(f"{d}:{lagfreq[d]}" for d in sorted(lagfreq)))
    print(f"   distinct cores: {len(set(cores))};  most common: {Counter(cores).most_common(4)}")
