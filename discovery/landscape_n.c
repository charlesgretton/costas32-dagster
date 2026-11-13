/* Phase A landscape around a seed permutation: delta_m (excess repeated displacements) for every state
   reachable by: one swap, two swaps, three-cycles, block reversals, block relocations, and every
   rearrangement of the collision kernel K0 (endpoints of all colliding pairs), and of K0 plus one dot. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifndef N
#define N 32
#endif
static int seen[N][2*N];
static int dm(const int*p){                 /* excess repeats: sum over classes of (multiplicity-1)+ */
  memset(seen,0,sizeof seen); int e=0;
  for(int i=0;i<N;i++) for(int j=i+1;j<N;j++){ int*s=&seen[j-i][p[j]-p[i]+N]; if(*s) e++; (*s)++; }
  return e; }
static long long hist[8][64]; static int best[8]; static const char*name[8]={"one swap","two swaps","three-cycles","block reversals","block relocations","kernel K0 rearrangements","K0 plus one dot","(unused)"};
static void rec(int cls,const int*q){ int d=dm(q); if(d>63)d=63; hist[cls][d]++; if(d<best[cls]) best[cls]=d; }
static int perm[16], used16[16], ks, kv[16], kpos[16], q[N]; static const int*P0; static int CLS;
static void gen(int t){ if(t==ks){ memcpy(q,P0,sizeof q); for(int a=0;a<ks;a++) q[kpos[a]]=kv[perm[a]]; rec(CLS,q); return; }
  for(int c=0;c<ks;c++) if(!used16[c]){ used16[c]=1; perm[t]=c; gen(t+1); used16[c]=0; } }
int main(void){
  int p[N]; for(int i=0;i<N;i++) if(scanf("%d",&p[i])!=1) return 2;
  for(int c=0;c<8;c++) best[c]=99;
  printf("seed: order %d, delta_m = %d\n",N,dm(p));
  int K[N]={0}; /* collision kernel */
  { int cnt[N][2*N]; memset(cnt,0,sizeof cnt);
    for(int i=0;i<N;i++) for(int j=i+1;j<N;j++) cnt[j-i][p[j]-p[i]+N]++;
    for(int i=0;i<N;i++) for(int j=i+1;j<N;j++) if(cnt[j-i][p[j]-p[i]+N]>1){ K[i]=K[j]=1; printf("   collision pair (%d,%d): displacement (%d,%d)\n",i,j,j-i,p[j]-p[i]); } }
  int a,b,c,d;
  for(a=0;a<N;a++) for(b=a+1;b<N;b++){ memcpy(q,p,sizeof q); int t=q[a];q[a]=q[b];q[b]=t; rec(0,q); }
  int sw[496][2],ns=0; for(a=0;a<N;a++) for(b=a+1;b<N;b++){ sw[ns][0]=a; sw[ns][1]=b; ns++; }
  for(int s1=0;s1<ns;s1++) for(int s2=s1+1;s2<ns;s2++){ memcpy(q,p,sizeof q);
    int t=q[sw[s1][0]];q[sw[s1][0]]=q[sw[s1][1]];q[sw[s1][1]]=t; t=q[sw[s2][0]];q[sw[s2][0]]=q[sw[s2][1]];q[sw[s2][1]]=t; rec(1,q); }
  for(a=0;a<N;a++) for(b=0;b<N;b++) for(c=0;c<N;c++) if(a!=b&&b!=c&&a!=c&&a<b&&a<c){ memcpy(q,p,sizeof q); q[a]=p[b]; q[b]=p[c]; q[c]=p[a]; rec(2,q); }
  for(a=0;a<N;a++) for(b=a+1;b<N;b++){ memcpy(q,p,sizeof q); for(int i=0;i<=b-a;i++) q[a+i]=p[b-i]; rec(3,q); }
  for(a=0;a<N;a++) for(b=a;b<N;b++){ int L=b-a+1, rest[N], nr=0; for(int i=0;i<N;i++) if(i<a||i>b) rest[nr++]=p[i];
    for(c=0;c<=nr;c++){ if(c==a) continue; int k=0; for(int i=0;i<c;i++) q[k++]=rest[i]; for(int i=a;i<=b;i++) q[k++]=p[i]; for(int i=c;i<nr;i++) q[k++]=rest[i]; rec(4,q); } }
  ks=0; for(int i=0;i<N;i++) if(K[i]){ kpos[ks]=i; kv[ks]=p[i]; ks++; }
  P0=p; CLS=5; gen(0);
  int base=ks; for(int x=0;x<N;x++) if(!K[x]){ ks=base; kpos[ks]=x; kv[ks]=p[x]; ks++; CLS=6; gen(0); }
  printf("kernel K0 has %d dots\n",base);
  for(int cl=0;cl<7;cl++){ long long tot=0; for(int d2=0;d2<64;d2++) tot+=hist[cl][d2];
    printf("%-26s %10lld states   min delta_m %d   states with delta_m 0/1/2: %lld / %lld / %lld\n",name[cl],tot,best[cl],hist[cl][0],hist[cl][1],hist[cl][2]); }
  return 0; }
