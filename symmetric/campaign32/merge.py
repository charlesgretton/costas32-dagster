"""Fail-closed merge for the split transpose-symmetric search.
usage: merge.py TASKFILE RESULTDIR [--expect-nodes N --expect-arrays A] [--json OUT]
Exit status 0 only if every task has exactly one COMPLETE result and every reported array verifies."""
import sys, glob, os, json, hashlib, argparse
ap=argparse.ArgumentParser(); ap.add_argument('tasks'); ap.add_argument('resultdir')
ap.add_argument('--expect-nodes',type=int); ap.add_argument('--expect-arrays',type=int); ap.add_argument('--json')
a=ap.parse_args()
def sha(path): return hashlib.sha256(open(path,'rb').read()).hexdigest()
tasks=[]; header=None
for line in open(a.tasks):
    if line.startswith('T'): tasks.append(line.split()[0])
    elif line.startswith('#SPLIT'): header=dict(kv.split('=') for kv in line.split()[1:])
problems=[]
if header is None: problems.append("task file has no #SPLIT trailer (split did not finish)")
elif int(header['tasks'])!=len(tasks): problems.append(f"task file lists {len(tasks)} tasks, trailer says {header['tasks']}")
if len(set(tasks))!=len(tasks): problems.append("duplicate task ids in task file")
n=int(header['n']) if header else None
results={}; arrays=[]; files=sorted(glob.glob(os.path.join(a.resultdir,'*.out')))
for f in files:
    for line in open(f):
        w=line.split()
        if not w: continue
        if w[0]=='RESULT':
            tid,status=w[1],w[2]
            if tid in results: problems.append(f"task {tid} reported twice")
            results[tid]=(status,dict(kv.split('=') for kv in w[3:] if '=' in kv))
        elif w[0]=='ARRAY': arrays.append((w[1],[int(x) for x in w[2].split(',')]))
taskset=set(tasks)
missing=[t for t in tasks if t not in results]
failed=[t for t,(s,_) in results.items() if s!='COMPLETE']
unknown=[t for t in results if t not in taskset]
if missing: problems.append(f"{len(missing)} tasks have no result")
if failed: problems.append(f"{len(failed)} tasks did not complete: {failed[:5]}")
if unknown: problems.append(f"{len(unknown)} results for unknown task ids")
def is_costas_involution(p):
    if sorted(p)!=list(range(len(p))): return False
    if any(p[p[i]]!=i for i in range(len(p))): return False
    seen=set()
    for i in range(len(p)):
        for j in range(i+1,len(p)):
            v=(j-i,p[j]-p[i])
            if v in seen: return False
            seen.add(v)
    return True
bad_arrays=[t for t,p in arrays if len(p)!=n or not is_costas_involution(p)]
if bad_arrays: problems.append(f"{len(bad_arrays)} reported arrays fail independent verification")
task_nodes=sum(int(r[1].get('nodes',0)) for r in results.values() if r[0]=='COMPLETE')
task_arrays=sum(int(r[1].get('arrays',0)) for r in results.values() if r[0]=='COMPLETE')
total_nodes=task_nodes+(int(header['prefix_nodes']) if header else 0)
total_arrays=task_arrays+(int(header['prefix_arrays']) if header else 0)
if task_arrays!=len(arrays): problems.append(f"array count {task_arrays} disagrees with {len(arrays)} ARRAY lines")
if a.expect_nodes is not None and total_nodes!=a.expect_nodes: problems.append(f"total nodes {total_nodes} != expected {a.expect_nodes}")
if a.expect_arrays is not None and total_arrays!=a.expect_arrays: problems.append(f"total arrays {total_arrays} != expected {a.expect_arrays}")
secs=[float(r[1].get('seconds',0)) for r in results.values() if r[0]=='COMPLETE']
summary={"order":n,"tasks":len(tasks),"completed":len(tasks)-len(missing)-len(failed),"missing":len(missing),"failed":len(failed),
 "total_nodes":total_nodes,"total_arrays":total_arrays,"arrays":[{"task":t,"permutation":p} for t,p in arrays],
 "task_seconds_total":round(sum(secs),1),"task_seconds_max":round(max(secs),2) if secs else None,
 "task_file_sha256":sha(a.tasks),"result_files":{os.path.basename(f):sha(f) for f in files},
 "verdict":("COMPLETE: "+("NO transpose-symmetric Costas array" if total_arrays==0 else f"{total_arrays} arrays found and verified")) if not problems else "INCOMPLETE",
 "problems":problems}
if a.json: json.dump(summary,open(a.json,'w'),indent=1)
print(json.dumps({k:v for k,v in summary.items() if k not in ('result_files','arrays')},indent=1))
if missing:
    open(os.path.join(a.resultdir,'missing_tasks.txt'),'w').write("\n".join(missing)+"\n")
sys.exit(0 if not problems else 1)
