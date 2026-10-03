import sys, json, time
sys.path.insert(0,'.')
from zq import ZQ
from multiprocessing import Pool
MS=int(sys.argv[1]) if len(sys.argv)>1 else 400
def work(g):
    z=ZQ(); out=[]
    try:
        for i in range(len(g)+1):
            out.append(z.go(g[:i],MS))
    finally: z.close()
    return out
if __name__=='__main__':
    a=json.load(open('stab9.json')); games=a['games']; t=time.time()
    with Pool(8) as p: res=p.map(work,games,chunksize=1)
    json.dump({'ms':MS,'res':res},open('zq_eval.json','w')); print('done',round(time.time()-t))
