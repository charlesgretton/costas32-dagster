#!/usr/bin/env python3
import argparse,csv
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--mode',choices=['full','structural'],default='structural');a=p.parse_args();root=Path(__file__).resolve().parent;exp={r['root_key'] for r in csv.DictReader(open(root/'roots.csv'))};files=list((root/'results'/'raw').glob(f'*.{a.mode}.result.csv'));got=set();positive=0
for f in files:
 r=list(csv.DictReader(open(f)))[0];got.add(r['root_key']);positive+=int('EXHAUSTED_WITH' in r['summary'])
print('expected',len(exp));print('completed',len(got));print('missing',len(exp-got));print('unexpected',len(got-exp));print('positive_roots',positive)
