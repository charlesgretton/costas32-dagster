# T4-8 positive arm — CLOSED

The corrected self-test exercises seeding, one successful `place_pair`,
signed-vector separation and rollback. It does **not** descend 13 levels to the
terminal-success branch, so it does not close T4-8. The production census found
no completion, so the successful path never executed there either.

Wording that was corrected: not "the terminal path is reachable" but "the
terminal path is present in the source and had not been exercised successfully
by a known-positive fixture."

## Option B: recursive known-positive fixture

`src/z1t_f4_search_posarm.cpp` lifts **only** the Z budget — the `Zp+zadd>1`
prune and the terminal `Zp!=1` test — under an environment flag. Every other
terminal condition is untouched: endpoint cover (`popcount(used)==32`), centre
sum (`sum==target_short`), the 13-length spectrum, and the recursion itself.
Completions then exist, so the recursion must find them if it can.

    POSARM=1 ./posarm 0 structural catalogue/T_f4_reflection_canonical.csv 0

## Result on ruler F0000 = {0,1,3,7}

    terminal reached and accepted                        : yes
    structural_covers incremented                        : yes
    survivor lines emitted during 60-second bounded run  : 3,498,614
    survivor lines sampled and independently checked     : 2,000
    accepted by the independent checker                  : 2,000
    rejected                                             : 0

The 3,498,614 figure is the output of a **bounded 60-second run**. It is not the
total number of weakened-mode completions, not an exhaustive count, and not a
cardinality. It is evidence that the path was exercised at scale.

Duplicate check: the first 200,000 emitted lines are 200,000 distinct, so the
emitter is duplicate-free on that prefix.

Each of the 2,000 sampled objects was independently revalidated against:
permutation, involution, fixed points equal the ruler, 14 transpositions,
exactly one long (>=16), 13 distinct short lengths, exactly two omitted, exact
32-coordinate endpoint cover, and centre sum 496 - sum(F) - (2u+L).

## Scope statement

T4-8 passes by positive-arm testing **under a weakened Z-budget specification**.
After removing only the incremental `Zp+zadd>1` prune and the terminal `Zp!=1`
rejection, the otherwise unchanged recursion reaches accepted terminal states,
increments `structural_covers`, and emits independently valid completions. This
establishes that the recursion, terminal acceptance machinery, counter and
emission path are operational when admissible completions exist.

It does **not** establish the correctness of the enforced Z=1 budget, which is
covered separately by A5/T4-5 through `recompute_Z()==Zp` in the audit build.

Naming the specification under which the path was exercised is sharper than
calling the terminal path "reachable", and is the distinction that matters:
reachable-in-source is what v1's broken selftest had.
