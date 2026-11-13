"""Positive control for lifted obstructions: corner reduction.
Bijection: order-n Costas arrays with a dot at (0,0)  <->  order-(n-1) Costas arrays admitting a corner addition at (0,0)
(add (0,0), shift every other dot by (+1,+1)). Prediction for a corner triple A = {(0,0), a, b} at order n:
feasible  iff  some corner-admissible order-(n-1) array contains A' = {a-(1,1), b-(1,1)}.
Compared with the exact order-n catalogue for every Costas-valid corner triple, at orders 13, 14, 15."""
import subprocess, time
from itertools import combinations
def arrays(n):
    out=subprocess.run(['/tmp/listall','exact',str(n)],capture_output=True,text=True).stdout.splitlines()
    return [tuple(map(int,l.split(','))) for l in out if ',' in l]
def is_costas(p):
    D=set()
    for i in range(len(p)):
        for j in range(i+1,len(p)):
            v=(j-i,p[j]-p[i])
            if v in D: return False
            D.add(v)
    return True
def index(A):
    ix={}
    for k,a in enumerate(A):
        for c,r in enumerate(a): ix.setdefault((c,r),set()).add(k)
    return ix
def contains(ix,dots):
    s=None
    for d in dots:
        t=ix.get(d,set()); s=t if s is None else s&t
        if not s: return False
    return True
cat={}
t=time.time()
for n in (12,13,14,15): cat[n]=arrays(n)
print(f"catalogues: " + ", ".join(f"order {n}: {len(cat[n]):,}" for n in cat) + f"  ({time.time()-t:.0f} s)")
for n in (13,14,15):
    lower=cat[n-1]
    admissible=[b for b in lower if is_costas((0,)+tuple(x+1 for x in b))]
    with_corner=[a for a in cat[n] if a[0]==0]
    print(f"order {n}: arrays with a dot at (0,0): {len(with_corner)}; corner-admissible order-{n-1} arrays: {len(admissible)}"
          f"  -> bijection count {'holds' if len(with_corner)==len(admissible) else 'FAILS'}")
    ix_n=index(cat[n]); ix_adm=index(admissible); ix_low=index(lower)
    tot=agree=inf_true=inf_plain=0
    for (c2,c3) in combinations(range(1,n),2):
        for r2 in range(1,n):
            for r3 in range(1,n):
                if r3==r2: continue
                A=[(0,0),(c2,r2),(c3,r3)]
                if not is_costas([None]*0 or [0]) : pass
                D=[(c2,r2),(c3,r3),(c3-c2,r3-r2)]
                if len(set(D))<3: continue          # not Costas-valid
                tot+=1
                truth=contains(ix_n,A)
                Ap=[(c2-1,r2-1),(c3-1,r3-1)]
                pred=contains(ix_adm,Ap)
                agree+= (truth==pred); inf_true+= (not truth)
                inf_plain+= (not truth) and (not contains(ix_low,Ap))
    print(f"   {tot:,} corner triples; infeasible {inf_true:,} ({inf_true/tot:.1%}); lifted prediction agrees on {agree:,}/{tot:,}"
          f" ({'100% precision and coverage' if agree==tot else 'MISMATCH'}); explained by plain lower-order infeasibility alone: {inf_plain}/{inf_true}")
