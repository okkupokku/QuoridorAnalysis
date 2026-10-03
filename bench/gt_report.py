import json, sys, math
def auc(pos,neg):
    # P(score_pos > score_neg), ties 0.5
    if not pos or not neg: return float('nan')
    allv=sorted([(s,1) for s in pos]+[(s,0) for s in neg]); 
    rank=0; i=0; sumpos=0.0
    while i<len(allv):
        j=i
        while j<len(allv) and allv[j][0]==allv[i][0]: j+=1
        avg=(i+1+j)/2
        sumpos+=avg*sum(1 for k in range(i,j) if allv[k][1]==1); i=j
    return (sumpos-len(pos)*(len(pos)+1)/2)/(len(pos)*len(neg))
def norm(c): return 1 if c in ('W',1) else 2 if c==2 else 0
def report(path):
    d=json.load(open(path)); rows=d['rows']; out=[]
    out.append('## %dx%d board, %d walls each: %d positions from %d games; rule mismatches vs solver: %d'%(d['n'],d['n'],d['w'],d['npos'],len(set(r['g'] for r in rows)),d['rule_mis']))
    for depth,ev in sorted(d['depths'].items(),key=lambda x:int(x[0])):
        win=[(r,e) for r,e in zip(rows,ev) if r['v']==1]; loss=[(r,e) for r,e in zip(rows,ev) if r['v']==2]
        # true error: mover is winning but plays a move to a lost position
        tp=fp=fn=tn=0
        for r,e in win:
            err=norm(r['child'])==2; flag=e['cls'] in ('mistake','blunder')
            if err and flag: tp+=1
            elif err: fn+=1
            elif flag: fp+=1
            else: tn+=1
        prec=tp/(tp+fp) if tp+fp else float('nan'); rec=tp/(tp+fn) if tp+fn else float('nan')
        a=auc([e['drop'] for r,e in win if norm(r['child'])==2],[e['drop'] for r,e in win if norm(r['child'])!=2])
        # flagged although the win was kept: how many were much slower wins (>=3 plies longer than the fastest win)?
        slow=sum(1 for r,e in win if norm(r['child'])==1 and e['cls'] in ('mistake','blunder') and r['cd']-r['mindtm']>=3)
        keepflag=sum(1 for r,e in win if norm(r['child'])==1 and e['cls'] in ('mistake','blunder'))
        # best move optimality
        opt=sum(1 for r,e in win if e['best_child'] is not None and norm(e['best_child'])==1)
        # who-is-winning verdict
        ver=sum(1 for r,e in zip(rows,ev) if (e['wpBefore']>0.5)==(r['v']==1))
        brier=sum((e['wpBefore']-(1 if r['v']==1 else 0))**2 for r,e in zip(rows,ev))/len(rows)
        lossflag=sum(1 for r,e in loss if e['cls'] in ('mistake','blunder'))
        out.append('depth %s | winning positions %d (of which player erred %d): flagged mistake/blunder TP=%d FN=%d FP=%d TN=%d  precision=%.2f recall=%.2f  AUC(drop)=%.3f'%(depth,len(win),tp+fn,tp,fn,fp,tn,prec,rec,a))
        out.append('         of the %d flagged-but-win-kept moves, %d (%.0f%%) made the win >=3 plies slower than the fastest win'%(keepflag,slow,100*slow/max(1,keepflag)))
        out.append('         best-move keeps the win: %d/%d (%.1f%%) | verdict "who is winning" correct: %.1f%% | Brier(win%%)=%.3f (0.25 = coin flip) | lost-position moves flagged as mistakes (noise): %d/%d'%(opt,len(win),100*opt/max(1,len(win)),100*ver/len(rows),brier,lossflag,len(loss)))
    return '\n'.join(out)
if __name__=='__main__':
    for p in sys.argv[1:]: print(report(p)); print()
