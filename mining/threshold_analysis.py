import json, math, numpy as np
from collections import defaultdict
from scipy.optimize import minimize
R=[json.loads(l) for l in open('thr.jsonl')]
dead=[r for r in R if r['dead']]; alive=[r for r in R if not r['dead']]
print(f"{len(R)} prefixes: {len(dead)} dead, {len(alive)} completable; completable cut by LP-2: {sum(r['LP2'] for r in alive)}; by LP-1: {sum(r['LP1'] for r in alive)}; LP-0 detections among dead: {sum(r['LP0'] for r in dead)}")
cells=defaultdict(list)
for r in dead: cells[(r['n'],r['k'])].append(r)
print(f"\n{'n':>3} {'k':>3} {'k/n':>6} {'dead':>5} {'LP-1':>6} {'LP-2 raw':>9} {'LP-2 uniform':>13} {'LP-2 node-wt':>13} {'95% upper miss (if 100%)':>25}")
for (n,k),rs in sorted(cells.items()):
    m=len(rs); l1=sum(r['LP1'] for r in rs)/m; l2=sum(r['LP2'] for r in rs)/m
    w=np.exp(np.array([r['logw'] for r in rs])-max(r['logw'] for r in rs)); u=float(np.sum(w*np.array([r['LP2'] for r in rs]))/np.sum(w))
    s=np.array([r['subtree'] for r in rs],float); nw=float(np.sum(s*np.array([r['LP2'] for r in rs]))/max(1,np.sum(s)))
    extra=f"{3/m:.1%}" if l2==1.0 else ""
    print(f"{n:>3} {k:>3} {k/n:>6.3f} {m:>5} {l1:>6.0%} {l2:>9.0%} {u:>13.0%} {nw:>13.0%} {extra:>25}")
def fit(xs,ys):
    X=np.array(xs); Y=np.array(ys,float)
    def nll(p):
        z=p[0]+p[1]*X; pz=1/(1+np.exp(-z)); pz=np.clip(pz,1e-9,1-1e-9)
        return -np.sum(Y*np.log(pz)+(1-Y)*np.log(1-pz))
    res=minimize(nll,[0.0,1.0],method='Nelder-Mead',options={'maxiter':20000,'xatol':1e-8,'fatol':1e-10}); return res.x,res.fun
print("\nlogistic fits of P(LP-2 infeasible | dead):")
for n in sorted({r['n'] for r in dead}):
    rs=[r for r in dead if r['n']==n]
    (a,b),_=fit([r['k']/n for r in rs],[r['LP2'] for r in rs])
    a50=-a/b; a90=(math.log(9)-a)/b
    print(f"   n={n}: alpha50 = {a50:.3f}, alpha90 = {a90:.3f}   (in remaining columns: {n*(1-a50):.1f} and {n*(1-a90):.1f})")
xs=[r['k']/r['n'] for r in dead]; ys=[r['LP2'] for r in dead]; (a,b),nll_frac=fit(xs,ys)
(a2,b2),nll_rem=fit([r['n']-r['k'] for r in dead],ys)
print(f"pooled: fraction model alpha50 = {-a/b:.3f}, alpha90 = {(math.log(9)-a)/b:.3f};  negative log-likelihood: fraction model {nll_frac:.1f}, remaining-columns model {nll_rem:.1f}  (lower is better)")
