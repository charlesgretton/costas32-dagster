#!/usr/bin/env python3
"""Decode a saved Dagster master log (dagster_logs/*.master.log.gz) for a depth-2 native
split: hardest messages with their edge choices, and work grouped by first-coordinate
partner. usage: COSTAS_N=32 analyse_master_log.py <log.gz> <fixed points> [a,b]
Coordinates default to the current dag_native_split rule; pass a,b explicitly for logs
from runs before 2026-10-15 (old rule: the two lowest free coordinates, e.g. 1,2)."""
import sys, re, gzip, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from gen_sym32_v2 import build, N
log, F = sys.argv[1], [int(x) for x in sys.argv[2].split(',')]
Fb, nv, var, cl, rep, edge = build(F)
free = [i for i in range(N) if i not in F]
inc = {c: sorted(v for (x, y), v in edge.items() if c in (x, y)) for c in free}
order = sorted(free, key=lambda c: (len(inc[c]), c))
from itertools import combinations
def seed_refutes(x, y):
    pts = sorted([(f, f) for f in F] + [(x, y), (y, x)])
    d = [(q[0]-p[0], q[1]-p[1]) for p, q in combinations(pts, 2)]; return len(set(d)) != len(d)
if len(sys.argv) > 3:                    # explicit coordinates, e.g. "1,2" for logs from the old rule
    ca, cb = (int(x) for x in sys.argv[3].split(","))
else:                                    # the current dag_native_split rule
    ca = order[0]
    cb = next((c for c in order if c != ca and seed_refutes(c, ca)), order[1])
rx = re.compile(r"^[IWEF](?:\d{8}|\d{4}) (\d\d):(\d\d):(\d\d\.\d+)")
cur, done, pre = {}, collections.defaultdict(list), collections.defaultdict(list)
for l in gzip.open(log, 'rt'):
    m = rx.match(l)
    if not m: continue
    t = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
    a = re.search(r"sending message to worker (\d+) message about node (\d+) assignments:(.*)$", l)
    if a:
        w, n = a.group(1), a.group(2)
        key = tuple(sorted(int(x) for x in re.findall(r"-?\d+", a.group(3)))) if n == '1' else None
        if w in cur and cur[w][0] == '1': pre[cur[w][2]].append(t - cur[w][1])
        cur[w] = (n, t, key); continue
    b = re.search(r"received MPI_TAG_REQUEST_FOR_ASSIGNMENT from worker (\d+)", l)
    if b and b.group(1) in cur:
        n, t0, key = cur.pop(b.group(1))
        if n == '1': done[key].append(t - t0)
def partner(c, key):
    pos = [v for v in key if v > 0 and v in var and c in (var[v]['a'], var[v]['b'])]
    return [var[v]['b'] if var[v]['a'] == c else var[v]['a'] for v in pos]
msgs = {k: max(v) for k, v in done.items()}             # time of the copy that finished
tot = sorted(msgs.values(), reverse=True)
print(f"split coordinates: a={ca} ({len(inc[ca])} partners), b={cb} ({len(inc[cb])} partners)")
print(f"distinct completed messages: {len(msgs)}   pre-empted copies: {sum(len(v) for v in pre.values())}")
print(f"durations: top 10 = {[round(x,1) for x in tot[:10]]}")
print(f"           #>20s = {sum(x>20 for x in tot)}, #>10s = {sum(x>10 for x in tot)}, median = {tot[len(tot)//2]:.1f}s, total = {sum(tot):.0f}s")
print("hardest messages (a-partner, b-partner):")
for k in sorted(msgs, key=lambda k: -msgs[k])[:8]:
    print(f"   {msgs[k]:6.1f}s  a->{partner(ca,k)}  b->{partner(cb,k)}   copies finished {len(done[k])}, pre-empted {len(pre.get(k,[]))}")
by_a = collections.defaultdict(list)
for k, d in msgs.items():
    p = partner(ca, k); by_a[p[0] if p else None].append(d)
rows = sorted(by_a.items(), key=lambda kv: -sum(kv[1]))
print("work by a-partner (i.e. by depth-1 child), top 6:")
for p, ds in rows[:6]:
    print(f"   a->{p}: {len(ds)} msgs, total {sum(ds):6.0f}s, max {max(ds):6.1f}s")
print(f"   ... share of total work in the top depth-1 child: {100*sum(rows[0][1])/sum(tot):.0f}%")
