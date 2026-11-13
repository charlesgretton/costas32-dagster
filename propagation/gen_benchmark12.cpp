// F3 step 1: regenerate the order-12 infeasible-configuration benchmark.
// A configuration is a Costas-valid assignment of the first s columns.
// Infeasible = no completion to a full order-12 Costas array.
#include <cstdlib>
#include <cstdio>
#include <cstdint>
#include <vector>
using namespace std;
int n=12,s=6; int p[16]; uint64_t used, dmask[32];
bool place(int c,int r){
  uint64_t add[32]; int k=0;
  for(int i=0;i<c;i++){ int d=c-i, v=r-p[i]+n; if(dmask[d]>>v&1){ for(int j=0;j<k;j++); return false;} add[k++]= (uint64_t)d<<32 | v; }
  for(int i=0;i<c;i++){ int d=c-i, v=r-p[i]+n; dmask[d]|=1ULL<<v; }
  return true;
}
void unplace(int c,int r){ for(int i=0;i<c;i++){ int d=c-i,v=r-p[i]+n; dmask[d]&=~(1ULL<<v);} }
bool extend(int c){
  if(c==n) return true;
  for(int r=0;r<n;r++){
    if(used>>r&1) continue;
    if(!place(c,r)) continue;
    p[c]=r; used|=1ULL<<r;
    if(extend(c+1)) { used&=~(1ULL<<r); unplace(c,r); return true; }
    used&=~(1ULL<<r); unplace(c,r);
  }
  return false;
}
long long total=0, infeas=0; vector<vector<int>> bad;
void gen(int c){
  if(c==s){ total++; if(!extend(s)){ infeas++; bad.push_back(vector<int>(p,p+s)); } return; }
  for(int r=0;r<n;r++){
    if(used>>r&1) continue;
    if(!place(c,r)) continue;
    p[c]=r; used|=1ULL<<r; gen(c+1); used&=~(1ULL<<r); unplace(c,r);
  }
}
int main(int argc,char**argv){ if(argc>1) s=atoi(argv[1]);
  gen(0);
  printf("n=%d s=%d  Costas-valid prefixes=%lld  infeasible=%lld  (%.2f%%)\n",n,s,total,infeas,100.0*infeas/total);
  FILE*f=fopen("/tmp/infeasible12.txt","w");
  for(auto&v:bad){ for(int x:v) fprintf(f,"%d ",x); fprintf(f,"\n"); }
  fclose(f); return 0; }
