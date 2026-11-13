// Relation-algebra closure for the Costas network, implemented exactly as
#include <functional>
// specified for Cm(Z): atoms are signed differences e in [-(n-1), n-1],
// converse is negation, composition is the group addition table, so
// composition of edge domains is the SUMSET intersected with the board bound.
//
//   D[i][k]  <-  D[i][k]  AND  ( D[i][j] + D[j][k] )        (RA path consistency)
//   D[j][i]  =   -D[i][j]                                   (converse)
//   D[i][j]  excludes 0 for i != j                          (distinct potentials)
//   D[i][j]  subset of [-(n-1), n-1]                        (board bound)
//   {c_{i,i+d}} all different for each d                    (Costas, GAC by Regin)
//
// Domains are 63-bit masks: bit p represents e = p - (n-1).
//
// Modes:
//   cells n              every pointed cell, report refutations and pruning
//   gt n s samples       ground-truth detection at order n (needs cat<n>.txt)
//   score2               the score-2 order-32 candidate diagnostic
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <string>
#include <vector>
using namespace std;

static int N, W;                       // W = 2N-1 bit positions
static uint64_t FULL;
static uint64_t D[32][32];

static inline uint64_t revmask(uint64_t m) {   // converse: e -> -e
  uint64_t r = 0;
  while (m) { int p = __builtin_ctzll(m); m &= m - 1; r |= 1ull << (W - 1 - p); }
  return r;
}
// sumset of two difference sets, truncated to the board range
static inline uint64_t comp(uint64_t a, uint64_t b) {
  unsigned __int128 s = 0;
  while (a) { int p = __builtin_ctzll(a); a &= a - 1; s |= (unsigned __int128)b << p; }
  // bit p1+p2 of s corresponds to e = (p1+p2) - 2(N-1); we want p = e + (N-1)
  s >>= (N - 1);
  return (uint64_t)s & FULL;
}

// ---- Regin GAC for alldifferent over a list of variables with 63-value domains
static bool alldiff_gac(vector<uint64_t*>& dom) {
  int nv = dom.size();
  vector<int> mv(nv, -1), mval(W, -1);
  function<bool(int, vector<char>&)> aug = [&](int v, vector<char>& seen) -> bool {
    uint64_t m = *dom[v];
    while (m) { int u = __builtin_ctzll(m); m &= m - 1;
      if (seen[u]) continue; seen[u] = 1;
      if (mval[u] == -1 || aug(mval[u], seen)) { mv[v] = u; mval[u] = v; return true; } }
    return false;
  };
  for (int v = 0; v < nv; v++) { vector<char> seen(W, 0); if (!aug(v, seen)) return false; }
  // digraph: vars 0..nv-1, values nv..nv+W-1; matched var->val, unmatched val->var
  int T = nv + W; vector<vector<int>> g(T);
  for (int v = 0; v < nv; v++) { g[v].push_back(nv + mv[v]);
    uint64_t m = *dom[v]; while (m) { int u = __builtin_ctzll(m); m &= m - 1;
      if (u != mv[v]) g[nv + u].push_back(v); } }
  vector<int> idx(T, -1), low(T), comp_(T, -1); vector<char> on(T, 0); vector<int> stk;
  int cnt = 0, nc = 0;
  function<void(int)> tj = [&](int u) {
    idx[u] = low[u] = cnt++; stk.push_back(u); on[u] = 1;
    for (int w : g[u]) { if (idx[w] == -1) { tj(w); low[u] = min(low[u], low[w]); }
                         else if (on[w]) low[u] = min(low[u], idx[w]); }
    if (low[u] == idx[u]) { while (1) { int w = stk.back(); stk.pop_back(); on[w] = 0; comp_[w] = nc; if (w == u) break; } nc++; }
  };
  for (int u = 0; u < T; u++) if (idx[u] == -1) tj(u);
  vector<char> reach(T, 0); vector<int> st;
  for (int u = 0; u < W; u++) if (mval[u] == -1) { reach[nv + u] = 1; st.push_back(nv + u); }
  while (!st.empty()) { int u = st.back(); st.pop_back();
    for (int w : g[u]) if (!reach[w]) { reach[w] = 1; st.push_back(w); } }
  for (int v = 0; v < nv; v++) { uint64_t keep = 1ull << mv[v], m = *dom[v];
    while (m) { int u = __builtin_ctzll(m); m &= m - 1;
      if (u == mv[v]) continue;
      if (comp_[nv + u] == comp_[v] || reach[nv + u]) keep |= 1ull << u; }
    *dom[v] = keep; if (!*dom[v]) return false; }
  return true;
}

static long long domsize() { long long s = 0;
  for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) if (i != j) s += __builtin_popcountll(D[i][j]);
  return s; }

// returns false if refuted
static bool closure(bool use_alldiff) {
  for (int pass = 0; pass < 60; pass++) {
    bool ch = false;
    for (int i = 0; i < N; i++) for (int k = 0; k < N; k++) { if (i == k) continue;
      for (int j = 0; j < N; j++) { if (j == i || j == k) continue;
        uint64_t nd = D[i][k] & comp(D[i][j], D[j][k]);
        if (nd != D[i][k]) { if (!nd) return false; D[i][k] = nd; D[k][i] = revmask(nd); ch = true; } } }
    if (use_alldiff) for (int d = 1; d < N; d++) {
      vector<uint64_t*> dom; for (int i = 0; i + d < N; i++) dom.push_back(&D[i][i + d]);
      long long before = 0; for (auto p : dom) before += __builtin_popcountll(*p);
      if (!alldiff_gac(dom)) return false;
      long long after = 0; for (auto p : dom) after += __builtin_popcountll(*p);
      if (after != before) { ch = true; for (int i = 0; i + d < N; i++) D[i + d][i] = revmask(D[i][i + d]); } }
    if (!ch) break;
  }
  return true;
}

static void init(int n, const vector<pair<int,int>>& fixed) {
  N = n; W = 2 * n - 1; FULL = (W == 64) ? ~0ull : ((1ull << W) - 1);
  uint64_t all = FULL & ~(1ull << (n - 1));            // exclude e = 0
  for (int i = 0; i < n; i++) for (int j = 0; j < n; j++)
    D[i][j] = (i == j) ? (1ull << (n - 1)) : all;
  // fixed cells: h_c = v pins one-sided bounds, and pins edges between fixed cells
  for (auto& f : fixed) { int c = f.first, v = f.second;
    for (int j = 0; j < n; j++) { if (j == c) continue;
      uint64_t m = 0;                                   // h_j - v with h_j in [0,n-1]\{v}
      for (int hj = 0; hj < n; hj++) if (hj != v) m |= 1ull << (hj - v + n - 1);
      D[c][j] &= m; D[j][c] = revmask(D[c][j]); } }
  for (auto& f : fixed) for (auto& g : fixed) { if (f.first == g.first) continue;
    D[f.first][g.first] = 1ull << (g.second - f.second + n - 1);
    D[g.first][f.first] = revmask(D[f.first][g.first]); }
}

static bool costas_ok(const vector<pair<int,int>>& a) {
  set<pair<int,int>> s;
  for (size_t x = 0; x < a.size(); x++) for (size_t y = x + 1; y < a.size(); y++) {
    if (a[x].second == a[y].second) return false;
    pair<int,int> lab = {a[y].first - a[x].first, a[y].second - a[x].second};
    if (s.count(lab)) return false; s.insert(lab); }
  return true;
}

int main(int argc, char** argv) {
  string mode = argv[1];
  if (mode == "cells") {
    int n = atoi(argv[2]); long long ref = 0, pruned = 0, maxp = 0;
    for (int c = 0; c < n; c++) for (int v = 0; v < n; v++) {
      init(n, {{c, v}}); long long b = domsize();
      bool ok = closure(true);
      if (!ok) { ref++; continue; }
      long long p = b - domsize(); pruned += p; maxp = max(maxp, p); }
    printf("CELLS n=%d cells=%d refuted=%lld extra_pruned_total=%lld max_per_cell=%lld\n",
           n, n * n, ref, pruned, maxp);
    return 0;
  }
  if (mode == "cells32row") {
    int n = 32; long long ref = 0, pruned = 0;
    for (int v = 0; v < 16; v++) { init(n, {{15, v}}); long long b = domsize();
      if (!closure(true)) { ref++; continue; } pruned += b - domsize(); }
    printf("CELLS n=32 central-row reps=16 refuted=%lld extra_pruned_total=%lld\n", ref, pruned);
    return 0;
  }
  if (mode == "gt") {
    int n = atoi(argv[2]), smax = atoi(argv[3]), samples = atoi(argv[4]);
    vector<vector<int>> cat; { ifstream f("cat" + to_string(n) + ".txt"); string ln;
      while (getline(f, ln)) { vector<int> p; const char* s = ln.c_str(); char* e;
        for (long x = strtol(s, &e, 10); e != s; s = e, x = strtol(s, &e, 10)) p.push_back((int)x);
        if ((int)p.size() == n) cat.push_back(p); } }
    printf("GT n=%d catalogue=%zu\n", n, cat.size());
    mt19937_64 rng(7);
    printf(" s  tested   feas infeas refuted unsound detect%%\n");
    for (int s = 1; s <= smax; s++) {
      int tested = 0, nf = 0, ni = 0, rf = 0, uns = 0; long long tries = 0;
      while (tested < samples && tries < samples * 500LL) { tries++;
        vector<int> cols(n); iota(cols.begin(), cols.end(), 0);
        shuffle(cols.begin(), cols.end(), rng); cols.resize(s); sort(cols.begin(), cols.end());
        vector<int> hs(n); iota(hs.begin(), hs.end(), 0); shuffle(hs.begin(), hs.end(), rng); hs.resize(s);
        vector<pair<int,int>> cfg; for (int t = 0; t < s; t++) cfg.push_back({cols[t], hs[t]});
        if (!costas_ok(cfg)) continue;
        tested++;
        bool feas = false;
        for (auto& p : cat) { bool m = true; for (auto& c : cfg) if (p[c.first] != c.second) { m = false; break; }
          if (m) { feas = true; break; } }
        init(n, cfg); bool ok = closure(true);
        if (feas) nf++; else ni++;
        if (!ok) { rf++; if (feas) uns++; } }
      printf("%2d %7d %6d %6d %7d %7d %7.2f\n", s, tested, nf, ni, rf, uns, ni ? 100.0 * rf / ni : 0.0); }
    return 0;
  }
  if (mode == "file") {      // read configs "n s c1 v1 c2 v2 ..." one per line, print refute flag
    int n=atoi(argv[2]); string ln; ifstream f(argv[3]);
    while (getline(f,ln)) { vector<int> t; const char* p=ln.c_str(); char* e;
      for(long x=strtol(p,&e,10); e!=p; p=e, x=strtol(p,&e,10)) t.push_back((int)x);
      if(t.empty())continue; vector<pair<int,int>> cfg;
      for(size_t i=0;i+1<t.size();i+=2)cfg.push_back({t[i],t[i+1]});
      init(n,cfg); printf("%d\n", closure(true)?0:1); }
    return 0; }
  if (mode == "score2") {
    vector<int> h = {0,1,28,20,27,17,18,21,30,26,14,9,25,11,31,29,23,5,13,6,16,15,12,3,7,19,24,8,22,2,4,10};
    for (int k = 2; k <= 32; k++) {
      vector<pair<int,int>> cfg; for (int i = 0; i < k; i++) cfg.push_back({i, h[i]});
      bool selfok = costas_ok(cfg);
      init(32, cfg); bool ok = closure(true);
      printf("prefix=%2d  own_displacements_distinct=%d  closure_refutes=%d\n", k, (int)selfok, (int)!ok);
      if (!selfok || !ok) { printf("  -> first detection at prefix length %d\n", k); break; } }
    return 0;
  }
  return 1;
}
