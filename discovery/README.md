# Discovery, Phase A: the landscape around N32 (2026-10-21)
`landscape.c` (order 32) and `landscape_n.c` (any order; seed on stdin) compute delta_m, the number of excess
repeated displacements, for every state reachable by: one swap; two swaps; three-cycles; block reversals;
block relocations; every rearrangement of the collision kernel, and of the kernel plus one dot.

N32 (delta_m = 2): the two collisions are one parallelogram on columns 0, 1, 17, 18 (vectors (1,-1) and
(17,-5)). No state at delta_m 0, 1 or 2 in any neighbourhood (apart from the seed and symmetries); every swap,
pair of swaps, three-cycle and block relocation gives delta_m >= 6.
Control, true Costas arrays: W0 (order 31) one swap >= 10, two swaps >= 12; Welch order 30: >= 11 and >= 14.
True solutions are more isolated than N32: a golf-course landscape, so defect gives no gradient towards a
solution. Block relocations of the Welch array include 58 Costas arrays (cyclic shifts of a periodic array).
Modular index transformations g(i) = f(k i mod 33), all 20 units k, on all 8 symmetry images of N32: only
k = 1 and k = 32 (a symmetry) keep delta_m = 2; all others give 19-42.
With Rosic's reported exclusion of Costas arrays within Hamming distance 12 (DRAT) and 16 (program), there is
no evidence of a Costas array near N32.
