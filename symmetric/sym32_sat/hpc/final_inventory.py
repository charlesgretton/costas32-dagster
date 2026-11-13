#!/usr/bin/env python3
"""Authoritative post-run inventory. Reads regions.csv, every result ledger and audit_results.csv;
writes final_region_status.csv (one row per region), f0_cases.csv (the 31 cases of R00000) and
FINAL_CAMPAIGN_MANIFEST.json. A Dagster closure counts only if its audit passed (audit_all.py);
a region closed by cases counts only if every case on one coordinate is an audited closure.
usage: final_inventory.py   (needs COSTAS_DATA)"""
import csv, glob, hashlib, json, os, re, sys, time
D = os.environ.get("COSTAS_DATA") or sys.exit("set COSTAS_DATA")
N = int(os.environ.get("COSTAS_N", 32))
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
REG = {r["region_id"]: r for r in csv.DictReader(open(f"{D}/regions.csv"))}
Fof = lambda r: [int(x) for x in r["fixed_points"].split()] if r["fixed_points"] else []
audited = {}
if os.path.exists(f"{D}/audit_results.csv"):
    for a in csv.DictReader(open(f"{D}/audit_results.csv")):
        if a["result"] == "PASS": audited.setdefault((a["region_id"], a["ledger"]), a)
recs, ledsha = {}, {}
for led in sorted(glob.glob(f"{D}/results/**/shard*/ledger.jsonl", recursive=True)):
    for l in open(led):
        r = json.loads(l); rid = r.get("region_id", "")
        base = rid.split("@")[0]
        if base not in REG or r.get("fixed_points") != Fof(REG[base]) or r.get("arm") == "split_child": continue
        r["_ledger"] = led; recs.setdefault(rid, []).append(r)
job = lambda p: (re.search(r"_(\d+)\.[A-Za-z0-9_-]+", p) or re.search(r"_(\d+)", "_")).group(1) if re.search(r"_(\d+)\.[A-Za-z0-9_-]+", p) else ""
def closing(rid):
    """the accepted closing record: Kissat UNSAT, else an audited Dagster UNSAT."""
    rs = recs.get(rid, [])
    sat = [r for r in rs if r["status"] == "SAT" and r.get("model_validated")]
    if sat: return "SAT-VALIDATED", sat[0]
    k = [r for r in rs if r["arm"] == "kissat" and r["status"] == "UNSAT"]
    if k: return "UNSAT-UNCERTIFIED", k[0]
    d = [r for r in rs if r["arm"] == "dagster_native_split" and r["status"] == "UNSAT_UNPROVEN"]
    da = [r for r in d if (rid, r["_ledger"]) in audited]
    if da: return "UNSAT-UNCERTIFIED", da[0]
    if d: return "UNAUDITED", d[0]
    if rs and all(r["status"] == "TIMEOUT" for r in rs): return "OPEN", rs[0]
    return ("ERROR" if rs else "NEVER"), (rs[0] if rs else None)
def row(rid, st, r, method=None):
    lp = r["_ledger"] if r else ""
    if lp and lp not in ledsha: ledsha[lp] = sha(lp)
    return dict(region_id=rid, fixed_points=REG[rid.split("@")[0]]["fixed_points"], f=REG[rid.split("@")[0]]["f"],
                final_status=st, closure_method=method or (r["arm"] if r else ""),
                cnf_sha256=(r or {}).get("parent_cnf_sha256", ""), generator_sha256=(r or {}).get("generator_sha256", ""),
                symmetry_breaking=(r or {}).get("symmetry_breaking") or "", wall_s=(r or {}).get("wall_s", ""),
                pbs_job=job(lp), ledger=lp, ledger_sha256=ledsha.get(lp, ""),
                audit=("PASS" if r and (rid, lp) in audited else ("n/a" if r and r["arm"] == "kissat" else "")),
                proof_status="none")
out, cases = [], []
for rid in sorted(REG):
    st, r = closing(rid)
    if st != "UNSAT-UNCERTIFIED" and st != "SAT-VALIDATED":
        F = Fof(REG[rid]); free = [i for i in range(N) if i not in F]
        for c in free:
            ks = [f"{rid}@{min(c,x)}-{max(c,x)}" for x in free if x != c]
            if not any(k in recs for k in ks): continue
            cs = [(k,) + closing(k) for k in ks]
            cases += [row(k, s2, r2) for k, s2, r2 in cs]
            if any(s2 == "SAT-VALIDATED" for _, s2, _ in cs): st, r = "SAT-VALIDATED", None
            elif all(s2 == "UNSAT-UNCERTIFIED" for _, s2, _ in cs): st, r = "UNSAT-UNCERTIFIED", None
            out.append(row(rid, st, None, f"case_split_{len(ks)}_on_{c}")); break
        else:
            out.append(row(rid, st, r))
        continue
    out.append(row(rid, st, r))
def write(p, rows):
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
write(f"{D}/final_region_status.csv", out)
if cases: write(f"{D}/f0_cases.csv", cases)
from collections import Counter
byf = {}
for o in out: byf.setdefault(o["f"], Counter())[o["final_status"]] += 1
meth = Counter(o["closure_method"] for o in out if o["final_status"] == "UNSAT-UNCERTIFIED")
man = {"schema": "sym32-final-campaign-manifest-v1", "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "regions": len(out), "by_class": {k: dict(v) for k, v in sorted(byf.items())},
       "closure_methods": dict(meth), "cases": {"rows": len(cases), "all_unsat": all(c["final_status"] == "UNSAT-UNCERTIFIED" for c in cases)},
       "sat_validated": sum(o["final_status"] == "SAT-VALIDATED" for o in out),
       "not_closed": sum(o["final_status"] not in ("UNSAT-UNCERTIFIED", "SAT-VALIDATED") for o in out),
       "claim_level": "search-closed, uncertified (no checked UNSAT proofs)",
       "digests": {"regions.csv": sha(f"{D}/regions.csv"), "final_region_status.csv": sha(f"{D}/final_region_status.csv"),
                   **({"f0_cases.csv": sha(f"{D}/f0_cases.csv")} if cases else {}),
                   **({"audit_results.csv": sha(f"{D}/audit_results.csv")} if os.path.exists(f"{D}/audit_results.csv") else {})}}
json.dump(man, open(f"{D}/FINAL_CAMPAIGN_MANIFEST.json", "w"), indent=1)
print(json.dumps({k: man[k] for k in ("regions", "by_class", "closure_methods", "cases", "sat_validated", "not_closed")}, indent=1))
