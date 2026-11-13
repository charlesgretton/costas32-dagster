import random, sys
from itertools import combinations

def is_ddc(pts):
    d = set()
    for a, b in combinations(pts, 2):
        v = (b[0]-a[0], b[1]-a[1])
        if v in d or (-v[0], -v[1]) in d:
            return False
        d.add(v)
    return True

def is_perm_ddc(pts):
    if len({p[0] for p in pts}) != len(pts): return False
    if len({p[1] for p in pts}) != len(pts): return False
    return is_ddc(pts)

# ---- (a) is the n x n grid a B_{3,1}-set?  (hypothesis of Dias da Silva-Nathanson, h=2)
def b31_counterexample(n):
    G = [(i, j) for i in range(n) for j in range(n)]
    seen = {}
    for t in combinations(G, 3):
        s = (t[0][0]+t[1][0]+t[2][0], t[0][1]+t[1][1]+t[2][1])
        for u in seen.get(s, []):
            if not (set(u) & set(t)):
                return u, t
        seen.setdefault(s, []).append(t)
    return None

# ---- (b)/(c) exchange axiom: find DDCs A, B with |A| < |B| and no augmentation of A from B
def exchange_fails(n, perm=False, tries=400000, seed=1):
    rng = random.Random(seed)
    G = [(i, j) for i in range(n) for j in range(n)]
    test = is_perm_ddc if perm else is_ddc
    maximals = {}
    for _ in range(tries):
        rng.shuffle(G)
        cur = []
        for p in G:
            if test(cur + [p]):
                cur.append(p)
        key = tuple(sorted(cur))
        maximals[key] = len(cur)
    sizes = sorted({v for v in maximals.values()})
    small = min(maximals.values()); big = max(maximals.values())
    A = next(k for k, v in maximals.items() if v == small)
    B = next(k for k, v in maximals.items() if v == big)
    return sizes, small, big, A, B, len(maximals)

if __name__ == '__main__':
    print("=== (a) is the grid a B_{3,1}-set? ===")
    for n in (3, 4):
        c = b31_counterexample(n)
        print(f"  n={n}: {'B_31 holds' if c is None else f'FAILS: {c[0]} and {c[1]} are disjoint with equal sum'}")

    print("\n=== (b) inclusion-maximal DDCs in the n x n grid ===")
    for n in (4, 5, 6, 7):
        sizes, sm, bg, A, B, cnt = exchange_fails(n, perm=False, tries=20000)
        print(f"  n={n}: maximal-DDC sizes found {sizes}  ({cnt} distinct maximals sampled)")
        if sm < bg:
            print(f"        smallest maximal {A} (size {sm}); largest size {bg}")

    print("\n=== (c) inclusion-maximal PERMUTATION DDCs (partial Costas) ===")
    for n in (4, 5, 6, 7, 8):
        sizes, sm, bg, A, B, cnt = exchange_fails(n, perm=True, tries=20000)
        print(f"  n={n}: maximal partial-Costas sizes found {sizes}  ({cnt} distinct sampled)")
        if sm < bg:
            print(f"        non-extendable example of size {sm}: {A}")
