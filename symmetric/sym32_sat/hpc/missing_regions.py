#!/usr/bin/env python3
"""Regions listed in <selected> that have no row in <ledger.jsonl>.
usage: missing_regions.py <selected.txt> <ledger.jsonl>  > missing.txt"""
import json, sys
want = [l.strip() for l in open(sys.argv[1]) if l.strip()]
have = {json.loads(l)["region_id"] for l in open(sys.argv[2]) if l.strip()}
miss = [r for r in want if r not in have]
print("\n".join(miss))
print(f"{len(miss)} of {len(want)} selected regions have no result", file=sys.stderr)
