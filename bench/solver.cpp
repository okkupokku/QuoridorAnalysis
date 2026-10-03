// Exact retrograde solver for small N x N Quoridor (same rules as the app).
// Usage: solver N W [serve]   -- builds table; with 'serve' reads move lists from stdin.
#include <vector>
#include <unordered_map>
#include <string>
#include <sstream>
#include <iostream>
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <functional>
using namespace std;
using namespace std;
typedef uint64_t u64; typedef uint32_t u32;
int N, M, W, SC;
struct St { int px[2], py[2], wl[2], turn; u32 h, v; };
static inline u64 pack(const St&s){
  u64 k=0; k=s.h; k=(k<<M*M)|s.v;
  k=(k<<5)|(s.py[0]*N+s.px[0]); k=(k<<5)|(s.py[1]*N+s.px[1]);
  k=(k<<3)|s.wl[0]; k=(k<<3)|s.wl[1]; k=(k<<1)|s.turn; return k;
}
static inline St unpack(u64 k){
  St s; s.turn=k&1; k>>=1; s.wl[1]=k&7; k>>=3; s.wl[0]=k&7; k>>=3;
  int c1=k&31; k>>=5; int c0=k&31; k>>=5;
  s.px[0]=c0%N; s.py[0]=c0/N; s.px[1]=c1%N; s.py[1]=c1/N;
  u32 mask=(M*M==16)?0xFFFF:((1u<<(M*M))-1);
  s.v=k&mask; k>>=M*M; s.h=k&mask; return s;
}
static const int DX[4]={0,0,1,-1}, DY[4]={1,-1,0,0};
static inline bool hb(const St&s,int c,int r){ return c>=0&&c<M&&r>=0&&r<M&&((s.h>>(r*M+c))&1); }
static inline bool vb(const St&s,int c,int r){ return c>=0&&c<M&&r>=0&&r<M&&((s.v>>(r*M+c))&1); }
bool blocked(const St&s,int x,int y,int d){
  switch(d){
    case 0: return y==N-1||hb(s,x,y)||hb(s,x-1,y);
    case 1: return y==0||hb(s,x,y-1)||hb(s,x-1,y-1);
    case 2: return x==N-1||vb(s,x,y)||vb(s,x,y-1);
    default: return x==0||vb(s,x-1,y)||vb(s,x-1,y-1);
  }
}
int goalRow(int p){ return p==0?N-1:0; }
int pawnMoves(const St&s,int p,int out[][2]){
  int o=1-p,x=s.px[p],y=s.py[p],n=0;
  for(int d=0;d<4;d++){
    if(blocked(s,x,y,d)) continue;
    int tx=x+DX[d],ty=y+DY[d];
    if(tx!=s.px[o]||ty!=s.py[o]){ out[n][0]=tx;out[n][1]=ty;n++; continue; }
    if(!blocked(s,tx,ty,d)){ out[n][0]=tx+DX[d];out[n][1]=ty+DY[d];n++; continue; }
    for(int e=0;e<4;e++){ if(e==d||e==(d^1)) continue; if(!blocked(s,tx,ty,e)){ out[n][0]=tx+DX[e];out[n][1]=ty+DY[e];n++; } }
  }
  return n;
}
bool reach(const St&s,int p){
  int goal=goalRow(p); bool seen[25]={0}; int q[25],h=0,t=0; int st=s.py[p]*N+s.px[p]; q[t++]=st; seen[st]=1;
  while(h<t){ int c=q[h++],x=c%N,y=c/N; if(y==goal) return true;
    for(int d=0;d<4;d++){ if(blocked(s,x,y,d)) continue; int n=(y+DY[d])*N+x+DX[d]; if(!seen[n]){seen[n]=1;q[t++]=n;} } }
  return false;
}
bool overlaps(const St&s,int t,int c,int r){
  if(t==1) return hb(s,c,r)||hb(s,c-1,r)||hb(s,c+1,r)||vb(s,c,r);
  return vb(s,c,r)||vb(s,c,r-1)||vb(s,c,r+1)||hb(s,c,r);
}
bool wallOK(St s,int t,int c,int r){
  if(s.wl[s.turn]<=0||overlaps(s,t,c,r)) return false;
  if(t==1) s.h|=1u<<(r*M+c); else s.v|=1u<<(r*M+c);
  return reach(s,0)&&reach(s,1);
}
St startState(){ St s; s.px[0]=s.px[1]=SC; s.py[0]=0; s.py[1]=N-1; s.wl[0]=s.wl[1]=W; s.turn=0; s.h=s.v=0; return s; }
St applyWall(St s,int t,int c,int r){ if(t==1) s.h|=1u<<(r*M+c); else s.v|=1u<<(r*M+c); s.wl[s.turn]--; s.turn^=1; return s; }
St applyPawn(St s,int x,int y){ s.px[s.turn]=x; s.py[s.turn]=y; s.turn^=1; return s; }
// value codes
enum {UNK=0, WIN=1, LOSS=2};
vector<u64> keys; unordered_map<u64,u32> idOf; vector<uint8_t> val; vector<uint16_t> dtm;
vector<u32> off, adj;

int main(int argc,char**argv){
  N=atoi(argv[1]); W=atoi(argv[2]); M=N-1; SC=N>>1; bool serve=argc>3;
  idOf.reserve(1<<22);
  St s0=startState(); keys.push_back(pack(s0)); idOf[keys[0]]=0;
  vector<uint8_t> immWin; immWin.push_back(0);
  off.push_back(0);
  for(size_t i=0;i<keys.size();i++){
    St s=unpack(keys[i]); int p=s.turn; int pm[8][2]; int n=pawnMoves(s,p,pm); bool win=false;
    for(int k=0;k<n;k++) if(pm[k][1]==goalRow(p)) win=true;
    if(win){ immWin[i]=1; off.push_back(adj.size()); if(i+1<keys.size()) {} ; continue; }
    auto add=[&](const St&c){ u64 k=pack(c); auto it=idOf.find(k); u32 id;
      if(it==idOf.end()){ id=keys.size(); idOf[k]=id; keys.push_back(k); immWin.push_back(0);} else id=it->second; adj.push_back(id); };
    for(int k=0;k<n;k++) add(applyPawn(s,pm[k][0],pm[k][1]));
    if(s.wl[p]>0) for(int t=1;t<=2;t++) for(int r=0;r<M;r++) for(int c=0;c<M;c++) if(wallOK(s,t,c,r)) add(applyWall(s,t,c,r));
    off.push_back(adj.size());
  }
  size_t S=keys.size(); fprintf(stderr,"states %zu edges %zu\n",S,adj.size());
  // reverse edges
  vector<u32> roff(S+1,0), radj(adj.size());
  for(size_t i=0;i<adj.size();i++) roff[adj[i]+1]++;
  for(size_t i=0;i<S;i++) roff[i+1]+=roff[i];
  { vector<u32> pos(roff.begin(),roff.end()-1);
    for(size_t i=0;i<S;i++) for(u32 e=off[i];e<off[i+1];e++) radj[pos[adj[e]]++]=i; }
  val.assign(S,UNK); dtm.assign(S,0); vector<u32> cnt(S);
  vector<u32> q; q.reserve(S);
  for(size_t i=0;i<S;i++){ cnt[i]=off[i+1]-off[i]; if(immWin[i]){ val[i]=WIN; dtm[i]=1; q.push_back(i);} }
  for(size_t h=0;h<q.size();h++){ u32 s=q[h];
    for(u32 e=roff[s];e<roff[s+1];e++){ u32 p=radj[e]; if(val[p]!=UNK) continue;
      if(val[s]==LOSS){ val[p]=WIN; dtm[p]=dtm[s]+1; q.push_back(p); }
      else if(--cnt[p]==0){ val[p]=LOSS; dtm[p]=dtm[s]+1; q.push_back(p); } } }
  size_t nw=0,nl=0,nd=0; for(size_t i=0;i<S;i++){ if(val[i]==WIN)nw++; else if(val[i]==LOSS)nl++; else nd++; }
  const char* r0 = val[0]==WIN?"first player (white) wins":val[0]==LOSS?"second player (black) wins":"draw";
  printf("N=%d W=%d states=%zu win=%zu loss=%zu draw=%zu start: %s (dtm %d)\n",N,W,S,nw,nl,nd,r0,dtm[0]); fflush(stdout);
  if(!serve) return 0;
  // serve: each stdin line = move list; reply: VAL v dtm ; then per legal move "move v dtm" (child value from mover's view)
  string line; const char* LET="abcdefghi";
  auto code=[&](u32 id,int&d)->int{ d=dtm[id]; return val[id]; };
  while(getline(cin,line)){
    stringstream ss(line); string tok; St s=startState(); bool bad=false;
    while(ss>>tok){ int x=tok[0]-'a', y=tok[1]-'1';
      if(tok.size()==2) s=applyPawn(s,x,y); else s=applyWall(s,tok[2]=='h'?1:2,x,y); }
    auto it=idOf.find(pack(s)); if(it==idOf.end()){ printf("UNREACHABLE\n"); fflush(stdout); continue; }
    int p=s.turn; u32 id=it->second; printf("VAL %d %d\n",val[id],dtm[id]);
    int pm[8][2]; int n=pawnMoves(s,p,pm);
    for(int k=0;k<n;k++){ char mv[8]; snprintf(mv,8,"%c%d",LET[pm[k][0]],pm[k][1]+1);
      if(pm[k][1]==goalRow(p)){ printf("%s W 1\n",mv); continue; }
      St c=applyPawn(s,pm[k][0],pm[k][1]); u32 ci=idOf[pack(c)]; printf("%s %d %d\n",mv,val[ci]==WIN?LOSS:val[ci]==LOSS?WIN:UNK,dtm[ci]); }
    if(s.wl[p]>0) for(int t=1;t<=2;t++) for(int r=0;r<M;r++) for(int c=0;c<M;c++) if(wallOK(s,t,c,r)){
      St cc=applyWall(s,t,c,r); u32 ci=idOf[pack(cc)]; char mv[8]; snprintf(mv,8,"%c%d%c",LET[c],r+1,t==1?'h':'v');
      printf("%s %d %d\n",mv,val[ci]==WIN?LOSS:val[ci]==LOSS?WIN:UNK,dtm[ci]); }
    printf("END\n"); fflush(stdout);
  }
}
