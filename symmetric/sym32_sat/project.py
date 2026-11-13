#!/usr/bin/env python3
"""Campaign projection with correct censoring.

The previous version took the median of COMPLETED runs and multiplied by the
population, giving timed-out regions no contribution and returning nan for a
stratum with no completions. Both are wrong: a stratum with zero completions is
informative, and censored observations still consumed work.

Observed-work lower bound, per region i:

    L_i = t_i   if completed
        = c_i   if censored at cap c_i

  sum_i L_i  is a defensible lower bound on the work already demanded.

Also reports, per stratum: completion fraction, completed-time quantiles, the
restricted mean to the censoring horizon, and an explicit unresolved tail.
Never an unrestricted mean when the largest observations are censored -- the
tail is unidentified without stronger assumptions.
"""
import sys, csv, statistics
from collections import defaultdict

POP = {0: 1, 2: 256, 4: 13587, 6: 31103}

def km_restricted_mean(times, censored, horizon):
    """Kaplan-Meier restricted mean up to the horizon. With administrative
    censoring all at the same cap this reduces to the obvious estimator, but
    the general form is used so mixed caps stay correct."""
    ev = sorted([(t, 1) for t in times] + [(c, 0) for c in censored])
    n = len(ev); S = 1.0; prev = 0.0; area = 0.0; at_risk = n
    for t, is_event in ev:
        t = min(t, horizon)
        area += S * (t - prev); prev = t
        if is_event and at_risk > 0:
            S *= (1 - 1/at_risk)
        at_risk -= 1
        if prev >= horizon: break
    area += S * (horizon - prev)
    return area

def main(path, arm="kissat"):
    rows = list(csv.DictReader(open(path)))
    by = defaultdict(list)
    for r in rows: by[int(r["f"])].append(r)
    print(f"arm={arm}")
    print(f"{'f':>3} {'n':>5} {'done':>5} {'cens':>5} {'frac':>6} "
          f"{'med s':>9} {'RMST s':>9} {'sampleLB h':>11} {'pop':>8} "
          f"{'projRestr h':>12} {'atRisk':>7} {'tail':>6}")
    tot_lb = 0.0; unresolved = 0
    for f in sorted(by):
        g = by[f]
        done = [float(r[f"{arm}_s"]) for r in g if r[f"{arm}_status"] == "COMPLETED"]
        cens = [float(r[f"{arm}_cap_s"]) for r in g if r[f"{arm}_status"] != "COMPLETED"]
        n = len(g); L = sum(done) + sum(cens)          # observed-work lower bound
        frac = len(done)/n if n else 0.0
        hz = max(cens) if cens else (max(done) if done else 0.0)
        rmst = km_restricted_mean(done, cens, hz) if (done or cens) else float('nan')
        # population lower bound uses RMST, which is defined even with 0 completions
        lb = POP.get(f, 0) * rmst if rmst == rmst else float('nan')
        tot_lb += lb if lb == lb else 0.0
        unresolved += len(cens)
        med = statistics.median(done) if done else float('nan')
        p90 = (sorted(done)[int(0.9*(len(done)-1))] if done else float('nan'))
        print(f"{f:>3} {n:>5} {len(done):>5} {len(cens):>5} {frac:>6.2f} "
              f"{med:>9.1f} {rmst:>9.1f} {L/3600:>11.3f} {POP.get(f,0):>8,} "
              f"{lb/3600 if lb==lb else float('nan'):>12.1f} {len(cens):>7} {len(cens):>6}")
    samp = sum(float(r[f'{arm}_s']) if r[f'{arm}_status']=='COMPLETED'
               else float(r[f'{arm}_cap_s']) for r in rows)/3600
    print(f"\nTWO DISTINCT QUANTITIES -- do not conflate them:")
    print(f"  sample observed-work lower bound  : {samp:>12.3f} core-h")
    print(f"      sum over the ACTUAL runs of t_i (completed) or c_i (censored).")
    print(f"      A deterministic statement about work already demanded.")
    print(f"  population restricted-work proj.  : {tot_lb/3600:>12,.0f} core-h")
    print(f"      sum_f N_f * RMST_f(cap). An EXTRAPOLATION from a censored sample,")
    print(f"      counting work only THROUGH the horizon. It does NOT estimate the")
    print(f"      cost of finishing: all work beyond the cap is unidentified.")
    print(f"\n  unresolved in sample: {unresolved} of {len(rows)}")
    print(f"  No unrestricted mean is reported -- with censored largest observations")
    print(f"  the tail is unidentified without stronger assumptions.")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "kissat")
