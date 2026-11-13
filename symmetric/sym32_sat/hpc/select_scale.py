#!/usr/bin/env python3
"""Regions for the Dagster scaling test: the hardest f=4 regions Kissat DID solve in
Stage 1 (so every Dagster time has a Kissat baseline), plus a few Kissat could not."""
import json, sys
led = sys.argv[1]; nsol = int(sys.argv[2]) if len(sys.argv) > 2 else 9
ncen = int(sys.argv[3]) if len(sys.argv) > 3 else 3
R = [json.loads(l) for l in open(led)]; R = [r for r in R if r.get("arm") == "kissat"]
sol = sorted([r for r in R if r["f"] == 4 and r["status"] == "UNSAT"], key=lambda r: -r["wall_s"])[:nsol]
fonly = int(sys.argv[4]) if len(sys.argv) > 4 else None      # e.g. 2: censored f=2 regions only
cen = sorted([r for r in R if r["status"] == "TIMEOUT" and (fonly is None or r["f"] == fonly)],
             key=lambda r: (-r["f"], r["region_id"]))[:ncen]
for r in sol + cen: print(r["region_id"])
