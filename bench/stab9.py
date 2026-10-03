import sys, json, glob, time
sys.path.insert(0,'.')
from mine import Mine
from multiprocessing import Pool
DEPTHS=[3,4,5,6]
def work(g):
    m=Mine(); out={}
    for d in DEPTHS:
        r=m.q(cmd='analyze',moves=g,depth=d); out[d]=[(e['cls'],e['drop'],e['best'],e['move'],e['wpWhite']) for e in r['entries']]
    m.close(); return out
if __name__=='__main__':
    games=[]
    for f in sorted(glob.glob('m_pavlos_d[345].json')):
        for r in json.load(open(f)):
            if r['status'] in ('ok','draw_cap') or r['status'].startswith('rule_dispute'):
                g=r['moves'][:-1] if r['status'].startswith('rule_dispute') else r['moves']
                if len(g)>20: games.append(g[:100])
    games=games[:45]; print(len(games),'games',sum(map(len,games)),'plies',flush=True)
    t=time.time()
    with Pool(8) as p: res=p.map(work,games,chunksize=1)
    json.dump({'games':games,'res':[{str(k):v for k,v in r.items()} for r in res]},open('stab9.json','w')); print('done',round(time.time()-t))
