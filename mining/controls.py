"""Negative control: do minimal obstructions of the Costas arrays differ from those of an equally sparse random set?
For a solution set A (all Costas arrays of order n, or the same number of random permutations), a dot set is
feasible iff some member of A contains it. The same sampled prefixes (Costas-valid, passing forward checking)
are analysed against both sets: dead or not, minimal infeasible subset by deletion, its size and shape."""
import sys, random, subprocess
from collections import Counter
n=int(sys.argv[1]); DEPTH=int(sys.argv[2]); SAMPLES=int(sys.argv[3]); random.seed(int(sys.argv[4]))
out=subprocess.run(['/tmp/listall','exact',str(n)],capture_output=True,text=True).stdout.splitlines()
costas=[tuple(map(int,l.split(','))) for l in out if ',' in l]
rnd=[tuple(random.sample(range(n),n)) for _ in range(len(costas))]
def index(A):
    ix={}
    for k,a in enumerate(A):
        for c,r in enumerate(a): ix.setdefault((c,r),set()).add(k)
    return ix
IX={'Costas':index(costas),'random':index(rnd)}
def feasible(ix,dots):
    s=None
    for d in dots:
        t=ix.get(d,set()); s=t if s is None else s&t
        if not s: return False
    return True
src=open('/home/claude/costas32/mining/mine_cores.py').read(); ns={'random':random,'n':n,'DEPTH':DEPTH}
exec("from itertools import combinations\n"+src[src.index("def legal(p,c,r):"):src.index("def feasible(dots)")],ns)
exec(src[src.index("def shape(dots):"):src.index("t0=time.time()")],ns); shape=ns['shape']
prefixes=[sorted(ns['random_prefix']().items()) for _ in range(SAMPLES)]
print(f"n={n}: {len(costas)} Costas arrays and {len(rnd)} random permutations; {SAMPLES} prefixes at depth {DEPTH}")
for name,ix in IX.items():
    dead=[p for p in prefixes if not feasible(ix,p)]
    cores=[]
    for p in dead:
        core=list(p)
        for d in list(core):
            trial=[x for x in core if x!=d]
            if not feasible(ix,trial): core=trial
        cores.append(core)
    sizes=Counter(len(c) for c in cores); shp=Counter(shape(c) for c in cores)
    rec=sum(k for k in shp.values() if k>1)
    print(f"  {name:<7}: dead {len(dead)}/{SAMPLES} ({len(dead)/SAMPLES:.0%}); obstruction sizes {dict(sorted(sizes.items()))}; "
          f"{len(shp)} distinct shapes; obstructions whose shape recurs: {rec}/{len(cores)} ({rec/max(1,len(cores)):.0%})")
