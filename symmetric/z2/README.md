# Z = 2: the next finite layer

Z=1 and M_LL=0 are closed, so every remaining transpose-symmetric order-32
candidate has Z >= 2. Do not search Z >= 2 at once. Close Z = 2.

## Organising lemma — verified

For an involution h, let L(h) be the set of unordered pairs {x,y} with
|x-y| >= 16 and |h(x)-h(y)| >= 16, so Z = |L(h)|. The involution acts by
tau{x,y} = {h(x),h(y)}, and since h^2 = id every orbit has size 1 or 2. A pair is
tau-fixed exactly when both points are fixed points, or when (x,y) is itself a
transposition. Hence with I_F = far fixed-point pairs, q = transpositions of
length >= 16, and C = non-singleton orbits:

    Z = I_F + q + 2C

**Verified here**: 12,000 random involutions at n=16,20,24,32 and all 158
historical involutive Costas arrays. Zero violations. Singleton orbits are
exactly the fixed-fixed far pairs plus the long transpositions.

## Z = 2 has exactly two structural types

    Type S:  I_F + q = 2,  C = 0     two singleton witnesses, no cross-orbit
    Type X:  I_F = q = 0,  C = 1     one cross-orbit, nothing else

And an exclusion worth its own line: **I_F + q = 1 implies Z != 2**, because
every non-singleton orbit contributes two. That removes a whole family before
any search.

## Fixed-point catalogue, derived here

Reflection-canonical Golomb rulers on {0..31} by f and I_F:

| f | I_F=0 | I_F=1 | I_F=2 | I_F>=3 | total |
|---|---|---|---|---|---|
| 0 | 1 | 0 | 0 | 0 | 1 |
| 2 | 184 | 72 | 0 | 0 | 256 |
| 4 | **2,735** | **2,573** | 3,932 | 4,347 | 13,587 |
| 6 | 0 | **13** | 481 | 30,609 | 31,103 |
| 8 | 0 | 0 | 0 | 0 | **0** |

Three cross-checks fall out, and all three hold:
* f=4, I_F=0 gives **2,735** — the Z=1T f=4 catalogue.
* f=4, I_F=1 gives **2,573** — the Z=1F f=4 catalogue.
* f=6, I_F=0 is **empty** and I_F=1 is **13** — OGR(6)=17>15, and the Z=1F f=6
  catalogue.
* f=8 has no Golomb ruler at all on 32 points.

So this census reproduces every catalogue the Z=1 programme used, as special
cases of one formula. That is the check I would want before trusting it.

## The ten feasible Z=2 cells

Omitted short lengths = f/2 + q - 1.

| label | f | I_F | q | omitted | outer roots |
|---|---|---|---|---|---|
| Z2-S0-f00 | 0 | 0 | 2 | 1 | 1 |
| Z2-S0-f02 | 2 | 0 | 2 | 2 | 184 |
| Z2-S1-f02 | 2 | 1 | 1 | 1 | 72 |
| Z2-X-f02  | 2 | 0 | 0 | 0 | 184 |
| Z2-S0-f04 | 4 | 0 | 2 | 3 | 2,735 |
| Z2-S1-f04 | 4 | 1 | 1 | 2 | 2,573 |
| Z2-S2-f04 | 4 | 2 | 0 | 1 | 3,932 |
| Z2-X-f04  | 4 | 0 | 0 | 1 | 2,735 |
| Z2-S1-f06 | 6 | 1 | 1 | 3 | 13 |
| Z2-S2-f06 | 6 | 2 | 0 | 2 | 481 |

Every other (type, f, I_F, q) combination is infeasible: negative omission
count, no ruler, or I_F >= 3.

## Parity, generalised

    sum over all transposition lengths d  =  a  (mod 2)

since each transposition (u,u+d) has endpoint sum = d (mod 2) and the board sums
to 496. With R the omitted short set and Q the selected long set, and
1+...+15 = 120 even:

    sum_{L in Q} L  =  a + sum_{r in R} r   (mod 2)

This is the root-generation condition for every Z=2 cell, and it specialises to
each of the Z=1 parity rules.

## Architecture, settled in advance

Outer root = reflection-canonical fixed-point ruler, as for Z=1T f=4. Long
lengths, long placements and omitted short sets stay internal. Type S and Type X
need separate solver modes: S forbids every cross-orbit (so the invariant is
Z == I_F + longs_placed, stricter than Z <= 2), while X must create exactly one
(so dZ in {0,2} per insertion, terminal Z == 2).

Build the independent SAT/CP-SAT reference **at the same time**, not after. F+
has been the standing gap through the whole Z=1 programme precisely because the
second implementation was always deferred.
