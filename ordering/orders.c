/* Same exact Costas search under different column orders.
   usage: orders MODE N    MODE = l2r | outin | midout | mrv
   A node is a placed dot. Displacements are stored with positive horizontal lag. Symmetry: the first placed
   column's row <= (N-1)/2 (vertical complement), valid whichever column is placed first.
   mrv: choose the unassigned column with fewest legal rows; a column with none ends the branch (forward checking). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
static int N, mode, row[40], ord[40], placed[40], np;   /* row[c] = -1 if unassigned */
static uint64_t used[40], rows; static long long nodes, sols;
static int ok(int c,int r){
  if(rows>>r&1) return 0;
  if(np==0 && r>(N-1)/2) return 0;
  for(int k=0;k<np;k++){ int c2=placed[k], r2=row[c2];
    int lag = c>c2? c-c2 : c2-c, d = c>c2? r-r2 : r2-r;
    if(used[lag]>>(d+N-1)&1) return 0; }
  /* the new dot's own pairs at equal lag L, one to each side, must differ: r is not the midpoint (Ladendorf) */
  for(int L=1; c-L>=0 && c+L<N; L++) if(row[c-L]>=0 && row[c+L]>=0 && 2*r==row[c-L]+row[c+L]) return 0;
  return 1;
}
static void put(int c,int r){ for(int k=0;k<np;k++){ int c2=placed[k], r2=row[c2];
    int lag = c>c2? c-c2 : c2-c, d = c>c2? r-r2 : r2-r; used[lag]|=1ULL<<(d+N-1); }
  row[c]=r; rows|=1ULL<<r; placed[np++]=c; }
static void take(int c){ np--; int r=row[c]; rows&=~(1ULL<<r); row[c]=-1;
  for(int k=0;k<np;k++){ int c2=placed[k], r2=row[c2];
    int lag = c>c2? c-c2 : c2-c, d = c>c2? r-r2 : r2-r; used[lag]&=~(1ULL<<(d+N-1)); } }
static void dfs(int depth){
  if(depth==N){ sols++; return; }
  int c;
  if(mode<3) c=ord[depth];
  else { int best=-1,bc=99;                       /* minimum remaining values, with forward checking */
    for(int x=0;x<N;x++) if(row[x]<0){ int cnt=0; for(int r=0;r<N;r++) cnt+=ok(x,r); if(cnt==0) return; if(cnt<bc){bc=cnt;best=x;} }
    c=best; }
  for(int r=0;r<N;r++) if(ok(c,r)){ put(c,r); nodes++; dfs(depth+1); take(c); }
}
int main(int argc,char**argv){
  const char*m=argv[1]; N=atoi(argv[2]); mode=!strcmp(m,"l2r")?0:!strcmp(m,"outin")?1:!strcmp(m,"midout")?2:3;
  for(int i=0;i<N;i++) row[i]=-1;
  if(mode==0) for(int i=0;i<N;i++) ord[i]=i;
  if(mode==1){ int a=0,b=N-1,k=0; while(a<=b){ ord[k++]=a++; if(a<=b) ord[k++]=b--; } }
  if(mode==2){ int k=0, lo=(N-1)/2, hi=lo+1; while(k<N){ if(lo>=0) ord[k++]=lo--; if(k<N && hi<N) ord[k++]=hi++; } }
  struct timespec t0,t1; clock_gettime(CLOCK_MONOTONIC,&t0); dfs(0); clock_gettime(CLOCK_MONOTONIC,&t1);
  printf("%s n=%d nodes=%lld solutions=%lld seconds=%.2f\n",m,N,nodes,sols,(t1.tv_sec-t0.tv_sec)+1e-9*(t1.tv_nsec-t0.tv_nsec));
  return 0;
}
