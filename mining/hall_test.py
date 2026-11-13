"""How many dead prefixes (no Costas completion, yet passing native checks and forward checking) does Hall's
matching condition detect?  Domains: legal rows of each unplaced column given the placed dots (pairwise checks
against placed dots only). Hall-dead = no perfect matching of unplaced columns to unused rows within domains."""
import sys, random, time
src=open('/home/claude/costas32/mining/mine_cores.py').read()
n=int(sys.argv[1]); DEPTH=int(sys.argv[2]); SAMPLES=int(sys.argv[3]); random.seed(int(sys.argv[4]))
ns={}; exec(src.split("cnf,X=encode(n)")[0].replace("n=int(sys.argv[1]); DEPTH=int(sys.argv[2]); SAMPLES=int(sys.argv[3]); SEED=int(sys.argv[4]); random.seed(SEED)","n=%d; DEPTH=%d"%(n,DEPTH)),ns)
exec(src[src.index("def legal(p,c,r):"):src.index("def feasible(dots)")],ns)
encode=ns['encode']; Solver=ns['Solver']; legal=ns['legal']
cnf,X=encode(n); S=Solver(name='cadical195',bootstrap_with=cnf); ns['random']=random
def perfect_matching(dom):
    match={}
    def aug(c,seen):
        for r in dom[c]:
            if r in seen: continue
            seen.add(r)
            if r not in match or aug(match[r],seen): match[r]=c; return True
        return False
    return all(aug(c,set()) for c in dom)
t=time.time(); dead=hall=0; total=0
while dead<SAMPLES:
    p=ns['random_prefix'](); total+=1
    if S.solve(assumptions=[X(c,r) for c,r in p.items()]): continue
    dead+=1
    dom={c:[r for r in range(n) if legal(p,c,r)] for c in range(DEPTH,n)}
    if not perfect_matching(dom): hall+=1
print(f"n={n} depth={DEPTH}: {total} prefixes passing native and forward checks; {dead} dead; caught by Hall: {hall} ({hall/dead:.0%})   [{time.time()-t:.0f} s]")
