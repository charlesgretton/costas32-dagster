# Paired-column hierarchy for Costas search

Date: 2026-10-19

## Construction

Partition consecutive columns into adjacent pairs

\[
B_j=(2j,2j+1).
\]

A leaf block is represented by its ordered two-row pattern. Its vertical translation is irrelevant to all internal displacement tests, so a pair has a normalised shape determined by its signed internal difference. Two adjacent pair blocks are joined to form a four-column block; two four-column blocks form an eight-column block; and so on.

For a block of width `w`, an exact state must retain:

1. the normalised row pattern inside the block;
2. its admissible vertical-translation interval;
3. its used row set after translation;
4. every internal displacement keyed by horizontal lag;
5. for composition, enough cross-boundary information to test all displacements created between its two children.

The first experiment asks whether translation and reflection identify enough locally Costas-consistent blocks to support useful state compression.

## Exact order-12 block census

All locally Costas-consistent left-prefix blocks were enumerated exactly. `Translation shape` subtracts the block minimum row. `Translation+reflection shape` also identifies vertical reflection.

| block width | raw blocks | translation shapes | translation+reflection shapes | compression |
|---:|---:|---:|---:|---:|
| 2 | 132 | 22 | 11 | 12.00x |
| 3 | 1,260 | 320 | 160 | 7.88x |
| 4 | 10,112 | 3,492 | 1,746 | 5.79x |
| 5 | 64,000 | 28,280 | 14,140 | 4.53x |
| 6 | 304,288 | 165,260 | 82,630 | 3.68x |
| 7 | 987,664 | 641,336 | 320,668 | 3.08x |
| 8 | 2,011,880 | 1,518,364 | 759,182 | 2.65x |

## Interpretation

The leaf-pair representation is very compact: 132 absolute ordered row pairs collapse to 11 shapes after translation and reflection. But the compression decreases steadily as blocks merge. By width eight, more than three quarters of a million exact normalised shapes remain.

This is the critical issue for a hierarchy. Cross-block Costas constraints depend on the detailed pattern of every row in each child, because joining two width-`w` blocks creates `w^2` new cross displacements spread over many horizontal lags. Translation alone shifts all corresponding vertical differences, but does not make distinct child shapes equivalent.

Adjacent pair assignment itself is not a new search ordering: assigning `(0,1)`, then `(2,3)`, and so forth is the ordinary left-to-right column order grouped two decisions at a time. Its value can only come from memoising or combining equivalent block states. The census shows strong equivalence at width two, moderate equivalence at width four, and rapidly diminishing equivalence thereafter.

## Exact hierarchical join

A sound binary join of children `A` and `B` at relative vertical offset `h` is permitted only if:

1. translated row sets are disjoint;
2. internal displacement sets of `A` and `B` remain individually valid;
3. every cross displacement

\[
(j-i,\,b_j+h-a_i)
\]

is distinct from every existing displacement at the same horizontal lag and from every other new cross displacement;
4. the merged span fits inside the order-`n` row interval.

The parent is then canonicalised by translation and vertical reflection. This gives a complete exact hierarchy for widths `2,4,8,16,32`.

## Prospective gate

The next implementation should build the width-2 and width-4 state tables and join them into width eight while recording:

- number of child-state pairs considered;
- number of legal offsets;
- number of distinct canonical parent states;
- multiplicity of raw constructions per parent state;
- memory per state;
- comparison with the ordinary native frontier at the same width.

Continue only if the ratio

\[
\frac{\text{canonical hierarchical states}}{\text{ordinary locally valid prefixes}}
\]

falls with block width and is below 0.1 by widths eight or sixteen. The exact census currently gives approximately 0.377 at width four and 0.377 after vertical reflection? More directly, the raw-to-canonical compression is 5.79x at width four but only 2.65x at width eight, so the observed trend is in the wrong direction for large-scale state merging.

## Assessment

A paired-column hierarchy is mathematically sound and gives a natural divide-and-conquer representation. It is more promising than unlabelled residue counts because it retains exact displacement ownership. However, simple translation/reflection canonicalisation does not provide scalable compression: the benefit decays quickly as block width grows.

The hierarchy remains worth one tightly gated implementation of exact joins, because different raw child decompositions might merge into the same parent state more often than prefix canonicalisation alone reveals. If that does not reverse the observed trend by width eight, the method should be recorded as an exact but non-compressing re-encoding of the native search.
