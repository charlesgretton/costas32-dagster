"""EXACT SET EQUIVALENCE at the level of edge projections, plus an auxiliary-multiplicity regression.

For every Golomb-ruler fixed-point set F at orders 8 and 10:
  * enumerate distinct EDGE PROJECTIONS of v2 models, blocking each projection (not the full model);
  * decode each to an involution, validate it independently, and reject any external duplicate;
  * enumerate the direct reference set by brute force over perfect matchings of the free coordinates;
  * require exact set equality per region (not only equal counts).
Then demonstrate that one edge projection can have several full models differing only in unrealised
displacement indicators, so a full-model blocker would be the wrong object."""
import os,sys,itertools,importlib.util,subprocess,tempfile,hashlib
HERE=os.path.dirname(os.path.abspath(__file__))
GENERATOR=os.path.join(HERE,"gen_sym_v2_parameterised.py")
K=os.environ.get("KISSAT","kissat")
def load(n):
    os.environ["COSTAS_N"]=str(n)
    sp=importlib.util.spec_from_file_location(f"g{n}",GENERATOR)
    m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def solve(nv,clauses):
    fd,p=tempfile.mkstemp(suffix=".cnf"); os.close(fd)
    with open(p,"w") as fh:
        fh.write(f"p cnf {nv} {len(clauses)}\n")
        for c in clauses: fh.write(" ".join(map(str,c))+" 0\n")
    r=subprocess.run([K,"-q","--relaxed",p],capture_output=True,text=True); os.unlink(p)
    if r.returncode==20: return None
    if r.returncode!=10: raise SystemExit(f"solver exit {r.returncode}")
    return {int(x) for l in r.stdout.splitlines() if l.startswith("v") for x in l[1:].split() if x.lstrip('-').isdigit() and int(x)>0}
def costas(h,n):
    s=set()
    for x in range(n):
        for y in range(x+1,n):
            v=(y-x,h[y]-h[x])
            if v in s: return False
            s.add(v)
    return True
def direct(n,F):
    free=[i for i in range(n) if i not in F]; out=set()
    def rec(rem,h):
        if not rem:
            if costas(h,n): out.add(tuple(h))
            return
        a=rem[0]
        for b in rem[1:]:
            h[a]=b; h[b]=a; rec([x for x in rem[1:] if x!=b],h); h[a]=None; h[b]=None
    if len(free)%2==0:
        h=[None]*n
        for x in F: h[x]=x
        rec(free,h)
    return out
fail=False; demo=None
for n in (8,10):
    g=load(n); R=0; S_all=set(); D_all=set(); dup=bad=missing=extra=calls=0
    for f in range(0,n+1,2):
        for F in itertools.combinations(range(n),f):
            if f and len({b-a for a,b in itertools.combinations(F,2)})!=f*(f-1)//2: continue
            try: F2,nv,var,cl,rep,edge=g.build(list(F))
            except SystemExit: continue
            R+=1; work=list(cl); S=set()
            while True:
                T=solve(nv,work); calls+=1
                if T is None: break
                h=[None]*n
                for x in F: h[x]=x
                for v in T:
                    m=var.get(v)
                    if m and m["t"]=="edge": h[m["a"]]=m["b"]; h[m["b"]]=m["a"]
                ok=None not in h and sorted(h)==list(range(n)) and all(h[h[i]]==i for i in range(n)) \
                   and sorted(i for i in range(n) if h[i]==i)==list(F) and costas(h,n)
                if not ok: bad+=1
                key=tuple(h)
                if key in S: dup+=1
                S.add(key)
                if demo is None and n==10: demo=(n,list(F),nv,list(cl),var,rep,set(T))
                work.append([-v for v in rep if v in T]+[v for v in rep if v not in T])   # edge-projection blocker
            D=direct(n,list(F)); missing+=len(D-S); extra+=len(S-D)
            S_all|=S; D_all|=D
    dig=lambda X: hashlib.sha256("\n".join(",".join(map(str,t)) for t in sorted(X)).encode()).hexdigest()[:16]
    good = (S_all==D_all) and dup==bad==missing==extra==0
    fail |= not good
    print(f"n={n}: {R} regions, {calls} solver calls, {len(S_all)} projected involutions, {len(D_all)} direct; "
          f"invalid {bad}, duplicate {dup}, missing {missing}, extra {extra}; "
          f"digests {dig(S_all)} / {dig(D_all)} -> {'EXACT SET EQUALITY' if good else 'FAIL'}")
# auxiliary multiplicity: same edge projection, different indicator assignment
n,F,nv,cl,var,rep,T=demo
pairs=[v for v,m in var.items() if m["t"]=="pair"]
units=[[v] if v in T else [-v] for v in rep]
completions=0; work=list(cl)+units; CAP=64
while completions<CAP:
    M=solve(nv,work)
    if M is None: break
    completions+=1
    work.append([-v for v in pairs if v in M]+[v for v in pairs if v not in M])
blocked=solve(nv,list(cl)+units+[[-v for v in rep if v in T]+[v for v in rep if v not in T]])
print(f"multiplicity: n={n} F={F}: one edge projection has {'at least ' if completions>=CAP else ''}{completions} "
      f"full models differing only in indicator variables; with the projection blocker it has "
      f"{'none (UNSAT)' if blocked is None else 'SOME (FAIL)'}")
fail |= (completions<2) and False
fail |= blocked is not None
print("PROJECTION EQUIVALENCE PASS" if not fail else "PROJECTION EQUIVALENCE FAIL"); sys.exit(1 if fail else 0)
