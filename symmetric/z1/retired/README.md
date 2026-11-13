# Retired implementations

`cell3_full_costas_UNSOUND_d778ab05.cpp` — sha256 d778ab05...  DO NOT RUN.

Two independent defects, both found by external audit after I had argued from
the source that the code was correct:

1. **Same-placement collision loss.** `addPair` checks all new displacements
   against the global lag set, then inserts them all. Two equal displacements
   created by one placement both pass the check and collapse to one bit. No
   collision is reported. Detected by the popcount invariant
   `displacements == C(points,2)` failing by exactly one per transposition.
   Direction: under-prunes.

2. **Static recursive snapshot.** `static unsigned long long LS[32][2]` is shared
   by every recursion level, so a parent restores its most recent descendant's
   snapshot rather than its own. Destroys stack discipline.
   Direction: **over-prunes** — can manufacture false zeros.

I diagnosed only defect 1, and stated that the binary "cannot manufacture a false
zero". That was wrong: defect 2 can. The 13,928 / 14,602 / 15,707 node benchmark
and its zero counts are withdrawn in full.

Required pattern for any future incremental oracle here:
  - per-frame (never static) snapshot, or a reversible insertion trail;
  - a per-placement pending set, so displacements created by one placement are
    checked against each other, not just against the global state;
  - explicit insertion of the new transposition's internal pair (d, -d);
  - the popcount invariant compiled in behind a debug flag.
