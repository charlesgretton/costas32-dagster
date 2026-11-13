#!/usr/bin/env python3
"""Three-arm pilot driver, v2-correct.  Replaces the retired sample_campaign.py.

Per region:   generate v2 CNF -> certified split -> discharge split gates ->
              run arms A, B, C in RANDOMISED order on byte-identical parent CNF.

  A  direct Kissat on the parent CNF
  B  Dagster mono on the same parent CNF
  D  Dagster NATIVE split: source node enumerates one coordinate's partners,
     destination solves the full CNF once per message (dag_native_split.py)

  Dagster flags come from $DAGSTER_FLAGS, default "-m 3 -e 0 -b 0 -g 1":
  TiniSAT + clause strengthener, no local search. Restart control (-p, -x, -y)
  acts on TiniSAT only; under -m 4 (MiniSat) those flags are silently ignored.

  -e 3 IS REFUSED. Under -e 3 a worker stops at the first solution per message,
  so an intermediate node never enumerates: a known-SAT order-10 region was
  reported as having no solution. Use -e 0, which enumerates every node and
  stops at the first complete solution.
  C  Kissat on each certified child (parent CNF + one unit clause).
     Arm C is a Kissat arm.  It tests whether SPLITTING helps; it does not test
     Dagster.  A Dagster-on-children arm is a separate, later question.

FAIL-CLOSED STATUS.  Kissat: exit 10 + "s SATISFIABLE" = SAT, exit 20 +
"s UNSATISFIABLE" = UNSAT, anything else UNKNOWN.  Dagster prints no status
line; an empty solution file is NOT taken as UNSAT on its own.  Dagster is
UNSAT only on exit 0 + output file present + empty, and that is labelled
UNSAT_UNPROVEN to keep it distinct from Kissat's evidence.  Every SAT model is
decoded and independently checked before it counts.

Environment:  KISSAT, DAGSTER_BIN, MPIRUN_EXTRA (e.g. "--map-by core --bind-to core"),
              COSTAS_N (default 32; smaller only for testing).
"""
from itertools import combinations
import argparse, csv, shutil, hashlib, json, os, random, shlex, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
N = int(os.environ.get("COSTAS_N", "32"))

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

def run(cmd, tmo):
    t0 = time.time(); r0 = os.times()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=tmo)
        rc, out = p.returncode, p.stdout + "\n" + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        # keep BOTH streams: Dagster's master logs each send and each finished message as
        # it happens, so a run killed at the cap still shows how far it got.
        dec = lambda x: x.decode(errors="replace") if isinstance(x, bytes) else (x or "")
        rc, out = "TIMEOUT", dec(e.stdout) + "\n" + dec(e.stderr)
    r1 = os.times()
    cpu = (r1.children_user - r0.children_user) + (r1.children_system - r0.children_system)
    return rc, out, time.time() - t0, cpu

def kissat_status(rc, out):
    if rc == 10 and "s SATISFIABLE" in out:   return "SAT"
    if rc == 20 and "s UNSATISFIABLE" in out: return "UNSAT"
    if rc == "TIMEOUT":                        return "TIMEOUT"
    # Kissat stopping at its own --time limit exits 0 with "s UNKNOWN". That is a
    # censored run at the cap, not an error. Any other exit is still UNKNOWN.
    if rc == 0 and "s UNKNOWN" in out:         return "TIMEOUT"
    return f"UNKNOWN_exit{rc}"

def kissat_stat(out, key):
    for l in out.splitlines():
        if l.startswith("c ") and key + ":" in l:
            try: return int(l.split(":")[1].split()[0])
            except Exception: pass
    return None

def decode_and_check(var, F, true):
    h = [None] * N
    for x in F: h[x] = x
    for v in true:
        m = var.get(v)
        if m and m["t"] == "edge": h[m["a"]] = m["b"]; h[m["b"]] = m["a"]
    if None in h or sorted(h) != list(range(N)): return False, "not a permutation", h
    if any(h[h[i]] != i for i in range(N)):       return False, "not an involution", h
    if sorted(i for i in range(N) if h[i] == i) != sorted(F): return False, "fixed set != F", h
    seen = set()
    for x in range(N):
        for y in range(x + 1, N):
            d = (y - x, h[y] - h[x])
            if d in seen: return False, "repeated displacement", h
            seen.add(d)
    return True, "valid Costas involution", h

def arm_kissat(cnf, cap, var, F):
    rc, out, wall, cpu = run([os.environ["KISSAT"], f"--time={cap}", cnf], cap + 60)
    st = kissat_status(rc, out); valid = None
    if st == "SAT":
        true = {int(t) for l in out.splitlines() if l.startswith("v")
                for t in l[1:].split() if t.lstrip("-").isdigit() and int(t) > 0}
        valid, why, h = decode_and_check(var, F, true)
        if not valid: st = "SAT_MODEL_INVALID"
        witness = h
    else:
        witness = None
    return dict(status=st, exit_code=rc, wall_s=wall, cpu_s=cpu, model_validated=valid,
                witness=witness,
                conflicts=kissat_stat(out, "conflicts"),
                decisions=kissat_stat(out, "decisions"),
                propagations=kissat_stat(out, "propagations"))

LOG_OUT = None    # set in main(): where raw Dagster master logs are kept

def dagster_flags():
    fl = shlex.split(os.environ.get("DAGSTER_FLAGS", "-m 3 -e 0 -b 0 -g 1"))
    if "-e" in fl and fl[fl.index("-e") + 1] == "3":
        sys.exit("REFUSED: -e 3 is unsound for UNSAT search on multi-node DAGs. Use -e 0.")
    return fl

def parse_dagster_stats(text):
    """'MASTER: Timings -- 0:1,75:...  1:729,0:0.42spm180.0%,S###...,U0.40spm...'
    -> {node: {messages, solutions, mean_s, cv_pct}}. Times are the master's clock(),
    which tracks wall time only when the master has its own core and spins (as on the cluster)."""
    import re
    line = next((l for l in text.splitlines() if "MASTER: Timings --" in l), None)
    if not line: return None
    res = {"raw": line.split("Timings --", 1)[1].strip()}
    for m in re.finditer(r"(\d+):(\d+),(\d+):([0-9.#]+)spm([0-9.#]+)%", line):
        node, msgs, sols, mean, cv = m.groups()
        res[node] = {"messages": int(msgs), "solutions": int(sols),
                     "mean_s": None if "#" in mean else float(mean),
                     "cv_pct": None if "#" in cv else float(cv)}
    return res

def parse_dagster_sends(text):
    """From 'sending message to worker W message about node N assignments: l1 l2 ...':
    per node -> sends, distinct messages, literals per message (min/max), duplicate sends.
    Distinct counts how finely the master actually decomposed the problem; a message with
    fewer literals than the interface is a merged cube; sends - distinct = duplicated or
    re-sent work (portfolio duplication or pre-empted workers)."""
    import re
    per = {}
    for l in text.splitlines():
        m = re.search(r"message about node (\d+) assignments:(.*)$", l)
        if not m: continue
        lits = tuple(sorted(int(t) for t in re.findall(r"-?\d+", m.group(2))))
        d = per.setdefault(m.group(1), {"sends": 0, "msgs": set()})
        d["sends"] += 1; d["msgs"].add(lits)
    out = {"phases": dagster_phases(text)}
    for n, d in per.items():
        ls = [len(x) for x in d["msgs"]]
        out[n] = {"sends": d["sends"], "distinct": len(d["msgs"]),
                  "duplicate_sends": d["sends"] - len(d["msgs"]),
                  "literals_min": min(ls) if ls else None, "literals_max": max(ls) if ls else None}
    return out

def dagster_phases(text):
    """Split a run's wall time using glog timestamps on the master's Master=2 lines:
      startup  = first log line -> first send to node 1 (everyone enumerating the source)
      dispatch = first node-1 send -> every distinct node-1 message sent at least once
      tail     = last first-send -> last finished message (the hardest messages, raced
                 by idle workers given duplicate copies)
    Seconds; None where a phase did not occur (e.g. a run cut off at the cap)."""
    import re
    # Time of day only, so a run past midnight would go backwards: carry a day offset
    # whenever a timestamp drops by more than 12 hours.
    day = [0, None]
    def ts(l):
        m = re.match(r"^[IWEF](?:\d{8}|\d{4}) (\d\d):(\d\d):(\d\d\.\d+)", l)
        if not m: return None
        t = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        if day[1] is not None and t < day[1] - 43200: day[0] += 86400
        day[1] = t
        return t + day[0]
    t0 = t_first = t_alldisp = t_end = None; seen = set()
    for l in text.splitlines():
        t = ts(l)
        if t is None or "Master.cpp" not in l: continue
        if t0 is None: t0 = t
        m = re.search(r"message about node 1 assignments:(.*)$", l)
        if m:
            key = tuple(sorted(int(x) for x in re.findall(r"-?\d+", m.group(1))))
            if t_first is None: t_first = t
            if key not in seen: seen.add(key); t_alldisp = t
        if "received MPI_TAG_REQUEST_FOR_ASSIGNMENT" in l: t_end = t
    r = lambda a, b: round(b - a, 1) if (a is not None and b is not None and b >= a) else None
    return {"startup_s": r(t0, t_first), "dispatch_s": r(t_first, t_alldisp), "tail_s": r(t_alldisp, t_end)}

def dagster_message_times(text):
    """Pair each 'sending message to worker W ... node K' with that worker's next event:
    'received MPI_TAG_REQUEST_FOR_ASSIGNMENT from worker W' = finished; another send to W
    first = reassigned mid-message (pre-empted; its search is lost). Per node: completed
    count, max/p90/median duration, total completed time, pre-emptions and time lost."""
    import re
    rx = re.compile(r"^[IWEF](?:\d{8}|\d{4}) (\d\d):(\d\d):(\d\d\.\d+)")
    cur = {}; done = {}; pre = {}; off = [0]; last_t = [None]
    for l in text.splitlines():
        if "Master.cpp" not in l: continue
        m = rx.match(l)
        if not m: continue
        t = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        if last_t[0] is not None and t + off[0] < last_t[0] - 43200: off[0] += 86400   # midnight
        t += off[0]; last_t[0] = t
        a = re.search(r"sending message to worker (\d+) message about node (\d+)", l)
        if a:
            w, n = a.group(1), a.group(2)
            if w in cur:                                  # reassigned before finishing
                pn, pt = cur[w]; pre.setdefault(pn, []).append(t - pt)
            cur[w] = (n, t); continue
        b = re.search(r"received MPI_TAG_REQUEST_FOR_ASSIGNMENT from worker (\d+)", l)
        if b and b.group(1) in cur:
            n, t0 = cur.pop(b.group(1)); done.setdefault(n, []).append(t - t0)
    out = {}
    for n in set(done) | set(pre):
        d = sorted(done.get(n, [])); q = lambda f: round(d[int(f*(len(d)-1))], 1) if d else None
        out[n] = {"completed": len(d), "max_s": q(1.0), "p90_s": q(0.9), "median_s": q(0.5),
                  "work_s": round(sum(d), 1), "preempted": len(pre.get(n, [])),
                  "preempted_s": round(sum(pre.get(n, [])), 1)}
    return out

def size_ranks(slot, messages, flags):
    """Workers matched to messages. Dagster never splits one message across workers:
    surplus workers duplicate a message (a portfolio) and the master's rebalancing
    pre-empts busy workers, discarding their search. -m 3 needs master + pairs."""
    m = flags[flags.index("-m") + 1] if "-m" in flags else "0"
    want = int(os.environ.get("DAGSTER_WORKERS", "0")) or messages
    if m == "3":
        k = max(1, min(want, (slot - 1) // 2)); return 1 + 2 * k, k
    k = max(1, min(want, slot - 1)); return 1 + k, k

def arm_dagster(rdir, cap, ranks, var, F, dag="dag_mono.dag", cnf="model.cnf", tag="B"):
    sols = f"{rdir}/{tag}.sols"
    if os.path.exists(sols): os.remove(sols)
    # Dagster's own per-node timing summary is printed only at verbosity 3; raise it for
    # StatisticsModule alone so nothing else from 100+ workers floods the output.
    os.environ["GLOG_vmodule"] = "StatisticsModule=3,Master=2"   # Master=2: one line per send
    cmd = (["mpirun", "-n", str(ranks), "-x", "GLOG_vmodule", "-x", "GLOG_logtostderr"] +
           shlex.split(os.environ.get("MPIRUN_EXTRA", "")) +
           [os.environ["DAGSTER_BIN"]] + dagster_flags() +
           [f"{rdir}/{dag}", f"{rdir}/{cnf}", "-o", sols])
    rc, out, wall, cpu = run(cmd, cap)
    if rc == "TIMEOUT": st = "TIMEOUT"
    elif rc != 0:       st = f"SOLVER_ERROR_exit{rc}"
    elif not os.path.exists(sols): st = "NO_OUTPUT_FILE"
    elif os.path.getsize(sols) == 0: st = "UNSAT_UNPROVEN"
    else:               st = "SAT_UNVALIDATED"
    valid = None
    if st == "SAT_UNVALIDATED":
        # every line of the output file is one reported model; check each one
        models = [l for l in open(sols) if l.strip()]
        oks = []; wit = []
        for l in models:
            true = {int(t) for t in l.split() if t.lstrip("-").isdigit() and int(t) > 0}
            ok, why, h = decode_and_check(var, F, true); oks.append(ok); wit.append(h)
        valid = bool(oks) and all(oks)
        st = "SAT" if valid else "SAT_MODEL_INVALID"
    else:
        wit = None
    stats = parse_dagster_stats(out) or {}          # end-of-run summary: absent on timeout
    stats["sends"] = parse_dagster_sends(out)        # per-send log: present even on timeout
    stats["finished_messages"] = out.count("received MPI_TAG_REQUEST_FOR_ASSIGNMENT")
    stats["message_times"] = dagster_message_times(out)
    # keep the raw master log (small, gzipped) so a parser can be fixed without a rerun
    if LOG_OUT:
        import gzip
        keep = "\n".join(l for l in out.splitlines() if "Master.cpp" in l or "Timings" in l)
        os.makedirs(LOG_OUT, exist_ok=True)
        base = os.path.basename(rdir.rstrip("/"))
        if base == "native":                       # arm D works in <region dir>/native
            base = os.path.basename(os.path.dirname(rdir.rstrip("/")))
        with gzip.open(f"{LOG_OUT}/{base}_{tag}.master.log.gz", "wt") as f:
            f.write(keep)
    return dict(status=st, exit_code=rc, wall_s=wall, cpu_s=cpu, mpi_ranks=ranks,
                allocated_s=wall * ranks, model_validated=valid, witness=wit, dagster_stats=stats)

def queue_ids(qdir):
    """Shared work queue: several drivers on one node each claim the next unclaimed region.
    DIR holds ids.txt and a counter 'next', updated under an exclusive flock on DIR/lock.
    DIR must be node-local (job-local storage), where flock is reliable. Each id is handed
    out exactly once; a driver stops when the queue is exhausted."""
    import fcntl
    ids = open(f"{qdir}/ids.txt").read().split()
    while True:
        with open(f"{qdir}/lock", "a+") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            try:
                with open(f"{qdir}/next") as g: i = int(g.read().strip() or 0)
            except FileNotFoundError:
                i = 0
            if i >= len(ids): return
            with open(f"{qdir}/next", "w") as g: g.write(str(i + 1))
        yield ids[i]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", required=True); ap.add_argument("--ids", required=True,
        help="comma list of region_ids, @file, or queue:DIR (shared work queue, see queue_ids)")
    ap.add_argument("--out", required=True); ap.add_argument("--cap", type=int, default=600)
    ap.add_argument("--ranks", type=int, default=3)
    ap.add_argument("--arms", default="A,B,C,D"); ap.add_argument("--seed", type=int, default=20261001)
    a = ap.parse_args()
    ids = (queue_ids(a.ids[6:]) if a.ids.startswith("queue:") else
           open(a.ids[1:]).read().split() if a.ids.startswith("@") else a.ids.split(","))
    dag_arms = {"B", "D"} & set(a.arms.split(","))
    if dag_arms:
        fl = dagster_flags(); m = fl[fl.index("-m") + 1] if "-m" in fl else "0"
        if m == "3" and (a.ranks < 3 or (a.ranks - 1) % 2):
            sys.exit("-m 3 needs an ODD rank count >= 3: one master plus TiniSAT/strengthener pairs")
        if a.ranks < 2:
            sys.exit("Dagster needs --ranks >= 2: one master plus at least one worker")
    rows = {r["region_id"]: r for r in csv.DictReader(open(a.regions))}
    os.makedirs(a.out, exist_ok=True)
    global LOG_OUT; LOG_OUT = f"{a.out}/dagster_logs"
    led_path = f"{a.out}/ledger.jsonl"
    rng = random.Random(a.seed)
    sys.path.insert(0, HERE)
    from gen_sym32_v2 import build, write, N as GEN_N
    from symbreak import rho_clauses
    SB = os.environ.get("SYMBREAK") == "1"   # reflection symmetry breaking (reflection-fixed F only)
    for rid in ids:
        # A case id 'R00000@0-5' is region R00000 with transposition (0 5) fixed by a unit clause.
        reg, _, case = rid.partition("@")
        r = rows[reg]; F = [int(x) for x in r["fixed_points"].split()] if r["fixed_points"] else []
        TR = [tuple(sorted(map(int, t.split("-")))) for t in case.split(",") if t]
        # Working files (CNF ~9 MB, DAGs, native-split CNF) go to node-local storage and
        # are deleted after the region. They are a deterministic function of F and the
        # generator, both pinned in the ledger; verify_cnf.py regenerates and checks.
        # KEEP_CNF=1 keeps them under --out instead.
        keep = os.environ.get("KEEP_CNF") == "1"
        wroot = a.out if keep else (os.environ.get("PBS_JOBFS") or os.environ.get("TMPDIR") or "/tmp")
        rdir = os.path.join(wroot, f"costas_{rid}_{os.getpid()}")
        Fb, nv, var, cl, rep, edge = build(F)
        if SB: cl = cl + rho_clauses(F, var, GEN_N)      # raises unless rho(F) == F
        for t in TR: cl = cl + [[edge[t]]]
        write(Fb, nv, var, cl, rep, rdir)
        parent = sha(f"{rdir}/model.cnf")
        base = dict(region_id=rid, fixed_points=F, f=len(F), diameter=r.get("diameter"),
                    symmetry_breaking=("rho" if SB else None),
                    fixed_transpositions=[list(t) for t in TR],
                    parent_cnf_sha256=parent, generator_sha256=sha(f"{HERE}/gen_sym32_v2.py"),
                    cap_s=a.cap, seed=a.seed)
        # Certified split, ONLY if arm C runs. Certified SYNTACTICALLY: the parent CNF
        # must itself contain the at-least-one clause over the split literals (coverage)
        # and every pairwise at-most-one clause (disjointness). That is exact, needs no
        # solver, and writes nothing. split_certified.py + check_split.py remain the
        # solver-based validation tools; at order 32 they write 379 files (3.1 GB) and
        # take ~2.5 min per region, which is why production does not use them.
        split = None
        if "C" in a.arms.split(","):
            free = [i for i in range(N) if i not in F]
            inc = {c: sorted(v for (x, y), v in edge.items() if c in (x, y)) for c in free}
            ci = min(free, key=lambda c: (len(inc[c]), c))      # smallest domain
            S = inc[ci]
            have = {tuple(sorted(c)) for c in cl}
            cov = tuple(sorted(S)) in have
            dis = all(tuple(sorted((-u, -v))) in have for u, v in combinations(S, 2))
            if not (cov and dis):
                with open(led_path, "a") as f:
                    f.write(json.dumps({**base, "arm": "SPLIT_GATE", "status": "GENERATOR_DEFECT",
                                        "detail": f"coverage={cov} disjoint={dis}"}) + "\n")
                print(f"{rid}: SPLIT CERTIFICATE MISSING FROM PARENT CNF -- excluded", flush=True)
                continue
            split = dict(coord=ci, literals=S, rule="smallest_domain",
                         certificate="syntactic: ALO + all pairwise AMO present in parent CNF")
        arms = [x for x in a.arms.split(",")]; rng.shuffle(arms)       # randomised order
        for arm in arms:
            if arm == "A":
                res = arm_kissat(f"{rdir}/model.cnf", a.cap, var, F)
                rec = {**base, "arm": "kissat", **res, "core_s": res["cpu_s"]}
            elif arm == "B":
                res = arm_dagster(rdir, a.cap, a.ranks, var, F)
                rec = {**base, "arm": "dagster_mono", "dagster_flags": " ".join(dagster_flags()), **res}
            elif arm == "D":
                nd = f"{rdir}/native"
                subprocess.run([sys.executable, f"{HERE}/dag_native_split.py",
                                ",".join(map(str, F)) if F else "-", nd,
                                "--depth", os.environ.get("NATIVE_DEPTH", "1")] + (["--symbreak"] if SB else [])
                               + (["--fix-trans", ",".join(f"{x}-{y}" for x, y in TR)] if TR else []),
                               check=True, capture_output=True)
                meta = json.load(open(f"{nd}/split_meta.json"))
                rk, nw = size_ranks(a.ranks, meta["expected_messages_upper"], dagster_flags())
                res = arm_dagster(nd, a.cap, rk, var, F, dag="dag_split.dag", tag="D")
                rec = {**base, "arm": "dagster_native_split", "dagster_flags": " ".join(dagster_flags()),
                       "native_cnf_sha256": sha(f"{nd}/model.cnf"),
                       "split_coords": meta["coords"], "split_domains": meta["domains"],
                       "split_coord_rules": meta.get("coord_rules"),
                       "native_depth": int(os.environ.get("NATIVE_DEPTH", "1")),
                       "messages_upper": meta["expected_messages_upper"], "dagster_workers": nw, **res}
            else:
                tmpd = os.environ.get("PBS_JOBFS") or os.environ.get("TMPDIR") or "/tmp"
                body = open(f"{rdir}/model.cnf").read().split("\n")
                hdr = next(i for i, l in enumerate(body) if l.startswith("p "))
                _, _, nvs, ncs = body[hdr].split()
                cw = []; cc = []; sts = []; cwit = None
                for idx, lit in enumerate(split["literals"]):
                    child = os.path.join(tmpd, f"{rid}_c{idx:03d}_{os.getpid()}.cnf")
                    with open(child, "w") as f:
                        f.write(f"p cnf {nvs} {int(ncs)+1}\n")
                        f.write("\n".join(body[hdr+1:]).rstrip("\n") + f"\n{lit} 0\n")
                    cdig = sha(child)
                    try:
                        res = arm_kissat(child, a.cap, var, F)
                    finally:
                        os.remove(child)                     # never accumulate child CNFs
                    cw.append(res["wall_s"]); cc.append(res["cpu_s"]); sts.append(res["status"])
                    if res["status"] == "SAT" and cwit is None: cwit = res["witness"]
                    with open(led_path, "a") as f:
                        f.write(json.dumps({**base, "arm": "split_child", "split_index": idx,
                                            "split_literal": lit, "child_cnf_sha256": cdig,
                                            **res}) + "\n")
                kids = split["literals"]
                agg = ("SAT" if "SAT" in sts else
                       "UNSAT" if all(s == "UNSAT" for s in sts) else
                       "SAT_MODEL_INVALID" if "SAT_MODEL_INVALID" in sts else "INCOMPLETE")
                rec = {**base, "arm": "kissat_split_agg", "status": agg, "witness": cwit,
                       "model_validated": (True if cwit else None),
                       "split_count": len(kids), "split_rule": split["rule"],
                       "split_coord": split["coord"], "split_certificate": split["certificate"],
                       "T_wall_ideal_parallel_s": max(cw) if cw else None,
                       "T_core_s": sum(cc), "T_wall_serial_s": sum(cw),
                       "note": "children ran serially; T_wall_ideal_parallel = max child, not measured concurrently"}
            with open(led_path, "a") as f: f.write(json.dumps(rec) + "\n")
            print(f"{rid} {rec['arm']:<18} {rec['status']:<18} "
                  f"{rec.get('wall_s', rec.get('T_core_s', 0)):8.2f}s", flush=True)
            if rec["status"] in ("SAT_MODEL_INVALID",):
                print("STOP: a SAT model failed independent validation -- defect, not discovery")
                sys.exit(4)
            if rec["status"] == "SAT":
                # a valid witness is the one artefact that must never be lost
                os.makedirs(f"{a.out}/WITNESSES", exist_ok=True)
                with open(f"{a.out}/WITNESSES/{rid}_{rec['arm']}.json", "w") as f:
                    json.dump(rec, f, indent=1)
                note = ("" if N == 32 else f" (order {N} test region: expected)")
                print(f"!! {rid}: VALID SAT WITNESS{note} saved to {a.out}/WITNESSES/", flush=True)
        if not keep:
            shutil.rmtree(rdir, ignore_errors=True)
    print(f"ledger -> {led_path}")

if __name__ == "__main__":
    main()
