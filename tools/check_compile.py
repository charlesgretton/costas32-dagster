#!/usr/bin/env python3
"""Every shipped .py must compile. Hash and coverage checks cannot see a
SyntaxError -- a broken fail-closed guard shipped once past both of them."""
import os, sys, subprocess
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
bad = []; n = 0
for d, ds, fs in os.walk(R):
    ds[:] = [x for x in ds if x not in ('__pycache__', '.git')]
    for f in fs:
        if not f.endswith('.py'): continue
        p = os.path.join(d, f); n += 1
        src = open(p, encoding='utf-8', errors='replace').read()
        try: compile(src, p, 'exec')
        except SyntaxError as e: bad.append(f"{os.path.relpath(p, R)}:{e.lineno}: {e.msg}")
if bad:
    print("PY COMPILE FAIL"); [print("  -", b) for b in bad]; sys.exit(1)
print(f"PY COMPILE PASS: {n} files")
