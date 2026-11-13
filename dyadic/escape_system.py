#!/usr/bin/env python3
"""
escape_system.py -- the conditioned dyadic test.

Scalar survivor counts Z_k discard the geometry of which defects share which
positions. This tool keeps it. For a permutation p of {0..n-1} and a level k:

  survivors      S_k = { omega : 2^k | R_omega },  R_omega the rectangle defect
                 R = p[r+l+h] - p[r+l] - p[r+h] + p[r]

  escape system  choosing bit b_k of p sends R -> R + 2^k * A_k with
                 A_k = b[r+l+h] - b[r+l] - b[r+h] + b[r].  A survivor escapes
                 iff  A_k = R/2^k + 1  (mod 2), so killing every survivor at one
                 step is the affine F_2 system

                        H_k b_k = c_k,

                 rows indexed by S_k, columns by positions, H_k[omega,i] the
                 parity of the multiplicity of i in {r, r+l, r+h, r+l+h}, and
                 c_k[omega] = (R_omega / 2^k) + 1  mod 2.

  balance        b_k must also split each residue class mod 2^k the way the
                 available values do, or the lift is not a permutation.

  Lambda_k(p)    the number of solutions of H_k b = c_k obeying that balance.

The point of the exercise is a comparison, not a bound: if Costas arrays and
random permutations are indistinguishable under rank, consistency and Lambda_k,
the dyadic branch closes.

Caveat, stated because it governs how the output must be read: a Costas array
does NOT need every survivor to escape in one step. It needs only S_6 empty.
Lambda_k > 0 is therefore sufficient but not necessary, and Lambda_k = 0 for a
genuine Costas array is not a contradiction.

  python3 escape_system.py calibrate <catalogue> <n> [--levels 1,2,3,4]
                                     [--sample 150] [--controls 150]
"""
import argparse, random, statistics, sys
from collections import Counter


def defects(n):
    """All rectangle defects (l,h,r) with l,h>=1 and r+l+h <= n-1."""
    out = []
    for l in range(1, n):
        for h in range(1, n):
            for r in range(0, n - l - h):
                out.append((l, h, r))
    return out


def is_costas(p):
    n = len(p); seen = set()
    for i in range(n):
        for j in range(i + 1, n):
            v = (j - i, p[j] - p[i])
            if v in seen:
                return False
            seen.add(v)
    return True


def row_mask(l, h, r):
    """Parity of the multiplicity of each position in {r, r+l, r+h, r+l+h}."""
    m = 0
    for pos in (r, r + l, r + h, r + l + h):
        m ^= (1 << pos)
    return m


def gauss(rows, rhs, ncols):
    """Solve H b = c over F_2. Returns (consistent, rank, particular, basis)."""
    rows = list(rows); rhs = list(rhs)
    piv = []
    r = 0
    for c in range(ncols):
        pr = None
        for i in range(r, len(rows)):
            if rows[i] >> c & 1:
                pr = i; break
        if pr is None:
            continue
        rows[r], rows[pr] = rows[pr], rows[r]
        rhs[r], rhs[pr] = rhs[pr], rhs[r]
        for i in range(len(rows)):
            if i != r and (rows[i] >> c & 1):
                rows[i] ^= rows[r]; rhs[i] ^= rhs[r]
        piv.append(c); r += 1
        if r == len(rows):
            break
    for i in range(r, len(rows)):
        if rows[i] == 0 and rhs[i] == 1:
            return False, r, None, None
    part = 0
    for i, c in enumerate(piv):
        if rhs[i]:
            part |= (1 << c)
    free = [c for c in range(ncols) if c not in piv]
    basis = []
    for f in free:
        v = 1 << f
        for i, c in enumerate(piv):
            if rows[i] >> f & 1:
                v |= (1 << c)
        basis.append(v)
    return True, r, part, basis


def balance_targets(n, k):
    """For each residue class s mod 2^k, how many of its values have bit k set."""
    t = Counter(); size = Counter()
    for v in range(n):
        s = v % (2 ** k)
        size[s] += 1
        if v >> k & 1:
            t[s] += 1
    return t, size


def analyse(p, k, D, cap=20):
    n = len(p)
    M = 2 ** k
    q = [x % M for x in p]
    rows = []; rhs = []
    for (l, h, r) in D:
        R = q[r + l + h] - q[r + l] - q[r + h] + q[r]
        if R % M == 0:
            rows.append(row_mask(l, h, r))
            rhs.append(((R // M) + 1) & 1)
    S = len(rows)
    if S == 0:
        return dict(S=0, rank=0, consistent=True, dim=n, Lam=None)
    ok, rank, part, basis = gauss(rows, rhs, n)
    if not ok:
        return dict(S=S, rank=rank, consistent=False, dim=None, Lam=0)
    dim = len(basis)
    tgt, _ = balance_targets(n, k)
    cls = {}
    for i in range(n):
        cls.setdefault(q[i], []).append(i)

    def balanced(b):
        for s, idx in cls.items():
            if sum((b >> i) & 1 for i in idx) != tgt[s]:
                return False
        return True

    if dim > cap:
        return dict(S=S, rank=rank, consistent=True, dim=dim, Lam=None)
    Lam = 0
    for mask in range(1 << dim):
        b = part
        mm = mask
        j = 0
        while mm:
            if mm & 1:
                b ^= basis[j]
            mm >>= 1; j += 1
        if balanced(b):
            Lam += 1
    return dict(S=S, rank=rank, consistent=True, dim=dim, Lam=Lam)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("calibrate")
    c.add_argument("catalogue"); c.add_argument("n", type=int)
    c.add_argument("--levels", default="1,2,3,4")
    c.add_argument("--sample", type=int, default=150)
    c.add_argument("--controls", type=int, default=150)
    c.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()

    n = a.n
    cat = [tuple(map(int, l.split())) for l in open(a.catalogue)]
    cat = [p for p in cat if len(p) == n]
    for p in cat:
        assert sorted(p) == list(range(n)) and is_costas(list(p)), \
            "catalogue entry is not a Costas permutation"
    random.seed(a.seed)
    cs = random.sample(cat, min(a.sample, len(cat)))
    ctrl = []
    while len(ctrl) < a.controls:
        q = list(range(n)); random.shuffle(q); ctrl.append(tuple(q))
    D = defects(n)
    print(f"order {n}: {len(D)} rectangle defects, "
          f"{len(cs)} Costas arrays vs {len(ctrl)} random permutations")
    print(f"{'k':>2} {'arm':<7} {'|S_k|':>9} {'rank':>6} {'incons':>7} "
          f"{'dim':>5} {'Lam=0':>7} {'Lam>0':>7} {'unknown':>8}")
    for k in [int(x) for x in a.levels.split(",")]:
        for nm, arm in (("costas", cs), ("random", ctrl)):
            S = []; rk = []; inc = 0; dm = []; l0 = 0; lp = 0; unk = 0
            for p in arm:
                r = analyse(list(p), k, D)
                S.append(r["S"]); rk.append(r["rank"])
                if not r["consistent"]:
                    inc += 1; continue
                dm.append(r["dim"])
                if r["Lam"] is None: unk += 1
                elif r["Lam"] == 0: l0 += 1
                else: lp += 1
            print(f"{k:>2} {nm:<7} {statistics.mean(S):>9.1f} "
                  f"{statistics.mean(rk):>6.1f} {inc:>7} "
                  f"{(statistics.mean(dm) if dm else 0):>5.1f} "
                  f"{l0:>7} {lp:>7} {unk:>8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
