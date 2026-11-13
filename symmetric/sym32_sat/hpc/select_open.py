#!/usr/bin/env python3
"""Regions Kissat did NOT close (status TIMEOUT) in one or more ledgers, optionally one f only.
A region counts as open only if no ledger shows it closed.
usage: select_open.py <ledger.jsonl> [more ledgers ...] [--f 2]"""
import json, sys
args = sys.argv[1:]; f = None
if "--f" in args: i = args.index("--f"); f = int(args[i + 1]); del args[i:i + 2]
closed, open_ = set(), {}
for p in args:
    for l in open(p):
        r = json.loads(l)
        if r.get("arm") != "kissat" or (f is not None and r["f"] != f): continue
        if r["status"] in ("SAT", "UNSAT"): closed.add(r["region_id"])
        elif r["status"] == "TIMEOUT": open_[r["region_id"]] = r
ids = sorted(set(open_) - closed)
print("\n".join(ids))
print(f"{len(ids)} open region(s)" + (f" with f={f}" if f is not None else ""), file=sys.stderr)
