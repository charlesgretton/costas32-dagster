// ============================================================================
// costas_rung.cpp  --  augmentation-rung search for order-32 Costas arrays
//
//   Given a catalogue of order-n Costas arrays (n < 32, k = 32 - n), enumerate
//   every order-32 permutation formed by
//        * deleting k columns C and k rows R from the 32x32 board,
//        * placing the order-n core in the surviving 28x28 compressed board,
//        * placing k extra dots as a bijection C -> R,
//   and report every configuration with Costas score <= THRESH.
//
//   A negative result at n = 28 states:
//       no order-32 Costas array contains any order-28 Costas array as an
//       order-preserving subpermutation obtained by deleting 4 rows and 4 columns.
//
// SOUNDNESS NOTES
//   * The k extra dots are a superset-free addition: the n core dots are a
//     subset of the 32, so a repeated displacement among them kills the whole
//     configuration.  That is the core-first prune and it is exact.
//   * --canonical restricts cores to one representative per dihedral orbit.
//     This is EXACT for existence and for the minimum score, because the whole
//     configuration space is D4-equivariant and the score is D4-invariant.
//     It is NOT exact for counting solutions; use --full for that.
//   * Every unit reports EXHAUSTED only if its whole core range completed.
//     Any other status must not be merged into an exhaustiveness claim.
//
// BUILD   g++ -O3 -march=native -std=c++17 costas_rung.cpp -o costas_rung
// ============================================================================
#include <algorithm>
#include <array>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <map>
#include <numeric>
#include <set>
#include <string>
#include <vector>
using namespace std;

typedef vector<int> Perm;

// ---------------------------------------------------------------- utilities
static bool is_perm(const Perm& p) {
  vector<char> s(p.size(), 0);
  for (int x : p) { if (x < 0 || x >= (int)p.size() || s[x]) return false; s[x] = 1; }
  return true;
}
static int costas_score(const Perm& p, int cut = 1 << 30) {
  int n = p.size(), s = 0;
  vector<uint64_t> u(n + 1, 0);
  for (int d = 1; d < n; d++) {
    uint64_t m = 0;
    for (int i = 0; i + d < n; i++) {
      unsigned e = (unsigned)(p[i + d] - p[i] + n - 1);
      s += (int)((m >> e) & 1ull); m |= 1ull << e;
    }
    if (s > cut) return cut + 1;
  }
  return s;
}
static Perm d4_image(const Perm& p, int g) {         // g in 0..7: (transpose?) x (hflip,vflip)
  int n = p.size(); Perm b = p;
  if (g & 4) { Perm inv(n); for (int i = 0; i < n; i++) inv[b[i]] = i; b = inv; }
  Perm c(n);
  for (int i = 0; i < n; i++) {
    int j = (g & 1) ? n - 1 - i : i;
    c[i] = (g & 2) ? n - 1 - b[j] : b[j];
  }
  return c;
}
static Perm canonical(const Perm& p) {
  Perm best = d4_image(p, 0);
  for (int g = 1; g < 8; g++) { Perm c = d4_image(p, g); if (c < best) best = c; }
  return best;
}
static uint64_t fnv1a(const string& s) {
  uint64_t h = 1469598103934665603ull;
  for (unsigned char c : s) { h ^= c; h *= 1099511628211ull; }
  return h;
}

// ------------------------------------------------- algebraic core generation
static vector<int> primitive_roots(int p) {
  vector<int> r;
  for (int g = 2; g < p; g++) { set<int> s; int x = 1;
    for (int i = 0; i < p - 1; i++) { x = x * g % p; s.insert(x); }
    if ((int)s.size() == p - 1) r.push_back(g); }
  return r;
}
// Welch W1(p,g,c): order p-1
static vector<Perm> welch(int p) {
  vector<Perm> out;
  for (int g : primitive_roots(p))
    for (int c = 0; c < p - 1; c++) {
      Perm h(p - 1); long long v = 1;
      for (int i = 0; i < c; i++) v = v * g % p;
      for (int i = 0; i < p - 1; i++) { v = v * g % p; h[i] = (int)v - 1; }
      out.push_back(h);
    }
  return out;
}
static uint8_t gf32_mul(uint8_t a, uint8_t b) {      // GF(2^5), x^5+x^2+1
  uint8_t r = 0;
  for (int s = 0; s < 5; s++) { if (b & 1) r ^= a; b >>= 1;
    bool c = a & 0x10; a = (uint8_t)((a << 1) & 0x1f); if (c) a ^= 0x05; }
  return r & 0x1f;
}
// Golomb G2(q,a,b): a^i + b^j = 1, order q-2.  q = 31 (prime) or 32 (GF(2^5)).
static vector<Perm> golomb_prime(int p) {
  vector<Perm> out; auto pr = primitive_roots(p);
  for (int a : pr) for (int b : pr) {
    Perm h(p - 2); bool ok = true;
    for (int i = 1; i <= p - 2 && ok; i++) {
      long long ai = 1; for (int e = 0; e < i; e++) ai = ai * a % p;
      long long t = (1 - ai % p + p) % p; if (!t) { ok = false; break; }
      int j = -1; long long bj = 1;
      for (int e = 1; e <= p - 2; e++) { bj = bj * b % p; if (bj == t) { j = e; break; } }
      if (j < 0) { ok = false; break; } h[i - 1] = j - 1;
    }
    if (ok && is_perm(h) && costas_score(h) == 0) out.push_back(h);
  }
  return out;
}
static vector<Perm> golomb_gf32() {
  vector<Perm> out; uint8_t ex[31]; int lg[32]; memset(lg, -1, sizeof lg);
  uint8_t x = 1; for (int i = 0; i < 31; i++) { ex[i] = x; lg[x] = i; x = gf32_mul(x, 2); }
  for (uint8_t a = 2; a < 32; a++) for (uint8_t b = 2; b < 32; b++) {
    Perm h(30); bool ok = true; long long inv = 1, lb = lg[b];
    for (int e = 0; e < 29; e++) inv = inv * lb % 31;
    for (int i = 1; i <= 30 && ok; i++) {
      uint8_t ai = ex[(lg[a] * i) % 31], t = ai ^ 1;
      if (!t) { ok = false; break; }
      int j = (int)((long long)lg[t] * inv % 31);
      if (j < 1 || j > 30) { ok = false; break; } h[i - 1] = j - 1;
    }
    if (ok && is_perm(h) && costas_score(h) == 0) out.push_back(h);
  }
  return out;
}
// every corner ADDITION that stays Costas is a Costas array one order larger.
// This is the step the first version was missing: G2(29) has order q-2 = 27 and
// only reaches order 28 upwards, so a downward-only closure cannot see it.
static vector<Perm> corner_additions(const Perm& p) {
  int n = p.size(); vector<Perm> out;
  for (int c : {0, n}) for (int r : {0, n}) {
    Perm q; q.reserve(n + 1);
    for (int i = 0; i <= n; i++) {
      if (i == c) q.push_back(r);
      else { int v = (i > c) ? p[i - 1] : p[i]; q.push_back(v >= r ? v + 1 : v); }
    }
    if (is_perm(q) && costas_score(q) == 0) out.push_back(q);
  }
  return out;
}

// every corner deletion of a Costas array is a Costas array one order smaller
static vector<Perm> corner_deletions(const Perm& p) {
  int n = p.size(); vector<Perm> out;
  for (int corner = 0; corner < 4; corner++) {
    int ci = (corner & 1) ? n - 1 : 0, want = (corner & 2) ? n - 1 : 0;
    if (p[ci] != want) continue;
    Perm q; q.reserve(n - 1);
    for (int i = 0; i < n; i++) { if (i == ci) continue; q.push_back(p[i] > want ? p[i] - 1 : p[i]); }
    if (costas_score(q) == 0) out.push_back(q);
  }
  return out;
}
// Build every algebraically reachable Costas array of the requested order by
// taking the direct constructions available near order 32 and closing downward
// under corner deletion.  Then close under the dihedral group.
static vector<Perm> generate_cores(int order) {
  map<int, set<Perm>> by;
  auto add = [&](const Perm& p) -> bool {
    if ((int)p.size() < 26 || (int)p.size() > 31) return false;
    if (costas_score(p) != 0) return false;
    auto& s = by[(int)p.size()];
    bool nw = false;
    for (int g = 0; g < 8; g++) if (s.insert(d4_image(p, g)).second) nw = true;
    return nw;
  };
  for (auto& p : welch(29)) add(p);            // order 28
  for (auto& p : welch(31)) add(p);            // order 30
  for (auto& p : golomb_prime(29)) add(p);     // order 27
  for (auto& p : golomb_prime(31)) add(p);     // order 29
  for (auto& p : golomb_gf32()) add(p);        // order 30
  for (int it = 0; it < 8; it++) {
    int added = 0;
    map<int, set<Perm>> snap = by;
    for (auto& kv : snap)
      for (auto& p : kv.second) {
        for (auto& q : corner_deletions(p)) if (add(q)) added++;
        for (auto& q : corner_additions(p)) if (add(q)) added++;
      }
    if (!added) break;
  }
  return vector<Perm>(by[order].begin(), by[order].end());
}

// ---------------------------------------------------------------- the sweep
struct Combos { int k, n, B; vector<uint8_t> del, surv; size_t count; };
static Combos build_combos(int k, int B) {
  Combos C; C.k = k; C.B = B; C.n = B - k; C.count = 0;
  vector<int> idx(k); iota(idx.begin(), idx.end(), 0);
  while (true) {
    for (int t = 0; t < k; t++) C.del.push_back((uint8_t)idx[t]);
    for (int x = 0, t = 0; x < B; x++) { bool d = false;
      for (int u = 0; u < k; u++) if (idx[u] == x) d = true;
      if (!d) { C.surv.push_back((uint8_t)x); t++; } }
    C.count++;
    int i = k - 1; while (i >= 0 && idx[i] == B - k + i) i--;
    if (i < 0) break; idx[i]++; for (int j = i + 1; j < k; j++) idx[j] = idx[j-1] + 1;
  }
  return C;
}

struct Result {
  string status = "INCOMPLETE";
  long long placements = 0, survivors = 0, configs = 0, costas = 0;
  vector<long long> hist;
  vector<string> low;        // full record of every configuration at or below THRESH
  int best = 1 << 30;
};

static Result sweep(const vector<Perm>& cores, int coreLo, int coreHi,
                    const Combos& CB, int THRESH, double timeLimit, bool prune = true) {
  const int n = CB.n, k = CB.k, B = CB.B;
  Result R; R.hist.assign(THRESH + 1, 0);
  vector<array<int, 8>> matchings;   // k! bijections C -> R
  { vector<int> m(k); iota(m.begin(), m.end(), 0);
    do { array<int, 8> a{}; for (int i = 0; i < k; i++) a[i] = m[i]; matchings.push_back(a); }
    while (next_permutation(m.begin(), m.end())); }

  const int P = n * (n - 1) / 2;
  vector<int> pa(P), pb(P), pd(P), ra(P), rb(P);
  vector<int> bucket(33), tmpa(P), tmpb(P), tmpd(P);
  static uint32_t stamp[32][64]; static uint32_t gen = 0;
  memset(stamp, 0, sizeof stamp);
  int h[32];
  const unsigned OFF = (unsigned)(B - 1);
  auto t0 = chrono::steady_clock::now();

  for (int ci = coreLo; ci < coreHi; ci++) {
    if (timeLimit > 0 &&
        chrono::duration<double>(chrono::steady_clock::now() - t0).count() > timeLimit) {
      R.status = "TIME_LIMIT"; return R;
    }
    const Perm& K = cores[ci];
    for (size_t cc = 0; cc < CB.count; cc++) {
      const uint8_t* cols = &CB.surv[cc * n];
      const uint8_t* dcol = &CB.del[cc * k];
      // pair list bucketed by column displacement (ascending): short distances
      // carry the most pairs and collide first, which shortens the abort path
      int m = 0;
      for (int a = 0; a < n; a++) for (int b = a + 1; b < n; b++) {
        tmpa[m] = a; tmpb[m] = b; tmpd[m] = cols[b] - cols[a]; m++; }
      fill(bucket.begin(), bucket.end(), 0);
      for (int i = 0; i < P; i++) bucket[tmpd[i]]++;
      { int run = 0; for (int d = 1; d <= 32; d++) { int c = bucket[d]; bucket[d] = run; run += c; } }
      for (int i = 0; i < P; i++) { int q = bucket[tmpd[i]]++;
        pa[q] = tmpa[i]; pb[q] = tmpb[i]; pd[q] = tmpd[i];
        ra[q] = K[tmpa[i]]; rb[q] = K[tmpb[i]]; }

      for (size_t rr = 0; rr < CB.count; rr++) {
        const uint8_t* rows = &CB.surv[rr * n];
        const uint8_t* drow = &CB.del[rr * k];
        R.placements++;
        if (++gen == 0) { memset(stamp, 0, sizeof stamp); gen = 1; }
        bool ok = true;
        for (int i = 0; i < P; i++) {
          int d = pd[i]; unsigned e = (unsigned)(rows[rb[i]] - rows[ra[i]] + OFF);
          if (stamp[d][e] == gen) { ok = false; break; }
          stamp[d][e] = gen;
        }
        if (!ok && prune) continue;
        if (ok) R.survivors++;
        for (int t = 0; t < n; t++) h[cols[t]] = rows[K[t]];
        for (auto& mm : matchings) {
          for (int j = 0; j < k; j++) h[dcol[j]] = drow[mm[j]];
          R.configs++;
          int s = 0; uint64_t u[32]; memset(u, 0, sizeof u);
          for (int d = 1; d < B && s <= THRESH; d++)
            for (int i = 0; i + d < B; i++) {
              unsigned e = (unsigned)(h[i + d] - h[i] + OFF);
              s += (int)((u[d] >> e) & 1ull); u[d] |= 1ull << e; }
          if (s > THRESH) continue;
          R.hist[s]++; if (s < R.best) R.best = s; if (s == 0) R.costas++;
          char buf[400]; int o = snprintf(buf, sizeof buf,
            "LOW score=%d core=%d delC=", s, ci);
          for (int j = 0; j < k; j++) o += snprintf(buf+o, sizeof buf-o, "%d%s", dcol[j], j+1<k?",":"");
          o += snprintf(buf+o, sizeof buf-o, " delR=");
          for (int j = 0; j < k; j++) o += snprintf(buf+o, sizeof buf-o, "%d%s", drow[j], j+1<k?",":"");
          o += snprintf(buf+o, sizeof buf-o, " perm=");
          for (int q = 0; q < B; q++) o += snprintf(buf+o, sizeof buf-o, "%d%s", h[q], q<B-1?" ":"");
          R.low.push_back(buf);
        }
      }
    }
  }
  R.status = "EXHAUSTED";
  return R;
}

// ------------------------------------------------------------------- driver
static void usage() {
  printf(
"usage:\n"
"  costas_rung selftest\n"
"      regenerate the algebraic order-30 cores and reproduce the published\n"
"      k=1 and k=2 rungs.  Run this before trusting any long job.\n"
"  costas_rung cat <order> [outfile]\n"
"      generate and validate the algebraic catalogue for that order\n"
"  costas_rung run <order> <catalogue|-> <unit> <nunits> [--full] [--thresh N] [--time S]\n"
"      sweep one work unit; '-' for the catalogue means generate it internally\n");
}

static vector<Perm> load_catalogue(const string& path, int order, uint64_t& hash) {
  ifstream f(path); if (!f) { fprintf(stderr, "cannot open %s\n", path.c_str()); exit(2); }
  string all((istreambuf_iterator<char>(f)), istreambuf_iterator<char>());
  hash = fnv1a(all);
  vector<Perm> out; size_t pos = 0;
  while (pos < all.size()) {
    size_t e = all.find('\n', pos); if (e == string::npos) e = all.size();
    string ln = all.substr(pos, e - pos); pos = e + 1;
    Perm p; const char* s = ln.c_str(); char* q;
    for (long v = strtol(s, &q, 10); q != s; s = q, v = strtol(s, &q, 10)) p.push_back((int)v);
    if ((int)p.size() == order) out.push_back(p);
  }
  return out;
}

static void validate(vector<Perm>& cat, int order, bool canonical_only) {
  size_t raw = cat.size();
  for (auto& p : cat) {
    if ((int)p.size() != order || !is_perm(p)) { fprintf(stderr, "bad entry in catalogue\n"); exit(3); }
    if (costas_score(p) != 0)                  { fprintf(stderr, "entry is not Costas\n");   exit(3); }
  }
  set<Perm> S(cat.begin(), cat.end());
  set<Perm> orb; for (auto& p : S) orb.insert(canonical(p));
  printf("CATALOGUE order=%d entries=%zu distinct=%zu d4_orbits=%zu all_score_zero=yes\n",
         order, raw, S.size(), orb.size());
  bool closed = true;
  for (auto& p : S) for (int g = 0; g < 8; g++) if (!S.count(d4_image(p, g))) closed = false;
  printf("CATALOGUE d4_closed=%s\n", closed ? "yes" : "no");
  { // published census invariants (arrays counted with all symmetry images, and
    // inequivalent arrays under the dihedral group, OEIS A001441)
    static const map<int, pair<int,int>> census = {
      {24,{200,25}}, {25,{88,12}}, {26,{56,8}}, {27,{204,29}}, {28,{712,89}}, {29,{164,23}} };
    auto it = census.find(order);
    if (it != census.end()) {
      int ea = it->second.first, eo = it->second.second;
      bool okA = (int)S.size() == ea, okO = (int)orb.size() == eo;
      printf("CENSUS expected arrays=%d orbits=%d  -> arrays=%s orbits=%s\n",
             ea, eo, okA ? "MATCH" : "MISMATCH", okO ? "MATCH" : "MISMATCH");
      if (!okA || !okO)
        printf("CENSUS WARNING: this catalogue is INCOMPLETE. A negative result is then\n"
               "                only a statement about the arrays actually supplied.\n"
               "                Supply the published order-%d catalogue for a complete claim.\n", order);
    } }
  if (canonical_only) { cat.assign(orb.begin(), orb.end());
    printf("CATALOGUE using %zu canonical representatives (exact for existence and minimum)\n", cat.size()); }
  else { cat.assign(S.begin(), S.end());
    printf("CATALOGUE using all %zu distinct arrays\n", cat.size()); }
}

int main(int argc, char** argv) {
  if (argc < 2) { usage(); return 1; }
  string mode = argv[1];

  if (mode == "selftest") {
    vector<Perm> c30 = generate_cores(30);
    printf("selftest: algebraic order-30 cores after dihedral closure = %zu (expected 664)\n", c30.size());
    if (c30.size() != 664) { printf("SELFTEST FAIL\n"); return 4; }
    for (int k = 1; k <= 2; k++) {
      Combos CB = build_combos(k, 30 + k);
      Result R = sweep(c30, 0, c30.size(), CB, 6, 0);
      printf("selftest k=%d order=%d: configs=%lld costas=%lld best=%d hist=",
             k, 32 - k, R.configs, R.costas, R.best);
      for (int i = 0; i <= 6; i++) printf(" %d:%lld", i, R.hist[i]);
      printf("\n");
      if (k == 1 && !(R.costas == 8 && R.best == 0)) { printf("SELFTEST FAIL (k=1)\n"); return 4; }
      if (k == 2 && !(R.costas == 0 && R.best == 2 && R.hist[2] == 8)) { printf("SELFTEST FAIL (k=2)\n"); return 4; }
    }
    printf("SELFTEST PASS\n"); return 0;
  }

  if (mode == "cat") {
    int order = atoi(argv[2]);
    vector<Perm> cat = generate_cores(order);
    printf("generated %zu arrays of order %d\n", cat.size(), order);
    validate(cat, order, false);
    if (argc > 3) { ofstream f(argv[3]);
      for (auto& p : cat) { for (size_t i = 0; i < p.size(); i++) f << p[i] << (i + 1 < p.size() ? ' ' : '\n'); }
      printf("written to %s\n", argv[3]); }
    return 0;
  }

  if (mode == "run") {
    int order = atoi(argv[2]); string catpath = argv[3];
    int unit = atoi(argv[4]), nunits = atoi(argv[5]);
    bool canon = true; int thresh = 12; double tl = 0; bool prune = true;
    for (int i = 6; i < argc; i++) { string a = argv[i];
      if (a == "--full") canon = false;
      else if (a == "--thresh") thresh = atoi(argv[++i]);
      else if (a == "--time") tl = atof(argv[++i]);
      else if (a == "--no-prune") prune = false; }
    uint64_t hash = 0; vector<Perm> cat;
    if (catpath == "-") { cat = generate_cores(order);
      string s; for (auto& p : cat) for (int x : p) s += to_string(x) + " ";
      hash = fnv1a(s); printf("CATALOGUE source=generated\n"); }
    else { cat = load_catalogue(catpath, order, hash); printf("CATALOGUE source=%s\n", catpath.c_str()); }
    validate(cat, order, canon);
    int k = 32 - order; Combos CB = build_combos(k, 32);
    int lo = (int)((long long)cat.size() * unit / nunits);
    int hi = (int)((long long)cat.size() * (unit + 1) / nunits);
    printf("RUNG order=%d k=%d mode=%s cores=%zu catalogue_hash=%016llx unit=%d/%d core_range=[%d,%d) thresh=%d\n",
           order, k, canon ? "canonical" : "full", cat.size(),
           (unsigned long long)hash, unit, nunits, lo, hi, thresh);
    fflush(stdout);
    auto t0 = chrono::steady_clock::now();
    Result R = sweep(cat, lo, hi, CB, thresh, tl, prune);
    double el = chrono::duration<double>(chrono::steady_clock::now() - t0).count();
    printf("STATUS %s\n", R.status.c_str());
    printf("COUNTS placements=%lld survivors=%lld configs=%lld costas=%lld elapsed=%.1f\n",
           R.placements, R.survivors, R.configs, R.costas, el);
    printf("HIST"); for (int i = 0; i <= thresh; i++) printf(" %d:%lld", i, R.hist[i]); printf("\n");
    printf("BEST_CORE_INTACT %d   (core-first pruning makes score 0 exact; the\n"
           "                        histogram above score 0 counts only configurations\n"
           "                        whose core carries no repeated displacement)\n",
           R.best > thresh ? -1 : R.best);
    for (auto& s : R.low) printf("%s\n", s.c_str());
    printf("END unit=%d\n", unit);
    return R.status == "EXHAUSTED" ? 0 : 10;
  }
  usage(); return 1;
}
