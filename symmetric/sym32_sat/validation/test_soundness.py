import os
HERE=os.path.dirname(os.path.abspath(__file__))
GENERATOR=os.path.join(HERE,"gen_sym_v2_parameterised.py")
CATALOGUE=os.path.join(HERE,"historical_involutive_costas_12_22.txt")
"""SOUNDNESS: enumerate EVERY v2 model and require each to decode to a genuine
Costas involution with fixed set exactly F.  Completeness (previous test) says
no valid array is excluded; this says nothing invalid is admitted."""
import os,sys,itertools,importlib.util,subprocess,tempfile
K=os.environ.get("KISSAT","kissat")
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
for n in (8,10):
    g=load(n); models=0; bad=0; regions=0
    for f in range(0,n+1,2):
        for F in itertools.combinations(range(n),f):
            if f and len({b-a for a,b in itertools.combinations(F,2)})!=f*(f-1)//2: continue
            try: F2,nv,var,cl,rep,edge=g.build(list(F))
            except SystemExit: continue
            regions+=1; work=list(cl)
            while True:
                fd,p=tempfile.mkstemp(suffix=".cnf"); os.close(fd)
                with open(p,"w") as fh:
                    fh.write(f"p cnf {nv} {len(work)}\n")
                    for c in work: fh.write(" ".join(map(str,c))+" 0\n")
                r=subprocess.run([K,"-q","--relaxed",p],capture_output=True,text=True)
                os.unlink(p)
                if r.returncode==20: break
                if r.returncode!=10: print(f"  solver exit {r.returncode}"); break
                T={int(x) for l in r.stdout.splitlines() if l.startswith("v")
                   for x in l[1:].split() if x.lstrip('-').isdigit() and int(x)>0}
                h=[None]*n
                for x in F: h[x]=x
                for v in T:
                    m=var.get(v)
                    if m and m["t"]=="edge": h[m["a"]]=m["b"]; h[m["b"]]=m["a"]
                models+=1
                okperm = None not in h and sorted(h)==list(range(n))
                okinv  = okperm and all(h[h[i]]==i for i in range(n))
                okfix  = okperm and sorted(i for i in range(n) if h[i]==i)==list(F)
                okc    = okperm and costas(h,n)
                if not (okperm and okinv and okfix and okc):
                    bad+=1; print(f"  n={n} F={F} BAD MODEL perm={okperm} inv={okinv} fix={okfix} costas={okc}")
                work.append([-v for v in sorted(rep) if v in T]+[v for v in sorted(rep) if v not in T])
    print(f"n={n}: {regions} regions, {models} models enumerated, {bad} invalid -> "
          f"{'SOUNDNESS PASS' if bad==0 else 'FAIL'}")
