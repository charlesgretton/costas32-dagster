/* Bit-parallel left-to-right Costas search with full dihedral (D4) symmetry pruning.
   Canonical form: an array is kept iff it is lexicographically <= all 8 of its images (lex-leader), so exactly one
   array per symmetry class survives. A prefix is cut when some image is GUARANTEED lexicographically smaller for
   every completion. The comparison runs over known positions j < c of p; an image entry is either known or confined
   to an interval (an unplaced row's column lies in [c, N-1]).
   Images (p = permutation, q = inverse):   V: N-1-p[j]     H: p[N-1-j]       R: N-1-p[N-1-j]
                                            T: q[j]         VT: N-1-q[j]      HT: q[N-1-j]      RT: N-1-q[N-1-j]
   usage: sym exact N | sym rate N SECONDS | sym knuth N PROBES SEED | sym list N   (list: canonical arrays) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
static int N, p[40], q[40]; static uint64_t used[40], rows, MASK; static long long nodes, sols; static double tstop; static int timed, listing;
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+1e-9*t.tv_nsec; }
/* value of image g at position j given c columns placed: returns 1 and sets *v if known, else 0 and sets [*lo,*hi] */
static int img(int g,int j,int c,int*v,int*lo,int*hi){
  int k;
  switch(g){
    case 0: if(j<c){*v=N-1-p[j];return 1;} break;
    case 1: k=N-1-j; if(k<c){*v=p[k];return 1;} break;
    case 2: k=N-1-j; if(k<c){*v=N-1-p[k];return 1;} break;
    case 3: if(q[j]>=0){*v=q[j];return 1;} *lo=c;*hi=N-1; return 0;
    case 4: if(q[j]>=0){*v=N-1-q[j];return 1;} *lo=0;*hi=N-1-c; return 0;
    case 5: k=N-1-j; if(q[k]>=0){*v=q[k];return 1;} *lo=c;*hi=N-1; return 0;
    case 6: k=N-1-j; if(q[k]>=0){*v=N-1-q[k];return 1;} *lo=0;*hi=N-1-c; return 0;
  }
  *lo=0;*hi=N-1; return 0;
}
/* 1 if some image is certainly lexicographically smaller than p for every completion of the c-column prefix */
static int dominated(int c){
  for(int g=0;g<7;g++){
    for(int j=0;j<c;j++){
      int v,lo,hi;
      if(img(g,j,c,&v,&lo,&hi)){ if(v<p[j]) return 1; if(v>p[j]) break; continue; }
      if(hi<p[j]) return 1;
      break;                                   /* undetermined (or certainly larger): this image is no threat yet */
    }
  }
  return 0;
}
static void dfs(int c){
  if(c==N){ sols++; if(listing){ for(int i=0;i<N;i++) printf(i?",%d":"%d",p[i]); printf("\n"); } return; }
  if(timed && (nodes&0xFFFFF)==0 && now()>tstop) return;
  uint64_t forb=rows; for(int i=0;i<c;i++) forb |= used[c-i] >> (N-1-p[i]);
  uint64_t cand=~forb & MASK;
  while(cand){
    int r=__builtin_ctzll(cand); cand&=cand-1;
    for(int i=0;i<c;i++) used[c-i] |= 1ULL<<(r-p[i]+N-1);
    p[c]=r; q[r]=c; rows|=1ULL<<r;
    if(!dominated(c+1)){ nodes++; dfs(c+1); }
    rows&=~(1ULL<<r); q[r]=-1; for(int i=0;i<c;i++) used[c-i]&=~(1ULL<<(r-p[i]+N-1));
    if(timed && now()>tstop) return;
  }
}
static uint64_t rs; static uint64_t rnd(void){ rs^=rs<<13; rs^=rs>>7; rs^=rs<<17; return rs; }
static double probe(void){                      /* Knuth probe of the symmetry-pruned tree, from the root */
  double est=0,w=1; int c=0;
  while(c<N){
    int cand[40],nc=0;
    uint64_t forb=rows; for(int i=0;i<c;i++) forb |= used[c-i] >> (N-1-p[i]);
    uint64_t m=~forb & MASK;
    while(m){ int r=__builtin_ctzll(m); m&=m-1;
      for(int i=0;i<c;i++) used[c-i] |= 1ULL<<(r-p[i]+N-1); p[c]=r; q[r]=c; rows|=1ULL<<r;
      if(!dominated(c+1)) cand[nc++]=r;
      rows&=~(1ULL<<r); q[r]=-1; for(int i=0;i<c;i++) used[c-i]&=~(1ULL<<(r-p[i]+N-1)); }
    if(!nc) break;
    w*=nc; est+=w;
    int r=cand[rnd()%nc]; for(int i=0;i<c;i++) used[c-i] |= 1ULL<<(r-p[i]+N-1); p[c]=r; q[r]=c; rows|=1ULL<<r; c++;
  }
  while(c>0){ c--; int r=p[c]; rows&=~(1ULL<<r); q[r]=-1; for(int i=0;i<c;i++) used[c-i]&=~(1ULL<<(r-p[i]+N-1)); }
  return est;
}
int main(int argc,char**argv){
  N=atoi(argv[2]); MASK=(1ULL<<N)-1; for(int i=0;i<40;i++) q[i]=-1;
  double t=now();
  if(!strcmp(argv[1],"knuth")){ long long P=atoll(argv[3]); rs=strtoull(argv[4],0,10)*2654435761ULL+1;
    double s=0,s2=0; for(long long k=0;k<P;k++){ double e=probe(); s+=e; s2+=e*e; }
    double m=s/P, se=sqrt((s2/P-m*m)/(P-1));
    printf("knuth n=%d probes=%lld estimate=%.4e stderr=%.3e seconds=%.1f\n",N,P,m,se,now()-t); return 0; }
  if(!strcmp(argv[1],"rate")){ timed=1; tstop=t+atof(argv[3]); }
  if(!strcmp(argv[1],"list")) listing=1;
  dfs(0);
  if(!listing) printf("%s n=%d nodes=%lld classes=%lld seconds=%.2f rate=%.3e\n",argv[1],N,nodes,sols,now()-t,nodes/(now()-t));
  return 0;
}
