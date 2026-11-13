import re
p='/tmp/proc/costas32_proceedings.tex'; s=open(p).read()
heads={'p1':'\\chapter{The Landscape at Order 32','p2':'\\chapter{Two-Point Augmentations','p3':'\\chapter{Deletion-Minor Exclusions',
       'p4':'\\chapter{Reconstructing and Verifying','p5':'\\chapter{Telescoping-Sum Propagation','p6':'\\chapter{A Conditional First-Moment',
       'p7':'\\chapter{The Dyadic Defect','p8':'\\chapter{An Independent SAT Verification','p9':'\\chapter{The Cost of an Unrestricted','p10':'\\chapter{Searching for Short Obstructions'}
order=['p1','p2','p3','p4','p5','p6','p7','p8','p9','p10']
def span(pid):
    a=s.index(heads[pid]); nxt=[s.index(heads[q]) for q in order if s.index(heads[q])>a]
    b=min(nxt) if nxt else s.index('\\end{document}'); return a,b
def rx(t): return r'\s+'.join(re.escape(w) for w in t.split())
def sub(pid,old,new,regex=False):
    global s
    a,b=span(pid); seg=s[a:b]; pat=old if regex else rx(old)
    seg2,n=re.subn(pat,lambda m:new,seg,count=1,flags=re.S)
    if n==0: print(f"REVISE NO MATCH [{pid}]:",old[:70].replace('\n',' '))
    s=s[:a]+seg2+s[b:]
# ---------------- Paper 1
sub('p1',r"\begin{proposition}[Automatic loss-free parameterisation]", r"\begin{proposition}[Orders of the unmodified standard constructions]")
sub('p1',r"Consequently there is no automatically loss-free Welch or Golomb parameterisation at order 32. \end{proposition}",
 "Consequently there is no automatically loss-free Welch or Golomb parameterisation at order 32.\n\\end{proposition}\n\n\\noindent The proposition concerns only the unmodified constructions. It says nothing about deletion\nvariants, augmentation, subfield restrictions, other polynomial constructions or emergent\ntransformations, which this paper and Papers~2 and~3 treat separately.")
sub('p1',r"This makes the naming question moot for the order-32 problem.",
 "The naming ambiguity therefore does not affect the order-32 reachability conclusion, although it remains material to the completeness and historical accuracy of the construction catalogue.")
sub('p1',r"or of order $10^3$--$10^4$ modern core-years.",
 "or of order $10^3$--$10^4$ modern core-years. This projection concerns unrestricted enumeration of all\norder-32 permutations. It should not be confused with the involution-only search of Paper~8, which\nthe symmetry restriction makes many orders of magnitude cheaper, projected at 30--45 single-core hours.")

# ---------------- Paper 1: circular arrays -- citations at the attributions, and a remark
sub('p1',r"exists only when $n+1$ is prime.", "exists only when $n+1$ is prime~\\cite{p1-golombmoreno}.")
sub('p1',r"this covers every circular sequence.", "this covers every circular sequence~\\cite{p1-mpttw2015,p1-torresrubio2023}.")
sub('p1',r"Moreno proved in 1992 that", "Moreno proved in 1992~\\cite{p1-moreno92} that")
a,b=span('p1'); seg=s[a:b]
k=seg.index('\\item \\textbf{Constructed and augmented arrays.}'); e=seg.index('\\end{enumerate}',k)+len('\\end{enumerate}')
remark=r"""

\begin{remark}[Circular arrays are a strict subclass]
\label{p1-rem:circular}
A circular Costas sequence becomes an ordinary Costas array once its entries are read as integers:
two equal integer displacements would also be equal modulo $n$ horizontally and modulo $n+1$
vertically, which circularity forbids. The converse fails. The order-3 Costas array $(1,3,2)$ is
not circular, since its lag-1 circular differences $3-1$, $2-3$ and $1-2$ are $2$, $3$ and $3$
modulo 4. An exhaustive check at orders 3 to 6 finds circular sequences only at orders 4 and 6, 8
and 12 of them, which is exactly the number $\varphi(p-1)(p-1)$ of exponential Welch arrays of
those orders, as the two theorems require. Excluding circular arrays at order 32 therefore closes a
subclass of the problem, not the problem.
\end{remark}"""
seg=seg[:e]+remark+seg[e:]; s=s[:a]+seg+s[b:]
sub('p1',r"projected at 30--45 single-core hours.", "projected at 30--45 single-core hours. The projection also assumes the efficiency of the 2011 enumeration: Paper~9\nmeasures a straightforward column-by-column search at about $1.5\\times10^{20}$ nodes at order 32, over\n$10^6$ core-years, and finds the 2011 method at least 36 times more efficient.")
# ---------------- Paper 2
# (Paper 2's count sentence is now corrected in the main report itself)
a,b=span('p2'); s=s[:a]+s[a:b].replace("324{,}741{,}120$ two-point augmentations","326{,}709{,}248$ two-point augmentations")+s[b:]
# ---------------- Paper 3
sub('p3',r"\end{definition}", r"""\end{definition}

\begin{proposition}[Augmentation and deletion minors]
\label{p3-prop:augminor}
An order-$n$ permutation $P$ contains a Costas array $K$ of order $n-k$ as a $k$-row, $k$-column
deletion minor if and only if $P$ lies in the rung-$k$ augmentation space generated from $K$.
\end{proposition}
\begin{proof}
Suppose deleting columns $C$ and rows $R$, with $|C|=|R|=k$, removes exactly the $k$ dots of $P$
in $C\times R$ and leaves $K$ once the gaps are closed. The surviving dots then sit in the surviving
columns and rows at the order-preserving positions of $K$'s dots, and $P$'s dots in the deleted
columns define a bijection $\mu:C\to R$. So $(K,C,R,\mu)$ is a rung-$k$ configuration whose array
is $P$. Conversely, a configuration $(K,C,R,\mu)$ yields a permutation from which deleting $C$, $R$
and the dots of $\mu$ recovers $K$.
\end{proof}

\noindent Hence a rung-$k$ search over a complete census of order $n-k$ finds every order-$n$ Costas
array that has a Costas deletion minor of that order.""")
sub('p3',r"This is independent of Theorem~\ref{p3-thm:rung4census} rather than stronger than it (Remark~\ref{p3-rem:independent}): neither implies the other without a hereditary-minor property",
 "Neither this theorem nor Theorem~\\ref{p3-thm:rung4census} is known to imply the other\n(Remark~\\ref{p3-rem:independent}): deriving either would need a hereditary-minor property")
sub('p3',r"\begin{remark}[The two census-complete rungs are independent]", r"\begin{remark}[Neither census-complete rung is known to imply the other]")
sub('p3',r"the point is logical independence of the present proofs, which close different extension channels",
 "the point is that neither present proof implies the other, since they close different extension channels")
sub('p3',r"and only 8 are non-corner coincidences. \end{theorem}",
 "and only 8 are non-corner coincidences.\n\\end{theorem}\n\n\\noindent The table counts arrays with at least one Costas sub-array; the theorem counts\nsub-arrays. A corner deletion of a Costas array is always Costas, so the 104 arrays with a corner\ndot are exactly the 104 arrays of the table, and the 8 non-corner sub-arrays come from among them.")
# ---------------- Paper 4
sub('p4',r"It is now largely constructed, in Lean 4.15.0 with no Mathlib, no \texttt{sorry} and no \texttt{native\_decide}.",
 "Every constituent theorem has been kernel-checked in an individual compilation, in Lean 4.15.0\nwith no Mathlib, no \\texttt{sorry} and no \\texttt{native\\_decide}. The released aggregate target\nhas not yet been built in one invocation, because the available 4\\,GB environment was\ninsufficient.")
sub('p4',r"nothing in it is unproven, only unbuilt in one sitting.",
 "each of its theorems has compiled individually, but the module has not been built in one invocation.")
# ---------------- Paper 5
sub('p5',r"and $R$ the remaining value set. Put",
 "and $R$ the remaining value set. If $U$ has fewer than $k$ values, reject: the remaining\ndifferences at lag $m$ would have to be $k$ distinct values drawn from $U$. Otherwise put")
sub('p5',r"A propagator with \emph{identical} power would clear it roughly one time in ten.",
 "A propagator with \\emph{identical} power would clear it with probability $0.12$, the exact\nbinomial tail $\\Pr(X\\ge106)$ for $X\\sim\\mathrm{Bin}(296,96/296)$: roughly one time in eight.")
i=s.index('\\label{p5-lem:tmsound}'); j=s.index('\\end{proof}',i)+len('\\end{proof}')
s=s[:j]+r"""

\noindent The rule is sound but incomplete. The interval $[\ell,h]$ ignores which values can go to
which pairs, so the $k$ extremal values need not be simultaneously assignable, and the endpoint
interval ignores the joint feasibility of the row placements. In outline, the test at one lag is:
\begin{enumerate}[nosep]
\item collect the $k$ unresolved pairs at lag $m$, the union $U$ of their difference domains, the sum
  of the determined differences, and the remaining value set $R$;
\item if $|U|<k$, reject;
\item form $[\ell,h]$ from the $k$ smallest and $k$ largest values of $U$, and $[\tau_-,\tau_+]$ from
  the extremal subset sums of $R$ for the first and last $m$ positions;
\item reject if the two intervals are disjoint; otherwise pass.
\end{enumerate}"""+s[j:]
# ---------------- Paper 6
sub('p6',r"This explains, without recourse to any structural obstruction, why no amount of computation has produced an order-32 array:",
 "Conditional on the quadratic model, the projected population is so small that continued failure to\nfind an order-32 array is unsurprising. This is an interpretation of non-observation, not an\nexplanation independent of the model. On that reading,")
sub('p6',r"Read as a Poisson probability that no sporadic array ever appears again, that is $97\%$ as a point estimate but $87\%$--$99\%$ as an interval.",
 "If, additionally and heuristically, the class counts at successive orders are treated as\nindependent Poisson variables with these means, the probability that no sporadic array ever\nappears again is $97\\%$ as a point estimate but $87\\%$--$99\\%$ as an interval.")
sub('p6',r"$\sim10^{191}$", r"diverges")
sub('p6',r"\noindent This is a model",
 "\\noindent Information criteria do not settle the choice. With eight points, the small-sample\ncorrected AIC slightly favours the quadratic ($-8.1$ against $-6.2$), while BIC favours the cubic\n($-19.2$ against $-13.9$). This is a model")
# ---------------- Paper 7
sub('p7',r"\section{The clique reduction and $m_2\ge1$}", r"\section{A clique reduction and the strict lower bound $m_2\ge1$}")
sub('p7',r"The scalar minimisation can in fact be settled, and the structure does it without a solver.",
 "The zero-survivor case can be excluded exactly, and the structure does it without a solver,\nalthough the minimum itself remains unknown.")
sub('p7',r"visits 744 nodes, reaches index 17, and finds no consistent $v$.",
 "visits 744 nodes, reaches index 17, and finds no consistent $v$. The search extends $u$ one index\nat a time, keeps the induced parity constraints on $v$ in a union-find structure, and abandons a\nprefix as soon as those constraints are contradictory; every word extending an abandoned prefix\nfails for the same reason. That is how 744 visited nodes account for all $2^{17}$ words.")
sub('p7',r"\section{Exact counting and the filtration}",
 "\\section{Exact counting and the filtration}\n\nFor a permutation $p$ of order 32 and integers $r\\ge0$ and $\\ell,h\\ge1$ with $r+\\ell+h\\le31$, put\n\\[\nR_{\\ell,h,r}(p)=p_{r+\\ell+h}-p_{r+\\ell}-p_{r+h}+p_r .\n\\]\nIt vanishes exactly when the dot pairs in columns $(r,r+h)$ and $(r+\\ell,r+\\ell+h)$ have the same\ndisplacement, so $p$ is Costas if and only if no $R_{\\ell,h,r}(p)$ is zero. When $\\ell=h$ it is the\ndiagonal second difference $p_{r+2\\ell}-2p_{r+\\ell}+p_r$.\n")
sub('p7',r"Since $-62\le R_{\ell,h,r}\le62$ at order 32,", r"Since $-62\le R_{\ell,h,r}\le62$ at order 32, being a sum of two values in $[0,31]$ minus another two,")
# ---------------- Paper 8
sub('p8',r"the only non-identity motions that can fix a Costas array are the reflections in the two diagonals",
 "the only possible non-identity elements of the stabiliser of a Costas array in $D_4$ are the two diagonal reflections")
sub('p8',r"Each family of diagonal arrays contains exactly two transpose-symmetric arrays: an array and its $180^\circ$ rotation, which differ by Proposition~\ref{p8-prop:onlytranspose}. So its counts should be exactly half of counts of individual arrays,",
 "Let $A$ be transpose-symmetric, that is, fixed by the main-diagonal reflection $D$. By\nProposition~\\ref{p8-prop:onlytranspose} its stabiliser in $D_4$ is exactly $\\{\\mathrm{id},D\\}$: it\ncannot also be fixed by the other diagonal reflection, whose product with $D$ is the $180^\\circ$\nrotation. So its orbit has $8/2=4$ members. The $180^\\circ$ rotation commutes with $D$, so it maps\n$A$ to a second, different transpose-symmetric array; the reflections in the horizontal and vertical\naxes conjugate $D$ to the anti-diagonal reflection, so they give the two anti-diagonally symmetric\nmembers. Each class of diagonal arrays therefore contains exactly two transpose-symmetric arrays,\nand the 2009 counts, one per class, should be exactly half of counts of individual arrays,")
sub('p8',r"$f$ is even. An exhaustive backtracking search over 8-element subsets of $[32]$ with distinct pairwise differences finds none (run to completion), so there is no Golomb ruler with 8 or more marks in $[32]$, since any such ruler contains an 8-mark one. This agrees with the known optimal 8-mark length, 34. Hence $f\le 6$.",
 "$f$ is even. The shortest Golomb ruler with eight marks has length 34~\\cite{p8-oeisgolomb}, while\nmarks in $[32]$ span at most 31, so no eight of them have distinct pairwise differences, and any\nruler with more marks contains an 8-mark one. An exhaustive backtracking search over 8-element\nsubsets of $[32]$, run to completion, confirms this independently. Hence $f\\le 6$.")
sub('p8',r"so nothing learned carries over.",
 "so nothing learned carries over. The campaign is therefore closer to cube-and-conquer than to one\nglobally learning solver: a nogood useful in many messages is rediscovered in each.")
sub('p8',r"almost certainly one of the 27 unsplit branches",
 "most probably one of the 27 unsplit branches (the correlation strongly implicates them; mapping\neach longest message back to its partner assignment would settle it)")
sub('p8',r"It can also lower the total work for Dagster's TiniSAT workers, whose gap to Kissat is small on easy instances and large on hard ones.",
 "It can also lower the total work, plausibly because Dagster's TiniSAT workers trail Kissat by\nlittle on easy instances and by much on hard ones; this is a hypothesis, supported by a single\ncomparison.")
sub('p8',r"\begin{proposition}\label{p8-prop:simulation} On any piece, a DPLL search on the regional formula, using unit propagation and branching on the edge variables in the direct search's order, visits a subset of the direct search's nodes. \end{proposition}",
 "\\begin{proposition}\\label{p8-prop:simulation}\nFix a piece, and consider a \\emph{multiway propagation search} on its regional formula. At each node\nit selects the coordinate the direct search would select, creates one child for each candidate\npartner, asserts that partner's edge variable, and applies unit propagation, never branching on\nauxiliary variables. Every node it visits is also visited by the direct search.\n\\end{proposition}")
sub('p8',r"So each rejection is a propagation conflict at the same node.",
 "So each rejection is a propagation conflict at the same node, and by induction on depth the\npropagation search visits only nodes that the direct search visits.")
sub('p8',r"\end{proof} Counted in steps, then, the SAT solver never needs more than the direct search,",
 "\\end{proof}\n\n\\noindent The proposition concerns this multiway procedure. An ordinary DPLL or CDCL solver\nbranches on individual edge literals, and on others, so its tree is not directly comparable; what\ncarries over to it is the fact used in the proof, that every immediate displacement rejection of the\ndirect search is a unit-propagation conflict.\n\nCounted in steps, then, the propagation search never needs more nodes than the direct search,")
sub('p8',r"An exponential separation, of the kind Rintanen established between SAT-based planning and state-space search~\cite{p8-rintanen2012}, would need failures hidden many levels deep, and the reduction would then grow geometrically with the order; the data show the hidden failures are shallow. In steps, therefore, Dagster could finish at most about three or four times sooner than an equally split direct search: a modest constant factor, not an asymptotic advantage.",
 "This measures one inference, not everything that propagation and clause learning can do, so it is\nnot an upper bound on SAT's advantage, and it does not establish a ratio at order 32. On its own,\nthis inference suggests a factor of about four. An exponential separation of the kind Rintanen\nestablished between SAT-based planning and A$^*$-style state-space search~\\cite{p8-rintanen2011}\nwould need the encoding to detect future impossibilities long before the direct search reaches\nthem. The measurements show no sign of that at these orders, although a worst-case family with\nsuch behaviour could coexist with modest averages.")
sub('p8',r"We timed it on a single 2.8\,GHz Intel Xeon core of a virtual machine.",
 "We timed it on a single 2.8\\,GHz Intel Xeon core of a virtual machine. Clock frequency and turbo\nbehaviour were controlled neither here nor on the cluster, so absolute times are indicative; the\nconclusions rest on ratios far larger than such effects.")
sub('p8',r"\section{Case splitting by a fixed transposition",
 "\\paragraph{Knowingly inconsistent messages.} The source does not encode the matching constraints\nbetween the outside partners of split coordinates, which keeps it simple and its message count in\nclosed form. Some messages therefore give two split coordinates the same outside partner, and the\nterminal solver rejects them at once. At depth 3 with $D=29$, $27^3-27\\cdot26\\cdot25=2{,}133$ of the\n$19{,}764$ messages, about $11\\%$, are of this kind.\n\n\\section{Case splitting by a fixed transposition")
sub('p8',r"\section{Costas arrays from first principles}",
 "\\paragraph{Dependencies.} This paper uses only the shared notation at the front of the volume, and\ncompares its results with the published enumerations of 1993 and 2009. It is independent of\nPapers~1--7.\n\n\\section{Costas arrays from first principles}")

# ---------------- Paper 8 reference list: swap Rintanen 2012 for 2011, add OEIS A003022
a,b=span('p8'); seg=s[a:b]
i=seg.index('\\begin{paperrefs}'); j=seg.index('\\end{paperrefs}')
refs=seg[i:j]
refs=re.sub(r'\\bibitem\{p8-rintanen2012\}.*?(?=\\bibitem|$)','',refs,flags=re.S)
refs=refs.rstrip()+"\n\\bibitem{p8-rintanen2011} J.~Rintanen, \\emph{Planning with SAT, admissible heuristics and A*}, Proceedings of the 22nd International Joint Conference on Artificial Intelligence (IJCAI), 2011.\n\\bibitem{p8-oeisgolomb} OEIS A003022, length of the shortest Golomb ruler with $n$ marks.\n"
s=s[:a]+seg[:i]+refs+seg[j:]+s[b:]
# ---------------- Paper 8: projection-level validation
import importlib.util as _iu
_sp=_iu.spec_from_file_location('pb','/tmp/proc/projblock.py'); _pb=_iu.module_from_spec(_sp); _sp.loader.exec_module(_pb)
a,b=span('p8'); s=s[:a]+_pb.apply(s[a:b],'p8-')+s[b:]

# ---------------- Paper 7: dyadic residue caps and M10 (closed direction)
a,b=span('p7'); seg=s[a:b]
k=seg.index('\\section{Status of the claims}')
seg=seg[:k]+open('/tmp/proc/p7caps.tex').read()+seg[k:]
i=seg.index('\\end{paperrefs}')
seg=seg[:i]+"\\bibitem{p7-sheridan2005} P.~Sheridan, D.~M.~Alexander and K.~S.~Nunn-Clark, \\emph{Fast Fourier transform in the spiral honeycomb image algebra}, Proceedings of the Third International Conference on Information Technology and Applications (ICITA'05), IEEE, 2005, \\href{https://doi.org/10.1109/ICITA.2005.143}{\\texttt{doi:10.1109/ICITA.2005.143}}.\n"+seg[i:]
s=s[:a]+seg+s[b:]
# ---------------- conclusions chapter
s=s.replace("\\end{document}", open('/tmp/proc/conclusions.tex').read()+"\n\\end{document}")
open(p,'w').write(s); print("revisions applied")
