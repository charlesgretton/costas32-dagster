"""Latency and charged cost of a direct order-32 search, from per-prefix subtree estimates.
usage: python3 latency.py PREFIX_FILE RATE_NODES_PER_CORE_SECOND [SU_PER_CORE_HOUR=2] [WORKERS ...]
PREFIX_FILE: lines "rows estimate stderr" from `costas_tree prefixes`. Each prefix is one task.
Tasks are scheduled largest first onto the least-loaded worker (LPT list scheduling)."""
import sys, heapq, math
f=sys.argv[1]; rate=float(sys.argv[2]); su=float(sys.argv[3]) if len(sys.argv)>3 else 2.0
P_list=[int(x) for x in sys.argv[4:]] or [104,1040,10400,104000]
est=[]; var=0.0
for line in open(f):
    parts=line.split()
    if len(parts)>=2: est.append(float(parts[1])); var+=float(parts[2])**2 if len(parts)>2 else 0
tasks=sorted((e/rate for e in est), reverse=True)            # seconds per task on one core
total_nodes=sum(est); total_s=sum(tasks)
print(f"prefixes: {len(est):,}   total nodes: {total_nodes:.4e} (s.e. {math.sqrt(var):.2e})   rate: {rate:.3e} nodes/core-s")
print(f"total work: {total_s/3600:.4e} core-hours = {total_s/3600/8766:.4e} core-years = {total_s/3600*su/1000:.4e} KSU at {su:g} SU/core-hour")
mean=total_s/len(tasks); print(f"largest task: {tasks[0]/3600:.3e} core-hours ({tasks[0]/mean:.1f} x the mean); "
      f"largest 1% of tasks hold {sum(tasks[:max(1,len(tasks)//100)])/total_s:.1%} of the work")
print(f"{'workers':>9} {'wall time (days)':>17} {'efficiency':>11} {'charged KSU':>13} {'largest task / ideal wall':>27}")
for P in P_list:
    if P>len(tasks): print(f"{P:>9}  more workers than tasks: split deeper"); continue
    heap=[0.0]*P
    for t in tasks: heapq.heapreplace(heap, heap[0]+t)
    mk=max(heap); eff=total_s/(P*mk)
    print(f"{P:>9} {mk/86400:>17.4g} {eff:>11.1%} {P*mk/3600*su/1000:>13.4e} {tasks[0]/(total_s/P):>27.3f}")
