#!/usr/bin/env python3
"""f=2 campaign bookkeeping: what is closed, what is open, and batches for what remains.

  f2_campaign.py status                         per-region state across ALL results
  f2_campaign.py plan [--batch 8] [--exclude file ...]   write batches of unclosed regions

A record counts only if its region_id is an f=2 region in regions.csv AND its fixed points
match that row (so test runs can never pass as campaign results). States, strongest first:
  SAT       a validated witness exists -- would be a transpose-symmetric Costas array
  CLOSED    a definite UNSAT: Kissat exit 20 'UNSAT', or Dagster 'UNSAT_UNPROVEN'.
            NO CERTIFICATE: neither verdict is a checked proof.
  OPEN      only timeouts so far      FAILED  only errors      NEVER   no record at all
"""
import argparse, csv, glob, json, os, sys
D = os.environ.get("COSTAS_DATA") or sys.exit("set COSTAS_DATA (source hpc/env.sh)")
F2 = {r["region_id"]: [int(x) for x in r["fixed_points"].split()]
      for r in csv.DictReader(open(f"{D}/regions.csv")) if r["f"] == "2"}
UNSAT = {("kissat", "UNSAT"), ("dagster_native_split", "UNSAT_UNPROVEN"),
         ("dagster_mono", "UNSAT_UNPROVEN"), ("kissat_split_agg", "UNSAT")}
ERR = lambda s: s not in ("SAT", "UNSAT", "UNSAT_UNPROVEN", "TIMEOUT", "INCOMPLETE")

def scan():
    st = {}
    for p in glob.glob(f"{D}/results/**/ledger.jsonl", recursive=True):
        for l in open(p):
            try: r = json.loads(l)
            except ValueError: continue
            rid = r.get("region_id")
            if rid not in F2 or r.get("fixed_points") != F2[rid] or r.get("arm") == "split_child": continue
            s = st.setdefault(rid, {"sat": False, "closed_by": set(), "timeouts": 0, "errors": 0})
            if r["status"] == "SAT" and r.get("model_validated"): s["sat"] = True
            elif (r["arm"], r["status"]) in UNSAT: s["closed_by"].add(r["arm"])
            elif r["status"] == "TIMEOUT": s["timeouts"] += 1
            elif ERR(r["status"]): s["errors"] += 1
    return st

def state(s):
    if s is None: return "NEVER"
    if s["sat"]: return "SAT"
    if s["closed_by"]: return "CLOSED"
    if s["timeouts"]: return "OPEN"
    return "FAILED"

ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["status", "plan"])
ap.add_argument("--batch", type=int, default=8); ap.add_argument("--exclude", nargs="*", default=[])
a = ap.parse_args(); st = scan()
cls = {rid: state(st.get(rid)) for rid in sorted(F2)}
if a.cmd == "status":
    from collections import Counter
    c = Counter(cls.values())
    by = Counter(arm for s in st.values() if s["closed_by"] for arm in s["closed_by"])
    print(f"f=2 regions: {len(F2)}")
    for k in ("SAT", "CLOSED", "OPEN", "FAILED", "NEVER"): print(f"  {k:<7} {c.get(k, 0)}")
    print(f"  closed by: {dict(by)}  (a region closed by both counts under each)")
    print("  CLOSED = definite UNSAT verdicts, NO CERTIFICATE (no checked proofs yet)")
    for k in ("SAT", "FAILED", "OPEN"):
        ids = [r for r, v in cls.items() if v == k]
        if ids: print(f"  {k}: {' '.join(ids)}")
    if c.get("SAT"): print("!! A SAT f=2 REGION: see its WITNESSES/ file. Reproduce before anything else.")
else:
    skip = set()
    for f in a.exclude: skip |= {l.strip() for l in open(f) if l.strip()}
    todo = [r for r, v in cls.items() if v in ("NEVER", "OPEN", "FAILED") and r not in skip]
    out = f"{D}/campaign_f2"; os.makedirs(out, exist_ok=True)
    for old in glob.glob(f"{out}/batch_*.txt"): os.remove(old)
    n = 0
    for i in range(0, len(todo), a.batch):
        open(f"{out}/batch_{n:03d}.txt", "w").write("\n".join(todo[i:i + a.batch]) + "\n"); n += 1
    print(f"{len(todo)} regions to run (excluded {len(skip & set(cls))} in flight) -> {n} batches of <= {a.batch} in {out}/")
