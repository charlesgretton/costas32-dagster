# Anchored insertions into paper bodies, applied before citations are resolved (see assemble.py).
# Each anchor must occur exactly once in its paper's body, or assembly stops.
INSERTS = [
 ('p1', "growth of the search is slightly worse than a factor of 5 per increment of $n$.\n", 'after', r"""
\subsection{Recent work, 2022--2026}
\label{sec:recent}
The enumeration frontier has not moved: Gulec and Abolghasemi, proposing a framework of ``universal
Costas matrices'' for reconstruction-based search, note that all Costas arrays are known only up to
order 29~\cite{gulec2026ucm}. Two structural results bear on searches at higher orders. Warnke, Correll
and Swanson proved that the proportion of permutations of order $n$ that are Costas arrays decays
exponentially, $C(n)/n!\le e^{-cn}$~\cite{warnke2023density}. Correll and Swanson showed that, unless
undiscovered sporadic arrays exist at high orders, the number of positive first differences of an
order-$n$ Costas array lies within 2.5 of $(n-1)/2$, and that this property alone yields only an
$O(n^{-1/2})$ density among permutations~\cite{correll2023difference}.

At order 32 itself there are two near-solutions and two restricted searches. An ant-colony search reported
an order-32 permutation with 17 violations of the Costas property after more than 10{,}000
CPU-days~\cite{vulakh2022mdraco}. In August 2026 Rosi\'c publicly documented a permutation with only two
repeated displacement vectors, the array $N_{32}$ of Paper~2, with a proof checked in DRAT format that no
Costas array lies within Hamming distance 12 of it and a program enumeration of distances 13 to 16 that
found none; the eight such balls around its symmetry orbit exclude about $3.3\times10^{17}$ permutations,
some $10^{-18}$ of all, and are expressly not a non-existence result~\cite{rosic2026gist}. The proof
package is held outside the published record and was not rechecked here. In a preprint, Dumitru and
Budala restrict the search at a new order to prefixes whose seven-dot difference signatures occur at
smaller orders: at order 28 such a vocabulary built from order 27 recovers 67 of the 89 known classes;
restricted sweeps at orders 30 and 31 return exactly the known arrays; and at order 32 the restricted
class is empty, after 102 GPU-hours. They stress that an order-32 array outside the class would simply be
sporadic, so this is not evidence against existence~\cite{dumitru2026localpatterns}. In a second preprint
they report an exhaustive census of transpose-symmetric arrays of orders 37 to 42, finding 4, 0, 16, 2, 12
and 4 of them, and no sporadic symmetric array at any order from 24 to 42~\cite{dumitru2026symmetriccensus}.
"""),
 ('p2', "$N_{32}'$ is a\ndihedral image of the known candidate $N_{32}$.\n", 'after', r"""
\paragraph{Attribution.} $N_{32}$ was publicly documented by Rosi\'c on 19 August
2026~\cite{rosic2026gist}, constructed as a corner extension of an exceptional order-31 array (``W0'') in
Beard's database of known Costas arrays. That order-31 array is a dihedral image of $C_{31}$, so the two
genealogies coincide: our searches reached the same order-31 array by one-dot augmentation of the
algebraic order-30 cores, and the same order-32 permutation by one further corner dot. We reached it
independently and claim no priority for it. Rosi\'c also reports a proof, checked in DRAT format, that
no order-32 Costas array lies within Hamming distance 12 of the candidate, and an exhaustive program
enumeration of distances 13 to 16 that found none; the 3.79\,GB proof package is held outside the
published record and was not rechecked here. For comparison, the best order-32 permutation reported by an
ant-colony search had 17 violations of the Costas property~\cite{vulakh2022mdraco}.
"""),
 ('p8', "They found no sporadic symmetric array at any order from 24 to 36.\n\\end{itemize}", 'replace', r"""They found no sporadic symmetric array at any order from 24 to 36.
\item In a 2026 preprint, Dumitru and Budala report an exhaustive census of transpose-symmetric
(main-diagonal symmetric) arrays of orders 37 to 42, and no sporadic symmetric array at any order from
24 to 42~\cite{dumitru2026symmetriccensus}.
\end{itemize}"""),
]
BIB = {
 'rosic2026gist': r"\bibitem{rosic2026gist} V.~Rosi\'c, \emph{Order-32 Costas array: reproducible bounded partial result}, GitHub gist, created 19 August 2026, \url{https://gist.github.com/vukrosic/afa4096cd8b16fe17dbf413f63422b72}. Unpublished; the DRAT proof package is held outside the gist.",
 'dumitru2026localpatterns': r"\bibitem{dumitru2026localpatterns} B.~Dumitru and C.~Budala, \emph{Local patterns and the cost of Costas array search}, preprint hal-05731061v1, 2026, \url{https://hal.science/hal-05731061}. Not peer-reviewed.",
 'dumitru2026symmetriccensus': r"\bibitem{dumitru2026symmetriccensus} B.~Dumitru and C.~Budala, \emph{An exhaustive census of main-diagonal symmetric Costas arrays of orders 37--42}, preprint arXiv:2608.28690, 2026. Not peer-reviewed.",
 'vulakh2022mdraco': r"\bibitem{vulakh2022mdraco} D.~Vulakh and R.~Finkel, \emph{Parallel $m$-dimensional relative ant colony optimization (mDRACO) for the Costas-array problem}, Soft Computing 26(12) (2022), 5765--5772.",
 'warnke2023density': r"\bibitem{warnke2023density} L.~Warnke, B.~Correll~Jr. and C.~N.~Swanson, \emph{The density of Costas arrays decays exponentially}, IEEE Transactions on Information Theory 69(1) (2023), 575--581.",
 'correll2023difference': r"\bibitem{correll2023difference} B.~Correll~Jr. and C.~N.~Swanson, \emph{Difference-based structural properties of Costas arrays}, Designs, Codes and Cryptography 91(3) (2023), 779--794.",
 'gulec2026ucm': r"\bibitem{gulec2026ucm} F.~Gulec and V.~Abolghasemi, \emph{Universal Costas matrices: towards a general framework for Costas array construction}, IEEE International Conference on Communications (ICC), Glasgow, 2026; arXiv:2602.03407.",
}
