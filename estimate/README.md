# Cost of an unrestricted order-32 search (Paper 9)

`costas_tree.c` is an exact column-by-column Costas search (vertical-complement symmetry only) with four modes:
`exact N`, `knuth N PROBES SEED`, `strat N DEPTH PROBES_PER_NODE SEED` and `rate N SECONDS`.
`run_estimates.sh` reproduces every figure in Paper 9; `estimate_results.json` records them.

Headline: the order-32 tree has 1.538e20 nodes (relative s.e. 0.07%, five independent estimates); at 3.71e6
nodes/s this search would take about 1.3e6 core-years. The 2011 order-29 enumeration was at least 36 times
more efficient than this search, so cost projections scaled from it describe that method, not this one.
