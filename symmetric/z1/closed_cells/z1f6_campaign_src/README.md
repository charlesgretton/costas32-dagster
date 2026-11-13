# Z=1F, f=6 campaign

Generate 728 parity-admissible roots from 13 reflection-canonical rulers and 56 opposite-parity omitted pairs per ruler.

## Build and generate roots

```bash
./build.sh
python3 make_roots.py
```

## Structural census, four workers

```bash
python3 run_campaign.py --mode structural -j 4 2>&1 | tee logs/structural.log
python3 verify.py --mode structural
```

## Full-Costas census, four workers

```bash
python3 run_campaign.py --mode full -j 4 2>&1 | tee logs/full.log
python3 verify.py --mode full
```

Use `-j 1` for one core or set `-j` to the physical-core count. Each root writes separate log and result files, so rerunning safely skips completed roots.
