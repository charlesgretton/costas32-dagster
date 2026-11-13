/* Left-to-right bit-parallel Costas search with lookahead at every node, to measure how much each level
   of local consistency shrinks the tree (logical nodes) and costs (time).
   usage: binac MODE N      MODE 0 = none, 1 = forward checking, 2 = forward checking + binary displacement AC
   Binary AC: for unplaced columns i<j (lag L=j-i), row r in D_i needs a partner s in D_j with s != r, s unused,
   (L, s-r) not already used at lag L, no collision between the dots' new displacements to placed dots
   (s = r - p[c] + p[c+L] for placed c, c+L), and (L, s-r) not equal to i's new displacement at lag L
   (s = 2r - p[2i-j] if column 2i-j is placed). Unsupported rows are removed to a fixed point. (n <= 16.) */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
static int N, MODE, p[40]; static long long acut[41], fcut[41], vis[41], mind[41][41]; static uint64_t used[40], rows, MASK; static long long nodes, sols;
static inline uint64_t dom(int j,int k){ uint64_t f=rows; for(int i=0;i<k;i++) f|=used[j-i]>>(N-1-p[i]); return ~f&MASK; }
static uint64_t forb_s(int i,int j,int r,int k){
  int L=j-i; uint64_t f=rows|(1ULL<<r);
  f |= ((used[L]<<r)>>(N-1)) & MASK;                       /* (L, s-r) already used at lag L */
  for(int c=0;c+L<k;c++){ int s=r-p[c]+p[c+L]; if(s>=0&&s<N) f|=1ULL<<s; }   /* cross collision */
  int c=2*i-j; if(c>=0&&c<k){ int s=2*r-p[c]; if(s>=0&&s<N) f|=1ULL<<s; }    /* midpoint-type */
  return f;
}
static int lookahead(int k){       /* k columns placed; returns 0 if the node is dead */
  if(MODE==0) return 1;
  uint64_t D[40];
  for(int j=k;j<N;j++){ D[j]=dom(j,k); if(!D[j]){ fcut[k]++; return 0; } }
  if(MODE==1) return 1;
  int md=99; for(int j=k;j<N;j++){ int c=__builtin_popcountll(D[j]); if(c<md) md=c; }
  if(MODE==3){                         /* cheap: one pass, small-domain pairs only, emptiness of the pair relation */
    for(int i=k;i<N;i++){ int ci=__builtin_popcountll(D[i]); if(ci>3) continue;
      for(int j=i+1;j<N;j++){ int cj=__builtin_popcountll(D[j]); if(ci*cj>9) continue;
        int any=0; for(uint64_t m=D[i];m&&!any;m&=m-1){ int r=__builtin_ctzll(m); if(D[j]&~forb_s(i,j,r,k)) any=1; }
        if(!any) return 0; } }
    return 1; }
  int changed=1;
  while(changed){ changed=0;
    for(int i=k;i<N;i++) for(int j=i+1;j<N;j++){
      uint64_t Di=D[i], newDi=0, supJ=0;
      for(uint64_t m=Di;m;m&=m-1){ int r=__builtin_ctzll(m); uint64_t ok=D[j]&~forb_s(i,j,r,k); if(ok){ newDi|=1ULL<<r; supJ|=ok; } }
      if(newDi!=Di){ D[i]=newDi; changed=1; if(!newDi){ acut[k]++; mind[k][md<40?md:40]++; return 0; } }
      if((D[j]&supJ)!=D[j]){ D[j]&=supJ; changed=1; if(!D[j]){ acut[k]++; mind[k][md<40?md:40]++; return 0; } }
    }
  }
  return 1;
}
static void dfs(int c){
  if(c==N){ sols++; return; }
  uint64_t forb=rows; for(int i=0;i<c;i++) forb|=used[c-i]>>(N-1-p[i]);
  uint64_t cand=~forb&MASK; if(c==0) cand&=(1ULL<<((N-1)/2+1))-1;
  while(cand){ int r=__builtin_ctzll(cand); cand&=cand-1;
    for(int i=0;i<c;i++) used[c-i]|=1ULL<<(r-p[i]+N-1); p[c]=r; rows|=1ULL<<r;
    vis[c+1]++; if(lookahead(c+1)){ nodes++; dfs(c+1); }
    rows&=~(1ULL<<r); for(int i=0;i<c;i++) used[c-i]&=~(1ULL<<(r-p[i]+N-1)); }
}
int main(int argc,char**argv){ MODE=atoi(argv[1]); N=atoi(argv[2]); MASK=(1ULL<<N)-1;
  struct timespec a,b; clock_gettime(CLOCK_MONOTONIC,&a); dfs(0); clock_gettime(CLOCK_MONOTONIC,&b);
  printf("mode=%d n=%d nodes=%lld solutions=%lld seconds=%.2f\n",MODE,N,nodes,sols,(b.tv_sec-a.tv_sec)+1e-9*(b.tv_nsec-a.tv_nsec));
  if(MODE==2){ long long T=0; for(int k=0;k<=N;k++) T+=acut[k];
    printf("AC cuts (forward checking passed) by depth k: k  k/n  share-of-AC-cuts  AC-cut-rate-among-visited  median-min-domain\n");
    for(int k=1;k<=N;k++) if(acut[k]){ long long h=0,med=0; for(int d=0;d<=40;d++){ h+=mind[k][d]; if(2*h>=acut[k]){ med=d; break; } }
      printf("  %2d  %.2f  %5.1f%%  %5.1f%%  %lld\n",k,(double)k/N,100.0*acut[k]/T,100.0*acut[k]/vis[k],med); } }
  return 0; }
