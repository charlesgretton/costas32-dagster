#!/usr/bin/env python3
"""Per-arm stage summary. Censoring kept: L_i = t_i if finished, cap if not.
Reports completion fraction, observed-work lower bound, and any validation failure."""
import json, sys, statistics
led, arm = sys.argv[1], sys.argv[2]
R = [json.loads(l) for l in open(led)]; R = [r for r in R if r.get("arm") == arm]
if not R: print(f"{arm}: no records"); sys.exit(0)
tkey = "T_core_s" if arm == "kissat_split_agg" else "wall_s"
done = [r for r in R if r["status"] in ("SAT", "UNSAT", "UNSAT_UNPROVEN")]
cens = [r for r in R if r["status"] == "TIMEOUT"]            # ONLY timeouts are censored
errs = [r for r in R if r not in done and r not in cens]     # errors are failures, not censoring
L = sum(r[tkey] for r in done) + sum(r["cap_s"] for r in cens)
sat = [r for r in R if r["status"] == "SAT"]
bad = [r for r in R if r["status"] == "SAT_MODEL_INVALID"]
print(f"== {arm}: {len(R)} regions, completed {len(done)} ({len(done)/len(R):.0%}), censored {len(cens)}, ERRORS {len(errs)}")
if errs:
    from collections import Counter
    print(f"   *** {len(errs)} RUN(S) FAILED, not censored: {dict(Counter(r['status'] for r in errs))}")
    print(f"   *** errors are excluded from the work bound; fix and rerun before trusting this arm")
if done: print(f"   completed {tkey}: median {statistics.median(r[tkey] for r in done):.1f}s, max {max(r[tkey] for r in done):.1f}s")
print(f"   observed-work lower bound: {L/3600:.2f} core-h   (censored runs charged their cap)")
print(f"   SAT regions: {len(sat)}   *** {len(bad)} SAT MODEL(S) FAILED VALIDATION ***" if bad else f"   SAT regions: {len(sat)}")
if sat: import os
if sat: print(f"   !! A SAT REGION AT ORDER {os.environ.get('COSTAS_N','32')} IS A CANDIDATE TRANSPOSE-SYMMETRIC COSTAS ARRAY -- reproduce and check before anything else")
