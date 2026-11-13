// Cell 3 (Z=1T, f=2) integrated solver over canonical (L,u) roots.
// Fixed pair is ONE object; omitted length r branched inside the root.
// Gate 0 parity oracle built in; tuple recovery for Gate 1.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
using namespace std;
static const int N=32,R=15;
static int U,V,P_,Q_,Om;
static int hh[32]; static unsigned used; static int Zp;
static unsigned long long lagset[32][2]; static bool NOLAG1=false; static long long nodes,exact_z1_covers,fixed_pairs_considered,fixed_pairs_parity_rejected;
static inline bool ll(int i,int hi,int j,int hj){int d=i>j?i-j:j-i,e=hi>hj?hi-hj:hj-hi;return d>=16&&e>=16;}
static bool addPair(int a,int b,int hA,int hB,int&back){
  back=0; int nc[2]={a,b},nh[2]={hA,hB}; int cnt=(a==b)?1:2;
  for(int t=0;t<cnt;t++){int i=nc[t];
    for(int j=0;j<N;j++){ if(!(used>>j&1))continue; if(t==1&&j==a)continue;
      if(i==j) continue;
      if(ll(i,nh[t],j,hh[j])){Zp++;back++; if(Zp>1){Zp-=back;
        for(int s=0;s<t;s++) used&=~(1u<<nc[s]); return false;}}}
    used|=1u<<i; hh[i]=nh[t];}
  // lag-1 propagator: delta_i = h(i+1)-h(i) must be distinct
  // FULL incremental Costas oracle: every newly determined pair, every lag
  if(!NOLAG1){
   for(int t=0;t<cnt;t++){int i=nc[t];
    for(int j=0;j<N;j++){ if(!(used>>j&1)||j==i) continue; if(t==1&&j==a) continue;
      int lo=i<j?i:j, hi2=i<j?j:i; int s=hi2-lo; int dv=hh[hi2]-hh[lo]+N;
      if(lagset[s][dv>>6]>>(dv&63)&1) return false; } }
   for(int t=0;t<cnt;t++){int i=nc[t];
    for(int j=0;j<N;j++){ if(!(used>>j&1)||j==i) continue; if(t==1&&j==a) continue;
      int lo=i<j?i:j, hi2=i<j?j:i; int s=hi2-lo; int dv=hh[hi2]-hh[lo]+N;
      lagset[s][dv>>6]|=1ULL<<(dv&63); } } }
  return true;}
static int ordD[16],nOrd;
static void rec(int k){
  nodes++;
  if(k==nOrd){ if(Zp==1){ exact_z1_covers++;
      // CONTINGENCY: a lag-1 survivor must be emitted for offline full-Costas audit
      printf("LAG1_SURVIVOR root=L%d-u%d r=%d p=%d q=%d h=",V-U,U,Om,P_,Q_);
      for(int i=0;i<N;i++) printf("%d ",hh[i]);
      printf("status=REQUIRES_FULL_COSTAS_ORACLE\n"); fflush(stdout); }
    return; }
  int d=ordD[k];
  for(int a=0;a+d<N;a++){int b=a+d;
    if((used>>a&1)||(used>>b&1))continue;
    int zb,z0=Zp; unsigned u0=used; static unsigned long long LS[32][2]; __builtin_memcpy(LS,lagset,sizeof lagset);
    if(!addPair(a,b,b,a,zb)){Zp=z0;used=u0;__builtin_memcpy(lagset,LS,sizeof lagset);continue;}
    rec(k+1); used=u0; Zp=z0; __builtin_memcpy(lagset,LS,sizeof lagset);}
}
int main(int argc,char**argv){
  int L=atoi(argv[1]), u=atoi(argv[2]); if(argc>3) NOLAG1=true;
  U=u; V=u+L;
  long long tot_nodes=0, tot_cov=0, pairs=0, parity_rej=0;
  for(Om=1;Om<=15;Om++){
    for(P_=0;P_<N;P_++){ if(P_==U||P_==V)continue;
      for(Q_=P_+1;Q_<N&&Q_-P_<=R;Q_++){ if(Q_==U||Q_==V)continue;
        pairs++;
        if(Om%2 != (L+P_+Q_)%2){ parity_rej++; continue; }
        memset(hh,0,sizeof hh);
        used=(1u<<U)|(1u<<V)|(1u<<P_)|(1u<<Q_);
        hh[U]=V;hh[V]=U;hh[P_]=P_;hh[Q_]=Q_; Zp=0;
        // seed Z from the four placed coords
        for(int i=0;i<N;i++) if(used>>i&1) for(int j=i+1;j<N;j++) if(used>>j&1)
          if(ll(i,hh[i],j,hh[j])) Zp++;
        if(Zp>1) continue;
        __builtin_memset(lagset,0,sizeof lagset);
        for(int i=0;i<N;i++) if(used>>i&1) for(int j=i+1;j<N;j++) if(used>>j&1){int s=j-i,dv=hh[j]-hh[i]+N; if(lagset[s][dv>>6]>>(dv&63)&1) goto nextpair; lagset[s][dv>>6]|=1ULL<<(dv&63);}
        nOrd=0; for(int d=15;d>=1;d--) if(d!=Om) ordD[nOrd++]=d;
        nodes=0; exact_z1_covers=0;
        rec(0);
        tot_nodes+=nodes; tot_cov+=exact_z1_covers;
        nextpair:; } } }
  printf("L%d-u%d,%lld,%lld,%lld,%lld,%s\n",L,u,pairs,parity_rej,tot_nodes,tot_cov,
         tot_cov?"EXHAUSTED_WITH_Z1_COVERS":"EXHAUSTED_NO_Z1_COVER");
  return 0; }
