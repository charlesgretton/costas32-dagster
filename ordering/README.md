# Engineering the order-32 search (Paper 9, "Engineering the search")

- `fast.c`: bit-parallel candidate rows; the same tree as `estimate/costas_tree.c`, ~5x the node rate at order 32.
- `orders.c`: the same search under four column orders (left to right, outside in, middle out, fewest legal
  rows with forward checking). Non-contiguous orders need the midpoint (Ladendorf) check, included.
- `sym.c`: bit-parallel search with lex-leader pruning by all eight symmetries of the square; modes
  `exact`, `rate`, `knuth`, `list`. Validated: identical class representatives to brute force at orders 4-13.
- `results_10_14.txt`, `sym_vs_fast.txt`: the measurements reported in Paper 9.

Build: `gcc -O3 -march=native -o sym sym.c -lm` (likewise for the others).
- `halflag.c`, `fast_halflag.c`: the same searches checking only lags <= floor((n-1)/2) (half-lag theorem).
  Trees are identical (orders 10-15); rate gain at order 32 is nil with symmetry pruning and ~5% without.
