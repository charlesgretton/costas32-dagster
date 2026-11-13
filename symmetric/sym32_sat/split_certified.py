#!/usr/bin/env python3
"""Certified case split of a region CNF.

The previous dag_splitK was NOT a space partition: siblings received different
subsets of interface variables rather than mutually exclusive, collectively
exhaustive restrictions. Its timings are withdrawn.

Correct construction. Let i be a deterministically chosen free coordinate with
available partners j_1..j_k, and S_r := x_{i,j_r}. The region CNF already
contains, for coordinate i, an at-least-one clause over its incident edges and
the pairwise at-most-one clauses. Hence

    C_F  ==  OR_r (C_F AND S_r)          with the cases pairwise disjoint.

Each CHILD is the FULL region CNF plus its own unit clause. Nothing else differs.

Emitted checks, to be discharged by a solver rather than argued:
  coverage.cnf      C_F AND ~S_1 AND ... AND ~S_k     must be UNSAT
  disjoint_r_s.cnf  C_F AND S_r AND S_s               must be UNSAT
"""
import sys, os, json, re

def read_cnf(p):
    head=None; cl=[]
    for l in open(p):
        if l.startswith('c'): continue
        if l.startswith('p'): head=l.split(); continue
        t=[int(x) for x in l.split()]
        if t and t[-1]==0: cl.append(t[:-1])
    return int(head[2]), int(head[3]), cl

def write_cnf(p, nv, cl, comment=""):
    with open(p,'w') as f:
        if comment: f.write(f"c {comment}\n")
        f.write(f"p cnf {nv} {len(cl)}\n")
        for c in cl: f.write(" ".join(map(str,c))+" 0\n")

def main(region_dir, out, rule="lowest"):
    nv, nc, cl = read_cnf(f"{region_dir}/model.cnf")
    var = json.load(open(f"{region_dir}/meta.json"))
    F = var["region_F"]; from gen_sym32_v2 import N as _N
    free=[i for i in range(_N) if i not in F]
    # recover the edge variable map from the CNF comment-free structure:
    # regenerate it the same way gen_sym32 does, so the ids line up
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gen_sym32_v2 import build as v2build          # v2, explicitly
    _F,_nv,vmap,_cl,_rep,_edge = v2build(F)
    # Equal counts do NOT prove artefact identity -- the v1 episode is exactly
    # why. Compare the canonical CNF body byte-for-byte.
    import hashlib
    def canon(nvv, cls):
        return hashlib.sha256(
            (f"p cnf {nvv} {len(cls)}\n" +
             "".join(" ".join(map(str,c))+" 0\n" for c in cls)).encode()).hexdigest()
    stored = hashlib.sha256(
        ("".join(l for l in open(f"{region_dir}/model.cnf") if not l.startswith('c'))).encode()
    ).hexdigest()
    regen = canon(_nv, _cl)
    if stored != regen:
        raise SystemExit(f"CNF MISMATCH\n  stored  {stored[:16]}\n  regen   {regen[:16]}\n"
                         f"  the split must be generated against the SAME artefact it certifies")
    nv, nc = _nv, len(_cl); cl = _cl
    if rule=="lowest":
        i = min(free)
    else:                                   # smallest remaining partner domain
        dom={c: sum(1 for k in vmap if vmap[k]["t"]=="edge" and c in (vmap[k]["a"],vmap[k]["b"]))
             for c in free}
        i = min(dom, key=lambda c:(dom[c], c))
    S = sorted(k for k in vmap if vmap[k]["t"]=="edge" and i in (vmap[k]["a"],vmap[k]["b"]))
    os.makedirs(out, exist_ok=True)
    for r,s in enumerate(S):
        write_cnf(f"{out}/child{r:03d}.cnf", nv, cl+[[s]],
                  f"region F={F} case {r}: x{vmap[s]['a']},{vmap[s]['b']} TRUE")
    write_cnf(f"{out}/coverage.cnf", nv, cl+[[-s] for s in S],
              f"coverage check: MUST be UNSAT (no parent model omitted)")
    pairs=[]
    for a in range(len(S)):
        for b in range(a+1,len(S)):
            pairs.append((a,b))
            write_cnf(f"{out}/disjoint_{a:03d}_{b:03d}.cnf", nv, cl+[[S[a]],[S[b]]],
                      "disjointness check: MUST be UNSAT")
    import hashlib
    dg=lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
    json.dump({"encoding":"v2",
               "generator_sha256":dg(os.path.join(os.path.dirname(os.path.abspath(__file__)),"gen_sym32_v2.py")),
               "split_generator_sha256":dg(os.path.abspath(__file__)),
               "parent_cnf_sha256":dg(f"{region_dir}/model.cnf"),
               "coverage_cnf_sha256":dg(f"{out}/coverage.cnf"),
               "region_F":F,"split_rule":rule,"split_coordinate":i,
               "split_count":len(S),"split_literals":S,
               "split_edges":[[vmap[s]["a"],vmap[s]["b"]] for s in S],
               "parent_vars":nv,"parent_clauses":nc,
               "checks":{"coverage":"coverage.cnf","disjoint_pairs":len(pairs)}},
              open(f"{out}/split.json","w"), indent=1)
    print(f"region F={F}: split on coordinate {i} -> {len(S)} certified children")
    print(f"  children child000..child{len(S)-1:03d}.cnf   (full CNF + one unit clause each)")
    print(f"  coverage.cnf and {len(pairs)} disjointness CNFs, all MUST be UNSAT")
    return len(S)

if __name__=="__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)>3 else "lowest")
