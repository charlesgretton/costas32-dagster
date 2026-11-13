// Order-n Costas arrays that are transpose-symmetric (h = h^{-1}, an involution).
// Rotational and axial stabilisers are impossible (see note), so this is the
// only symmetry class that can occur.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>
using namespace std;
static int n; static int p[70]; static unsigned long long used, mask[70];
static int pc[70],np;
static inline bool add1(int c,int r,int*U,int&nu){
  nu=0;
  for(int t=0;t<np;t++){int i=pc[t]; int d=c>i?c-i:i-c; int v=(c>i?r-p[i]:p[i]-r)+n;
    if(mask[d]>>v&1ULL){for(int u=0;u<nu;u+=2)mask[U[u]]&=~(1ULL<<U[u+1]);return false;}
    mask[d]|=1ULL<<v; U[nu++]=d; U[nu++]=v;}
  p[c]=r; pc[np++]=c; used|=1ULL<<r; return true;
}
static inline void del1(int*U,int nu,int r){for(int i=0;i<nu;i+=2)mask[U[i]]&=~(1ULL<<U[i+1]); np--; used&=~(1ULL<<r);}
static long long nodes=0,sols=0; static int nfix=0, FMAX=99, maxfix=0; static long long fixhist[40]={0};
static void go(int c){
  nodes++;
  while(c<n && (used>>c&1)) c++;
  if(c==n){sols++;return;}
  for(int r=c;r<n;r++){
    if(used>>r&1) continue;
    int U1[512],n1,U2[512],n2;
    if(!add1(c,r,U1,n1)) continue;
    if(r==c){ if(nfix<FMAX){ nfix++; if(nfix>maxfix)maxfix=nfix; fixhist[nfix]++; go(c+1); nfix--; } del1(U1,n1,r); continue; }
    if(add1(r,c,U2,n2)){ go(c+1); del1(U2,n2,c); }
    del1(U1,n1,r);
  }
}
int main(int argc,char**argv){ n=atoi(argv[1]);
  if(argc>2){ int OGR[12]={0,0,1,3,6,11,17,25,34,44,55,72};
    int cb=0; while((cb+1)*cb/2<=n-1) cb++;
    for(int f=0;f<=cb;f++) if(f%2==n%2 && (f<2||OGR[f]<=n-1)) FMAX=f; }
  auto t0=chrono::steady_clock::now(); memset(mask,0,sizeof(mask)); used=0; np=0; nodes=0; sols=0;
  go(0);
  double el=chrono::duration<double>(chrono::steady_clock::now()-t0).count();
  printf("n=%2d nodes=%-11lld arrays=%-4lld FMAX=%d maxfix_reached=%d  nodes_by_fixcount:",n,nodes,sols,FMAX,maxfix);
  for(int i=1;i<=8;i++) printf(" %d:%lld",i,fixhist[i]); printf("\n");
  return 0;}
