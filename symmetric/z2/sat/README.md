# Z=2 SAT models — Phase 1 draft infrastructure

Independent second implementation for the Z=2 layer. Built **concurrently** with
the production search rather than after it, because deferral is the sole reason
F+ stayed open through the whole Z=1 programme.

    python3 z2_model_gen.py 0,1,3,17 0 out/     # F, q, output dir
    python3 validate_solution.py out/ < assignment.txt

## Design decisions, and why

The source material arrived in several passes with real tensions. Resolved:

**One CNF per root, decomposed internally.** "Monolithic per root" and "true
decomposition" are not alternatives: the root is the *job unit*, the DAG inside
it is the decomposition. The valid criticism is a DAG that is a pipeline of
black-box stages.

**Conflict-graph separator, not board intervals.** The earlier note answers the
later proposal: Costas clauses connect distant coordinates densely, so a
lower/upper half cut has a large separator. Interval partitioning is kept only
as a baseline to measure against.

**Interface target = width + number of distinct satisfying interface
assignments.** A 20-variable interface realising 2^20 assignments is worse than
a 40-variable one leaving hundreds.

**REPORTING = primary edge variables only.** y_d and w_o are emitted as
**equivalences**, so the reported edge assignment determines them and the
auxiliary encoding cannot change the mathematical count.

## Independence from the C++ search

`z2_common.py` uses plain loops: no bitsets, no incremental state, no trail. It
shares with the production solver only the mathematical definitions and the
frozen root catalogue. Conflicts are generated statically and pairwise; the
production solver checks displacements incrementally on a trail. That difference
is the point.

## Measured on the first package

Root Z2-S2-f04 {0,1,3,17}, I_F=2, q=0:

    edges kept 156   dropped 222 of 378   vars 171   clauses 4,207

The seed filter removes 59% of candidate edges before the solver starts — the
"Type S is SAT-friendly" claim, visible.

## A family that generated zero clauses, and why that is not a bug

`type_s_pair_orbit_exclusion` emitted **0** clauses at this root. Checked rather
than assumed: at an I_F=0 root (F={0,1,3,7}) the same family fires **23,745**
times, e.g. edges (2,9) and (16,17). So the family is not vacuous. At the I_F=2
root the seed already drops every edge that could participate.

This is worth recording because "a filter that never fires is indistinguishable
from a filter that is not running" — and here the distinction had to be
established by running it somewhere it does fire.

## Still to build

    decomposition.json + model.dag   conflict-graph separator, emitted from the
                                     same IR as the CNF
    validate_model.py                independent clause regeneration and
                                     comparison against the parsed CNF
    Type X generator                 w_o witness variables, exactly-one orbit
    acceptance tests A-D             static audit; known-positive weakened
                                     fixture; one-node vs separator agreement;
                                     standalone solver vs Dagster
