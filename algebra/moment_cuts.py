"""Strength of lag-moment inequalities (the 'distinct bounded integers' cuts).
For lag d, the m = n-d differences D_i = p[i+d]-p[i] of a Costas permutation are distinct nonzero integers in
[-(n-1), n-1] with sum s_d. Hence  Qmin(m, s_d) <= sum D_i^2 <= Qmax(m, s_d), where Qmin/Qmax are the exact
minimum/maximum sums of squares over m distinct allowed integers summing to s_d (dynamic programme).
Test: what fraction of NON-Costas permutations satisfy all these inequalities at every lag?"""
import random, sys, numpy as np
n=int(sys.argv[1]) if len(sys.argv)>1 else 32; TRIALS=int(sys.argv[2]) if len(sys.argv)>2 else 20000
vals=[v for v in range(-(n-1),n) if v!=0]; OFF=n*n; INF=10**9
# dp[c][s+OFF] = (min sq, max sq) over choices of c distinct values summing to s
mn=np.full((n+1,2*OFF+1),INF,dtype=np.int64); mx=np.full((n+1,2*OFF+1),-INF,dtype=np.int64); mn[0][OFF]=0; mx[0][OFF]=0
for v in vals:
    for c in range(n-1,-1,-1):
        src_mn=mn[c]; src_mx=mx[c]; ok=src_mn<INF
        if not ok.any(): continue
        idx=np.nonzero(ok)[0]; tgt=idx+v
        good=(tgt>=0)&(tgt<=2*OFF); idx=idx[good]; tgt=tgt[good]
        np.minimum.at(mn[c+1],tgt,src_mn[idx]+v*v); np.maximum.at(mx[c+1],tgt,src_mx[idx]+v*v)
def passes(p):
    for d in range(1,n):
        D=[p[i+d]-p[i] for i in range(n-d)]; s=sum(D); q=sum(x*x for x in D); m=n-d
        if not (mn[m][s+OFF]<=q<=mx[m][s+OFF]): return False, d
    return True, None
def costas(p):
    return all(len({p[i+d]-p[i] for i in range(n-d)})==n-d for d in range(1,n))
random.seed(1); npass=0; ncost=0; cut_at={}
for _ in range(TRIALS):
    p=list(range(n)); random.shuffle(p)
    if costas(p): ncost+=1; continue
    ok,d=passes(p); npass+=ok
    if not ok: cut_at[d]=cut_at.get(d,0)+1
print(f"order {n}: {TRIALS} random permutations ({ncost} Costas); non-Costas permutations satisfying EVERY lag-moment inequality: {npass}/{TRIALS-ncost} ({npass/(TRIALS-ncost):.1%})")
if cut_at: print("   lags at which the others were cut:", dict(sorted(cut_at.items())[:8]))
N32=[31,30,2,8,1,14,12,7,4,20,0,18,9,13,21,10,11,26,25,6,28,24,3,15,5,19,22,27,29,16,23,17]
H=[5,19,25,28,29,8,0,26,14,3,31,1,23,30,2,20,16,13,18,9,15,10,22,27,12,21,7,4,6,17,11,24]
if n==32:
    for name,p in (("N32 (defect 2)",N32),("Paper 7 witness h* (defect 55)",H)): print(f"   {name}: satisfies all lag-moment inequalities: {passes(p)[0]}")
