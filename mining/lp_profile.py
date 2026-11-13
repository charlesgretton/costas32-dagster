import sys, random, subprocess, time
sys.argv=[sys.argv[0], sys.argv[1], '5', '1', '1']
exec(open('lp_relax.py').read().split("t=time.time()")[0])
DEPTHS=[int(x) for x in sys.argv_depths.split(',')] if False else None
