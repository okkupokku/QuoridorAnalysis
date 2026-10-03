import subprocess, re, time, os, atexit
HERE=os.path.dirname(os.path.abspath(__file__))
def to_qtp(m):
    """my notation -> (kind, vertex, orient)"""
    if len(m)==2: return ('m', m.upper(), None)
    return ('w', m[0].upper()+str(int(m[1])+1), m[2])
def from_qtp(tokens):
    """genmove result tokens -> my notation"""
    v=tokens[0].lower()
    if len(tokens)==1: return v
    o=tokens[1][0].lower()
    return v[0]+str(int(v[1:])-1)+o
class QTP:
    def __init__(self, cmd, upper=False, setup=None):
        self.cmd=cmd; self.p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
        self.upper=upper
        atexit.register(lambda p=self.p: p.kill())
        for l in (setup or []): self.send(l)
    def send(self,line):
        self.p.stdin.write(line+'\n'); self.p.stdin.flush()
        out=[]
        while True:
            l=self.p.stdout.readline()
            if l=='': break
            l=l.rstrip('\n')
            if l.startswith('winnrate'): self.last_winrate=float(l.split(':')[1]); continue
            if l=='' and out: break
            if l!='' : out.append(l)
        ok = bool(out) and out[0].startswith('=')
        return ok, out
    def board(self):
        self.p.stdin.write('showboard\n'); self.p.stdin.flush()
        rows=[]; hdr=0
        while hdr<2:
            l=self.p.stdout.readline()
            if l=='': break
            if re.match(r'\s+A\s+B\s+C',l): hdr+=1
            rows.append(l.rstrip('\n'))
        # swallow trailing '=' / blank lines until a blank line appears
        return rows
    def color(self,p): return 'white' if p==0 else 'black'
    def play(self,p,m):
        k,v,o=to_qtp(m)
        if k=='m': ok,_=self.send('playmove %s %s'%(self.color(p),v))
        else: ok,_=self.send('playwall %s %s %s'%(self.color(p),v,o))
        return ok
    def undo(self,n=1): return self.send('undo %d'%n)[0]
    def clear(self): return self.send('clear_board')[0]
    def genmove(self,p):
        ok,out=self.send('genmove '+self.color(p)); self.last_raw=out
        if not ok: return None
        toks=out[0][1:].split()
        return from_qtp(toks)
    def close(self):
        try: self.p.stdin.write('quit\n'); self.p.stdin.flush(); self.p.wait(timeout=3)
        except Exception: self.p.kill()
def pavlos(): return QTP([os.path.join(HERE,'pavlos/bin/ipquoridor')])
def georgen(): return QTP([os.path.join(HERE,'georgen/qmcts')],setup=['boardsize 9','walls 10','clear_board'])
