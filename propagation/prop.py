"""Board consistency propagator for the Costas CSP.

Variables h_0..h_{n-1}, domains subsets of {0..n-1}.
Constraints:
  alldifferent(h_0,...,h_{n-1})
  for each d in 1..n-1: alldifferent(h_{i+d} - h_i : 0 <= i < n-d)

Levels:
  L1  arc consistency: height alldifferent GAC (Regin) only
  L2  L1 + difference-class alldifferent GAC with channelling back to heights,
      iterated to fixpoint.  This is "board-4 consistency with exact
      difference-class propagation" in its strongest practical form:
      every Costas violation is supported on <=4 columns and every such
      violation is an equality inside one difference class, so GAC on the
      difference classes is the exact 4-point condition, relaxed only by
      the decomposition into separate classes.
  L3  L2 + pairwise extension: every ordered pair of unassigned columns must
      admit a joint assignment consistent with the fixed part; values with no
      partner are pruned.  Iterated with L2.
"""
from itertools import combinations


def _max_matching(adj, nvars, nvals):
    """adj[v] = list of value-indices. Returns match_var (len nvars, -1 if none)."""
    match_var = [-1] * nvars
    match_val = [-1] * nvals

    def try_aug(v, seen):
        for u in adj[v]:
            if seen[u]:
                continue
            seen[u] = True
            if match_val[u] == -1 or try_aug(match_val[u], seen):
                match_var[v] = u
                match_val[u] = v
                return True
        return False

    cnt = 0
    for v in range(nvars):
        if try_aug(v, [False] * nvals):
            cnt += 1
    return cnt, match_var, match_val


def regin_filter(adj, nvars, nvals):
    """GAC for alldifferent (Regin 1994) on the bipartite var/value digraph.
    Nodes 0..nvars-1 are variables, nvars..nvars+nvals-1 are values.
    Matched edges are oriented var->val, unmatched val->var.
    An edge is in some maximum matching iff it is matched, or its endpoints lie
    in a common SCC, or it lies on an alternating path from a free value."""
    cnt, match_var, match_val = _max_matching(adj, nvars, nvals)
    if cnt < nvars:
        return False, None
    N = nvars + nvals
    g = [[] for _ in range(N)]
    for v in range(nvars):
        mv = match_var[v]
        g[v].append(nvars + mv)
        for u in adj[v]:
            if u != mv:
                g[nvars + u].append(v)
    # iterative Tarjan
    idx = [-1]*N; low = [0]*N; onstk = [False]*N; comp = [-1]*N
    stk = []; c = [0]; nc = [0]
    for root in range(N):
        if idx[root] != -1:
            continue
        work = [(root, 0)]
        while work:
            node, pi = work[-1]
            if pi == 0:
                idx[node] = low[node] = c[0]; c[0] += 1
                stk.append(node); onstk[node] = True
            rec = False
            for i in range(pi, len(g[node])):
                w = g[node][i]
                if idx[w] == -1:
                    work[-1] = (node, i+1); work.append((w, 0)); rec = True; break
                elif onstk[w]:
                    low[node] = min(low[node], idx[w])
            if rec:
                continue
            if low[node] == idx[node]:
                while True:
                    w = stk.pop(); onstk[w] = False; comp[w] = nc[0]
                    if w == node: break
                nc[0] += 1
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
    # nodes reachable from a free value
    reach = [False]*N
    st = [nvars+u for u in range(nvals) if match_val[u] == -1]
    for x in st: reach[x] = True
    while st:
        x = st.pop()
        for w in g[x]:
            if not reach[w]:
                reach[w] = True; st.append(w)
    kept = []
    for v in range(nvars):
        mv = match_var[v]
        s = {mv}
        for u in adj[v]:
            if u == mv: continue
            if comp[nvars+u] == comp[v] or reach[nvars+u]:
                s.add(u)
        kept.append(s)
    return True, kept


class Costas:
    def __init__(self, n, fixed=None):
        self.n = n
        self.dom = [set(range(n)) for _ in range(n)]
        if fixed:
            for c, v in fixed.items():
                self.dom[c] = {v}
        self.fixed = dict(fixed) if fixed else {}

    def _heights_gac(self):
        n = self.n
        adj = [sorted(self.dom[i]) for i in range(n)]
        if any(len(a) == 0 for a in adj):
            return False
        ok, kept = regin_filter(adj, n, n)
        if not ok:
            return False
        changed = False
        for i in range(n):
            new = {adj[i][k] for k in range(len(adj[i])) if adj[i][k] in kept[i]} if False else kept[i]
            new = set(new) & self.dom[i]
            if new != self.dom[i]:
                self.dom[i] = new
                changed = True
            if not new:
                return False
        return changed if changed else True

    def _diff_class(self, d):
        """GAC on alldifferent over {h_{i+d}-h_i}. Returns False on wipeout,
        else True; prunes height domains via channelling."""
        n = self.n
        m = n - d
        # value universe: differences in [-(n-1), n-1] \ {0}
        vals = [z for z in range(-(n - 1), n) if z != 0]
        vidx = {z: k for k, z in enumerate(vals)}
        adj = []
        supp = []  # supp[i][z] = list of (a,b) pairs realising difference z
        for i in range(m):
            s = {}
            for a in self.dom[i]:
                for b in self.dom[i + d]:
                    if a == b:
                        continue
                    s.setdefault(b - a, []).append((a, b))
            if not s:
                return False
            supp.append(s)
            adj.append(sorted(vidx[z] for z in s))
        ok, kept = regin_filter(adj, m, len(vals))
        if not ok:
            return False
        # channel back
        for i in range(m):
            allowed = {vals[k] for k in kept[i]}
            newa, newb = set(), set()
            for z in allowed:
                for (a, b) in supp[i][z]:
                    newa.add(a)
                    newb.add(b)
            self.dom[i] &= newa
            self.dom[i + d] &= newb
            if not self.dom[i] or not self.dom[i + d]:
                return False
        return True

    def propagate(self, level=2, max_iter=50):
        n = self.n
        for _ in range(max_iter):
            snapshot = [frozenset(s) for s in self.dom]
            if self._heights_gac() is False:
                return False
            if level >= 2:
                for d in range(1, n):
                    if self._diff_class(d) is False:
                        return False
            if level >= 3:
                if not self._pair_extension():
                    return False
            if [frozenset(s) for s in self.dom] == snapshot:
                break
        return True

    def _costas_ok(self, assign):
        """assign: dict col->height. Checks all displacements distinct."""
        items = sorted(assign.items())
        seen = set()
        for x in range(len(items)):
            for y in range(x + 1, len(items)):
                (i, a), (j, b) = items[x], items[y]
                if a == b:
                    return False
                lab = (j - i, b - a)
                if lab in seen:
                    return False
                seen.add(lab)
        return True

    def _pair_extension(self):
        n = self.n
        base = dict(self.fixed)
        free = [i for i in range(n) if len(self.dom[i]) > 1]
        for i, j in combinations(free, 2):
            oki, okj = set(), set()
            for a in self.dom[i]:
                for b in self.dom[j]:
                    t = dict(base)
                    t[i] = a
                    t[j] = b
                    if self._costas_ok(t):
                        oki.add(a)
                        okj.add(b)
            if not oki or not okj:
                return False
            self.dom[i] &= oki
            self.dom[j] &= okj
            if not self.dom[i] or not self.dom[j]:
                return False
        return True


def refutes(n, fixed, level=2):
    """True iff propagation proves the partial assignment has no Costas completion."""
    c = Costas(n, fixed)
    # the fixed part must itself be Costas
    if not c._costas_ok(fixed):
        return True
    return not c.propagate(level=level)
