# A/B/C wall-time test of binary displacement arc consistency
`abc.c`: one engine, three policies (A forward checking; B + triggered binary AC; C + dynamic column order).
Columns may be placed in any order (both displacement orientations stored; midpoint condition in domains).
AC recomputes supports at every triggered node (no cache). Trigger: env ABC_TRIG_MINC (default 3),
ABC_TRIG_DEPTH (default ceil(N/2)). Modes: full | split DEPTH | run (task lines, as in campaign32).
Validated: identical solution counts to the reference search at orders 8-15, identical solution-set hashes
across A, B, C at orders 10 and 12.
Result (orders 12-14, one core): with the default trigger B is 7.4-9.8x slower than A; with the most
selective triggers 1.3-1.5x slower. Time outside AC bounds any implementation: at most 2.0x (order 13) and
1.6x (order 14) faster even if AC were free. The program's 1.25x gate is not met, and the ceiling falls with n.
