"""Second, independent parser of a completed campaign (shares no code with merge.py).
Checks: exactly one terminal record per task in tasks.txt, every one COMPLETE, no unknown ids, and
   sum(task nodes) + prefix_nodes == EXPECTED_NODES   and   sum(task arrays) == EXPECTED_ARRAYS.
usage: independent_check.py CAMPAIGN_DIR EXPECTED_NODES EXPECTED_ARRAYS"""
import sys, os, re
d, exp_nodes, exp_arrays = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ids = []; prefix_nodes = None
with open(os.path.join(d, 'tasks.txt')) as f:
    for line in f:
        if line[:1] == 'T': ids.append(line.split(' ', 1)[0])
        m = re.search(r'prefix_nodes=(\d+)', line)
        if m: prefix_nodes = int(m.group(1))
want = set(ids); seen = {}; extra = 0; nodes = 0; arrays = 0; bad = 0
for name in sorted(os.listdir(os.path.join(d, 'results'))):
    if not name.endswith('.out'): continue
    with open(os.path.join(d, 'results', name)) as f:
        for line in f:
            if not line.startswith('RESULT '): continue
            fields = line.split()
            tid = fields[1]
            if tid not in want: extra += 1; continue
            seen[tid] = seen.get(tid, 0) + 1
            if fields[2] != 'COMPLETE': bad += 1; continue
            kv = dict(x.split('=') for x in fields[3:])
            nodes += int(kv['nodes']); arrays += int(kv['arrays'])
checks = {
  'task ids unique in tasks.txt': len(ids) == len(want),
  'prefix_nodes present': prefix_nodes is not None,
  'every task has a record': len(seen) == len(want),
  'no task has two records': all(v == 1 for v in seen.values()),
  'no unknown task ids': extra == 0,
  'every record COMPLETE': bad == 0,
  f'nodes = {exp_nodes}': prefix_nodes is not None and nodes + prefix_nodes == exp_nodes,
  f'arrays = {exp_arrays}': arrays == exp_arrays,
}
print(f"tasks {len(want)}, records {sum(seen.values())}, task nodes {nodes}, prefix nodes {prefix_nodes}, total {nodes + (prefix_nodes or 0)}, arrays {arrays}")
for k, v in checks.items(): print(f"  {'PASS' if v else 'FAIL'}  {k}")
ok = all(checks.values()); print("INDEPENDENT CHECK", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
