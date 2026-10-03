import subprocess, os, re
HERE=os.path.dirname(os.path.abspath(__file__))
class ZQ:
    def __init__(self):
        d=os.path.join(HERE,'zquoridor')
        self.p=subprocess.Popen([os.path.join(d,'bin/zquoridor'),'--nnue',os.path.join(d,'data/nnue/nnue_weights_int8.bin')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1,cwd=d)
        self._send('uci','uciok'); self._send('isready','readyok')
    def _send(self,line,until):
        self.p.stdin.write(line+'\n'); self.p.stdin.flush(); out=[]
        while True:
            l=self.p.stdout.readline()
            if l=='': break
            out.append(l.strip())
            if l.strip().startswith(until): break
        return out
    def go(self,moves,ms=500):
        """returns (bestmove, mover win prob) for the side to move after `moves`"""
        self.p.stdin.write('position startpos'+(' moves '+' '.join(moves) if moves else '')+'\n'); self.p.stdin.flush()
        out=self._send('go movetime %d'%ms,'bestmove')
        q=None
        for l in out:
            m=re.search(r'rootq ([-0-9.e+]+)',l)
            if m: q=float(m.group(1))
        bm=out[-1].split()[1] if out and out[-1].startswith('bestmove') else None
        return bm,q
    def new(self): self.p.stdin.write('ucinewgame\n'); self.p.stdin.flush()
    def close(self):
        try: self.p.stdin.write('quit\n'); self.p.stdin.flush(); self.p.wait(timeout=3)
        except Exception: self.p.kill()
