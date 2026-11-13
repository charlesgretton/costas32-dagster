import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
import time
N=32
triples=[(r,r+l,r+2*l) for l in range(1,16) for r in range(N-2*l)]
T=len(triples)
ny=N*4
nt=T*64
nv=ny+nt
# rows: position 32, balance4, tuple-one 240, marginal 3*4*240=2880 =>3156
nr=32+4+T+T*12
A=lil_matrix((nr,nv),dtype=np.float64); b=np.zeros(nr); row=0
# y index
def yi(i,s): return i*4+s
def ti(w,a,bv,c): return ny+w*64+a*16+bv*4+c
for i in range(N):
 for s in range(4): A[row,yi(i,s)]=1
 b[row]=1; row+=1
for s in range(4):
 for i in range(N): A[row,yi(i,s)]=1
 b[row]=8; row+=1
for w,(i,j,k) in enumerate(triples):
 for a in range(4):
  for bb in range(4):
   for c in range(4): A[row,ti(w,a,bb,c)]=1
 b[row]=1; row+=1
 # first marginal
 for a in range(4):
  for bb in range(4):
   for c in range(4): A[row,ti(w,a,bb,c)]=1
  A[row,yi(i,a)]=-1; row+=1
 for bb in range(4):
  for a in range(4):
   for c in range(4): A[row,ti(w,a,bb,c)]=1
  A[row,yi(j,bb)]=-1; row+=1
 for c in range(4):
  for a in range(4):
   for bb in range(4): A[row,ti(w,a,bb,c)]=1
  A[row,yi(k,c)]=-1; row+=1
assert row==nr
obj=np.zeros(nv)
for w in range(T):
 for a in range(4):
  for bb in range(4):
   for c in range(4):
    if (a+c-2*bb)%4==0: obj[ti(w,a,bb,c)]=1
print('model',nv,nr,A.nnz,flush=True)
t=time.time()
res=milp(obj, integrality=np.ones(nv), bounds=Bounds(0,1), constraints=LinearConstraint(A.tocsr(),b,b), options={'time_limit':300,'mip_rel_gap':0.0,'presolve':True,'disp':True})
print('time',time.time()-t,'status',res.status,res.message,'fun',res.fun,'bound',getattr(res,'mip_node_count',None),getattr(res,'mip_gap',None),flush=True)
if res.x is not None:
 q=[]
 for i in range(N): q.append(int(np.argmax(res.x[i*4:i*4+4])))
 print('q',q)
 print('counts',[q.count(s) for s in range(4)])
 sc=sum((q[i]+q[k]-2*q[j])%4==0 for i,j,k in triples)
 print('scorecheck',sc)
