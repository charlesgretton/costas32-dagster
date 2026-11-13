// Mode A (ordinary exact cover) and Mode B (exact cover with global Z==1),
// counted in SEPARATE recursions so they cannot be conflated.
#include <cstdio>
#include <cstdlib>
#include <vector>
using namespace std;
static int U,V,L; static int hh[32];
static vector<unsigned> ed[16]; static vector<pair<int,int>> ep[16];
static unsigned used; static long long cnt; static bool stopAtFirst;
static int ordA[16];
static bool zmode; static int Zp;
static bool addOK(int a,int b){            // returns false if Z budget exceeded
  int back=0;
  int nc[2]={a,b}, nh[2]={b,a};
  for(int t=0;t<2;t++){ int i=nc[t];
    for(int j=0;j<32;j++){ if(!(used>>j&1)) continue; if(t==1&&j==a) continue;
      int d=i>j?i-j:j-i; if(!d) continue;
      int e=nh[t]>hh[j]?nh[t]-hh[j]:hh[j]-nh[t];
      if(d>=16&&e>=16){ Zp++; back++; if(Zp>1){ Zp-=back; return false; } } }
    used|=1u<<i; hh[i]=nh[t]; }
  return true; }
static void rec(int k){
  if(k==15){ if(!zmode||Zp==1){ cnt++;
      if(zmode&&cnt==1){ printf("WITNESS %d-%d",U,V);
        for(int i=0;i<32;i++) if(hh[i]>i&&!(i==U)) printf(" %d-%d",i,hh[i]);
        printf("\n"); } }
    return; }
  int d=ordA[k];
  for(size_t q=0;q<ed[d].size();q++){
    unsigned m=ed[d][q]; if(m&used) continue;
    int a=ep[d][q].first,b=ep[d][q].second;
    if(zmode){ int z0=Zp; unsigned u0=used;
      if(!addOK(a,b)) continue;
      rec(k+1); used=u0; Zp=z0; }
    else { used|=m; rec(k+1); used&=~m; }
    if(stopAtFirst&&cnt) return; } }
int main(int argc,char**argv){
  printf("L,u,modeA_ordinary_covers,modeB_Z1_covers\n");
  L=atoi(argv[1]); U=atoi(argv[2]); {
    V=U+L;
    for(int d=1;d<=15;d++){ ed[d].clear(); ep[d].clear();
      for(int a=0;a+d<32;a++){ int b=a+d;
        if(a==U||a==V||b==U||b==V) continue;
        ed[d].push_back((1u<<a)|(1u<<b)); ep[d].push_back({a,b}); } }
    for(int i=1;i<=15;i++) ordA[i-1]=i;
    for(int i=0;i<15;i++) for(int j=i+1;j<15;j++)
      if(ed[ordA[j]].size()<ed[ordA[i]].size()){int t=ordA[i];ordA[i]=ordA[j];ordA[j]=t;}
    stopAtFirst=true;
    zmode=false; used=(1u<<U)|(1u<<V); cnt=0; rec(0); long long A=cnt;
    zmode=true;  used=(1u<<U)|(1u<<V); for(int i=0;i<32;i++)hh[i]=0;
    hh[U]=V; hh[V]=U; Zp=1; cnt=0; rec(0); long long B=cnt;
    printf("%d,%d,%lld,%lld\n",L,U,A,B); fflush(stdout); }
  return 0; }
