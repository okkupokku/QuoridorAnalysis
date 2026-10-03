import sys, json, random, subprocess, math, os, time
sys.path.insert(0,'.')
from mine import Mine
HERE=os.path.dirname(os.path.abspath(__file__))
class Solver:
    def __init__(self,n,w):
        self.p=subprocess.Popen([os.path.join(HERE,'solver'),str(n),str(w),'serve'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
        self.header=self.p.stdout.readline().strip()
    def query(self,moves):
        self.p.stdin.write(' '.join(moves)+'\n'); self.p.stdin.flush()
        first=self.p.stdout.readline().split()
        if first[0]!='VAL': return None
        v=int(first[1]); d=int(first[2]); ch={}
        while True:
            l=self.p.stdout.readline().split()
            if l[0]=='END': break
            ch[l[0]]=(l[1],int(l[2])) if l[1]=='W' else (int(l[1]),int(l[2]))
        return v,d,ch
def gen_games(m,rng,ngames,maxply,mix):
    games=[]
    for g in range(ngames):
        eps=rng.choice(mix); depth=rng.choice([1,2,3]); moves=[]
        while len(moves)<maxply:
            L=m.q(cmd='legal',moves=moves)
            if L['winner']>=0: break
            if rng.random()<eps:
                if L['walls'] and L['wl'][L['turn']]>0 and rng.random()<0.4: mv=rng.choice(L['walls'])
                else: mv=rng.choice(L['pawn'])
            else:
                b=m.q(cmd='best',moves=moves,depth=depth); mv=b['move']
            moves.append(mv)
        games.append(moves)
    return games
def sig_true(v): return 1.0 if v==1 else 0.0
if __name__=='__main__':
    n=int(sys.argv[1]); w=int(sys.argv[2]); ng=int(sys.argv[3]); depths=[int(x) for x in sys.argv[4].split(',')]; out=sys.argv[5]
    rng=random.Random(42+n*10+w)
    m=Mine('bridge_n.js'); m.q(cmd='config',n=n,w=w)
    sol=Solver(n,w); print(sol.header,flush=True)
    games=gen_games(m,rng,ng,60,[0.1,0.2,0.3,0.5,0.8])
    # positions
    rows=[]; rule_mis=0; npos=0
    for gi,g in enumerate(games):
        for i,mv in enumerate(g):
            pos=g[:i]; q=sol.query(pos)
            if q is None: continue
            v,d,ch=q
            L=m.q(cmd='legal',moves=pos)
            mine_set=set(L['pawn'])|set(L['walls']); npos+=1
            if mine_set!=set(ch.keys()): rule_mis+=1
            cv,cd=ch[mv]
            rows.append({'g':gi,'i':i,'pos':pos,'move':mv,'v':v,'d':d,'child':cv,'cd':cd,'nlegal':len(ch),
                         'nwin':sum(1 for x in ch.values() if x[0] in ('W',1)),'mindtm':min([x[1] for x in ch.values() if x[0] in ('W',1)] or [0]),'ch':ch})
    print('positions',npos,'rule set mismatches (solver vs JS legal moves):',rule_mis,flush=True)
    res={'n':n,'w':w,'rows':[{k:r[k] for k in ('g','i','move','v','d','child','cd','nlegal','nwin','mindtm')} for r in rows],'rule_mis':rule_mis,'npos':npos,'depths':{}}
    for depth in depths:
        t0=time.time(); ev=[]
        for r in rows:
            e=m.q(cmd='ply',moves=r['pos']+[r['move']],ply=len(r['pos']),depth=depth)   # analyzes last move in context
            b=m.q(cmd='best',moves=r['pos'],depth=depth)
            ev.append({'cls':e['cls'],'drop':e['drop'],'wpBefore':e['wpBeforeWhite'] if e['player']==0 else 1-e['wpBeforeWhite'],
                       'wpAfter':e['wpWhite'] if e['player']==0 else 1-e['wpWhite'],'best':b['move'] if b else None,'bestEq':e['best']==r['move'],'bestmove':e['best']})
        res['depths'][depth]=ev; print('depth',depth,'done',round(time.time()-t0,1),'s',flush=True)
    # attach child values for chosen engine moves
    for depth,ev in res['depths'].items():
        for r,e in zip(rows,ev):
            e['best_child']=r['ch'].get(e['bestmove'],[None,None])[0]
    json.dump(res,open(out,'w'))
