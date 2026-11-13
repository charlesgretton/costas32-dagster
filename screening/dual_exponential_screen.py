#!/usr/bin/env python3
"""
dual_exponential_screen.py
==========================

Extends the single-exponential screen with dual-exponential coordinates and
extension-field arithmetic, so that Golomb constructions are visible.

  single-exponential (Welch):  nodes u_i = g^i in F_q,  values h_i
                               W1(p) has h_i = g^(i+c) - 1 = g^c u_i - 1,  d = 1
  dual-exponential (Golomb):   nodes u_i = a^(i+1),  values v_i = b^(h_i+1)
                               G2(q) has a^i + b^j = 1, i.e. v = 1 - u,     d = 1

Offsets are free: u -> lambda*u rescales coefficients as a_j -> a_j lambda^-j,
and v -> mu*v scales the whole interpolant, so neither changes the degree.
No grid search over c1, c2 is needed.

Fields: prime GF(p), and GF(2^m) for m = 3,4,5 with standard modulus. Golomb of
order 28 requires q = 32 = 2^5 (G4) and q = 31 (G3), so extension-field support
is not optional here.

  python3 dual_exponential_screen.py selftest
  python3 dual_exponential_screen.py classify <catalogue> <N>
"""
import argparse, sys
from collections import Counter


# ------------------------------------------------------------------- fields
class Field:
    """Minimal finite field: GF(p) or GF(2^m). Elements are ints 0..q-1."""

    def __init__(self, q):
        self.q = q
        self.char2 = (q & (q - 1)) == 0 and q > 1
        if self.char2:
            m = q.bit_length() - 1
            mod = {8: 0b1011, 16: 0b10011, 32: 0b100101, 64: 0b1000011}[q]
            self.m, self.mod = m, mod
            self.exp = [0] * (q - 1)
            self.log = [-1] * q
            x = 1
            for i in range(q - 1):
                self.exp[i] = x
                self.log[x] = i
                x = self._mul_raw(x, 2)
            if x != 1:
                raise ValueError(f"2 is not primitive in GF({q})")
        else:
            if not self._is_prime(q):
                raise ValueError(f"{q} is neither prime nor a power of two")

    @staticmethod
    def _is_prime(n):
        if n < 2:
            return False
        d = 2
        while d * d <= n:
            if n % d == 0:
                return False
            d += 1
        return True

    def _mul_raw(self, a, b):
        r = 0
        while b:
            if b & 1:
                r ^= a
            b >>= 1
            a <<= 1
            if a & self.q:
                a ^= self.mod
        return r

    def add(self, a, b):
        return (a ^ b) if self.char2 else (a + b) % self.q

    def sub(self, a, b):
        return (a ^ b) if self.char2 else (a - b) % self.q

    def mul(self, a, b):
        if self.char2:
            if a == 0 or b == 0:
                return 0
            return self.exp[(self.log[a] + self.log[b]) % (self.q - 1)]
        return (a * b) % self.q

    def inv(self, a):
        if a == 0:
            raise ZeroDivisionError
        if self.char2:
            return self.exp[(-self.log[a]) % (self.q - 1)]
        return pow(a, self.q - 2, self.q)

    def pow(self, a, e):
        if self.char2:
            if a == 0:
                return 0
            return self.exp[(self.log[a] * e) % (self.q - 1)]
        return pow(a, e, self.q)

    def primitive_elements(self):
        """Generators of the multiplicative group."""
        out = []
        n = self.q - 1
        for g in range(2, self.q):
            x, seen = 1, set()
            for _ in range(n):
                x = self.mul(x, g)
                seen.add(x)
            if len(seen) == n:
                out.append(g)
        return out


def newton_degree(F, nodes, vals):
    """Degree of the interpolant through (nodes_i, vals_i) over F, or None if the
    nodes collide."""
    N = len(nodes)
    x = list(nodes)
    a = list(vals)
    for j in range(1, N):
        for i in range(N - 1, j - 1, -1):
            den = F.sub(x[i], x[i - j])
            if den == 0:
                return None
            a[i] = F.mul(F.sub(a[i], a[i - 1]), F.inv(den))
    d = 0
    for j in range(N):
        if a[j]:
            d = j
    return d


# -------------------------------------------------------------- D4 and utils
def d4_orbit(h):
    N = len(h)
    inv = [0] * N
    for i, v in enumerate(h):
        inv[v] = i
    out = []
    for base in (list(h), inv):
        for f in range(4):
            out.append(tuple((N - 1 - base[N - 1 - i if (f & 1) else i]) if (f & 2)
                             else base[N - 1 - i if (f & 1) else i]
                             for i in range(N)))
    return out


def canonical(h):
    return min(d4_orbit(h))


def costas0(h):
    n = len(h)
    s = set()
    for i in range(n):
        for j in range(i + 1, n):
            v = (j - i, h[j] - h[i])
            if v in s:
                return False
            s.add(v)
    return True


# ------------------------------------------------------------------ screens
class Screen:
    def __init__(self, N, qs):
        self.N = N
        self.fields = {}
        for q in qs:
            try:
                F = Field(q)
            except ValueError:
                continue
            if q - 1 < N:
                continue
            self.fields[q] = (F, F.primitive_elements())

    def single(self, h):
        """Welch-style: nodes exponential, values as integers in GF(p).
        Only meaningful over prime fields, where the array values are field
        elements rather than exponents."""
        best = (self.N, None)
        for oi, y in enumerate(d4_orbit(h)):
            for q, (F, prims) in self.fields.items():
                if F.char2:
                    continue
                for g in prims:
                    nd = [F.pow(g, i) for i in range(self.N)]
                    if len(set(nd)) < self.N:
                        continue
                    d = newton_degree(F, nd, list(y))
                    if d is not None and d < best[0]:
                        best = (d, ("single", q, g, oi))
                        if d <= 1:
                            return best
        return best

    def dual(self, h):
        """Golomb-style: both axes exponential. Values are used as exponents, so
        this works over extension fields as well."""
        best = (self.N, None)
        for oi, y in enumerate(d4_orbit(h)):
            for q, (F, prims) in self.fields.items():
                for a in prims:
                    nd = [F.pow(a, i + 1) for i in range(self.N)]
                    if len(set(nd)) < self.N:
                        continue
                    for b in prims:
                        vl = [F.pow(b, y[i] + 1) for i in range(self.N)]
                        d = newton_degree(F, nd, vl)
                        if d is not None and d < best[0]:
                            best = (d, ("dual", q, a, b, oi))
                            if d <= 1:
                                return best
        return best

    def classify(self, h):
        d1, w1 = self.single(h)
        if d1 <= 1:
            return d1, w1
        d2, w2 = self.dual(h)
        return (d1, w1) if d1 <= d2 else (d2, w2)


# ------------------------------------------------------------- constructions
def welch(p, g, c=0):
    return tuple(pow(g, i + c, p) - 1 for i in range(p - 1))


def golomb_prime(q, a, b):
    logb = {}
    x = 1
    for e in range(1, q):
        x = x * b % q
        logb[x] = e
    h = []
    for i in range(1, q - 1):
        t = (1 - pow(a, i, q)) % q
        if t == 0:
            return None
        j = logb.get(t)
        if j is None or j > q - 2:
            return None
        h.append(j - 1)
    return tuple(h) if sorted(h) == list(range(q - 2)) else None


def golomb_ext(q, a, b):
    F = Field(q)
    logb = {}
    x = 1
    for e in range(1, q):
        x = F.mul(x, b)
        logb[x] = e
    h = []
    for i in range(1, q - 1):
        t = F.sub(1, F.pow(a, i))
        if t == 0:
            return None
        j = logb.get(t)
        if j is None or j > q - 2:
            return None
        h.append(j - 1)
    return tuple(h) if sorted(h) == list(range(q - 2)) else None


def corner_deletions(p):
    n = len(p)
    out = []
    for ci in (0, n - 1):
        for want in (0, n - 1):
            if p[ci] != want:
                continue
            qq = [(v - 1 if v > want else v) for i, v in enumerate(p) if i != ci]
            if costas0(qq):
                out.append(tuple(qq))
    return out


def selftest():
    print("=== field arithmetic ===")
    for q in (29, 31, 32, 37):
        F = Field(q)
        pr = F.primitive_elements()
        print(f"  GF({q}): char2={F.char2}, {len(pr)} primitive elements, "
              f"first={pr[0] if pr else None}")

    print("\n=== single-exponential recovers Welch ===")
    for p, g in ((13, 2), (29, 2), (31, 3)):
        h = welch(p, g)
        assert costas0(h)
        sc = Screen(len(h), [p, p + 2, p + 6])
        d, w = sc.single(list(h))
        print(f"  W1({p}) order {len(h):>2}: single-exp degree {d}  witness {w}  "
              f"{'PASS' if d == 1 else 'FAIL'}")
        assert d == 1

    print("\n=== dual-exponential recovers Golomb, prime and extension field ===")
    g31 = golomb_prime(31, 3, 3)
    assert g31 and costas0(g31)
    sc = Screen(29, [31, 37])
    d, w = sc.dual(list(g31))
    print(f"  G2(31) order 29: dual-exp degree {d}  witness {w}  "
          f"{'PASS' if d == 1 else 'FAIL'}")
    assert d == 1

    g32 = golomb_ext(32, 2, 2)
    assert g32 and costas0(g32), "G2(32) generation failed"
    sc = Screen(30, [31, 32, 37])
    d, w = sc.dual(list(g32))
    print(f"  G2(32) order 30: dual-exp degree {d}  witness {w}  "
          f"{'PASS' if d == 1 else 'FAIL'}")
    assert d == 1

    print("\n=== does corner deletion preserve the coordinates? ===")
    for nm, arr, mode in (("W1(31)->order 29", welch(31, 3), "single"),
                          ("G2(31)->order 28", g31, "dual"),
                          ("G2(32)->order 29", g32, "dual")):
        dels = corner_deletions(list(arr))
        if not dels:
            print(f"  {nm}: no corner dot present, no deletion available")
            continue
        for q in dels[:1]:
            sc = Screen(len(q), [29, 31, 32, 37, 41])
            d, w = (sc.single(list(q)) if mode == "single" else sc.dual(list(q)))
            print(f"  {nm}: order {len(q)}, {mode}-exp degree {d}  witness {w}")
    print("\nSELFTEST PASS")
    return 0


def classify_catalogue(path, N, qs):
    cat = [tuple(map(int, l.split())) for l in open(path)]
    cat = [h for h in cat if len(h) == N]
    for h in cat:
        assert sorted(h) == list(range(N)) and costas0(h), "catalogue entry invalid"
    print(f"catalogue {path}: {len(cat)} validated order-{N} Costas arrays, "
          f"{len({canonical(list(h)) for h in cat})} D4 orbits")
    sc = Screen(N, qs)
    print(f"fields in use: {sorted(sc.fields)}\n")

    hist = Counter()
    residual = []
    for h in cat:
        d, w = sc.classify(list(h))
        tag = w[0] if (w and d <= 1) else "generic"
        hist[tag] += 1
        if d > 1:
            residual.append((h, d, w))
    print("classification of the census:")
    for k, v in hist.most_common():
        print(f"  {k:<10} {v:>5}  ({100*v/len(cat):.1f}%)")
    print(f"\nresidual (degree > 1 in both coordinate systems): {len(residual)} arrays, "
          f"{len({canonical(list(h)) for h, _, _ in residual})} D4 orbits")
    if residual:
        ds = Counter(d for _, d, _ in residual)
        print(f"  residual degree distribution: {dict(sorted(ds.items()))}")
        print(f"  canonical representatives:")
        for r in sorted({canonical(list(h)) for h, _, _ in residual}):
            print("   ", " ".join(map(str, r)))
    return residual


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    c = sub.add_parser("classify")
    c.add_argument("catalogue")
    c.add_argument("N", type=int)
    c.add_argument("--qs", default=None)
    a = ap.parse_args()
    if a.cmd == "selftest":
        sys.exit(selftest())
    qs = [int(x) for x in a.qs.split(",")] if a.qs else [29, 31, 32, 37, 41, 43]
    classify_catalogue(a.catalogue, a.N, qs)
