# Order-32 cost probes on a cluster node

One job, one full 104-core node, about 40 minutes.

    qsub estimate/cluster/probe.pbs         # from the repository root; set the placeholders first

What it measures, in order:

1. **Environment**: `lscpu`, compiler, governor and turbo settings where readable, mean/min/max clock
   when idle and under full load.
2. **Node rate** of `costas_tree` at order 32: one core alone, then all 104 cores at once. Converts any
   node count into core-hours and KSU on the real hardware.
3. **Order-32 tree estimate**: 8 independent Knuth runs, to confirm the VM's 1.538e20 on the cluster.
4. **Estimator validation in genuine order-32 subtrees**: 96 random depth-8 subtrees (~1e9 nodes each,
   30-minute cap) and ~96 depth-9 subtrees (~4e7 nodes) counted exactly and compared with their probe
   estimates. Paper 9's validation so far is at orders 12-16 only; this closes that gap. The summary
   reports how many subtrees hit the cap: excluding them biases towards small subtrees, so any
   non-zero count means the cap should be raised.
5. **Prefix-work profile** at depth 4 (~408,000 prefixes), and the latency analysis `latency.py`:
   wall time, efficiency and charged KSU for 104 to 104,000 workers, using the measured full-load rate.

Results land in `$COSTAS_DATA/estimate_results/probe_<jobid>/`. Please send back `summary.txt` and
`summary.json`; the rest (including the ~15 MB prefix file) is useful if anything looks odd.

Every size can be overridden with `qsub -v NAME=value`, e.g. `-v DEEP8_CAP=3600`. The same script runs
locally at tiny scale for rehearsal (see the header comments).

**What it will not tell us.** The straightforward search costs ~2e7 KSU on any hardware. The decisive
unknown for a realistic campaign is the efficiency of the 2011 enumeration method, which has not been
reproduced; these probes calibrate the conversion from nodes to KSU and latency that any method's
estimate will need.
