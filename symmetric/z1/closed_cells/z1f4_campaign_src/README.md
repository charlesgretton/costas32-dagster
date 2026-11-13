# Z=1F, f=4 campaign

This bundle enumerates 2,573 reflection-canonical four-mark Golomb rulers with exactly one fixed-fixed distance at least 16, generates the 19,405 parity-admissible `(F,r)` roots, and supports structural and full signed-Costas modes.

## Build and verify roots

```bash
python3 catalogue/generate_catalogue.py
python3 make_roots.py
python3 audit/verify_catalogue_and_roots.py
./build.sh
```

Expected:

```text
raw=5146 canonical=2573
roots=19405
PASS catalogue=2573 roots=19405
```

## Pilot benchmark

```bash
python3 run_campaign.py --mode full -j 4 --start 0 --count 100
python3 run_campaign.py --mode structural -j 4 --start 0 --count 100
```

## Full structural campaign

```bash
python3 run_campaign.py --mode structural -j 4 2>&1 | tee logs/structural.log
python3 verify.py --mode structural
```

## Full-Costas campaign

```bash
python3 run_campaign.py --mode full -j 4 2>&1 | tee logs/full.log
python3 verify.py --mode full
```

Use `-j 1` for one core or set `-j` to the number of physical cores assigned. Each root writes separate log and CSV files; reruns skip completed roots. `--start` and `--count` allow parameter-space sharding across machines.

This is a new solver adaptation. Treat it as an audit candidate until signed-vector controls, seed-population checks, sanitizer builds, structural-reference comparisons, positive survivor handling, and historical checker regression are completed.
