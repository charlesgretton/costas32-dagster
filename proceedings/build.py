import re
MAIN='/home/claude/costas32/report/costas32_report.tex'
SYM='/tmp/texbuild/costas32_symmetric_report.tex'
M=open(MAIN).read().split('\n'); S=open(SYM).read().split('\n')
def L(src,a,b): return '\n'.join(src[a-1:b])
def between(text,start,end=None):
    i=text.index(start); j=text.index(end,i) if end else len(text); return text[i:j]
def shift(t):
    t=t.replace('\\subsubsection','\\SUBSUBX').replace('\\subsection','\\section').replace('\\SUBSUBX','\\subsection')
    return t
def drop_section_line(t):
    return re.sub(r'^\\section\*?\{[^\n]*\n','',t,count=1)
# ---------- shared preliminaries for papers 1-7
notation=L(M,113,171)
notation=notation.replace('\\section{Notation}\n\\label{sec:notation}\n','')
_a=notation.index('\\endhead')+len('\\endhead'); _b=notation.index('\\bottomrule')
_rows=re.split(r'(?<=\\\\)\n',notation[_a:_b])
notation=notation[:_a]+'\n'.join(r for r in _rows if not re.match(r'\s*\$(\\Cm|\\At|\\RA_n|\\RRA)',r))+notation[_b:]
notation=notation.replace('p{0.78\\textwidth}','p{0.62\\textwidth}')
prelim=r"""\section{Preliminaries}\label{sec:notation}
A \emph{Costas array} of order $n$ is an $n\times n$ permutation array in which the displacement
vectors between pairs of dots are all distinct. Writing the array as a permutation $h$ of
$\{0,\dots,n-1\}$, with the dot of column $i$ in row $h_i$, the condition is that for each
horizontal separation $m$ the vertical differences $h_{i+m}-h_i$ are distinct. Costas arrays are
known at every order up to 31; orders 32 and 33 are the smallest for which existence is open.
The dihedral group $D_4$ of the square maps Costas arrays to Costas arrays, and arrays are
counted either individually or by $D_4$ orbit (equivalence class). Notation used in this paper:
"""+notation+"\n"
# ---------- rung subsection, split by content markers
R=L(M,562,729)
intro=between(R,'All rungs were run','\\begin{center}')
table=between(R,'\\begin{center}','\\paragraph{Rung $k=1$')
def rows(tab,keep):
    return '\n'.join(l for l in tab.split('\n') if not re.match(r'^[1-4] &',l) or l[0] in keep)
k1=between(R,'\\paragraph{Rung $k=1$','\\paragraph{Rung $k=2$')
k2=between(R,'\\paragraph{Rung $k=2$','\\paragraph{Rung $k=3$ (order 29')
k4=between(R,'\\paragraph{Rung $k=4$','\\begin{remark}[Column convention')
colconv=between(R,'\\begin{remark}[Column convention','\\paragraph{Rung $k=3$ is now')
k3=between(R,'\\paragraph{Rung $k=3$ is now','\\begin{theorem}[Census-complete rung')
k3_recon=between(k3,'The complete order-29 census','Running the rung over')
k3_run=between(k3,'Running the rung over')
thm3=between(R,'\\begin{theorem}[Census-complete rung','This is independent of')
indep=between(R,'This is independent of','\\paragraph{The generator gap')
gap=between(R,'\\paragraph{The generator gap','\\paragraph{Prior run')
canon=between(R,'\\begin{remark}[Canonical mode')
indep=indep.replace("Theorem~\\ref{thm:rungs}' $k=4$ clause","Theorem~\\ref{thm:rung4census}")
indep=indep.replace("Deriving the $k=4$ clause from the $k=3$ clause","Deriving Theorem~\\ref{thm:rung4census} from Theorem~\\ref{thm:rung3census}")
indep=indep.replace("deriving $k=3$ from\n$k=4$","deriving the latter from\nthe former")
thm2=r"""\begin{theorem}[Two-point augmentation]
\label{thm:rungs}
No order-32 Costas array arises as a two-point augmentation of any of the 664 generated order-30
Costas cores. Among all $324{,}741{,}120$ two-point augmentations the minimum defect is 2, attained
uniquely up to the dihedral group.

The conclusion is catalogue-relative: order 30 has never been enumerated, so its 664 cores are the
generated set.
\end{theorem}
"""
thm4=r"""\begin{theorem}[Census-complete rung $k=4$]
\label{thm:rung4census}
No order-32 Costas array contains an order-28 Costas array as a four-row, four-column deletion
minor. The statement quantifies over all 712 order-28 Costas arrays.
\end{theorem}
"""
formulation=L(M,482,500); catalogue=L(M,501,561)
open('/tmp/proc/parts.py','w').write('')
import json
prelim=open('/tmp/proc/prelim_short.tex').read()
json.dump(dict(prelim=prelim,intro=intro,table=table,k1=k1,k2=k2,k4=k4,colconv=colconv,k3_recon=k3_recon,
  k3_run=k3_run,thm3=thm3,indep=indep,gap=gap,canon=canon,thm2=thm2,thm4=thm4,formulation=formulation,
  catalogue=catalogue,rows12=rows(table,'12'),rows34=rows(table,'34')),open('/tmp/proc/parts.json','w'))
print("parts extracted:", ", ".join(f"{k}={len(v)}" for k,v in json.load(open('/tmp/proc/parts.json')).items()))
