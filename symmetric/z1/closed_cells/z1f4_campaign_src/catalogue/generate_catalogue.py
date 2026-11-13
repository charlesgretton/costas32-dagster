#!/usr/bin/env python3
from itertools import combinations
import csv

def diffs(m): return [m[j]-m[i] for i in range(len(m)) for j in range(i+1,len(m))]
def good(m):
 d=diffs(m)
 return len(d)==len(set(d)) and sum(x>=16 for x in d)==1
def refl(m): return tuple(sorted(31-x for x in m))
raw=[m for m in combinations(range(32),4) if good(m)]
can=sorted({min(m,refl(m)) for m in raw})
fixed=sum(m==refl(m) for m in raw)
assert len(raw)==5146 and fixed==0 and len(can)==2573
with open('catalogue/F_f4_reflection_canonical.csv','w',newline='') as h:
 w=csv.writer(h);w.writerow(['id','marks','even_fixed_points','diameter','differences','long_difference'])
 for i,m in enumerate(can):
  d=sorted(diffs(m));long=[x for x in d if x>=16]
  w.writerow([i,' '.join(map(str,m)),sum(x%2==0 for x in m),m[-1]-m[0],' '.join(map(str,d)),long[0]])
print('raw=5146 canonical=2573')
