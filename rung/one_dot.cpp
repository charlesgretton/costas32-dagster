#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <set>
#include <vector>
using namespace std;
static uint8_t gmul(uint8_t a,uint8_t b){uint8_t r=0;for(int s=0;s<5;s++){if(b&1)r^=a;b>>=1;bool c=a&0x10;a=(uint8_t)((a<<1)&0x1f);if(c)a^=0x05;}return r&0x1f;}
template<int M> static bool costasM(const array<int,M>&k){for(int d=1;d<M;d++){uint64_t m=0;for(int i=0;i+d<M;i++){unsigned e=(unsigned)(k[i+d]-k[i]+M-1);if((m>>e)&1ull)return false;m|=1ull<<e;}}return true;}
int main(){
  vector<array<int,30>> c30;
  for(int g=2;g<31;g++){set<int>s;int x=1;for(int i=0;i<30;i++){x=x*g%31;s.insert(x);}if((int)s.size()!=30)continue;
    for(int c=0;c<30;c++){array<int,30>k;int v=1;for(int i=0;i<c;i++)v=v*g%31;for(int i=0;i<30;i++){v=v*g%31;k[i]=v-1;}c30.push_back(k);}}
  {uint8_t ex[31];int lg[32];memset(lg,-1,sizeof lg);uint8_t x=1;for(int i=0;i<31;i++){ex[i]=x;lg[x]=i;x=gmul(x,2);}
   for(uint8_t a=2;a<32;a++)for(uint8_t b=2;b<32;b++){array<int,30>k;bool ok=true;int inv=1,lb=lg[b];
     for(int e=0;e<29;e++)inv=inv*lb%31;
     for(int i=1;i<=30&&ok;i++){uint8_t ai=ex[(lg[a]*i)%31],t=ai^1;if(!t){ok=false;break;}int j=(int)((long long)lg[t]*inv%31);if(j<1||j>30){ok=false;break;}k[i-1]=j-1;}
     if(!ok)continue;set<int>s(k.begin(),k.end());if(s.size()!=30)continue;if(!costasM<30>(k))continue;c30.push_back(k);}}
  set<array<int,30>> S;
  for(auto&k:c30){array<int,30>b=k;for(int t=0;t<2;t++){if(t){array<int,30>iv;for(int i=0;i<30;i++)iv[b[i]]=i;b=iv;}
    for(int f=0;f<4;f++){array<int,30>c;for(int i=0;i<30;i++){int j=(f&1)?29-i:i;c[i]=(f&2)?29-b[j]:b[j];}S.insert(c);}}}
  vector<array<int,30>> cores(S.begin(),S.end());
  printf("distinct order-30 cores: %zu\n",cores.size());
  int N=31,best=1<<30,cnt0=0;long long tested=0;long long hist[8]={0};array<int,31> bh{};
  int cols[30],rows[30],h[31];
  for(auto&k:cores) for(int C=0;C<N;C++){int t=0;for(int x=0;x<N;x++)if(x!=C)cols[t++]=x;
    for(int R=0;R<N;R++){t=0;for(int x=0;x<N;x++)if(x!=R)rows[t++]=x;
      for(int i=0;i<30;i++)h[cols[i]]=rows[k[i]]; h[C]=R; tested++;
      int s=0;uint64_t u[32];memset(u,0,sizeof u);
      for(int d=1;d<N&&s<=7;d++)for(int i=0;i+d<N;i++){unsigned e=(unsigned)(h[i+d]-h[i]+N-1);s+=(int)((u[d]>>e)&1ull);u[d]|=1ull<<e;}
      if(s<=7)hist[s]++; if(s==0)cnt0++;
      if(s<best){best=s;memcpy(bh.data(),h,sizeof h);} }}
  printf("ONE-DOT augmentation to order 31: tested=%lld  COSTAS FOUND=%d  min score=%d\n",tested,cnt0,best);
  printf("score histogram (0..7):");for(int i=0;i<8;i++)printf(" %d:%lld",i,hist[i]);printf("\n");
  printf("example order-31 Costas array:");for(int x:bh)printf(" %d",x);printf("\n");
}
