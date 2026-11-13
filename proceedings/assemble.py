import re, json
MAIN='/home/claude/costas32/report/costas32_report.tex'
SYM='/tmp/texbuild/costas32_symmetric_report.tex'
M=open(MAIN).read().split('\n'); S=open(SYM).read().split('\n')
P=json.load(open('/tmp/proc/parts.json'))
def L(src,a,b): return '\n'.join(src[a-1:b])
def shift(t): return t.replace('\\subsubsection','\\SUBSUBX').replace('\\subsection','\\section').replace('\\SUBSUBX','\\subsection')
def body_of_section(src,a,b):   # a \section block: drop its heading, promote its subsections
    t=L(src,a,b); t=re.sub(r'^\\section\*?\{[^\n]*\n(\\label\{[^}]*\}\n)?','',t,count=1); return shift(t)
F=json.load(open('/tmp/proc/front.json'))
papers=[]
# 1 landscape
papers.append(dict(id='p1', body= body_of_section(M,242,388)+'\n'+L(M,389,478)+'\n'+shift(L(M,1462,1525))))
# 2 augmentation
rung2="\\section{The rungs $k=1$ and $k=2$}\n\\label{sec:rungs}\n\n"+P['intro']+P['rows12']+P['k1']+P['k2']+P['thm2']+'\n'+P['canon']
papers.append(dict(id='p2', body= shift(P['formulation'])+'\n'+shift(P['catalogue'])+'\n'+rung2+'\n'+shift(L(M,730,793))))
# 3 deletion minors
rung3=("\\section{The rungs $k=3$ and $k=4$}\n\\label{sec:rungs}\n\n"+P['intro']+P['rows34']+P['k4']+thm4 if False else
      "\\section{The rungs $k=3$ and $k=4$}\n\\label{sec:rungs}\n\n"+P['intro']+P['rows34']+P['k4']+P['thm4']+'\n'+P['colconv']+
      "\n\\paragraph{Rung $k=3$ (order 29 $\\to$ 32).}\nThe order-29 catalogue is the complete published census, reconstructed and verified as\ndescribed in the paper on the order-29 census in these proceedings. In brief: "+P['k3_recon']+P['k3_run']+P['thm3']+'\n'+P['indep']+'\n'+P['canon'])
papers.append(dict(id='p3', body= shift(P['formulation'])+'\n'+shift(P['catalogue'])+'\n'+rung3+'\n'+L(M,794,844)))
# 4 census
papers.append(dict(id='p4', body="\\section{Reconstruction from the published representatives}\n\\label{sec:recon}\n"+P['k3_recon']+'\n'+P['gap']+'\n'+shift(L(M,3257,3312))))
# 5 propagation, 6 extinction, 7 dyadic
papers.append(dict(id='p5', body=body_of_section(M,1121,1461)))
papers.append(dict(id='p6', body=body_of_section(M,2588,2864)))
papers.append(dict(id='p7', body=body_of_section(M,2035,2280)))
# 8 symmetric
_heads=[k for k,l in enumerate(S,1) if re.match(r'\\(section|part|appendix)\b|\\begin\{thebibliography\}|\\end\{document\}',l)]
_inc=['\\section{Introduction}','\\section{Costas arrays from first principles}','\\section{Symmetry, and','\\section{Earlier structural',
      '\\section{The fixed-point partition}','\\section{SAT encoding of a region}','\\section{Solvers, verdicts','\\section{The Dagster native split',
      '\\section{Case splitting by a fixed','\\section{Results}','\\section{Performance analysis}','\\section{Cost}','\\section{Claim boundary','\\section{Conclusion}']
symranges=[]
for _p in _inc:
    _a=[k for k in _heads if S[k-1].startswith(_p)]
    assert len(_a)==1, ("Paper 8 section not found uniquely", _p, _a)
    _a=_a[0]; _b=min(k for k in _heads if k>_a)-1; symranges.append((_a,_b))
papers.append(dict(id='p8', body='\n'.join(L(S,a,b) for a,b in symranges)))
papers.append(dict(id='p9', body=open('/tmp/proc/p9body.tex').read()))
papers.append(dict(id='p10', body=open('/tmp/proc/p10body.tex').read()))
# ---- anchored insertions (inserts.py), applied before citations are resolved
import sys as _sys; _sys.path.insert(0,'/tmp/proc')
from inserts import INSERTS, BIB as _NEWBIB
for _pid,_anchor,_mode,_text in INSERTS:
    _p=[q for q in papers if q['id']==_pid][0]; _n=_p['body'].count(_anchor)
    if _n!=1: raise SystemExit(f"INSERT FAILED: anchor for {_pid} occurs {_n} times: {_anchor[:60]!r}")
    _p['body']=_p['body'].replace(_anchor, _anchor+_text if _mode=='after' else (_text+_anchor if _mode=='before' else _text),1)
# ---- bibliographies
def bibitems(src):
    t='\n'.join(src); t=t[t.index('\\begin{thebibliography}'):t.index('\\end{thebibliography}')]
    items={}
    for blk in re.split(r'(?=\\bibitem)',t)[1:]:
        k=re.match(r'\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}',blk).group(1); items[k]=blk.strip()
    return items
B=bibitems(M); B.update({k:v for k,v in bibitems(S).items() if k not in B})
B.update(_NEWBIB)
B['rintanen2011']=r'\bibitem{rintanen2011} J.~Rintanen, \emph{Planning with SAT, admissible heuristics and A*}, Proceedings of the 22nd International Joint Conference on Artificial Intelligence (IJCAI), 2011.'
B['oeisgolomb']=r'\bibitem{oeisgolomb} OEIS A003022, length of the shortest Golomb ruler with $n$ marks.'
B['mpttw2015']=r"\bibitem{mpttw2015} A.~Muratovi\'c-Ribi\'c, A.~Pott, D.~Thomson and Q.~Wang, \emph{On the characterization of a semi-multiplicative analogue of planar functions over finite fields}, in Topics in Finite Fields, Contemporary Mathematics 632, American Mathematical Society, 2015, 317--325."
B['torresrubio2023']=r'\bibitem{torresrubio2023} J.~Torres and I.~Rubio, \emph{Circular Costas maps: a multidimensional analog of circular Costas sequences}, Cryptography and Communications 15(5) (2023), 941--958, \href{https://doi.org/10.1007/s12095-023-00654-2}{\texttt{doi:10.1007/s12095-023-00654-2}}.'
B['golombmoreno']=r'\bibitem{golombmoreno} S.~W.~Golomb and O.~Moreno, \emph{On periodicity properties of Costas arrays and a conjecture on permutation polynomials}, IEEE Transactions on Information Theory 42(6) (1996), 2252--2253.'
B['knuth1975']=r'\bibitem{knuth1975} D.~E.~Knuth, \emph{Estimating the efficiency of backtrack programs}, Mathematics of Computation 29 (1975), 121--136.'
B['kilby2006']=r'\bibitem{kilby2006} P.~Kilby, J.~Slaney, S.~Thi\'ebaux and T.~Walsh, \emph{Estimating search tree size}, Proceedings of the 21st National Conference on Artificial Intelligence (AAAI), 2006.'
B['sherali1990']=r'\bibitem{sherali1990} H.~D.~Sherali and W.~P.~Adams, \emph{A hierarchy of relaxations between the continuous and convex hull representations for zero-one programming problems}, SIAM Journal on Discrete Mathematics 3(3) (1990), 411--430.'
B['elffers2018']=r'\bibitem{elffers2018} J.~Elffers and J.~Nordstr\"om, \emph{Divide and conquer: towards faster pseudo-Boolean solving}, Proceedings of the 27th International Joint Conference on Artificial Intelligence (IJCAI), 2018.'
B['drakakis28']=r'\bibitem{drakakis28} K.~Drakakis, F.~Iorio and S.~Rickard, \emph{The enumeration of Costas arrays of order 28 and its consequences}, Advances in Mathematics of Communications, 2011.'
# ---- per-paper transform
def transform(pid,t):
    t=re.sub(r'\\label\{([^}]*)\}',lambda m:'\\label{%s-%s}'%(pid,m.group(1)),t)
    t=re.sub(r'\\(ref|eqref|pageref)\{([^}]*)\}',lambda m:'\\%s{%s-%s}'%(m.group(1),pid,m.group(2)),t)
    cited=[]
    def cite(m):
        keys=[k.strip() for k in m.group(2).split(',')]
        for k in keys:
            if k not in cited: cited.append(k)
        return '\\cite%s{%s}'%(m.group(1) or '',','.join(pid+'-'+k for k in keys))
    t=re.sub(r'\\cite(\[[^\]]*\])?\{([^}]*)\}',cite,t)
    return t,cited
out=[]
for p in papers:
    f=F[p['id']]
    pre=P['prelim'] if p['id']!='p8' else ''
    txt=("\\chapter{%s}\\label{paper}\n\\paperauthor\n\\paperabstract{%s}\n\n\\section{Introduction}\\label{sec:paperintro}\n%s\n\n"%(f['title'],f['abstract'],f['intro'])
         if p['id']!='p8' else "\\chapter{%s}\\label{paper}\n\\paperauthor\n\\paperabstract{%s}\n\n"%(f['title'],f['abstract']))
    txt+=pre+'\n'+p['body']+'\n\n'+("\\section{Status of the claims}\\label{sec:status}\n"+f['status'] if f.get('status') else '')
    txt,cited=transform(p['id'],txt)
    missing=[k for k in cited if k not in B]
    if missing: print(p['id'],"MISSING BIB:",missing)
    bib="\n\\begin{paperrefs}\n"+'\n'.join(re.sub(r'\\bibitem(\[[^\]]*\])?\{([^}]*)\}',lambda m:'\\bibitem%s{%s-%s}'%(m.group(1) or '',p['id'],m.group(2)),B[k]) for k in cited if k in B)+"\n\\end{paperrefs}\n" if cited else ''
    out.append(txt+bib)
    print(p['id'],"chars",len(txt),"refs",len(cited))
pre=open('/tmp/proc/preamble.tex').read()
doc=pre+"\n\\begin{document}\n"+open('/tmp/proc/frontmatter.tex').read()+'\n'+'\n\\clearpage\n'.join(out)+"\n\\end{document}\n"
open('/tmp/proc/costas32_proceedings.tex','w').write(doc); print("assembled")
