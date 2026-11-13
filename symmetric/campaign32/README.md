# Order-32 transpose-symmetric Costas campaign (direct search)

An exhaustive direct search over every involution of order 32 for Costas arrays: a fourth, independent
determination of the result of Paper 8 (known since 1993, confirmed in 2009, re-determined by SAT in Paper 8).

## Files
- `inv32.cpp`      the search (the project's validated involution search) with `full`, `split` and `run` modes
- `run_campaign.pbs` the cluster job: build, self-test, split, run, merge
- `selftest.sh`    split-and-merge must reproduce the unsplit search exactly at orders 16-24
- `merge.py`       fail-closed merge: verdict only if every task has exactly one COMPLETE result

## Run
From this directory on your cluster. First set the site-specific placeholders in `run_campaign.pbs`
(`YOUR_PROJECT`, `YOUR_QUEUE`, `YOUR_STORAGE`) and point `COSTAS_DATA` at a scratch directory:

    qsub run_campaign.pbs

Expected: about 20 core-hours of search, 15-20 minutes on one 104-core node. The job requests 104 cores
and a 1.5-hour walltime; adjust both for your nodes.

## What the job does
1. Builds `inv32` natively and records hashes of the source, scripts and binary.
2. Self-test at orders 16, 18, 20, 22, 24: split-and-merge must reproduce the unsplit node and array counts
   exactly, and the array counts must be 40, 20, 8, 10, 0. The job stops if any check fails.
3. Splits order 32 at depth 3 into 21,727 tasks (deterministic; 934 nodes above the frontier, no arrays).
4. Runs the tasks in chunks of 25 on 104 workers. A chunk's result file appears only when the whole chunk
   has finished.
5. Merges: every task must report exactly one COMPLETE result; any reported array is re-verified as a
   permutation, an involution and a Costas array.

## Results
In `$COSTAS_DATA/campaign32_inv_n32/` (`COSTAS_DATA` defaults to `$HOME/costas32_data`):
`summary.json` (the verdict, total nodes and arrays, task-file and result-file hashes), `summary.txt`,
`progress.log`, `tasks.txt`, `results/`, and `build_<jobid>.txt`.

The expected verdict is `COMPLETE: NO transpose-symmetric Costas array`, with about 1.42e11 total nodes.
Keep `summary.json` and `progress.log`; they are the run's record.

## If the job is interrupted
Resubmit the same job. It verifies that the regenerated task list is identical, skips every finished chunk,
and runs only the rest. An `INCOMPLETE` verdict always lists what is missing in `results/missing_tasks.txt`.

## Local rehearsal
    N=20 NW=2 CHUNK=50 SELFTEST_ORDERS="16 18" CAMPAIGN_DIR=/tmp/rehearse bash run_campaign.pbs

## Disk quota
The job writes about 2 MB in about 1,800 small files. It first checks that the campaign directory accepts
writes and aborts before any search if not. Many clusters limit both space and the number of files per
project; if the campaign directory's file system is over either limit (check with your site's quota tool),
free space there, or move the campaign directory and point the job at it:

    cp -r OLD_DIR/campaign32_inv_n32 NEW_DIR/
    rm -f NEW_DIR/campaign32_inv_n32/results/*.part
    qsub -v CAMPAIGN_DIR=NEW_DIR/campaign32_inv_n32 run_campaign.pbs

Use `cp -r` rather than `cp -a`: on systems that charge files to their owning group, `cp -a` keeps the old
group and therefore the old quota. Completed chunks are kept and skipped; only the rest are run.

## Site-specific details
The released scripts carry placeholders for everything that depends on a particular cluster: project and
queue names, storage directives, and data and archive directories. The transcribed run records under
`results_181675851/` keep the scientific content (counts, hashes, timings, job number) with site paths and
account details removed. `run_campaign.pbs` was generalised in this way after the completed run; the search,
merge and self-test sources (`inv32.cpp`, `merge.py`, `selftest.sh`) are unchanged.

## After the campaign: checks and archiving (`postrun/`)
- `independent_check.py CAMPAIGN_DIR 135486910196 0` - a second parser, sharing no code with merge.py:
  one COMPLETE record per task, no unknown ids, and task nodes + prefix nodes = the expected total.
- `arraylist_check.sh` - at orders 16-22, the split pipeline's arrays must equal, as sorted lists, those of
  the independent unsplit search `symmetric/src/involution_dfs_printing.cpp`.
- `archive_campaign.sh CAMPAIGN_DIR 135486910196 0` - reruns merge.py and the independent parser, writes
  SHA256SUMS and CAMPAIGN_MANIFEST.json, and writes a hashed tarball to `$ARCHIVE_DIR` (default
  `$HOME/costas32_archive`); choose durable storage on your system.

## Licence
Code in this bundle is licensed under the Apache License, Version 2.0, and this README under CC BY 4.0;
see `LICENSE`, `LICENSE-CC-BY-4.0.md` and `LICENSING.md` at the repository root. The source files carry no
licence headers, because their hashes are bound to the completed campaign run.
