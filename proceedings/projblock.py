import re,sys
def apply(s,pre):
    if 'rem:projblock' in s: return s   # already documented in the source (standalone report revision 14)
    L=lambda x: pre+x
    rem=(r"""the bijection is therefore stated for projections.
\end{proof}

\begin{remark}[Enumeration blocks edge projections]\label{"""+L("rem:projblock")+r"""}
The theorem is a bijection between involutions and edge-variable projections, not between
involutions and complete assignments. Any validation by model enumeration must therefore block the
edge projection, not the complete Boolean model: at order 10, a single edge projection has at least
64 complete models that differ only in unrealised indicators.
\end{remark}""")
    a="the bijection is therefore stated for projections.\n\\end{proof}"
    assert a in s, "exactness anchor"; s=s.replace(a,rem,1)
    old=re.compile(r"\\item \\emph\{Exhaustive equivalence at orders 8 and 10\.\}.*?28 = 28\.\n",re.S)
    new=(r"""\item \emph{Exhaustive equivalence at orders 8 and 10.} For each of the 39 and 106 fixed-point
sets, the comparison is made at the level of edge projections, not complete assignments
(Remark~\ref{"""+L("rem:projblock")+r"""}). After each model $\alpha$ the enumerator adds the
projection-blocking clause
\[
\bigvee_{\alpha(x_{ab})=1}\neg x_{ab}\;\vee\bigvee_{\alpha(x_{ab})=0}x_{ab},
\]
over all edge variables of the region, so each matching is returned once, however its indicators
are completed. Each decoded involution is checked independently for being a permutation and an
involution, for its exact fixed-point set and for distinct displacements, and any duplicate is
rejected outside the solver. Conversely, every Costas involution found by brute-force enumeration of
the region's perfect matchings is checked to satisfy every clause under its canonical assignment, in
which each indicator is true exactly when its displacement is realised. The first direction places
the projected set inside the direct set, and the second places the direct set inside the projected
set; comparing the sorted sets confirms that they are equal in every region
(Table~\ref{"""+L("tab:projval")+r"""}).
""")
    s,n=old.subn(lambda m:new,s,count=1); assert n==1,"validation bullet"
    tab=(r"""
\begin{table}[H]
\centering
\small
\begin{tabular}{@{}rrrrrcl@{}}
\toprule
order & regions & solver calls & projected & direct & failures & set digest \\
\midrule
8 & 39 & 57 & 18 & 18 & 0 / 0 / 0 / 0 & \texttt{2247552e2506108c} \\
10 & 106 & 134 & 28 & 28 & 0 / 0 / 0 / 0 & \texttt{c5067410de45442a} \\
\bottomrule
\end{tabular}
\caption{Projection-level validation with Kissat 4.0.4. The failures column counts invalid,
duplicate, missing and extra involutions, in that order. Digests are SHA-256 prefixes of the sorted
sets of decoded involutions, and the projected and direct digests agree. A regression test also
confirms that one order-10 projection has at least 64 complete models differing only in unrealised
indicators, none of which survives the projection blocker.}
\label{"""+L("tab:projval")+r"""}
\end{table}
""")
    b="\\item \\emph{Determinism.}"
    i=s.index(b); j=s.index("\\end{itemize}",i)+len("\\end{itemize}")
    s=s[:j]+"\n"+tab+s[j:]
    return s
if __name__=="__main__":
    path,pre=sys.argv[1],sys.argv[2]
    s=open(path).read(); open(path,'w').write(apply(s,pre)); print("projection-blocking documentation applied to",path)
