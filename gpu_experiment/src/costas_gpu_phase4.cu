#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <fstream>
#include <sstream>
#include <vector>
#include <algorithm>

#ifdef __CUDACC__
#include <cuda_runtime.h>
#define HD __host__ __device__
#define DEV __device__
#define FORCE __forceinline__
#else
#define HD
#define DEV
#define FORCE inline
#endif

namespace cg {
constexpr int MAX_N = 32;
constexpr int MAX_CHANGES = MAX_N * (MAX_N - 1) / 2;
constexpr uint64_t FNV_OFFSET = UINT64_C(14695981039346656037);
constexpr uint64_t FNV_PRIME = UINT64_C(1099511628211);
static_assert(MAX_CHANGES == 496, "unexpected change-log capacity");
static_assert(sizeof(uint16_t) == 2, "16-bit packed log required");

enum Error : uint8_t {
    OK = 0,
    INVALID_PREFIX = 1,
    PHYSICAL_LOG_OVERFLOW = 2,
    MATHEMATICAL_LOG_OVERFLOW = 3,
    INCOMPLETE_SOLUTION_LOG = 4,
    NONEMPTY_TERMINAL_LOG = 5,
    TERMINAL_MASK_MISMATCH = 6,
    NODE_ACCOUNTING = 7,
    CANDIDATE_ACCOUNTING = 8
};

struct Prefix {
    uint64_t id;
    uint8_t n;
    int8_t h[MAX_N];
};

struct Counters {
    uint64_t entered_nodes;
    uint64_t candidate_attempts;
    uint64_t occupied_rejections;
    uint64_t costas_rejections;
    uint64_t accepted_children;
    uint64_t complete_involutions;
    uint64_t verified_solutions;
    uint64_t backtracks;
    uint64_t invariant_failures;
};

struct WorkResult {
    uint64_t prefix_id;
    Counters c;
    uint64_t traversal_fnv;
    uint64_t solution_fnv;
    uint16_t initial_displacements;
    uint16_t max_change_top;
    uint16_t terminal_change_top;
    uint8_t exhausted;
    uint8_t error_code;
};

struct Frame {
    uint16_t mark;
    uint8_t c;
    uint8_t next_r;
    uint8_t undo_c;
    uint8_t undo_r;
};
static_assert(sizeof(Frame) <= 8, "frame unexpectedly large");

HD FORCE uint16_t pack_change(unsigned lag, unsigned bit) {
    return static_cast<uint16_t>((bit << 5U) | lag);
}
HD FORCE unsigned unpack_lag(uint16_t p) { return p & 31U; }
HD FORCE unsigned unpack_bit(uint16_t p) { return p >> 5U; }

HD FORCE void clear_result(WorkResult& out, uint64_t id) {
    std::memset(&out, 0, sizeof(out));
    out.prefix_id = id;
    out.traversal_fnv = FNV_OFFSET;
    out.solution_fnv = FNV_OFFSET;
}
HD FORCE void fail(WorkResult& out, Error e) {
    if (out.error_code == OK) out.error_code = static_cast<uint8_t>(e);
    ++out.c.invariant_failures;
}
HD FORCE void fnv_byte(uint64_t& h, uint8_t b) {
    h ^= b;
    h *= FNV_PRIME;
}
HD FORCE void hash_board(uint64_t& z, const int8_t h[MAX_N], int n) {
    fnv_byte(z, UINT8_C(0x43));
    fnv_byte(z, static_cast<uint8_t>(n));
    for (int i = 0; i < n; ++i) {
        fnv_byte(z, static_cast<uint8_t>(static_cast<int>(h[i]) + 1));
    }
}
HD FORCE int frontier(const int8_t h[MAX_N], int n) {
    for (int i = 0; i < n; ++i) if (h[i] == -1) return i;
    return n;
}

HD FORCE bool add_diff(const uint64_t masks[MAX_N], uint64_t add[MAX_N],
                       uint32_t& touched, int lag, int diff) {
    const uint32_t lag_bit = UINT32_C(1) << lag;
    if ((touched & lag_bit) == 0) {
        add[lag] = 0;
        touched |= lag_bit;
    }
    const uint64_t bit = UINT64_C(1) << (diff + 31);
    if (((masks[lag] | add[lag]) & bit) != 0) return false;
    add[lag] |= bit;
    return true;
}
HD FORCE bool add_pair(const uint64_t masks[MAX_N], uint64_t add[MAX_N],
                       uint32_t& touched, int x1, int y1, int x2, int y2) {
    if (x1 < x2) return add_diff(masks, add, touched, x2 - x1, y2 - y1);
    return add_diff(masks, add, touched, x1 - x2, y1 - y2);
}
HD bool candidate_valid(const int8_t h[MAX_N], int n,
                        const uint64_t masks[MAX_N], int c, int r,
                        uint64_t add[MAX_N], uint32_t& touched) {
    touched = 0;
    for (int x = 0; x < n; ++x) {
        if (h[x] == -1 || x == r) continue;
        if (!add_pair(masks, add, touched, c, r, x, static_cast<int>(h[x]))) return false;
    }
    if (r > c) {
        if (!add_pair(masks, add, touched, c, r, r, c)) return false;
        for (int x = 0; x < n; ++x) {
            if (h[x] == -1 || x == c || x == r) continue;
            if (!add_pair(masks, add, touched, r, c, x, static_cast<int>(h[x]))) return false;
        }
    }
    return true;
}

HD bool initialise(const Prefix& p, int8_t h[MAX_N], uint64_t masks[MAX_N],
                   uint16_t& initial_displacements) {
    if (p.n < 1 || p.n > MAX_N) return false;
    for (int i = 0; i < MAX_N; ++i) {
        h[i] = p.h[i];
        masks[i] = 0;
    }
    int assigned = 0;
    for (int i = 0; i < p.n; ++i) {
        const int v = h[i];
        if (v == -1) continue;
        ++assigned;
        if (v < 0 || v >= p.n || h[v] != i) return false;
    }
    const int c = frontier(h, p.n);
    for (int x = 0; x < c; ++x) if (h[x] == -1) return false;
    initial_displacements = static_cast<uint16_t>(assigned * (assigned - 1) / 2);
    uint16_t counted = 0;
    for (int x = 0; x < p.n; ++x) if (h[x] != -1) {
        for (int y = x + 1; y < p.n; ++y) if (h[y] != -1) {
            const int lag = y - x;
            const int diff = static_cast<int>(h[y]) - static_cast<int>(h[x]);
            const uint64_t bit = UINT64_C(1) << (diff + 31);
            if ((masks[lag] & bit) != 0) return false;
            masks[lag] |= bit;
            ++counted;
        }
    }
    return counted == initial_displacements;
}

struct LocalLog {
    uint16_t entries[MAX_CHANGES];
    HD FORCE void put(uint16_t depth, uint16_t packed) { entries[depth] = packed; }
    HD FORCE uint16_t get(uint16_t depth) const { return entries[depth]; }
};

#ifdef __CUDACC__
struct SharedLog {
    uint16_t* entries;
    unsigned stride;
    unsigned lane;
    DEV FORCE void put(uint16_t depth, uint16_t packed) {
        entries[static_cast<std::size_t>(depth) * stride + lane] = packed;
    }
    DEV FORCE uint16_t get(uint16_t depth) const {
        return entries[static_cast<std::size_t>(depth) * stride + lane];
    }
};
#endif

template<class Log>
HD FORCE void undo_to(uint16_t mark, const Log& log, uint16_t& top,
                      uint64_t masks[MAX_N]) {
    while (top > mark) {
        const uint16_t packed = log.get(--top);
        const unsigned lag = unpack_lag(packed);
        const unsigned bit = unpack_bit(packed);
        masks[lag] &= ~(UINT64_C(1) << bit);
    }
}

template<class Log>
HD void search_one_impl(const Prefix& p, WorkResult& out, Log& log) {
    clear_result(out, p.id);
    int8_t h[MAX_N];
    uint64_t masks[MAX_N];
    uint64_t initial_masks[MAX_N];
    uint64_t add[MAX_N];
    Frame stack[MAX_N + 1];
    uint16_t change_top = 0;
    int depth = 0;

    if (!initialise(p, h, masks, out.initial_displacements)) {
        fail(out, INVALID_PREFIX);
        return;
    }
    for (int i = 0; i < MAX_N; ++i) initial_masks[i] = masks[i];
    const uint16_t total = static_cast<uint16_t>(p.n * (p.n - 1) / 2);
    const uint16_t remaining = static_cast<uint16_t>(total - out.initial_displacements);

    auto enter = [&](uint16_t undo_mark, uint8_t undo_c, uint8_t undo_r) HD {
        ++out.c.entered_nodes;
        hash_board(out.traversal_fnv, h, p.n);
        const int c = frontier(h, p.n);
        stack[depth] = Frame{undo_mark, static_cast<uint8_t>(c),
                             static_cast<uint8_t>(c), undo_c, undo_r};
    };
    enter(0, UINT8_C(255), UINT8_C(255));

    for (;;) {
        Frame& frame = stack[depth];
        if (frame.c == p.n) {
            if (static_cast<uint16_t>(out.initial_displacements + change_top) != total) {
                fail(out, INCOMPLETE_SOLUTION_LOG);
                return;
            }
            ++out.c.complete_involutions;
            ++out.c.verified_solutions;
            hash_board(out.solution_fnv, h, p.n);
            if (depth == 0) break;
            const Frame done = frame;
            --depth;
            h[done.undo_c] = -1;
            if (done.undo_r != done.undo_c) h[done.undo_r] = -1;
            undo_to(done.mark, log, change_top, masks);
            ++out.c.backtracks;
            continue;
        }

        if (frame.next_r >= p.n) {
            if (depth == 0) break;
            const Frame done = frame;
            --depth;
            h[done.undo_c] = -1;
            if (done.undo_r != done.undo_c) h[done.undo_r] = -1;
            undo_to(done.mark, log, change_top, masks);
            ++out.c.backtracks;
            continue;
        }

        const int c = frame.c;
        const int r = frame.next_r++;
        ++out.c.candidate_attempts;
        if (h[r] != -1) {
            ++out.c.occupied_rejections;
            continue;
        }

        uint32_t touched = 0;
        if (!candidate_valid(h, p.n, masks, c, r, add, touched)) {
            ++out.c.costas_rejections;
            continue;
        }

        const uint16_t undo_mark = change_top;
        uint32_t pending = touched;
        while (pending != 0) {
#ifdef __CUDA_ARCH__
            const unsigned lag = static_cast<unsigned>(__ffs(static_cast<int>(pending)) - 1);
#else
            const unsigned lag = static_cast<unsigned>(__builtin_ctz(pending));
#endif
            pending &= pending - 1;
            uint64_t bits = add[lag];
            masks[lag] |= bits;
            while (bits != 0) {
#ifdef __CUDA_ARCH__
                const unsigned bit = static_cast<unsigned>(__ffsll(static_cast<long long>(bits)) - 1);
#else
                const unsigned bit = static_cast<unsigned>(__builtin_ctzll(bits));
#endif
                bits &= bits - 1;
                if (change_top >= MAX_CHANGES) {
                    fail(out, PHYSICAL_LOG_OVERFLOW);
                    return;
                }
                if (change_top >= remaining) {
                    fail(out, MATHEMATICAL_LOG_OVERFLOW);
                    return;
                }
                log.put(change_top++, pack_change(lag, bit));
            }
        }
        if (change_top > out.max_change_top) out.max_change_top = change_top;

        h[c] = static_cast<int8_t>(r);
        if (r != c) h[r] = static_cast<int8_t>(c);
        ++out.c.accepted_children;
        ++depth;
        enter(undo_mark, static_cast<uint8_t>(c), static_cast<uint8_t>(r));
    }

    out.terminal_change_top = change_top;
    if (change_top != 0) {
        fail(out, NONEMPTY_TERMINAL_LOG);
        return;
    }
    for (int lag = 0; lag < p.n; ++lag) {
        if (masks[lag] != initial_masks[lag]) {
            fail(out, TERMINAL_MASK_MISMATCH);
            return;
        }
    }
    if (out.c.accepted_children + 1 != out.c.entered_nodes) {
        fail(out, NODE_ACCOUNTING);
        return;
    }
    if (out.c.occupied_rejections + out.c.costas_rejections +
            out.c.accepted_children != out.c.candidate_attempts) {
        fail(out, CANDIDATE_ACCOUNTING);
        return;
    }
    out.exhausted = 1;
}

HD void search_one_local(const Prefix& p, WorkResult& out) {
    LocalLog log{};
    search_one_impl(p, out, log);
}

#ifdef __CUDACC__
__global__ void kernel_local(const Prefix* prefixes, uint64_t count, WorkResult* results) {
    const uint64_t tid = static_cast<uint64_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (tid < count) search_one_local(prefixes[tid], results[tid]);
}

__global__ void kernel_shared(const Prefix* prefixes, uint64_t count, WorkResult* results) {
    extern __shared__ uint16_t shared_changes[];
    const uint64_t tid = static_cast<uint64_t>(blockIdx.x) * blockDim.x + threadIdx.x;
    if (tid >= count) return;
    SharedLog log{shared_changes, blockDim.x, threadIdx.x};
    search_one_impl(prefixes[tid], results[tid], log);
}
#endif

Prefix empty_prefix(int n) {
    Prefix p{};
    p.id = 0;
    p.n = static_cast<uint8_t>(n);
    for (int i = 0; i < MAX_N; ++i) p.h[i] = -1;
    return p;
}

void print_result(int n, const WorkResult& r) {
    const Counters& c = r.c;
    std::printf(
        "N=%d prefix=%llu nodes=%llu candidates=%llu occupied=%llu "
        "costas_reject=%llu accepted=%llu complete=%llu solutions=%llu "
        "backtracks=%llu invariant_failures=%llu exhausted=%s "
        "traversal_fnv=0x%016llx solution_fnv=0x%016llx "
        "initial_displacements=%u max_change_top=%u terminal_change_top=%u error=%u\n",
        n, static_cast<unsigned long long>(r.prefix_id),
        static_cast<unsigned long long>(c.entered_nodes),
        static_cast<unsigned long long>(c.candidate_attempts),
        static_cast<unsigned long long>(c.occupied_rejections),
        static_cast<unsigned long long>(c.costas_rejections),
        static_cast<unsigned long long>(c.accepted_children),
        static_cast<unsigned long long>(c.complete_involutions),
        static_cast<unsigned long long>(c.verified_solutions),
        static_cast<unsigned long long>(c.backtracks),
        static_cast<unsigned long long>(c.invariant_failures),
        r.exhausted ? "yes" : "no",
        static_cast<unsigned long long>(r.traversal_fnv),
        static_cast<unsigned long long>(r.solution_fnv),
        r.initial_displacements, r.max_change_top, r.terminal_change_top,
        r.error_code);
}

#ifndef __CUDA_ARCH__

bool same_result(const WorkResult& a, const WorkResult& b) {
    return std::memcmp(&a, &b, sizeof(WorkResult)) == 0;
}

void generate_prefixes_rec(int target_decisions, int decisions,
                           int8_t h[MAX_N], int n, uint64_t masks[MAX_N],
                           std::vector<Prefix>& out) {
    if (decisions == target_decisions) {
        Prefix p{};
        p.id = static_cast<uint64_t>(out.size());
        p.n = static_cast<uint8_t>(n);
        for (int i = 0; i < MAX_N; ++i) p.h[i] = h[i];
        out.push_back(p);
        return;
    }
    const int c = frontier(h, n);
    if (c == n) return;
    for (int r = c; r < n; ++r) {
        if (h[r] != -1) continue;
        uint64_t add[MAX_N];
        uint32_t touched = 0;
        if (!candidate_valid(h, n, masks, c, r, add, touched)) continue;
        uint64_t old_masks[MAX_N];
        for (int lag = 0; lag < MAX_N; ++lag) old_masks[lag] = masks[lag];
        uint32_t pending = touched;
        while (pending != 0) {
            const unsigned lag = static_cast<unsigned>(__builtin_ctz(pending));
            pending &= pending - 1;
            masks[lag] |= add[lag];
        }
        h[c] = static_cast<int8_t>(r);
        if (r != c) h[r] = static_cast<int8_t>(c);
        generate_prefixes_rec(target_decisions, decisions + 1, h, n, masks, out);
        h[c] = -1;
        if (r != c) h[r] = -1;
        for (int lag = 0; lag < MAX_N; ++lag) masks[lag] = old_masks[lag];
    }
}

std::vector<Prefix> generate_prefixes(int n, int decisions) {
    if (decisions < 0 || decisions > n) throw std::runtime_error("invalid prefix depth");
    std::vector<Prefix> out;
    int8_t h[MAX_N];
    uint64_t masks[MAX_N];
    for (int i = 0; i < MAX_N; ++i) { h[i] = -1; masks[i] = 0; }
    generate_prefixes_rec(decisions, 0, h, n, masks, out);
    return out;
}

void write_prefixes(const std::string& path, const std::vector<Prefix>& prefixes) {
    std::ofstream f(path);
    if (!f) throw std::runtime_error("cannot open prefix output: " + path);
    f << "COSTAS_PREFIXES_V1 " << prefixes.size() << '\n';
    for (const Prefix& p : prefixes) {
        f << p.id << ' ' << static_cast<unsigned>(p.n);
        for (int i = 0; i < MAX_N; ++i) f << ' ' << static_cast<int>(p.h[i]);
        f << '\n';
    }
    if (!f) throw std::runtime_error("failed writing prefixes: " + path);
}

std::vector<Prefix> read_prefixes(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("cannot open prefix input: " + path);
    std::string magic;
    uint64_t count = 0;
    if (!(f >> magic >> count) || magic != "COSTAS_PREFIXES_V1")
        throw std::runtime_error("invalid prefix header: " + path);
    std::vector<Prefix> out;
    out.reserve(static_cast<std::size_t>(count));
    for (uint64_t k = 0; k < count; ++k) {
        Prefix p{};
        unsigned n = 0;
        if (!(f >> p.id >> n) || n < 1 || n > MAX_N)
            throw std::runtime_error("invalid prefix record header");
        p.n = static_cast<uint8_t>(n);
        for (int i = 0; i < MAX_N; ++i) {
            int v = 0;
            if (!(f >> v) || v < -1 || v >= MAX_N)
                throw std::runtime_error("invalid prefix board value");
            p.h[i] = static_cast<int8_t>(v);
        }
        out.push_back(p);
    }
    std::string extra;
    if (f >> extra) throw std::runtime_error("trailing data in prefix file");
    std::vector<bool> seen(out.size(), false);
    for (const Prefix& p : out) {
        if (p.id >= out.size()) throw std::runtime_error("prefix ID outside catalogue range");
        if (seen[static_cast<std::size_t>(p.id)]) throw std::runtime_error("duplicate prefix ID");
        seen[static_cast<std::size_t>(p.id)] = true;
    }
    for (std::size_t id = 0; id < seen.size(); ++id)
        if (!seen[id]) throw std::runtime_error("missing prefix ID " + std::to_string(id));
    return out;
}

void write_results(const std::string& path, const std::vector<WorkResult>& results) {
    std::vector<WorkResult> canonical(results.size());
    std::vector<bool> seen(results.size(), false);
    for (const WorkResult& r : results) {
        if (r.prefix_id >= results.size()) throw std::runtime_error("result ID outside range");
        if (seen[static_cast<std::size_t>(r.prefix_id)]) throw std::runtime_error("duplicate result ID");
        seen[static_cast<std::size_t>(r.prefix_id)] = true;
        canonical[static_cast<std::size_t>(r.prefix_id)] = r;
    }
    std::ofstream f(path);
    if (!f) throw std::runtime_error("cannot open result output: " + path);
    f << "COSTAS_RESULTS_V1 " << canonical.size() << '\n';
    for (const WorkResult& r : canonical) {
        const Counters& c = r.c;
        f << r.prefix_id << ' ' << c.entered_nodes << ' ' << c.candidate_attempts << ' '
          << c.occupied_rejections << ' ' << c.costas_rejections << ' '
          << c.accepted_children << ' ' << c.complete_involutions << ' '
          << c.verified_solutions << ' ' << c.backtracks << ' ' << c.invariant_failures << ' '
          << r.traversal_fnv << ' ' << r.solution_fnv << ' '
          << r.initial_displacements << ' ' << r.max_change_top << ' '
          << r.terminal_change_top << ' ' << static_cast<unsigned>(r.exhausted) << ' '
          << static_cast<unsigned>(r.error_code) << '\n';
    }
    if (!f) throw std::runtime_error("failed writing results: " + path);
}


int assigned_points(const Prefix& p) {
    int count = 0;
    for (int i = 0; i < p.n; ++i) if (p.h[i] != -1) ++count;
    return count;
}

std::vector<Prefix> valid_children(const Prefix& p) {
    int8_t h[MAX_N]; uint64_t masks[MAX_N]; uint16_t initial = 0;
    if (!initialise(p, h, masks, initial)) throw std::runtime_error("invalid parent in refinement");
    std::vector<Prefix> out;
    const int c = frontier(h, p.n);
    if (c == p.n) return out;
    for (int r = c; r < p.n; ++r) {
        if (h[r] != -1) continue;
        uint64_t add[MAX_N]; uint32_t touched = 0;
        if (!candidate_valid(h, p.n, masks, c, r, add, touched)) continue;
        Prefix child = p;
        child.h[c] = static_cast<int8_t>(r);
        if (r != c) child.h[r] = static_cast<int8_t>(c);
        out.push_back(child);
    }
    return out;
}

uint32_t b2_score(const Prefix& p) {
    uint64_t total = 0;
    for (const Prefix& child : valid_children(p)) total += valid_children(child).size();
    if (total > UINT32_MAX) throw std::runtime_error("b2 score overflow");
    return static_cast<uint32_t>(total);
}

std::vector<uint64_t> read_exact_sizes(const std::string& path, std::size_t expected) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("cannot open oracle results: " + path);
    std::string magic; uint64_t count = 0;
    if (!(f >> magic >> count) || magic != "COSTAS_RESULTS_V1" || count != expected)
        throw std::runtime_error("oracle result header mismatch");
    std::vector<uint64_t> sizes(expected, UINT64_MAX);
    for (uint64_t k = 0; k < count; ++k) {
        uint64_t id, nodes, discard;
        if (!(f >> id >> nodes) || id >= expected || sizes[id] != UINT64_MAX)
            throw std::runtime_error("invalid oracle result ID");
        sizes[id] = nodes;
        for (int field = 0; field < 15; ++field) if (!(f >> discard))
            throw std::runtime_error("short oracle result record");
    }
    return sizes;
}

void assign_final_ids(std::vector<Prefix>& prefixes) {
    for (std::size_t i = 0; i < prefixes.size(); ++i) prefixes[i].id = i;
}

uint64_t refine_top_b2(std::vector<Prefix>& prefixes, std::size_t top) {
    if (top == 0) return 0;
    if (top > prefixes.size()) top = prefixes.size();
    std::vector<uint32_t> b2(prefixes.size());
    for (std::size_t i = 0; i < prefixes.size(); ++i) b2[i] = b2_score(prefixes[i]);
    std::vector<std::size_t> order(prefixes.size());
    for (std::size_t i = 0; i < order.size(); ++i) order[i] = i;
    std::stable_sort(order.begin(), order.end(), [&](std::size_t a, std::size_t b) {
        if (b2[a] != b2[b]) return b2[a] > b2[b];
        return prefixes[a].id < prefixes[b].id;
    });
    std::vector<bool> selected(prefixes.size(), false);
    for (std::size_t i = 0; i < top; ++i) selected[order[i]] = true;
    std::vector<Prefix> refined;
    refined.reserve(prefixes.size() + top * 8);
    uint64_t replaced = 0;
    for (std::size_t i = 0; i < prefixes.size(); ++i) {
        if (!selected[i]) { refined.push_back(prefixes[i]); continue; }
        const auto children = valid_children(prefixes[i]);
        ++replaced;
        refined.insert(refined.end(), children.begin(), children.end());
    }
    prefixes.swap(refined);
    assign_final_ids(prefixes);
    return replaced;
}

void schedule_prefixes(std::vector<Prefix>& prefixes, const std::string& mode,
                       const std::string& oracle_path) {
    if (mode.empty() || mode == "catalogue") return;
    if (mode == "exact") {
        const auto sizes = read_exact_sizes(oracle_path, prefixes.size());
        std::stable_sort(prefixes.begin(), prefixes.end(), [&](const Prefix& a, const Prefix& b) {
            if (sizes[a.id] != sizes[b.id]) return sizes[a.id] > sizes[b.id];
            return a.id < b.id;
        });
        return;
    }
    if (mode == "p-b2") {
        std::vector<uint32_t> b2(prefixes.size());
        for (const Prefix& p : prefixes) b2[p.id] = b2_score(p);
        std::stable_sort(prefixes.begin(), prefixes.end(), [&](const Prefix& a, const Prefix& b) {
            const int pa = assigned_points(a), pb = assigned_points(b);
            if (pa != pb) return pa < pb;
            if (b2[a.id] != b2[b.id]) return b2[a.id] > b2[b.id];
            return a.id < b.id;
        });
        return;
    }
    throw std::runtime_error("unknown schedule: " + mode);
}

uint64_t nodes_strictly_above_cut(int n, int cut_depth) {
    if (cut_depth < 0 || cut_depth > n)
        throw std::runtime_error("invalid decomposition cut depth");
    uint64_t above = 0;
    for (int depth = 0; depth < cut_depth; ++depth) {
        above += static_cast<uint64_t>(generate_prefixes(n, depth).size());
    }
    return above;
}

void verify_decomposition(const WorkResult& root,
                          const std::vector<WorkResult>& units,
                          uint64_t nodes_above_cut) {
    uint64_t nodes = 0, solutions = 0;
    for (const WorkResult& r : units) {
        if (!r.exhausted || r.error_code != OK)
            throw std::runtime_error("non-exhausted prefix result");
        nodes += r.c.entered_nodes;
        solutions += r.c.verified_solutions;
    }
    if (nodes_above_cut > root.c.entered_nodes ||
        nodes != root.c.entered_nodes - nodes_above_cut)
        throw std::runtime_error("prefix node decomposition failed");
    if (solutions != root.c.verified_solutions)
        throw std::runtime_error("prefix solution decomposition failed");
}

#endif

} // namespace cg

int main(int argc, char** argv) {
    try {
        int n = 16;
        int threads = 32;
        int prefix_depth = -1;
        bool gpu = false;
        bool shared = false;
        bool check_decomposition = false;
        std::size_t refine_top = 0;
        std::string schedule = "catalogue";
        std::string oracle_path;
        std::string write_prefix_path, read_prefix_path, write_result_path;
        for (int i = 1; i < argc; ++i) {
            const std::string a = argv[i];
            if (a == "--gpu") gpu = true;
            else if (a == "--backend=shared") shared = true;
            else if (a == "--backend=local") shared = false;
            else if (a == "--check-decomposition") check_decomposition = true;
            else if (a.rfind("--threads=", 0) == 0) threads = std::atoi(a.c_str() + 10);
            else if (a.rfind("--prefix-depth=", 0) == 0) prefix_depth = std::atoi(a.c_str() + 15);
            else if (a.rfind("--write-prefixes=", 0) == 0) write_prefix_path = a.substr(17);
            else if (a.rfind("--read-prefixes=", 0) == 0) read_prefix_path = a.substr(16);
            else if (a.rfind("--write-results=", 0) == 0) write_result_path = a.substr(16);
            else if (a.rfind("--schedule=", 0) == 0) schedule = a.substr(11);
            else if (a.rfind("--oracle-results=", 0) == 0) oracle_path = a.substr(17);
            else if (a.rfind("--refine-top-b2=", 0) == 0) refine_top = static_cast<std::size_t>(std::stoull(a.substr(16)));
            else if (a == "--help") {
                std::printf("usage: %s [N] [--gpu] [--backend=local|shared] [--threads=N]\n"
                            "       [--prefix-depth=K] [--write-prefixes=FILE]\n"
                            "       [--read-prefixes=FILE] [--write-results=FILE]\n"
                            "       [--check-decomposition] [--refine-top-b2=N]\n"
                            "       [--schedule=catalogue|exact|p-b2] [--oracle-results=FILE]\n", argv[0]);
                return 0;
            } else n = std::atoi(a.c_str());
        }
        if (n < 1 || n > cg::MAX_N || threads <= 0 || threads > 1024) return 2;
        if (!read_prefix_path.empty() && prefix_depth >= 0)
            throw std::runtime_error("use either --read-prefixes or --prefix-depth, not both");

        std::vector<cg::Prefix> prefixes;
        if (!read_prefix_path.empty()) prefixes = cg::read_prefixes(read_prefix_path);
        else if (prefix_depth >= 0) prefixes = cg::generate_prefixes(n, prefix_depth);
        else prefixes.push_back(cg::empty_prefix(n));
        if (prefixes.empty()) throw std::runtime_error("prefix catalogue is empty");
        n = prefixes.front().n;
        for (const cg::Prefix& p : prefixes)
            if (p.n != n) throw std::runtime_error("mixed orders in prefix catalogue");
        const uint64_t refined_parents = cg::refine_top_b2(prefixes, refine_top);
        if (schedule == "exact" && oracle_path.empty())
            throw std::runtime_error("--schedule=exact requires --oracle-results");
        cg::schedule_prefixes(prefixes, schedule, oracle_path);
        if (!write_prefix_path.empty()) cg::write_prefixes(write_prefix_path, prefixes);

        std::vector<cg::WorkResult> results(prefixes.size());
#ifdef __CUDACC__
        if (gpu) {
            cg::Prefix* dp = nullptr;
            cg::WorkResult* dr = nullptr;
            const std::size_t pbytes = prefixes.size() * sizeof(cg::Prefix);
            const std::size_t rbytes = results.size() * sizeof(cg::WorkResult);
            cudaError_t st = cudaMalloc(&dp, pbytes);
            if (st == cudaSuccess) st = cudaMalloc(&dr, rbytes);
            if (st != cudaSuccess) throw std::runtime_error(cudaGetErrorString(st));
            st = cudaMemcpy(dp, prefixes.data(), pbytes, cudaMemcpyHostToDevice);
            if (st != cudaSuccess) throw std::runtime_error(cudaGetErrorString(st));
            const unsigned blocks = static_cast<unsigned>((prefixes.size() + threads - 1) / threads);
            if (shared) {
                const std::size_t bytes = static_cast<std::size_t>(threads) * cg::MAX_CHANGES * sizeof(uint16_t);
                int device = 0; cudaDeviceProp prop{};
                cudaGetDevice(&device); cudaGetDeviceProperties(&prop, device);
                if (bytes > static_cast<std::size_t>(prop.sharedMemPerBlockOptin))
                    throw std::runtime_error("shared-memory request exceeds opt-in device limit");
                st = cudaFuncSetAttribute(cg::kernel_shared,
                        cudaFuncAttributeMaxDynamicSharedMemorySize, static_cast<int>(bytes));
                if (st != cudaSuccess) throw std::runtime_error(cudaGetErrorString(st));
                cg::kernel_shared<<<blocks, threads, bytes>>>(dp, prefixes.size(), dr);
            } else {
                cg::kernel_local<<<blocks, threads>>>(dp, prefixes.size(), dr);
            }
            st = cudaGetLastError();
            if (st == cudaSuccess) st = cudaDeviceSynchronize();
            if (st != cudaSuccess) throw std::runtime_error(cudaGetErrorString(st));
            st = cudaMemcpy(results.data(), dr, rbytes, cudaMemcpyDeviceToHost);
            cudaFree(dp); cudaFree(dr);
            if (st != cudaSuccess) throw std::runtime_error(cudaGetErrorString(st));
        } else
#else
        (void)shared;
        if (gpu) throw std::runtime_error("built without CUDA; omit --gpu");
        else
#endif
        {
            for (std::size_t i = 0; i < prefixes.size(); ++i)
                cg::search_one_local(prefixes[i], results[i]);
        }

        for (const cg::WorkResult& r : results)
            if (!r.exhausted || r.error_code != cg::OK)
                throw std::runtime_error("work unit failed closed: prefix " + std::to_string(r.prefix_id));
        if (!write_result_path.empty()) cg::write_results(write_result_path, results);
        if (results.size() == 1) cg::print_result(n, results[0]);
        else {
            uint64_t nodes = 0, solutions = 0;
            for (const auto& r : results) { nodes += r.c.entered_nodes; solutions += r.c.verified_solutions; }
            std::printf("N=%d units=%zu sum_nodes=%llu sum_solutions=%llu backend=%s schedule=%s refined=%llu\n",
                        n, results.size(), static_cast<unsigned long long>(nodes),
                        static_cast<unsigned long long>(solutions), gpu ? (shared ? "gpu-shared" : "gpu-local") : "cpu-local",
                        schedule.c_str(), static_cast<unsigned long long>(refined_parents));
        }
        if (check_decomposition) {
            int cut_depth = prefix_depth;
            if (cut_depth < 0) {
                // Infer the number of involution cycles from the first prefix.
                cut_depth = 0;
                const cg::Prefix& p0 = prefixes.front();
                for (int i = 0; i < p0.n; ++i) {
                    if (p0.h[i] == -1) continue;
                    if (p0.h[i] == i || i < p0.h[i]) ++cut_depth;
                }
                for (const cg::Prefix& p : prefixes) {
                    int d = 0;
                    for (int i = 0; i < p.n; ++i) {
                        if (p.h[i] == -1) continue;
                        if (p.h[i] == i || i < p.h[i]) ++d;
                    }
                    if (d != cut_depth)
                        throw std::runtime_error("catalogue is not a fixed-depth cut");
                }
            }
            const uint64_t above = cg::nodes_strictly_above_cut(n, cut_depth) + refined_parents;
            cg::WorkResult root{};
            const cg::Prefix empty = cg::empty_prefix(n);
            cg::search_one_local(empty, root);
            cg::verify_decomposition(root, results, above);
            std::printf("decomposition=exact cut_depth=%d nodes_above=%llu "
                        "root_nodes=%llu root_solutions=%llu\n",
                        cut_depth, static_cast<unsigned long long>(above),
                        static_cast<unsigned long long>(root.c.entered_nodes),
                        static_cast<unsigned long long>(root.c.verified_solutions));
        }
        return 0;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "fatal: %s\n", e.what());
        return 1;
    }
}
