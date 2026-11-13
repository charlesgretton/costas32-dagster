// Exhaustive search for order-n Costas arrays with a non-trivial D4 stabiliser.
//   rot180 : h_i = n-1-h_{n-1-i}   (place cols 0..n/2-1, partner forced)
//   invol  : h = h^{-1}            (transpose-symmetric)
//   anti   : h_i = n-1-h^{-1}(n-1-i)
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>
using namespace std;
static int n=32; static int p[64]; static unsigned long long used;
static unsigned long long dm[70][2];
static inline bool getb(int d,int v){return (dm[d][v>>6]>>(v&63))&1ULL;}
static inline void setb(int d,int v){dm[d][v>>6]|=1ULL<<(v&63);}
static inline void clrb(int d,int v){dm[d][v>>6]&=~(1ULL<<(v&63));}
static long long nodes=0,sols=0;
// place dot at column c with value r against all already-placed columns in list
static int plc[64],np;
static bool tryAdd(int c,int r,int*undo,int&nu){
  nu=0;
  for(int t=0;t<np;t++){int i=plc[t];int d=c-i,v=r-p[i]+n; if(d<0){d=-d;v=-v+2*n-2*n; v=p[i]-r+n;}
    if(getb(d,v)){ for(int u=0;u<nu;u+=2) clrb(undo[u],undo[u+1]); return false;}
    setb(d,v); undo[nu++]=d; undo[nu++]=v;}
  return true;
}
static void undoAll(int*u,int nu){for(int i=0;i<nu;i+=2) clrb(u[i],u[i+1]);}
static void rot180(int c){
  nodes++;
  if(c==n/2){sols++;return;}
  int partner=n-1-c;
  for(int r=0;r<n;r++){
    int pr=n-1-r;
    if(used>>r&1) continue; if(used>>pr&1) continue; if(r==pr) continue;
    int u1[256],nu1,u2[256],nu2;
    if(!tryAdd(c,r,u1,nu1)) continue;
    p[c]=r; plc[np++]=c; used|=1ULL<<r;
    if(tryAdd(partner,pr,u2,nu2)){
      p[partner]=pr; plc[np++]=partner; used|=1ULL<<pr;
      rot180(c+1);
      np--; used&=~(1ULL<<pr); undoAll(u2,nu2);
    }
    np--; used&=~(1ULL<<r); undoAll(u1,nu1);
  }
}
int main(int argc,char**argv){ if(argc>1)n=atoi(argv[1]);
  auto t0=chrono::steady_clock::now();
  memset(dm,0,sizeof(dm)); used=0; np=0;
  rot180(0);
  double el=chrono::duration<double>(chrono::steady_clock::now()-t0).count();
  printf("n=%2d rot180: nodes=%lld solutions=%lld  %.2fs\n",n,nodes,sols,el);
  return 0;}
