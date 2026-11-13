# Labelled residue-block assessment for Costas arrays

Date: 2026-10-19

## Question

Can the dyadic hierarchy be made useful by retaining the label of each source column, rather than reducing the displacement multiset to unlabelled residue counts?

## Representation

For a permutation `p`, retain the sequence

\[
a_i=p(i)\bmod m,
\]

so every source column remains labelled. At modulus `m`, row-balance fixes how many occurrences of each output residue must appear. For every horizontal lag `d`, the labelled sequence determines the number of pairs whose vertical displacement is in each residue class modulo `m`. Costas uniqueness gives a necessary capacity bound: this count cannot exceed the number of distinct nonzero integer vertical differences in `[-(n-1),n-1]` having that residue.

This is stronger than the previously rejected unlabelled occupancy summary because it retains which column has which output residue. It is still substantially smaller than the full permutation.

## Exact census results

### Modulus 2

The elementary residue-capacity test rejects no balanced parity assignment at orders 12--14.

Even so, the complete Costas catalogues do not realise every labelled parity sequence:

| order | balanced parity sequences | realised by Costas arrays | fraction |
|---:|---:|---:|---:|
| 12 | 924 | 738 | 79.9% |
| 13 | 1,716 | 1,262 | 73.5% |
| 14 | 3,432 | 2,656 | 77.4% |

Matched random catalogues of the same sizes realise almost every parity sequence: means 923.8, 1,715.0 and 3,409.7 respectively. Thus the missing parity sequences are Costas-specific rather than a simple catalogue-sparsity effect.

However, their lag-parity autocorrelation signatures remain diverse. Costas catalogues realise 192 of 252 possible signatures at order 12, 635 of 868 at order 13, and 678 of 890 at order 14. No single elementary parity-capacity rule explains the missing classes.

### Modulus 4

At order 12 there are 369,600 balanced labelled residue sequences. The lag-by-lag residue-capacity conditions retain 313,952, or 84.9%. The Costas catalogue realises 7,012 sequences, all satisfying the conditions.

At order 13 there are 1,201,200 balanced labelled residue sequences. Capacity retains 1,030,994, or 85.8%. The Costas catalogue realises 12,224, all satisfying the conditions.

Matched random catalogues realise more distinct mod-4 sequences than the Costas catalogues, confirming real structure, but the elementary capacity rule removes only about 14--15% of the residue-labelled space.

### Modulus 3 control

The analogous labelled-capacity test is even weaker: it retains 96.7% of balanced patterns at order 12 and 97.1% at order 13.

## Assessment

Retaining source labels rescues genuine information that was destroyed by the earlier unlabelled dyadic summaries. The parity and mod-4 projections of Costas arrays occupy a significantly restricted subset compared with matched random catalogues.

But the obvious order-independent capacity rules are weak:

- parity capacity is completely nonrestrictive at orders 12--14;
- mod-4 capacity removes only about 15%;
- the remaining excluded Costas patterns have diverse labelled autocorrelation signatures.

Therefore the labelled dyadic representation is useful as a decomposition coordinate system, but the tested constraints do not supply an early obstruction capable of changing the order-32 search.

## Next admissible experiment

A further dyadic project should not mine more scalar residue statistics. It should formulate the decomposition as an exact constraint problem over residue-labelled blocks:

1. choose the complete parity routing `i -> p(i) mod 2`;
2. refine each route by output residues modulo 4, then modulo 8;
3. retain cross-block displacement ownership, not only class counts;
4. measure whether equivalent block states merge under exact dynamic programming or decision diagrams.

The stop condition is immediate: if the number of exact interface states grows at the same rate as the native prefix frontier, the dyadic decomposition is only a re-encoding of the original search.

The current evidence does not justify claiming an order-32 pruning theorem from labelled residues.
