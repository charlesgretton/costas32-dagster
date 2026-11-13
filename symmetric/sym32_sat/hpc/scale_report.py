#!/usr/bin/env python3
"""Per region: Kissat's Stage-1 time (1 core) against Dagster's native split (k workers),
with where Dagster's wall time went. All timings come from the master's log timestamps."""
import json, sys, glob
s1 = {}
for l in open(sys.argv[1]):
    r = json.loads(l)
    if r.get("arm") == "kissat": s1[r["region_id"]] = r
f = lambda v, u="s": "-" if v is None else f"{v:.0f}{u}"
for d in sys.argv[2:]:
    R = [json.loads(l) for p in glob.glob(f"{d}/shard*/ledger.jsonl") for l in open(p)]
    R = [r for r in R if r["arm"] == "dagster_native_split"]
    print(f"== {d.rstrip('/').split('/')[-1]}")
    print(f"   {'region':<7} f {'kissat':>7} {'dagster':>7} {'wkrs':>4} {'msgs':>9} {'dup':>4} "
          f"{'start':>5} {'disp':>5} {'tail':>5} {'longest':>7} {'p90':>5} {'busy':>5} {'pre-empt':>9} "
          f"{'wall x':>6} {'core x':>6} status")
    for r in sorted(R, key=lambda r: r["region_id"]):
        k = s1.get(r["region_id"]); ks = k["wall_s"] if k and k["status"] == "UNSAT" else None
        dw = r["wall_s"]; done = r["status"] in ("UNSAT_UNPROVEN", "SAT")
        S = r.get("dagster_stats") or {}; sd = S.get("sends") or {}
        n1 = sd.get("1") or {}; P = sd.get("phases") or {}; mt = (S.get("message_times") or {}).get("1") or {}
        busy = f"{100*mt['work_s']/(r['dagster_workers']*dw):.0f}%" if mt.get("work_s") and dw else "-"
        pre = f"{mt.get('preempted',0)}/{f(mt.get('preempted_s'))}" if mt else "-"
        ktxt = f"{ks:.0f}s" if ks else (f">{k['cap_s']:.0f}s" if k else "?")
        wx = f"{ks/dw:.1f}" if (ks and done) else "-"
        cx = f"{(r['dagster_workers']+1)*dw/ks:.1f}" if (ks and done) else "-"
        print(f"   {r['region_id']:<7} {r['f']} {ktxt:>7} {(f'{dw:.0f}s' if done else '>'+f(r['cap_s'])):>7} "
              f"{r['dagster_workers']:>4} {str(n1.get('distinct','-'))+'/'+str(r['messages_upper']):>9} "
              f"{str(n1.get('duplicate_sends','-')):>4} {f(P.get('startup_s')):>5} {f(P.get('dispatch_s')):>5} "
              f"{f(P.get('tail_s')):>5} {f(mt.get('max_s')):>7} {f(mt.get('p90_s')):>5} {busy:>5} {pre:>9} "
              f"{wx:>6} {cx:>6} {r['status']}")
print("""
   msgs     distinct node-1 messages generated / the split's upper bound
   dup      node-1 sends beyond the distinct messages (copies given to idle workers, or re-sends)
   start    until the first node-1 message is sent (all workers on the source node)
   disp     until every node-1 message has been sent at least once
   tail     from then to the last finish: only the hardest messages left, raced by copies
   longest  longest single node-1 message;  p90: 90th percentile message time
   busy     total node-1 message time / (workers x wall)
   pre-empt workers reassigned mid-message by the master's rebalancing / time they had spent
   A run is critical-path bound when 'longest' is close to 'tail' + some of 'disp'.""")
