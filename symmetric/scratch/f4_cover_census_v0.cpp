// f=4, M_LL=0 : does (F,r) admit any exact cover? Counts coverable pairs.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
using namespace std;
static const int N=32,R=15;
static int F[4],Om; static unsigned used; static long long SUMT;
static vector<int> dom[16]; static int order[16],nord; static int cur[16];
static bool found;
static void rec(int idx,long long rem){
  if(found) return;
  if(idx==nord){ if(rem==0) found=true; return; }
  int d=order[idx];
  for(size_t k=0;k<dom[d].size();k++){ int m=dom[d][k];
    int a=(m-d)/2,b=(m+d)/2;
    if((used>>a&1)||(used>>b&1)) continue;
    if(rem-m<0) continue;
    cur[d]=m; used|=(1u<<a)|(1u<<b);
    rec(idx+1,rem-m);
    used&=~((1u<<a)|(1u<<b));
    if(found) return; }
}
int main(int argc,char**argv){
  FILE*f=fopen(argv[1],"r"); int p0,p1,p2,p3,r; long long tot=0,cov=0;
  while(fscanf(f,"%d %d %d %d %d",&p0,&p1,&p2,&p3,&r)==5){
    tot++; F[0]=p0;F[1]=p1;F[2]=p2;F[3]=p3; Om=r;
    long long SF=p0+p1+p2+p3;
    // anchors
    bool anc[70]; memset(anc,0,sizeof anc);
    for(int i=0;i<4;i++) anc[2*F[i]]=true;
    for(int i=0;i<4;i++) for(int j=i+1;j<4;j++) anc[F[i]+F[j]]=true;
    bool isF[32]; memset(isF,0,sizeof isF); for(int i=0;i<4;i++) isF[F[i]]=true;
    nord=0; bool ok=true;
    for(int d=1;d<=15&&ok;d++){ if(d==r) continue; dom[d].clear();
      for(int m=d;m<=62-d;m++){ if((m-d)%2) continue; if(anc[m]) continue;
        int a=(m-d)/2,b=(m+d)/2; if(a<0||b>31) continue;
        if(isF[a]||isF[b]) continue;
        bool bad=false;
        for(int i=0;i<4;i++){ int x=abs(a-F[i]),y=abs(b-F[i]); if((x<y?x:y)>R){bad=true;break;} }
        if(bad) continue;
        dom[d].push_back(m); }
      if(dom[d].empty()) ok=false; else order[nord++]=d; }
    if(!ok) continue;
    // most-constrained first
    for(int i=0;i<nord;i++) for(int j=i+1;j<nord;j++)
      if(dom[order[j]].size()<dom[order[i]].size()){int t=order[i];order[i]=order[j];order[j]=t;}
    used=0; for(int i=0;i<4;i++) used|=1u<<F[i];
    found=false; rec(0,496-SF);
    if(found) cov++;
    if(tot%500==0){ printf("  %lld tested, %lld coverable\n",tot,cov); fflush(stdout); }
  }
  printf("pairs tested=%lld  coverable=%lld  (%.1f%%)\n",tot,cov,100.0*(double)cov/(double)tot);
  return 0; }
