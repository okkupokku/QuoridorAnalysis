import json,glob,sys
a=json.load(open('stab9.json')); games=a['games']; res=a['res']
try: resb=json.load(open('stab9b.json'))['res']
except Exception: resb=None
# rebuild outcome per game in the same order as stab9.py
outs=[]
for f in sorted(glob.glob('m_pavlos_d[345].json')):
    for r in json.load(open(f)):
        if r['status'] in ('ok','draw_cap') or r['status'].startswith('rule_dispute'):
            g=r['moves'][:-1] if r['status'].startswith('rule_dispute') else r['moves']
            if len(g)>20:
                mc=0 if r['mine_white'] else 1
                if r['status'].startswith('rule_dispute'): w=mc
                else: w=r['winner']
                outs.append(w)
outs=outs[:45]
def series(d):
    pts=[]
    for gi,r in enumerate(res):
        src=r if str(d) in r else resb[gi]
        w=outs[gi]
        if w<0: continue
        for i,x in enumerate(src[str(d)]):
            pts.append((x[4],1.0 if w==0 else 0.0,i,len(src[str(d)])))
    return pts
for d in [4,6]+([8] if resb else []):
    pts=series(d)
    br=sum((p-o)**2 for p,o,_,_ in pts)/len(pts)
    base=sum((0.5-o)**2 for p,o,_,_ in pts)/len(pts)
    acc=sum(1 for p,o,_,_ in pts if (p>0.5)==(o==1.0))/len(pts)
    # early / mid / late thirds
    def part(lo,hi):
        q=[(p,o) for p,o,i,n in pts if lo<=i/n<hi]; 
        return (sum((p-o)**2 for p,o in q)/len(q), sum(1 for p,o in q if (p>0.5)==(o==1.0))/len(q))
    e,m_,l=part(0,.34),part(.34,.67),part(.67,1.01)
    print('depth %d: %d positions from %d finished games | Brier %.3f (coin-flip %.3f) | predicts eventual winner %.0f%% | by game phase (Brier/accuracy): early %.3f/%.0f%%, middle %.3f/%.0f%%, late %.3f/%.0f%%'%(d,len(pts),len(set(range(len(outs)))),br,base,100*acc,e[0],100*e[1],m_[0],100*m_[1],l[0],100*l[1]))
    bins=[0]*10; cnt=[0]*10
    for p,o,_,_ in pts:
        b=min(9,int(p*10)); bins[b]+=o; cnt[b]+=1
    print('   reliability (predicted bucket -> actual white win rate): '+', '.join('%d-%d%%: %.0f%% (n=%d)'%(10*i,10*i+10,100*bins[i]/cnt[i],cnt[i]) for i in range(10) if cnt[i]))
