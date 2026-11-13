import os
HERE=os.path.dirname(os.path.abspath(__file__))
GENERATOR=os.path.join(HERE,"gen_sym_v2_parameterised.py")
CATALOGUE=os.path.join(HERE,"historical_involutive_costas_12_22.txt")
"""158-array regression: direct clause evaluation, not solver rediscovery.
Reports failures by clause family so a generator defect is localised."""
import os,importlib.util,collections
def load(n):
    os.environ["COSTAS_N"]=str(n)
    sp=importlib.util.spec_from_file_location(f"g{n}",GENERATOR)
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def costas(h,n):
    s=set()
    for x in range(n):
        for y in range(x+1,n):
            v=(y-x,h[y]-h[x])
            if v in s: return False
            s.add(v)
    return True
tot=acc=rej=0; fails=collections.Counter(); cache={}
for n in (12,14,16,18,20,22):
    arrs=[list(map(int,l.split()[1:])) for l in open(CATALOGUE)
          if l.strip() and not l.startswith('#') and int(l.split()[0])==n]
    if not arrs: continue
    g=load(n)
    for h in arrs:
        tot+=1
        F=[i for i in range(n) if h[i]==i]
        assert sorted(h)==list(range(n)) and all(h[h[i]]==i for i in range(n))
        assert costas(h,n)
        key=(n,tuple(F))
        if key not in cache: cache[key]=g.build(list(F))
        F2,nv,var,cl,rep,edge=cache[key]
        T=set()
        for v,m in var.items():
            if m["t"]=="edge" and h[m["a"]]==m["b"]: T.add(v)
            elif m["t"]=="h" and h[m["i"]]==m["j"]: T.add(v)
            elif m["t"]=="pair":
                s_,x,d=m["s"],m["x"],m["delta"]
                if x+s_<n and h[x+s_]-h[x]==d: T.add(v)
        bad=None
        for c in cl:
            if not any((l>0 and l in T) or (l<0 and -l not in T) for l in c): bad=c; break
        if bad is None: acc+=1
        else:
            rej+=1
            kinds={var[abs(l)]["t"] for l in bad}
            fails["/".join(sorted(kinds))]+=1
            if rej<=3: print(f"  n={n} F={F} FAILS clause {bad[:8]} families={kinds}")
print(f"\n158-array regression: tested {tot}, accepted {acc}, rejected {rej}")
if fails: print("  failures by clause family:",dict(fails))
print("  RESULT:", "PASS" if rej==0 and tot==158 else f"FAIL ({tot} tested)")
