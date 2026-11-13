// Optimised exact Costas DFS. Same search tree as costas_cp_exact.cpp
// (left-to-right assignment, p[0] <= (n-1)/2 vertical-complement symmetry),
// but with zero allocation per node and 64-bit difference masks.
//
// For n <= 32, the set of used differences for a fixed horizontal distance d
// lives in [-(n-1), n-1], i.e. 2n-1 <= 63 values, so it fits in one uint64_t.
//
// Usage: ./costas_fast n [secs] [node_limit] [stop_after_first] [use_sym] [prefix...]
//   secs=0, node_limit=0  -> no budget; the run is exhaustive
//   use_sym=1             -> restrict p[0] <= (n-1)/2 (halves the tree AND the
//                            reported solution count for even n)
// Prints complete=1 only if the whole subtree was explored. complete=0 means the
// run hit a budget and the result is NOT exhaustive. Never merge complete=0 units
// into an exhaustiveness claim.
//
// NOTE: when a prefix is supplied the p[0] symmetry is not applied inside the
// search (k never equals 0), so a prefix manifest must be symmetry-reduced itself.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <chrono>
#include <vector>
using namespace std;

static int n;
static uint64_t diffmask[33];      // diffmask[d], bit (dy + n - 1)
static int p[33];
static uint64_t nodes = 0, solutions = 0;
static int witness[33];
static bool have_witness = false;
static bool stop_first = false;
static bool complete = true;       // false if we bailed on a limit
static double secs = 0;
static uint64_t nodelimit = 0;
static chrono::steady_clock::time_point t0;
static bool use_sym = true;

static inline bool out_of_budget() {
    if (nodelimit && nodes >= nodelimit) return true;
    if (secs > 0 && (nodes & 0xFFFFF) == 0) {
        if (chrono::duration<double>(chrono::steady_clock::now() - t0).count() >= secs)
            return true;
    }
    return false;
}

static void dfs2(int k, uint32_t freeMask) {
    nodes++;
    if (k == n) {
        solutions++;
        if (!have_witness) { for (int i = 0; i < n; i++) witness[i] = p[i]; have_witness = true; }
        return;
    }
    uint32_t cand = freeMask;
    if (k == 0 && use_sym) cand &= (uint32_t)((1u << (((n - 1) / 2) + 1)) - 1);
    while (cand) {
        if (out_of_budget()) { complete = false; return; }
        if (stop_first && have_witness) return;
        int v = __builtin_ctz(cand);
        cand &= cand - 1;
        int i = k - 1;
        bool ok = true;
        for (; i >= 0; i--) {
            uint64_t b = 1ull << (v - p[i] + n - 1);
            if (diffmask[k - i] & b) { ok = false; break; }
            diffmask[k - i] |= b;
        }
        if (ok) {
            p[k] = v;
            dfs2(k + 1, freeMask & ~(1u << v));
            for (int j = k - 1; j >= 0; j--)
                diffmask[k - j] &= ~(1ull << (v - p[j] + n - 1));
        } else {
            for (int j = k - 1; j > i; j--)
                diffmask[k - j] &= ~(1ull << (v - p[j] + n - 1));
        }
        if (!complete) return;
        if (stop_first && have_witness) return;
    }
}

int main(int argc, char **argv) {
    n = argc > 1 ? atoi(argv[1]) : 16;
    secs = argc > 2 ? atof(argv[2]) : 0;
    nodelimit = argc > 3 ? strtoull(argv[3], nullptr, 10) : 0;
    stop_first = argc > 4 ? atoi(argv[4]) : 0;
    use_sym = argc > 5 ? atoi(argv[5]) : 1;
    vector<int> pre;
    for (int i = 6; i < argc; i++) pre.push_back(atoi(argv[i]));

    uint32_t freeMask = (n == 32) ? 0xFFFFFFFFu : ((1u << n) - 1);
    int k = 0;
    for (int v : pre) {
        for (int i = 0; i < k; i++) {
            uint64_t b = 1ull << (v - p[i] + n - 1);
            if (diffmask[k - i] & b) { fprintf(stderr, "non-Costas prefix\n"); return 2; }
            diffmask[k - i] |= b;
        }
        p[k++] = v;
        freeMask &= ~(1u << v);
    }
    t0 = chrono::steady_clock::now();
    dfs2(k, freeMask);
    double el = chrono::duration<double>(chrono::steady_clock::now() - t0).count();
    printf("n=%d nodes=%llu solutions=%llu elapsed=%.4f nps=%.3g complete=%d\n",
           n, (unsigned long long)nodes, (unsigned long long)solutions, el, nodes / el, (int)complete);
    if (have_witness) { printf("witness"); for (int i = 0; i < n; i++) printf(" %d", witness[i]); printf("\n"); }
    return 0;
}
