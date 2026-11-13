"""Native/SAT frontier: for dead prefixes that survive native checks and forward checking, compare the native
search's effort (nodes to exhaust the subtree) with a fresh CDCL solver's (conflicts to refute it).
A large nodes/conflict ratio marks a prefix where SAT holds a much shorter reason than the native search."""
import sys, random, subprocess, statistics
n=int(sys.argv[1]); DEPTH=int(sys.argv[2]); SAMPLES=int(sys.argv[3]); random.seed(int(sys.argv[4]))
src=open('mine_cores.py').read(); ns={'random':random,'n':n,'DEPTH':DEPTH}
exec(src.split("cnf,X=encode(n)")[0].replace("n=int(sys.argv[1]); DEPTH=int(sys.argv[2]); SAMPLES=int(sys.argv[3]); SEED=int(sys.argv[4]); random.seed(SEED)","n=%d; DEPTH=%d"%(n,DEPTH)),ns)
exec("from itertools import combinations\n"+src[src.index("def legal(p,c,r):"):src.index("def feasible(dots)")],ns)
cnf,X=ns['encode'](n); Solver=ns['Solver']
rows=[]
while len(rows)<SAMPLES:
    p=ns['random_prefix'](); dots=sorted(p.items())
    s=Solver(name='cadical195',bootstrap_with=cnf); sat=s.solve(assumptions=[X(c,r) for c,r in dots]); conf=s.accum_stats()['conflicts']; s.delete()
    if sat: continue
    nodes=int(subprocess.run(['/tmp/subtree',str(n)]+[str(r) for _,r in dots],capture_output=True,text=True).stdout)
    rows.append((nodes/max(1,conf),nodes,conf))
r=sorted(x[0] for x in rows)
print(f"n={n} depth={DEPTH}: {len(rows)} dead prefixes (each surviving native and forward checks)")
print(f"   native nodes per SAT conflict: min {r[0]:.2f}, median {statistics.median(r):.2f}, 90th pct {r[9*len(r)//10]:.2f}, max {r[-1]:.2f}")
print(f"   prefixes where SAT needs 10x fewer conflicts than native nodes: {sum(x>=10 for x in r)}; 5x: {sum(x>=5 for x in r)}")
print(f"   median native subtree {statistics.median(x[1] for x in rows):,.0f} nodes; median SAT conflicts {statistics.median(x[2] for x in rows):,.0f}")
