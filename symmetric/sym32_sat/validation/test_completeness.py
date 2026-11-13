import os
HERE=os.path.dirname(os.path.abspath(__file__))
GENERATOR=os.path.join(HERE,"gen_sym_v2_parameterised.py")
CATALOGUE=os.path.join(HERE,"historical_involutive_costas_12_22.txt")
import sys, os, itertools, importlib.util, subprocess
K=os.environ.get("KISSAT","kissat")
def load(n):
    os.environ["COSTAS_N"]=str(n)
    sp=importlib.util.spec_from_file_location(f"g{n}",GENERATOR)
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def involutions(n,F):
    free=[i for i in range(n) if i not in F]
    def rec(rem,h):
        if not rem: yield list(h); return
        a=rem[0]
        for b in rem[1:]:
            h[a]=b; h[b]=a
            yield from rec([x for x in rem[1:] if x!=b],h)
            h[a]=None; h[b]=None
    if len(free)%2: return
    h=[None]*n
    for x in F: h[x]=x
    yield from rec(free,h)
def costas(h,n):
    s=set()
    for x in range(n):
        for y in range(x+1,n):
            v=(y-x,h[y]-h[x])
            if v in s: return False
            s.add(v)
    return True
def assign(g,var,F,h,n):
    """build the full truth assignment implied by h, then check every clause."""
    T=set()
    for v,m in var.items():
        if m["t"]=="edge":
            if h[m["a"]]==m["b"]: T.add(v)
        elif m["t"]=="h":
            if h[m["i"]]==m["j"]: T.add(v)
        elif m["t"]=="pair":
            s,x,d=m["s"],m["x"],m["delta"]
            if x+s<n and h[x+s]-h[x]==d: T.add(v)
    return T
def clauses_ok(cl,T):
    for c in cl:
        if not any((l>0 and l in T) or (l<0 and -l not in T) for l in c): return c
    return None
for n in (8,10):
    g=load(n); tot=0; bad=0; cs=0
    for f in range(0,n+1,2):
        for F in itertools.combinations(range(n),f):
            if f and len({b-a for a,b in itertools.combinations(F,2)})!=f*(f-1)//2: continue
            try: F2,nv,var,cl,rep,edge=g.build(list(F))
            except SystemExit: continue
            for h in involutions(n,list(F)):
                if not costas(h,n): continue
                cs+=1; tot+=1
                T=assign(g,var,list(F),h,n)
                c=clauses_ok(cl,T)
                if c: bad+=1;  print(f"  n={n} F={F} h={h} VIOLATES clause {c[:6]}")
    print(f"n={n}: {cs} direct Costas involutions, {bad} fail the v2 CNF  -> "
          f"{'COMPLETENESS PASS' if bad==0 else 'FAIL'}")
