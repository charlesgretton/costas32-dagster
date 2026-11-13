"""Is an obstruction structural or accidental? Place each mined shape at every translation on an n'xn' board
and check whether any Costas array of order n' contains it. A structural obstruction is infeasible everywhere."""
import sys, json, random, time
from collections import Counter
sys.argv=[sys.argv[0]]+sys.argv[1:]
src=open('/home/claude/costas32/mining/mine_cores.py').read()
ns={}; exec(src.split("cnf,X=encode(n)")[0].replace("n=int(sys.argv[1]); DEPTH=int(sys.argv[2]); SAMPLES=int(sys.argv[3]); SEED=int(sys.argv[4]); random.seed(SEED)","n=0"),ns)
exec(src[src.index("def shape(dots):"):src.index("t0=time.time()")],ns)
encode=ns['encode']; shape=ns['shape']; Solver=ns['Solver']
data=json.load(open(sys.argv[1])); cores=[[tuple(d) for d in m] for m in data['cores']]
shapes=Counter(shape(m) for m in cores)
random.seed(3)
chosen=[s for s,k in shapes.most_common() if k>1]
rest=[s for s,k in shapes.items() if k==1]; chosen+=random.sample(rest,min(len(rest),12-len(chosen)))
for N in map(int,sys.argv[2:]):
    cnf,X=encode(N); S=Solver(name='cadical195',bootstrap_with=cnf); t=time.time()
    print(f"--- order {N}")
    allinf=0
    for sh in chosen:
        W=max(c for c,_ in sh); H=max(r for _,r in sh); pos=inf=0
        for dc in range(N-W):
            for dr in range(N-H):
                pos+=1; inf+= not S.solve(assumptions=[X(c+dc,r+dr) for c,r in sh])
        allinf+= (inf==pos)
        print(f"   shape {sh}: infeasible at {inf}/{pos} positions")
    print(f"   shapes infeasible at every position: {allinf}/{len(chosen)}   ({time.time()-t:.0f} s)")
