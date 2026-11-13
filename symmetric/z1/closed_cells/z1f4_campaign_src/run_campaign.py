#!/usr/bin/env python3
import argparse,csv,concurrent.futures,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('-j','--jobs',type=int,default=1);p.add_argument('--mode',choices=['full','structural'],default='structural');p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int);a=p.parse_args();root=Path(__file__).resolve().parent;keys=[r['root_key'] for r in csv.DictReader(open(root/'roots.csv'))];keys=keys[a.start:None if a.count is None else a.start+a.count]
def run(k):return subprocess.run([sys.executable,str(root/'run_root.py'),k,'--mode',a.mode],cwd=root,capture_output=True,text=True)
fail=0
with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,a.jobs)) as ex:
 for f in concurrent.futures.as_completed([ex.submit(run,k) for k in keys]):
  cp=f.result();print((cp.stdout+cp.stderr).strip(),flush=True);fail|=cp.returncode
sys.exit(1 if fail else 0)
