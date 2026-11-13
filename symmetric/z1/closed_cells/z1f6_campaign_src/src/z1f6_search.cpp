#include <array>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
static constexpr int N=32, CUT=16;
struct TrailEntry{uint8_t lag,bit;};
static int F[6],rid,om1,om2,h[N],Zp,target_sum,active_count;
static uint32_t used;
static uint64_t lagset[32];
static uint8_t active_points[32];
static TrailEntry trail[496]; static int trail_size;
static int orderD[15],nord;
static long long nodes,structural_covers,costas_covers,collision_prunes,z_prunes,sum_prunes,domain_prunes;
static bool FULL=true,EMIT=true;
static inline bool ll(int i,int hi,int j,int hj){return abs(i-j)>=CUT&&abs(hi-hj)>=CUT;}
static inline unsigned bit_of(int d){return unsigned(d+31);}
static inline void rollback(int mark){while(trail_size>mark){auto e=trail[--trail_size];lagset[e.lag]&=~(1ULL<<e.bit);}}
static inline bool add_pending(uint64_t pending[32],int x,int hx,int y,int hy){
 int lo=x<y?x:y,hi=x<y?y:x; int d=(lo==x?hy-hx:hx-hy),s=hi-lo; unsigned b=bit_of(d);
 if(s<=0||s>=32||d==0||b>=63)return false; uint64_t m=1ULL<<b;
 if((lagset[s]&m)||(pending[s]&m))return false; pending[s]|=m; return true;
}
static bool place_pair(int a,int b){
 uint64_t pending[32]={0}; int zadd=0;
 if(ll(a,b,b,a))zadd++;
 if(FULL&&!add_pending(pending,a,b,b,a)){collision_prunes++;return false;}
 int nc[2]={a,b},nh[2]={b,a};
 for(int t=0;t<2;t++)for(int ai=0;ai<active_count;ai++){
  int j=active_points[ai]; if(ll(nc[t],nh[t],j,h[j]))zadd++;
  if(FULL&&!add_pending(pending,nc[t],nh[t],j,h[j])){collision_prunes++;return false;}
 }
 if(Zp+zadd>1){z_prunes++;return false;}
 h[a]=b;h[b]=a;used|=(1U<<a)|(1U<<b);Zp+=zadd;active_points[active_count++]=a;active_points[active_count++]=b;
 if(FULL)for(int s=1;s<N;s++){uint64_t x=pending[s];while(x){unsigned b=__builtin_ctzll(x);x&=x-1;lagset[s]|=1ULL<<b;trail[trail_size++]={(uint8_t)s,(uint8_t)b};}}
 return true;
}
static void rec(int k,int sum){
 nodes++;
 if(k==nord){
  if(sum!=target_sum)return; structural_covers++;
  if(FULL)costas_covers++;
  if(EMIT){printf("SURVIVOR root=F%03d-r%02d-s%02d fixed=",rid,om1,om2);for(int i=0;i<6;i++)printf("%d%c",F[i],i==5?' ':' ');printf("h=");for(int i=0;i<N;i++)printf("%d%c",h[i],i==N-1?' ':' ');printf("status=REQUIRES_INDEPENDENT_COSTAS_CHECK\n");fflush(stdout);} return;
 }
 int rem=nord-k,d=orderD[k];
 int lo=sum,hi=sum;
 for(int j=k;j<nord;j++){
  int dd=orderD[j],mn=1000,mx=-1;
  for(int a=0;a+dd<N;a++){int b=a+dd;if((used>>a&1U)||(used>>b&1U))continue;mn=min(mn,a+b);mx=max(mx,a+b);}
  if(mx<0){domain_prunes++;return;}lo+=mn;hi+=mx;
 }
 if(target_sum<lo||target_sum>hi){sum_prunes++;return;}
 for(int a=0;a+d<N;a++){
  int b=a+d;if((used>>a&1U)||(used>>b&1U))continue;
  uint32_t u0=used;int z0=Zp,ha=h[a],hb=h[b],mark=trail_size,ac0=active_count;
  if(place_pair(a,b))rec(k+1,sum+a+b);
  rollback(mark);active_count=ac0;used=u0;Zp=z0;h[a]=ha;h[b]=hb;
 }
}
static bool seed(){
 memset(h,0,sizeof h);memset(lagset,0,sizeof lagset);used=0;active_count=0;trail_size=0;Zp=0;
 for(int i=0;i<6;i++){h[F[i]]=F[i];used|=1U<<F[i];active_points[active_count++]=F[i];}
 for(int i=0;i<6;i++)for(int j=i+1;j<6;j++){
  if(ll(F[i],F[i],F[j],F[j]))Zp++; if(FULL){uint64_t p[32]={0};if(!add_pending(p,F[i],F[i],F[j],F[j]))return false;for(int s=1;s<N;s++)lagset[s]|=p[s];}
 }
 return Zp==1;
}
int main(int argc,char**argv){
 if(argc<6){fprintf(stderr,"usage: %s ruler_id r s mode rulers.csv\n",argv[0]);return 2;}
 rid=atoi(argv[1]);om1=atoi(argv[2]);om2=atoi(argv[3]);FULL=strcmp(argv[4],"structural")!=0;
 if(om1>=om2||((om1^om2)&1)==0)return 3;
 ifstream in(argv[5]);string line;getline(in,line);bool found=false;
 while(getline(in,line)){stringstream ss(line);string id,marks;getline(ss,id,',');getline(ss,marks,',');if(atoi(id.c_str())!=rid)continue;stringstream mm(marks);for(int i=0;i<6;i++)mm>>F[i];found=true;break;}
 if(!found)return 4; target_sum=496;for(int x:F)target_sum-=x;if(!seed())return 5;
 nord=0;for(int d=15;d>=1;d--)if(d!=om1&&d!=om2)orderD[nord++]=d;
 nodes=structural_covers=costas_covers=collision_prunes=z_prunes=sum_prunes=domain_prunes=0;rec(0,0);
 const char* pred=FULL?"EXACT_Z1F_F6_AND_FULL_COSTAS":"EXACT_Z1F_F6_STRUCTURAL";
 const char* status=(FULL?(costas_covers?"EXHAUSTED_WITH_COSTAS_Z1F_F6_COVERS":"EXHAUSTED_NO_COSTAS_Z1F_F6_COVER"):(structural_covers?"EXHAUSTED_WITH_STRUCTURAL_Z1F_F6_COVERS":"EXHAUSTED_NO_STRUCTURAL_Z1F_F6_COVER"));
 printf("F%03d-r%02d-s%02d,%s,%d,%lld,%lld,%lld,%lld,%lld,%lld,%s\n",rid,om1,om2,pred,target_sum,nodes,structural_covers,costas_covers,collision_prunes,z_prunes,sum_prunes,status);return 0;
}
