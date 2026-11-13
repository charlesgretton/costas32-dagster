#include <bits/stdc++.h>
using namespace std;
struct Tr{int a,b,c,l;};
int main(){vector<Tr>T; vector<vector<int>> inc(32); for(int l=1;l<=15;l++)for(int r=0;r<32-2*l;r++){int w=T.size();T.push_back({r,r+l,r+2*l,l});inc[r].push_back(w);inc[r+l].push_back(w);inc[r+2*l].push_back(w);} mt19937_64 g(1234567); uniform_real_distribution<double> U(0,1); int global=999; vector<int> gq; auto sat=[&](const vector<int>&q,int w){auto z=T[w];return ((q[z.a]+q[z.c]-2*q[z.b])&3)==0;};
 auto st=chrono::steady_clock::now();
 for(int rep=0;rep<20000 && global>0;rep++){vector<int>q;for(int s=0;s<4;s++)for(int j=0;j<8;j++)q.push_back(s);shuffle(q.begin(),q.end(),g);vector<char> ok(T.size());int sc=0;for(int w=0;w<(int)T.size();w++)sc+=(ok[w]=sat(q,w));double temp=3.0;
  for(int it=0;it<200000;it++){int i=g()%32,j=g()%32;if(i==j||q[i]==q[j])continue; vector<int> ids=inc[i];ids.insert(ids.end(),inc[j].begin(),inc[j].end());sort(ids.begin(),ids.end());ids.erase(unique(ids.begin(),ids.end()),ids.end());int old=0;for(int w:ids)old+=ok[w];swap(q[i],q[j]);int nw=0;for(int w:ids)nw+=sat(q,w);int delta=nw-old;if(delta<=0||U(g)<exp(-delta/temp)){sc+=delta;for(int w:ids)ok[w]=sat(q,w);}else swap(q[i],q[j]); temp=max(.02,temp*.99995);if(sc<global){global=sc;gq=q;cerr<<"best "<<global<<" rep "<<rep<<" it "<<it<<"\n";}if(sc==0)break;}
  if(rep%100==0)cerr<<"rep "<<rep<<" global "<<global<<"\n";
 }
 cout<<"best "<<global<<"\n";for(int v:gq)cout<<v<<' ';cout<<"\n";vector<int>prof(16);for(auto z:T)if(((gq[z.a]+gq[z.c]-2*gq[z.b])&3)==0)prof[z.l]++;for(int l=1;l<=15;l++)cout<<l<<":"<<prof[l]<<" ";cout<<"\n";
}
