"""Certificate check: unlabelled dyadic residue caps do not characterise the Costas property at order 32.

Definitions (zero-based, pairs i<j so the horizontal lag d=j-i is positive):
  displacement of a pair:  (d, e) = (j-i, h[j]-h[i]),   1<=d<=31, 1<=|e|<=31
  occupancy at level r:    c_r(a,b) = #{pairs with (d,e) == (a,b) mod 2^r}
  capacity at level r:     C_r(a,b) = #{admissible integer (d,e) with (d,e) == (a,b) mod 2^r}
  defect:                  sum over integer displacements of max(0, multiplicity - 1)
A Costas array has every integer displacement at most once, hence c_r <= C_r at every level.
The witness h* below was found by local search; this script checks it from the definitions alone.
It also reproduces the radix-2 shuffle experiment on the near-solution N32 (defect 2)."""
import json, hashlib, sys
from collections import Counter
n=32
H_STAR=[5,19,25,28,29,8,0,26,14,3,31,1,23,30,2,20,16,13,18,9,15,10,22,27,12,21,7,4,6,17,11,24]
N32=[31,30,2,8,1,14,12,7,4,20,0,18,9,13,21,10,11,26,25,6,28,24,3,15,5,19,22,27,29,16,23,17]
def disp(h): return [(j-i,h[j]-h[i]) for i in range(n) for j in range(i+1,n)]
def defect(h): return sum(v-1 for v in Counter(disp(h)).values() if v>1)
def lags_with_repeats(h):
    c=Counter(disp(h)); return sorted({d for (d,e),v in c.items() if v>1})
def capacity(r):
    M=2**r; C=Counter()
    for d in range(1,n):
        for e in [x for x in range(-(n-1),n) if x!=0]: C[(d%M,e%M)]+=1
    return C
def occupancy(h,r):
    M=2**r; return Counter((d%M,e%M) for d,e in disp(h))
ok=True; out={"witness":H_STAR,"n":n}
assert sorted(H_STAR)==list(range(n)), "witness is not a permutation"; out["is_permutation"]=True
out["defect"]=defect(H_STAR); out["lags_with_repeated_displacements"]=lags_with_repeats(H_STAR)
out["levels"]={}
for r in range(1,6):
    C=capacity(r); c=occupancy(H_STAR,r)
    viol=[k for k,v in c.items() if v>C[k]]
    out["levels"][r]={"classes_occupied":len(c),"violations":len(viol),"max_occupancy_over_capacity":round(max(v/C[k] for k,v in c.items()),4)}
    ok &= not viol
out["satisfies_every_cap_r1_to_r5"]=ok
# radix-2 shuffle analogues of M10, applied to the eight dihedral images of N32
def d4(h):
    imgs=[]; inv=lambda g:[g.index(i) for i in range(n)]
    for g in (list(h),inv(list(h))):
        for a in (g,[n-1-v for v in g]):
            for b in (a,a[::-1]): imgs.append(tuple(b))
    return list(dict.fromkeys(imgs))
rot=lambda x,bits,r: ((x<<r)|(x>>(bits-r)))&((1<<bits)-1)
rev=lambda x,bits: int(format(x,f'0{bits}b')[::-1],2)
imgs=d4(N32); assert len(imgs)==8 and all(defect(g)==2 for g in imgs)
def act_rc(h,s,cols_only):
    g=[None]*n
    for i in range(n): g[s(i)]=h[i] if cols_only else s(h[i])
    return g
def act_img(h,s):
    P=[(a//n,a%n) for a in (s(i*n+h[i]) for i in range(n))]
    if len({x for x,_ in P})<n or len({y for _,y in P})<n: return None
    g=[None]*n
    for x,y in P: g[x]=y
    return g
rows=[]
for name,maps5,maps10 in [("rotation",[lambda x,r=r: rot(x,5,r) for r in range(1,5)],[lambda x,r=r: rot(x,10,r) for r in range(1,10)]),
                          ("bit reversal",[lambda x: rev(x,5)],[lambda x: rev(x,10)])]:
    for label,res in [("rows and columns",[act_rc(h,s,False) for h in imgs for s in maps5]),
                      ("columns only",[act_rc(h,s,True) for h in imgs for s in maps5]),
                      ("whole 10-bit address",[act_img(h,s) for h in imgs for s in maps10])]:
        perms=[g for g in res if g is not None]; ds=[defect(g) for g in perms]
        rows.append({"action":f"{label}, {name}","images":len(res),"permutations":len(perms),
                     "defect_min":min(ds),"defect_max":max(ds),"costas":sum(d==0 for d in ds),
                     "dihedral_images_of_N32":sum(tuple(g) in set(imgs) for g in perms)})
out["N32_shuffles"]=rows
out["witness_sha256"]=hashlib.sha256(",".join(map(str,H_STAR)).encode()).hexdigest()
blob=json.dumps(out,indent=1,sort_keys=True)
open("dyadic_caps_result.json","w").write(blob)
print(blob); print("result_sha256:",hashlib.sha256(blob.encode()).hexdigest())
print("CERTIFICATE PASS" if ok and out["defect"]==55 and all(r["costas"]==0 for r in rows) else "CERTIFICATE FAIL")
sys.exit(0 if ok else 1)
