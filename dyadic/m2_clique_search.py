#!/usr/bin/env python3
"""m2_clique_search.py -- settles the zero-survivor question structurally.

The 240 diagonal triples ARE the 240 same-parity index pairs, so for fixed u the
zero-survivor condition forces v_i xor v_k = 1 xor u_i xor u_j on four COMPLETE
graphs. Consistency is a parity union-find. Result: no balanced u admits a
consistent v, in 744 nodes.  Hence m_2 >= 1.
"""
N=32
class PUF:
    def __init__(s,n): s.p=list(range(n)); s.r=[0]*n
    def find(s,x):
        par=0
        while s.p[x]!=x: par^=s.r[x]; x=s.p[x]
        return x,par
    def union(s,x,y,d):
        rx,px=s.find(x); ry,py=s.find(y)
        if rx==ry: return (px^py)==d
        s.p[rx]=ry; s.r[rx]=px^py^d; return True
    def snap(s): return (s.p[:],s.r[:])
    def rest(s,t): s.p[:],s.r[:]=t[0][:],t[1][:]
u=[0]*N; sols=[]; nodes=[0]
def dfs(i,ones,puf):
    nodes[0]+=1
    if ones>16 or (16-ones)>(N-i): return
    if i==N:
        if ones==16: sols.append(u[:])
        return
    for bit in ((0,) if i==0 else (0,1)):      # u_0 = 0 WLOG (translation by 1)
        u[i]=bit; t=puf.snap(); ok=True
        for k in range(i-2,-1,-2):
            if u[k]==bit and not puf.union(i,k,1^bit^u[(i+k)//2]):
                ok=False; break
        if ok: dfs(i+1,ones+bit,puf)
        puf.rest(t)
    u[i]=0
if __name__=="__main__":
    dfs(0,0,PUF(N))
    print(f"nodes {nodes[0]}, consistent balanced u-words {len(sols)}")
    print("m_2 >= 1" if not sols else "m_2 = 0, witness found")
