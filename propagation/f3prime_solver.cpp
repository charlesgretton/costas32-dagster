// f3prime_solver.cpp -- F3': does L_3+T_m reduce the tree of an exact search?
//
// ONE solver, three propagation configurations selected by flag. Every
// non-propagation choice is identical across modes: branching order (columns
// left to right), value order (ascending), no symmetry breaking, no restarts,
// single thread, same incremental displacement check.
//
//   --prop inc    incremental Costas check only            (I)
//   --prop l3     I + unary filter, arc consistency,
//                 Hall matching, singleton shaving         (I + L_3)
//   --prop l3tm   I + L_3 + the T_m interval rule          (I + L_3 + T_m)
//
// RA is omitted from the candidate: on every tested leading-prefix benchmark it
// contributed no detections beyond L_3. That conclusion is benchmark-scoped.
//
// Schedule, declared a priori and NOT tuned: the propagator runs at a node when
// the number of free positions U satisfies U <= UMAX (default 8). Above that the
// domains are too wide to prune and the propagator is expensive; below it the
// remaining subtree is small. No per-order tuning was performed.
//
// Primary metric is entered search nodes, deterministic under fixed branching.
// Secondary: declared propagation work, wall time.
//
// Solution-set identity. --emit FILE writes every solution in canonical form,
// one per line; sorting and comparing those files byte for byte establishes set
// equality outright. The two order-independent 64-bit hashes are retained as a
// fast regression guard, but aggregate hashes are not collision-free
// certificates of set equality, so the claim rests on the exact comparison.
//
// build: g++ -O3 -march=native -std=c++17 f3prime_solver.cpp -o f3prime_solver
// run:   ./f3prime_solver --order 13 --prop l3tm
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <algorithm>
#include <chrono>
using namespace std;

static int n = 12, UMAX = 8, mode = 0;          // 0=inc 1=l3 2=l3tm
static int p[24];
static unsigned used;
static unsigned dmask[32];
static long long nodes = 0, propCalls = 0, workL3 = 0, workTM = 0;
static long long pruneL3 = 0, pruneTM = 0, solutions = 0, leaves = 0;
static unsigned long long hashXor = 0, hashSum = 0;
static FILE* emitF = nullptr;

static inline bool placeOK(int c, int r) {
    for (int i = 0; i < c; i++) { int d = c - i, v = r - p[i] + n; if (dmask[d] >> v & 1) return false; }
    return true;
}
static inline void doPlace(int c, int r) { for (int i = 0; i < c; i++) dmask[c - i] |= 1u << (r - p[i] + n); }
static inline void unPlace(int c, int r) { for (int i = 0; i < c; i++) dmask[c - i] &= ~(1u << (r - p[i] + n)); }

static int mt[40];
static bool aug(const vector<unsigned>& D, int u, unsigned& seen, int K) {
    for (int k = 0; k < K; k++) {
        if (!(D[u] >> k & 1)) continue;
        if (seen >> k & 1) continue;
        seen |= 1u << k;
        if (mt[k] < 0 || aug(D, mt[k], seen, K)) { mt[k] = u; return true; }
    }
    return false;
}
static bool match(const vector<unsigned>& D, int K) {
    memset(mt, -1, sizeof(mt));
    for (size_t u = 0; u < D.size(); u++) { unsigned seen = 0; workL3++; if (!aug(D, (int)u, seen, K)) return false; }
    return true;
}
static bool acFilter(vector<unsigned>& D, const vector<int>& R, const vector<int>& pos) {
    int U = pos.size(), K = R.size();
    bool ch = true;
    while (ch) {
        ch = false;
        for (int u = 0; u < U; u++) for (int w = 0; w < U; w++) {
            if (u == w) continue; int d = pos[w] - pos[u]; if (d <= 0) continue;
            unsigned nd = 0;
            for (int k = 0; k < K; k++) {
                if (!(D[u] >> k & 1)) continue; bool sup = false;
                for (int l = 0; l < K; l++) {
                    if (l == k || !(D[w] >> l & 1)) continue;
                    workL3++;
                    if (!(dmask[d] >> (R[l] - R[k] + n) & 1)) { sup = true; break; }
                }
                if (sup) nd |= 1u << k;
            }
            if (nd != D[u]) { D[u] = nd; ch = true; if (!nd) return false; }
        }
    }
    return true;
}
// returns true if infeasible; fills D with the shaved domains when feasible
static bool l3Detect(int s, const vector<int>& R, const vector<int>& pos, vector<unsigned>& D) {
    int U = pos.size(), K = R.size();
    D.assign(U, 0);
    for (int u = 0; u < U; u++) {
        unsigned nd = 0;
        for (int k = 0; k < K; k++) {
            int r = R[k]; bool ok = true;
            for (int a = 0; a < s; a++) { workL3++; if (dmask[pos[u] - a] >> (r - p[a] + n) & 1) { ok = false; break; } }
            if (ok) nd |= 1u << k;
        }
        D[u] = nd; if (!nd) return true;
    }
    if (!acFilter(D, R, pos)) return true;
    if (!match(D, K)) return true;
    bool ch = true;
    while (ch) {
        ch = false;
        for (int u = 0; u < U; u++) for (int k = 0; k < K; k++) {
            if (!(D[u] >> k & 1)) continue;
            vector<unsigned> T = D; T[u] = 1u << k;
            if (!acFilter(T, R, pos) || !match(T, K)) {
                D[u] &= ~(1u << k); ch = true;
                if (!D[u]) return true;
            }
        }
    }
    return false;
}
static bool tmDetect(int s, const vector<int>& R, const vector<unsigned>& D) {
    int K = R.size();
    vector<int> Rs = R; sort(Rs.begin(), Rs.end());
    vector<long long> lo(K + 1, 0), hi(K + 1, 0);
    for (int k = 1; k <= K; k++) { lo[k] = lo[k - 1] + Rs[k - 1]; hi[k] = hi[k - 1] + Rs[K - k]; }
    long long pre[24]; pre[0] = 0; for (int i = 0; i < s; i++) pre[i + 1] = pre[i] + p[i];
    for (int m = 1; m < n; m++) {
        long long det = 0; vector<int> pool; int ku = 0;
        for (int i = 0; i + m < n; i++) {
            int a = i, b = i + m;
            if (a < s && b < s) { det += p[b] - p[a]; continue; }
            ku++;
            if (a < s) { int u = b - s; for (int k = 0; k < K; k++) { workTM++; if (D[u] >> k & 1) pool.push_back(R[k] - p[a]); } }
            else { int u = a - s, w = b - s;
                   for (int k = 0; k < K; k++) if (D[u] >> k & 1)
                       for (int l = 0; l < K; l++) { workTM++; if (l != k && (D[w] >> l & 1)) pool.push_back(R[l] - R[k]); } }
        }
        if (!ku) continue;
        sort(pool.begin(), pool.end()); pool.erase(unique(pool.begin(), pool.end()), pool.end());
        if ((int)pool.size() < ku) return true;
        long long slo = det, shi = det;
        for (int i = 0; i < ku; i++) { slo += pool[i]; shi += pool[pool.size() - 1 - i]; }
        int fk = min(m, s), fR = m - fk, lk = max(0, s - (n - m)), lR = m - lk;
        if (fR < 0 || lR < 0 || fR > K || lR > K) continue;
        long long lks = 0; for (int i = max(0, n - m); i < s; i++) lks += p[i];
        long long tlo = (lks + lo[lR]) - (pre[fk] + hi[fR]);
        long long thi = (lks + hi[lR]) - (pre[fk] + lo[fR]);
        workTM++;
        if (shi < tlo || slo > thi) return true;
    }
    return false;
}

static void record() {
    unsigned long long h = 1469598103934665603ULL;
    for (int i = 0; i < n; i++) { h ^= (unsigned long long)p[i]; h *= 1099511628211ULL; }
    hashXor ^= h; hashSum += h; solutions++;
    if (emitF) { for (int i = 0; i < n; i++) fprintf(emitF, "%02d%c", p[i], i + 1 == n ? '\n' : ' '); }
}

static void dfs(int c) {
    nodes++;
    if (c == n) { leaves++; record(); return; }
    int U = n - c;
    if (mode > 0 && U <= UMAX && c > 0) {
        propCalls++;
        vector<int> R, pos;
        for (int r = 0; r < n; r++) if (!(used >> r & 1)) R.push_back(r);
        for (int b = c; b < n; b++) pos.push_back(b);
        vector<unsigned> D;
        if (l3Detect(c, R, pos, D)) { pruneL3++; return; }
        if (mode == 2 && tmDetect(c, R, D)) { pruneTM++; return; }
    }
    for (int r = 0; r < n; r++) {
        if (used >> r & 1) continue;
        if (!placeOK(c, r)) continue;
        p[c] = r; used |= 1u << r; doPlace(c, r);
        dfs(c + 1);
        used &= ~(1u << r); unPlace(c, r);
    }
}

int main(int argc, char** argv) {
    const char* pm = "inc";
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--order")) n = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--prop")) pm = argv[++i];
        else if (!strcmp(argv[i], "--schedule")) UMAX = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--emit")) emitF = fopen(argv[++i], "w");
    }
    if (!strcmp(pm, "inc")) mode = 0;
    else if (!strcmp(pm, "l3")) mode = 1;
    else if (!strcmp(pm, "l3tm")) mode = 2;
    else { fprintf(stderr, "unknown propagator %s\n", pm); return 2; }
    auto t0 = chrono::steady_clock::now();
    dfs(0);
    if (emitF) fclose(emitF);
    double el = chrono::duration<double>(chrono::steady_clock::now() - t0).count();
    printf("{\"order\":%d,\"propagator\":\"%s\",\"schedule_umax\":%d,"
           "\"solutions\":%lld,\"nodes\":%lld,\"leaves\":%lld,"
           "\"prop_calls\":%lld,\"work_l3\":%lld,\"work_tm\":%lld,"
           "\"prunes_l3\":%lld,\"prunes_tm\":%lld,"
           "\"hash_xor\":\"%016llx\",\"hash_sum\":\"%016llx\",\"wall_seconds\":%.3f}\n",
           n, pm, UMAX, solutions, nodes, leaves, propCalls, workL3, workTM,
           pruneL3, pruneTM, hashXor, hashSum, el);
    return 0;
}
