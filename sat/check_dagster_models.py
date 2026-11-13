#!/usr/bin/env python3
"""
check_dagster_models.py -- decode and independently verify Dagster's dag_out.txt.

Nothing here trusts the solver.  Every reported model is decoded to a
permutation from scratch, re-checked for being a permutation, re-scored for the
Costas property with a fresh routine, and checked against the instance's own
declared constraint (score bound, parent structure, Hamming radius).

Usage
  python3 check_dagster_models.py <stem>.map dag_out.txt
  python3 check_dagster_models.py <stem>.map dag_out.txt --expect UNSAT
"""
import argparse, json, sys


def costas_score(p):
    n, seen, s = len(p), set(), 0
    for d in range(1, n):
        for i in range(n - d):
            z = (d, p[i + d] - p[i])
            if z in seen:
                s += 1
            seen.add(z)
    return s


def insert_extension(core, c, r):
    out = []
    for i in range(len(core) + 1):
        if i == c:
            out.append(r)
        else:
            v = core[i - 1] if i > c else core[i]
            out.append(v + 1 if v >= r else v)
    return out


def is_one_point_augmentation(p, core):
    """True iff deleting one dot from p and compressing yields core."""
    n = len(p)
    for c in range(n):
        r = p[c]
        red = []
        for i in range(n):
            if i == c:
                continue
            v = p[i]
            red.append(v - 1 if v > r else v)
        if red == core:
            return True, (c, r)
    return False, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mapfile")
    ap.add_argument("outfile")
    ap.add_argument("--expect", choices=["SAT", "UNSAT"], default=None)
    ap.add_argument("--count", action="store_true",
                    help="census mode: compare the model count with the published census")
    a = ap.parse_args()

    meta = json.load(open(a.mapfile))
    N, xb = meta["n"], meta["x_base"]

    models = []
    for line in open(a.outfile):
        lits = [int(t) for t in line.split() if t.lstrip("-").isdigit()]
        if not lits:
            continue
        true_x = {abs(l) for l in lits if l > 0 and xb <= abs(l) < xb + N * N}
        perm = [None] * N
        bad = False
        for v in sorted(true_x):
            i, j = divmod(v - xb, N)
            if perm[i] is not None:
                bad = True
            perm[i] = j
        models.append((line.rstrip(), perm, bad))

    print(f"instance: mode={meta['mode']} N={N} vars={meta['vars']} "
          f"clauses={meta['clauses']} dag_nodes={meta['dag_nodes']}")
    if meta["mode"] == "lemma":
        print(f"  declared bound: Costas score <= {meta['max_score']}")
    elif meta["mode"] == "census":
        print(f"  census instance: every model should be a Costas array of order {N}")
    else:
        print(f"  declared bound: Costas score 0, Hamming radius <= {meta['radius']}")
    print(f"models reported: {len(models)}")

    if a.count:
        seen, nonc, dup = set(), 0, 0
        for line, perm, bad in models:
            if bad or any(v is None for v in perm) or sorted(perm) != list(range(N)):
                nonc += 1; continue
            if costas_score(perm) != 0:
                nonc += 1; continue
            t = tuple(perm)
            if t in seen:
                dup += 1
            seen.add(t)
        exp = meta.get("expected_models")
        print(f"  distinct Costas arrays among the models : {len(seen)}")
        print(f"  models that are not Costas arrays       : {nonc}")
        print(f"  duplicate models                        : {dup}")
        print(f"  published census for N={N}               : {exp}")
        good = (nonc == 0 and dup == 0 and exp is not None and len(seen) == exp)
        print("VERDICT: " + ("PASS -- model count matches the census exactly"
                             if good else "FAIL -- see the discrepancies above"))
        return 0 if good else 1

    fails = 0
    for line, perm, bad in models:
        tag = []
        if bad or any(v is None for v in perm):
            print(f"  REJECT: model does not decode to one dot per column")
            fails += 1
            continue
        if sorted(perm) != list(range(N)):
            print(f"  REJECT: rows are not a permutation: {perm}")
            fails += 1
            continue
        s = costas_score(perm)
        tag.append(f"score={s}")
        if meta["mode"] == "lemma":
            if s > meta["max_score"]:
                print(f"  REJECT: score {s} exceeds declared bound {meta['max_score']}")
                fails += 1
                continue
            ok, at = is_one_point_augmentation(perm, meta["core"])
            if not ok:
                print(f"  REJECT: not a one-point augmentation of the order-31 parent")
                fails += 1
                continue
            tag.append(f"insertion=(c,r)={at}")
        else:
            base = meta["base"]
            ham = sum(1 for i in range(N) if perm[i] != base[i])
            tag.append(f"hamming={ham}")
            if s != 0:
                print(f"  REJECT: score {s} != 0")
                fails += 1
                continue
            if ham > meta["radius"]:
                print(f"  REJECT: Hamming distance {ham} exceeds radius {meta['radius']}")
                fails += 1
                continue
        print(f"  ACCEPT {' '.join(tag)}  perm={' '.join(map(str, perm))}")

    print()
    if meta["mode"] == "lemma":
        brute = [(costas_score(insert_extension(meta["core"], c, r)), c, r)
                 for c in range(N) for r in range(N)]
        m = min(b[0] for b in brute)
        print(f"independent brute force over all {N*N} insertions: minimum score {m}, "
              f"attained {sum(1 for b in brute if b[0] == m)} times")
        expected = "SAT" if m <= meta["max_score"] else "UNSAT"
        print(f"  therefore the instance must be {expected}")
        got = "SAT" if models else "UNSAT"
        if got != expected:
            print(f"  DISAGREEMENT: Dagster reported {got}")
            fails += 1
        else:
            print(f"  Dagster agrees: {got}")

    if a.expect:
        got = "SAT" if models else "UNSAT"
        if got != a.expect:
            print(f"VERDICT: FAIL -- expected {a.expect}, got {got}")
            return 1
    if fails:
        print(f"VERDICT: FAIL -- {fails} model(s) rejected")
        return 1
    if not models:
        print("VERDICT: UNSAT, no models to check.")
        if meta["mode"] == "lemma" and meta["max_score"] == 1:
            print("  This certifies: every order-preserving one-point augmentation")
            print("  of the order-31 parent has Costas score at least 2.")
        return 0
    print(f"VERDICT: PASS -- all {len(models)} models independently verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
