// Z=1 Stage A census.  Branch T: one long transposition.  Branch F: one long fixed pair.
// Enforces exact cover + incremental global large-large mass <= 1, final == 1.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
using namespace std;
static int h[32]; static bool as[32];
static int Zp;                       // partial large-large count
static long long ncover=0,nz1=0,nodes=0;
static vector<int> lens; static int F[8],nf;
static bool addPair(int x,int y,int hx,int hy,int&back){ // returns false if Z would exceed 1
  back=0;
  int nc[2]={x,y}, nh[2]={hx,hy}; int cnt=(x==y)?1:2;
  for(int t=0;t<cnt;t++){ int i=nc[t];
    for(int j=0;j<32;j++){ if(!as[j]) continue;
      if(t==1&&j==nc[0]) continue;   // counted already
      int d=i>j?i-j:j-i; if(d==0) continue;
      int e=nh[t]>h[j]?nh[t]-h[j]:h[j]-nh[t];
      if(d>=16&&e>=16){ Zp++; back++; if(Zp>1){ Zp-=back; return false; } } } 
    as[i]=true; h[i]=nh[t]; }
  if(cnt==2){ int d=y-x,e=hy>hx?hy-hx:hx-hy; }
  return true;
}
static void rmPair(int x,int y,int back,int cnt){ as[x]=false; if(cnt==2) as[y]=false; Zp-=back; }
static void rec(size_t idx){
  nodes++;
  if(idx==lens.size()){ ncover++; if(Zp==1) nz1++; return; }
  int d=lens[idx];
  for(int a=0;a+d<32;a++){ int b=a+d;
    if(as[a]||as[b]) continue;
    int back; 
    if(!addPair(a,b,b,a,back)) { continue; }
    rec(idx+1);
    rmPair(a,b,back,2); }
}
int main(int argc,char**argv){
  int branch=atoi(argv[1]);      // 0=T 1=F
  long long P=0,Pd=0;
  for(int L=16;L<=31;L++){
    if(branch==0){ // long transposition (u,u+L), f=0 only for this pass
      for(int u=0;u+L<32;u++){
        P++;
        memset(as,0,sizeof as); Zp=0;
        lens.clear(); for(int d=1;d<=15;d++) lens.push_back(d);
        // place long transposition first
        as[u]=true; h[u]=u+L; as[u+L]=true; h[u+L]=u; Zp=1;
        // order lengths descending (most constrained first)
        for(size_t i=0;i<lens.size();i++) for(size_t j=i+1;j<lens.size();j++)
          if(lens[j]>lens[i]){int t=lens[i];lens[i]=lens[j];lens[j]=t;}
        Pd++; rec(0);
        printf("  T L=%d u=%d cum_covers=%lld cum_z1=%lld\n",L,u,ncover,nz1); fflush(stdout);
      }
    } else {       // long fixed pair p, p+L ; f=2 exactly, 15 short transpositions
      for(int p=0;p+L<32;p++){
        P++;
        memset(as,0,sizeof as); Zp=0;
        lens.clear(); for(int d=1;d<=15;d++) lens.push_back(d);
        as[p]=true; h[p]=p; as[p+L]=true; h[p+L]=p+L; Zp=1;
        for(size_t i=0;i<lens.size();i++) for(size_t j=i+1;j<lens.size();j++)
          if(lens[j]>lens[i]){int t=lens[i];lens[i]=lens[j];lens[j]=t;}
        Pd++; rec(0);
        printf("  F L=%d p=%d cum_covers=%lld cum_z1=%lld\n",L,p,ncover,nz1); fflush(stdout);
      }
    }
  }
  printf("branch=%s  parameters=%lld  nodes=%lld  covers=%lld  Z==1 covers=%lld\n",
         branch?"F (f=2)":"T (f=0)",P,nodes,ncover,nz1);
  return 0; }
