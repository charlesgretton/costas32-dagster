/* count nodes of the Costas search below a prefix: subtree N p0 p1 ... (same tree as estimate/costas_tree.c) */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static int N,p[40]; static uint64_t used[40],rows; static long long cnt;
static int ok(int c,int r){ if(rows>>r&1) return 0; if(c==0 && r>(N-1)/2) return 0;
  for(int i=0;i<c;i++) if(used[c-i]>>(r-p[i]+N-1)&1) return 0; return 1; }
static void pl(int c,int r){ p[c]=r; rows|=1ULL<<r; for(int i=0;i<c;i++) used[c-i]|=1ULL<<(r-p[i]+N-1); }
static void un(int c,int r){ rows&=~(1ULL<<r); for(int i=0;i<c;i++) used[c-i]&=~(1ULL<<(r-p[i]+N-1)); }
static void dfs(int c){ if(c==N) return; for(int r=0;r<N;r++) if(ok(c,r)){ pl(c,r); cnt++; dfs(c+1); un(c,r);} }
int main(int argc,char**argv){ N=atoi(argv[1]); int k=argc-2; for(int c=0;c<k;c++) pl(c,atoi(argv[2+c])); dfs(k); printf("%lld\n",cnt); return 0; }
