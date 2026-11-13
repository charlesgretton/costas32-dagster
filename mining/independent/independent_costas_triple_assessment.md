# Independent order-12 triple-consistency assessment

Date: 2026-10-19

## Formulation

This experiment extends the independent pair-marginal LP with triple variables

\[
z_{ijkrst}\in[0,1],\qquad i<j<k,
\]

for distinct rows \(r,s,t\). For every column triple, the triple distribution projects to all three existing pair distributions:

\[
\sum_t z_{ijkrst}=y_{ijrs},\qquad
\sum_s z_{ijkrst}=y_{ikrt},\qquad
\sum_r z_{ijkrst}=y_{jkst}.
\]

The pair variables retain the placement marginals and displacement-capacity constraints of LP-2.

For computational efficiency, each prefix was used to make an exactly equivalent reduced face of the full model: assigned columns have singleton row domains, and rows already occupied by the prefix are removed from unassigned columns.

## Reduced model sizes

- depth 5: 13,451 variables, comprising 54 placement, 1,137 pair and 12,260 triple variables; 11,988 equalities.
- depth 6: 6,383 variables, comprising 42 placement, 681 pair and 5,660 triple variables; 7,296 equalities.
- depth 4: 27,374 variables in the tested instances.

A raw unreduced order-12 triple formulation has 290,400 distinct-row triple variables, rather than 380,160 unrestricted row triples.

## Results

All prefixes were labelled independently from the complete order-12 Costas catalogue.

### Depth 5, 5/12 = 0.417

Across 22 distinct confirmed-dead prefixes:

- LP-2 certified 0 of 20 prefixes for which a matched LP-2 status was recorded in the new batch;
- triple consistency certified 2 of 22 dead prefixes (9.1%);
- all 9 live controls remained feasible.

The 2 positive cases show that triple consistency is strictly stronger than LP-2. However, it is far below the predeclared 90% gate needed to move effective closure to approximately 0.42n.

### Depth 6, 6/12 = 0.500

Across 12 distinct confirmed-dead prefixes:

- LP-2 certified only a subset of the matched population;
- triple consistency certified all 12 of 12 dead prefixes;
- all 5 live controls remained feasible.

Thus, in this pilot the 90% transition moved from the LP-2 region near depth 7 (0.583n) to depth 6 (0.500n), a shift of one assigned column or approximately 0.083n.

### Depth 4, 4/12 = 0.333

Two dead-prefix attempts completed before the batch time limit:

- one remained feasible after 64.9 seconds;
- one reached the per-instance 90-second limit without a verdict.

No early infeasibility was observed. The depth-4 model is substantially harder to solve in the installed floating-point LP stack.

## Independent conclusion

The triple formulation is genuinely stronger than LP-2, but the first order-12 evidence does **not** support the strong operational hypothesis that triple consistency makes dead prefixes nearly complete around 0.4n.

Instead, it moves sampled complete detection by about one depth level:

\[
0.583n\longrightarrow 0.500n
\]

at order 12. This meets a modest formulation-strength result but not the decisive transition gate. At depth 5, only 9.1% of dead prefixes were cut.

The result also remains a small random-walk sample. It is adequate to reject the proposed 90%-at-depth-5 gate, not to estimate a final transition curve precisely.

## Strategic implication

The next-level reformulation hierarchy does not appear to move the obstruction transition far enough left to alter the order-32 feasibility picture materially. Its direct use at order 32 would be impossible, and the observed depth-5 coverage is too low to motivate immediate separator-mining work as an operational route.

The sensible next step is to write up the obstruction programme, recording triple consistency as the final hierarchy test:

1. LP-2 gives a sharp, sound midpoint obstruction system.
2. Cutting-plane reasoning below the LP transition tracks native search rather than compressing it.
3. Triple consistency is strictly stronger and shifts the sampled transition by one level, but fails the predeclared early-transition gate.

The triple formulation and raw JSON results are included for independent reproduction.
