// Job B: Costas-aware exhaustion of Z=1T, f=0, L=28, u=0.
// Fixed (0,28); one transposition of each length 1..15; incremental Z<=1,
// terminal Z==1; incremental per-lag Costas check with reversible trail.
// Counters name their predicate (project rule).
#include <cstdio>
#include <cstring>
using namespace std;
static const int N=32, U=0, V=28;
static int hh[32]; static unsigned used; static int Zp;
static unsigned long long lag[32][2];          // lag -> set of seen vertical diffs (+N offset)
static long long nodes=0, z_budget_partials=0, exact_z1_covers=0, costas_covers=0;
static long long firstFailLag[32];             // first-collision histogram by lag
static bool COSTAS=true;
static inline bool getb(int s,int v){return (lag[s][v>>6]>>(v&63))&1ULL;}
static inline void setb(int s,int v){lag[s][v>>6]|=1ULL<<(v&63);}
static inline void clrb(int s,int v){lag[s][v>>6]&=~(1ULL<<(v&63));}
static int trailS[4096],trailV[4096];
static bool place(int a,int b,int&zback,int&tn,int&failLag){
  zback=0; tn=0; failLag=-1;
  int nc[2]={a,b}, nh[2]={b,a};
  for(int t=0;t<2;t++){ int i=nc[t];
    for(int j=0;j<N;j++){ if(!(used>>j&1)) continue; if(t==1&&j==a) continue;
      int d=i>j?i-j:j-i; if(!d) continue;
      int e=nh[t]>hh[j]?nh[t]-hh[j]:hh[j]-nh[t];
      if(d>=16&&e>=16){ Zp++; zback++;
        if(Zp>1){ Zp-=zback; for(int q=0;q<tn;q++) clrb(trailS[q],trailV[q]);
                  used&=~((t?(1u<<a):0u)); return false; } }
      if(COSTAS){ int lo=i<j?i:j, hi=i<j?j:i;
        int s=hi-lo, dv=(lo==i? hh[j]-nh[t] : nh[t]-hh[j]) + N;
        if(getb(s,dv)){ failLag=s; Zp-=zback;
          for(int q=0;q<tn;q++) clrb(trailS[q],trailV[q]);
          used&=~((t?(1u<<a):0u)); return false; }
        setb(s,dv); trailS[tn]=s; trailV[tn]=dv; tn++; } }
    used|=1u<<i; hh[i]=nh[t]; }
  return true; }
static void unplace(int a,int b,int zback,int tn){
  used&=~((1u<<a)|(1u<<b)); Zp-=zback;
  for(int q=0;q<tn;q++) clrb(trailS[q],trailV[q]); }
static int ordD[16];
static void rec(int k){
  nodes++;
  if(k==15){ z_budget_partials++; if(Zp==1){ exact_z1_covers++; if(COSTAS) costas_covers++; } return; }
  int d=ordD[k];
  for(int a=0;a+d<N;a++){ int b=a+d;
    if((used>>a&1)||(used>>b&1)) continue;
    int zb,tn,fl;
    if(!place(a,b,zb,tn,fl)){ if(fl>=0) firstFailLag[fl]++; continue; }
    rec(k+1);
    unplace(a,b,zb,tn); } }
int main(int argc,char**argv){
  if(argc>1&&argv[1][0]=='n') COSTAS=false;
  memset(lag,0,sizeof lag); memset(firstFailLag,0,sizeof firstFailLag);
  used=(1u<<U)|(1u<<V); hh[U]=V; hh[V]=U; Zp=1;
  if(COSTAS){ int s=V-U, dv=hh[V]-hh[U]+N; setb(s,dv); }
  for(int i=0;i<15;i++) ordD[i]=15-i;
  rec(0);
  printf("mode=%s  search_nodes=%lld  complete_assignments=%lld  exact_z1_covers=%lld  costas_covers=%lld  status=EXHAUSTED\n",
         COSTAS?"costas-aware":"structural-only",nodes,z_budget_partials,exact_z1_covers,costas_covers);
  if(COSTAS){ printf("first-collision histogram by lag:\n");
    for(int s=1;s<N;s++) if(firstFailLag[s]) printf("  lag %2d : %lld\n",s,firstFailLag[s]); }
  return 0; }
