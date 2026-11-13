#!/usr/bin/env python3
"""Type X (I_F=0, q=0, C=1): exactly ONE cross large-large orbit.

The witness orbit w_o is a genuine mathematical partition, not an imposed cut:
conditioning on which orbit is the witness forces its edges and forbids every
other cross orbit. That is the one structure in this layer that might make a
node locally closable.
"""
import sys, os, json
from itertools import combinations
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import z2_common as Z

def build(F):
    F=sorted(F); free=[i for i in range(Z.N) if i not in F]; seed=[(x,x) for x in F]
    assert len(Z.fixed_far_pairs(F))==0, "Type X needs I_F=0"
    nv=0; var={}; cl=[]; fam=[]
    def V(m):
        nonlocal nv; nv+=1; var[nv]=m; return nv
    def C(l,f): cl.append(list(l)); fam.append(f)
    edge={}
    for a,b in combinations(free,2):
        if Z.is_far(a,b): continue                     # q=0: no long transpositions
        pts=seed+Z.edge_graph_points(a,b); ds=Z.displacements_of(pts)
        if len(set(ds))!=len(ds): continue
        edge[(a,b)]=V({"type":"edge","a":a,"b":b,"length":b-a})
    rep=sorted(edge.values())
    marks={}
    def mark(n,fn):
        s=len(cl); fn(); marks[n]=(s,len(cl)-1) if len(cl)>s else None
    def endpoints():
        for c in free:
            inc=[edge[e] for e in edge if c in e]
            C(inc,"alo")
            for u,v in combinations(inc,2): C([-u,-v],"amo")
    mark("endpoint",endpoints)
    def lengths():
        for d in range(1,16):
            es=[edge[e] for e in edge if e[1]-e[0]==d]
            for u,v in combinations(es,2): C([-u,-v],"len_amo")
    mark("length",lengths)
    # candidate cross orbits, and the pairwise Costas conflicts
    orb={}
    def costas_and_orbits():
        ek=sorted(edge)
        for i in range(len(ek)):
            for j in range(i+1,len(ek)):
                (a,b),(c,d)=ek[i],ek[j]
                if len({a,b,c,d})<4: continue
                pts=seed+Z.edge_graph_points(a,b)+Z.edge_graph_points(c,d)
                ds=Z.displacements_of(pts)
                if len(set(ds))!=len(ds):
                    C([-edge[(a,b)],-edge[(c,d)]],"costas_pair"); continue
                hh={x:x for x in F}; hh[a]=b; hh[b]=a; hh[c]=d; hh[d]=c
                cross=any(x<y and Z.is_far(x,y) and Z.is_far(hh[x],hh[y])
                          and not ((x in F and y in F) or (hh[x]==y and hh[y]==x))
                          for x in hh for y in hh)
                if cross: orb[(ek[i],ek[j])]=None
    mark("costas",costas_and_orbits)
    def witnesses():
        for k in list(orb):
            e1,e2=k; w=V({"type":"orbit_witness","e1":e1,"e2":e2}); orb[k]=w
            u,v=edge[e1],edge[e2]
            C([-w,u],"w_eq"); C([-w,v],"w_eq"); C([w,-u,-v],"w_eq")   # equivalence
        ws=list(orb.values())
        C(ws,"w_exactly_one")                          # at least one
        # LADDER at-most-one: linear, not pairwise. Pairwise over ~24k witnesses
        # is 2.8e8 clauses and OOMs -- recorded as a real constraint on the design.
        prev=None
        for w in ws:
            s_i=V({"type":"ladder_aux"})
            if prev is None: C([-w,s_i],"w_ladder")
            else:
                C([-w,s_i],"w_ladder"); C([-prev,s_i],"w_ladder"); C([-w,-prev],"w_ladder")
            prev=s_i
    mark("witness",witnesses)
    return dict(F=F,nv=nv,var=var,cl=cl,fam=fam,edge=edge,rep=rep,
                orb=orb,marks=marks)

def write(M,out):
    os.makedirs(out,exist_ok=True); n=len(M["cl"]); rep=M["rep"]
    with open(f"{out}/model.cnf","w") as f:
        f.write(f"c TypeX F={M['F']}\np cnf {M['nv']} {n}\n")
        for c in M["cl"]: f.write(" ".join(map(str,c))+" 0\n")
    R=f"{rep[0]}-{rep[-1]}"; W=sorted(M["orb"].values())
    open(f"{out}/dag_A_monolithic.dag","w").write(
        f"DAG-FILE\nNODES:1\nGRAPH:\nCLAUSES:\n0:0-{n-1}\nREPORTING:\n{R}\n")
    # W: witness source fans out to k siblings, each holding the full stack;
    #    the witness choice is the partition, and it is mathematical.
    wm=M["marks"]["witness"]; k=4
    grp=[W[i::k] for i in range(k)]
    lines=[f"0->{i+1}:"+",".join(map(str,g)) for i,g in enumerate(grp) if g]
    lines+= [f"{i+1}->{k+1}:{R}" for i,g in enumerate(grp) if g]
    cls=[f"0:{wm[0]}-{wm[1]}"]+[f"{i+1}:0-{n-1}" for i,g in enumerate(grp) if g]+[f"{k+1}:0-{n-1}"]
    open(f"{out}/dag_W_witness.dag","w").write(
        "DAG-FILE\nNODES:%d\nGRAPH:\n%s\nCLAUSES:\n%s\nREPORTING:\n%s\n"
        % (k+2,"\n".join(lines),"\n".join(cls),R))
    json.dump({"F":M["F"],"vars":M["nv"],"clauses":n,"edges":len(rep),
               "candidate_cross_orbits":len(M["orb"]),
               "families":{a:b for a,b in M["marks"].items()}},
              open(f"{out}/meta.json","w"),indent=1)
    return n,len(rep),len(M["orb"])

if __name__=="__main__":
    F=[int(x) for x in sys.argv[1].split(",")]; out=sys.argv[2]
    M=build(F); n,e,o=write(M,out)
    print(f"TypeX F={F}: vars={M['nv']} clauses={n:,} edges={e} candidate cross orbits={o:,}")
