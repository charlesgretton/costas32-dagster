import numpy as np,time
from scipy.optimize import milp,LinearConstraint,Bounds
from scipy.sparse import lil_matrix
N=32; triples=[(r,r+l,r+2*l) for l in range(1,16) for r in range(N-2*l)]
allowed=[(a,b,c) for a in range(4) for b in range(4) for c in range(4) if (a+c-2*b)%4==0]
ny=128; nt=len(triples)*16; nv=ny+nt
# Position/balance equalities 36. For each t: t<= ya,yb,yc; t>=ya+yb+yc-2
nr=36+nt*4
A=lil_matrix((nr,nv)); lo=np.full(nr,-np.inf); hi=np.full(nr,np.inf); row=0
def y(i,s):return i*4+s
def t(w,u):return ny+w*16+u
for i in range(N):
 for s in range(4):A[row,y(i,s)]=1
 lo[row]=hi[row]=1;row+=1
for s in range(4):
 for i in range(N):A[row,y(i,s)]=1
 lo[row]=hi[row]=8;row+=1
for w,(i,j,k) in enumerate(triples):
 for u,(a,b,c) in enumerate(allowed):
  z=t(w,u)
  for yy in [y(i,a),y(j,b),y(k,c)]:
   A[row,z]=1;A[row,yy]=-1;hi[row]=0;row+=1
  A[row,z]=-1;A[row,y(i,a)]=1;A[row,y(j,b)]=1;A[row,y(k,c)]=1;hi[row]=2;row+=1
assert row==nr
obj=np.zeros(nv);obj[ny:]=1
print('model',nv,nr,A.nnz,flush=True)
res=milp(obj,integrality=np.ones(nv),bounds=Bounds(0,1),constraints=LinearConstraint(A.tocsr(),lo,hi),options={'time_limit':170,'mip_rel_gap':0,'presolve':True,'disp':True})
print('status',res.status,res.message,'fun',res.fun,'gap',getattr(res,'mip_gap',None),'bound',getattr(res,'mip_dual_bound',None),'nodes',getattr(res,'mip_node_count',None))
if res.x is not None:
 q=[int(np.argmax(res.x[4*i:4*i+4])) for i in range(N)]
 print(q);print([q.count(s) for s in range(4)])
 print('score',sum((q[i]+q[k]-2*q[j])%4==0 for i,j,k in triples))
