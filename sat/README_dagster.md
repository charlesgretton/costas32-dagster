# Costas instances for Dagster

Three files:

* `gen_costas_dagster.py` — emits `<stem>.cnf`, `<stem>.dag`, `<stem>.map`
* `check_dagster_models.py` — decodes and independently verifies `dag_out.txt`
* this README — the encoding, the two decompositions, and what to check with the
  Dagster engineers

## Verify the encoder before anything else

    python3 gen_costas_dagster.py selftest

Builds the plain Costas CNF at N = 6, 7, 8 and checks **every** permutation of
0..N-1 against it. CNF satisfaction must coincide exactly with being a Costas
array. All 720 / 5040 / 40320 agree. If this fails, nothing downstream means
anything.

## The encoding

Variables `x[i][j] = 1 + N*i + j` — a dot in column i, row j.

* exactly one dot per column, exactly one per row (pairwise at-most-one)
* auxiliary `y[d][e][i]` with `x[i][j] AND x[i+d][j+e] -> y[d][e][i]`.
  Only the `->` direction is needed: `y` may be false when the conjunction is
  false, and must be true when it holds, which is all the cardinality constraint
  below requires. `e = 0` is never generated because the row constraint already
  forbids two dots in a row.
* Costas: at most one `i` per class `(d,e)`. For `--max-score 1` this is relaxed
  to at most two per class, a per-class collision flag `b[d][e]`, and at most one
  `b` true overall (Sinz sequential counter, linear size).

At N = 32: about 32k variables and 864k clauses for the score-0 form, 97k
variables and 1.02M clauses for score ≤ 1.

## Instance 1 — the lemma

    python3 gen_costas_dagster.py lemma --max-score 1 --stem lemma_k1
    mpirun -n 8 ./dagster -m 0 -o dag_out.txt lemma_k1.dag lemma_k1.cnf
    python3 check_dagster_models.py lemma_k1.map dag_out.txt --expect UNSAT

Selector variables `s[c]` and `t[r]` choose where the new column and row are
inserted into the order-31 parent C31; 1024 ternary clauses per insertion pin the
resulting array. UNSAT at `--max-score 1` certifies:

> every order-preserving one-point augmentation of C31 has Costas score at least 2.

The generator prints an independent brute-force check over all 1024 insertions
(minimum score 2, attained twice), and the checker repeats it, so Dagster's
verdict is compared against ground truth every run.

## Instance 2 — the radius-t neighbourhood

    python3 gen_costas_dagster.py neighbourhood --radius 13 --blocks 8,14,20,26 \
                                  --stem nbhd_r13

Is there an order-32 Costas array agreeing with the score-2 candidate on at least
32 − t columns? `--radius` is the difficulty dial and generalises the radius-12
exclusion. `--base` overrides the base permutation; `--n` changes the board.

## What the DAG file does

A node is **a subset of the CNF's clauses**, named by index. An edge `a->b:V`
means: solve node a; each model of a assigns the variables V; those assignments
are carried to node b and constrain it; solve b under each of them. A chain of
compatible solutions through to the terminal node is a solution to the whole
formula, which is why the terminal node owns every clause.

Parallelism comes from two places, and the second dominates:

1. sibling nodes with no ancestor relation run concurrently;
2. **fan-out** — if node a has M models, node b is instantiated M times, each an
   independent subproblem the master hands to a solving unit.

So the DAG is a work-generation structure: upstream nodes manufacture
independent jobs, downstream nodes consume them. Whether it works turns entirely
on the size of the edge variable set (the separator) and the number of upstream
models. `dagify` chooses the decomposition by min-fill on the variable
interaction graph, the classic treewidth heuristic, which is looking for small
separators.

### Why these DAGs are hand-built

The Costas primal graph is dense: every pair of columns is coupled through some
`y` variable, so there is no small separator and min-fill has nothing to find.
Running `dagify` on these CNFs will produce edges carrying most of the variable
set. Both decompositions here are therefore written by hand.

**Lemma — a two-node generator/worker split.** Node 0 owns only the 994 selector
clauses and has exactly 32 × 32 = 1024 models. The separator is 64 variables.
Each model is shipped to node 1, which owns the full CNF with `s[c]` and `t[r]`
pinned; under that assumption the template clauses become units, the array is
fully determined, and the unit is a propagate-and-conflict. Fan-out 1024, uniform
cost, tiny messages. This is the shape Dagster is designed for.

**Neighbourhood — a cumulative prefix chain.** Node k owns every clause whose
board variables lie within columns 0..b_k−1, so node k's clause set contains node
k−1's, matching the minimal example in the Dagster README. The edge carries the
`x` variables of the decided columns, and node k's models are exactly the
Costas-consistent partial assignments on those columns.

Be clear-eyed about this one: **the separator is the entire prefix, not a cut.**
Costas constraints reach back to column 0 with displacement up to 31, so nothing
can be forgotten downstream. The decomposition is therefore prefix enumeration.
It is correct and it parallelises perfectly, but it buys distribution, not
pruning. Choose `--blocks` so the first node's model count is a few times your
core count: too small starves the cluster, too large drowns the master.

## Questions for the Dagster engineers

1. Are node clause sets expected to be cumulative along a chain (node k ⊇ node
   k−1), as in the minimal example? These generators assume yes.
2. Is the edge variable list applied to the downstream solver as unit
   assumptions, or compiled into clauses by the master? Does `-g` (BDD
   assistance) change that semantics?
3. Does the master materialise all upstream models before dispatch, or stream
   them? Node 0 of the lemma has 1024 models, which is trivial; a prefix chain
   node can have billions.
4. Is `-e 1` (enumerate all solutions) safe against double counting across a
   multi-node DAG? The lemma wants `-e 0`; a census would want `-e 1`.
5. Does a checkpoint-resumed run (`-u`, `-v`, `-z`) preserve the exhaustiveness
   guarantee, and is there a completion record that distinguishes "finished" from
   "stopped"?
6. **Does Dagster emit a DRAT or LRAT proof?** The README does not mention one.
   If it does not, an UNSAT verdict is a solver claim rather than a checkable
   certificate — which matters, because certification is the main reason to use
   SAT on this problem at all rather than the dedicated backtracker.
