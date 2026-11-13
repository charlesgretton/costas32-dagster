#!/usr/bin/env python3
"""Stratified pilot sample, per RUN_PROTOCOL.md section 1.
f=0 is a deterministic singleton (diameter undefined) -- included whole, never
passed through quartile construction. f>0 sampled by fixed-point diameter
quartile. Seeded; the seed is written beside the sample."""
import csv, random, sys
regs, out = sys.argv[1], sys.argv[2]
SEED = 20261001; PER = {0: None, 2: 24, 4: 100, 6: 100}
rng = random.Random(SEED); rows = list(csv.DictReader(open(regs))); pick = []
for f, want in PER.items():
    g = [r for r in rows if int(r["f"]) == f]
    if want is None: pick += g; continue                      # f=0: all of it
    g.sort(key=lambda r: (int(r["diameter"]), r["region_id"]))
    q = [g[i*len(g)//4:(i+1)*len(g)//4] for i in range(4)]
    per = [want//4 + (1 if i < want % 4 else 0) for i in range(4)]
    for chunk, k in zip(q, per): pick += rng.sample(chunk, min(k, len(chunk)))
open(out, "w").write("\n".join(r["region_id"] for r in pick) + "\n")
open(out + ".seed", "w").write(f"{SEED}\n")
print(f"sample: {len(pick)} regions -> {out}  (seed {SEED})")
