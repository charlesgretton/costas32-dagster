#!/usr/bin/env python3
"""merge_rung.py -- fail-closed merge of costas_rung work units.

Usage:  python3 merge_rung.py unit_*.txt

Refuses to report an exhaustive verdict unless
  * every unit reports STATUS EXHAUSTED,
  * all units agree on order, k, mode and catalogue hash,
  * the units cover 0..nunits-1 exactly once with no gap and no duplicate,
and it re-scores every reported low-defect permutation from scratch rather than
trusting the search engine's own score.
"""
import sys, re
from collections import Counter


def costas_score(p):
    n = len(p)
    seen = set()
    s = 0
    for d in range(1, n):
        for i in range(n - d):
            z = (d, p[i + d] - p[i])
            if z in seen:
                s += 1
            seen.add(z)
    return s


def main(paths):
    hdr = None
    seen_units = {}
    totals = Counter()
    hist = Counter()
    lows = []
    statuses = []

    for path in paths:
        meta = {}
        for line in open(path):
            line = line.rstrip("\n")
            if line.startswith("RUNG "):
                m = dict(kv.split("=", 1) for kv in line[5:].split() if "=" in kv)
                meta = m
            elif line.startswith("STATUS "):
                meta["status"] = line.split()[1]
            elif line.startswith("COUNTS "):
                for kv in line[7:].split():
                    k, v = kv.split("=")
                    if k != "elapsed":
                        totals[k] += int(v)
            elif line.startswith("HIST "):
                for kv in line[5:].split():
                    k, v = kv.split(":")
                    hist[int(k)] += int(v)
            elif line.startswith("LOW "):
                lows.append((path, line))
        if not meta:
            print(f"FAIL: {path} has no RUNG header")
            return 1
        key = (meta.get("order"), meta.get("k"), meta.get("mode"), meta.get("catalogue_hash"))
        if hdr is None:
            hdr = key
        elif key != hdr:
            print(f"FAIL: {path} disagrees with earlier units on {key} vs {hdr}")
            return 1
        u, n = meta["unit"].split("/")
        if u in seen_units:
            print(f"FAIL: unit {u} appears twice ({seen_units[u]} and {path})")
            return 1
        seen_units[u] = path
        statuses.append((path, meta.get("status", "MISSING")))

    nunits = int(list(seen_units.values()) and
                 open(list(seen_units.values())[0]).read().split("unit=")[1].split("/")[1].split()[0])
    missing = [str(i) for i in range(nunits) if str(i) not in seen_units]

    print(f"order={hdr[0]}  k={hdr[1]}  mode={hdr[2]}  catalogue_hash={hdr[3]}")
    print(f"units present: {len(seen_units)} of {nunits}")
    bad = [p for p, s in statuses if s != "EXHAUSTED"]
    for p, s in statuses:
        if s != "EXHAUSTED":
            print(f"  NOT EXHAUSTED: {p} -> {s}")
    print()
    print("placements = {:,}".format(totals["placements"]))
    print("survivors  = {:,}".format(totals["survivors"]))
    print("configs    = {:,}".format(totals["configs"]))
    print("costas     = {:,}".format(totals["costas"]))
    print("histogram  =", " ".join(f"{k}:{hist[k]}" for k in sorted(hist)))
    print()

    print(f"independently rescoring {len(lows)} reported low-defect permutations")
    fails = 0
    best = None
    for path, line in lows:
        claimed = int(re.search(r"score=(\d+)", line).group(1))
        perm = [int(x) for x in line.split("perm=")[1].split()]
        if sorted(perm) != list(range(len(perm))):
            print(f"  FAIL: not a permutation in {path}: {line[:60]}")
            fails += 1
            continue
        actual = costas_score(perm)
        if actual != claimed:
            print(f"  FAIL: claimed {claimed}, recomputed {actual} in {path}")
            fails += 1
        if best is None or actual < best:
            best = actual
    print(f"  rescoring failures: {fails}")
    print(f"  minimum independently verified score: {best}")
    print()

    if missing:
        print(f"VERDICT: INCOMPLETE -- missing units {','.join(missing)}")
        return 1
    if bad:
        print("VERDICT: INCOMPLETE -- some units did not finish")
        return 1
    if fails:
        print("VERDICT: INVALID -- rescoring disagreed with the engine")
        return 1
    if totals["costas"] == 0:
        print("VERDICT: EXHAUSTIVE, NO COSTAS ARRAY FOUND")
        print("  Every order-32 permutation formed by augmenting a catalogue core")
        print("  with k dots was examined; none is a Costas array.")
        return 0
    print(f"VERDICT: EXHAUSTIVE, {totals['costas']} COSTAS ARRAY(S) FOUND -- verify immediately")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
