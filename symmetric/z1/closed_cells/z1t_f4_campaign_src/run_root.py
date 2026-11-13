#!/usr/bin/env python3
import argparse,csv,subprocess,time,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root_key');p.add_argument('--mode',choices=['full','structural'],default='full');p.add_argument('--audit',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parent
try: rec=next(x for x in csv.DictReader(open(root/'roots.csv')) if x['root_key']==a.root_key)
except StopIteration: print('unknown root',a.root_key,file=sys.stderr);sys.exit(2)
out=root/'results'/'raw';out.mkdir(parents=True,exist_ok=True);tag=a.mode+('.audit' if a.audit else '');final=out/f'{a.root_key}.{tag}.log';tmp=out/f'{a.root_key}.{tag}.tmp'
if final.exists():print('skip',a.root_key,tag);sys.exit(0)
bin=root/('z1t_f4_search_audit' if a.audit else 'z1t_f4_search');env=None
if a.audit:
 import os;env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0'
t=time.time()
with tmp.open('w') as f: cp=subprocess.run([str(bin),rec['ruler_id'],a.mode,str(root/'catalogue'/'T_f4_reflection_canonical.csv'),'1' if a.audit else '0'],stdout=f,stderr=subprocess.STDOUT,env=env)
if cp.returncode: tmp.rename(out/f'{a.root_key}.{tag}.failed.log');sys.exit(cp.returncode)
txt=tmp.read_text();tmp.rename(final);last=txt.strip().splitlines()[-1]
with (out/f'{a.root_key}.{tag}.result.csv').open('w',newline='') as h:w=csv.writer(h);w.writerow(['root_key','mode','audit','summary','elapsed_seconds']);w.writerow([a.root_key,a.mode,int(a.audit),last,f'{time.time()-t:.6f}'])
if 'SURVIVOR ' in txt:(root/'results'/'survivors'/f'{a.root_key}.{tag}.txt').write_text(txt)
print(a.root_key,tag,f'{time.time()-t:.3f}s',last)
