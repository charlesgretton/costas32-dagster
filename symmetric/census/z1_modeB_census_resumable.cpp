// Job B: Costas-aware exhaustion of Z=1T, f=0, L=28, u=0.
// Fixed (0,28); one transposition of each length 1..15; incremental Z<=1,
// terminal Z==1; incremental per-lag Costas check with reversible trail.
// Counters name their predicate (project rule).
#include <cstdio>
#include <cstring>
#include <cstdlib>
using namespace std;
static const int N=32; static int U=0,V=28,LL_=28;
static int hh[32]; static unsigned used; static int Zp;
static unsigned long long lag[32][2];          // lag -> set of seen vertical diffs (+N offset)
static long long nodes=0, z_budget_partials=0, exact_z1_covers=0, costas_covers=0;
static long long collisionEvents[32];          // duplicate-displacement detections by lag
static long long costas_rejected_placements=0;
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
    if(!place(a,b,zb,tn,fl)){ if(fl>=0){ collisionEvents[fl]++; costas_rejected_placements++; } continue; }
    rec(k+1);
    unplace(a,b,zb,tn); } }
static void run(int L,int u,bool costas){
  COSTAS=costas; U=u; V=u+L; LL_=L;
  nodes=0; z_budget_partials=0; exact_z1_covers=0; costas_covers=0; costas_rejected_placements=0;
  memset(lag,0,sizeof lag); memset(collisionEvents,0,sizeof collisionEvents);
  memset(hh,0,sizeof hh);
  used=(1u<<U)|(1u<<V); hh[U]=V; hh[V]=U; Zp=1;
  if(COSTAS){ int s=V-U, dv=hh[V]-hh[U]+N; setb(s,dv); }
  for(int i=0;i<15;i++) ordD[i]=15-i;
  rec(0); }
#include <ctime>
int main(int argc,char**argv){
  int L0=argc>1?atoi(argv[1]):16, u0=argc>2?atoi(argv[2]):0;
  printf("canonical_key,modeB_status,modeB_complete,search_nodes,complete_assignments,exact_z1_covers,duplicate_displacement_events,runtime_ms\n");
  for(int L=16;L<=30;L+=2) for(int u=0;u<=(31-L)/2;u++){
    if(L<L0||(L==L0&&u<u0)) continue;
    clock_t t0=clock();
    run(L,u,false);
    long long ms=(long long)((clock()-t0)*1000.0/CLOCKS_PER_SEC);
    printf("L%d-u%d,%s,1,%lld,%lld,%lld,%lld,%lld\n",L,u,
      exact_z1_covers?"EXHAUSTED_WITH_Z1_COVERS":"EXHAUSTED_NO_Z1_COVER",
      nodes,z_budget_partials,exact_z1_covers,costas_rejected_placements,ms);
    fflush(stdout); }
  return 0; }
