"""Exact (cutting-planes PB solver) on dead prefixes that LP-2 cannot certify (below the transition).
Native strong model: binary x[i,r], y[i,j,r,s]; column/row equalities; pair marginals; displacement capacities <= 1.
Prefix placements are given as assumptions to a fresh solver. Compared with the native subtree size of each prefix.
usage: exact_pilot.py N DEPTHS DEAD_PER_DEPTH ALIVE SEED"""
import sys, random, time, subprocess, statistics, exact, os, json
n=int(sys.argv[1]); DEPTHS=[int(x) for x in sys.argv[2].split(',')]; NDEAD=int(sys.argv[3]); NALIVE=int(sys.argv[4]); SEED=int(sys.argv[5])
sys.argv=['lp_relax.py',str(n),'5','1',str(SEED)]
g={'__name__':'lp'}; exec(open('lp_relax.py').read().split("t=time.time()")[0],g); random.seed(SEED)
pairs=[(i,j) for i in range(n) for j in range(i+1,n)]
def build(opts):
    s=exact.Exact([("verbosity","0")]+opts)
    X=lambda i,r: f"x{i}_{r}"; Y=lambda i,j,r,t: f"y{i}_{j}_{r}_{t}"
    for i in range(n):
        for r in range(n): s.addVariable(X(i,r))
    for (i,j) in pairs:
        for r in range(n):
            for t in range(n):
                if r!=t: s.addVariable(Y(i,j,r,t))
    for i in range(n): s.addConstraint([(1,X(i,r)) for r in range(n)],True,1,True,1)
    for r in range(n): s.addConstraint([(1,X(i,r)) for i in range(n)],True,1,True,1)
    cap={}
    for (i,j) in pairs:
        for r in range(n): s.addConstraint([(1,Y(i,j,r,t)) for t in range(n) if t!=r]+[(-1,X(i,r))],True,0,True,0)
        for t in range(n): s.addConstraint([(1,Y(i,j,r,t)) for r in range(n) if r!=t]+[(-1,X(j,t))],True,0,True,0)
        for r in range(n):
            for t in range(n):
                if r!=t: cap.setdefault((j-i,t-r),[]).append(Y(i,j,r,t))
    for vs in cap.values(): s.addConstraint([(1,v) for v in vs],False,0,True,1)
    return s, X
KEYS=['conflicts','decisions','propagations','learned clauses','learned cardinalities','learned general constraints','saturation steps','number of multiply-weakens on conflict']
def solve(dots,opts):
    s,X=build(opts); s.setAssumptions([(X(c,r),1) for c,r in dots]); t=time.time()
    res=s.runFull(False,60); st=dict(s.getStats()); return res,time.time()-t,{k:st.get(k,0) for k in KEYS}
rows=[]
for D in DEPTHS:
    g['ns']['DEPTH']=D; dead=[]; alive=[]
    while len(dead)<NDEAD or len(alive)<NALIVE:
        p=g['ns']['random_prefix'](); dots=sorted(p.items())
        live=g['S'].solve(assumptions=[g['X'](c,r) for c,r in dots])
        if live:
            if len(alive)<NALIVE: alive.append(dots)
            continue
        if len(dead)<NDEAD and g['lp_feasible'](g['models']['strong'],dots): dead.append(dots)
    for dots in alive:
        r,_,_=solve(dots,[]); assert r=="SAT", ("live control not SAT", r, dots)
    for dots in dead:
        nodes=int(subprocess.run(['/tmp/subtree',str(n)]+[str(r) for _,r in dots],capture_output=True,text=True).stdout)
        ra,ta,sa=solve(dots,[]); rb,tb,sb=ra,ta,sa   # this Exact build has no LP integration
        rows.append({'n':n,'k':D,'nodes':nodes,'with_lp':(ra,ta,sa),'no_lp':(rb,tb,sb)})
    sub=[r for r in rows if r['k']==D]
    def med(f): return statistics.median(f(r) for r in sub)
    print(f"n={n} k={D}: {len(sub)} LP-feasible dead prefixes, {len(alive)} live controls SAT; "
          f"refuted {sum(r['with_lp'][0] in ('UNSAT','INCONSISTENT') for r in sub)}/{len(sub)}", flush=True)
    print(f"   median native subtree {med(lambda r:r['nodes']):,.0f} nodes | Exact conflicts {med(lambda r:r['with_lp'][2]['conflicts']):,.0f} | native nodes per conflict {med(lambda r:r['nodes']/max(1,r['with_lp'][2]['conflicts'])):.1f}", flush=True)
    print(f"   prefixes refuted with <=10 conflicts: {sum(r['with_lp'][2]['conflicts']<=10 for r in sub)}; "
          f"learned cardinalities/general constraints (median): {med(lambda r:r['with_lp'][2]['learned cardinalities']):.0f}/{med(lambda r:r['with_lp'][2]['learned general constraints']):.0f}; "
          f"median Exact time {med(lambda r:r['with_lp'][1]):.2f} s", flush=True)
json.dump(rows,open(f"exact_pilot_n{n}.json","w"))
