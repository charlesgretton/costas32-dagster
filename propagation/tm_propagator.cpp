// F3: position-value domain propagators + T_m coupling, order-n benchmark.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <algorithm>
#include <chrono>
using namespace std;
static int n=12,s=6;
static int p[20]; static unsigned used; static unsigned dmask[24];
static inline bool placeOK(int c,int r){for(int i=0;i<c;i++){int d=c-i,v=r-p[i]+n;if(dmask[d]>>v&1)return false;}return true;}
static inline void doPlace(int c,int r){for(int i=0;i<c;i++)dmask[c-i]|=1u<<(r-p[i]+n);}
static inline void unPlace(int c,int r){for(int i=0;i<c;i++)dmask[c-i]&=~(1u<<(r-p[i]+n));}
static bool complete(int c){if(c==n)return true;for(int r=0;r<n;r++){if(used>>r&1)continue;if(!placeOK(c,r))continue;
 p[c]=r;used|=1u<<r;doPlace(c,r);if(complete(c+1)){used&=~(1u<<r);unPlace(c,r);return true;}used&=~(1u<<r);unPlace(c,r);}return false;}

static int mt[32];
static bool aug(const vector<unsigned>&D,int u,unsigned&seen,const vector<int>&R){
 for(size_t k=0;k<R.size();k++){ if(!(D[u]>>k&1))continue; if(seen>>k&1)continue; seen|=1u<<k;
  if(mt[k]<0||aug(D,mt[k],seen,R)){mt[k]=u;return true;} } return false;}
static bool perfectMatch(const vector<unsigned>&D,const vector<int>&R){
 memset(mt,-1,sizeof(mt));
 for(size_t u=0;u<D.size();u++){unsigned seen=0;if(!aug(D,(int)u,seen,R))return false;}return true;}

// unary filter + AC on binary (prefix-conflict) constraints
static bool filterAC(vector<unsigned>&D,const vector<int>&R,const vector<int>&pos){
 int U=pos.size(),K=R.size();
 for(int u=0;u<U;u++){ unsigned nd=0;
  for(int k=0;k<K;k++){ int r=R[k]; bool ok=true;
   for(int a=0;a<s;a++){int d=pos[u]-a; if(d<=0)continue; int v=r-p[a]+n; if(dmask[d]>>v&1){ok=false;break;}}
   if(ok) nd|=1u<<k; }
  D[u]=nd; if(!nd) return false; }
 bool ch=true;
 while(ch){ ch=false;
  for(int u=0;u<U;u++) for(int w=0;w<U;w++){ if(u==w)continue; int d=pos[w]-pos[u]; if(d<=0)continue;
   unsigned nd=0;
   for(int k=0;k<K;k++){ if(!(D[u]>>k&1))continue; bool sup=false;
    for(int l=0;l<K;l++){ if(l==k||!(D[w]>>l&1))continue; int v=R[l]-R[k]+n; if(!(dmask[d]>>v&1)){sup=true;break;} }
    if(sup) nd|=1u<<k; }
   if(nd!=D[u]){D[u]=nd;ch=true; if(!nd)return false;} } }
 return true;
}
long long nV=0,nI=0,nF=0,dL1=0,dL2=0,dL3=0,dTM=0,f1=0,f2=0,f3=0,ftm=0;
static void gen(int c){
 if(c==s){ nV++;
  vector<int> R,pos; for(int r=0;r<n;r++) if(!(used>>r&1)) R.push_back(r);
  for(int b=s;b<n;b++) pos.push_back(b);
  int U=pos.size(),K=R.size();
  // L1 unary + matching
  vector<unsigned> D1(U,0);
  bool l1=false;
  for(int u=0;u<U;u++){unsigned nd=0;
   for(int k=0;k<K;k++){int r=R[k];bool ok=true;
    for(int a=0;a<s;a++){int d=pos[u]-a;int v=r-p[a]+n;if(dmask[d]>>v&1){ok=false;break;}}
    if(ok)nd|=1u<<k;}
   D1[u]=nd; if(!nd) l1=true;}
  if(!l1&&!perfectMatch(D1,R)) l1=true;
  // L2 = unary + AC + matching
  vector<unsigned> D2(U,0); bool l2=l1;
  if(!l2){ D2=D1; if(!filterAC(D2,R,pos)) l2=true; else if(!perfectMatch(D2,R)) l2=true; }
  // L3 = L2 + singleton shaving
  bool l3=l2;
  if(!l3){ bool ch=true;
   while(ch&&!l3){ ch=false;
    for(int u=0;u<U&&!l3;u++) for(int k=0;k<K;k++){ if(!(D2[u]>>k&1))continue;
     vector<unsigned> T=D2; T[u]=1u<<k;
     if(!filterAC(T,R,pos)||!perfectMatch(T,R)){ D2[u]&=~(1u<<k); ch=true; if(!D2[u]){l3=true;break;} } } } }
  // T_m coupling on top of L2
  bool tm=l2;
  if(!tm){
   vector<int> Rs=R; sort(Rs.begin(),Rs.end());
   vector<long long> pre_lo(K+1,0), pre_hi(K+1,0);
   for(int k=1;k<=K;k++){ pre_lo[k]=pre_lo[k-1]+Rs[k-1]; pre_hi[k]=pre_hi[k-1]+Rs[K-k]; }
   int pre[20]; pre[0]=0; for(int i=0;i<s;i++) pre[i+1]=pre[i]+p[i];
   for(int m=1;m<n&&!tm;m++){
    long long det=0; vector<int> pool; int ku=0;
    for(int i=0;i+m<n;i++){ int a=i,b=i+m;
     if(a<s&&b<s){det+=p[b]-p[a];continue;}
     ku++;
     if(a<s){ int u=b-s; for(int k=0;k<K;k++) if(D2[u]>>k&1) pool.push_back(R[k]-p[a]); }
     else   { int u=a-s,w=b-s; for(int k=0;k<K;k++) if(D2[u]>>k&1) for(int l=0;l<K;l++) if(l!=k&&(D2[w]>>l&1)) pool.push_back(R[l]-R[k]); } }
    if(!ku) continue;
    sort(pool.begin(),pool.end()); pool.erase(unique(pool.begin(),pool.end()),pool.end());
    if((int)pool.size()<ku){tm=true;break;}
    long long lo=det,hi=det;
    for(int i=0;i<ku;i++) lo+=pool[i];
    for(int i=0;i<ku;i++) hi+=pool[pool.size()-1-i];
    int fk=min(m,s), fR=m-fk, lk=max(0,s-(n-m)), lR=m-lk;
    if(fR<0||lR<0||fR>K||lR>K) continue;
    long long lks=0; for(int i=max(0,n-m);i<s;i++) lks+=p[i];
    long long tlo=(lks+pre_lo[lR])-(pre[fk]+pre_hi[fR]);
    long long thi=(lks+pre_hi[lR])-(pre[fk]+pre_lo[fR]);
    if(tlo>thi) continue;
    if(hi<tlo||lo>thi) tm=true; } }
  unsigned su=used; unsigned sd[24]; memcpy(sd,dmask,sizeof(dmask));
  bool feas=complete(s); used=su; memcpy(dmask,sd,sizeof(dmask));
  if(feas){nF++; f1+=l1;f2+=l2;f3+=l3;ftm+=tm;} else {nI++; dL1+=l1;dL2+=l2;dL3+=l3;dTM+=tm;}
  return; }
 for(int r=0;r<n;r++){ if(used>>r&1)continue; if(!placeOK(c,r))continue;
  p[c]=r;used|=1u<<r;doPlace(c,r); gen(c+1); used&=~(1u<<r);unPlace(c,r);} }
int main(int argc,char**argv){ if(argc>1)n=atoi(argv[1]); if(argc>2)s=atoi(argv[2]);
 auto t0=chrono::steady_clock::now(); gen(0);
 double el=chrono::duration<double>(chrono::steady_clock::now()-t0).count();
 printf("n=%d s=%d  valid=%lld infeasible=%lld feasible=%lld  (%.1fs)\n",n,s,nV,nI,nF,el);
 printf("  L1 unary+matching : %8lld/%lld = %6.3f%%   fp=%lld\n",dL1,nI,100.0*dL1/nI,f1);
 printf("  L2 +arc consist.  : %8lld/%lld = %6.3f%%   fp=%lld\n",dL2,nI,100.0*dL2/nI,f2);
 printf("  L3 +shaving       : %8lld/%lld = %6.3f%%   fp=%lld\n",dL3,nI,100.0*dL3/nI,f3);
 printf("  L2 + T_m coupling : %8lld/%lld = %6.3f%%   fp=%lld\n",dTM,nI,100.0*dTM/nI,ftm);
 printf("  marginal T_m over L2: %+lld (%+.3f pp)   T_m vs L3: %+lld\n",dTM-dL2,100.0*(dTM-dL2)/nI,dTM-dL3);
 printf("  SOUNDNESS: %s\n",(f1==0&&f2==0&&f3==0&&ftm==0)?"PASS":"FAIL");
 return 0;}
