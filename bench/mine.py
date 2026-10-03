import subprocess, json, os
JSC='/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc'
HERE=os.path.dirname(os.path.abspath(__file__))
class Mine:
    def __init__(self, script=None):
        self.p=subprocess.Popen([JSC, script or os.path.join(HERE,'bridge.js')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    def q(self,**kw):
        self.p.stdin.write(json.dumps(kw)+'\n'); self.p.stdin.flush()
        return json.loads(self.p.stdout.readline())
    def close(self):
        try: self.p.stdin.close(); self.p.wait(timeout=5)
        except Exception: self.p.kill()
