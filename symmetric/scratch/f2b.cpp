// f=2, M_LL=0 branch: rainbow perfect matching with one edge of each length 1..15,
// plus the neighbourhood-cover condition, then the full Costas test.
#include <cstdio>
#include <cstring>
#include <cstdlib>
using namespace std;
static const int N=32,R=15;
static int P,Q,dom[16][40],nd[16],cur[16];
static unsigned used;
static long long nmatch=0,ncostas=0;
static int h[N];
static bool costas(){
  for(int s=1;s<N;s++){ unsigned long long m=0;
    for(int i=0;i+s<N;i++){ int v=h[i+s]-h[i]+N; if(m>>v&1) return false; m|=1ULL<<v; } }
  return true;
}
static void rec(unsigned rem){
  if(!rem){ nmatch++;
    memset(h,0,sizeof h); h[P]=P; h[Q]=Q;
    for(int d=1;d<=15;d++){ int a=cur[d]; h[a]=a+d; h[a+d]=a; }
    if(costas()){ ncostas++; printf("COSTAS CANDIDATE p=%d q=%d:",P,Q);
      for(int i=0;i<N;i++) printf(" %d",h[i]); printf("\n"); }
    return; }
  int best=-1,bc=1<<30;
  for(int d=1;d<=15;d++){ if(!(rem>>d&1)) continue; int c=0;
    for(int k=0;k<nd[d];k++){ int a=dom[d][k]; if(!(used>>a&1)&&!(used>>(a+d)&1)) c++; }
    if(c<bc){bc=c;best=d;} }
  if(bc==0) return;
  int d=best;
  for(int k=0;k<nd[d];k++){ int a=dom[d][k];
    if((used>>a&1)||(used>>(a+d)&1)) continue;
    cur[d]=a; used|=(1u<<a)|(1u<<(a+d));
    rec(rem&~(1u<<d));
    used&=~((1u<<a)|(1u<<(a+d))); }
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
        dom[d][nd[d]++]=a; }
      if(!nd[d]) ok=false; }
    if(!ok) continue;
    long long before=nmatch;
    used=(1u<<P)|(1u<<Q);
    rec(0xFFFEu);
    printf("  p=%d q=%d cumulative_matchings=%lld costas=%lld\n",P,Q,nmatch,ncostas); fflush(stdout);
    if(nmatch>before) withmatch++;
  }
  printf("fixed-point pairs examined         : %d\n",examined);
  printf("pairs admitting a rainbow matching : %d\n",withmatch);
  printf("total rainbow matchings            : %lld\n",nmatch);
  printf("of which full Costas               : %lld\n",ncostas);
  return 0;
}
