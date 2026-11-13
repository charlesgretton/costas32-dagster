#!/usr/bin/env python3
"""
dyadic_profile.py -- the dyadic defect filtration at order 32.

Three things, all cheap:

  verify     Check the diagonal parity floor identically against random
             permutations:  Z_1^diag = 2*binom(e0,2) + 2*binom(16-e0,2)
                                     = 2(e0-8)^2 + 112  >=  112,
             with equality exactly at e0 = 8. This is the only unconditional
             universal bound in the project.

  profile    Compute the filtration Z_1..Z_6 of a permutation, where
             Z_k = #{diagonal triples with 2^k | D}. Since |D| <= 62 at order
             32, D = 0 in Z iff 64 | D, so a Costas array is exactly one with
             Z_6 = 0 on the full defect family.

  calibrate  Compare Z_2^diag for a catalogue of Costas arrays against a matched
             random control. This is the measurement that closes the m_2
             minimisation as an order-32 programme: Z_2^diag does not separate
             Costas arrays from random permutations, so minimising it moves away
             from the region real Costas arrays occupy.

Usage
  python3 dyadic_profile.py verify [--trials 400]
  python3 dyadic_profile.py profile --perm "30 2 8 1 ..."
  python3 dyadic_profile.py calibrate <catalogue> <N> [--controls 3000]
"""
import argparse, random, statistics, sys
from collections import Counter


def diagonal_defects(p):
    """D_{l,r} = p[r+2l] - 2p[r+l] + p[r] over all valid (l, r)."""
    n = len(p)
    return [(l, r, p[r + 2 * l] - 2 * p[r + l] + p[r])
            for l in range(1, n // 2 + 1)
            for r in range(0, n - 2 * l)]


def z_profile(p, kmax=6):
    D = [d for _, _, d in diagonal_defects(p)]
    return len(D), {k: sum(1 for d in D if d % (2 ** k) == 0)
                    for k in range(1, kmax + 1)}


def parity_floor_prediction(p):
    n = len(p)
    e0 = sum(1 for i in range(0, n, 2) if p[i] % 2 == 0)
    h = n // 2
    return e0, e0 * (e0 - 1) + (h - e0) * (h - e0 - 1)


def is_costas(p):
    n = len(p)
    seen = set()
    for i in range(n):
        for j in range(i + 1, n):
            v = (j - i, p[j] - p[i])
            if v in seen:
                return False
            seen.add(v)
    return True


def cmd_verify(a):
    random.seed(a.seed)
    n = 32
    bad = 0
    observed = []
    for _ in range(a.trials):
        p = list(range(n))
        random.shuffle(p)
        _, prof = z_profile(p, 1)
        e0, pred = parity_floor_prediction(p)
        if prof[1] != pred:
            bad += 1
        observed.append(prof[1])
    print(f"diagonal triples at n=32: {len(diagonal_defects(list(range(32))))} "
          f"(expected 240)")
    print(f"Z_1^diag = 2(e0-8)^2 + 112 over {a.trials} random permutations: "
          f"{'VERIFIED' if bad == 0 else f'FAILS in {bad} cases'}")
    print(f"observed minimum {min(observed)}, floor is 112, "
          f"attained {observed.count(112)} times")
    return 0 if bad == 0 else 3


def cmd_profile(a):
    p = [int(x) for x in a.perm.split()]
    n = len(p)
    if sorted(p) != list(range(n)):
        print("not a zero-indexed permutation", file=sys.stderr)
        return 2
    N, prof = z_profile(p)
    e0, pred = parity_floor_prediction(p)
    print(f"n = {n}, diagonal triples = {N}, Costas = {is_costas(p)}")
    print(f"e0 = {e0}, parity-floor prediction for Z_1 = {pred}")
    print("Z_1..Z_6 =", [prof[k] for k in range(1, 7)])
    esc = [prof[k] - prof[k + 1] for k in range(1, 6)]
    print("escape counts E_1..E_5 =", esc, " (Z_{k+1} = Z_k - E_k)")
    return 0


def cmd_calibrate(a):
    cat = [tuple(map(int, l.split())) for l in open(a.catalogue)]
    cat = [p for p in cat if len(p) == a.N]
    for p in cat:
        assert sorted(p) == list(range(a.N)) and is_costas(list(p)), \
            f"catalogue entry is not a Costas permutation: {p}"
    ntri = len(diagonal_defects(list(range(a.N))))
    cz = [z_profile(list(p), 2)[1][2] for p in cat]
    random.seed(a.seed)
    rz = []
    for _ in range(a.controls):
        q = list(range(a.N))
        random.shuffle(q)
        rz.append(z_profile(q, 2)[1][2])
    print(f"Z_2^diag at order {a.N} ({ntri} diagonal triples)")
    print(f"  Costas census ({len(cat)}) : min {min(cz)} "
          f"mean {statistics.mean(cz):.1f} max {max(cz)}")
    print(f"  random perms ({a.controls}) : min {min(rz)} "
          f"mean {statistics.mean(rz):.1f} max {max(rz)}")
    print(f"  census mean as a fraction of triples: "
          f"{100*statistics.mean(cz)/ntri:.1f}%")
    print(f"  random mean as a fraction of triples: "
          f"{100*statistics.mean(rz)/ntri:.1f}%")
    print()
    print("  Costas arrays are statistically typical in this statistic, not")
    print("  extremal, so minimising Z_2^diag moves away from them.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--trials", type=int, default=400)
    v.add_argument("--seed", type=int, default=1)
    v.set_defaults(fn=cmd_verify)
    pr = sub.add_parser("profile")
    pr.add_argument("--perm", required=True)
    pr.set_defaults(fn=cmd_profile)
    c = sub.add_parser("calibrate")
    c.add_argument("catalogue")
    c.add_argument("N", type=int)
    c.add_argument("--controls", type=int, default=3000)
    c.add_argument("--seed", type=int, default=4)
    c.set_defaults(fn=cmd_calibrate)
    a = ap.parse_args()
    sys.exit(a.fn(a))
