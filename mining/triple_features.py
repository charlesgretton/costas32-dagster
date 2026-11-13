"""Where do the infeasible 3-dot sets concentrate? Infeasibility rate at order 12 by simple geometric features."""
import subprocess
from itertools import combinations
from collections import defaultdict
exec(open('triples.py').read().split("IX={n:index")[0])
n=12; ix=index(arrays(n))
stats=defaultdict(lambda:[0,0])
def add(key,inf): stats[key][0]+=inf; stats[key][1]+=1
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
            inf= not feasible(ix,d)
            dist=min(min(c,r,n-1-c,n-1-r) for c,r in d)          # closest approach of any dot to the border
            corner=sum(min(c,n-1-c)+min(r,n-1-r)==0 for c,r in d)
            span=(c3-c1)
            add(('all',),inf); add(('closest distance to border',dist),inf); add(('dots on a corner cell',corner),inf)
            add(('column span',span//3*3),inf)
def show(prefix):
    for k in sorted(k for k in stats if k[0]==prefix):
        i,t=stats[k]; print(f"   {str(k[1:]) if len(k)>1 else '':<8} {i:>6}/{t:<8} = {i/t:6.2%}")
for p in ('all','closest distance to border','dots on a corner cell','column span'):
    print(p+":"); show(p)
