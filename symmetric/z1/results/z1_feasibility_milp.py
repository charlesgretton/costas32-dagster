import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
import csv
rows=[]
for L in range(16,31,2):
  for u in range((31-L)//2+1):
    v=u+L
    edges=[]
    for d in range(1,16):
      for a in range(32-d):
        b=a+d
        if a in (u,v) or b in (u,v): continue
        edges.append((d,a,b))
    A=lil_matrix((15+30,len(edges)),dtype=float); rhs=np.ones(45)
    # length rows
    for j,(d,a,b) in enumerate(edges): A[d-1,j]=1
    verts=[x for x in range(32) if x not in (u,v)]; idx={x:i for i,x in enumerate(verts)}
    for j,(d,a,b) in enumerate(edges): A[15+idx[a],j]=1;A[15+idx[b],j]=1
    res=milp(np.zeros(len(edges)),integrality=np.ones(len(edges)),bounds=Bounds(0,1),constraints=LinearConstraint(A.tocsr(),rhs,rhs),options={'time_limit':10})
    status='FEASIBLE' if res.x is not None else ('INFEASIBLE' if res.status==2 else f'STATUS_{res.status}')
    witness=''
    if res.x is not None:
      witness=';'.join(f'{d}:{a}-{b}' for x,(d,a,b) in zip(res.x,edges) if x>.5)
    rows.append([L,u,status,witness])
    print(L,u,status,flush=True)
with open('/mnt/data/z1_t_f0_feasibility.csv','w',newline='') as f:
 csv.writer(f).writerows([['L','u','status','witness']]+rows)
