import json, glob, sys
sys.path.insert(0,'.')
from mine import Mine
m=Mine()
for f in sorted(glob.glob('m_*_d*.json')):
    if 'pilot' in f: continue
    res=json.load(open(f)); 
    legit=[r for r in res if r['status'] in ('ok','draw_cap')]; forf=[r for r in res if r['status'].startswith('rule_dispute')]
    w=sum(1 for r in legit if r['result']==1.0); l=sum(1 for r in legit if r['result']==0.0); dr=sum(1 for r in legit if r['result'] is None)
    # validate forfeits: was the offending side actually losing? my depth-6 evaluation of the position before the illegal move
    fv=[]
    for r in forf:
        pos=r['moves'][:-1]; b=m.q(cmd='best',moves=pos,depth=6)
        mine_color=0 if r['mine_white'] else 1
        wpw=b['wpWhite']; fv.append(wpw if mine_color==0 else 1-wpw)
    nl=sum(1 for x in fv if x>0.7)
    print(f, 'opp',res[0]['opp'],'my depth',res[0]['depth'],'| games',len(res),'| wins %d losses %d draws %d | opp illegal-move forfeits %d (my depth-6 eval says I was clearly ahead in %d of them) | my ms/move %.0f, opp ms/move %.0f'%(w,l,dr,len(forf),nl,sum(r['mine_ms'] for r in res)/len(res),sum(r['opp_ms'] for r in res)/len(res)))
