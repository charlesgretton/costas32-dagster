#include <bits/stdc++.h>
using namespace std;

struct Solver {
    vector<vector<uint32_t>> edges; // length index 0..14
    unordered_map<unsigned long long, unsigned long long> memo;
    unsigned long long nodes=0;

    unsigned long long dfs(uint32_t used, uint16_t rem) {
        nodes++;
        if (!rem) return used==0xFFFFFFFFu ? 1ULL : 0ULL;
        unsigned long long key=((unsigned long long)used<<15)|rem;
        auto it=memo.find(key); if(it!=memo.end()) return it->second;
        int best=-1, bestc=INT_MAX;
        for(int d=0;d<15;d++) if(rem&(1u<<d)) {
            int c=0;
            for(uint32_t e:edges[d]) if(!(e&used)) c++;
            if(c<bestc){bestc=c;best=d; if(c==0) break;}
        }
        if(bestc==0) return memo[key]=0;
        unsigned long long ans=0;
        uint16_t nrem=rem&~(1u<<best);
        for(uint32_t e:edges[best]) if(!(e&used)) ans += dfs(used|e,nrem);
        memo[key]=ans; return ans;
    }
};

int main(){
    cout << "L,u,canonical,nodes,ordinary_covers\n";
    for(int L=16;L<=30;L+=2){
        for(int u=0;u<=31-L;u++){
            if(u>31-L-u) continue; // reflection canonical
            int v=u+L;
            Solver s; s.edges.resize(15);
            for(int d=1;d<=15;d++){
                for(int a=0;a+d<32;a++){
                    int b=a+d;
                    if(a==u||a==v||b==u||b==v) continue;
                    s.edges[d-1].push_back((1u<<a)|(1u<<b));
                }
            }
            uint32_t used=(1u<<u)|(1u<<v);
            auto count=s.dfs(used,0x7FFFu);
            cout<<L<<","<<u<<",1,"<<s.nodes<<","<<count<<"\n";
        }
    }
}
