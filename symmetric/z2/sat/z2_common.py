"""Z=2 shared mathematics. Deliberately plain loops — no bitsets, no incremental
state. This module must never import from the C++ search or its conventions:
it is one half of the independence required for F+."""
from itertools import combinations
N = 32
FAR = 16                                  # |i-j| >= FAR is "large"

def is_far(x, y):      return abs(x - y) >= FAR
def ll_pair(h, x, y):  return is_far(x, y) and is_far(h[x], h[y])

def large_large_pairs(h):
    return [(x, y) for x in range(N) for y in range(x+1, N) if ll_pair(h, x, y)]

def orbit_decomposition(h):
    """Z = I_F + q + 2C.  Returns (I_F, q, C, Z_direct)."""
    F = [i for i in range(N) if h[i] == i]
    I_F = sum(1 for x, y in combinations(F, 2) if is_far(x, y))
    q   = sum(1 for i in range(N) if h[i] > i and is_far(i, h[i]))
    LL  = {frozenset(p) for p in large_large_pairs(h)}
    seen, C = set(), 0
    for p in LL:
        if p in seen: continue
        x, y = tuple(p); img = frozenset((h[x], h[y]))
        seen.add(p)
        if img != p:
            C += 1; seen.add(img)
    return I_F, q, C, len(LL)

def signed_displacements(h):
    """All C(32,2) signed displacement vectors, oriented by smaller coordinate."""
    return [(y - x, h[y] - h[x]) for x in range(N) for y in range(x+1, N)]

def is_costas(h):
    seen = set()
    for v in signed_displacements(h):
        if v in seen: return False
        seen.add(v)
    return True

def fixed_far_pairs(F):
    return [(x, y) for x, y in combinations(F, 2) if is_far(x, y)]

def omitted_short_count(f, q):
    """f/2 + q - 1, from  15 - ((32-f)/2 - q)."""
    return f // 2 + q - 1

def parity_ok(F, Q, R):
    """sum_{L in Q} L  ==  a + sum_{r in R} r   (mod 2)."""
    a = sum(1 for x in F if x % 2 == 0)
    return sum(Q) % 2 == (a + sum(R)) % 2

def seed_partial(F):
    """Graph points of the fixed seed: h(x)=x for x in F, None elsewhere."""
    h = [None] * N
    for x in F: h[x] = x
    return h

def edge_graph_points(a, b):
    """A transposition (a,b) contributes graph points (a,b) and (b,a)."""
    return [(a, b), (b, a)]

def displacements_of(points):
    """Signed displacements among an explicit set of graph points."""
    out = []
    for (x, hx), (y, hy) in combinations(sorted(points), 2):
        lo, hi = (x, y) if x < y else (y, x)
        d = (hy - hx) if x < y else (hx - hy)
        out.append((hi - lo, d))
    return out
