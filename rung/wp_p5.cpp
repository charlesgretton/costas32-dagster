// WP-P5: exhaust every order-32 permutation obtained by deleting two columns
// and two rows from the board and filling the remaining 30x30 compressed
// sub-board with an algebraically constructed order-30 Costas array.
//
// Core families of order 30:
//   W1(31,g,c)   h[i] = g^(i+c) mod 31 - 1,  g primitive mod 31   (240 arrays)
//   G2(32,a,b)   a^i + b^j = 1 over F_32,    a,b primitive        (900 arrays)
// Both families closed under the dihedral group of the square, then deduplicated.
//
// Augmentation space, per core:
//   C = 2 deleted columns  (C(32,2) = 496)
//   R = 2 deleted rows     (496)
//   mu : C -> R            (2 matchings)
// The 30 core dots go to the surviving columns/rows in increasing order; the two
// extra dots go to (c, mu(c)).  When the deleted columns and rows are both at the
// ends of the board the compression is a translation and the core's displacements
// are inherited unchanged; that CONTIGUOUS sub-case is reported separately because
// it is the actual construction mechanism (and is where the score-2 candidate sits).
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <set>
#include <vector>
#include <string>
using namespace std;

static int score32(const int* h, int cut) {
  int s = 0;
  for (int d = 1; d < 32; d++) {
    uint64_t m = 0; const int lim = 32 - d;
    for (int i = 0; i < lim; i++) {
      unsigned e = (unsigned)(h[i + d] - h[i] + 31);
      s += (int)((m >> e) & 1ull); m |= 1ull << e;
    }
    if (s > cut) return cut + 1;
  }
  return s;
}
static bool costas30(const array<int,30>& k) {
  for (int d = 1; d < 30; d++) { uint64_t m = 0;
    for (int i = 0; i + d < 30; i++) { unsigned e = (unsigned)(k[i+d]-k[i]+29);
      if ((m >> e) & 1ull) return false; m |= 1ull << e; } }
  return true;
}

// --- GF(32), x^5 + x^2 + 1
static uint8_t gmul(uint8_t a, uint8_t b) { uint8_t r = 0;
  for (int s = 0; s < 5; s++) { if (b & 1) r ^= a; b >>= 1;
    bool c = a & 0x10; a = (uint8_t)((a << 1) & 0x1f); if (c) a ^= 0x05; }
  return r & 0x1f; }

int main(int argc, char** argv) {
  // ---------- build core families
  vector<array<int,30>> cores;
  int nW = 0, nG = 0;
  for (int g = 2; g < 31; g++) {                       // primitive roots mod 31
    set<int> seen; int x = 1; bool prim = true;
    for (int i = 0; i < 30; i++) { x = x * g % 31; seen.insert(x); }
    if ((int)seen.size() != 30) prim = false;
    if (!prim) continue;
    for (int c = 0; c < 30; c++) { array<int,30> k; int v = 1;
      for (int i = 0; i < c; i++) v = v * g % 31;
      for (int i = 0; i < 30; i++) { v = v * g % 31; k[i] = v - 1; }
      assert(costas30(k)); cores.push_back(k); nW++; }
  }
  { // GF(32) log/exp
    uint8_t ex[31]; int lg[32]; memset(lg, -1, sizeof lg);
    uint8_t x = 1; for (int i = 0; i < 31; i++) { ex[i] = x; lg[x] = i; x = gmul(x, 2); }
    assert(x == 1);
    for (uint8_t a = 2; a < 32; a++) for (uint8_t b = 2; b < 32; b++) {
      // h[i-1] = j-1 with a^i + b^j = 1, i,j in 1..30
      array<int,30> k; bool ok = true;
      for (int i = 1; i <= 30 && ok; i++) {
        uint8_t ai = ex[(lg[a] * i) % 31];
        uint8_t t = ai ^ 1;                                   // need b^j = 1 - a^i = a^i + 1
        if (t == 0) { ok = false; break; }
        int lt = lg[t], lb = lg[b];
        // solve lb*j = lt mod 31
        int inv = 1; for (int e = 0; e < 29; e++) inv = inv * lb % 31;   // lb^29 = lb^{-1} mod 31
        int j = (int)((long long)lt * inv % 31);
        if (j < 1 || j > 30) { ok = false; break; }
        k[i-1] = j - 1;
      }
      if (!ok) continue;
      set<int> s(k.begin(), k.end()); if (s.size() != 30) continue;
      if (!costas30(k)) continue;
      cores.push_back(k); nG++;
    }
  }
  printf("cores before symmetry closure: Welch W1(31)=%d  Golomb G2(32)=%d\n", nW, nG);
  { // close under the dihedral group and deduplicate
    set<array<int,30>> S;
    for (auto& k : cores) { array<int,30> b = k;
      for (int t = 0; t < 2; t++) { if (t) { array<int,30> inv; for (int i = 0; i < 30; i++) inv[b[i]] = i; b = inv; }
        for (int f = 0; f < 4; f++) { array<int,30> c;
          for (int i = 0; i < 30; i++) { int j = (f & 1) ? 29 - i : i; c[i] = (f & 2) ? 29 - b[j] : b[j]; }
          assert(costas30(c)); S.insert(c); } } }
    cores.assign(S.begin(), S.end());
  }
  printf("distinct order-30 cores after dihedral closure: %zu\n", cores.size());
  { // the score-2 candidate's core must be present, else the sweep is incomplete
    int S2[32]={0,1,28,20,27,17,18,21,30,26,14,9,25,11,31,29,23,5,13,6,16,15,12,3,7,19,24,8,22,2,4,10};
    array<int,30> kc; for(int i=0;i<30;i++) kc[i]=S2[i+2]-2;
    assert(costas30(kc));
    bool found=false; for(auto&k:cores) if(k==kc){found=true;break;}
    printf("score-2 candidate core present in core set: %s\n", found?"YES":"NO");
    assert(found);
  }

  // ---------- augmentation sweep
  vector<pair<int,int>> pairs;
  for (int a = 0; a < 32; a++) for (int b = a + 1; b < 32; b++) pairs.push_back({a, b});
  printf("augmentation space = %zu cores x %zu col-pairs x %zu row-pairs x 2 = %lld\n",
         cores.size(), pairs.size(), pairs.size(), (long long)cores.size() * pairs.size() * pairs.size() * 2);

  long long tested = 0, costas = 0;
  int best = 1 << 30; array<int,32> bh{}; string bd;
  long long hist[12] = {0};
  long long tested_cont = 0; int best_cont = 1 << 30; array<int,32> bhc{};
  int cols[30], rows[30], h[32];
  auto contiguous = [](int a, int b) { return (a == 0 && b == 1) || (a == 0 && b == 31) || (a == 30 && b == 31); };

  for (size_t ci = 0; ci < cores.size(); ci++) {
    const auto& k = cores[ci];
    for (size_t pc = 0; pc < pairs.size(); pc++) {
      int c1 = pairs[pc].first, c2 = pairs[pc].second;
      { int t = 0; for (int x = 0; x < 32; x++) if (x != c1 && x != c2) cols[t++] = x; }
      bool ccont = contiguous(c1, c2);
      for (size_t pr = 0; pr < pairs.size(); pr++) {
        int r1 = pairs[pr].first, r2 = pairs[pr].second;
        { int t = 0; for (int x = 0; x < 32; x++) if (x != r1 && x != r2) rows[t++] = x; }
        bool cont = ccont && contiguous(r1, r2);
        for (int t = 0; t < 30; t++) h[cols[t]] = rows[k[t]];
        for (int m = 0; m < 2; m++) {
          h[c1] = m ? r2 : r1; h[c2] = m ? r1 : r2;
          tested++;
          int s = score32(h, 10);
          if (s <= 10) hist[s]++;
          if (s == 0) { costas++; if (best > 0) { best = 0; memcpy(bh.data(), h, sizeof h); } }
          if (s < best) { best = s; memcpy(bh.data(), h, sizeof h);
            char buf[128]; snprintf(buf, sizeof buf, "core#%zu del_cols=(%d,%d) del_rows=(%d,%d) match=%d", ci, c1, c2, r1, r2, m); bd = buf; }
          if (cont) { tested_cont++; if (s < best_cont) { best_cont = s; memcpy(bhc.data(), h, sizeof h); } }
        }
      }
    }
    if ((ci % 200) == 0) fprintf(stderr, "core %zu/%zu tested=%lld best=%d\n", ci, cores.size(), tested, best);
  }
  printf("\nTESTED %lld   COSTAS ARRAYS FOUND: %lld   minimum score: %d  (%s)\n", tested, costas, best, bd.c_str());
  printf("score histogram (0..10):"); for (int i = 0; i <= 10; i++) printf(" %d:%lld", i, hist[i]); printf("\n");
  printf("best permutation:"); for (int x : bh) printf(" %d", x); printf("\n");
  printf("\nCONTIGUOUS sub-case (core in a corner block, displacements inherited):\n");
  printf("  tested %lld   minimum score %d\n  perm:", tested_cont, best_cont);
  for (int x : bhc) printf(" %d", x); printf("\n");
  return 0;
}
