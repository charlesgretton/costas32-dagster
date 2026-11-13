// WP-P5 extension: three-point augmentation from algebraic order-29 Costas cores.
// Same shape as the two-point run: delete 3 columns and 3 rows, place the order-29
// core in the compressed 29x29 sub-board, place 3 extra dots as a bijection from
// the deleted columns to the deleted rows, test the resulting order-32 permutation.
//
// Core-first pruning: the 29 placed core dots are a subset of the 32, so if they
// already carry a repeated displacement the whole configuration is dead. That test
// costs C(29,2)=406 pairs with early abort and removes the overwhelming majority of
// the C(32,3)^2 = 2.46e7 placements per core before any extra dot is considered.
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <set>
#include <vector>
using namespace std;

static uint8_t gmul(uint8_t a, uint8_t b) { uint8_t r = 0;
  for (int s = 0; s < 5; s++) { if (b & 1) r ^= a; b >>= 1;
    bool c = a & 0x10; a = (uint8_t)((a << 1) & 0x1f); if (c) a ^= 0x05; } return r & 0x1f; }

template <int M> static bool costasM(const array<int,M>& k) {
  for (int d = 1; d < M; d++) { uint64_t m = 0;
    for (int i = 0; i + d < M; i++) { unsigned e = (unsigned)(k[i+d]-k[i]+M-1);
      if ((m >> e) & 1ull) return false; m |= 1ull << e; } }
  return true; }

int main(int argc, char** argv) {
  double budget = argc > 1 ? atof(argv[1]) : 250.0;
  size_t START = argc > 2 ? (size_t)atoll(argv[2]) : 0;
  // ---- order-30 algebraic cores (as in the two-point run)
  vector<array<int,30>> c30;
  for (int g = 2; g < 31; g++) { set<int> s; int x = 1;
    for (int i = 0; i < 30; i++) { x = x * g % 31; s.insert(x); }
    if ((int)s.size() != 30) continue;
    for (int c = 0; c < 30; c++) { array<int,30> k; int v = 1;
      for (int i = 0; i < c; i++) v = v * g % 31;
      for (int i = 0; i < 30; i++) { v = v * g % 31; k[i] = v - 1; }
      c30.push_back(k); } }
  { uint8_t ex[31]; int lg[32]; memset(lg, -1, sizeof lg); uint8_t x = 1;
    for (int i = 0; i < 31; i++) { ex[i] = x; lg[x] = i; x = gmul(x, 2); }
    for (uint8_t a = 2; a < 32; a++) for (uint8_t b = 2; b < 32; b++) {
      array<int,30> k; bool ok = true; int inv = 1, lb = lg[b];
      for (int e = 0; e < 29; e++) inv = inv * lb % 31;
      for (int i = 1; i <= 30 && ok; i++) { uint8_t ai = ex[(lg[a]*i)%31], t = ai ^ 1;
        if (!t) { ok = false; break; } int j = (int)((long long)lg[t] * inv % 31);
        if (j < 1 || j > 30) { ok = false; break; } k[i-1] = j - 1; }
      if (!ok) continue; set<int> s(k.begin(), k.end()); if (s.size() != 30) continue;
      if (!costasM<30>(k)) continue; c30.push_back(k); } }

  // ---- order-29 cores: G2(31,a,b) directly, plus corner deletions from the order-30 set
  set<array<int,29>> S29;
  for (int a = 2; a < 31; a++) { set<int> sa; int x = 1;
    for (int i = 0; i < 30; i++) { x = x * a % 31; sa.insert(x); } if (sa.size() != 30) continue;
    for (int b = 2; b < 31; b++) { set<int> sb; int y = 1;
      for (int i = 0; i < 30; i++) { y = y * b % 31; sb.insert(y); } if (sb.size() != 30) continue;
      array<int,29> k; bool ok = true;
      for (int i = 1; i <= 29 && ok; i++) { int ai = 1; for (int e = 0; e < i; e++) ai = ai * a % 31;
        int t = (1 - ai + 31) % 31; if (!t) { ok = false; break; }
        int j = -1, bj = 1; for (int e = 1; e <= 29; e++) { bj = bj * b % 31; if (bj == t) { j = e; break; } }
        if (j < 0) { ok = false; break; } k[i-1] = j - 1; }
      if (!ok) continue; set<int> s(k.begin(), k.end()); if (s.size() != 29) continue;
      if (costasM<29>(k)) S29.insert(k); } }
  int nG2_31 = S29.size();
  for (auto& k : c30) {                       // delete a corner dot and compress
    for (int corner = 0; corner < 4; corner++) {
      int ci = (corner & 1) ? 29 : 0, want = (corner & 2) ? 29 : 0;
      if (k[ci] != want) continue;
      array<int,29> q; int t = 0;
      for (int i = 0; i < 30; i++) { if (i == ci) continue;
        q[t++] = (k[i] > want) ? k[i] - 1 : k[i]; }
      if (costasM<29>(q)) S29.insert(q); } }
  { set<array<int,29>> T;                      // dihedral closure
    for (auto& k : S29) { array<int,29> b = k;
      for (int t = 0; t < 2; t++) { if (t) { array<int,29> inv; for (int i = 0; i < 29; i++) inv[b[i]] = i; b = inv; }
        for (int f = 0; f < 4; f++) { array<int,29> c;
          for (int i = 0; i < 29; i++) { int j = (f & 1) ? 28 - i : i; c[i] = (f & 2) ? 28 - b[j] : b[j]; }
          T.insert(c); } } }
    S29 = T; }
  vector<array<int,29>> cores(S29.begin(), S29.end());
  printf("order-29 algebraic cores: G2(31)=%d direct, corner-deletions of the order-30 set added,\n", nG2_31);
  printf("  distinct after dihedral closure: %zu\n", cores.size());

  vector<array<int,3>> trip;
  for (int a = 0; a < 32; a++) for (int b = a+1; b < 32; b++) for (int c = b+1; c < 32; c++) trip.push_back({a,b,c});
  printf("space per core = %zu x %zu x 6 = %lld ; total %lld\n", trip.size(), trip.size(),
         (long long)trip.size()*trip.size()*6, (long long)cores.size()*trip.size()*trip.size()*6);

  int perm3[6][3] = {{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
  long long coreplace = 0, survived = 0, tested = 0, costas = 0; int best = 1 << 30;
  array<int,32> bh{}; long long hist[12] = {0};
  auto t0 = chrono::steady_clock::now(); size_t done = 0;
  int cols[29], rows[29], h[32]; uint64_t used[32];

  for (size_t ci = START; ci < cores.size(); ci++) {
    if (chrono::duration<double>(chrono::steady_clock::now()-t0).count() > budget) break;
    const auto& k = cores[ci];
    for (auto& C : trip) {
      { int t = 0; for (int x = 0; x < 32; x++) if (x!=C[0]&&x!=C[1]&&x!=C[2]) cols[t++] = x; }
      for (auto& R : trip) {
        { int t = 0; for (int x = 0; x < 32; x++) if (x!=R[0]&&x!=R[1]&&x!=R[2]) rows[t++] = x; }
        coreplace++;
        memset(used, 0, sizeof used);
        bool ok = true;
        for (int a = 0; a < 29 && ok; a++) { int xa = cols[a], ya = rows[k[a]];
          for (int b = a+1; b < 29; b++) { int d = cols[b]-xa; unsigned e = (unsigned)(rows[k[b]]-ya+31);
            if ((used[d] >> e) & 1ull) { ok = false; break; } used[d] |= 1ull << e; } }
        if (!ok) continue;
        survived++;
        for (int t = 0; t < 29; t++) h[cols[t]] = rows[k[t]];
        for (int m = 0; m < 6; m++) {
          h[C[0]] = R[perm3[m][0]]; h[C[1]] = R[perm3[m][1]]; h[C[2]] = R[perm3[m][2]];
          tested++;
          int s = 0; uint64_t u2[32]; memset(u2, 0, sizeof u2);
          for (int d = 1; d < 32 && s <= 10; d++) for (int i = 0; i+d < 32; i++) {
            unsigned e = (unsigned)(h[i+d]-h[i]+31);
            s += (int)((u2[d] >> e) & 1ull); u2[d] |= 1ull << e; }
          if (s <= 10) hist[s]++;
          if (s == 0) costas++;
          if (s < best) { best = s; memcpy(bh.data(), h, sizeof h); } }
      }
    }
    done = ci + 1;
  }
  double el = chrono::duration<double>(chrono::steady_clock::now()-t0).count();
  printf("\ncores %zu..%zu of %zu in %.1f s\n", START, done, cores.size(), el);
  printf("core placements examined: %lld   surviving core-only Costas test: %lld (%.4f%%)\n",
         coreplace, survived, 100.0*survived/max(1LL,coreplace));
  printf("full configurations tested: %lld   COSTAS FOUND: %lld   minimum score: %d\n", tested, costas, best);
  printf("score histogram (0..10):"); for (int i = 0; i <= 10; i++) printf(" %d:%lld", i, hist[i]); printf("\n");
  printf("best perm:"); for (int x : bh) printf(" %d", x); printf("\n");
  printf("projected full-run time: %.0f s\n", el * cores.size() / max((size_t)1, done));
  return 0;
}
