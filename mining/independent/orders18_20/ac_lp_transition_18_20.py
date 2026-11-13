import random,json,time,statistics
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix,csr_matrix

def occset(p):return {(j-i,p[j]-p[i]) for j in range(len(p)) for i in range(j)}
def valid_add(p,r):
 if r in p:return False
 O=occset(p);c=len(p)
 return all((c-i,r-p[i]) not in O for i in range(c))
def randprefix(n,k,rng):
 for _ in range(10000):
  p=[]
  for c in range(k):
   v=[r for r in range(n) if valid_add(p,r)]
   if not v:break
   p.append(rng.choice(v))
  if len(p)==k:return tuple(p)
 raise RuntimeError

def domains(n,p):
 O=occset(p);used=set(p);D={}
 for c in range(len(p),n):
  s=set()
  for r in range(n):
   if r in used:continue
   new=[];ok=True
   for i,a in enumerate(p):
    q=(c-i,r-a)
    if q in O or q in new:ok=False;break
    new.append(q)
   if ok:s.add(r)
  D[c]=s
 return D,O

def pair_ok(a,ra,b,rb,p,O):
 if ra==rb:return False
 # all new displacements induced by either candidate against prefix and each other unique and not occupied
 new=[]
 for c,r in [(a,ra),(b,rb)]:
  for i,x in enumerate(p):
   if c>i:q=(c-i,r-x)
   else:q=(i-c,x-r)
   if q in O or q in new:return False
   new.append(q)
 q=(b-a,rb-ra) if b>a else (a-b,ra-rb)
 if q in O or q in new:return False
 new.append(q)
 return True

def ac(n,p):
 D,O=domains(n,p);initial={c:len(s) for c,s in D.items()};checks=0;rounds=0;removed=0
 if any(not s for s in D.values()):return True,initial,D,0,0,0
 changed=True
 while changed:
  changed=False;rounds+=1
  for a in list(D):
   for ra in list(D[a]):
    supported=True
    for b in D:
     if a==b:continue
     ok=False
     for rb in D[b]:
      checks+=1
      if pair_ok(a,ra,b,rb,p,O):ok=True;break
     if not ok:supported=False;break
    if not supported:
     D[a].remove(ra);removed+=1;changed=True
     if not D[a]:return True,initial,D,rounds,removed,checks
 return False,initial,D,rounds,removed,checks

def lp2(n,p,D):
 # restrict x to domain for future, fixed prefix. y only allowed row pairs
 xidx={};t=0
 allowed={i:({p[i]} if i<len(p) else set(D[i])) for i in range(n)}
 for i in range(n):
  for a in allowed[i]:xidx[i,a]=t;t+=1
 yidx={};qrows={}
 for i in range(n):
  for j in range(i+1,n):
   for a in allowed[i]:
    for b in allowed[j]:
     if a==b:continue
     yidx[i,j,a,b]=t;qrows.setdefault((j-i,b-a),[]).append(t);t+=1
 eq=[];rhs=[]
 for i in range(n):eq.append([(xidx[i,a],1) for a in allowed[i]]);rhs.append(1)
 for r in range(n):
  row=[(xidx[i,r],1) for i in range(n) if (i,r) in xidx]
  if row:eq.append(row);rhs.append(1)
 for i in range(n):
  for j in range(i+1,n):
   for a in allowed[i]:eq.append([(yidx[i,j,a,b],1) for b in allowed[j] if b!=a]+[(xidx[i,a],-1)]);rhs.append(0)
   for b in allowed[j]:eq.append([(yidx[i,j,a,b],1) for a in allowed[i] if a!=b]+[(xidx[j,b],-1)]);rhs.append(0)
 Aeq=lil_matrix((len(eq),t))
 for r,row in enumerate(eq):
  for c,v in row:Aeq[r,c]=v
 Aub=lil_matrix((len(qrows),t));bub=np.ones(len(qrows))
 for r,ids in enumerate(qrows.values()):
  for c in ids:Aub[r,c]=1
 st=time.time();res=linprog(np.zeros(t),A_ub=csr_matrix(Aub),b_ub=bub,A_eq=csr_matrix(Aeq),b_eq=np.array(rhs),bounds=(0,1),method='highs')
 return not res.success,t,len(eq),len(qrows),time.time()-st

rng=random.Random(20261021);out=[]
for n in [18,20]:
 for k in range(int(.4*n),int(.7*n)+1):
  for z in range(24):
   p=randprefix(n,k,rng);st=time.time();cut,ini,D,rou,rem,chk=ac(n,p);act=time.time()-st
   rec={'n':n,'depth':k,'frac':k/n,'prefix':p,'ac_cut':cut,'min_domain_initial':min(ini.values()),'min_domain_final':min((len(x) for x in D.values()),default=0),'ac_rounds':rou,'ac_removed':rem,'ac_checks':chk,'ac_seconds':act}
   # LP on 8 samples/cell that survived AC; compare support-fixed LP
   if z<8 and not cut:
    inf,nv,ne,nu,sec=lp2(n,p,D);rec.update(lp_tested=True,lp_infeasible=inf,lp_vars=nv,lp_eq=ne,lp_caps=nu,lp_seconds=sec)
   else:rec['lp_tested']=False
   out.append(rec)
  a=[x for x in out if x['n']==n and x['depth']==k]
  print(n,k,'AC',sum(x['ac_cut'] for x in a),'minmed',statistics.median(x['min_domain_initial'] for x in a),'remmed',statistics.median(x['ac_removed'] for x in a),'LP',sum(x.get('lp_infeasible',False) for x in a), '/',sum(x['lp_tested'] for x in a),flush=True)
json.dump(out,open('/mnt/data/ac_lp_transition_18_20.json','w'),indent=2)
