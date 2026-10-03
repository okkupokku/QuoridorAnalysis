import sys, json, random, time
sys.path.insert(0,'.')
from mine import Mine
from zq import ZQ
from multiprocessing import Pool
def play(args):
    depth, mine_white, seed, ms = args
    rng=random.Random(seed); m=Mine(); z=ZQ(); moves=[]; status='ok'
    try:
        for i in range(4):
            L=m.q(cmd='legal',moves=moves)
            mv=rng.choice(L['walls']) if L['walls'] and rng.random()<0.3 else rng.choice(L['pawn']); moves.append(mv)
        while len(moves)<150:
            L=m.q(cmd='legal',moves=moves)
            if L['winner']>=0: break
            mine_turn=(L['turn']==0)==mine_white
            if mine_turn: mv=m.q(cmd='best',moves=moves,depth=depth)['move']
            else:
                mv,_=z.go(moves,ms)
                if mv not in L['pawn'] and mv not in L['walls']: status='illegal:'+str(mv); break
            moves.append(mv)
        L=m.q(cmd='legal',moves=moves); w=L['winner']
    finally: m.close(); z.close()
    mc=0 if mine_white else 1
    res=None if w<0 else (1.0 if w==mc else 0.0)
    if status.startswith('illegal'): res=1.0
    return {'depth':depth,'mine_white':mine_white,'seed':seed,'moves':moves,'result':res,'status':status}
if __name__=='__main__':
    depth=int(sys.argv[1]); n=int(sys.argv[2]); ms=int(sys.argv[3]); procs=int(sys.argv[4]); out=sys.argv[5]
    jobs=[(depth,w,2000+s,ms) for s in range(n) for w in (True,False)]
    with Pool(procs) as p: res=p.map(play,jobs,chunksize=1)
    json.dump(res,open(out,'w'))
    w=sum(1 for r in res if r['result']==1.0); l=sum(1 for r in res if r['result']==0.0); d=sum(1 for r in res if r['result'] is None)
    print('mine depth',depth,'vs zquoridor %dms: wins %d losses %d draws %d (games %d), statuses %s'%(ms,w,l,d,len(res),sorted(set(r['status'] for r in res))))
