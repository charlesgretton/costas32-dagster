#!/usr/bin/env python3
from itertools import combinations
from collections import Counter
import csv
N=32
def ds(m):return tuple(sorted(b-a for a,b in combinations(m,2)))
def good(m):
 d=ds(m);return len(d)==6 and len(set(d))==6 and max(d)<=15
def refl(m):return tuple(31-x for x in reversed(m))
def nshape(m):
 z=tuple(x-m[0] for x in m);return z
def nrshape(m):
 z=nshape(m);D=z[-1];return min(z,tuple(D-x for x in reversed(z)))
raw=[m for m in combinations(range(N),4) if good(m)]
fixed=[m for m in raw if m==refl(m)]
can=sorted({min(m,refl(m)) for m in raw})
trans={nshape(m) for m in raw};tr={nrshape(m) for m in raw}
assert (len(raw),len(fixed),len(can),len(trans),len(tr))==(5470,0,2735,282,141)
rows=list(csv.DictReader(open('catalogue/T_f4_reflection_canonical.csv')))
disk={tuple(map(int,r['marks'].split())) for r in rows};assert disk==set(can)
byL=Counter(); longplacements=0; external=0
same=sum(1 for r in range(1,16) for s in range(r+1,16) if (r+s)%2==0)
opp=sum(1 for r in range(1,16) for s in range(r+1,16) if (r+s)%2==1)
assert (same,opp)==(49,56)
for F in can:
 a=sum(x%2==0 for x in F)
 for L in range(16,32):
  for u in range(32-L):
   if u in F or u+L in F:continue
   longplacements+=1;byL[L]+=1
   external+=sum(1 for r in range(1,16) for s in range(r+1,16) if (L-a-r-s)%2==0)
expect={16:32820,17:31213,18:29534,19:27797,20:25993,21:24130,22:22203,23:20222,24:18177,25:16079,26:13932,27:11739,28:9494,29:7201,30:4851,31:2453}
assert dict(byL)==expect and longplacements==297838 and external==15642886
roots=list(csv.DictReader(open('roots.csv')));assert len(roots)==2735
assert {r['root_key'] for r in roots}=={f'F{i:04d}' for i in range(2735)}
print('raw_rulers=5470')
print('reflection_fixed=0')
print('canonical_rulers=2735')
print('translation_shapes=282')
print('translation_reflection_shapes=141')
print('long_placements=297838')
print('same_parity_pairs=49')
print('opposite_parity_pairs=56')
print('external_parameter_records=15642886')
print('per_L='+','.join(f'{k}:{v}' for k,v in sorted(byL.items())))
print('CATALOGUE AUDIT PASS')
