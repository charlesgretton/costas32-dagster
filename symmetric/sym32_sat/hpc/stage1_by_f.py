#!/usr/bin/env python3
"""Stage-1 results by fixed-point count f, with a population projection.

RMST(cap) = mean over sampled regions of min(t_i, cap): censored runs count as
the cap. N_f * RMST is the work needed to take every region in stratum f to the
cap -- a projection through the horizon only. Work beyond the cap is unknown.
usage: stage1_by_f.py <ledger.jsonl>"""
import json, sys, statistics
POP = {0: 1, 2: 256, 4: 13587, 6: 31103}
NOPROJ = "--no-projection" in sys.argv
R = [json.loads(l) for l in open(sys.argv[1])]
R = [r for r in R if r.get("arm") == "kissat"]
print(f"{'f':>2} {'n':>4} {'done':>5} {'cens':>5} {'err':>4} {'frac':>5} {'median s':>9} "
      f"{'RMST s':>7} {'regions':>8} {'proj core-h':>11} {'proj open':>9}")
tot_h = tot_open = 0
for f in sorted({r["f"] for r in R}):
    g = [r for r in R if r["f"] == f]
    done = [r for r in g if r["status"] in ("SAT", "UNSAT")]
    cens = [r for r in g if r["status"] == "TIMEOUT"]
    err = [r for r in g if r not in done and r not in cens]
    cap = max(r["cap_s"] for r in g)
    rmst = (sum(min(r["wall_s"], cap) for r in done) + cap * len(cens)) / max(1, len(done) + len(cens))
    frac = len(done) / max(1, len(done) + len(cens))
    med = statistics.median(r["wall_s"] for r in done) if done else float("nan")
    h = POP[f] * rmst / 3600; op = POP[f] * (1 - frac)
    tot_h += h; tot_open += op
    print(f"{f:>2} {len(g):>4} {len(done):>5} {len(cens):>5} {len(err):>4} {frac:>5.0%} {med:>9.1f} "
          f"{rmst:>7.0f} {POP[f]:>8,} {h:>11,.0f} {op:>9,.0f}")
if NOPROJ:
    print("\n(projection columns are not meaningful for a tail-only sample)"); sys.exit(0)
print(f"\nall 44,947 regions taken to the {cap:.0f} s cap: ~{tot_h:,.0f} core-h (~{2*tot_h:,.0f} SU at 2 SU per core-hour)")
print(f"regions projected still open at the cap: ~{tot_open:,.0f}  -- their cost beyond the cap is unknown")
if any(r["status"] == "SAT" for r in R): print("!! SAT REGION PRESENT -- see WITNESSES/ and stop")
