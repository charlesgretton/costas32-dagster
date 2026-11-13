import sys, time
from prop import Costas

def sweep(n, level=2, cells=None):
    if cells is None:
        cells = [(c, v) for c in range(n) for v in range(n)]
    ref = 0; pruned_total = 0; maxpruned = 0; t0 = time.time()
    base = n * (n - 1)                      # free domain values after fixing one cell
    for (c, v) in cells:
        s = Costas(n, {c: v})
        ok = s.propagate(level=level)
        if not ok:
            ref += 1
            continue
        rem = sum(len(s.dom[i]) for i in range(n) if i != c)
        pruned_total += base - rem
        maxpruned = max(maxpruned, base - rem)
    return ref, len(cells), pruned_total, maxpruned, time.time() - t0

if __name__ == '__main__':
    level = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    print(f"level={level}")
    print(f"{'n':>3} {'cells':>6} {'refuted':>8} {'values pruned':>14} {'max/cell':>9} {'sec':>7}")
    for n in (25, 26, 27, 29):
        r, tot, pr, mx, el = sweep(n, level)
        print(f"{n:>3} {tot:>6} {r:>8} {pr:>14} {mx:>9} {el:>7.1f}")
    # order 32: the 16 reflection representatives of the central row
    cells32 = [(15, v) for v in range(16)]
    r, tot, pr, mx, el = sweep(32, level, cells32)
    print(f"{32:>3} {tot:>6} {r:>8} {pr:>14} {mx:>9} {el:>7.1f}   (central-row representatives)")
