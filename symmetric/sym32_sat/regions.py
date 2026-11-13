#!/usr/bin/env python3
"""Enumerate the 44,947 regions of the transpose-symmetric order-32 space.

A region is a reflection-canonical fixed-point set F. The partition is forced:
every transpose-symmetric permutation has exactly one F; F must be a Golomb
ruler (lemma D2); |F| in {0,2,4,6} because f=8 needs span 34 > 31 and f odd is
impossible for even n. Disjoint and exhaustive -- nothing is chosen here.
"""
import sys, csv
from itertools import combinations
N = 32
def canonical(F): return min(tuple(F), tuple(sorted(N-1-x for x in F)))
def regions():
    out = [((), 0)]
    for f in (2, 4, 6):
        seen = set()
        for F in combinations(range(N), f):
            if len({b-a for a, b in combinations(F, 2)}) != f*(f-1)//2: continue
            c = canonical(F)
            if c in seen: continue
            seen.add(c); out.append((c, f))
    return out
if __name__ == "__main__":
    R = regions()
    with open(sys.argv[1] if len(sys.argv) > 1 else "regions.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["region_id", "f", "fixed_points", "diameter", "even_fixed"])
        for i, (F, f) in enumerate(R):
            w.writerow([f"R{i:05d}", f, " ".join(map(str, F)),
                        (max(F)-min(F)) if F else 0,
                        sum(1 for x in F if x % 2 == 0)])
    from collections import Counter
    print(f"{len(R):,} regions: {dict(Counter(f for _, f in R))}")
