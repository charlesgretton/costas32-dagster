#!/usr/bin/env python3
"""Run the v2 message audit over every Dagster closure in the campaign ledgers.
Writes $COSTAS_DATA/audit_results.csv (one row per audited closing run).
usage: audit_all.py   (needs COSTAS_DATA, and COSTAS_N for test orders)"""
import csv, glob, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_dagster import audit, VERSION
D = os.environ.get("COSTAS_DATA") or sys.exit("set COSTAS_DATA")
rows = []
for led in sorted(glob.glob(f"{D}/results/**/shard*/ledger.jsonl", recursive=True)):
    for l in open(led):
        r = json.loads(l)
        if r.get("arm") != "dagster_native_split" or r.get("status") != "UNSAT_UNPROVEN": continue
        rid, coords = r["region_id"], r.get("split_coords") or []
        logs = glob.glob(f"{os.path.dirname(led)}/dagster_logs/costas_{rid}_*_D.master.log.gz")
        res, why, lsha = "FAIL", "", ""
        if len(logs) != 1: why = f"{len(logs)} matching logs"
        else:
            lsha = hashlib.sha256(open(logs[0], "rb").read()).hexdigest()
            trans = [tuple(t) for t in r.get("fixed_transpositions") or []]
            try:
                ok, checks, info = audit(logs[0], r["fixed_points"], trans, len(coords), coords)
                res = "PASS" if ok else "FAIL"; why = "; ".join(f"{n}: {w}" for n, c, w in checks if not c)
            except Exception as e:
                why = f"audit error: {e}"
        rows.append(dict(region_id=rid, f=r["f"], depth=len(coords), coords=" ".join(map(str, coords)),
                         result=res, audit_version=VERSION, log=logs[0] if len(logs) == 1 else "",
                         log_sha256=lsha, ledger=led, detail=why))
out = f"{D}/audit_results.csv"
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["region_id"]); w.writeheader(); w.writerows(rows)
p = sum(r["result"] == "PASS" for r in rows)
print(f"{VERSION}: {len(rows)} Dagster closures audited: {p} PASS, {len(rows)-p} FAIL -> {out}")
for r in rows:
    if r["result"] != "PASS": print(f"  FAIL {r['region_id']}: {r['detail'][:150]}")
