#!/usr/bin/env python3
"""
gen_costas_dagster.py -- CNF + DAG generator for Dagster (ANU-HPC).

Two instance families, both over an N x N board (N = 32 by default):

  lemma         Does the unique order-31 parent C31 admit a one-point
                augmentation to an order-32 permutation of Costas score <= k?
                UNSAT at k = 1 proves:  every order-preserving one-point
                augmentation of C31 has score at least 2.

  neighbourhood Is there an order-32 Costas array agreeing with a given base
                permutation on at least N - t columns?  t is the difficulty
                dial and generalises the radius-t exclusion.

  selftest      Verify the encoder exhaustively at small N: every permutation
                of 0..N-1 is checked against the CNF, and CNF-satisfaction must
                coincide exactly with being a Costas array.

Outputs <stem>.cnf, <stem>.dag and <stem>.map.  The .map file records the
variable numbering so check_dagster_models.py can decode dag_out.txt.

Usage
  python3 gen_costas_dagster.py selftest
  python3 gen_costas_dagster.py lemma --max-score 1 --stem lemma_k1
  python3 gen_costas_dagster.py neighbourhood --radius 13 --blocks 8,14,20,26 \
                                --stem nbhd_r13
"""
import argparse, itertools, json, sys

# The unique order-31 Costas array reachable by one-dot augmentation of the 660
# algebraic order-30 cores (one dihedral orbit; this is one representative).
C31 = [30, 2, 8, 1, 14, 12, 7, 4, 20, 0, 18, 9, 13, 21, 10, 11, 26, 25, 6, 28,
       24, 3, 15, 5, 19, 22, 27, 29, 16, 23, 17]

# Its corner extension, the known score-2 order-32 candidate (up to D4).
BASE32 = [31] + C31


CENSUS = {6: 116, 7: 200, 8: 444, 9: 760, 10: 2160, 11: 4368, 12: 7852,
          13: 12828, 14: 17252, 15: 19612, 16: 21104, 17: 18276, 18: 15096}

# --------------------------------------------------------------------- scoring
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
    """Insert a new column at index c and a new row at index r, put the new dot
    at their intersection, and shift the core accordingly."""
    out = []
    for i in range(len(core) + 1):
        if i == c:
            out.append(r)
        else:
            v = core[i - 1] if i > c else core[i]
            out.append(v + 1 if v >= r else v)
    return out


# ----------------------------------------------------------------- CNF builder
class CNF:
    def __init__(self):
        self.clauses = []          # list of (list_of_literals, level)
        self.nv = 0

    def new_var(self):
        self.nv += 1
        return self.nv

    def add(self, lits, level):
        """level = highest board column the clause constrains; used to place the
        clause in the DAG's prefix chain.  N means 'global / terminal node'."""
        self.clauses.append((list(lits), level))


def amo_pairwise(cnf, lits, level):
    for a, b in itertools.combinations(lits, 2):
        cnf.add([-a, -b], level)


def amk_sequential(cnf, lits, k, level):
    """Sinz sequential counter: at most k of lits are true.  Linear size."""
    n = len(lits)
    if k >= n:
        return
    if k == 0:
        for l in lits:
            cnf.add([-l], level)
        return
    s = [[cnf.new_var() for _ in range(k)] for _ in range(n)]
    cnf.add([-lits[0], s[0][0]], level)
    for j in range(1, k):
        cnf.add([-s[0][j]], level)
    for i in range(1, n):
        cnf.add([-lits[i], s[i][0]], level)
        cnf.add([-s[i - 1][0], s[i][0]], level)
        for j in range(1, k):
            cnf.add([-lits[i], -s[i - 1][j - 1], s[i][j]], level)
            cnf.add([-s[i - 1][j], s[i][j]], level)
        cnf.add([-lits[i], -s[i - 1][k - 1]], level)


def build_costas(cnf, N, max_score, exact_y=False):
    """Core encoding.  Returns the x variable table."""
    x = [[cnf.new_var() for _ in range(N)] for _ in range(N)]   # x[col][row]

    for i in range(N):                       # exactly one dot per column
        cnf.add([x[i][j] for j in range(N)], i)
        amo_pairwise(cnf, [x[i][j] for j in range(N)], i)
    for j in range(N):                       # exactly one dot per row
        cnf.add([x[i][j] for i in range(N)], N)
        amo_pairwise(cnf, [x[i][j] for i in range(N)], N)

    # y[d][e][i]  <--  x[i][j] AND x[i+d][j+e]
    # Only the <-- direction is needed: y may be false when the conjunction is
    # false, and must be true when it holds, which is what the at-most-k below
    # requires.  e = 0 is excluded because the row constraint already forbids it.
    y = {}
    for d in range(1, N):
        if N - d < 2:                        # a class with one member cannot collide
            continue
        for e in list(range(-(N - 1), 0)) + list(range(1, N)):
            cls = []
            for i in range(N - d):
                v = cnf.new_var()
                y[(d, e, i)] = v
                cls.append(v)
                for j in range(max(0, -e), min(N, N - e)):
                    cnf.add([-x[i][j], -x[i + d][j + e], v], i + d)
                if exact_y:
                    # y -> the conjunction.  Columns are exactly-one, so the row
                    # of column i is unique; force the partner or forbid y.
                    for j in range(N):
                        if 0 <= j + e < N:
                            cnf.add([-v, -x[i][j], x[i + d][j + e]], i + d)
                        else:
                            cnf.add([-v, -x[i][j]], i + d)
            if max_score == 0:
                amo_pairwise(cnf, cls, N)
            else:
                amk_sequential(cnf, cls, 2, N)        # no class may hold 3
                b = cnf.new_var()                     # this class collides
                for a1, a2 in itertools.combinations(cls, 2):
                    cnf.add([-a1, -a2, b], N)
                y[("b", d, e)] = b
    if max_score >= 1:
        bs = [v for k, v in y.items() if isinstance(k, tuple) and k[0] == "b"]
        amk_sequential(cnf, bs, max_score, N)
    return x


# ------------------------------------------------------------------ DAG writer
LEVEL_SELECT = -1          # insertion-position selector clauses, solved first


def finalize(cnf):
    """Stable-sort clauses by level so that every DAG node's clause set is a
    single contiguous prefix range.  Returns a function level -> last index."""
    cnf.clauses.sort(key=lambda c: c[1])
    levels = [lv for _, lv in cnf.clauses]

    def last_index_upto(lv):
        lo, hi = 0, len(levels)
        while lo < hi:
            mid = (lo + hi) // 2
            if levels[mid] <= lv:
                lo = mid + 1
            else:
                hi = mid
        return lo - 1
    return last_index_upto


def write_dag(path, cnf, N, x, node_spec, report_upto):
    """node_spec is an ordered list of (last_level, pass_variables).  Node k owns
    every clause of level <= last_level, which is the contiguous prefix
    0..last_index_upto(last_level); the terminal node always owns all clauses."""
    upto = finalize(cnf)
    rows = []
    for lv, pv in node_spec:
        rows.append((upto(lv), pv))
    rows[-1] = (len(cnf.clauses) - 1, rows[-1][1])
    with open(path, "w") as f:
        f.write("DAG-FILE\n")
        f.write(f"NODES:{len(rows)}\n")
        f.write("GRAPH:\n")
        for k in range(len(rows) - 1):
            f.write(f"{k}->{k+1}:" + ",".join(map(str, rows[k][1])) + "\n")
        f.write("CLAUSES:\n")
        for k, (last, _) in enumerate(rows):
            f.write(f"{k}:0-{last}\n")
        f.write("REPORTING:\n")
        f.write(f"1-{report_upto}\n")
    return len(rows)


def write_cnf(path, cnf):
    with open(path, "w") as f:
        f.write(f"p cnf {cnf.nv} {len(cnf.clauses)}\n")
        for lits, _ in cnf.clauses:
            f.write(" ".join(map(str, lits)) + " 0\n")


# ---------------------------------------------------------------------- modes
def mode_lemma(a):
    N = a.n
    cnf = CNF()
    x = build_costas(cnf, N, a.max_score)
    s = [cnf.new_var() for _ in range(N)]      # new column inserted at index c
    t = [cnf.new_var() for _ in range(N)]      # new row inserted at index r
    cnf.add(s, LEVEL_SELECT); amo_pairwise(cnf, s, LEVEL_SELECT)
    cnf.add(t, LEVEL_SELECT); amo_pairwise(cnf, t, LEVEL_SELECT)
    for c in range(N):
        for r in range(N):
            ext = insert_extension(C31, c, r)
            for i in range(N):
                cnf.add([-s[c], -t[r], x[i][ext[i]]], N)
    nn = write_dag(a.stem + ".dag", cnf, N, x,
                   [(LEVEL_SELECT, s + t), (N, [])], N * N)
    write_cnf(a.stem + ".cnf", cnf)
    json.dump({"mode": "lemma", "n": N, "max_score": a.max_score,
               "x_base": 1, "s_base": s[0], "t_base": t[0],
               "core": C31, "vars": cnf.nv, "clauses": len(cnf.clauses),
               "dag_nodes": nn},
              open(a.stem + ".map", "w"), indent=1)
    brute = sorted((costas_score(insert_extension(C31, c, r)), c, r)
                   for c in range(N) for r in range(N))
    print(f"lemma: N={N} max_score={a.max_score} vars={cnf.nv} "
          f"clauses={len(cnf.clauses)} dag_nodes={nn}")
    print(f"  brute-force check over all {N*N} insertions: minimum score "
          f"{brute[0][0]} at (c,r)={brute[0][1], brute[0][2]}; "
          f"count at minimum = {sum(1 for b in brute if b[0]==brute[0][0])}")
    print(f"  expected Dagster verdict: "
          f"{'UNSAT' if brute[0][0] > a.max_score else 'SAT'}")


def mode_nbhd(a):
    N = a.n
    base = [int(v) for v in a.base.split(",")] if a.base else (BASE32 if N == 32 else list(range(N)))
    cnf = CNF()
    x = build_costas(cnf, N, 0)
    if a.radius < N:
        amk_sequential(cnf, [-x[i][base[i]] for i in range(N)], a.radius, N)
    blocks = sorted(set([int(b) for b in a.blocks.split(",")] if a.blocks else []))
    spec = [(b - 1, [x[i][j] for i in range(b) for j in range(N)]) for b in blocks]
    spec.append((N, []))
    nn = write_dag(a.stem + ".dag", cnf, N, x, spec, N * N)
    write_cnf(a.stem + ".cnf", cnf)
    json.dump({"mode": "neighbourhood", "n": N, "radius": a.radius,
               "base": base, "x_base": 1, "vars": cnf.nv,
               "clauses": len(cnf.clauses), "dag_nodes": nn},
              open(a.stem + ".map", "w"), indent=1)
    print(f"neighbourhood: N={N} radius={a.radius} vars={cnf.nv} "
          f"clauses={len(cnf.clauses)} dag_nodes={nn} blocks={blocks}")


def mode_census(a):
    N = a.n
    cnf = CNF()
    x = build_costas(cnf, N, 0, exact_y=True)
    blocks = sorted(set(int(b) for b in a.blocks.split(","))) if a.blocks else [max(2, N // 3)]
    spec = [(b - 1, [x[i][j] for i in range(b) for j in range(N)]) for b in blocks]
    spec.append((N, []))
    nn = write_dag(a.stem + ".dag", cnf, N, x, spec, N * N)
    write_cnf(a.stem + ".cnf", cnf)
    json.dump({"mode": "census", "n": N, "x_base": 1, "vars": cnf.nv,
               "clauses": len(cnf.clauses), "dag_nodes": nn,
               "expected_models": CENSUS.get(N)},
              open(a.stem + ".map", "w"), indent=1)
    print(f"census: N={N} vars={cnf.nv} clauses={len(cnf.clauses)} "
          f"dag_nodes={nn} blocks={blocks}")
    print(f"  models are in bijection with Costas arrays (y is biconditional)")
    print(f"  expected model count: {CENSUS.get(N, 'unknown')}")
    print(f"  run with -e 1 to enumerate, then check_dagster_models.py --count")


def mode_selftest(a):
    for N in (6, 7, 8):
        cnf = CNF()
        x = build_costas(cnf, N, 0)
        lit_of = {}
        for i in range(N):
            for j in range(N):
                lit_of[(i, j)] = x[i][j]
        ok = bad = 0
        for p in itertools.permutations(range(N)):
            assign = {v: False for v in range(1, cnf.nv + 1)}
            for i in range(N):
                assign[lit_of[(i, p[i])]] = True
            # y variables, numbered in the same order build_costas created them
            yv = {}
            vid = N * N
            for d in range(1, N):
                if N - d < 2:
                    continue
                for e in list(range(-(N - 1), 0)) + list(range(1, N)):
                    for i in range(N - d):
                        vid += 1
                        yv[(d, e, i)] = vid
            for (d, e, i), v in yv.items():
                assign[v] = (p[i + d] - p[i] == e)
            sat = all(any((l > 0) == assign[abs(l)] for l in lits)
                      for lits, _ in cnf.clauses)
            if sat == (costas_score(list(p)) == 0):
                ok += 1
            else:
                bad += 1
        print(f"  N={N}: {ok} permutations agree, {bad} disagree "
              f"({'PASS' if bad == 0 else 'FAIL'})")
        if bad:
            sys.exit(3)
    # exact-y: for a Costas array the auxiliary assignment must be forced,
    # so models are in bijection with arrays and #SAT is the census count
    N = 7
    cnf = CNF(); x = build_costas(cnf, N, 0, exact_y=True)
    p = next(q for q in itertools.permutations(range(N)) if costas_score(list(q)) == 0)
    assign = {v: False for v in range(1, cnf.nv + 1)}
    for i in range(N):
        assign[x[i][p[i]]] = True
    yv, vid = {}, N * N
    for d in range(1, N):
        if N - d < 2:
            continue
        for e in list(range(-(N - 1), 0)) + list(range(1, N)):
            for i in range(N - d):
                vid += 1
                yv[vid] = (p[i + d] - p[i] == e)
    for v, val in yv.items():
        assign[v] = val
    def sat():
        return all(any((l > 0) == assign[abs(l)] for l in lits)
                   for lits, _ in cnf.clauses)
    # exact-y: for a Costas array the auxiliary assignment must be forced, so
    # models are in bijection with arrays and #SAT is the census count
    N = 7
    cnf = CNF(); x = build_costas(cnf, N, 0, exact_y=True)
    p = next(q for q in itertools.permutations(range(N)) if costas_score(list(q)) == 0)
    assign = {v: False for v in range(1, cnf.nv + 1)}
    for i in range(N):
        assign[x[i][p[i]]] = True
    vid = N * N; yv = {}
    for d in range(1, N):
        if N - d < 2:
            continue
        for e in list(range(-(N - 1), 0)) + list(range(1, N)):
            for i in range(N - d):
                vid += 1
                yv[vid] = (p[i + d] - p[i] == e)
    for v, val in yv.items():
        assign[v] = val

    def sat():
        return all(any((l > 0) == assign[abs(l)] for l in lits)
                   for lits, _ in cnf.clauses)
    assert sat(), "exact-y: the intended assignment is not a model"
    flips = 0
    for v in yv:
        assign[v] = not assign[v]
        if sat():
            flips += 1
        assign[v] = not assign[v]
    print(f"  exact-y at N=7: {len(yv)} auxiliaries, {flips} of them free "
          f"({'PASS' if flips == 0 else 'FAIL'})")
    if flips:
        sys.exit(3)

    # radius constraint: exercise the Sinz counter against every permutation
    N, R = 7, 2
    base = list(next(q for q in itertools.permutations(range(N))
                     if costas_score(list(q)) == 0))
    cnf = CNF(); x = build_costas(cnf, N, 0, exact_y=True)
    nbefore = cnf.nv
    inputs = [-x[i][base[i]] for i in range(N)]
    amk_sequential(cnf, inputs, R, N)
    svars = list(range(nbefore + 1, cnf.nv + 1))
    ok = bad = 0
    for q in itertools.permutations(range(N)):
        assign = {v: False for v in range(1, cnf.nv + 1)}
        for i in range(N):
            assign[x[i][q[i]]] = True
        vid = N * N
        for d in range(1, N):
            if N - d < 2:
                continue
            for e in list(range(-(N - 1), 0)) + list(range(1, N)):
                for i in range(N - d):
                    vid += 1
                    assign[vid] = (q[i + d] - q[i] == e)
        # Sinz counter: s[i][j] = at least j+1 of the first i+1 inputs are true
        run = 0
        for i in range(N):
            if (q[i] != base[i]):
                run += 1
            for j in range(R):
                assign[svars[i * R + j]] = (run >= j + 1)
        model = all(any((l > 0) == assign[abs(l)] for l in lits)
                    for lits, _ in cnf.clauses)
        want = costas_score(list(q)) == 0 and \
               sum(1 for i in range(N) if q[i] != base[i]) <= R
        ok += (model == want); bad += (model != want)
    print(f"  radius encoding at N={N}, r={R}: {ok} permutations agree, "
          f"{bad} disagree ({'PASS' if bad == 0 else 'FAIL'})")
    if bad:
        sys.exit(3)

    # score <= 1
    for N in (6, 7):
        cnf = CNF(); x = build_costas(cnf, N, 1)
        n_le1 = sum(1 for q in itertools.permutations(range(N))
                    if costas_score(list(q)) <= 1)
        print(f"  score<=1 target at N={N}: {n_le1} permutations qualify "
              f"(encoding emits {len(cnf.clauses)} clauses)")
    print("SELFTEST PASS -- CNF models coincide exactly with Costas arrays")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("lemma");         p.add_argument("--n", type=int, default=32)
    p.add_argument("--max-score", type=int, default=1, choices=[0, 1])
    p.add_argument("--stem", default="lemma");    p.set_defaults(fn=mode_lemma)
    p = sub.add_parser("neighbourhood"); p.add_argument("--n", type=int, default=32)
    p.add_argument("--radius", type=int, default=13)
    p.add_argument("--base", default=None)
    p.add_argument("--blocks", default="8,14,20,26")
    p.add_argument("--stem", default="nbhd");     p.set_defaults(fn=mode_nbhd)
    p = sub.add_parser("census");        p.add_argument("--n", type=int, default=13)
    p.add_argument("--blocks", default=None)
    p.add_argument("--stem", default="census");   p.set_defaults(fn=mode_census)
    p = sub.add_parser("selftest");               p.set_defaults(fn=mode_selftest)
    a = ap.parse_args()
    a.fn(a)
