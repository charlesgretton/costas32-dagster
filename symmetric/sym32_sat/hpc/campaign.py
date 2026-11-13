#!/usr/bin/env python3
"""Class campaign bookkeeping (any f): what is closed, what is open, and batches for what remains.

  campaign.py --f F list open|never|failed|closed|sat   one region id per line
  campaign.py --f F status                         per-region state across ALL results
  campaign.py --f F plan [--batch N] [--exclude file ...]   batches of unclosed regions

A record counts only if its region_id is an f=F region in regions.csv AND its fixed points
match that row (so test runs can never pass as campaign results). States, strongest first:
  SAT       a validated witness exists -- would be a transpose-symmetric Costas array
  CLOSED    a definite UNSAT: Kissat exit 20 'UNSAT', or Dagster 'UNSAT_UNPROVEN'.
            NO CERTIFICATE: neither verdict is a checked proof.
  OPEN      only timeouts so far      FAILED  only errors      NEVER   no record at all
"""
import argparse, csv, glob, json, os, sys
D = os.environ.get("COSTAS_DATA") or sys.exit("set COSTAS_DATA (source hpc/env.sh)")
import argparse as _a
_p = _a.ArgumentParser(add_help=False); _p.add_argument("--f", type=int, required=True)
FCLS = _p.parse_known_args()[0].f
F2 = {r["region_id"]: ([int(x) for x in r["fixed_points"].split()] if r["fixed_points"] else [])
      for r in csv.DictReader(open(f"{D}/regions.csv")) if r["f"] == str(FCLS)}
UNSAT = {("kissat", "UNSAT"), ("dagster_native_split", "UNSAT_UNPROVEN"),
         ("dagster_mono", "UNSAT_UNPROVEN"), ("kissat_split_agg", "UNSAT")}
ERR = lambda s: s not in ("SAT", "UNSAT", "UNSAT_UNPROVEN", "TIMEOUT", "INCOMPLETE")

CASES = {}     # region -> case ('0-5') -> records

def case_closed(rid):
    """Closed by cases: for one coordinate c, every possible partner x (x free, x != c) has a
    case 'c-x' with an UNSAT verdict. A coordinate has exactly one partner, so those cases
    are exhaustive and disjoint. Returns (closed, sat, detail)."""
    F = F2[rid]; free = [i for i in range(N) if i not in F]
    recs = CASES.get(rid, {})
    if any(r["status"] == "SAT" and r.get("model_validated") for rs in recs.values() for r in rs):
        return False, True, "a case is SAT"
    best = None
    for c in free:
        need = {f"{min(c,x)}-{max(c,x)}" for x in free if x != c}
        have = {k for k in need if any((r["arm"], r["status"]) in UNSAT for r in recs.get(k, []))}
        if best is None or len(have) > best[1]: best = (c, len(have), len(need))
        if have == need: return True, False, f"all {len(need)} cases on coordinate {c}"
    return False, False, (f"{best[1]}/{best[2]} cases on coordinate {best[0]}" if best else "no cases")

def scan():
    st = {}
    for p in glob.glob(f"{D}/results/**/ledger.jsonl", recursive=True):
        for l in open(p):
            try: r = json.loads(l)
            except ValueError: continue
            rid = r.get("region_id")
            if rid and "@" in rid and rid.split("@")[0] in F2 and r.get("fixed_points") == F2[rid.split("@")[0]]:
                CASES.setdefault(rid.split("@")[0], {}).setdefault(rid.split("@")[1], []).append(r)
                continue
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

ap = argparse.ArgumentParser(); ap.add_argument("--f", type=int, required=True)
ap.add_argument("cmd", choices=["status", "plan", "list"])
ap.add_argument("state", nargs="?", default="open", help="for list: open, never, failed, closed, sat")
ap.add_argument("--batch", type=int, default=8); ap.add_argument("--exclude", nargs="*", default=[])
a = ap.parse_args(); st = scan()
N = 32
cls = {rid: state(st.get(rid)) for rid in sorted(F2)}
for rid in CASES:
    closed, sat, detail = case_closed(rid)
    if sat: cls[rid] = "SAT"
    elif closed and cls[rid] != "SAT": cls[rid] = "CLOSED"
    print(f"  {rid}: case split -- {detail}" + (" -> CLOSED" if closed else ""), file=sys.stderr)
if a.cmd == "list":                         # one id per line, no truncation
    want = a.state.upper()
    print("\n".join(r for r, v in cls.items() if v == want))
    sys.exit(0)
if a.cmd == "status":
    from collections import Counter
    c = Counter(cls.values())
    by = Counter(arm for s in st.values() if s["closed_by"] for arm in s["closed_by"])
    print(f"f={FCLS} regions: {len(F2)}")
    for k in ("SAT", "CLOSED", "OPEN", "FAILED", "NEVER"): print(f"  {k:<7} {c.get(k, 0)}")
    print(f"  closed by: {dict(by)}  (a region closed by both counts under each)")
    print("  CLOSED = definite UNSAT verdicts, NO CERTIFICATE (no checked proofs yet)")
    for k in ("SAT", "FAILED", "OPEN"):
        ids = [r for r, v in cls.items() if v == k]
        if ids: print(f"  {k}: {' '.join(ids[:60])}" + (f" ... (+{len(ids)-60})" if len(ids) > 60 else ""))
    if c.get("SAT"): print(f"!! A SAT f={FCLS} REGION: see its WITNESSES/ file. Reproduce before anything else.")
else:
    skip = set()
    for f in a.exclude: skip |= {l.strip() for l in open(f) if l.strip()}
    todo = [r for r, v in cls.items() if v in ("NEVER", "OPEN", "FAILED") and r not in skip]
    out = f"{D}/campaign_f{FCLS}"; os.makedirs(out, exist_ok=True)
    for old in glob.glob(f"{out}/batch_*.txt"): os.remove(old)
    n = 0
    for i in range(0, len(todo), a.batch):
        open(f"{out}/batch_{n:03d}.txt", "w").write("\n".join(todo[i:i + a.batch]) + "\n"); n += 1
    print(f"{len(todo)} regions to run (excluded {len(skip & set(cls))} in flight) -> {n} batches of <= {a.batch} in {out}/")
