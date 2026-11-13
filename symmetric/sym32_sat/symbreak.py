"""Reflection symmetry breaking for regions fixed by rho(i) = n-1-i.

If rho(F) = F, then pi -> rho.pi.rho maps the region R_F onto itself (Lemma 'Reflection').
With sigma = rho.pi.rho:  sigma(0) + sigma(n-1) = 2(n-1) - (pi(0) + pi(n-1)), so every
rho-orbit has a member with pi(0) + pi(n-1) <= n-1. Adding that constraint therefore
preserves non-emptiness: the region is empty with it iff it is empty without it.

Encoding: for free 0 and n-1 (if 0 is fixed then so is n-1 and the sum is n-1 already),
one binary clause  -h(0,x) | -h(n-1,y)  for every pair of permitted images with x+y > n-1.
"""
def rho_clauses(F, var, n):
    F = sorted(F)
    if F != sorted(n - 1 - x for x in F):
        raise ValueError(f"symmetry breaking needs a reflection-fixed F; {F} is not")
    if 0 in F:
        return []
    h = {(m["i"], m["j"]): v for v, m in var.items() if m["t"] == "h"}
    out = []
    for (i, x), vx in h.items():
        if i != 0: continue
        for (k, y), vy in h.items():
            if k == n - 1 and x + y > n - 1:
                out.append([-vx, -vy])
    return out
