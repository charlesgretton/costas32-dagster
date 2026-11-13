/* Unrestricted Costas search tree: exact counting, Knuth probing, stratified probing, node rate.
   Columns are filled left to right; a node is a Costas-valid partial assignment of length 1..n.
   Symmetry: the first column's row is restricted to p0 <= (n-1)/2 (vertical complement), as in Paper 1.
   usage: costas_tree exact N | knuth N PROBES SEED | strat N DEPTH PROBES_PER_NODE SEED | rate N SECONDS
         | prefixes N DEPTH PROBES_PER_NODE SEED | deepval N DEPTH K CAP_SECONDS SEED PROBES */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define MAXN 40
static int N, p[MAXN];
static uint64_t used[MAXN];      /* used[m]: bit (diff+N-1) set if vertical difference diff seen at lag m */
static uint64_t rows;
static double now(void){ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+1e-9*t.tv_nsec; }
static int ok(int c,int r){                                  /* can row r go in column c? */
  if(rows>>r&1) return 0;
  for(int i=0;i<c;i++){ int m=c-i, d=r-p[i]+N-1; if(used[m]>>d&1) return 0; }
  return 1;
}
static void place(int c,int r){ p[c]=r; rows|=1ULL<<r; for(int i=0;i<c;i++) used[c-i]|=1ULL<<(r-p[i]+N-1); }
static void unplace(int c,int r){ rows&=~(1ULL<<r); for(int i=0;i<c;i++) used[c-i]&=~(1ULL<<(r-p[i]+N-1)); }
static int lim(int c){ return c==0 ? (N-1)/2 : N-1; }
static long long nodes, sols; static double tstop; static int timed;
static void dfs(int c){
  if(c==N){ sols++; return; }
  if(timed && (nodes&0xFFFFF)==0 && now()>tstop) return;
  for(int r=0;r<=lim(c);r++) if(ok(c,r)){ place(c,r); nodes++; dfs(c+1); unplace(c,r); if(timed && now()>tstop) return; }
}
static uint64_t rs; static uint64_t rnd(void){ rs^=rs<<13; rs^=rs>>7; rs^=rs<<17; return rs; }
/* one Knuth probe from the current state at column c: returns estimated node count of the subtree below */
static double probe(int c){
  double est=0, w=1; int placed[MAXN], k=0;
  while(c<N){
    int cand[MAXN], nc=0;
    for(int r=0;r<=lim(c);r++) if(ok(c,r)) cand[nc++]=r;
    if(!nc) break;
    w*=nc; est+=w;
    int r=cand[rnd()%nc]; place(c,r); placed[k++]=r; c++;
  }
  while(k>0){ c--; k--; unplace(c,placed[k]); }
  return est;
}
/* stratified: enumerate all nodes at depth D exactly (counting the nodes above them exactly), then probe each */
static long long frontier, above; static int D, Q; static double sum_est, sum_var;
static void strat(int c){
  if(c==D){ frontier++;
    double s=0,s2=0; for(int q=0;q<Q;q++){ double e=probe(c); s+=e; s2+=e*e; }
    double m=s/Q, v=(Q>1)?(s2/Q-m*m)/(Q-1):0; sum_est+=m; sum_var+=v; return; }
  for(int r=0;r<=lim(c);r++) if(ok(c,r)){ place(c,r); above++; strat(c+1); unplace(c,r); }
}

static void prefixes_out(int c){
  if(c==D){ double s=0,s2=0; for(int q=0;q<Q;q++){ double e=probe(c); s+=e; s2+=e*e; }
    double m=s/Q, se=(Q>1)?sqrt((s2/Q-m*m)/(Q-1)):0;
    for(int i=0;i<D;i++){ printf(i?"-%d":"%d",p[i]); }
    printf(" %.6e %.3e\n",m,se); return; }
  for(int r=0;r<=lim(c);r++) if(ok(c,r)){ place(c,r); prefixes_out(c+1); unplace(c,r); }
}
int main(int argc,char**argv){
  if(argc<3){ fprintf(stderr,"usage\n"); return 1; }
  N=atoi(argv[2]); memset(used,0,sizeof used); rows=0;
  if(!strcmp(argv[1],"exact")){ double t=now(); dfs(0);
    printf("exact n=%d nodes=%lld solutions=%lld seconds=%.2f rate=%.3e\n",N,nodes,sols,now()-t,nodes/(now()-t)); }
  else if(!strcmp(argv[1],"knuth")){ long long P=atoll(argv[3]); rs=strtoull(argv[4],0,10)*2654435761ULL+1;
    double s=0,s2=0,mx=0,t=now(); for(long long i=0;i<P;i++){ double e=probe(0); s+=e; s2+=e*e; if(e>mx) mx=e; }
    double m=s/P, se=sqrt((s2/P-m*m)/(P-1));   /* s.e. of the mean */
    printf("knuth n=%d probes=%lld estimate=%.4e stderr=%.3e maxshare=%.2e seconds=%.1f\n",N,P,m,se,mx/s,now()-t); }
  else if(!strcmp(argv[1],"strat")){ D=atoi(argv[3]); Q=atoi(argv[4]); rs=strtoull(argv[5],0,10)*2654435761ULL+1;
    double t=now(); strat(0); double est=above+sum_est, se=sqrt(sum_var);   /* sum of per-node variances of the mean */
    printf("strat n=%d depth=%d frontier=%lld per_node=%d estimate=%.4e stderr=%.3e seconds=%.1f\n",N,D,frontier,Q,est,se,now()-t); }

  else if(!strcmp(argv[1],"prefixes")){ /* every node at depth D, with a Q-probe estimate of its subtree: "rows estimate stderr" */
    D=atoi(argv[3]); Q=atoi(argv[4]); rs=strtoull(argv[5],0,10)*2654435761ULL+1; prefixes_out(0); }
  else if(!strcmp(argv[1],"deepval")){ /* K random depth-D nodes: probe estimate vs exact count of the subtree (time-capped) */
    D=atoi(argv[3]); int K=atoi(argv[4]); double cap=atof(argv[5]); rs=strtoull(argv[6],0,10)*2654435761ULL+1; Q=atoi(argv[7]);
    for(int k=0;k<K;k++){
      int c=0, path[MAXN];
      while(c<D){ int cand[MAXN],nc=0; for(int r=0;r<=lim(c);r++) if(ok(c,r)) cand[nc++]=r;
        if(!nc){ while(c>0){ c--; unplace(c,path[c]); } continue; }
        int r=cand[rnd()%nc]; place(c,r); path[c]=r; c++; }
      double s=0,s2=0; for(int q=0;q<Q;q++){ double e=probe(D); s+=e; s2+=e*e; }
      double m=s/Q, se=sqrt((s2/Q-m*m)/(Q-1));
      nodes=0; timed=1; double t=now(); tstop=t+cap; dfs(D); double el=now()-t; int done=el<cap; timed=0;
      printf("deepval n=%d depth=%d probe_estimate=%.6e stderr=%.3e exact=%lld complete=%d seconds=%.2f\n",N,D,m,se,nodes,done,el);
      fflush(stdout);
      for(int i=D-1;i>=0;i--) unplace(i,path[i]);
    } }
  else if(!strcmp(argv[1],"rate")){ timed=1; double t=now(); tstop=t+atof(argv[3]); dfs(0);
    printf("rate n=%d nodes=%lld seconds=%.1f rate=%.3e nodes/s\n",N,nodes,now()-t,nodes/(now()-t)); }
  return 0;
}
