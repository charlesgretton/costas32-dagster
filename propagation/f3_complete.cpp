// f3_complete.cpp -- F3 under the full protocol.
//
// Benchmark  B_{n,s} : every Costas-valid s-leading-column prefix at order n,
//                      labelled by exhaustive completion search.
//
// Baselines (run independently, detection sets retained):
//   RA  relation-algebra closure. Relations R_{ij} are masks of possible values
//       of h_j - h_i over {-(n-1)..n-1}\{0}. Path consistency uses sumset
//       composition R_{ik} &= R_{ij} (+) R_{jk}, iterated to fixpoint. An empty
//       relation proves infeasibility.
//   L3  position-value domains: unary filter, arc consistency on binary
//       prefix-conflict constraints, perfect-matching (Hall) test, singleton
//       shaving.
//   D_B = D_RA union D_L3.
//
// Candidate:
//   T   D_B plus the T_m coupling. sum_i D_{m,i} = T_m = (sum of last m)
//       - (sum of first m), an identity giving T_m = T_{n-m} free. The
//       achievable ranges of the two sides must intersect. By construction
//       D_B is a subset of D_T, so the gate reduces to marginal coverage.
//
// Gate (frozen before this run, preserving the original effect size of
// (106-96)/96 = 10.4167%):
//       |D_T| >= ceil(1.104167 * |D_B|),  false positives = 0,
//       cost(T)/cost(B) <= 2 on the declared primary metric.
//
// Primary cost metric: declared deterministic propagation-work counter.
// The counter instruments selected relation initialisations, sumset shifts,
// support tests, matching calls, domain scans and interval tests. It is NOT an
// instruction count nor a complete count of primitive mask operations.
// Wall-clock is reported as a secondary practical measure.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <algorithm>
#include <chrono>
using namespace std;

static int n = 12, s = 6;
static int p[20];
static unsigned used;
static unsigned dmask[24];
static long long workRA = 0, workL3 = 0, workTM = 0;

static inline bool placeOK(int c, int r) {
    for (int i = 0; i < c; i++) { int d = c - i, v = r - p[i] + n; if (dmask[d] >> v & 1) return false; }
    return true;
}
static inline void doPlace(int c, int r) { for (int i = 0; i < c; i++) dmask[c - i] |= 1u << (r - p[i] + n); }
static inline void unPlace(int c, int r) { for (int i = 0; i < c; i++) dmask[c - i] &= ~(1u << (r - p[i] + n)); }
static bool complete(int c) {
    if (c == n) return true;
    for (int r = 0; r < n; r++) {
        if (used >> r & 1) continue;
        if (!placeOK(c, r)) continue;
        p[c] = r; used |= 1u << r; doPlace(c, r);
        if (complete(c + 1)) { used &= ~(1u << r); unPlace(c, r); return true; }
        used &= ~(1u << r); unPlace(c, r);
    }
    return false;
}

// ---------------- RA: path consistency on difference relations
static unsigned Rel[20][20];
static inline unsigned sumset(unsigned A, unsigned B) {
    unsigned out = 0; int W = 2 * n;
    for (int ka = 0; ka <= W; ka++) {
        if (!(A >> ka & 1)) continue;
        int sh = ka - n;
        out |= (sh >= 0) ? (B << sh) : (B >> (-sh));
        workRA++;
    }
    return out & ((1u << (W + 1)) - 1);
}
static bool raClosure(const vector<int>& R) {
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++) {
            unsigned m = 0; int d = j - i;
            if (i < s && j < s) {
                m = 1u << (p[j] - p[i] + n);       // fixed pair: its own difference
            } else {                               // at least one endpoint free:
                if (i < s) { for (int r : R) m |= 1u << (r - p[i] + n); }
                else       { for (int a : R) for (int b : R) if (a != b) m |= 1u << (b - a + n); }
                m &= ~dmask[d];                    // must avoid differences the prefix already used
            }
            m &= ~(1u << n);                       // difference 0 impossible
            Rel[i][j] = m; workRA++;
            if (!m) return false;
        }
    bool ch = true;
    while (ch) {
        ch = false;
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++)
                for (int k = j + 1; k < n; k++) {
                    unsigned c = sumset(Rel[i][j], Rel[j][k]) & Rel[i][k];
                    workRA++;
                    if (c != Rel[i][k]) { Rel[i][k] = c; ch = true; if (!c) return false; }
                }
    }
    return true;
}

// ---------------- L3: position-value domains
static int mt[32];
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
static bool l3Detect(const vector<int>& R, const vector<int>& pos, vector<unsigned>& Dout) {
    int U = pos.size(), K = R.size();
    vector<unsigned> D(U, 0);
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
    Dout = D; return false;
}

// ---------------- T_m coupling
static bool tmDetect(const vector<int>& R, const vector<unsigned>& D) {
    int K = R.size();
    vector<int> Rs = R; sort(Rs.begin(), Rs.end());
    vector<long long> lo(K + 1, 0), hi(K + 1, 0);
    for (int k = 1; k <= K; k++) { lo[k] = lo[k - 1] + Rs[k - 1]; hi[k] = hi[k - 1] + Rs[K - k]; }
    int pre[20]; pre[0] = 0; for (int i = 0; i < s; i++) pre[i + 1] = pre[i] + p[i];
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


// ---------------- cpp_matches_reference: literal transcription of Reference.lean
// Independent of the production path above: builds pools as lists exactly as
// refFixedFreePool / refFreeFreePool specify, deduplicates by first occurrence
// as dedupInt does, sorts, and forms refLowerK / refUpperK. Compared against
// tmDetect on every configuration of the complete population.
static long long g_cmp = 0, g_mismatch = 0;

static vector<long long> refDedup(const vector<long long>& xs) {   // dedupInt
    vector<long long> out;
    for (size_t i = 0; i < xs.size(); i++) {
        bool later = false;
        for (size_t j = i + 1; j < xs.size(); j++) if (xs[j] == xs[i]) { later = true; break; }
        if (!later) out.push_back(xs[i]);
    }
    return out;
}
// returns true if the reference rule detects infeasibility
static bool tmDetectRef(const vector<int>& R, const vector<unsigned>& D) {
    int K = (int)R.size();
    vector<long long> Rs(R.begin(), R.end());
    sort(Rs.begin(), Rs.end());
    vector<long long> lo(K + 1, 0), hi(K + 1, 0);
    for (int k = 1; k <= K; k++) { lo[k] = lo[k-1] + Rs[k-1]; hi[k] = hi[k-1] + Rs[K-k]; }
    long long pre[24]; pre[0] = 0; for (int i = 0; i < s; i++) pre[i+1] = pre[i] + p[i];
    for (int m = 1; m < n; m++) {
        long long det = 0; int ku = 0;
        vector<long long> pool;
        for (int i = 0; i + m < n; i++) {
            int a = i, b = i + m;
            if (a < s && b < s) { det += p[b] - p[a]; continue; }
            ku++;
            if (a < s) {                                   // refFixedFreePool
                int u = b - s;
                for (int k = 0; k < K; k++) if (D[u] >> k & 1) pool.push_back((long long)R[k] - p[a]);
            } else {                                       // refFreeFreePool
                int u = a - s, w = b - s;
                for (int k = 0; k < K; k++) if (D[u] >> k & 1)
                    for (int l = 0; l < K; l++) if (l != k && (D[w] >> l & 1))
                        pool.push_back((long long)R[l] - (long long)R[k]);
            }
        }
        if (!ku) continue;
        vector<long long> dd = refDedup(pool);
        sort(dd.begin(), dd.end());
        if ((int)dd.size() < ku) return true;
        long long slo = det, shi = det;                    // refLowerK / refUpperK
        for (int i = 0; i < ku; i++) { slo += dd[i]; shi += dd[dd.size()-1-i]; }
        int fk = min(m, s), fR = m - fk, lk = max(0, s - (n - m)), lR = m - lk;
        if (fR < 0 || lR < 0 || fR > K || lR > K) continue;
        long long lks = 0; for (int i = max(0, n - m); i < s; i++) lks += p[i];
        long long tlo = (lks + lo[lR]) - (pre[fk] + hi[fR]);
        long long thi = (lks + hi[lR]) - (pre[fk] + lo[fR]);
        if (shi < tlo || slo > thi) return true;            // refDisjoint
    }
    return false;
}

long long nV = 0, nI = 0, nF = 0;
long long dRA = 0, dL3 = 0, dBoth = 0, dB = 0, dT = 0, dNew = 0;
long long fRA = 0, fL3 = 0, fT = 0;

static void gen(int c) {
    if (c == s) {
        nV++;
        vector<int> R, pos;
        for (int r = 0; r < n; r++) if (!(used >> r & 1)) R.push_back(r);
        for (int b = s; b < n; b++) pos.push_back(b);
        bool ra = !raClosure(R);
        vector<unsigned> D;
        bool l3 = l3Detect(R, pos, D);
        bool b = ra || l3;
        bool t = b;
        bool tmProd = false;
        if (!b) { tmProd = tmDetect(R, D);
                  bool tmRef = tmDetectRef(R, D);
                  g_cmp++; if (tmProd != tmRef) g_mismatch++;
                  t = tmProd; }
        unsigned su = used; unsigned sd[24]; memcpy(sd, dmask, sizeof(dmask));
        bool feas = complete(s);
        used = su; memcpy(dmask, sd, sizeof(dmask));
        if (feas) { nF++; fRA += ra; fL3 += l3; fT += t; }
        else { nI++; dRA += ra; dL3 += l3; dBoth += (ra && l3); dB += b; dT += t; dNew += (t && !b); }
        return;
    }
    for (int r = 0; r < n; r++) {
        if (used >> r & 1) continue;
        if (!placeOK(c, r)) continue;
        p[c] = r; used |= 1u << r; doPlace(c, r);
        gen(c + 1);
        used &= ~(1u << r); unPlace(c, r);
    }
}

int main(int argc, char** argv) {
    if (argc > 1) n = atoi(argv[1]);
    if (argc > 2) s = atoi(argv[2]);
    auto t0 = chrono::steady_clock::now();
    gen(0);
    double el = chrono::duration<double>(chrono::steady_clock::now() - t0).count();
    long long costB = workRA + workL3, costT = workRA + workL3 + workTM;
    long long req = (long long)( (1.104167 * (double)dB) ) + ( ( (1.104167*(double)dB) > (double)((long long)(1.104167*(double)dB)) ) ? 1 : 0 );
    printf("B_{%d,%d}: valid=%lld infeasible=%lld completable=%lld   (%.1fs)\n", n, s, nV, nI, nF, el);
    printf("  |D_RA|            = %lld  (%.4f%%)\n", dRA, 100.0 * dRA / nI);
    printf("  |D_L3|            = %lld  (%.4f%%)\n", dL3, 100.0 * dL3 / nI);
    printf("  |D_RA & D_L3|     = %lld\n", dBoth);
    printf("  |D_RA \\ D_L3|     = %lld\n", dRA - dBoth);
    printf("  |D_L3 \\ D_RA|     = %lld\n", dL3 - dBoth);
    printf("  |D_B| = union     = %lld  (%.4f%%)\n", dB, 100.0 * dB / nI);
    printf("  |D_T|             = %lld  (%.4f%%)\n", dT, 100.0 * dT / nI);
    printf("  |D_new| = D_T\\D_B = %lld\n", dNew);
    printf("  GATE: required |D_T| >= %lld ; achieved %lld  -> %s\n", req, dT, dT >= req ? "PASS" : "FAIL");
    printf("  COST (declared propagation-work): baseline %lld, candidate %lld, ratio %.4f -> %s\n",
           costB, costT, (double)costT / (double)costB, ((double)costT / (double)costB) <= 2.0 ? "within 2x" : "EXCEEDS 2x");
    printf("  false positives: RA %lld, L3 %lld, T %lld  -> SOUNDNESS %s\n",
           fRA, fL3, fT, (fRA == 0 && fL3 == 0 && fT == 0) ? "PASS" : "FAIL");
    const char* v = (fRA || fL3 || fT) ? "UNSOUND" : (dT >= req ? "PASS" : (dNew > 0 ? "INFORMATIVE FAILURE" : "NULL FAILURE"));
    printf("  VERDICT: %s\n", v);
    printf("  cpp_matches_reference: %lld comparisons, %lld mismatches -> %s\n",
           g_cmp, g_mismatch, g_mismatch == 0 ? "AGREE" : "DISAGREE");
    return 0;
}
