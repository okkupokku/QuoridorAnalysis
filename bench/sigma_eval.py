import sys, json, time
sys.path.insert(0,'.')
import sigma
from multiprocessing import Pool
SIMS=int(sys.argv[1]) if len(sys.argv)>1 else 100
def work(g):
    return [sigma.search(g[:i],SIMS) for i in range(len(g)+1)]
if __name__=='__main__':
    a=json.load(open('stab9.json')); games=a['games']; t=time.time()
    with Pool(6) as p: res=p.map(work,games,chunksize=1)
    json.dump({'sims':SIMS,'res':res},open('sigma_eval.json','w')); print('done',round(time.time()-t))
