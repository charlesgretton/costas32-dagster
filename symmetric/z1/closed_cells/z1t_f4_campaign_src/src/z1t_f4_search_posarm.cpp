#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
using namespace std;
static constexpr int N=32,CUT=16;
struct TrailEntry{uint8_t lag,bit;};
static int F[4],rid,h[N],active_count,trail_size,Zp,orderD[15],nord,target_short;
static uint32_t used; static uint64_t lagset[32]; static uint8_t active_points[32];static TrailEntry trail[496];
static bool FULL=true,EMIT=true,AUDIT=false,POSARM=false;
static long long terminal_calls=0,accepted_terminals=0;
static long long nodes;
static long long parity_admissible_records;
static long long seed_compatible_records;
static long long long_candidates;
static long long long_seed_ok;
static long long structural_covers;
static long long costas_covers;
static long long collision_prunes;
static long long z_prunes;
static long long sum_prunes;
static long long domain_prunes;
static inline bool ll(int x,int hx,int y,int hy){return abs(x-y)>=CUT&&abs(hx-hy)>=CUT;}
static inline unsigned bit_of(int d){return unsigned(d+31);}
static inline void rollback(int mark){while(trail_size>mark){auto e=trail[--trail_size];lagset[e.lag]&=~(1ULL<<e.bit);}}
static inline bool add_pending(uint64_t p[32],int x,int hx,int y,int hy){
 int lo=min(x,y),hi=max(x,y),s=hi-lo,d=(lo==x?hy-hx:hx-hy);unsigned bit=bit_of(d);
 if(s<=0||s>=N||d==0||bit>=63)return false;uint64_t m=1ULL<<bit;
 if((lagset[s]&m)||(p[s]&m))return false;p[s]|=m;return true;
}
static int recompute_Z(){int z=0;for(int i=0;i<active_count;i++)for(int j=i+1;j<active_count;j++){int x=active_points[i],y=active_points[j];z+=ll(x,h[x],y,h[y]);}return z;}
static int held_bits(){int n=0;for(int s=1;s<N;s++)n+=__builtin_popcountll(lagset[s]);return n;}
static void audit_state(int short_depth){
 if(!AUDIT)return;assert(__builtin_popcount(used)==6+2*short_depth);assert(active_count==6+2*short_depth);assert(recompute_Z()==Zp);if(FULL)assert(held_bits()==active_count*(active_count-1)/2);
}
static bool place_pair(int a,int b){
 uint64_t p[32]={0};int zadd=0;
 if(ll(a,b,b,a))zadd++;
 if(FULL&&!add_pending(p,a,b,b,a)){collision_prunes++;return false;}
 int nc[2]={a,b},nh[2]={b,a};
 for(int t=0;t<2;t++)for(int q=0;q<active_count;q++){int j=active_points[q];if(ll(nc[t],nh[t],j,h[j]))zadd++;if(FULL&&!add_pending(p,nc[t],nh[t],j,h[j])){collision_prunes++;return false;}}
 if(!POSARM && Zp+zadd>1){z_prunes++;return false;}
 h[a]=b;h[b]=a;used|=(1U<<a)|(1U<<b);Zp+=zadd;active_points[active_count++]=a;active_points[active_count++]=b;
 if(FULL)for(int s=1;s<N;s++){uint64_t x=p[s];while(x){unsigned bit=__builtin_ctzll(x);x&=x-1;lagset[s]|=1ULL<<bit;trail[trail_size++]={(uint8_t)s,(uint8_t)bit};}}
 return true;
}
static void rec_short(int k,int sum){
 nodes++;audit_state(k);
 if(k==nord){terminal_calls++; if(sum!=target_short||(!POSARM&&Zp!=1)||__builtin_popcount(used)!=32)return; accepted_terminals++;structural_covers++;if(FULL)costas_covers++;if(EMIT){printf("SURVIVOR root=F%04d h=",rid);for(int i=0;i<N;i++)printf("%d%c",h[i],i+1==N?'\n':' ');fflush(stdout);}return;}
 int lo=sum,hi=sum;
 for(int j=k;j<nord;j++){int d=orderD[j],mn=1000,mx=-1;for(int a=0;a+d<N;a++){int b=a+d;if((used>>a&1U)||(used>>b&1U))continue;mn=min(mn,a+b);mx=max(mx,a+b);}if(mx<0){domain_prunes++;return;}lo+=mn;hi+=mx;}
 if(target_short<lo||target_short>hi){sum_prunes++;return;}
 int d=orderD[k];
 for(int a=0;a+d<N;a++){int b=a+d;if((used>>a&1U)||(used>>b&1U))continue;uint32_t u0=used;int z0=Zp,ha=h[a],hb=h[b],mark=trail_size,ac0=active_count;if(place_pair(a,b))rec_short(k+1,sum+a+b);rollback(mark);active_count=ac0;used=u0;Zp=z0;h[a]=ha;h[b]=hb;}
}
static bool seed_fixed(){
 memset(h,0,sizeof h);memset(lagset,0,sizeof lagset);used=0;active_count=0;trail_size=0;Zp=0;
 for(int x:F){h[x]=x;used|=1U<<x;active_points[active_count++]=x;}
 for(int i=0;i<4;i++)for(int j=i+1;j<4;j++){if(ll(F[i],F[i],F[j],F[j]))Zp++;if(FULL){uint64_t p[32]={0};if(!add_pending(p,F[i],F[i],F[j],F[j]))return false;for(int s=1;s<N;s++)lagset[s]|=p[s];}}
 if(AUDIT){assert(Zp==0);assert(active_count==4);assert(__builtin_popcount(used)==4);if(FULL)assert(held_bits()==6);}return Zp==0;
}
static int selftest(){
 FULL=true;AUDIT=true;int A[4]={0,1,4,10};memcpy(F,A,sizeof F);if(!seed_fixed())return 1;
 // Signed-vector separation: fixed (1,1) and internal transposition (1,-1) coexist.
 uint32_t u0=used;int z0=Zp,mark=trail_size,ac0=active_count;if(!place_pair(6,7))return 2;assert((lagset[1]&(1ULL<<bit_of(1)))&&(lagset[1]&(1ULL<<bit_of(-1))));rollback(mark);used=u0;Zp=z0;active_count=ac0;
 int same=0,opp=0;for(int r=1;r<=15;r++)for(int s=r+1;s<=15;s++)((r+s)&1?opp:same)++;assert(same==49&&opp==56);
 puts("SELFTEST PASS: seed_Z=0 signed_vectors distinct pairs=49/56");return 0;
}
int main(int argc,char**argv){
 if(argc==2&&string(argv[1])=="--selftest")return selftest();
 if(argc<5){fprintf(stderr,"usage: %s ruler_id mode catalogue.csv audit(0|1)\n",argv[0]);return 2;}
 rid=atoi(argv[1]);FULL=string(argv[2])!="structural";AUDIT=atoi(argv[4])!=0;
 ifstream in(argv[3]);string line;getline(in,line);bool found=false;while(getline(in,line)){stringstream ss(line);string id,marks;getline(ss,id,',');getline(ss,marks,',');if(atoi(id.c_str())!=rid)continue;stringstream mm(marks);for(int i=0;i<4;i++)mm>>F[i];found=true;break;}if(!found)return 3;
 int aeven=0,sumF=0;for(int x:F){aeven+=(x%2==0);sumF+=x;}
 nodes=0;
 parity_admissible_records=0;
 seed_compatible_records=0;
 long_candidates=0;
 long_seed_ok=0;
 structural_covers=0;
 costas_covers=0;
 collision_prunes=0;
 z_prunes=0;
 sum_prunes=0;
 domain_prunes=0;
 if(getenv("POSARM"))POSARM=true;
 if(!seed_fixed())return 4;
 for(int L=16;L<32;L++)for(int u=0;u+L<32;u++){
  int v=u+L;if((used>>u&1U)||(used>>v&1U))continue;long_candidates++;
  for(int r=1;r<=15;r++)for(int s=r+1;s<=15;s++){
   if(((L-aeven-r-s)&1)==0)parity_admissible_records++;
  }
  uint32_t fixed_used=used;int fixed_z=Zp,hu=h[u],hv=h[v],markL=trail_size,acL=active_count;
  if(!place_pair(u,v)){rollback(markL);active_count=acL;used=fixed_used;Zp=fixed_z;h[u]=hu;h[v]=hv;continue;}
  if(Zp!=1){rollback(markL);active_count=acL;used=fixed_used;Zp=fixed_z;h[u]=hu;h[v]=hv;continue;}long_seed_ok++;if(AUDIT){assert(recompute_Z()==1);assert(__builtin_popcount(used)==6);}
  for(int r=1;r<=15;r++)for(int s=r+1;s<=15;s++){
   if((L-aeven-r-s)&1)continue;
   seed_compatible_records++;
   nord=0;
   for(int d=15;d>=1;d--)if(d!=r&&d!=s)orderD[nord++]=d;
   if(AUDIT)assert(nord==13);
   target_short=496-sumF-(2*u+L);
   rec_short(0,0);
  }
  rollback(markL);active_count=acL;used=fixed_used;Zp=fixed_z;h[u]=hu;h[v]=hv;
 }
 const char* pred=FULL?"EXACT_Z1T_F4_AND_FULL_COSTAS":"EXACT_Z1T_F4_STRUCTURAL";
 const char* status=FULL?(costas_covers?"EXHAUSTED_WITH_COSTAS_Z1T_F4_COVERS":"EXHAUSTED_NO_COSTAS_Z1T_F4_COVER"):(structural_covers?"EXHAUSTED_WITH_STRUCTURAL_Z1T_F4_COVERS":"EXHAUSTED_NO_STRUCTURAL_Z1T_F4_COVER");
 fprintf(stderr,"T4-8 terminal_calls=%lld accepted_terminals=%lld\n",terminal_calls,accepted_terminals);
 printf("F%04d,%s,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%lld,%s\n",rid,pred,long_candidates,parity_admissible_records,long_seed_ok,seed_compatible_records,nodes,structural_covers,costas_covers,collision_prunes,z_prunes,sum_prunes,domain_prunes,status);return 0;
}
