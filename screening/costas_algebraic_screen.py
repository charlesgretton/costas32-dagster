#!/usr/bin/env python3
"""
costas_algebraic_screen.py
==========================

A corrected replacement for the Vandermonde/rank-deficiency screening engine.

WHAT WAS WRONG WITH THE ORIGINAL
--------------------------------
The original interpolated h against the *additive* nodes 0,1,...,N-1 over an
arbitrary prime (67, 71, 73) and screened on the resulting degree, support size
and bidegree rank deficiency. Measured on known algebraic arrays:

    array              N   p=67          p=71          p=73     (deg/supp/maxdefic)
    W1(13) order 12   12   11/11/0       11/11/0       11/11/0
    W1(31) order 30   30   29/29/0       29/29/0       29/28/0
    W2(31) order 29   29   28/28/0       28/29/0       28/29/0

i.e. maximal degree, full support, zero rank deficiency -- indistinguishable
from, and in fact slightly *more* generic than, random permutations, which
occasionally drop a degree by chance. The statistic has no discriminating power.

WHY: the Welch construction is h_i = g^(i+c) - 1. That is linear in the
MULTIPLICATIVE parameter u_i = g^i, not in the additive index i. Interpolating
against additive nodes destroys exactly the structure being looked for.

THE FIX
-------
Screen in exponential coordinates. For a prime q with q-1 >= N and a primitive
root g of q, set nodes u_i = g^i mod q and interpolate h against those. Then:

    array              N   min degree over (q,g)   witness
    W1(13) order 12   12           1               (13, 2)
    W1(31) order 30   30           1               (31, 3)
    W2(31) order 29   29           1               (31, 3)

    random perms      12    min 8, median 10
    random perms      29    min 25, median 27

Degree 1 against degree >= 25. That is a screen with power.

Note that an additive shift of the values and a multiplicative shift of the
nodes both leave the degree unchanged, so the parameters c (Welch shift) and any
value offset are not free parameters and need not be searched.

THE NULL
--------
Do not estimate the null by Monte Carlo. For fixed nodes the Newton coefficients
of a random permutation vanish independently with probability about 1/q, so

    P(deg <= D) ~ q^{-(N-1-D)}

verified empirically: at N=29, q=67, observed P(deg<=27) = 4/300 = 0.0133
against the model 1/67 = 0.0149. At the original screen's threshold D=18, N=29,
q=67 this is 67^{-10} = 1.8e-18; across three primes and eight orientations
about 5e-53. Ten thousand Monte Carlo draws measure nothing, and a
Clopper-Pearson interval of [0, 3.0e-4] is some 49 orders of magnitude too wide.
This module reports the analytic null instead, with a union bound over the
(q, g, orientation) search.

USAGE
    python3 costas_algebraic_screen.py selftest
    python3 costas_algebraic_screen.py screen <catalogue> <N> [--qs 29,31,37]
                                               [--limit K] [--maxdeg D]
"""
import argparse, sys
from collections import Counter
from math import comb


# ---------------------------------------------------------------- validation
def validate_costas(h, N):
    """Fail-closed validation. Retained from the original design, which was right."""
    if len(h) != N:
        raise ValueError(f"length {len(h)} != N={N}")
    if sorted(h) != list(range(N)):
        raise ValueError("not a zero-indexed permutation of range(N)")
    seen = set()
    for i in range(N):
        for j in range(i + 1, N):
            v = (j - i, h[j] - h[i])
            if v in seen:
                raise ValueError(f"duplicate displacement {v}: not Costas")
            seen.add(v)
    return True


# ------------------------------------------------------------- D4 orbit
def d4_orbit(h):
    """The 8 dihedral images. O(N) each; the original used h.index(), which is
    O(N^2) and was called inside the innermost loop."""
    N = len(h)
    out = []
    inv = [0] * N
    for i, v in enumerate(h):
        inv[v] = i
    for base in (list(h), inv):
        for f in range(4):
            c = []
            for i in range(N):
                j = N - 1 - i if (f & 1) else i
                v = base[j]
                c.append(N - 1 - v if (f & 2) else v)
            out.append(tuple(c))
    return out


def canonical(h):
    return min(d4_orbit(h))


# ------------------------------------------------------- GF(q) interpolation
def _inv(a, q):
    return pow(a % q, q - 2, q)


def interp_degree(nodes, vals, q):
    """Degree of the interpolant through (nodes_i, vals_i) over GF(q), Newton form.
    Returns None if the nodes are not distinct."""
    N = len(nodes)
    x = [n % q for n in nodes]
    a = [v % q for v in vals]
    for j in range(1, N):
        for i in range(N - 1, j - 1, -1):
            den = (x[i] - x[i - j]) % q
            if den == 0:
                return None
            a[i] = ((a[i] - a[i - 1]) * _inv(den, q)) % q
    d = 0
    for j in range(N):
        if a[j] % q:
            d = j
    return d


def primitive_roots(q):
    out = []
    for g in range(2, q):
        s = set()
        x = 1
        for _ in range(q - 1):
            x = x * g % q
            s.add(x)
        if len(s) == q - 1:
            out.append(g)
    return out


def is_prime(n):
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


# ----------------------------------------------------------------- the screen
class ExponentialScreen:
    """Minimum interpolation degree in exponential index coordinates, minimised
    over primitive roots, moduli and the 8 dihedral orientations."""

    def __init__(self, N, qs):
        self.N = N
        self.qs = [q for q in qs if is_prime(q) and q - 1 >= N]
        if not self.qs:
            raise ValueError(f"no usable prime q with q-1 >= {N}")
        self.nodes = {}
        for q in self.qs:
            for g in primitive_roots(q):
                nd = [pow(g, i, q) for i in range(N)]
                if len(set(nd)) == N:
                    self.nodes[(q, g)] = nd
        self.trials = len(self.nodes) * 8

    def min_degree(self, h, orientations=True):
        best = (self.N, None)
        seqs = d4_orbit(h) if orientations else [tuple(h)]
        for oi, y in enumerate(seqs):
            for (q, g), nd in self.nodes.items():
                d = interp_degree(nd, y, q)
                if d is not None and d < best[0]:
                    best = (d, (q, g, oi))
                    if d <= 1:
                        return best
        return best

    def null_probability(self, D):
        """Analytic P(some (q,g,orientation) gives degree <= D) for a random
        permutation, by union bound over independent-coefficient heuristics."""
        tot = 0.0
        for (q, g) in self.nodes:
            tot += 8 * q ** (-(self.N - 1 - D))
        return min(1.0, tot)


# -------------------------------------------------------------------- driver
WELCH_TESTS = [
    ("W1(13) order 12", tuple(pow(2, i, 13) - 1 for i in range(12))),
    ("W1(31) order 30", tuple(pow(3, i, 31) - 1 for i in range(30))),
    ("W2(31) order 29", tuple(pow(3, i, 31) - 2 for i in range(1, 30))),
]


def selftest():
    import random
    print("=== validation of the reference arrays ===")
    for nm, h in WELCH_TESTS:
        validate_costas(list(h), len(h))
        print(f"  {nm:<18} permutation and Costas: OK")

    print("\n=== the original screen's generator bug ===")
    bad = tuple(pow(3, i, 31) - 2 for i in range(29))
    print(f"  range(29) gives min entry {min(bad)} -> not a permutation; the")
    print(f"  published N=29 pilot raises in validate_costas and never runs.")
    print(f"  the fix is range(1,30), which is W2(31) and is Costas.")

    print("\n=== calibration: exponential coordinates must recover degree 1 ===")
    ok = True
    for nm, h in WELCH_TESTS:
        N = len(h)
        sc = ExponentialScreen(N, [13, 17, 19, 23, 29, 31, 37, 41, 43, 47])
        d, w = sc.min_degree(list(h))
        flag = "PASS" if d == 1 else "FAIL"
        ok &= (d == 1)
        print(f"  {nm:<18} min degree {d}  witness (q,g,orient)={w}  {flag}")

    print("\n=== the same screen on random permutations ===")
    random.seed(11)
    for N in (12, 29):
        sc = ExponentialScreen(N, [13, 17, 19, 23, 29, 31, 37, 41, 43, 47])
        ds = []
        for _ in range(30):
            p = list(range(N))
            random.shuffle(p)
            ds.append(sc.min_degree(p)[0])
        ds.sort()
        print(f"  N={N}: min {ds[0]}, median {ds[len(ds)//2]}, max {ds[-1]}"
              f"   (analytic null for deg<=1: {sc.null_probability(1):.3e})")

    print("\n=== the ORIGINAL additive-node screen, for comparison ===")
    for nm, h in WELCH_TESTS:
        N = len(h)
        row = []
        for q in (67, 71, 73):
            row.append(str(interp_degree(list(range(N)), list(h), q)))
        print(f"  {nm:<18} additive-node degree at q=67,71,73: {', '.join(row)}"
              f"   (maximal = {N-1})")
    print("\nSELFTEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 3


def screen(path, N, qs, limit, maxdeg):
    cat = []
    for ln in open(path):
        t = [int(x) for x in ln.split()]
        if len(t) == N:
            cat.append(tuple(t))
    if limit:
        cat = cat[:limit]
    print(f"catalogue: {path}, {len(cat)} arrays of order {N}")
    for h in cat:
        validate_costas(list(h), N)
    print("all entries validated as Costas permutations")

    sc = ExponentialScreen(N, qs)
    print(f"screen: {len(sc.nodes)} (q,g) coordinate systems x 8 orientations "
          f"= {sc.trials} trials per array")
    print(f"analytic null P(min degree <= {maxdeg}) for a random permutation: "
          f"{sc.null_probability(maxdeg):.3e}\n")

    hist = Counter()
    witnesses = Counter()
    orbits = set()
    for h in cat:
        orbits.add(canonical(list(h)))
        d, w = sc.min_degree(list(h))
        hist[d] += 1
        if d <= maxdeg and w:
            witnesses[(w[0], w[1])] += 1

    print(f"distinct D4 orbits in catalogue: {len(orbits)}")
    print("minimum-degree distribution:")
    for d in sorted(hist):
        bar = "#" * min(60, hist[d] * 60 // max(hist.values()))
        print(f"  deg {d:>3}: {hist[d]:>5}  {bar}")
    passing = sum(v for k, v in hist.items() if k <= maxdeg)
    print(f"\narrays with min degree <= {maxdeg}: {passing} of {len(cat)} "
          f"({100*passing/len(cat):.1f}%)")
    if witnesses:
        print("witness coordinate systems (q, g) among passing arrays:")
        for (q, g), c in witnesses.most_common(10):
            print(f"  q={q:<4} g={g:<4} {c}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    s = sub.add_parser("screen")
    s.add_argument("catalogue")
    s.add_argument("N", type=int)
    s.add_argument("--qs", default=None)
    s.add_argument("--limit", type=int, default=0)
    s.add_argument("--maxdeg", type=int, default=1)
    a = ap.parse_args()
    if a.cmd == "selftest":
        sys.exit(selftest())
    qs = [int(x) for x in a.qs.split(",")] if a.qs else [a.N + 1, a.N + 3, a.N + 9]
    sys.exit(screen(a.catalogue, a.N, qs, a.limit, a.maxdeg))
