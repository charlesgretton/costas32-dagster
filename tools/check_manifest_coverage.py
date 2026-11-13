#!/usr/bin/env python3
"""sha256sum -c verifies that LISTED files match. It cannot see files present in
the tree but ABSENT from the manifest. This closes that gap."""
import os,sys
R=os.path.join(os.path.dirname(__file__),'..')
EXCL={'.git','__pycache__','.DS_Store'}
# nested manifests belong to self-contained sub-bundles and are excluded from
# the top-level manifest by design; they are verified inside their own bundle
SELF={'MANIFEST.sha256','gpu_experiment/MANIFEST.sha256'}
m=set()
for l in open(os.path.join(R,'MANIFEST.sha256')):
    if l.startswith('#'): continue
    p=l.split(None,1)
    if len(p)==2: m.add(p[1].strip().lstrip('*').lstrip('./'))
tree=set()
for r,ds,fs in os.walk(R):
    ds[:]=[d for d in ds if d not in EXCL]
    for f in fs:
        rel=os.path.relpath(os.path.join(r,f),R)
        if rel not in SELF and not any(e in rel.split(os.sep) for e in EXCL): tree.add(rel)
extra=sorted(tree-m); gone=sorted(m-tree)
if extra or gone:
    print("MANIFEST COVERAGE FAIL")
    for x in extra: print(f"  - in tree but NOT in manifest: {x}")
    for x in gone:  print(f"  - in manifest but NOT in tree: {x}")
    sys.exit(1)
print(f"MANIFEST COVERAGE PASS: {len(tree)} files, none unlisted, none missing")
