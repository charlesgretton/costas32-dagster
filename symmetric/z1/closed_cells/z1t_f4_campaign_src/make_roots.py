#!/usr/bin/env python3
import csv
rows=list(csv.DictReader(open('catalogue/T_f4_reflection_canonical.csv')))
out=[]
for row in rows:
    F=list(map(int,row['marks'].split()))
    out.append([f"F{int(row['id']):04d}",row['id'],row['marks'],sum(x%2==0 for x in F),496-sum(F)])
assert len(out)==2735
with open('roots.csv','w',newline='') as h:
    w=csv.writer(h);w.writerow(['root_key','ruler_id','fixed_points','even_fixed_points','centre_sum_target']);w.writerows(out)
print('roots=2735')
