# Overlapping-window consistency for Costas arrays

Date: 2026-10-19

## Construction

A width-`w` overlapping-window model requires every consecutive block

\[
(\pi(t),\pi(t+1),\ldots,\pi(t+w-1))
\]

to satisfy the Costas displacement condition internally, while the full sequence remains a permutation.

Equivalently, it enforces displacement uniqueness only for horizontal lags

\[
1\le d\le w-1.
\]

The experiment enumerates all permutations satisfying these short-lag constraints and then checks how many leaves are genuine Costas arrays.

## Half-lag theorem

For a permutation of order `n`, it is sufficient to check lags

\[
1\le d\le \left\lfloor\frac{n-1}{2}\right\rfloor.
\]

Proof: suppose a displacement repeats at a larger lag `d`:

\[
\pi(i+d)-\pi(i)=\pi(j+d)-\pi(j),\qquad i<j.
\]

Rearranging gives

\[
\pi(j)-\pi(i)=\pi(j+d)-\pi(i+d).
\]

Thus there is also a repeated displacement at lag

\[
h=j-i.
\]

Because both length-`d` intervals fit in the order-`n` array,

\[
h\le n-d-1\le \left\lfloor\frac{n-1}{2}\right\rfloor.
\]

Hence every long-lag collision has a short-lag witness.

Therefore overlapping windows of width

\[
w_* = \left\lfloor\frac{n-1}{2}\right\rfloor+1
\]

are exactly sufficient.

For order 32,

\[
w_*=16.
\]

So an order-32 permutation is Costas iff every consecutive 16-column window is internally Costas.

## Exact enumeration results

The columns `leaves` and `Costas leaves` count complete permutations surviving the window constraints and those that are globally Costas.

| order | window width | visited nodes | leaves | Costas leaves |
|---:|---:|---:|---:|---:|
| 10 | 3 | 398,185 | 12,756 | 2,160 |
| 10 | 4 | 308,493 | 3,368 | 2,160 |
| 10 | 5 | 304,201 | 2,160 | 2,160 |
| 11 | 3 | 2,253,542 | 63,168 | 4,368 |
| 11 | 4 | 1,503,562 | 10,936 | 4,368 |
| 11 | 5 | 1,438,018 | 4,872 | 4,368 |
| 11 | 6 | 1,437,514 | 4,368 | 4,368 |
| 12 | 3 | 13,831,577 | 338,308 | 7,852 |
| 12 | 4 | 7,750,717 | 38,320 | 7,852 |
| 12 | 5 | 7,000,461 | 11,932 | 7,852 |
| 12 | 6 | 6,977,361 | 7,852 | 7,852 |
| 13 | 3 | 90,096,842 | 1,956,876 | 12,828 |
| 13 | 4 | 41,261,838 | 139,848 | 12,828 |
| 13 | 5 | 34,285,430 | 29,252 | 12,828 |
| 13 | 6 | 33,832,450 | 14,040 | 12,828 |
| 13 | 7 | 33,831,238 | 12,828 | 12,828 |

The exact threshold agrees with the theorem:

- order 10: width 5;
- order 11: width 6;
- order 12: width 6;
- order 13: width 7.

## Transfer-state compression

A purely local transfer automaton could retain only the normalised overlap of `w-1` rows. Such a state representation merges many paths at intermediate depths. For order 12 and exact width 6, for example, 2,226,052 depth-9 prefixes map to 28,280 normalised five-column suffix shapes.

That merge is not sound for the full permutation problem. Two prefixes with the same overlap can differ in:

1. rows already used outside the overlap;
2. short-lag displacement values already used by earlier windows;
3. the number and identity of available translations inside the board.

These affect legal continuations. An exact automaton must therefore augment the overlap with the global used-row mask and all previously occupied short-lag displacement masks. That augmented state is essentially the native DFS state.

The enumeration confirms this operationally: once the window width reaches the exact half-lag threshold, node counts equal the ordinary native search exactly. The overlapping-window formulation has not reduced the search tree; it has restated which lag masks are actually necessary.

## Hierarchical interpretation

The theorem supplies a genuine hierarchy:

\[
w=2,3,\ldots,w_*.
\]

Increasing `w` adds one horizontal lag class. At order 12:

- width 3 leaves 338,308 complete candidates;
- width 4 leaves 38,320;
- width 5 leaves 11,932;
- width 6 leaves exactly the 7,852 Costas arrays.

Thus the hierarchy measures precisely how much each additional lag class contributes. Its strongest mathematical conclusion is that lags above half the order are redundant.

For order 32, the only required displacement masks are lags 1 through 15. Masks for lags 16 through 31 can be removed from the native solver without changing the search.

## Practical consequence

This yields a small but exact implementation improvement:

- store and update 15 lag masks rather than 31 at order 32;
- check only prior columns within distance 15 when placing a new dot;
- infer that any collision at a longer lag would already have a short-lag witness.

This roughly halves displacement-mask storage and reduces late-node pair checking. It does not halve the search tree, and the actual wall-time gain must be benchmarked because short-lag checks already dominate conflict detection.

## Assessment

Overlapping-window consistency produces a clean theorem and a correct order-32 reformulation:

> An order-32 permutation is Costas exactly when all 17 consecutive 16-column windows are internally Costas.

But exact overlap composition requires a 15-column overlap plus global row and short-lag displacement occupancy. The resulting exact state is effectively the native search state. Therefore the method does not presently offer state compression or a new route around the order-32 frontier.

The branch should be retained for two purposes:

1. simplify and optimise the native solver using only half of the lag masks;
2. present the window hierarchy as a structural result explaining why local windows shorter than half-order are incomplete and why half-order windows are exact.

A further dynamic-programming implementation is justified only if it discovers a sound quotient of the augmented state that merges prefixes while preserving continuation sets. The current local suffix quotient is unsound.
