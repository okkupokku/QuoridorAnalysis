import sys, json, random, time
sys.path.insert(0,'.')
from mine import Mine
from qtp import *
from multiprocessing import Pool
def work(args):
    name,pos=args
    eng=pavlos() if name=='pavlos' else georgen(); m=Mine()
    try:
        eng.clear()
        for i,mv in enumerate(pos):
            if not eng.play(i%2,mv): return {'name':name,'status':'replay_fail'}
        side=len(pos)%2
        t=time.time(); their=eng.genmove(side); dt=time.time()-t
        L=m.q(cmd='legal',moves=pos)
        out={'name':name,'status':'ok','pos':pos,'their':their,'dt':dt,'legal': their in L['pawn'] or their in L['walls']}
        for d in (4,6):
            b=m.q(cmd='best',moves=pos,depth=d); out['mine%d'%d]=b['move'] if b else None
        if out['legal']:
            e=m.q(cmd='ply',moves=pos+[their],ply=len(pos),depth=6); out['their_cls']=e['cls']; out['their_drop']=e['drop']; out['mine_best_in_ctx']=e['best']
        return out
    finally:
        eng.close(); m.close()
if __name__=='__main__':
    a=json.load(open('stab9.json')); rng=random.Random(5)
    positions=[]
    for g in a['games']:
        for i in rng.sample(range(4,min(len(g),70)),4): positions.append(g[:i])
    rng.shuffle(positions); positions=positions[:140]
    jobs=[(n,p) for n in ('pavlos','georgen') for p in positions]
    t=time.time()
    with Pool(8) as pool: res=pool.map(work,jobs,chunksize=1)
    json.dump(res,open('posagree.json','w')); print('done',round(time.time()-t))
