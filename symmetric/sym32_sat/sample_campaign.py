#!/usr/bin/env python3
"""RETIRED -- DO NOT USE.  Fails closed on purpose.

This driver invokes the v1 generator gen_sym32.py, whose encoding is VOID
(pairwise transposition conflicts only; admits non-Costas involutions), and
builds dag_splitK, which splits interface VARIABLES rather than the search
space and is NOT a partition.  It also reads meta["split_siblings"], a
v1-only field that the v2 generator does not emit.

It therefore embodied both retired defects at once, while RUN_PROTOCOL.md
described the correct procedure -- the automation contradicted the protocol.

Use RUN_PROTOCOL.md: gen_sym32_v2.py -> split_certified.py -> check_split.py,
then the three arms.  A v2-correct three-arm driver has NOT yet been written;
this file is not it.
"""
import sys
sys.stderr.write("sample_campaign.py is RETIRED: it drives the void v1 encoding and the non-partition split. Follow RUN_PROTOCOL.md.\n")
sys.exit(3)

# ---- original body retained below for provenance only; unreachable ----
#!/usr/bin/env python3
"""Stratified pilot: measure the per-region cost distribution and settle whether
the space-split DAG beats monolithic, BEFORE requesting an allocation.

Strata: f in {0,2,4,6}, and within each f by fixed-point diameter quartile, so
the sample spans the geometry rather than the first n regions of an ordering.

Each region is run twice on the SAME CNF -- monolithic and split -- so the
comparison is controlled. Both must report the same solution count or the row
is void.

usage:  sample_campaign.py regions.csv N_PER_STRATUM outdir ranks timeout_s
"""
import sys, os, csv, json, subprocess, time, random
HERE = os.path.dirname(os.path.abspath(__file__))
DAGSTER = os.environ.get("DAGSTER", "dagster")

def strata(rows, n_per):
    random.seed(20260921); out = []
    for f in (0, 2, 4, 6):
        grp = [r for r in rows if int(r["f"]) == f]
        if not grp: continue
        grp.sort(key=lambda r: int(r["diameter"]))
        q = max(1, len(grp)//4)
        for i in range(4):
            chunk = grp[i*q:(i+1)*q] if i < 3 else grp[3*q:]
            if chunk: out += random.sample(chunk, min(n_per, len(chunk)))
    return out

def run(dag, cnf, out, ranks, tmo):
    t0 = time.time()
    r = subprocess.run(["mpirun", "--allow-run-as-root", "-n", str(ranks),
                        "--oversubscribe", DAGSTER, "-m", "0", "-g", "1",
                        dag, cnf, "-o", out],
                       capture_output=True, timeout=None if tmo == 0 else tmo + 30)
    el = time.time() - t0
    sols = sum(1 for _ in open(out)) if os.path.exists(out) else None
    return r.returncode, el, sols

def main(regfile, n_per, outdir, ranks, tmo):
    rows = list(csv.DictReader(open(regfile)))
    sample = strata(rows, n_per)
    os.makedirs(outdir, exist_ok=True)
    led = open(f"{outdir}/pilot.csv", "w", newline=""); w = csv.writer(led)
    w.writerow(["region_id","f","diameter","vars","clauses","edge_vars",
                "mono_exit","mono_s","mono_sols","split_exit","split_s","split_sols",
                "agree","status"])
    for r in sample:
        rid = r["region_id"]; F = r["fixed_points"]
        d = f"{outdir}/{rid}"
        arg = F.replace(" ", ",") if F else "-"
        subprocess.run([sys.executable, f"{HERE}/gen_sym32.py", arg, d, str(ranks-1)],
                       capture_output=True)
        meta = json.load(open(f"{d}/meta.json"))
        k = meta["split_siblings"]
        try:
            me, ms, msol = run(f"{d}/dag_mono.dag", f"{d}/model.cnf", f"{d}/m.sols", ranks, tmo)
        except subprocess.TimeoutExpired: me, ms, msol = 124, tmo, None
        try:
            se, ss, ssol = run(f"{d}/dag_split{k}.dag", f"{d}/model.cnf", f"{d}/s.sols", ranks, tmo)
        except subprocess.TimeoutExpired: se, ss, ssol = 124, tmo, None
        agree = (msol == ssol) if (msol is not None and ssol is not None) else None
        st = ("BOTH_TIMEOUT" if me==124 and se==124 else
              "MONO_TIMEOUT" if me==124 else "SPLIT_TIMEOUT" if se==124 else
              "DISAGREE" if agree is False else "OK")
        w.writerow([rid, r["f"], r["diameter"], meta["vars"], meta["clauses"],
                    meta["edge_vars"], me, f"{ms:.2f}", msol, se, f"{ss:.2f}", ssol,
                    agree, st]); led.flush()
        print(f"{rid} f={r['f']} mono={ms:7.2f}s split={ss:7.2f}s {st}", flush=True)
    led.close()
    print(f"\nledger -> {outdir}/pilot.csv")

if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
