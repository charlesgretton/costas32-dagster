// Expanded native GF(32) affine-power gate.
//
//   h(i) = rho_out( a * [ rho_in^{-1}(i) ]^k  +  b )
//
// rho ranges over 240 structured orderings: 120 polynomial-basis bit
// permutations x 2 traversals (binary, reflected Gray).  Input and output
// orderings are chosen INDEPENDENTLY, which is the expansion the earlier gate
// asked for.  Parameters k in 1..30, a in F32^*, b in F32.
//
// Family size 30*31*32*240*240 = 1,714,176,000.
// b is swept over 16 representatives only: b and b^c_out differ by the
// vertical reflection h -> 31-h, which preserves the Costas score.
// (c_out = 31 for binary output traversal, 16 for Gray, since
//  gray(31-i) = gray(i) ^ 16.)
//
// Modes:
//   selftest         exhaustive field self-tests (as in the original gate)
//   sweep LO HI CUT  exhaustive minimum search over k in [LO,HI), early abort
//                    once the running score exceeds CUT
//   match N SEED     matched-sample comparison: N uniform family members and
//                    N uniform random permutations, full scores, quantiles,
//                    D4-canonical deduplication
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <string>
#include <vector>
using namespace std;

struct GF32 {
  static uint8_t mul_poly(uint8_t a, uint8_t b) {
    uint8_t r = 0;
    for (int s = 0; s < 5; s++) {
      if (b & 1) r ^= a;
      b >>= 1;
      bool c = a & 0x10;
      a = (uint8_t)((a << 1) & 0x1f);
      if (c) a ^= 0x05;
    }
    return r & 0x1f;
  }
  array<uint8_t, 31> ex{}; array<int8_t, 32> lg{}; uint8_t primitive = 0;
  GF32() {
    lg.fill(-1);
    for (uint8_t g = 2; g < 32; g++) {
      set<int> s; uint8_t x = 1;
      for (int i = 0; i < 31; i++) { s.insert(x); x = mul_poly(x, g); }
      if (s.size() == 31 && x == 1) { primitive = g; break; }
    }
    assert(primitive);
    uint8_t x = 1;
    for (int i = 0; i < 31; i++) { ex[i] = x; lg[x] = i; x = mul_poly(x, primitive); }
    assert(x == 1);
  }
  uint8_t mul(uint8_t a, uint8_t b) const { return (!a || !b) ? 0 : ex[(lg[a] + lg[b]) % 31]; }
  uint8_t pw(uint8_t a, int e) const { if (e == 0) return 1; if (a == 0) return 0; int z = (lg[a] * e) % 31; if (z < 0) z += 31; return ex[z]; }
  uint8_t trace(uint8_t a) const { uint8_t t = 0, x = a; for (int i = 0; i < 5; i++) { t ^= x; x = mul(x, x); } return t & 1; }
};

static inline int score32(const int* h) {
  int s = 0;
  for (int d = 1; d < 32; d++) {
    uint64_t m = 0; const int lim = 32 - d;
    for (int i = 0; i < lim; i++) {
      unsigned e = (unsigned)(h[i + d] - h[i] + 31);
      s += (int)((m >> e) & 1ull); m |= 1ull << e;
    }
  }
  return s;
}
// early-abort variant: returns >cut as soon as the running score passes cut
static inline int score32_cut(const int* h, int cut) {
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
static bool isperm(const int* h) { int c[32] = {0}; for (int i = 0; i < 32; i++) { if (h[i] < 0 || h[i] > 31 || c[h[i]]) return false; c[h[i]] = 1; } return true; }

// ---- 240 structured orderings: bit permutation o traversal
struct Ord { array<uint8_t, 32> elem{}, rank{}; int sigma, gray; uint8_t cflip; };
static vector<Ord> build_orders() {
  vector<Ord> v; int p[5] = {0, 1, 2, 3, 4}; vector<array<int, 5>> perms;
  sort(p, p + 5);
  do { perms.push_back({p[0], p[1], p[2], p[3], p[4]}); } while (next_permutation(p, p + 5));
  assert(perms.size() == 120);
  for (int si = 0; si < 120; si++)
    for (int g = 0; g < 2; g++) {
      Ord o; o.sigma = si; o.gray = g;
      for (int i = 0; i < 32; i++) {
        int t = g ? (i ^ (i >> 1)) : i, y = 0;
        for (int bpos = 0; bpos < 5; bpos++) if ((t >> bpos) & 1) y |= 1 << perms[si][bpos];
        o.elem[i] = (uint8_t)y;
      }
      for (int i = 0; i < 32; i++) o.rank[o.elem[i]] = (uint8_t)i;
      // constant realising the vertical reflection on this output ordering
      int t = g ? 16 : 31, y = 0;
      for (int bpos = 0; bpos < 5; bpos++) if ((t >> bpos) & 1) y |= 1 << perms[si][bpos];
      o.cflip = (uint8_t)y;
      v.push_back(o);
    }
  return v;
}

// ---- D4 canonical form (8 square symmetries)
static array<int, 32> canon(const int* h) {
  array<int, 32> best; bool first = true;
  int base[32], inv[32];
  for (int i = 0; i < 32; i++) base[i] = h[i];
  for (int t = 0; t < 2; t++) {
    if (t) { for (int i = 0; i < 32; i++) inv[base[i]] = i; memcpy(base, inv, sizeof inv); }
    for (int f = 0; f < 4; f++) {
      array<int, 32> c;
      for (int i = 0; i < 32; i++) {
        int j = (f & 1) ? 31 - i : i;
        c[i] = (f & 2) ? 31 - base[j] : base[j];
      }
      if (first || c < best) { best = c; first = false; }
    }
  }
  return best;
}

static void selftest(const GF32& F) {
  long long triples = 0;
  for (int a = 0; a < 32; a++) for (int b = 0; b < 32; b++) {
    assert(GF32::mul_poly(a, b) == F.mul(a, b));
    assert(GF32::mul_poly(a, b) == GF32::mul_poly(b, a));
    for (int c = 0; c < 32; c++) {
      assert(GF32::mul_poly(GF32::mul_poly(a, b), c) == GF32::mul_poly(a, GF32::mul_poly(b, c)));
      assert(GF32::mul_poly(a, b ^ c) == (GF32::mul_poly(a, b) ^ GF32::mul_poly(a, c)));
      triples++;
    }
  }
  for (int a = 1; a < 32; a++) assert(F.pw(a, 31) == 1);
  { set<int> s; for (auto x : F.ex) s.insert(x); assert(s.size() == 31); }
  for (int k = 1; k <= 30; k++) { set<int> s; for (int x = 0; x < 32; x++) s.insert(F.pw(x, k)); assert(s.size() == 32); }
  for (int a = 0; a < 32; a++) { assert(F.trace(a) <= 1); assert(F.trace(F.mul(a, a)) == F.trace(a)); }
  auto ords = build_orders();
  for (auto& o : ords) { set<int> s; for (int i = 0; i < 32; i++) s.insert(o.elem[i]); assert(s.size() == 32); }
  // canon is an involutive-closed D4 action: canon(sym(h)) == canon(h)
  mt19937_64 rng(1); int h[32]; iota(h, h + 32, 0);
  for (int t = 0; t < 200; t++) {
    shuffle(h, h + 32, rng); auto c0 = canon(h);
    int g[32]; for (int i = 0; i < 32; i++) g[i] = 31 - h[31 - i];
    assert(canon(g) == c0);
    int inv[32]; for (int i = 0; i < 32; i++) inv[h[i]] = i;
    assert(canon(inv) == c0);
    assert(score32(h) == score32(g) && score32(h) == score32(inv));
  }
  printf("SELFTEST PASS primitive=%d triples=%lld orders=%zu\n", (int)F.primitive, triples, ords.size());
}

int main(int argc, char** argv) {
  GF32 F; auto ords = build_orders();
  string mode = argc > 1 ? argv[1] : "selftest";

  if (mode == "selftest") { selftest(F); return 0; }

  if (mode == "sweep") {
    int klo = atoi(argv[2]), khi = atoi(argv[3]), cut = atoi(argv[4]);
    int best = 1 << 30; string bd; array<int, 32> bh{};
    long long tested = 0, survived = 0;
    map<int, long long> tail;             // histogram of everything <= cut
    vector<uint8_t> vv(32);
    for (int k = klo; k < khi; k++) {
      uint8_t pk[32]; for (int x = 0; x < 32; x++) pk[x] = F.pw(x, k);
      for (size_t oi = 0; oi < ords.size(); oi++) {
        uint8_t u[32]; for (int i = 0; i < 32; i++) u[i] = pk[ords[oi].elem[i]];
        for (int a = 1; a < 32; a++) {
          uint8_t v[32]; for (int i = 0; i < 32; i++) v[i] = F.mul((uint8_t)a, u[i]);
          for (size_t oo = 0; oo < ords.size(); oo++) {
            const uint8_t* R = ords[oo].rank.data(); uint8_t cf = ords[oo].cflip;
            for (int b = 0; b < 32; b++) {
              if ((b ^ cf) < b) continue;       // vertical-reflection quotient
              int h[32]; for (int i = 0; i < 32; i++) h[i] = R[v[i] ^ b];
              tested++;
              int s = score32_cut(h, cut);
              if (s <= cut) {
                survived++; tail[s]++;
                if (s < best) {
                  best = s; bh = *(array<int, 32>*)h;
                  char buf[160]; snprintf(buf, sizeof buf,
                    "k=%d a=%d b=%d in(sigma=%d,gray=%d) out(sigma=%d,gray=%d)",
                    k, a, b, ords[oi].sigma, ords[oi].gray, ords[oo].sigma, ords[oo].gray);
                  bd = buf;
                }
              }
            }
          }
        }
      }
      fprintf(stderr, "k=%d done tested=%lld best=%d\n", k, tested, best);
    }
    printf("SWEEP k=[%d,%d) cut=%d tested=%lld survived=%lld best=%d %s\n",
           klo, khi, cut, tested, survived, best, bd.c_str());
    if (best <= cut) {
      assert(isperm(bh.data())); assert(score32(bh.data()) == best);
      printf("perm="); for (int x : bh) printf("%d ", x); printf("\n");
    }
    printf("tail_hist");
    for (auto& kv : tail) printf(" %d:%lld", kv.first, kv.second);
    printf("\n");
    return 0;
  }


  if (mode == "one") {
    int k=atoi(argv[2]),a=atoi(argv[3]),b=atoi(argv[4]);size_t oi=atoi(argv[5]),oo=atoi(argv[6]);
    int h[32];for(int i=0;i<32;i++)h[i]=ords[oo].rank[F.mul((uint8_t)a,F.pw(ords[oi].elem[i],k))^b];
    assert(isperm(h));printf("ONE k=%d a=%d b=%d in=%zu out=%zu score=%d\nperm=",k,a,b,oi,oo,score32(h));
    for(int i=0;i<32;i++)printf("%d ",h[i]);printf("\n");return 0;
  }
  if (mode == "randtail") {
    long long N=atoll(argv[2]); uint64_t seed=strtoull(argv[3],nullptr,10); int cut=atoi(argv[4]);
    mt19937_64 rng(seed); int r[32]; iota(r,r+32,0);
    map<int,long long> tail; int best=1<<30; array<int,32> bh{};
    for(long long t=0;t<N;t++){
      for(int i=31;i>0;i--){int j=(int)(rng()%(unsigned)(i+1));swap(r[i],r[j]);}
      int s=score32_cut(r,cut);
      if(s<=cut){tail[s]++; if(s<best){best=s;for(int i=0;i<32;i++)bh[i]=r[i];}}
    }
    printf("RANDTAIL N=%lld seed=%llu cut=%d best=%d\n",N,(unsigned long long)seed,cut,best);
    if(best<=cut){assert(isperm(bh.data()));assert(score32(bh.data())==best);
      printf("perm=");for(int x:bh)printf("%d ",x);printf("\n");}
    printf("tail_hist");for(auto&kv:tail)printf(" %d:%lld",kv.first,kv.second);printf("\n");
    return 0;
  }

  if (mode == "famtail") {   // sample the family (optionally with input translation) with a cutoff
    long long N=atoll(argv[2]); uint64_t seed=strtoull(argv[3],nullptr,10); int cut=atoi(argv[4]);
    int useT = argc>5?atoi(argv[5]):0;
    mt19937_64 rng(seed); map<int,long long> tail; int best=1<<30; array<int,32> bh{}; string bd;
    for(long long n=0;n<N;n++){
      int k=1+(int)(rng()%30),a=1+(int)(rng()%31),b=(int)(rng()%32),t=useT?(int)(rng()%32):0;
      size_t oi=rng()%ords.size(),oo=rng()%ords.size();
      int h[32];
      for(int i=0;i<32;i++) h[i]=ords[oo].rank[F.mul((uint8_t)a,F.pw((uint8_t)(ords[oi].elem[i]^t),k))^b];
      int s=score32_cut(h,cut);
      if(s<=cut){tail[s]++; if(s<best){best=s;for(int i=0;i<32;i++)bh[i]=h[i];
        char buf[160];snprintf(buf,sizeof buf,"k=%d a=%d b=%d t=%d in=%zu out=%zu",k,a,b,t,oi,oo);bd=buf;}}
    }
    printf("FAMTAIL N=%lld seed=%llu cut=%d translate=%d best=%d %s\n",N,(unsigned long long)seed,cut,useT,best,bd.c_str());
    if(best<=cut){assert(isperm(bh.data()));assert(score32(bh.data())==best);
      printf("perm=");for(int x:bh)printf("%d ",x);printf("\n");}
    printf("tail_hist");for(auto&kv:tail)printf(" %d:%lld",kv.first,kv.second);printf("\n");
    return 0;
  }
  if (mode == "match") {
    long long N = atoll(argv[2]); uint64_t seed = strtoull(argv[3], nullptr, 10);
    mt19937_64 rng(seed);
    map<int, long long> hf, hr; set<array<int, 32>> canonf;
    long long famtested = 0;
    for (long long t = 0; t < N; t++) {
      int k = 1 + (int)(rng() % 30), a = 1 + (int)(rng() % 31), b = (int)(rng() % 32);
      size_t oi = rng() % ords.size(), oo = rng() % ords.size();
      int h[32];
      for (int i = 0; i < 32; i++) h[i] = ords[oo].rank[F.mul((uint8_t)a, F.pw(ords[oi].elem[i], k)) ^ b];
      assert(isperm(h)); famtested++;
      hf[score32(h)]++;
      if (canonf.size() < 4000000) canonf.insert(canon(h));
    }
    int r[32]; iota(r, r + 32, 0);
    for (long long t = 0; t < N; t++) { shuffle(r, r + 32, rng); hr[score32(r)]++; }
    printf("MATCH N=%lld seed=%llu family_distinct_D4_orbits=%zu\n", N, (unsigned long long)seed, canonf.size());
    auto dump = [&](const char* nm, map<int, long long>& h) {
      printf("%s_hist", nm); for (auto& kv : h) printf(" %d:%lld", kv.first, kv.second); printf("\n");
      long long tot = 0, acc = 0; double mean = 0;
      for (auto& kv : h) { tot += kv.second; mean += (double)kv.first * kv.second; }
      mean /= tot;
      double qs[] = {0.0001, 0.001, 0.01, 0.05, 0.25, 0.5};
      printf("%s_quantiles mean=%.3f", nm, mean);
      size_t qi = 0;
      for (auto& kv : h) { acc += kv.second;
        while (qi < 6 && (double)acc / tot >= qs[qi]) { printf(" p%g=%d", qs[qi] * 100, kv.first); qi++; } }
      printf("\n");
    };
    dump("family", hf); dump("random", hr);
    return 0;
  }
  return 1;
}
