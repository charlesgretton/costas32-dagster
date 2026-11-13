/* A/B/C wall-time test engine: one search engine, three policies.
   A: left-to-right, forward checking (every unplaced column must keep a legal row).
   B: A + binary displacement arc consistency, triggered when min domain <= 3 or placed >= ceil(N/2);
      children range over the arc-consistent domain of the next column.
   C: B with dynamic column choice (fewest legal rows after AC; ties to the smallest index).
   Columns may be placed in any order: displacements are stored in both orientations (used/rev), and a
   column's domain includes the midpoint condition (two placed columns at equal distance on either side).
   Arc consistency recomputes all supports at each triggered node: no cache, so no stale supports.
   Symmetry: the first placed column takes a row <= (N-1)/2 (vertical flip), identical for all policies.
   usage: abc CFG N full            (CFG = A|B|C; whole search)
          abc CFG N split DEPTH     (left-to-right prefixes of columns 0..DEPTH-1, shared by all policies)
          abc CFG N run < tasks     (one RESULT line per task; ARRAY lines for solutions)  */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
static int N, CFG, TRIG_DEPTH, TRIG_MINC=3, p[40], placed[40], np;
static uint64_t used[40], rev[40], rows, MASK;
static long long nodes, sols, fc_dead, ac_calls, ac_del, ac_dead; static double ac_sec;
static int print_arrays; static char tid[64];
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+1e-9*t.tv_nsec; }
static inline uint64_t dom(int x){
  uint64_t f=rows;
  for(int t=0;t<np;t++){ int c=placed[t];
    if(c<x) f|=used[x-c]>>(N-1-p[c]); else f|=rev[c-x]>>(N-1-p[c]); }
  for(int L=1;x-L>=0&&x+L<N;L++) if(p[x-L]>=0&&p[x+L]>=0){ int s2=p[x-L]+p[x+L]; if(!(s2&1)) f|=1ULL<<(s2/2); }
  return ~f&MASK;
}
static inline void place(int x,int s){
  for(int t=0;t<np;t++){ int c=placed[t],L,d; if(c<x){L=x-c;d=s-p[c];}else{L=c-x;d=p[c]-s;}
    used[L]|=1ULL<<(d+N-1); rev[L]|=1ULL<<(-d+N-1); }
  p[x]=s; rows|=1ULL<<s; placed[np++]=x;
}
static inline void unplace(int x){
  np--; int s=p[x]; rows&=~(1ULL<<s); p[x]=-1;
  for(int t=0;t<np;t++){ int c=placed[t],L,d; if(c<x){L=x-c;d=s-p[c];}else{L=c-x;d=p[c]-s;}
    used[L]&=~(1ULL<<(d+N-1)); rev[L]&=~(1ULL<<(-d+N-1)); }
}
/* can unplaced columns i<j take rows r,s together? (each alone is already legal: r in D_i, s in D_j) */
static inline int pair_ok(int i,int r,int j,int s){
  int L0=j-i, d0=s-r;
  if(used[L0]>>(d0+N-1)&1) return 0;                                   /* their mutual displacement */
  if(i-L0>=0 && p[i-L0]>=0 && r-p[i-L0]==d0) return 0;                 /* equals i's new pair at lag L0 */
  if(j+L0<N && p[j+L0]>=0 && p[j+L0]-s==d0) return 0;                  /* equals j's new pair at lag L0 */
  for(int t=0;t<np;t++){ int c=placed[t],L,di;                          /* i's and j's new pairs, same lag */
    if(c<i){L=i-c;di=r-p[c];}else{L=c-i;di=p[c]-r;}
    if(j-L>=0 && p[j-L]>=0 && s-p[j-L]==di) return 0;
    if(j+L<N  && p[j+L]>=0 && p[j+L]-s==di) return 0; }
  return 1;
}
static int ac(uint64_t *D,int *U,int m){
  ac_calls++; double t0=now(); int changed=1, alive=1;
  while(changed&&alive){ changed=0;
    for(int a=0;a<m&&alive;a++) for(int b=a+1;b<m&&alive;b++){
      int i=U[a], j=U[b];                                              /* U is in increasing column order */
      uint64_t Di=D[i], Dj=D[j], newDi=0, supJ=0;
      for(uint64_t m1=Di;m1;m1&=m1-1){ int r=__builtin_ctzll(m1); uint64_t ok=0;
        for(uint64_t m2=Dj&~(1ULL<<r);m2;m2&=m2-1){ int s=__builtin_ctzll(m2); if(pair_ok(i,r,j,s)) ok|=1ULL<<s; }
        if(ok){ newDi|=1ULL<<r; supJ|=ok; } }
      if(newDi!=Di){ ac_del+=__builtin_popcountll(Di^newDi); D[i]=newDi; changed=1; if(!newDi) alive=0; }
      if(alive && (Dj&supJ)!=Dj){ ac_del+=__builtin_popcountll(Dj&~supJ); D[j]=Dj&supJ; changed=1; if(!D[j]) alive=0; }
    } }
  ac_sec+=now()-t0; return alive;
}
static void dfs(void){
  if(np==N){ sols++; if(print_arrays){ printf("ARRAY %s ",tid); for(int i=0;i<N;i++) printf(i?",%d":"%d",p[i]); printf("\n"); } return; }
  uint64_t D[40]; int U[40], m=0, minc=99, best=-1;
  for(int x=0;x<N;x++) if(p[x]<0){ D[x]=dom(x); int c=__builtin_popcountll(D[x]); if(!c){ fc_dead++; return; }
    U[m++]=x; if(c<minc){minc=c;best=x;} }
  if(CFG>=1 && (minc<=TRIG_MINC || np>=TRIG_DEPTH)){
    if(!ac(D,U,m)){ ac_dead++; return; }
    if(CFG==2){ minc=99; for(int a=0;a<m;a++){ int c=__builtin_popcountll(D[U[a]]); if(c<minc){minc=c;best=U[a];} } } }
  int x=(CFG==2)?best:U[0];
  uint64_t cand=D[x]; if(np==0) cand&=(1ULL<<((N-1)/2+1))-1;
  for(;cand;cand&=cand-1){ int s=__builtin_ctzll(cand); place(x,s); nodes++; dfs(); unplace(x); }
}
static void reset(void){ memset(used,0,sizeof used); memset(rev,0,sizeof rev); rows=0; np=0; for(int i=0;i<40;i++) p[i]=-1; }
static int K; static int pref[40]; static long long ntasks;
static void split(int c){
  if(c==K){ printf("T%07lld",ntasks++); for(int i=0;i<K;i++) printf(" %d",pref[i]); printf("\n"); return; }
  uint64_t cand=dom(c); if(c==0) cand&=(1ULL<<((N-1)/2+1))-1;
  for(;cand;cand&=cand-1){ int s=__builtin_ctzll(cand); pref[c]=s; place(c,s); split(c+1); unplace(c); }
}
int main(int argc,char**argv){
  if(argc<4){ fprintf(stderr,"usage: abc A|B|C N full|split DEPTH|run\n"); return 2; }
  CFG=argv[1][0]-'A'; N=atoi(argv[2]); MASK=(1ULL<<N)-1; TRIG_DEPTH=(N+1)/2;
  if(getenv("ABC_TRIG_DEPTH")) TRIG_DEPTH=atoi(getenv("ABC_TRIG_DEPTH"));
  if(getenv("ABC_TRIG_MINC")) TRIG_MINC=atoi(getenv("ABC_TRIG_MINC"));
  if(CFG<0||CFG>2||N<4||N>30){ fprintf(stderr,"bad arguments\n"); return 2; }
  reset();
  if(!strcmp(argv[3],"full")){ print_arrays=getenv("ABC_PRINT")!=NULL; strcpy(tid,"FULL"); double t=now(); dfs();
    printf("FULL cfg=%c n=%d nodes=%lld solutions=%lld fc_dead=%lld ac_calls=%lld ac_deleted=%lld ac_dead=%lld ac_seconds=%.3f seconds=%.3f\n",
      'A'+CFG,N,nodes,sols,fc_dead,ac_calls,ac_del,ac_dead,ac_sec,now()-t); return 0; }
  if(!strcmp(argv[3],"split")){ K=atoi(argv[4]); split(0); printf("#SPLIT n=%d depth=%d tasks=%lld\n",N,K,ntasks); return 0; }
  if(!strcmp(argv[3],"run")){ print_arrays=1; char line[1024];
    while(fgets(line,sizeof line,stdin)){
      if(line[0]!='T') continue; char*save; char*tok=strtok_r(line," \n",&save); strncpy(tid,tok,63);
      reset(); int c=0, ok=1;
      while((tok=strtok_r(NULL," \n",&save))){ int s=atoi(tok); if(!(dom(c)>>s&1)){ ok=0; break; } place(c,s); c++; }
      if(!ok){ printf("RESULT %s ERROR replay\n",tid); fflush(stdout); continue; }
      nodes=sols=fc_dead=ac_calls=ac_del=ac_dead=0; ac_sec=0; double t=now(); dfs();
      printf("RESULT %s COMPLETE nodes=%lld arrays=%lld fc_dead=%lld ac_calls=%lld ac_deleted=%lld ac_dead=%lld ac_seconds=%.4f seconds=%.4f\n",
        tid,nodes,sols,fc_dead,ac_calls,ac_del,ac_dead,ac_sec,now()-t); fflush(stdout); }
    return 0; }
  return 2;
}
