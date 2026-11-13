#!/usr/bin/env python3
import argparse,csv,subprocess,time,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root_key');p.add_argument('--mode',choices=['full','structural'],default='structural');a=p.parse_args();root=Path(__file__).resolve().parent
rec=next(x for x in csv.DictReader(open(root/'roots.csv')) if x['root_key']==a.root_key);out=root/'results'/'raw';out.mkdir(parents=True,exist_ok=True);final=out/f'{a.root_key}.{a.mode}.log';tmp=out/f'{a.root_key}.{a.mode}.tmp'
if final.exists():print('skip',a.root_key,a.mode);sys.exit(0)
t=time.time()
with tmp.open('w') as f:cp=subprocess.run([str(root/'z1f4_search'),rec['ruler_id'],rec['omitted_length'],a.mode,str(root/'catalogue'/'F_f4_reflection_canonical.csv')],stdout=f,stderr=subprocess.STDOUT)
if cp.returncode:tmp.rename(out/f'{a.root_key}.{a.mode}.failed.log');sys.exit(cp.returncode)
txt=tmp.read_text();tmp.rename(final);last=txt.strip().splitlines()[-1]
with (out/f'{a.root_key}.{a.mode}.result.csv').open('w',newline='') as h:w=csv.writer(h);w.writerow(['root_key','mode','summary','elapsed_seconds']);w.writerow([a.root_key,a.mode,last,f'{time.time()-t:.6f}'])
if 'SURVIVOR ' in txt:(root/'results'/'survivors'/f'{a.root_key}.{a.mode}.txt').write_text(txt)
print(a.root_key,a.mode,f'{time.time()-t:.3f}s',last)
