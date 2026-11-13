"""The Costas-specific excess: 3-dot obstructions. Collect them, group by shape, and test every placement of
each shape at orders 12 and 13 exactly, against the complete lists of Costas arrays."""
import random, subprocess
from collections import Counter
from itertools import combinations
def arrays(n):
    out=subprocess.run(['/tmp/listall','exact',str(n)],capture_output=True,text=True).stdout.splitlines()
    return [tuple(map(int,l.split(','))) for l in out if ',' in l]
def index(A):
    ix={}
    for k,a in enumerate(A):
        for c,r in enumerate(a): ix.setdefault((c,r),set()).add(k)
    return ix
def feasible(ix,dots):
    s=None
    for d in dots:
        t=ix.get(d,set()); s=t if s is None else s&t
        if not s: return False
    return True
def costas_valid(dots):
    if len({c for c,_ in dots})<len(dots) or len({r for _,r in dots})<len(dots): return False
    D=[(b[0]-a[0],b[1]-a[1]) for a,b in combinations(sorted(dots),2)]
    return len(set(D))==len(D)
def shape(dots):
    c0=min(c for c,_ in dots); r0=min(r for _,r in dots); P=[(c-c0,r-r0) for c,r in dots]
    W=max(c for c,_ in P); H=max(r for _,r in P); ims=[]
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
IX={n:index(arrays(n)) for n in (12,13)}
# exhaustive: every Costas-valid 3-dot set on the 12x12 board, infeasible at order 12
n=12; bad=Counter(); tot=0
cells=[(c,r) for c in range(n) for r in range(n)]
for c1 in range(n):
  for c2 in range(c1+1,n):
    for c3 in range(c2+1,n):
      for r1 in range(n):
        for r2 in range(n):
          if r2==r1: continue
          for r3 in range(n):
            if r3 in (r1,r2): continue
            d=[(c1,r1),(c2,r2),(c3,r3)]
            if not costas_valid(d): continue
            tot+=1
            if not feasible(IX[12],d): bad[shape(d)]+=1
print(f"order 12: {tot:,} Costas-valid 3-dot sets; {sum(bad.values()):,} lie in no Costas array, in {len(bad)} shapes")
def everywhere(sh,N):
    W=max(c for c,_ in sh); H=max(r for _,r in sh); inf=pos=0
    for dc in range(N-W):
        for dr in range(N-H):
            pos+=1; inf+= not feasible(IX[N],[(c+dc,r+dr) for c,r in sh])
    return inf,pos
full12=[sh for sh in bad if everywhere(sh,12)[0]==everywhere(sh,12)[1]]
print(f"shapes infeasible at EVERY position at order 12: {len(full12)} of {len(bad)}")
full13=[sh for sh in full12 if everywhere(sh,13)[0]==everywhere(sh,13)[1]]
print(f"   ...and also at every position at order 13: {len(full13)}")
for sh in full13[:10]:
    print(f"   {sh}  (bounding box {max(c for c,_ in sh)+1} x {max(r for _,r in sh)+1})")
