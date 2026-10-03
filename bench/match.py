import sys, json, random, time, os
sys.path.insert(0,'.')
from mine import Mine
from qtp import *
from multiprocessing import Pool

def make_opp(name):
    return {'pavlos':pavlos,'georgen':georgen}[name]()

def play_game(args):
    opp_name, depth, mine_white, seed, nopen, maxply = args
    rng=random.Random(seed)
    m=Mine(); opp=make_opp(opp_name)
    moves=[]; times=[]; status='ok'; opp_time=[]
    try:
        # random opening (same for both colour assignments of one seed)
        for i in range(nopen):
            L=m.q(cmd='legal',moves=moves)
            if L['walls'] and L['wl'][L['turn']]>0 and rng.random()<0.3: mv=rng.choice(L['walls'])
            else: mv=rng.choice(L['pawn'])
            if not opp.play(i%2,mv): status='opp_rejects_opening'; break
            moves.append(mv)
        while status=='ok' and len(moves)<maxply:
            L=m.q(cmd='legal',moves=moves)
            if L['winner']>=0: break
            side=L['turn']; mine_turn=(side==0)==mine_white
            if mine_turn:
                t=time.time(); b=m.q(cmd='best',moves=moves,depth=depth); times.append(time.time()-t)
                mv=b['move']
                if not opp.play(side,mv): status='opp_rejects_my_move:'+mv; break
            else:
                t=time.time(); mv=opp.genmove(side); opp_time.append(time.time()-t); raw=getattr(opp,'last_raw',None)
                if mv is None: status='opp_no_move'; break
                if mv not in L['pawn'] and mv not in L['walls']: status='rule_dispute:'+mv+' raw='+str(raw); moves.append(mv); break
            moves.append(mv)
        L=m.q(cmd='legal',moves=moves)
        w=L['winner']
        if status=='ok' and w<0: status='draw_cap'
    finally:
        m.close(); opp.close()
    mine_color=0 if mine_white else 1
    result = None if w<0 else (1.0 if w==mine_color else 0.0)
    if status.startswith('rule_dispute'): result=1.0   # opponent produced an illegal move = forfeit
    return {'opp':opp_name,'depth':depth,'mine_white':mine_white,'seed':seed,'moves':moves,'winner':w,'result':result,'status':status,
            'mine_ms':1000*sum(times)/max(1,len(times)),'opp_ms':1000*sum(opp_time)/max(1,len(opp_time))}

if __name__=='__main__':
    opp, depth, n, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    procs=int(sys.argv[5]) if len(sys.argv)>5 else 10
    jobs=[(opp,depth,w,1000+s,4,150) for s in range(n) for w in (True,False)]
    t0=time.time(); res=[]
    with Pool(procs) as p:
        for r in p.imap_unordered(play_game,jobs):
            res.append(r); print(len(res),len(jobs),r['status'],r['result'],len(r['moves']),round(r['mine_ms']),round(r['opp_ms']),flush=True)
    json.dump(res,open(out,'w'))
    ok=[r for r in res if r['status'] in('ok','draw_cap') or r['status'].startswith('rule_dispute')]
    sc=sum((0.5 if r['result'] is None else r['result']) for r in ok)
    print('RESULT',opp,'mine depth',depth,'score',sc,'/',len(ok),'| disputes',sum(r['status'].startswith('rule_dispute') for r in res),'| time',round(time.time()-t0))
