#!/usr/bin/env python3
"""Registry consistency gate. Fails the build on any drift between
proofs/STATUS.json, the files it cites, and the human-readable registries."""
import json,sys,os,re,hashlib,collections
R=os.path.join(os.path.dirname(__file__),'..')
d=json.load(open(os.path.join(R,'proofs','STATUS.json')))
bad=[]
rep,sym=d['report_claims'],d['symmetric_claims']
# derived summary
t1=collections.Counter(c['tier'] for c in rep); t2=collections.Counter(c['evidence'] for c in sym)
s=d['summary']
if s['report_claims']['total']!=len(rep) or s['report_claims']['by_tier']!=dict(t1):
    bad.append("report_claims summary not derived from list")
if s['symmetric_claims']['total']!=len(sym) or s['symmetric_claims']['by_evidence']!=dict(t2):
    bad.append("symmetric_claims summary not derived from list")
if s['registry_objects_total']!=len(rep)+len(sym): bad.append("registry_objects_total wrong")
# duplicate ids across BOTH lists
ids=[c['id'] for c in rep]+[c['id'] for c in sym]
dup=[k for k,v in collections.Counter(ids).items() if v>1]
if dup: bad.append(f"duplicate ids: {dup}")
# every report claim in INVENTORY.md and vice versa
inv=set(re.findall(r'^\|\s*([ABC]\d+)\s*\|',open(os.path.join(R,'proofs','INVENTORY.md')).read(),re.M))
if inv and inv!={c['id'] for c in rep}:
    bad.append(f"STATUS/INVENTORY mismatch: only-inventory={sorted(inv-{c['id'] for c in rep})} only-status={sorted({c['id'] for c in rep}-inv)}")
# G6: every symmetric basis must resolve on disk, hash-match, and not point at scratch
for c in sym:
    b=c.get('basis')
    if not b: bad.append(f"{c['id']}: no basis"); continue
    if (c['evidence'].startswith('F') and not c.get('derives_from')
        and not any(e['type'] in ('certificate','release','manifest','source') for e in b)):
        bad.append(f"{c['id']}: finite claim with no certificate, source or derives_from")
    for e in b:
        p=os.path.join(R,e['path'])
        if not os.path.exists(p): bad.append(f"{c['id']}: missing basis {e['path']}"); continue
        if 'scratch' in e['path']: bad.append(f"{c['id']}: basis points into scratch/")
        if e.get('pinned_by')=='sha256' and 'sha256_16' not in e:
            bad.append(f"{c['id']}: {e['path']} claims sha256 pinning but has no hash")
        if 'sha256_16' in e:
            h=hashlib.sha256(open(p,'rb').read()).hexdigest()[:16]
            if h!=e['sha256_16']: bad.append(f"{c['id']}: {e['path']} hash drift")
        if e['type']=='report' and 'label' in e:
            if ('\\label{%s}'%e['label']) not in open(p,encoding='utf-8',errors='ignore').read():
                bad.append(f"{c['id']}: label {e['label']} not found in {e['path']}")
    # G7: F+ needs two implementation records
    if c['evidence']=='F+' and len(c.get('implementations',[]))<2:
        bad.append(f"{c['id']}: labelled F+ with fewer than two implementation records")
# G5: withdrawn count must match the human registry
md=open(os.path.join(R,'symmetric','CLAIMS.md')).read()
wsec=md.split('## Withdrawn')[1].split('\n## ')[0] if '## Withdrawn' in md else ''
nmd=len([l for l in wsec.splitlines() if re.match(r'^\|\s*W\d+\s*\|',l)]) if wsec else -1
if nmd>=0 and nmd!=len(d['withdrawn']):
    bad.append(f"withdrawn: CLAIMS.md has {nmd}, STATUS.json has {len(d['withdrawn'])}")
# documentation drift: backtick-delimited paths must resolve, either
# repo-relative or relative to the markdown file's own directory
DOCS=["README.md","symmetric/README.md","symmetric/CLAIMS.md",
      "symmetric/scratch/README.md","symmetric/z1/retired/README.md",
      "symmetric/z1/closed_cells/HISTORICAL_NOTE.md"]
checked=0
FILES={f for _,_,fs in os.walk(R) for f in fs}
for md in DOCS:
    fp=os.path.join(R,md)
    if not os.path.exists(fp): continue
    base=os.path.dirname(os.path.join(R,md))
    txt=open(fp,encoding='utf-8',errors='ignore').read()
    for ref in sorted(set(re.findall(r'`([\w./-]+\.(?:cpp|py|sh|md|tex|csv|txt|json|lean|gz|sha256))`',txt))):
        if '/' in ref:
            # asserts a location: must resolve repo-relative or file-relative
            if os.path.exists(os.path.join(R,ref)) or os.path.exists(os.path.join(base,ref)):
                checked+=1
            else:
                bad.append(f"{md}: path reference does not resolve: {ref}")
        else:
            # bare filename used in context: must exist somewhere in the tree
            if ref in FILES: checked+=1
            else: bad.append(f"{md}: names a file that no longer exists: {ref}")
    for ref in sorted(set(re.findall(r'`((?:\.\./)*(?:symmetric|proofs|report|tools)/[^`\s]*/)`',txt))):
        if os.path.exists(os.path.join(R,ref)) or os.path.exists(os.path.join(base,ref)): checked+=1
        else: bad.append(f"{md}: directory reference does not resolve: {ref}")

if bad:
    print("STATUS CHECK FAIL"); [print("  -",b) for b in bad]; sys.exit(1)
print(f"STATUS CHECK PASS: {len(rep)} report claims {dict(t1)}, "
      f"{len(sym)} symmetric {dict(t2)}, {len(d['withdrawn'])} withdrawn, "
      f"{len(d['known_gaps'])} known gaps, {checked} doc paths resolved")
