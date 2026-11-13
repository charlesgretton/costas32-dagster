"""Midpoint family classification with a null control.
Scheme B signature: for lags d=1..4, (#positive differences, #differences with |e| <= n/4) within the prefix.
A family is 'zero-live' if none of its states extends to a Costas array. Coverage = share of midpoint states in
zero-live families with support >= S. Null: shuffle the live labels across states (same live count)."""
import sys, subprocess, random
from collections import defaultdict
n=int(sys.argv[1]); K=int(sys.argv[2]); S=int(sys.argv[3]) if len(sys.argv)>3 else 100
P=[tuple(map(int,l.split())) for l in open(sys.argv[4])]
arrays=[tuple(map(int,l.split(','))) for l in subprocess.run(['/tmp/listall','exact',str(n)],capture_output=True,text=True).stdout.splitlines() if ',' in l]
livepref={a[:K] for a in arrays}
live=[p in livepref for p in P]
def sigB(p):
    out=[]
    for d in range(1,5):
        D=[p[i+d]-p[i] for i in range(len(p)-d)]
        out+= [sum(e>0 for e in D), sum(abs(e)<=n//4 for e in D)]
    return tuple(out)
sig=[sigB(p) for p in P]
fam=defaultdict(list)
for k,s in enumerate(sig): fam[s].append(k)
def coverage(lab):
    cov=0; nf=0
    for ks in fam.values():
        if len(ks)>=S and not any(lab[k] for k in ks): cov+=len(ks); nf+=1
    return cov/len(P), nf
real,nfr=coverage(live)
print(f"order {n}, depth {K}: {len(P):,} midpoint states, {sum(live):,} live ({sum(live)/len(P):.3%}); {len(fam):,} scheme-B families")
print(f"   real labels:     zero-live families with support >= {S}: {nfr}, covering {real:.2%} of states")
random.seed(1); nulls=[]
for t in range(5):
    lab=live[:]; random.shuffle(lab); c,nf=coverage(lab); nulls.append(c)
    print(f"   shuffled labels #{t+1}: {nf} zero-live families, covering {c:.2%}")
print(f"   excess of real over null mean: {real-sum(nulls)/len(nulls):+.2%}")
