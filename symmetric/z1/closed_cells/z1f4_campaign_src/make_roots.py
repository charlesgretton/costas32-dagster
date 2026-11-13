#!/usr/bin/env python3
import csv
rows=list(csv.DictReader(open('catalogue/F_f4_reflection_canonical.csv')));out=[]
for x in rows:
 F=list(map(int,x['marks'].split()));a=int(x['even_fixed_points']);target=496-sum(F)
 for r in range(1,16):
  if r%2==a%2: out.append([f"F{int(x['id']):04d}-r{r:02d}",x['id'],x['marks'],a,x['long_difference'],r,target])
assert len(out)==19405
with open('roots.csv','w',newline='') as h:
 w=csv.writer(h);w.writerow(['root_key','ruler_id','fixed_points','even_fixed_points','long_fixed_difference','omitted_length','centre_sum_target']);w.writerows(out)
print('roots=19405')
