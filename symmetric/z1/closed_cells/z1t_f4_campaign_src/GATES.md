# Z=1T, f=4 audit gates

This is an audit-candidate campaign. Do not interpret a zero census until these gates pass.

- **T4-0 catalogue:** 5,470 raw rulers; 0 reflection-fixed; 2,735 canonical; 282 translation shapes; 141 translation/reflection shapes.
- **T4-1 fixed seed:** four fixed points, six fixed-fixed signed displacements, `Z=0`.
- **T4-2 long placements:** 297,838 endpoint-compatible `(F,L,u)` records, with the frozen per-L vector in `audit/catalogue_audit.txt`.
- **T4-3 two omissions:** 49 same-parity and 56 opposite-parity pairs; enforce `L == a+r+s (mod 2)`.
- **T4-4 spectrum:** one long transposition, thirteen short transpositions, exactly two omitted short lengths.
- **T4-5 Z oracle:** audit binary recomputes Z after every accepted placement and checks equality with the incremental counter.
- **T4-6 signed vectors:** self-test confirms `(d,d)` and `(d,-d)` occupy distinct displacement bits.
- **T4-7 rollback:** audit binary checks `popcount(used)=6+2k`, active count, Z, and displacement population at every short-recursion node.
- **T4-8 positive arm:** still required before theorem use. Add a known-solvable weakened or small-order instance proving the terminal/emission path is reachable.
- **T4-9 independent terminal checker:** still required for every survivor.

General release requirements: complete root-key coverage, fail-closed statuses, no `.tmp` or `.failed.log` files, survivor preservation, source/binary hashes, environment record, and independent result retally.
