"""Does a per-lag matching condition explain what the strong LP relaxation proves?
For each lag d, every column pair (i, i+d) must take a distinct vertical difference e, from the differences its
columns' remaining rows allow, excluding differences already realised at lag d by two placed dots.
If some lag has no matching saturating its pairs, the prefix is dead (Hall's theorem on pairs and differences)."""
import sys, random, time
def setup(n,seed):
    sys.argv=['lp_relax.py',str(n),'5','1',str(seed)]
    g={'__name__':'lp'}; exec(open('lp_relax.py').read().split("t=time.time()")[0],g); return g
def domains(g,n,p):
    return {c:([p[c]] if c in p else [r for r in range(n) if g['ns']['legal'](p,c,r)]) for c in range(n)}
def matching_ok(cands):
    match={}
    def aug(u,seen):
        for v in cands[u]:
            if v in seen: continue
            seen.add(v)
            if v not in match or aug(match[v],seen): match[v]=u; return True
        return False
    return all(aug(u,set()) for u in cands)
def lag_dead(n,p,dom):
    for d in range(1,n):
        cands={}
        for i in range(n-d):
            j=i+d
            cands[i]={s-r for r in dom[i] for s in dom[j] if s!=r}
        if not matching_ok(cands): return True
    return False
def row_dead(n,p,dom):
    free={c:dom[c] for c in range(n) if c not in p}
    return not matching_ok(free)
for n,D,samples,seed in [(12,7,25,5),(14,8,16,6)]:
    g=setup(n,seed); g['ns']['DEPTH']=D; random.seed(seed); dead=[]
    while len(dead)<samples:
        pr=g['ns']['random_prefix'](); dots=sorted(pr.items())
        if not g['S'].solve(assumptions=[g['X'](c,r) for c,r in dots]): dead.append(pr)
    lp=lag=row=both=0
    for pr in dead:
        dom=domains(g,n,pr); dots=sorted(pr.items())
        a=not g['lp_feasible'](g['models']['strong'],dots); b=lag_dead(n,pr,dom); c=row_dead(n,pr,dom)
        lp+=a; lag+=b; row+=c; both+= a and (b or c)
    print(f"order {n} depth {D}: {len(dead)} dead prefixes; strong LP {lp}; per-lag matching {lag}; row matching (Hall) {row}; "
          f"LP cases explained by a matching condition {both}/{lp}", flush=True)
