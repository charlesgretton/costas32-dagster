"""LP relaxation diagnostic for dead prefixes. Native PB model: x[i,r] (placements), y[i,j,r,s] (pair i<j at rows r!=s).
Columns and rows sum to 1; each displacement class (d,e) has capacity 1 over the pair variables.
weak:   y <= x[i,r], y <= x[j,s], y >= x[i,r]+x[j,s]-1          (McCormick)
strong: sum_s y[i,j,r,s] = x[i,r],  sum_r y[i,j,r,s] = x[j,s]    (first-level RLT: each column pair carries one unit)
A prefix is LP-infeasible if no fractional point satisfies the model with the prefix's placements fixed to 1."""
import sys, random, numpy as np, time
from scipy.optimize import linprog
from scipy.sparse import coo_matrix
from itertools import combinations
n=int(sys.argv[1]); DEPTHS=[int(x) for x in sys.argv[2].split(',')]; SAMPLES=int(sys.argv[3]); random.seed(int(sys.argv[4]))
src=open('mine_cores.py').read()
ns={'random':random,'n':n,'DEPTH':0}
exec(src.split("cnf,X=encode(n)")[0].replace("n=int(sys.argv[1]); DEPTH=int(sys.argv[2]); SAMPLES=int(sys.argv[3]); SEED=int(sys.argv[4]); random.seed(SEED)","n=%d; DEPTH=0"%n),ns)
exec("from itertools import combinations\n"+src[src.index("def legal(p,c,r):"):src.index("def feasible(dots)")],ns)
cnf,X=ns['encode'](n); S=ns['Solver'](name='cadical195',bootstrap_with=cnf)
xid=lambda i,r: i*n+r
pairs=[(i,j) for i in range(n) for j in range(i+1,n)]
yid={}; k=n*n
for (i,j) in pairs:
    for r in range(n):
        for s in range(n):
            if r!=s: yid[(i,j,r,s)]=k; k+=1
NV=k
def build(strong):
    Aeq=[];beq=[];Aub=[];bub=[]; row=[0]; R=[];C=[];V=[]
    def add(target,coeffs,b):
        target.append((coeffs,b))
    for i in range(n): add(Aeq,{xid(i,r):1 for r in range(n)},1)
    for r in range(n): add(Aeq,{xid(i,r):1 for i in range(n)},1)
    if strong:
        for (i,j) in pairs:
            for r in range(n): add(Aeq,{**{yid[(i,j,r,s)]:1 for s in range(n) if s!=r}, xid(i,r):-1},0)
            for s in range(n): add(Aeq,{**{yid[(i,j,r,s)]:1 for r in range(n) if r!=s}, xid(j,s):-1},0)
    else:
        for (i,j,r,s),v in yid.items():
            add(Aub,{v:1,xid(i,r):-1},0); add(Aub,{v:1,xid(j,s):-1},0); add(Aub,{xid(i,r):1,xid(j,s):1,v:-1},1)
    cap={}
    for (i,j,r,s),v in yid.items(): cap.setdefault((j-i,s-r),{})[v]=1
    for key,co in cap.items(): add(Aub,co,1)
    def mat(L):
        rr=[];cc=[];vv=[]
        for t,(co,b) in enumerate(L):
            for c,v in co.items(): rr.append(t);cc.append(c);vv.append(v)
        return coo_matrix((vv,(rr,cc)),shape=(len(L),NV)).tocsr(), np.array([b for _,b in L],float)
    return mat(Aeq), mat(Aub) if Aub else (None,None)
models={'weak':build(False),'strong':build(True)}
def lp_feasible(model,dots):
    (Aeq,beq),(Aub,bub)=model
    lb=np.zeros(NV); ub=np.ones(NV)
    for c,r in dots: lb[xid(c,r)]=1
    res=linprog(np.zeros(NV),A_ub=Aub,b_ub=bub,A_eq=Aeq,b_eq=beq,bounds=np.column_stack([lb,ub]),method='highs')
    return res.status==0
t=time.time()
for D in DEPTHS:
    ns['DEPTH']=D; dead=[];alive=[]
    while len(dead)<SAMPLES:
        p=ns['random_prefix'](); dots=sorted(p.items())
        (alive if S.solve(assumptions=[X(c,r) for c,r in dots]) else dead).append(dots)
    out={m:sum(not lp_feasible(models[m],d) for d in dead) for m in models}
    sane={m:all(lp_feasible(models[m],d) for d in alive[:5]) for m in models}
    print(f"n={n} depth {D}: {len(dead)} dead prefixes; LP-infeasible: weak {out['weak']} ({out['weak']/len(dead):.0%}), "
          f"strong {out['strong']} ({out['strong']/len(dead):.0%});  completable prefixes LP-feasible: {sane}  [{time.time()-t:.0f} s]", flush=True)
