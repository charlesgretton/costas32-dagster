// f=2, M_LL=0 with the cycle-centre lemmas added:
//   (5) m_d = a_d+b_d  not in {2p, p+q, 2q}
//   (6) all m_d pairwise distinct
#include <cstdio>
#include <cstring>
#include <cstdlib>
using namespace std;
static const int N=32,R=15;
static int P,Q,dom[16][40],nd[16],cur[16];
static unsigned used; static unsigned long long midused;
static long long nmatch=0,ncostas=0,nodes=0,nmcostas=0,nk1=0,nfgfs=0; static long long hist[40]={0};
static int h[N];
static bool costas(){
  for(int s=1;s<N;s++){ unsigned long long m=0;
    for(int i=0;i+s<N;i++){ int v=h[i+s]-h[i]+N; if(m>>v&1) return false; m|=1ULL<<v; } }
  return true; }
static void rec(unsigned rem){
  nodes++;
  if(!rem){ nmatch++;
    { // centre sequence m_d = 2a_d + d : fixed-gap difference rows injective?
      int m[16]; for(int d=1;d<=15;d++) m[d]=2*cur[d]+d;
      bool k1=true, all=true;
      for(int k=1;k<=14&&all;k++){ int seen[200]; int ns=0;
        for(int d=1;d+k<=15;d++){ int v=m[d+k]-m[d]; int j;
          for(j=0;j<ns;j++) if(seen[j]==v) break;
          if(j<ns){ all=false; if(k==1) k1=false; break; }
          seen[ns++]=v; } }
      if(k1) nk1++;
      if(all){ nmcostas++;
        // fixed-sum fibres: for each s, m_e-m_d over pairs d<e with d+e=s must be distinct
        int firstfail=-1;
        for(int S=3;S<=29&&firstfail<0;S++){
          int vals[20],nv=0; bool bad=false;
          for(int d=1;d<=15&&!bad;d++){ int e=S-d; if(e<=d||e>15) continue;
            int v=m[e]-m[d]; for(int j=0;j<nv;j++) if(vals[j]==v){bad=true;break;}
            if(!bad) vals[nv++]=v; }
          if(bad) firstfail=S; }
        if(firstfail<0){ nfgfs++;
          printf("SURVIVOR p=%d q=%d m=",P,Q);
          for(int d=1;d<=15;d++) printf(" %d",m[d]); printf("\n"); fflush(stdout);
        } else hist[firstfail]++;
      }
    }
    memset(h,0,sizeof h); h[P]=P; h[Q]=Q;
    for(int d=1;d<=15;d++){ int a=cur[d]; h[a]=a+d; h[a+d]=a; }
    if(costas()){ ncostas++; printf("*** COSTAS p=%d q=%d:",P,Q);
      for(int i=0;i<N;i++) printf(" %d",h[i]); printf("\n"); }
    return; }
  int best=-1,bc=1<<30;
  for(int d=1;d<=15;d++){ if(!(rem>>d&1)) continue; int c=0;
    for(int k=0;k<nd[d];k++){ int a=dom[d][k];
      if((used>>a&1)||(used>>(a+d)&1)) continue;
      int m=2*a+d; if(midused>>m&1) continue;   // m has parity of d; index by m>>1 is not injective
      c++; }
    if(c<bc){bc=c;best=d;} }
  if(bc==0) return;
  int d=best;
  for(int k=0;k<nd[d];k++){ int a=dom[d][k];
    if((used>>a&1)||(used>>(a+d)&1)) continue;
    int m=2*a+d;
    if(midused>>m&1) continue;
    cur[d]=a; used|=(1u<<a)|(1u<<(a+d)); midused|=1ULL<<m;
    rec(rem&~(1u<<d));
    used&=~((1u<<a)|(1u<<(a+d))); midused&=~(1ULL<<m); }
}
int main(){
  int examined=0,withmatch=0;
  for(P=0;P<N;P++) for(Q=P+2;Q<N;Q+=2){
    if(Q-P>R) continue; examined++;
    bool ok=true;
    for(int d=1;d<=15&&ok;d++){ nd[d]=0;
      for(int a=0;a+d<N;a++){ int b=a+d;
        if(a==P||a==Q||b==P||b==Q) continue;
        int mp=abs(a-P)<abs(b-P)?abs(a-P):abs(b-P);
        int mq=abs(a-Q)<abs(b-Q)?abs(a-Q):abs(b-Q);
        if(mp>R||mq>R) continue;
        int m=a+b;
        if(m==2*P||m==2*Q||m==P+Q) continue;        // lemma (5)
        dom[d][nd[d]++]=a; }
      if(!nd[d]) ok=false; }
    if(!ok) continue;
    long long before=nmatch;
    used=(1u<<P)|(1u<<Q); midused=0;
    rec(0xFFFEu);

    if(nmatch>before) withmatch++;
  }
  printf("matchings=%lld  k1-pass=%lld  FG-pass=%lld  FG+FS-pass=%lld  COSTAS=%lld\n",nmatch,nk1,nmcostas,nfgfs,ncostas);
  printf("first fixed-sum failure by s:\n"); for(int S=3;S<=29;S++) if(hist[S]) printf("  s=%2d : %lld\n",S,hist[S]);
  return 0; }
