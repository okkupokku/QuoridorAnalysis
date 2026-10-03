import json,sys,math
a=json.load(open('stab9.json')); games=a['games']; res=a['res']
try: b=json.load(open('stab9b.json')); resb=b['res']
except Exception: resb=None
def flat(depth):
    out=[]
    for gi,r in enumerate(res):
        src=r if str(depth) in r else (resb[gi] if resb else None)
        out+=[x for x in src[str(depth)]]
    return out
depths=[3,4,5,6]+([7,8] if resb else [])
data={d:flat(d) for d in depths}
n=len(data[4]); print('plies analysed:',n)
def flag(x): return x[0] in ('mistake','blunder')
def cmp(d,ref):
    A=data[d]; R=data[ref]
    tp=sum(1 for x,y in zip(A,R) if flag(x) and flag(y)); fp=sum(1 for x,y in zip(A,R) if flag(x) and not flag(y)); fn=sum(1 for x,y in zip(A,R) if not flag(x) and flag(y))
    exact=sum(1 for x,y in zip(A,R) if x[0]==y[0])/n; sameBest=sum(1 for x,y in zip(A,R) if x[2]==y[2])/n
    mad=sum(abs(x[4]-y[4]) for x,y in zip(A,R))/n
    p=tp/(tp+fp) if tp+fp else float('nan'); r=tp/(tp+fn) if tp+fn else float('nan')
    return 'depth %d vs depth %d: mistake/blunder flags: agree on %d, extra %d, missed %d (precision %.2f, recall %.2f) | same rating label %.0f%% | same best move %.0f%% | mean |win%% difference| %.3f'%(d,ref,tp,fp,fn,p,r,100*exact,100*sameBest,mad)
ref=max(depths)
print('reference depth',ref,'(flagged mistakes/blunders in reference:',sum(1 for x in data[ref] if flag(x)),'of',n,')')
for d in depths:
    if d!=ref: print(cmp(d,ref))
