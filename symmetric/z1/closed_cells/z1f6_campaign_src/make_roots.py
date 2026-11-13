#!/usr/bin/env python3
import csv
from pathlib import Path
rows=list(csv.DictReader(open('catalogue/F_f6_reflection_canonical.csv')));out=[]
for x in rows:
 F=list(map(int,x['marks'].split()));target=496-sum(F)
 for r in range(1,16):
  for s in range(r+1,16):
   if (r^s)&1:out.append([f"F{int(x['id']):03d}-r{r:02d}-s{s:02d}",x['id'],x['marks'],r,s,target])
assert len(out)==728
with open('roots.csv','w',newline='') as h:w=csv.writer(h);w.writerow(['root_key','ruler_id','fixed_points','r','s','centre_sum_target']);w.writerows(out)
print('roots=728')
