import csv
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix


def ll_cross(e1,e2):
    a,b=e1; c,d=e2
    h={a:b,b:a,c:d,d:c}
    for x in e1:
        for y in e2:
            if abs(x-y)>=16 and abs(h[x]-h[y])>=16:
                return True
    return False

rows=[]
for L in range(16,31,2):
    for u in range((31-L)//2+1):
        long=(u,u+L)
        edges=[]
        for length in range(1,16):
            for a in range(32-length):
                b=a+length
                if a in long or b in long: continue
                if ll_cross((a,b),long): continue
                edges.append((length,a,b))
        n=len(edges)
        cons=[]; los=[]; his=[]
        # one edge of each short length
        for length in range(1,16):
            cons.append([j for j,e in enumerate(edges) if e[0]==length]);los.append(1);his.append(1)
        # each remaining vertex exactly once
        for x in range(32):
            if x in long: continue
            cons.append([j for j,e in enumerate(edges) if x in e[1:]]);los.append(1);his.append(1)
        # pairwise incompatible selected cycles create another LL pair
        for i in range(n):
            ei=edges[i][1:]
            for j in range(i+1,n):
                if edges[i][0]==edges[j][0]: continue
                if set(ei)&set(edges[j][1:]): continue
                if ll_cross(ei,edges[j][1:]):
                    cons.append([i,j]);los.append(-np.inf);his.append(1)
        A=lil_matrix((len(cons),n),dtype=float)
        for r,idxs in enumerate(cons):
            for j in idxs:A[r,j]=1
        res=milp(np.zeros(n),integrality=np.ones(n),bounds=Bounds(0,1),
                 constraints=LinearConstraint(A.tocsr(),np.array(los),np.array(his)),
                 options={'time_limit':60,'mip_rel_gap':0})
        status='FEASIBLE' if res.x is not None else ('INFEASIBLE' if res.status==2 else f'STATUS_{res.status}')
        witness=''
        if res.x is not None:
            witness=';'.join(f'{d}:{a}-{b}' for x,(d,a,b) in zip(res.x,edges) if x>.5)
        rows.append([L,u,status,res.status,res.message,witness])
        print(L,u,status,flush=True)
with open('/mnt/data/z1_t_f0_mode_b_results.csv','w',newline='') as f:
    csv.writer(f).writerows([['L','u','status','solver_status','message','witness']]+rows)
