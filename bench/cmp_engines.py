import json, glob, math, itertools
a=json.load(open('stab9.json')); games=a['games']; res=a['res']; resb=json.load(open('stab9b.json'))['res']
zq=json.load(open('zq_eval.json'))['res']; sg=json.load(open('sigma_eval.json'))['res']
# outcomes (same order as stab9)
outs=[]
for f in sorted(glob.glob('m_pavlos_d[345].json')):
    for r in json.load(open(f)):
        if r['status'] in ('ok','draw_cap') or r['status'].startswith('rule_dispute'):
            g=r['moves'][:-1] if r['status'].startswith('rule_dispute') else r['moves']
            if len(g)>20:
                mc=0 if r['mine_white'] else 1
                outs.append(mc if r['status'].startswith('rule_dispute') else r['winner'])
outs=outs[:45]
# per engine: for each game, list of mover-win-prob for positions P_0..P_n, and best move per position
def mine_series(gi,d):
    src=res[gi] if str(d) in res[gi] else resb[gi]
    ent=src[str(d)]   # entries per ply: (cls,drop,best,move,wpWhite)
    n=len(ent); wpw=[None]*(n+1); best=[None]*n
    # wpWhite after ply i is entry i[4]; P_0 value derived from ply0: before = wpWhite_after + (drop) for white mover... use best-play value: wpBefore not stored -> approximate with after-values
    return ent
def white_series_from_mover(vals):    # vals[i]=mover win prob at P_i, mover = white if i even
    return [v if i%2==0 else 1-v for i,v in enumerate(vals)]
E={}
E['zquoridor']=[ [x[1] for x in zq[gi]] for gi in range(len(games))]
E['sigma100']=[ [x[1] for x in sg[gi]] for gi in range(len(games)) ]
E['sigma-raw']=[ [x[2] for x in sg[gi]] for gi in range(len(games)) ]
B={'zquoridor':[[x[0] for x in zq[gi]] for gi in range(len(games))],'sigma100':[[x[0] for x in sg[gi]] for gi in range(len(games))]}
# mine: wpWhite after each ply is available at positions P_1..P_n; P_0 = 0.5-ish. Build white series length n+1
def mine_white(gi,d):
    ent=mine_series(gi,d); ser=[0.5]+[e[4] for e in ent]; return ser
for d in (4,6,8): 
    E['mine d%d'%d]=[None]*len(games)
    for gi in range(len(games)):
        w=mine_white(gi,d); E['mine d%d'%d][gi]=[ (v if i%2==0 else 1-v) for i,v in enumerate(w)]   # mover-view
    B['mine d%d'%d]=[[e[2] for e in mine_series(gi,d)]+[None] for gi in range(len(games))]
names=list(E.keys())
print('== 1. Does the win percentage predict who actually won? (45 games, 2.6k positions)')
for nme in names:
    br=0;n=0;acc=0; ph={'early':[0,0],'mid':[0,0],'late':[0,0]}
    for gi,ser in enumerate(E[nme]):
        w=outs[gi]
        if w<0: continue
        L=len(ser)
        for i,v in enumerate(ser):
            if v is None: continue
            wv=v if i%2==0 else 1-v
            o=1.0 if w==0 else 0.0
            br+=(wv-o)**2; n+=1; ok=(wv>0.5)==(o==1.0); acc+=ok
            k='early' if i/L<.34 else 'mid' if i/L<.67 else 'late'
            ph[k][0]+=ok; ph[k][1]+=1
    print('%-10s Brier %.3f  winner predicted %.0f%%  (early %.0f%%, mid %.0f%%, late %.0f%%)'%(nme,br/n,100*acc/n,100*ph['early'][0]/ph['early'][1],100*ph['mid'][0]/ph['mid'][1],100*ph['late'][0]/ph['late'][1]))
# drop per ply
def drops(nme):
    out=[]
    for gi,ser in enumerate(E[nme]):
        d=[]
        for i in range(len(ser)-1):
            if ser[i] is None or ser[i+1] is None: d.append(None); continue
            if nme.startswith('mine'):
                # mine series are after-move values; drop stored directly
                d.append(None)
            else: d.append(max(0.0,ser[i]-(1-ser[i+1])))
        out.append(d)
    return out
D={n:drops(n) for n in ('zquoridor','sigma100','sigma-raw')}
for d in (4,6,8):
    D['mine d%d'%d]=[[e[1] for e in mine_series(gi,d)] for gi in range(len(games))]
print('\n== 2. Agreement on which moves are mistakes (win-chance drop >= 10%)')
def flags(n,thr=0.10): return [[(x is not None and x>=thr) for x in g] for g in D[n]]
F={n:flags(n) for n in D}
def agree(a,b):
    tp=fp=fn=tn=0
    for ga,gb in zip(F[a],F[b]):
        for x,y in zip(ga,gb):
            if x and y: tp+=1
            elif x: fp+=1
            elif y: fn+=1
            else: tn+=1
    prec=tp/(tp+fp) if tp+fp else float('nan'); rec=tp/(tp+fn) if tp+fn else float('nan')
    return tp,fp,fn,prec,rec
print('flagged by zquoridor: %d, by sigma: %d, by mine d4: %d, d6: %d, d8: %d (of %d moves)'%tuple([sum(map(sum,F[n])) for n in ('zquoridor','sigma100','mine d4','mine d6','mine d8')]+[sum(len(g) for g in F['zquoridor'])]))
for ref in ('zquoridor','sigma100'):
    for n in ('mine d4','mine d6','mine d8','sigma100' if ref=='zquoridor' else 'zquoridor'):
        tp,fp,fn,p,r=agree(n,ref); print('%-10s vs %-10s: its flags confirmed by reference %.0f%% (precision), reference mistakes it also flags %.0f%% (recall)  [%d/%d/%d]'%(n,ref,100*p,100*r,tp,fp,fn))
print('\n== 3. Same best move')
def same(a,b):
    n=m=0
    for ga,gb in zip(B[a],B[b]):
        for x,y in zip(ga,gb):
            if x is None or y is None: continue
            n+=1; m+=(x==y)
    return m/n
for x,y in [('zquoridor','sigma100'),('mine d4','zquoridor'),('mine d6','zquoridor'),('mine d8','zquoridor'),('mine d4','sigma100'),('mine d6','sigma100'),('mine d8','sigma100')]:
    print('%-10s vs %-10s: %.0f%%'%(x,y,100*same(x,y)))
