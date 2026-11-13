"""Collect the outputs of probe.pbs into summary.json and a readable report."""
import sys, os, glob, json, math, re, subprocess
out=sys.argv[1]
def kv(line): return {k:v for k,v in (t.split('=',1) for t in line.split() if '=' in t)}
def rate(f):
    L=[l for l in open(f) if l.startswith('rate')]; return float(kv(L[0])['rate']) if L else None
S={}
S['single_core_rate']=rate(os.path.join(out,'rate_single.txt'))
full=[r for r in (rate(f) for f in sorted(glob.glob(os.path.join(out,'rate_full_*.txt')))) if r]
S['full_node']={'workers':len(full),'per_core_mean':sum(full)/len(full),'per_core_min':min(full),'per_core_max':max(full),'aggregate':sum(full)}
S['full_load_slowdown']=S['single_core_rate']/S['full_node']['per_core_mean']
K=[kv(open(f).read()) for f in sorted(glob.glob(os.path.join(out,'knuth_*.txt')))]
ests=[float(k['estimate']) for k in K]; ses=[float(k['stderr']) for k in K]
w=[1/s**2 for s in ses]; m=sum(e*x for e,x in zip(ests,w))/sum(w)
S['order32_tree']={'estimates':ests,'mean':m,'stderr':(1/sum(w))**0.5,'max_single_probe_share':max(float(k.get('maxshare',0)) for k in K)}
for depth in (8,9):
    rows=[kv(l) for f in glob.glob(os.path.join(out,f'deep{depth}_*.txt')) for l in open(f) if l.startswith('deepval')]
    done=[r for r in rows if r['complete']=='1' and float(r['exact'])>0]
    z=[(float(r['exact'])-float(r['probe_estimate']))/float(r['stderr']) for r in done if float(r['stderr'])>0]
    lr=[math.log(float(r['probe_estimate'])/float(r['exact'])) for r in done if float(r['probe_estimate'])>0]
    inc=sum(r['complete']=='0' for r in rows)
    S[f'validation_depth{depth}']={'subtrees':len(rows),'counted_exactly':len(done),'incomplete_at_cap':inc,
        'warning':('subtrees cut off by the time cap are excluded, which biases the comparison towards small subtrees; raise the cap' if inc else None),
        'median_subtree_nodes':sorted(float(r['exact']) for r in done)[len(done)//2] if done else None,
        'within_2_stderr':sum(abs(x)<=2 for x in z)/len(z) if z else None,
        'mean_log_ratio_estimate_over_exact':sum(lr)/len(lr) if lr else None,
        'sum_estimate_over_sum_exact':sum(float(r['probe_estimate']) for r in done)/sum(float(r['exact']) for r in done) if done else None}
S['environment']=open(os.path.join(out,'environment.txt')).read().splitlines()[-6:]
pf=glob.glob(os.path.join(out,'prefixes_d*.txt'))
if pf:
    rate_full=S['full_node']['per_core_mean']
    lat=subprocess.run([sys.executable,os.path.join(os.path.dirname(__file__),'..','latency.py'),pf[0],str(rate_full),'2','104','1040','10400','104000'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True).stdout   # Python 3.6-compatible
    S['latency_report']=lat.splitlines()
json.dump(S,open(os.path.join(out,'summary.json'),'w'),indent=1)
print(json.dumps({k:v for k,v in S.items() if k!='latency_report'},indent=1)); print("\n".join(S.get('latency_report',[])))
