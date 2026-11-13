/* Same left-to-right tree as estimate/costas_tree.c, but candidate rows are computed bit-parallel:
   forbidden rows at column c = used rows | OR over earlier columns i of (used[c-i] shifted into row coordinates).
   Row r conflicts with column i iff difference r-p[i] is already used at lag c-i, i.e. bit (r-p[i]+N-1) of used[c-i];
   so the forbidden-row mask from column i is used[c-i] >> (N-1-p[i]), truncated to N bits.
   usage: fast exact N | fast rate N SECONDS */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
static int N, p[40]; static uint64_t used[40], rows, MASK; static long long nodes, sols, lev[40]; static double tstop; static int timed;
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+1e-9*t.tv_nsec; }
static void dfs(int c){
  if(c==N){ sols++; return; }
  if(timed && (nodes&0xFFFFF)==0 && now()>tstop) return;
  uint64_t forb=rows;
  for(int i=0;i<c;i++) forb |= used[c-i] >> (N-1-p[i]);
  uint64_t cand = ~forb & MASK;
  if(c==0) cand &= (1ULL<<((N-1)/2+1))-1;            /* vertical-complement symmetry: p0 <= (N-1)/2 */
  while(cand){
    int r=__builtin_ctzll(cand); cand&=cand-1;
    for(int i=0;i<c;i++) used[c-i] |= 1ULL<<(r-p[i]+N-1);
    p[c]=r; rows|=1ULL<<r; nodes++; lev[c+1]++;
    dfs(c+1);
    rows&=~(1ULL<<r); for(int i=0;i<c;i++) used[c-i] &= ~(1ULL<<(r-p[i]+N-1));
    if(timed && now()>tstop) return;
  }
}
int main(int argc,char**argv){
  N=atoi(argv[2]); MASK=(N==64)?~0ULL:((1ULL<<N)-1);
  double t=now();
  if(!strcmp(argv[1],"rate")){ timed=1; tstop=t+atof(argv[3]); }
  dfs(0);
  printf("n=%d",N); for(int k=1;k<=N;k++) printf(" %lld",lev[k]); printf("\n");
  return 0;
}
