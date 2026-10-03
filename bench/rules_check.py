import sys, json, time
sys.path.insert(0,'.')
from mine import Mine
from qtp import *
LET='abcdefghi'
which=sys.argv[1]; step=int(sys.argv[2]); games=json.load(open('games_rules.json'))
eng=pavlos() if which=='pavlos' else georgen()
m=Mine()
cands_pawn=[c+str(r) for c in LET for r in range(1,10)]
cands_wall=[c+str(r)+o for c in LET[:8] for r in range(1,9) for o in 'hv']
tot=0; mism=[]; replay_fail=[]; t0=time.time()
for gi,g in enumerate(games):
    for ply in range(0,len(g),step):
        pos=g[:ply]; L=m.q(cmd='legal',moves=pos)
        if L['winner']>=0: continue
        eng.clear(); ok=True
        for i,mv in enumerate(pos):
            if not eng.play(i%2,mv): ok=False; replay_fail.append((gi,i,mv)); break
        if not ok: break
        side=L['turn']; mine_set=set(L['pawn'])|set(L['walls'])
        theirs=set()
        for c in cands_pawn+cands_wall:
            if eng.play(side,c): theirs.add(c); eng.undo(1)
        tot+=1
        extra=theirs-mine_set; missing=mine_set-theirs
        if extra or missing: mism.append({'game':gi,'ply':ply,'extra_in_engine':sorted(extra),'missing_in_engine':sorted(missing),'moves':pos})
print(which,'positions',tot,'mismatch positions',len(mism),'replay failures',len(replay_fail),'time',round(time.time()-t0))
json.dump({'mism':mism,'replay_fail':replay_fail,'positions':tot},open('rules_%s.json'%which,'w'))
for x in mism[:5]: print(x['ply'],'engine-only:',x['extra_in_engine'][:6],'mine-only:',x['missing_in_engine'][:6])
for x in replay_fail[:5]: print('replay fail',x)
