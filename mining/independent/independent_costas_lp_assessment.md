# Independent Costas LP assessment

Date: 2026-10-19

## Scope

This assessment was built from first principles in the execution environment. It does not use the existing `mining/` repository, its sampled prefixes, its LP generator, or its pilot outputs.

## Independent enumeration

A C++ depth-first enumerator assigns columns from left to right, enforces row uniqueness, and rejects a placement immediately if it repeats an existing displacement at the same horizontal lag.

Reproduced counts:

- order 12: 7,852 arrays, 6,977,361 visited DFS nodes
- order 13: 12,828 arrays, 33,831,238 visited DFS nodes
- order 14: 17,252 arrays, 166,352,169 visited DFS nodes

## Ground truth and sampling

For each order, a prefix is labelled live iff it is a prefix of at least one independently enumerated Costas array. Random-walk prefixes assign columns consecutively and reject any immediate repeated displacement. The pilot used 10 dead and 5 live prefixes per tested depth.

## Strong LP (LP-2)

Variables:

- placement variables `x[i,r]`;
- pair-marginal variables `y[i,j,r,s]` for `i<j` and `r!=s`.

Constraints:

- each column has placement mass one;
- each row has placement mass one;
- each pair distribution has marginals equal to its two placement vectors;
- every displacement class `(j-i,s-r)` has total pair mass at most one.

Model sizes:

- n=12: 8,856 variables, 1,608 equalities, 242 displacement inequalities
- n=13: 12,337 variables, 2,054 equalities, 288 displacement inequalities
- n=14: 16,744 variables, 2,576 equalities, 338 displacement inequalities

## Results

`dead detected / dead tested`; all tested live prefixes remained LP feasible.

| n | k | k/n | weak LP | strong LP |
|---:|---:|---:|---:|---:|
| 12 | 5 | 0.417 | 0/10 | 0/10 |
| 12 | 6 | 0.500 | 0/10 | 3/10 |
| 12 | 7 | 0.583 | 6/10 | 10/10 |
| 12 | 8 | 0.667 | 9/10 | 10/10 |
| 13 | 5 | 0.385 | 0/10 | 0/10 |
| 13 | 6 | 0.462 | 0/10 | 0/10 |
| 13 | 7 | 0.538 | 2/10 | 9/10 |
| 13 | 8 | 0.615 | 8/10 | 10/10 |
| 13 | 9 | 0.692 | 10/10 | 10/10 |
| 14 | 6 | 0.429 | 0/10 | 0/10 |
| 14 | 7 | 0.500 | 1/10 | 2/10 |
| 14 | 8 | 0.571 | 4/10 | 10/10 |
| 14 | 9 | 0.643 | 10/10 | 10/10 |
| 14 | 10 | 0.714 | 10/10 | 10/10 |

Mean strong-LP solve times were approximately 0.03 to 0.10 seconds per prefix in this environment.

## Independent conclusion

The independent implementation reproduces the qualitative pilot finding:

1. The weak McCormick-style linearisation is materially weaker.
2. The full pair-marginal reformulation has a steep detection transition.
3. In this small sample, the transition location is compatible with a fraction near 0.55 to 0.58 of assigned columns.
4. No tested live Costas prefix was rejected.

This is replication evidence, not a theorem or final threshold estimate. The sample is deliberately small, uses one random-walk sampler, and covers only orders 12 to 14.

## Certificate limitation

SciPy/HiGHS in this environment reports LP infeasibility but does not expose an infeasibility dual ray through the installed interface. The threshold claim can be assessed here; exact Farkas-certificate structure requires either a solver interface exposing dual rays or a separate exact certificate reconstruction implementation.

## Files

- `enumerate.cpp`: independent Costas enumerator
- `lp_threshold.py`: independent strong LP and sampling experiment
- `compare_weak.py`: independent weak LP comparison
- `costas_12.csv`, `costas_13.csv`, `costas_14.csv`: independently enumerated catalogues
- `lp_results.json`: complete prefix and strong-LP results
- `weak_results.json`: weak-LP results
