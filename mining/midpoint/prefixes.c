/* all locally Costas-consistent prefixes of length K at order N (no symmetry restriction), one per line */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static int N,K,p[40]; static uint64_t used[40],rows,MASK;
static void dfs(int c){
  if(c==K){ for(int i=0;i<K;i++) printf(i?" %d":"%d",p[i]); printf("\n"); return; }
  uint64_t f=rows; for(int i=0;i<c;i++) f|=used[c-i]>>(N-1-p[i]);
  for(uint64_t m=~f&MASK;m;m&=m-1){ int r=__builtin_ctzll(m);
    for(int i=0;i<c;i++) used[c-i]|=1ULL<<(r-p[i]+N-1); p[c]=r; rows|=1ULL<<r; dfs(c+1);
    rows&=~(1ULL<<r); for(int i=0;i<c;i++) used[c-i]&=~(1ULL<<(r-p[i]+N-1)); }
}
int main(int a,char**v){ N=atoi(v[1]); K=atoi(v[2]); MASK=(1ULL<<N)-1; dfs(0); return 0; }
