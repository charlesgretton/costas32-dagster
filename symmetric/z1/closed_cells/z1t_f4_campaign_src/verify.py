#!/usr/bin/env python3
import argparse,csv
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['full','structural'],default='full');p.add_argument('--audit',action='store_true');p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int);a=p.parse_args();root=Path(__file__).resolve().parent;allkeys=[r['root_key'] for r in csv.DictReader(open(root/'roots.csv'))];keys=allkeys[a.start:None if a.count is None else a.start+a.count];exp=set(keys);tag=a.mode+('.audit' if a.audit else '');got=set();positive=0;incomplete=0
for f in (root/'results'/'raw').glob(f'*.{tag}.result.csv'):
 r=list(csv.DictReader(open(f)))[0];got.add(r['root_key']);positive+=int('EXHAUSTED_WITH' in r['summary']);incomplete+=int('EXHAUSTED_' not in r['summary'])
print('expected',len(exp));print('completed',len(got&exp));print('missing',len(exp-got));print('unexpected',len(got-exp));print('positive_roots',positive);print('incomplete',incomplete)
