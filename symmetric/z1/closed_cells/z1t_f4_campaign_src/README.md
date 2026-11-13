# Z=1T, f=4 final Z=1 campaign

This campaign uses 2,735 reflection-canonical four-point Golomb rulers as outer jobs. For each ruler, the solver internally enumerates a long transposition `(u,u+L)`, `16 <= L <= 31`, and two omitted short lengths `r<s`. The thirteen retained short lengths are `{1,...,15}\{r,s}`. Parity is enforced by `L = a+r+s (mod 2)`, where `a` is the number of even fixed points.

## Important status

This is an **audit candidate**, not theorem-grade evidence. Catalogue gates and internal audit assertions are included. T4-8 positive-arm testing and T4-9 an independent terminal checker remain required. A second independent solver is required for F+.

## Verified parameter space

```text
raw rulers                      5,470
reflection-fixed rulers             0
reflection-canonical rulers     2,735
translation shapes                282
translation/reflection shapes     141
(F,L,u) endpoint-compatible     297,838
same/opposite parity pairs        49/56
external-equivalent tuples   15,642,886
```

## Build and verify

```bash
python3 make_roots.py
python3 audit/verify_catalogue.py
./build.sh
ASAN_OPTIONS=detect_leaks=0 ./z1t_f4_search_audit --selftest
```

## Audit pilot

The audit binary recomputes Z and checks endpoint/displacement-population invariants. Start with one ruler, then 25 only if runtime permits:

```bash
python3 run_campaign.py --mode full --audit -j 1 --start 0 --count 1
python3 verify.py --mode full --audit --start 0 --count 1
```

## Production performance pilot

```bash
python3 run_campaign.py --mode full -j 4 --start 0 --count 25 2>&1 | tee logs/full_pilot_25.log
python3 verify.py --mode full --start 0 --count 25
```

## Full campaign, only after remaining gates

```bash
python3 run_campaign.py --mode full -j 4 2>&1 | tee logs/full_campaign.log
python3 verify.py --mode full
```

Reruns skip final root logs. `--start` and `--count` support machine-level sharding. A root summary reports pre-dynamic long candidates and parity-admissible internal records so the totals can be independently checked against 297,838 and 15,642,886.

## v2 self-test correction

The original fixture attempted `place_pair(20,21)` against fixed points `{0,1,4,10}`. That placement correctly exceeded the `Z<=1` budget before reaching the signed-vector assertion. Version 2 uses `place_pair(6,7)`, which exercises coexistence of `(1,1)` and `(1,-1)` without creating forbidden large-large pairs. Both the production and ASan/UBSan self-tests now pass.

## v3 counter semantics

Version 3 separates the independently derived premise count from the dynamically filtered search count. `parity_admissible_records` counts all endpoint-compatible parity-admissible `(F,L,u,r,s)` tuples before Costas or Z rejection of the long seed. `seed_compatible_records` counts tuples whose long seed passed those dynamic filters. See `RESULT_COLUMNS.md`.
