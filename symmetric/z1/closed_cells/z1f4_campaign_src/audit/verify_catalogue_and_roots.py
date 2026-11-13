#!/usr/bin/env python3
from itertools import combinations
import csv

def check(m):
 seen=set();long=0
 for a,b in combinations(m,2):
  d=b-a
  if d in seen:return False
  seen.add(d);long+=d>=16
 return long==1
def key(m):return min(m,tuple(31-x for x in m[::-1]))
raw=[m for m in combinations(range(32),4) if check(m)]
want={key(m) for m in raw}
rows=list(csv.DictReader(open('catalogue/F_f4_reflection_canonical.csv')))
got={tuple(map(int,r['marks'].split())) for r in rows}
assert want==got and len(got)==2573
roots=list(csv.DictReader(open('roots.csv')))
expected=set()
for row in rows:
 a=int(row['even_fixed_points'])
 for r in range(1,16):
  if r%2==a%2: expected.add(f"F{int(row['id']):04d}-r{r:02d}")
actual={r['root_key'] for r in roots}
assert actual==expected and len(actual)==19405
print('PASS catalogue=2573 roots=19405')
