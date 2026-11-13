import random, sys, time
from itertools import combinations
from prop import Costas, refutes

n = int(sys.argv[1]); SAMPLE = int(sys.argv[2]); LEVEL = int(sys.argv[3])
arrays = [tuple(map(int, l.split())) for l in open(f'cat{n}.txt')]
print(f"n={n} catalogue={len(arrays)} level={LEVEL}")

def costas_ok(assign):
    items = sorted(assign.items()); seen = set()
    for x in range(len(items)):
        for y in range(x+1, len(items)):
            (i,a),(j,b) = items[x], items[y]
            if a == b: return False
            lab = (j-i, b-a)
            if lab in seen: return False
            seen.add(lab)
    return True

# ground truth: for a config on columns S, feasible iff some array matches
def feasible(cfg):
    for p in arrays:
        if all(p[c] == v for c, v in cfg.items()):
            return True
    return False

random.seed(7)
print(f"{'s':>2} {'tested':>7} {'feas':>7} {'infeas':>7} {'refuted':>8} {'unsound':>8} {'detect%':>8} {'sec':>7}")
for s in range(1, 7):
    t0 = time.time()
    seen = set(); tested = 0; nf = 0; ni = 0; ref = 0; unsound = 0
    tries = 0
    while tested < SAMPLE and tries < SAMPLE*200:
        tries += 1
        cols = tuple(sorted(random.sample(range(n), s)))
        hs = random.sample(range(n), s)
        cfg = dict(zip(cols, hs))
        key = (cols, tuple(hs))
        if key in seen: continue
        if not costas_ok(cfg): continue
        seen.add(key); tested += 1
        f = feasible(cfg)
        r = refutes(n, cfg, level=LEVEL)
        if f: nf += 1
        else: ni += 1
        if r:
            ref += 1
            if f: unsound += 1
    pct = (100.0*ref/ni) if ni else float('nan')
    print(f"{s:>2} {tested:>7} {nf:>7} {ni:>7} {ref:>8} {unsound:>8} {pct:>8.2f} {time.time()-t0:>7.1f}")
