#!/bin/sh
# Mandatory before any GPU run. Regenerates every oracle from the shipped catalogues.
cd "$(dirname "$0")/.."; T=$(mktemp -d); fail=0
chk(){ if cmp -s "$1" "$2"; then echo "  PASS  $3"; else echo "  FAIL  $3"; fail=1; fi; }
./costas_cpu_phase4 16 > $T/r16.txt 2>&1
if grep -q "nodes=160797" $T/r16.txt && grep -q "solutions=40" $T/r16.txt \
   && grep -q "traversal_fnv=0x964a2027eb628c96" $T/r16.txt
then echo "  PASS  order-16 empty-root baseline"; else echo "  FAIL  order-16 baseline"; fail=1; fi
./costas_cpu_phase4 --read-prefixes=catalogues/prefixes_N16_D1_v2.txt --write-results=$T/a.txt >/dev/null
chk oracles/results_N16_D1_v2_cpu.txt $T/a.txt "N=16 depth-1 oracle (16 units)"
./costas_cpu_phase4 --read-prefixes=catalogues/prefixes_N20_D4_v2.txt --write-results=$T/b.txt >/dev/null
chk oracles/results_N20_D4_v2_cpu.txt $T/b.txt "N=20 depth-4 oracle (37,573 units)"
./costas_cpu_phase4 --read-prefixes=catalogues/prefixes_N20_refined400_pb2.txt --write-results=$T/c.txt >/dev/null
chk oracles/results_N20_refined400_pb2_cpu.txt $T/c.txt "N=20 refined oracle (41,479 units)"
./costas_cpu_phase4 --read-prefixes=catalogues/prefixes_N20_D4_v2.txt --refine-top-b2=400 \
  --schedule=p-b2 --write-prefixes=$T/p.txt --write-results=$T/d.txt >/dev/null
chk catalogues/prefixes_N20_refined400_pb2.txt $T/p.txt "refined catalogue regenerates byte-identically"
rm -rf $T
if [ $fail -eq 0 ]; then echo "CPU VERIFY PASS"; else echo "CPU VERIFY FAIL - do not proceed to GPU"; exit 1; fi
