# Costas order-32 transpose-symmetric pilot on a cluster

`costas32_hpc.tar.gz` unpacks to a folder called **`sym32_sat`**. Every command
below is run from inside it, and every `qsub` is submitted from inside it.

    tar -xzf costas32_hpc.tar.gz && cd sym32_sat

Uses `openmpi/4.1.0` and `$HOME/local` for glog/CUDD. Set the project, queue, storage directives and
`COSTAS_DATA` for your own cluster before submitting (the scripts carry placeholders).
Edit `PROJECT`/paths in `hpc/env.sh` and the `#PBS -P` lines if yours differ.

## 0. Install Kissat (login node, ~2 minutes)

Dagster (AFSAT-Integration) is already built. Kissat has no dependencies beyond a
C compiler and libc. Build on a **login node** -- compute nodes have no internet.

    cd $HOME
    git clone https://github.com/arminbiere/kissat.git kissat-src
    cd kissat-src
    git checkout rel-4.0.4          # the version VALIDATION.json was produced with
    ./configure                     # NOT --no-proofs: keep DRAT support for later
    make -j 8
    mkdir -p $HOME/local/bin
    cp build/kissat $HOME/local/bin/kissat

`./configure` adds no CPU-specific flags, so one binary serves login nodes and
compute nodes. If the default compiler fails, run `module avail gcc`
and load a newer one before `./configure`. Optional: `make test` runs Kissat's
own test suite (slow; not required).

Check it, on the login node and then on a compute node:

    cd sym32_sat
    bash hpc/kissat_check.sh       # login node; must end KISSAT CHECK OK
    qsub hpc/kissat_check.pbs      # compute node; read costas-kchk.o<id>

The check confirms what the driver relies on: exit 10 with `s SATISFIABLE`,
exit 20 with `s UNSATISFIABLE`, and **exit 0 with `s UNKNOWN` when `--time` is
reached**, which the driver records as a censored `TIMEOUT`. A build that behaves
differently would corrupt every status in the ledger, so the check fails closed.

**Point the scripts at your Dagster.** `env.sh` defaults to
`$HOME/dagster-afsat/dagster`. If yours is elsewhere, set it once:

    export DAGSTER_DIR=/path/to/your/afsat/dagster     # the directory holding the binary

## 0b. Wall-clock patch for Dagster (optional, needed for checkpoints)

Dagster's master times checkpoints (`-v N`) and its per-message statistics with its own
CPU time, which barely advances while it waits for workers; on the cluster checkpoints then
effectively never fire. The patch switches those 12 uses to wall-clock time:

    bash hpc/patch_dagster_wallclock.sh $DAGSTER_DIR     # keeps *.orig; safe to re-run
    bash hpc/build_dagster.sh $DAGSTER_DIR               # sources env.sh, checks glog/CUDD, makes

Always build through `build_dagster.sh` (or `source hpc/env.sh` first): a bare `make` in a
fresh shell cannot find glog and CUDD in `$HOME/local`.

## 1. Prepare (login node, a few minutes). Stops on the first failure.

    cd sym32_sat
    bash hpc/prepare.sh

Checks Dagster is AFSAT-Integration (`-e 3`), builds Kissat, writes
`$COSTAS_DATA/provenance.txt`, **re-runs the frozen regression suite on the cluster** and
refuses to continue if it differs from `VALIDATION.json`, then writes the 44,947
regions and the stratified 225-region sample.

## 2. Smoke test — must end `SMOKE OK`

    qsub hpc/smoke.pbs

Order 10, one region known SAT and one known UNSAT, all three arms. Checks every
arm agrees and every SAT model passes independent validation.

## 3. Stage 1 — Arm A only (direct Kissat), whole sample

    qsub hpc/stage1_kissat.pbs        # 1 node, 104 cores, <= 2 h

Answers **Q1: is direct Kissat sufficient?** Cost ceiling 225 x 600 s = 37.5
core-hours of solving; you are charged for 104 cores x walltime used.

**Cost.** Your smoke job charged 0.04 SU for 8 cores x 10 s, i.e. about 2 SU per
core-hour. Stage 1 runs at most 3 regions per shard at a 600 s cap,
so about 30 min on 104 cores: roughly **100 SU worst case**.

**What runs per region.** Stage 1 generates the region CNF (about 1 s, 8.4 MB)
and runs Kissat. It does not build the case split -- only Arm C needs it.

## 4. Stage 2 — Arms B and C on the Stage-1 tail only

    STAGE1=$COSTAS_DATA/results/stage1_<jobid> qsub -v STAGE1 hpc/stage2_tail.pbs

Runs only the regions Kissat did not answer, or answered slower than `SLOW`
(default 120 s). Answers **Q2** (Dagster's cost), **Q3** (does splitting cut the tail),
and runs **Arm D** (Dagster's native split). If Stage 1 leaves no tail, Stage 2 exits immediately: Q1 is answered.

## Why staged, not all three arms everywhere

`RUN_PROTOCOL.md` runs all three arms on every region. Arm C launches one Kissat
per certified child (~27 per region), so its worst case is ~27 x cap per region.
Running it on regions Kissat already finishes in seconds spends most of the
allocation measuring nothing. The decision rules only need B and C where A
struggles, so this ordering asks the same three questions for far less.

## CRITICAL: never use -e 3 for this search

The XSA bundle uses `-e 3`. That is right for finding one attack and **unsound
for an UNSAT search on any multi-node DAG**. `Worker.cpp:105` moves a worker on
after the first solution per message, "assuming only one solution to each dag
node message", so an intermediate node never enumerates.

Measured, order 10, native-split DAG:

    -e 3   known-SAT region -> reported NO SOLUTION   (1 message reached node 1)
    -e 0   known-SAT region -> SAT                     (stopped after 2)
    -e 0   known-UNSAT      -> no solution             (all 7 messages = 7 partners)

`-e 0` enumerates every node and stops at the first complete solution. One-node
DAGs were unaffected only because they pass no messages. `pilot_driver.py`
refuses `-e 3`, and the smoke test fails if a known-SAT region comes back empty.

## Dagster flags, checked against the source

    -m 0  TiniSAT                              ranks >= 2
    -m 1  TiniSAT + gNovelty+ (local search)   ranks >= 2 + k
    -m 2  TiniSAT + strengthener + gNovelty+   ranks >= 3 + k
    -m 3  TiniSAT + clause strengthener        ranks ODD, >= 3  (master + pairs)
    -m 4  MiniSat                              ranks >= 2

Restarting (`SatSolver.cpp`, TiniSAT only; ignored under -m 4):

    -x 0 (default)  use -p:  -p 1 Luby (default), -p 2 restart every conflict,
                             -p 0 no full restarts
    -x N, -y D      geometric: every N conflicts consider restarting with
                    probability 1-p, then p *= D. Restarts grow MORE likely over
                    time; smaller N or D is more aggressive.

Default here: `-m 3 -e 0 -b 0 -g 1` (set in `env.sh` as `DAGSTER_FLAGS`).

## What is stored, and what is not

Each region's CNF (7-14 MB), DAG files and native-split CNF are written to
node-local `$PBS_JOBFS`, solved, and deleted. The results directory on `/scratch`
keeps only `ledger.jsonl` and, if any region is satisfiable, `WITNESSES/`.

Deleting the CNFs is safe because they are a deterministic function of the
fixed-point set and the generator, and the ledger records both digests
(`parent_cnf_sha256`, `generator_sha256`). To prove it for any results:

    COSTAS_N=32 python3 verify_cnf.py $DIR/ledger.jsonl [max_regions]

It regenerates each CNF and requires an exact digest match; it exits 1 on any
mismatch or generator difference. Set `KEEP_CNF=1` to keep the files instead.

For scale: storing them for all 44,947 regions would be about 400 GB plain or
85 GB gzipped. Kissat reads `.gz`, but Dagster does not.

**Any valid SAT model is written to `WITNESSES/<region>_<arm>.json`**, including
the full permutation. With the CNFs gone, that file is the evidence.

## How Arm C's split is certified

The split literals are one coordinate's incident edges. The certificate is
checked **syntactically** against the parent CNF: it must contain the
at-least-one clause over those literals (coverage) and every pairwise
at-most-one clause (disjointness). That is exact and needs no solver.
Each child -- the parent plus one unit clause -- is written to `$PBS_JOBFS`,
solved, and deleted, so nothing accumulates on `/scratch`.

`split_certified.py` and `check_split.py` remain as solver-based validation
tools. At order 32 they write 379 files (3.1 GB) and take about 2.5 minutes per
region, which is why production no longer uses them.

First order-32 measurement (region F={0,1,3,7}, coordinate 2, 3 s per child):
5 of 27 children refuted in 0.1 s each, 22 still open. The split is uneven.

## Arm D: the split, executed by Dagster

`dag_native_split.py`: the source node holds only one coordinate's exactly-one
clauses, so enumerating it yields one message per partner; the destination is
the full CNF, solved once per message. That is the certified partition, now
distributed by Dagster across TiniSAT workers. Coverage holds because every
model picks exactly one partner. `--depth 2` chains a second coordinate for
roughly 15x more, smaller messages.

## The restart question

    STAGE1=$COSTAS_DATA/results/stage1_<id> qsub -v STAGE1 hpc/restart_sweep.pbs

Arms B and D over seven TiniSAT settings (Luby, every-conflict, two geometric,
each with and without the strengthener), on the hardest Stage-1 regions.
Override the grid with `GRID=`. No proofs -- this measures time to complete.

Locally every setting gave the same answer on known-SAT and known-UNSAT regions
at orders 10 and 16, and the split always sent exactly one message per partner.
Speed could not be measured: order 16 solves under the ~450 ms MPI start-up
cost. That measurement is what the sweep is for.

## Status semantics (fail-closed)

    Kissat   SAT/UNSAT only with exit 10/20 AND the matching "s ..." line
    Dagster  UNSAT_UNPROVEN on exit 0 + empty output; never called UNSAT
    any SAT  decoded and independently checked; failure STOPS the run (exit 4)
    errors   reported separately -- never counted as censored

## Cluster pitfalls handled

* `--map-by core --bind-to core` (from the XSA bundle) is right when one mpirun
  owns a node. Here many shards share a node, and binding would stack every
  Dagster onto cores 0..R-1. Each shard is confined by `taskset` instead, with
  `--bind-to none` so mpirun stays inside the shard's mask.
* Dagster needs >= 2 ranks (master + worker). The driver refuses Arm B below that.
* No PBS job arrays are used; sharding happens inside one node job. If you prefer
  a site-provided parallel launcher, `run_shards.sh` is the one file to replace.

## If any region at order 32 comes back SAT

That is a candidate transpose-symmetric Costas array of order 32, and an open
question would be answered. Do not announce it: reproduce from the archived CNF,
re-validate with an independent checker, and confirm with a second solver first.


## The f=2 campaign (Dagster, depth 3, one full node per region)

All 256 f=2 regions, each closed by Kissat (tail runs) or by Dagster's depth-3 native
split. Results are UNSAT verdicts WITHOUT certificates: no checked proofs yet.

    python3 hpc/f2_campaign.py status                     # closed / open / never run
    python3 hpc/f2_campaign.py plan --exclude <in-flight lists>   # batches of 8 not yet closed
    bash hpc/submit_f2.sh 0 4                             # submit batches 000..004

A record counts only if its region id is an f=2 region and its fixed points match
regions.csv. Regions that hit the 1 h cap stay OPEN; re-plan and resubmit them later
with a larger CAP. Each batch's walltime is sized for every region hitting the cap
(8.5 h for 8 regions); typical batches finish in about 2 h, and only time used is charged.


## The f=6 and f=4 class campaigns (Kissat, one core per region, shared queue)

    python3 hpc/campaign.py --f 6 plan --batch 10400      # 31,003 regions -> 3 batches
    python3 hpc/campaign.py --f 4 plan --batch 2496       # 13,487 regions -> 6 batches
    F=6 bash hpc/submit_class.sh 0 0                      # one batch first, check, then the rest
    F=4 bash hpc/submit_class.sh 0 0
    python3 hpc/campaign.py --f 6 status                  # likewise --f 4

Each job is one full node: 104 Kissat processes draw regions from a shared queue on
node-local storage, so the node stays busy until the work runs out. Defaults: f=6 cap 600 s
and walltime 2 h; f=4 cap 3600 s and walltime 8 h. Regions that time out stay OPEN; send
them to Dagster at depth 2 (hpc/dagster_scale.pbs with IDS=, GRID='tini_d2|2|...').


## Reflection symmetry breaking (SYMBREAK=1), for regions with rho(F) = F

For a region fixed by reflection (the f=0 region, and the 16 symmetric f=2 regions), every
solution pi has a mirror rho.pi.rho in the same region, and one of the two satisfies
pi(0) + pi(31) <= 31. With SYMBREAK=1 the driver adds that constraint (about 465 binary
clauses at order 32), which roughly halves the search without changing whether the region is
empty. It is refused for any other region. Results record symmetry_breaking: "rho", and
verify_cnf.py regenerates those CNFs with the clauses. Validated against brute force at
orders 8, 10, 12 and 14 (symbreak.py). Pass it to a job with qsub -v SYMBREAK=1,...


## Case split of a region by one coordinate's partner (used for f=0, R00000)

A case id 'R00000@0-x' is region R00000 with the transposition (0 x) fixed by a unit clause.
The 31 cases x = 1..31 are exhaustive and disjoint (coordinate 0 has exactly one partner).
Inside a case the fixed transposition acts as a seed, so dag_native_split chooses split
coordinates whose pairing it refutes: no unsplit branches at depth 2 for any x. With
SYMBREAK=1 the constraint becomes pi(31) <= 31 - x. campaign.py counts R00000 CLOSED only
when all 31 cases have UNSAT verdicts, and SAT if any case is SAT. Audit with hpc/audit_all.py (below).


## Final audit and inventory (post-run)

    python3 hpc/audit_all.py         # v2 message audit of every Dagster closure -> audit_results.csv
    python3 hpc/final_inventory.py   # final_region_status.csv, f0_cases.csv, FINAL_CAMPAIGN_MANIFEST.json

audit_dagster.py v2 checks each message against the exact interface the run used (the edge
variables incident to the split coordinates recorded in its ledger), one literal per variable.
Single log: audit_dagster.py LOG --region RID --fixed "F" --depth K --coords c1,c2[,c3].
final_inventory.py counts a Dagster closure only if its audit passed. VALIDATION.json is the
frozen pre-run manifest; FINAL_CAMPAIGN_MANIFEST.json is the post-run one.
