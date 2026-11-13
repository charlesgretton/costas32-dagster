// Independent completion test: value-ordered DFS over ROWS (not columns), with
// a different conflict representation, to cross-check the infeasible count.
#include <cstdio>
#include <cstdlib>
#include <cstring>
int n=12,s=6,p[20]; unsigned used; signed char seen[64][64];
bool ok(int c,int r){ for(int i=0;i<c;i++){ int d=c-i,v=r-p[i]+n; if(seen[d][v]) return false;} return true;}
void set_(int c,int r,int x){ for(int i=0;i<c;i++) seen[c-i][r-p[i]+n]+=x; }
bool comp(int c){ if(c==n) return true;
  for(int r=n-1;r>=0;r--){ if(used>>r&1)continue; if(!ok(c,r))continue;
    p[c]=r; used|=1u<<r; set_(c,r,1);
    if(comp(c+1)){ used&=~(1u<<r); set_(c,r,-1); return true;}
    used&=~(1u<<r); set_(c,r,-1);} return false;}
long long V=0,I=0,F=0;
void gen(int c){ if(c==s){ V++; if(comp(s)) F++; else I++; return;}
  for(int r=0;r<n;r++){ if(used>>r&1)continue; if(!ok(c,r))continue;
    p[c]=r; used|=1u<<r; set_(c,r,1); gen(c+1); used&=~(1u<<r); set_(c,r,-1);} }
int main(int argc,char**argv){ if(argc>2){n=atoi(argv[1]);s=atoi(argv[2]);}
  gen(0); printf("independent: valid=%lld infeasible=%lld feasible=%lld\n",V,I,F); return 0;}
