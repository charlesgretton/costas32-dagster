#!/usr/bin/env python3
"""Regions for Stage 2: Kissat did NOT return a definite answer, or took longer than SLOW s.
A region whose Kissat status was anything but SAT/UNSAT is included -- never dropped."""
import json, sys
led, slow = sys.argv[1], float(sys.argv[2])
for l in open(led):
    r = json.loads(l)
    if r.get("arm") != "kissat": continue
    if r["status"] not in ("SAT", "UNSAT") or r["wall_s"] > slow: print(r["region_id"])
