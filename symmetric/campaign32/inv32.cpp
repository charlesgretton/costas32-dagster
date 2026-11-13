// Order-n transpose-symmetric Costas arrays (involutions h = h^{-1}), split into independent tasks.
// The search is symmetric/src/involution_dfs.cpp unchanged: the lowest unmatched coordinate c takes a partner
// r >= c (r == c is a fixed point); each new dot's displacements are checked against all placed dots and
// recorded immediately, so pairs created by one placement are also checked against each other.
//
//   inv32 full  N                 unsplit search: prints nodes and arrays
//   inv32 split N DEPTH > tasks   frontier after DEPTH partner choices; header line "#SPLIT ..." gives
//                                 the nodes and arrays found above the frontier
//   inv32 run   N < tasks         replays each task line, exhausts its subtree, prints one RESULT line per
//                                 task (and an ARRAY line for every array found)
// Accounting identity: nodes(full) = prefix_nodes(split) + sum of task nodes; likewise for arrays.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <vector>
#include <string>
using namespace std;
static int n; static int p[70]; static unsigned long long used, mask[70];
static int pc[70], np;
static inline bool add1(int c,int r,int*U,int&nu){
  nu=0;
  for(int t=0;t<np;t++){int i=pc[t]; int d=c>i?c-i:i-c; int v=(c>i?r-p[i]:p[i]-r)+n;
    if(mask[d]>>v&1ULL){for(int u=0;u<nu;u+=2)mask[U[u]]&=~(1ULL<<U[u+1]);return false;}
    mask[d]|=1ULL<<v; U[nu++]=d; U[nu++]=v;}
  p[c]=r; pc[np++]=c; used|=1ULL<<r; return true;
}
static inline void del1(int*U,int nu,int r){for(int i=0;i<nu;i+=2)mask[U[i]]&=~(1ULL<<U[i+1]); np--; used&=~(1ULL<<r);}
static long long nodes=0, sols=0; static bool print_arrays=false; static string task_id;
static void report_array(){
  printf("ARRAY %s ",task_id.c_str()); for(int i=0;i<n;i++) printf(i?",%d":"%d",p[i]); printf("\n");
}
static void go(int c){
  nodes++;
  while(c<n && (used>>c&1)) c++;
  if(c==n){ sols++; if(print_arrays) report_array(); return; }
  for(int r=c;r<n;r++){
    if(used>>r&1) continue;
    int U1[512],n1,U2[512],n2;
    if(!add1(c,r,U1,n1)) continue;
    if(r==c){ go(c+1); del1(U1,n1,r); continue; }
    if(add1(r,c,U2,n2)){ go(c+1); del1(U2,n2,c); }
    del1(U1,n1,r);
  }
}
// split: identical traversal, but at DEPTH partner choices the state is emitted as a task instead of explored
static int D; static long long prefix_nodes=0, prefix_sols=0, ntasks=0; static vector<pair<int,int>> ch;
static void split(int c,int depth){
  if(depth==D){ printf("T%07lld %d",ntasks++,c); for(auto&x:ch) printf(" %d:%d",x.first,x.second); printf("\n"); return; }
  prefix_nodes++;
  while(c<n && (used>>c&1)) c++;
  if(c==n){ prefix_sols++; return; }
  for(int r=c;r<n;r++){
    if(used>>r&1) continue;
    int U1[512],n1,U2[512],n2;
    if(!add1(c,r,U1,n1)) continue;
    ch.push_back({c,r});
    if(r==c){ split(c+1,depth+1); del1(U1,n1,r); ch.pop_back(); continue; }
    if(add1(r,c,U2,n2)){ split(c+1,depth+1); del1(U2,n2,c); }
    del1(U1,n1,r); ch.pop_back();
  }
}
static void reset(){ memset(mask,0,sizeof(mask)); used=0; np=0; }
int main(int argc,char**argv){
  if(argc<3){ fprintf(stderr,"usage: inv32 full N | split N DEPTH | run N < tasks\n"); return 2; }
  string mode=argv[1]; n=atoi(argv[2]); if(n<2||n>32){ fprintf(stderr,"order must be 2..32\n"); return 2; }
  if(mode=="full"){ reset(); auto t0=chrono::steady_clock::now(); go(0);
    printf("FULL n=%d nodes=%lld arrays=%lld seconds=%.2f\n",n,nodes,sols,chrono::duration<double>(chrono::steady_clock::now()-t0).count()); return 0; }
  if(mode=="split"){ if(argc<4) return 2; D=atoi(argv[3]); reset();
    vector<char> buf; // header printed last to stderr-safe position: write to stdout after tasks via a trailer line
    split(0,0);
    printf("#SPLIT n=%d depth=%d tasks=%lld prefix_nodes=%lld prefix_arrays=%lld\n",n,D,ntasks,prefix_nodes,prefix_sols); return 0; }
  if(mode=="run"){ print_arrays=true; char line[4096];
    while(fgets(line,sizeof line,stdin)){
      if(line[0]!='T') continue;
      char*save; char*tok=strtok_r(line," \n",&save); task_id=tok;
      int cnext=atoi(strtok_r(nullptr," \n",&save)); reset(); bool ok=true; int lastc=-1;
      while((tok=strtok_r(nullptr," \n",&save))){
        int c,r; if(sscanf(tok,"%d:%d",&c,&r)!=2){ ok=false; break; }
        int U[512],nu; if(!add1(c,r,U,nu)){ ok=false; break; }
        if(r!=c && !add1(r,c,U,nu)){ ok=false; break; }
        lastc=c;
      }
      if(!ok || lastc+1!=cnext){ printf("RESULT %s ERROR replay\n",task_id.c_str()); fflush(stdout); continue; }
      nodes=0; sols=0; auto t0=chrono::steady_clock::now(); go(cnext);
      printf("RESULT %s COMPLETE nodes=%lld arrays=%lld seconds=%.3f\n",task_id.c_str(),nodes,sols,chrono::duration<double>(chrono::steady_clock::now()-t0).count());
      fflush(stdout);
    }
    return 0; }
  fprintf(stderr,"unknown mode\n"); return 2;
}
